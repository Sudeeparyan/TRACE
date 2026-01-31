"""
TRACE Health Monitor Lambda - Production Version

This Lambda function provides REAL health monitoring by querying actual AWS services:
- Timestream for time-series telemetry data
- DynamoDB for tower configuration and agent state
- CloudWatch for service metrics

NO RANDOM VALUES - All data comes from real AWS services.
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any

# Initialize AWS clients
timestream_query = boto3.client('timestream-query')
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

# Configuration from environment
ENVIRONMENT = os.getenv('TRACE_ENV', 'production')
TIMESTREAM_DATABASE = os.getenv('TIMESTREAM_DATABASE', f'TRACE-Telemetry-{ENVIRONMENT}')
TIMESTREAM_TABLE = os.getenv('TIMESTREAM_TABLE', 'TowerMetrics')
AGENT_STATE_TABLE = os.getenv('AGENT_STATE_TABLE', f'TRACE-AgentState-{ENVIRONMENT}')
TOWER_CONFIG_TABLE = os.getenv('TOWER_CONFIG_TABLE', f'TRACE-TowerConfig-{ENVIRONMENT}')

# Thresholds
THRESHOLDS = {
    'cpu_warning': 75.0,
    'cpu_critical': 90.0,
    'latency_warning': 80.0,
    'latency_critical': 150.0,
    'utilization_warning': 75.0,
    'utilization_critical': 90.0,
    'packet_loss_warning': 1.0,
    'packet_loss_critical': 3.0,
    'temperature_warning': 55.0,
    'temperature_critical': 65.0,
}


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def lambda_handler(event, context):
    """
    Main Lambda handler for health monitoring.
    
    Supported actions:
    - check_system_health: Overall system health from real telemetry
    - get_agent_status: Status of a specific agent from DynamoDB
    - get_tower_health: Health metrics for a specific tower from Timestream
    - get_regional_health: Regional health summary from aggregated Timestream data
    - get_anomalies: Detected anomalies from CloudWatch alarms
    """
    
    action = event.get('action', 'check_system_health')
    parameters = event.get('parameters', {})
    
    # Handle Bedrock action group format
    if 'actionGroup' in event:
        action = event.get('function', 'check_system_health')
        parameters = {p['name']: p['value'] for p in event.get('parameters', [])}
    
    handlers = {
        'check_system_health': check_system_health,
        'get_agent_status': get_agent_status,
        'get_tower_health': get_tower_health,
        'get_regional_health': get_regional_health,
        'get_anomalies': get_anomalies,
        'get_network_summary': get_network_summary,
    }
    
    handler = handlers.get(action, check_system_health)
    
    try:
        result = handler(parameters)
        return format_bedrock_response(result)
    except Exception as e:
        return format_bedrock_response({
            'error': str(e),
            'status': 'error',
            'action': action
        })


def check_system_health(params: dict) -> dict:
    """
    Check overall system health by querying REAL telemetry data from Timestream.
    """
    try:
        # Query Timestream for recent metrics (last 5 minutes)
        query = f"""
            SELECT 
                tower_id,
                region_id,
                AVG(cpu_util_pct) as avg_cpu,
                AVG(latency_ms) as avg_latency,
                AVG(connected_users) as avg_users,
                AVG(bandwidth_utilization_pct) as avg_bandwidth,
                MAX(cpu_util_pct) as max_cpu,
                MAX(latency_ms) as max_latency,
                COUNT(*) as sample_count
            FROM "{TIMESTREAM_DATABASE}"."{TIMESTREAM_TABLE}"
            WHERE time > ago(5m)
            GROUP BY tower_id, region_id
        """
        
        response = timestream_query.query(QueryString=query)
        
        # Process results
        tower_metrics = parse_timestream_results(response)
        
        # Calculate overall health
        health_status = calculate_health_status(tower_metrics)
        
        # Get agent statuses from DynamoDB
        agent_status = get_all_agent_statuses()
        
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'overall_status': health_status['status'],
            'components': {
                'towers': {
                    'total': health_status['total_towers'],
                    'healthy': health_status['healthy_towers'],
                    'warning': health_status['warning_towers'],
                    'critical': health_status['critical_towers'],
                },
                'agents': {
                    'total': agent_status['total'],
                    'active': agent_status['active'],
                    'inactive': agent_status['inactive'],
                    'error': agent_status['error'],
                },
            },
            'metrics': {
                'avg_cpu_usage': round(health_status['avg_cpu'], 2),
                'avg_latency_ms': round(health_status['avg_latency'], 2),
                'total_users': health_status['total_users'],
                'avg_bandwidth_utilization': round(health_status['avg_bandwidth'], 2),
            },
            'issues': health_status['issues'],
            'data_source': 'timestream_realtime',
            'query_time_range': 'last_5_minutes',
        }
        
    except timestream_query.exceptions.ValidationException as e:
        # Timestream database/table might not exist yet
        return get_fallback_health_status(str(e))
    except Exception as e:
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'overall_status': 'unknown',
            'error': str(e),
            'data_source': 'error',
        }


def get_agent_status(params: dict) -> dict:
    """
    Get REAL agent status from DynamoDB Agent State table.
    """
    agent_id = params.get('agent_id') or params.get('agent_name')
    
    if not agent_id:
        return {'error': 'agent_id is required'}
    
    try:
        table = dynamodb.Table(AGENT_STATE_TABLE)
        response = table.get_item(Key={'agent_id': agent_id})
        
        if 'Item' not in response:
            return {
                'agent_id': agent_id,
                'status': 'not_found',
                'message': f'Agent {agent_id} not found in state table'
            }
        
        item = response['Item']
        
        # Calculate derived metrics
        last_heartbeat = item.get('last_heartbeat', '')
        if last_heartbeat:
            hb_time = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
            time_since_heartbeat = (datetime.utcnow().replace(tzinfo=hb_time.tzinfo) - hb_time).total_seconds()
            heartbeat_status = 'healthy' if time_since_heartbeat < 60 else 'stale'
        else:
            time_since_heartbeat = None
            heartbeat_status = 'unknown'
        
        return {
            'agent_id': agent_id,
            'agent_type': item.get('agent_type', 'unknown'),
            'status': item.get('status', 'unknown'),
            'heartbeat_status': heartbeat_status,
            'last_heartbeat': last_heartbeat,
            'seconds_since_heartbeat': time_since_heartbeat,
            'region': item.get('region'),
            'tower_id': item.get('tower_id'),
            'metrics': {
                'tasks_completed': int(item.get('tasks_completed', 0)),
                'tasks_failed': int(item.get('tasks_failed', 0)),
                'success_rate': float(item.get('success_rate', 0)),
                'avg_response_time_ms': float(item.get('avg_response_time_ms', 0)),
            },
            'last_action': item.get('last_action'),
            'last_action_time': item.get('last_action_time'),
            'data_source': 'dynamodb_realtime',
        }
        
    except Exception as e:
        return {
            'agent_id': agent_id,
            'status': 'error',
            'error': str(e),
        }


def get_tower_health(params: dict) -> dict:
    """
    Get REAL tower health metrics from Timestream.
    """
    tower_id = params.get('tower_id')
    time_range = params.get('time_range', '1h')  # Default 1 hour
    
    if not tower_id:
        return {'error': 'tower_id is required'}
    
    try:
        # Map time range to Timestream syntax
        time_map = {'5m': '5m', '15m': '15m', '1h': '1h', '6h': '6h', '24h': '24h'}
        ts_time = time_map.get(time_range, '1h')
        
        query = f"""
            SELECT 
                tower_id,
                region_id,
                time,
                connected_users,
                capacity_users,
                cpu_util_pct,
                bandwidth_utilization_pct,
                latency_ms,
                packet_loss_pct,
                power_voltage_v,
                temperature_celsius,
                rsrq_db
            FROM "{TIMESTREAM_DATABASE}"."{TIMESTREAM_TABLE}"
            WHERE tower_id = '{tower_id}'
            AND time > ago({ts_time})
            ORDER BY time DESC
            LIMIT 100
        """
        
        response = timestream_query.query(QueryString=query)
        records = parse_timestream_results(response)
        
        if not records:
            return {
                'tower_id': tower_id,
                'status': 'no_data',
                'message': f'No recent telemetry data for tower {tower_id}',
            }
        
        # Get latest record
        latest = records[0]
        
        # Calculate health indicators
        health_indicators = assess_tower_health(latest)
        
        # Get tower config from DynamoDB
        tower_config = get_tower_config(tower_id)
        
        return {
            'tower_id': tower_id,
            'region_id': latest.get('region_id'),
            'timestamp': latest.get('time'),
            'status': health_indicators['status'],
            'current_metrics': {
                'connected_users': int(latest.get('connected_users', 0)),
                'capacity_users': int(latest.get('capacity_users', 1000)),
                'utilization_pct': round((int(latest.get('connected_users', 0)) / max(int(latest.get('capacity_users', 1000)), 1)) * 100, 2),
                'cpu_util_pct': round(float(latest.get('cpu_util_pct', 0)), 2),
                'bandwidth_utilization_pct': round(float(latest.get('bandwidth_utilization_pct', 0)), 2),
                'latency_ms': round(float(latest.get('latency_ms', 0)), 2),
                'packet_loss_pct': round(float(latest.get('packet_loss_pct', 0)), 2),
                'power_voltage_v': round(float(latest.get('power_voltage_v', 0)), 2),
                'temperature_celsius': round(float(latest.get('temperature_celsius', 0)), 2),
                'rsrq_db': round(float(latest.get('rsrq_db', 0)), 2),
            },
            'health_indicators': health_indicators['indicators'],
            'issues': health_indicators['issues'],
            'config': tower_config,
            'sample_count': len(records),
            'time_range': time_range,
            'data_source': 'timestream_realtime',
        }
        
    except timestream_query.exceptions.ValidationException as e:
        return {
            'tower_id': tower_id,
            'status': 'error',
            'error': f'Timestream query error: {str(e)}',
            'suggestion': 'Ensure Timestream database and table exist',
        }
    except Exception as e:
        return {
            'tower_id': tower_id,
            'status': 'error',
            'error': str(e),
        }


def get_regional_health(params: dict) -> dict:
    """
    Get REAL regional health summary by aggregating Timestream data.
    """
    region_id = params.get('region_id')
    
    try:
        # Build query based on whether region is specified
        if region_id:
            region_filter = f"AND region_id = '{region_id}'"
        else:
            region_filter = ""
        
        query = f"""
            SELECT 
                region_id,
                COUNT(DISTINCT tower_id) as tower_count,
                SUM(connected_users) as total_users,
                AVG(cpu_util_pct) as avg_cpu,
                AVG(bandwidth_utilization_pct) as avg_bandwidth,
                AVG(latency_ms) as avg_latency,
                MAX(cpu_util_pct) as max_cpu,
                MAX(latency_ms) as max_latency
            FROM "{TIMESTREAM_DATABASE}"."{TIMESTREAM_TABLE}"
            WHERE time > ago(5m)
            {region_filter}
            GROUP BY region_id
        """
        
        response = timestream_query.query(QueryString=query)
        regions = parse_timestream_results(response)
        
        # Process each region
        regional_summary = []
        for region in regions:
            # Determine region health status
            avg_cpu = float(region.get('avg_cpu', 0))
            avg_latency = float(region.get('avg_latency', 0))
            max_cpu = float(region.get('max_cpu', 0))
            
            if max_cpu > THRESHOLDS['cpu_critical'] or avg_latency > THRESHOLDS['latency_critical']:
                status = 'critical'
            elif avg_cpu > THRESHOLDS['cpu_warning'] or avg_latency > THRESHOLDS['latency_warning']:
                status = 'warning'
            else:
                status = 'healthy'
            
            regional_summary.append({
                'region_id': region.get('region_id'),
                'status': status,
                'tower_count': int(region.get('tower_count', 0)),
                'total_users': int(region.get('total_users', 0)),
                'metrics': {
                    'avg_cpu': round(avg_cpu, 2),
                    'avg_bandwidth': round(float(region.get('avg_bandwidth', 0)), 2),
                    'avg_latency': round(avg_latency, 2),
                    'max_cpu': round(max_cpu, 2),
                    'max_latency': round(float(region.get('max_latency', 0)), 2),
                },
            })
        
        # Overall summary
        total_towers = sum(r['tower_count'] for r in regional_summary)
        total_users = sum(r['total_users'] for r in regional_summary)
        healthy_regions = sum(1 for r in regional_summary if r['status'] == 'healthy')
        
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'summary': {
                'total_regions': len(regional_summary),
                'healthy_regions': healthy_regions,
                'total_towers': total_towers,
                'total_users': total_users,
            },
            'regions': regional_summary,
            'data_source': 'timestream_realtime',
            'time_range': 'last_5_minutes',
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
        }


def get_anomalies(params: dict) -> dict:
    """
    Get REAL anomalies from CloudWatch Alarms and Timestream data.
    """
    try:
        anomalies = []
        
        # Check CloudWatch alarms
        cw_response = cloudwatch.describe_alarms(
            StateValue='ALARM',
            AlarmNamePrefix='TRACE-'
        )
        
        for alarm in cw_response.get('MetricAlarms', []):
            anomalies.append({
                'source': 'cloudwatch_alarm',
                'type': alarm['AlarmName'],
                'severity': 'critical' if 'Critical' in alarm['AlarmName'] else 'warning',
                'message': alarm.get('StateReason', 'Alarm triggered'),
                'timestamp': alarm.get('StateUpdatedTimestamp', '').isoformat() if alarm.get('StateUpdatedTimestamp') else None,
                'metric': alarm.get('MetricName'),
                'threshold': alarm.get('Threshold'),
            })
        
        # Query Timestream for metric-based anomalies
        query = f"""
            SELECT 
                tower_id,
                region_id,
                time,
                cpu_util_pct,
                latency_ms,
                packet_loss_pct,
                temperature_celsius
            FROM "{TIMESTREAM_DATABASE}"."{TIMESTREAM_TABLE}"
            WHERE time > ago(15m)
            AND (
                cpu_util_pct > {THRESHOLDS['cpu_warning']}
                OR latency_ms > {THRESHOLDS['latency_warning']}
                OR packet_loss_pct > {THRESHOLDS['packet_loss_warning']}
                OR temperature_celsius > {THRESHOLDS['temperature_warning']}
            )
            ORDER BY time DESC
            LIMIT 50
        """
        
        response = timestream_query.query(QueryString=query)
        records = parse_timestream_results(response)
        
        for record in records:
            # Check each metric for anomalies
            cpu = float(record.get('cpu_util_pct', 0))
            latency = float(record.get('latency_ms', 0))
            packet_loss = float(record.get('packet_loss_pct', 0))
            temperature = float(record.get('temperature_celsius', 0))
            
            if cpu > THRESHOLDS['cpu_critical']:
                anomalies.append({
                    'source': 'timestream',
                    'type': 'HIGH_CPU',
                    'severity': 'critical',
                    'tower_id': record.get('tower_id'),
                    'region_id': record.get('region_id'),
                    'value': cpu,
                    'threshold': THRESHOLDS['cpu_critical'],
                    'timestamp': record.get('time'),
                })
            elif cpu > THRESHOLDS['cpu_warning']:
                anomalies.append({
                    'source': 'timestream',
                    'type': 'HIGH_CPU',
                    'severity': 'warning',
                    'tower_id': record.get('tower_id'),
                    'region_id': record.get('region_id'),
                    'value': cpu,
                    'threshold': THRESHOLDS['cpu_warning'],
                    'timestamp': record.get('time'),
                })
            
            if latency > THRESHOLDS['latency_critical']:
                anomalies.append({
                    'source': 'timestream',
                    'type': 'HIGH_LATENCY',
                    'severity': 'critical',
                    'tower_id': record.get('tower_id'),
                    'region_id': record.get('region_id'),
                    'value': latency,
                    'threshold': THRESHOLDS['latency_critical'],
                    'timestamp': record.get('time'),
                })
        
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_anomalies': len(anomalies),
            'critical_count': sum(1 for a in anomalies if a['severity'] == 'critical'),
            'warning_count': sum(1 for a in anomalies if a['severity'] == 'warning'),
            'anomalies': anomalies,
            'data_source': 'cloudwatch_and_timestream',
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'anomalies': [],
        }


def get_network_summary(params: dict) -> dict:
    """
    Get comprehensive network summary from REAL data sources.
    """
    try:
        # Get health status
        health = check_system_health({})
        
        # Get anomalies
        anomalies = get_anomalies({})
        
        # Query energy metrics
        energy_query = f"""
            SELECT 
                SUM(power_kw) as total_power,
                AVG(power_kw) as avg_power,
                SUM(active_trx) as total_active_trx,
                SUM(total_trx) as total_trx
            FROM "{TIMESTREAM_DATABASE}"."{TIMESTREAM_TABLE}"
            WHERE time > ago(5m)
        """
        
        try:
            energy_response = timestream_query.query(QueryString=energy_query)
            energy_data = parse_timestream_results(energy_response)
            energy_metrics = energy_data[0] if energy_data else {}
        except:
            energy_metrics = {}
        
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'health_summary': {
                'status': health.get('overall_status', 'unknown'),
                'towers': health.get('components', {}).get('towers', {}),
                'agents': health.get('components', {}).get('agents', {}),
            },
            'performance_metrics': health.get('metrics', {}),
            'energy_metrics': {
                'total_power_kw': round(float(energy_metrics.get('total_power', 0)), 2),
                'avg_power_per_tower_kw': round(float(energy_metrics.get('avg_power', 0)), 2),
                'active_trx': int(energy_metrics.get('total_active_trx', 0)),
                'total_trx': int(energy_metrics.get('total_trx', 0)),
                'efficiency_ratio': round(
                    int(energy_metrics.get('total_active_trx', 0)) / 
                    max(int(energy_metrics.get('total_trx', 1)), 1), 2
                ),
            },
            'anomaly_summary': {
                'total': anomalies.get('total_anomalies', 0),
                'critical': anomalies.get('critical_count', 0),
                'warning': anomalies.get('warning_count', 0),
            },
            'issues': health.get('issues', []),
            'data_source': 'multi_source_realtime',
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
        }


# ============================================
# HELPER FUNCTIONS
# ============================================

def parse_timestream_results(response: dict) -> List[dict]:
    """Parse Timestream query response into list of dictionaries."""
    columns = [col['Name'] for col in response.get('ColumnInfo', [])]
    rows = response.get('Rows', [])
    
    results = []
    for row in rows:
        record = {}
        for i, data in enumerate(row.get('Data', [])):
            if 'ScalarValue' in data:
                record[columns[i]] = data['ScalarValue']
            elif 'NullValue' in data:
                record[columns[i]] = None
        results.append(record)
    
    return results


def calculate_health_status(tower_metrics: List[dict]) -> dict:
    """Calculate overall health status from tower metrics."""
    if not tower_metrics:
        return {
            'status': 'unknown',
            'total_towers': 0,
            'healthy_towers': 0,
            'warning_towers': 0,
            'critical_towers': 0,
            'avg_cpu': 0,
            'avg_latency': 0,
            'avg_bandwidth': 0,
            'total_users': 0,
            'issues': [],
        }
    
    healthy = 0
    warning = 0
    critical = 0
    issues = []
    
    total_cpu = 0
    total_latency = 0
    total_bandwidth = 0
    total_users = 0
    
    for tower in tower_metrics:
        avg_cpu = float(tower.get('avg_cpu', 0))
        avg_latency = float(tower.get('avg_latency', 0))
        max_cpu = float(tower.get('max_cpu', 0))
        max_latency = float(tower.get('max_latency', 0))
        
        total_cpu += avg_cpu
        total_latency += avg_latency
        total_bandwidth += float(tower.get('avg_bandwidth', 0))
        total_users += int(float(tower.get('avg_users', 0)))
        
        if max_cpu > THRESHOLDS['cpu_critical'] or max_latency > THRESHOLDS['latency_critical']:
            critical += 1
            issues.append({
                'tower_id': tower.get('tower_id'),
                'severity': 'critical',
                'reason': f"CPU: {max_cpu:.1f}%, Latency: {max_latency:.1f}ms",
            })
        elif avg_cpu > THRESHOLDS['cpu_warning'] or avg_latency > THRESHOLDS['latency_warning']:
            warning += 1
            issues.append({
                'tower_id': tower.get('tower_id'),
                'severity': 'warning',
                'reason': f"CPU: {avg_cpu:.1f}%, Latency: {avg_latency:.1f}ms",
            })
        else:
            healthy += 1
    
    total = len(tower_metrics)
    
    if critical > 0:
        status = 'critical'
    elif warning > 0:
        status = 'degraded'
    else:
        status = 'healthy'
    
    return {
        'status': status,
        'total_towers': total,
        'healthy_towers': healthy,
        'warning_towers': warning,
        'critical_towers': critical,
        'avg_cpu': total_cpu / total if total > 0 else 0,
        'avg_latency': total_latency / total if total > 0 else 0,
        'avg_bandwidth': total_bandwidth / total if total > 0 else 0,
        'total_users': total_users,
        'issues': issues,
    }


def assess_tower_health(metrics: dict) -> dict:
    """Assess health status of a single tower based on its metrics."""
    indicators = {}
    issues = []
    
    # CPU check
    cpu = float(metrics.get('cpu_util_pct', 0))
    if cpu > THRESHOLDS['cpu_critical']:
        indicators['cpu'] = 'critical'
        issues.append({'type': 'HIGH_CPU', 'severity': 'critical', 'value': cpu})
    elif cpu > THRESHOLDS['cpu_warning']:
        indicators['cpu'] = 'warning'
        issues.append({'type': 'HIGH_CPU', 'severity': 'warning', 'value': cpu})
    else:
        indicators['cpu'] = 'healthy'
    
    # Latency check
    latency = float(metrics.get('latency_ms', 0))
    if latency > THRESHOLDS['latency_critical']:
        indicators['latency'] = 'critical'
        issues.append({'type': 'HIGH_LATENCY', 'severity': 'critical', 'value': latency})
    elif latency > THRESHOLDS['latency_warning']:
        indicators['latency'] = 'warning'
        issues.append({'type': 'HIGH_LATENCY', 'severity': 'warning', 'value': latency})
    else:
        indicators['latency'] = 'healthy'
    
    # Utilization check
    users = int(metrics.get('connected_users', 0))
    capacity = int(metrics.get('capacity_users', 1000))
    utilization = (users / capacity) * 100 if capacity > 0 else 0
    
    if utilization > THRESHOLDS['utilization_critical']:
        indicators['utilization'] = 'critical'
        issues.append({'type': 'NEAR_CAPACITY', 'severity': 'critical', 'value': utilization})
    elif utilization > THRESHOLDS['utilization_warning']:
        indicators['utilization'] = 'warning'
        issues.append({'type': 'HIGH_UTILIZATION', 'severity': 'warning', 'value': utilization})
    else:
        indicators['utilization'] = 'healthy'
    
    # Packet loss check
    packet_loss = float(metrics.get('packet_loss_pct', 0))
    if packet_loss > THRESHOLDS['packet_loss_critical']:
        indicators['packet_loss'] = 'critical'
        issues.append({'type': 'HIGH_PACKET_LOSS', 'severity': 'critical', 'value': packet_loss})
    elif packet_loss > THRESHOLDS['packet_loss_warning']:
        indicators['packet_loss'] = 'warning'
        issues.append({'type': 'PACKET_LOSS', 'severity': 'warning', 'value': packet_loss})
    else:
        indicators['packet_loss'] = 'healthy'
    
    # Determine overall status
    if any(v == 'critical' for v in indicators.values()):
        status = 'critical'
    elif any(v == 'warning' for v in indicators.values()):
        status = 'warning'
    else:
        status = 'healthy'
    
    return {
        'status': status,
        'indicators': indicators,
        'issues': issues,
    }


def get_all_agent_statuses() -> dict:
    """Get summary of all agent statuses from DynamoDB."""
    try:
        table = dynamodb.Table(AGENT_STATE_TABLE)
        response = table.scan()
        
        items = response.get('Items', [])
        
        active = sum(1 for item in items if item.get('status') == 'active')
        inactive = sum(1 for item in items if item.get('status') == 'inactive')
        error = sum(1 for item in items if item.get('status') == 'error')
        
        return {
            'total': len(items),
            'active': active,
            'inactive': inactive,
            'error': error,
        }
    except Exception as e:
        return {
            'total': 0,
            'active': 0,
            'inactive': 0,
            'error': 0,
            'query_error': str(e),
        }


def get_tower_config(tower_id: str) -> dict:
    """Get tower configuration from DynamoDB."""
    try:
        table = dynamodb.Table(TOWER_CONFIG_TABLE)
        response = table.get_item(Key={'tower_id': tower_id})
        
        if 'Item' in response:
            return {
                'region': response['Item'].get('region'),
                'capacity': int(response['Item'].get('capacity', 1000)),
                'latitude': float(response['Item'].get('latitude', 0)),
                'longitude': float(response['Item'].get('longitude', 0)),
                'trx_count': int(response['Item'].get('trx_count', 8)),
                'power_mode': response['Item'].get('power_mode', 'normal'),
            }
    except:
        pass
    
    return {}


def get_fallback_health_status(error_message: str) -> dict:
    """Return fallback health status when Timestream is unavailable."""
    return {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'overall_status': 'initializing',
        'message': 'Real-time data source not yet available',
        'error': error_message,
        'components': {
            'towers': {'total': 0, 'healthy': 0, 'warning': 0, 'critical': 0},
            'agents': {'total': 0, 'active': 0, 'inactive': 0, 'error': 0},
        },
        'metrics': {
            'avg_cpu_usage': 0,
            'avg_latency_ms': 0,
            'total_users': 0,
            'avg_bandwidth_utilization': 0,
        },
        'issues': [],
        'data_source': 'fallback',
        'suggestion': 'Ensure Timestream database is created and telemetry is being ingested',
    }


def format_bedrock_response(result: dict) -> dict:
    """Format response for Bedrock action group."""
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'health-monitor',
            'function': 'check_system_health',
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps(result, cls=DecimalEncoder)
                    }
                }
            }
        }
    }
