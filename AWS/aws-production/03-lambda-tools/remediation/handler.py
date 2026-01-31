"""
TRACE Remediation Lambda - Production Version

This Lambda function executes REAL remediation actions through AWS services:
- Restart agents via ECS/Lambda updates
- Redeploy via CodeDeploy/ECS
- Reroute traffic via actual DynamoDB state updates + IoT commands
- Log all actions to DynamoDB for audit

NO SIMULATED ACTIONS - All actions affect real infrastructure.
"""

import json
import boto3
import os
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
ecs_client = boto3.client('ecs')
lambda_client = boto3.client('lambda')
iot_client = boto3.client('iot-data')
stepfunctions = boto3.client('stepfunctions')
sns_client = boto3.client('sns')
cloudwatch = boto3.client('cloudwatch')

# Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'production')
AGENT_STATE_TABLE = os.getenv('AGENT_STATE_TABLE', f'TRACE-AgentState-{ENVIRONMENT}')
TOWER_CONFIG_TABLE = os.getenv('TOWER_CONFIG_TABLE', f'TRACE-TowerConfig-{ENVIRONMENT}')
REMEDIATION_LOG_TABLE = os.getenv('REMEDIATION_LOG_TABLE', f'TRACE-RemediationLog-{ENVIRONMENT}')
SNS_TOPIC_ARN = os.getenv('SNS_ALERTS_TOPIC')
ECS_CLUSTER = os.getenv('ECS_CLUSTER', f'TRACE-Agents-{ENVIRONMENT}')
IOT_TOPIC_PREFIX = os.getenv('IOT_TOPIC_PREFIX', 'trace/commands')


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def lambda_handler(event, context):
    """
    Main Lambda handler for remediation actions.
    
    Supported actions:
    - restart_agent: Restart an unhealthy agent
    - redeploy_agent: Full redeploy of an agent
    - reroute_traffic: Reroute traffic between towers
    - shutdown_trx: Shutdown transceivers for energy savings
    - activate_trx: Activate transceivers for capacity
    - rollback_change: Rollback a previous remediation
    - execute_remediation: General remediation executor
    """
    
    action = event.get('action', 'restart_agent')
    parameters = event.get('parameters', {})
    
    # Handle Bedrock action group format
    if 'actionGroup' in event:
        action = event.get('function', 'restart_agent')
        parameters = {p['name']: p['value'] for p in event.get('parameters', [])}
    
    handlers = {
        'restart_agent': restart_agent,
        'redeploy_agent': redeploy_agent,
        'reroute_traffic': reroute_traffic,
        'shutdown_trx': shutdown_trx,
        'activate_trx': activate_trx,
        'rollback_change': rollback_change,
        'execute_remediation': execute_remediation,
        'set_power_mode': set_power_mode,
    }
    
    handler = handlers.get(action, execute_remediation)
    
    try:
        result = handler(parameters)
        
        # Log all remediation actions
        log_remediation_action(action, parameters, result)
        
        return format_bedrock_response(result, action)
    except Exception as e:
        error_result = {
            'status': 'error',
            'action': action,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        log_remediation_action(action, parameters, error_result)
        return format_bedrock_response(error_result, action)


def restart_agent(params: dict) -> dict:
    """
    Restart an agent by updating its ECS service or invoking Lambda.
    This is a REAL restart, not simulated.
    """
    agent_id = params.get('agent_id') or params.get('agent_name')
    reason = params.get('reason', 'manual_restart')
    
    if not agent_id:
        return {'status': 'error', 'error': 'agent_id is required'}
    
    # Get agent info from DynamoDB
    try:
        table = dynamodb.Table(AGENT_STATE_TABLE)
        response = table.get_item(Key={'agent_id': agent_id})
        
        if 'Item' not in response:
            return {
                'status': 'error',
                'error': f'Agent {agent_id} not found',
                'agent_id': agent_id,
            }
        
        agent_info = response['Item']
        agent_type = agent_info.get('deployment_type', 'lambda')
        
        start_time = datetime.utcnow()
        
        if agent_type == 'ecs':
            # Restart ECS service
            result = restart_ecs_agent(agent_id, agent_info)
        else:
            # For Lambda-based agents, update the configuration to trigger restart
            result = restart_lambda_agent(agent_id, agent_info)
        
        # Update agent state in DynamoDB
        table.update_item(
            Key={'agent_id': agent_id},
            UpdateExpression='SET #status = :status, last_restart = :time, restart_reason = :reason',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'restarting',
                ':time': datetime.utcnow().isoformat() + 'Z',
                ':reason': reason,
            }
        )
        
        elapsed_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Send notification if critical
        if reason in ['critical_failure', 'unresponsive']:
            send_notification(
                f"Agent Restarted: {agent_id}",
                f"Agent {agent_id} was restarted due to: {reason}\nResult: {result.get('status')}"
            )
        
        return {
            'status': 'success',
            'operation': 'restart_agent',
            'agent_id': agent_id,
            'agent_type': agent_type,
            'reason': reason,
            'execution_time_seconds': round(elapsed_time, 2),
            'result': result,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'action_type': 'REAL_RESTART',
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'operation': 'restart_agent',
            'agent_id': agent_id,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }


def restart_ecs_agent(agent_id: str, agent_info: dict) -> dict:
    """Restart an ECS-based agent service."""
    service_name = agent_info.get('ecs_service', f'trace-{agent_id}')
    
    try:
        # Force new deployment
        response = ecs_client.update_service(
            cluster=ECS_CLUSTER,
            service=service_name,
            forceNewDeployment=True
        )
        
        return {
            'status': 'initiated',
            'service': service_name,
            'deployment_id': response['service']['deployments'][0]['id'] if response['service']['deployments'] else None,
        }
    except ecs_client.exceptions.ServiceNotFoundException:
        return {
            'status': 'error',
            'error': f'ECS service {service_name} not found',
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
        }


def restart_lambda_agent(agent_id: str, agent_info: dict) -> dict:
    """Restart a Lambda-based agent by updating its configuration."""
    function_name = agent_info.get('lambda_function', f'TRACE-{agent_id}-{ENVIRONMENT}')
    
    try:
        # Update environment variable to trigger cold start
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                'Variables': {
                    'RESTART_TIMESTAMP': datetime.utcnow().isoformat(),
                    'RESTART_REASON': 'agent_restart',
                }
            }
        )
        
        return {
            'status': 'initiated',
            'function': function_name,
            'message': 'Lambda configuration updated to trigger restart',
        }
    except lambda_client.exceptions.ResourceNotFoundException:
        return {
            'status': 'error',
            'error': f'Lambda function {function_name} not found',
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
        }


def redeploy_agent(params: dict) -> dict:
    """
    Full redeploy of an agent - more aggressive than restart.
    Creates new task/instance with fresh state.
    """
    agent_id = params.get('agent_id') or params.get('agent_name')
    version = params.get('version', 'latest')
    
    if not agent_id:
        return {'status': 'error', 'error': 'agent_id is required'}
    
    try:
        table = dynamodb.Table(AGENT_STATE_TABLE)
        response = table.get_item(Key={'agent_id': agent_id})
        
        if 'Item' not in response:
            return {
                'status': 'error',
                'error': f'Agent {agent_id} not found',
            }
        
        agent_info = response['Item']
        agent_type = agent_info.get('deployment_type', 'lambda')
        
        start_time = datetime.utcnow()
        
        if agent_type == 'ecs':
            # Stop and start new task
            result = redeploy_ecs_agent(agent_id, agent_info, version)
        else:
            # Publish new Lambda version
            result = redeploy_lambda_agent(agent_id, agent_info, version)
        
        # Clear agent state (fresh start)
        table.update_item(
            Key={'agent_id': agent_id},
            UpdateExpression='SET #status = :status, last_redeploy = :time, version = :version, tasks_completed = :zero, tasks_failed = :zero',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'redeploying',
                ':time': datetime.utcnow().isoformat() + 'Z',
                ':version': version,
                ':zero': 0,
            }
        )
        
        elapsed_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Always notify on redeploy
        send_notification(
            f"Agent Redeployed: {agent_id}",
            f"Agent {agent_id} was redeployed with version: {version}"
        )
        
        return {
            'status': 'success',
            'operation': 'redeploy_agent',
            'agent_id': agent_id,
            'version': version,
            'execution_time_seconds': round(elapsed_time, 2),
            'result': result,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'action_type': 'REAL_REDEPLOY',
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'operation': 'redeploy_agent',
            'agent_id': agent_id,
            'error': str(e),
        }


def redeploy_ecs_agent(agent_id: str, agent_info: dict, version: str) -> dict:
    """Redeploy ECS agent with new task definition."""
    service_name = agent_info.get('ecs_service', f'trace-{agent_id}')
    
    try:
        # Get current service
        service_response = ecs_client.describe_services(
            cluster=ECS_CLUSTER,
            services=[service_name]
        )
        
        if not service_response['services']:
            return {'status': 'error', 'error': 'Service not found'}
        
        service = service_response['services'][0]
        task_definition = service['taskDefinition']
        
        # Update to desired count 0, then back to original (full restart)
        desired_count = service['desiredCount']
        
        # Scale down
        ecs_client.update_service(
            cluster=ECS_CLUSTER,
            service=service_name,
            desiredCount=0
        )
        
        # Scale back up with force new deployment
        ecs_client.update_service(
            cluster=ECS_CLUSTER,
            service=service_name,
            desiredCount=desired_count,
            forceNewDeployment=True
        )
        
        return {
            'status': 'initiated',
            'service': service_name,
            'task_definition': task_definition,
            'desired_count': desired_count,
        }
        
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def redeploy_lambda_agent(agent_id: str, agent_info: dict, version: str) -> dict:
    """Redeploy Lambda agent by publishing new version."""
    function_name = agent_info.get('lambda_function', f'TRACE-{agent_id}-{ENVIRONMENT}')
    
    try:
        # Publish new version
        response = lambda_client.publish_version(
            FunctionName=function_name,
            Description=f'Redeploy {version} at {datetime.utcnow().isoformat()}'
        )
        
        return {
            'status': 'success',
            'function': function_name,
            'new_version': response['Version'],
            'code_sha': response['CodeSha256'],
        }
        
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def reroute_traffic(params: dict) -> dict:
    """
    Reroute traffic from one tower to another.
    This updates DynamoDB config and sends IoT commands to towers.
    """
    source_tower = params.get('source_tower')
    target_tower = params.get('target_tower')
    percentage = float(params.get('percentage', 50))
    
    if not source_tower or not target_tower:
        return {'status': 'error', 'error': 'source_tower and target_tower are required'}
    
    if not 0 <= percentage <= 100:
        return {'status': 'error', 'error': 'percentage must be between 0 and 100'}
    
    try:
        config_table = dynamodb.Table(TOWER_CONFIG_TABLE)
        
        # Verify source tower exists
        source_response = config_table.get_item(Key={'tower_id': source_tower})
        if 'Item' not in source_response:
            return {'status': 'error', 'error': f'Source tower {source_tower} not found'}
        
        # Verify target tower exists and has capacity
        target_response = config_table.get_item(Key={'tower_id': target_tower})
        if 'Item' not in target_response:
            return {'status': 'error', 'error': f'Target tower {target_tower} not found'}
        
        target_config = target_response['Item']
        current_utilization = float(target_config.get('current_utilization', 50))
        
        # Estimate traffic being moved
        source_config = source_response['Item']
        source_users = int(source_config.get('connected_users', 0))
        users_to_move = int(source_users * (percentage / 100))
        
        target_capacity = int(target_config.get('capacity', 1000))
        target_current_users = int(target_config.get('connected_users', 0))
        new_target_utilization = ((target_current_users + users_to_move) / target_capacity) * 100
        
        if new_target_utilization > 90:
            return {
                'status': 'error',
                'error': 'Target tower would exceed 90% capacity',
                'current_target_utilization': current_utilization,
                'projected_utilization': new_target_utilization,
            }
        
        reroute_id = str(uuid.uuid4())[:8]
        
        # Update tower configurations
        config_table.update_item(
            Key={'tower_id': source_tower},
            UpdateExpression='SET reroute_target = :target, reroute_percentage = :pct, reroute_id = :rid, last_modified = :time',
            ExpressionAttributeValues={
                ':target': target_tower,
                ':pct': Decimal(str(percentage)),
                ':rid': reroute_id,
                ':time': datetime.utcnow().isoformat() + 'Z',
            }
        )
        
        # Send IoT command to source tower
        command_payload = {
            'command': 'reroute_traffic',
            'reroute_id': reroute_id,
            'target_tower': target_tower,
            'percentage': percentage,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        
        try:
            iot_client.publish(
                topic=f'{IOT_TOPIC_PREFIX}/{source_tower}/commands',
                qos=1,
                payload=json.dumps(command_payload)
            )
            iot_status = 'command_sent'
        except Exception as e:
            iot_status = f'iot_error: {str(e)}'
        
        return {
            'status': 'success',
            'operation': 'reroute_traffic',
            'reroute_id': reroute_id,
            'source_tower': source_tower,
            'target_tower': target_tower,
            'percentage': percentage,
            'estimated_users_moved': users_to_move,
            'projected_target_utilization': round(new_target_utilization, 2),
            'iot_status': iot_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'action_type': 'REAL_REROUTE',
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'operation': 'reroute_traffic',
            'error': str(e),
        }


def shutdown_trx(params: dict) -> dict:
    """
    Shutdown transceivers on a tower for energy savings.
    Sends real IoT command to tower controller.
    """
    tower_id = params.get('tower_id')
    trx_count = int(params.get('trx_count', 2))  # Number of TRX to shutdown
    reason = params.get('reason', 'energy_optimization')
    
    if not tower_id:
        return {'status': 'error', 'error': 'tower_id is required'}
    
    try:
        config_table = dynamodb.Table(TOWER_CONFIG_TABLE)
        
        # Get current tower config
        response = config_table.get_item(Key={'tower_id': tower_id})
        if 'Item' not in response:
            return {'status': 'error', 'error': f'Tower {tower_id} not found'}
        
        tower_config = response['Item']
        active_trx = int(tower_config.get('active_trx', 8))
        min_trx = int(tower_config.get('min_trx', 2))  # Minimum TRX that must stay active
        
        # Calculate new active TRX count
        new_active_trx = max(active_trx - trx_count, min_trx)
        actual_shutdown = active_trx - new_active_trx
        
        if actual_shutdown == 0:
            return {
                'status': 'warning',
                'message': 'Cannot shutdown more TRX - minimum threshold reached',
                'current_active_trx': active_trx,
                'min_trx': min_trx,
            }
        
        # Calculate energy savings (approx 2.5 kW per TRX)
        energy_savings_kw = actual_shutdown * 2.5
        
        # Update DynamoDB
        config_table.update_item(
            Key={'tower_id': tower_id},
            UpdateExpression='SET active_trx = :active, power_mode = :mode, last_trx_change = :time',
            ExpressionAttributeValues={
                ':active': new_active_trx,
                ':mode': 'energy_saving',
                ':time': datetime.utcnow().isoformat() + 'Z',
            }
        )
        
        # Send IoT command
        command_payload = {
            'command': 'shutdown_trx',
            'shutdown_count': actual_shutdown,
            'new_active_count': new_active_trx,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        
        try:
            iot_client.publish(
                topic=f'{IOT_TOPIC_PREFIX}/{tower_id}/commands',
                qos=1,
                payload=json.dumps(command_payload)
            )
            iot_status = 'command_sent'
        except Exception as e:
            iot_status = f'iot_error: {str(e)}'
        
        # Publish CloudWatch metric
        cloudwatch.put_metric_data(
            Namespace='TRACE/Production',
            MetricData=[{
                'MetricName': 'TRXShutdown',
                'Dimensions': [
                    {'Name': 'TowerID', 'Value': tower_id},
                    {'Name': 'Environment', 'Value': ENVIRONMENT},
                ],
                'Value': actual_shutdown,
                'Unit': 'Count',
            }]
        )
        
        return {
            'status': 'success',
            'operation': 'shutdown_trx',
            'tower_id': tower_id,
            'trx_shutdown': actual_shutdown,
            'previous_active_trx': active_trx,
            'new_active_trx': new_active_trx,
            'estimated_energy_savings_kw': energy_savings_kw,
            'iot_status': iot_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'action_type': 'REAL_TRX_SHUTDOWN',
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'operation': 'shutdown_trx',
            'tower_id': tower_id,
            'error': str(e),
        }


def activate_trx(params: dict) -> dict:
    """
    Activate additional transceivers on a tower for increased capacity.
    """
    tower_id = params.get('tower_id')
    trx_count = int(params.get('trx_count', 2))
    reason = params.get('reason', 'capacity_increase')
    
    if not tower_id:
        return {'status': 'error', 'error': 'tower_id is required'}
    
    try:
        config_table = dynamodb.Table(TOWER_CONFIG_TABLE)
        
        response = config_table.get_item(Key={'tower_id': tower_id})
        if 'Item' not in response:
            return {'status': 'error', 'error': f'Tower {tower_id} not found'}
        
        tower_config = response['Item']
        active_trx = int(tower_config.get('active_trx', 2))
        total_trx = int(tower_config.get('total_trx', 8))
        
        new_active_trx = min(active_trx + trx_count, total_trx)
        actual_activation = new_active_trx - active_trx
        
        if actual_activation == 0:
            return {
                'status': 'warning',
                'message': 'All TRX already active',
                'current_active_trx': active_trx,
                'total_trx': total_trx,
            }
        
        # Update DynamoDB
        config_table.update_item(
            Key={'tower_id': tower_id},
            UpdateExpression='SET active_trx = :active, power_mode = :mode, last_trx_change = :time',
            ExpressionAttributeValues={
                ':active': new_active_trx,
                ':mode': 'full_capacity',
                ':time': datetime.utcnow().isoformat() + 'Z',
            }
        )
        
        # Send IoT command
        command_payload = {
            'command': 'activate_trx',
            'activate_count': actual_activation,
            'new_active_count': new_active_trx,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        
        try:
            iot_client.publish(
                topic=f'{IOT_TOPIC_PREFIX}/{tower_id}/commands',
                qos=1,
                payload=json.dumps(command_payload)
            )
            iot_status = 'command_sent'
        except Exception as e:
            iot_status = f'iot_error: {str(e)}'
        
        return {
            'status': 'success',
            'operation': 'activate_trx',
            'tower_id': tower_id,
            'trx_activated': actual_activation,
            'previous_active_trx': active_trx,
            'new_active_trx': new_active_trx,
            'iot_status': iot_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'action_type': 'REAL_TRX_ACTIVATION',
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'operation': 'activate_trx',
            'error': str(e),
        }


def set_power_mode(params: dict) -> dict:
    """
    Set power mode for a tower (normal, energy_saving, full_capacity).
    """
    tower_id = params.get('tower_id')
    power_mode = params.get('power_mode', 'normal')
    
    if not tower_id:
        return {'status': 'error', 'error': 'tower_id is required'}
    
    if power_mode not in ['normal', 'energy_saving', 'full_capacity', 'maintenance']:
        return {'status': 'error', 'error': 'Invalid power_mode'}
    
    try:
        config_table = dynamodb.Table(TOWER_CONFIG_TABLE)
        
        # Update config
        config_table.update_item(
            Key={'tower_id': tower_id},
            UpdateExpression='SET power_mode = :mode, last_modified = :time',
            ExpressionAttributeValues={
                ':mode': power_mode,
                ':time': datetime.utcnow().isoformat() + 'Z',
            }
        )
        
        # Send IoT command
        command_payload = {
            'command': 'set_power_mode',
            'power_mode': power_mode,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        
        try:
            iot_client.publish(
                topic=f'{IOT_TOPIC_PREFIX}/{tower_id}/commands',
                qos=1,
                payload=json.dumps(command_payload)
            )
            iot_status = 'command_sent'
        except Exception as e:
            iot_status = f'iot_error: {str(e)}'
        
        return {
            'status': 'success',
            'operation': 'set_power_mode',
            'tower_id': tower_id,
            'power_mode': power_mode,
            'iot_status': iot_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def rollback_change(params: dict) -> dict:
    """
    Rollback a previous remediation action.
    """
    change_id = params.get('change_id') or params.get('reroute_id')
    
    if not change_id:
        return {'status': 'error', 'error': 'change_id is required'}
    
    try:
        # Look up the change in remediation log
        log_table = dynamodb.Table(REMEDIATION_LOG_TABLE)
        
        # Query by change_id (assuming GSI exists)
        response = log_table.scan(
            FilterExpression='change_id = :cid',
            ExpressionAttributeValues={':cid': change_id}
        )
        
        if not response.get('Items'):
            return {
                'status': 'error',
                'error': f'Change {change_id} not found in remediation log',
            }
        
        original_action = response['Items'][0]
        action_type = original_action.get('action_type')
        
        # Perform rollback based on action type
        if action_type == 'reroute_traffic':
            # Reverse the reroute
            source = original_action.get('parameters', {}).get('source_tower')
            target = original_action.get('parameters', {}).get('target_tower')
            
            if source and target:
                rollback_result = reroute_traffic({
                    'source_tower': target,
                    'target_tower': source,
                    'percentage': original_action.get('parameters', {}).get('percentage', 100),
                })
            else:
                rollback_result = {'status': 'error', 'error': 'Missing tower info for rollback'}
                
        elif action_type in ['shutdown_trx', 'REAL_TRX_SHUTDOWN']:
            # Reactivate the TRX
            tower_id = original_action.get('parameters', {}).get('tower_id')
            trx_count = original_action.get('result', {}).get('trx_shutdown', 2)
            
            rollback_result = activate_trx({
                'tower_id': tower_id,
                'trx_count': trx_count,
                'reason': 'rollback',
            })
            
        elif action_type in ['activate_trx', 'REAL_TRX_ACTIVATION']:
            # Deactivate the TRX
            tower_id = original_action.get('parameters', {}).get('tower_id')
            trx_count = original_action.get('result', {}).get('trx_activated', 2)
            
            rollback_result = shutdown_trx({
                'tower_id': tower_id,
                'trx_count': trx_count,
                'reason': 'rollback',
            })
            
        else:
            rollback_result = {
                'status': 'error',
                'error': f'Rollback not supported for action type: {action_type}',
            }
        
        return {
            'status': rollback_result.get('status', 'unknown'),
            'operation': 'rollback_change',
            'original_change_id': change_id,
            'original_action': action_type,
            'rollback_result': rollback_result,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'operation': 'rollback_change',
            'change_id': change_id,
            'error': str(e),
        }


def execute_remediation(params: dict) -> dict:
    """
    General remediation executor - routes to specific action handlers.
    Used for Step Functions integration.
    """
    action = params.get('remediation_action') or params.get('action')
    
    action_handlers = {
        'restart_agent': restart_agent,
        'redeploy_agent': redeploy_agent,
        'reroute_traffic': reroute_traffic,
        'shutdown_trx': shutdown_trx,
        'activate_trx': activate_trx,
        'set_power_mode': set_power_mode,
        'rollback': rollback_change,
    }
    
    handler = action_handlers.get(action)
    if handler:
        return handler(params)
    else:
        return {
            'status': 'error',
            'error': f'Unknown remediation action: {action}',
            'available_actions': list(action_handlers.keys()),
        }


def log_remediation_action(action: str, parameters: dict, result: dict) -> None:
    """Log all remediation actions to DynamoDB for audit."""
    try:
        table = dynamodb.Table(REMEDIATION_LOG_TABLE)
        
        log_entry = {
            'remediation_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'action_type': action,
            'parameters': parameters,
            'result': result,
            'status': result.get('status', 'unknown'),
            'change_id': result.get('reroute_id') or result.get('change_id') or str(uuid.uuid4())[:8],
        }
        
        table.put_item(Item=json.loads(json.dumps(log_entry), parse_float=Decimal))
        
    except Exception as e:
        print(f"Failed to log remediation action: {str(e)}")


def send_notification(subject: str, message: str) -> None:
    """Send notification via SNS."""
    if not SNS_TOPIC_ARN:
        return
    
    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject[:100],  # SNS subject limit
            Message=message,
        )
    except Exception as e:
        print(f"Failed to send notification: {str(e)}")


def format_bedrock_response(result: dict, action: str) -> dict:
    """Format response for Bedrock action group."""
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'remediation',
            'function': action,
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps(result, cls=DecimalEncoder)
                    }
                }
            }
        }
    }
