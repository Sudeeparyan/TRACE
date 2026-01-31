#!/usr/bin/env python3
"""
TRACE Step Functions Deployment Script

Deploys Step Functions state machines:
1. Self-Healing Workflow - Automated remediation
2. Energy Optimization Workflow - Power management
3. Congestion Management Workflow - Traffic distribution
"""

import boto3
import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_config

# Configuration
CONFIG = get_config()
ENVIRONMENT = CONFIG['environment']
REGION = os.getenv('AWS_REGION', 'us-east-1')
SCRIPT_DIR = Path(__file__).parent

# Initialize clients
sfn = boto3.client('stepfunctions', region_name=REGION)
iam = boto3.client('iam', region_name=REGION)
sts = boto3.client('sts', region_name=REGION)

# Get account ID
ACCOUNT_ID = sts.get_caller_identity()['Account']


def replace_placeholders(template: str) -> str:
    """Replace placeholders in workflow definition."""
    return template.replace(
        '${AWS_REGION}', REGION
    ).replace(
        '${AWS_ACCOUNT_ID}', ACCOUNT_ID
    ).replace(
        '${ENVIRONMENT}', ENVIRONMENT
    )


def create_sfn_role(role_name: str) -> str:
    """Create IAM role for Step Functions."""
    print(f"  Creating IAM role: {role_name}")
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "states.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Comprehensive permissions for Step Functions
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "lambda:InvokeFunction"
                ],
                "Resource": f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:TRACE-*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "sns:Publish"
                ],
                "Resource": f"arn:aws:sns:{REGION}:{ACCOUNT_ID}:TRACE-*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "sqs:SendMessage"
                ],
                "Resource": f"arn:aws:sqs:{REGION}:{ACCOUNT_ID}:TRACE-*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:Query"
                ],
                "Resource": f"arn:aws:dynamodb:{REGION}:{ACCOUNT_ID}:table/TRACE-*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ssm:CreateOpsItem"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:CreateLogDelivery",
                    "logs:GetLogDelivery",
                    "logs:UpdateLogDelivery",
                    "logs:DeleteLogDelivery",
                    "logs:ListLogDeliveries",
                    "logs:PutResourcePolicy",
                    "logs:DescribeResourcePolicies",
                    "logs:DescribeLogGroups"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets"
                ],
                "Resource": "*"
            }
        ]
    }
    
    try:
        # Create role
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="IAM role for TRACE Step Functions"
        )
        
        # Attach inline policy
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=f"{role_name}-policy",
            PolicyDocument=json.dumps(permissions_policy)
        )
        
        role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
        print(f"  ✅ Role created: {role_arn}")
        return role_arn
        
    except iam.exceptions.EntityAlreadyExistsException:
        role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"
        print(f"  ℹ️  Role already exists: {role_arn}")
        return role_arn


def deploy_state_machine(name: str, definition_file: str, role_arn: str) -> dict:
    """Deploy a Step Functions state machine."""
    print(f"\n  Deploying: {name}")
    
    # Load and process definition
    definition_path = SCRIPT_DIR / definition_file
    with open(definition_path, 'r') as f:
        definition = f.read()
    
    definition = replace_placeholders(definition)
    
    # Validate JSON
    try:
        json.loads(definition)
    except json.JSONDecodeError as e:
        print(f"  ❌ Invalid JSON in {definition_file}: {str(e)}")
        raise
    
    state_machine_arn = f"arn:aws:states:{REGION}:{ACCOUNT_ID}:stateMachine:{name}"
    
    try:
        # Try to update existing
        response = sfn.update_state_machine(
            stateMachineArn=state_machine_arn,
            definition=definition,
            roleArn=role_arn,
            loggingConfiguration={
                'level': 'ALL',
                'includeExecutionData': True,
                'destinations': [
                    {
                        'cloudWatchLogsLogGroup': {
                            'logGroupArn': f"arn:aws:logs:{REGION}:{ACCOUNT_ID}:log-group:/aws/vendedlogs/states/{name}:*"
                        }
                    }
                ]
            },
            tracingConfiguration={
                'enabled': True
            }
        )
        print(f"  ✅ Updated: {state_machine_arn}")
        return {'stateMachineArn': state_machine_arn, 'action': 'updated'}
        
    except sfn.exceptions.StateMachineDoesNotExist:
        # Create new
        response = sfn.create_state_machine(
            name=name,
            definition=definition,
            roleArn=role_arn,
            type='STANDARD',
            loggingConfiguration={
                'level': 'ALL',
                'includeExecutionData': True,
                'destinations': [
                    {
                        'cloudWatchLogsLogGroup': {
                            'logGroupArn': f"arn:aws:logs:{REGION}:{ACCOUNT_ID}:log-group:/aws/vendedlogs/states/{name}:*"
                        }
                    }
                ]
            },
            tracingConfiguration={
                'enabled': True
            },
            tags=[
                {'key': 'Project', 'value': 'TRACE'},
                {'key': 'Environment', 'value': ENVIRONMENT}
            ]
        )
        print(f"  ✅ Created: {response['stateMachineArn']}")
        return {'stateMachineArn': response['stateMachineArn'], 'action': 'created'}


def create_eventbridge_rules():
    """Create EventBridge rules to trigger workflows."""
    print("\n  Creating EventBridge rules...")
    
    events = boto3.client('events', region_name=REGION)
    
    # Energy optimization - runs every hour
    try:
        events.put_rule(
            Name=f"TRACE-EnergyOptimization-Schedule-{ENVIRONMENT}",
            ScheduleExpression="rate(1 hour)",
            State="ENABLED",
            Description="Triggers energy optimization workflow every hour"
        )
        
        # Add target for each region
        for region_name in ['north', 'south', 'east', 'west', 'central']:
            events.put_targets(
                Rule=f"TRACE-EnergyOptimization-Schedule-{ENVIRONMENT}",
                Targets=[
                    {
                        'Id': f"energy-opt-{region_name}",
                        'Arn': f"arn:aws:states:{REGION}:{ACCOUNT_ID}:stateMachine:TRACE-EnergyOptimization-{ENVIRONMENT}",
                        'RoleArn': f"arn:aws:iam::{ACCOUNT_ID}:role/TRACE-EventBridgeRole-{ENVIRONMENT}",
                        'Input': json.dumps({'region': region_name})
                    }
                ]
            )
        
        print(f"  ✅ Energy optimization schedule created (hourly)")
    except Exception as e:
        print(f"  ⚠️  EventBridge rule creation failed: {str(e)}")
    
    # Self-healing trigger from CloudWatch Alarms
    try:
        events.put_rule(
            Name=f"TRACE-SelfHealing-Trigger-{ENVIRONMENT}",
            EventPattern=json.dumps({
                "source": ["aws.cloudwatch"],
                "detail-type": ["CloudWatch Alarm State Change"],
                "detail": {
                    "state": {"value": ["ALARM"]},
                    "alarmName": [{"prefix": "TRACE-"}]
                }
            }),
            State="ENABLED",
            Description="Triggers self-healing on CloudWatch alarm"
        )
        print(f"  ✅ Self-healing trigger created (CloudWatch alarms)")
    except Exception as e:
        print(f"  ⚠️  Self-healing trigger creation failed: {str(e)}")


def main():
    """Main deployment function."""
    print("=" * 60)
    print("  TRACE Step Functions Deployment")
    print("=" * 60)
    print(f"  Environment: {ENVIRONMENT}")
    print(f"  Region: {REGION}")
    print(f"  Account: {ACCOUNT_ID}")
    print("=" * 60)
    
    # Create IAM role
    role_name = f"TRACE-StepFunctionsRole-{ENVIRONMENT}"
    role_arn = create_sfn_role(role_name)
    
    # Wait for role propagation
    print("  Waiting for IAM role propagation...")
    import time
    time.sleep(10)
    
    # Workflows to deploy
    workflows = [
        (f"TRACE-SelfHealing-{ENVIRONMENT}", "self-healing-workflow.json"),
        (f"TRACE-EnergyOptimization-{ENVIRONMENT}", "energy-optimization-workflow.json"),
    ]
    
    results = []
    for name, definition_file in workflows:
        try:
            result = deploy_state_machine(name, definition_file, role_arn)
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ Failed to deploy {name}: {str(e)}")
            results.append((name, {'error': str(e)}))
    
    # Create EventBridge rules
    create_eventbridge_rules()
    
    # Summary
    print("\n" + "=" * 60)
    print("  DEPLOYMENT SUMMARY")
    print("=" * 60)
    
    for name, result in results:
        status = result.get('action', 'failed')
        arn = result.get('stateMachineArn', 'N/A')
        print(f"  {name}: {status}")
        if arn != 'N/A':
            print(f"    ARN: {arn}")
    
    print("\n  NEXT STEPS:")
    print("  1. Test self-healing workflow with a sample alert")
    print("  2. Verify energy optimization runs on schedule")
    print("  3. Monitor executions in Step Functions console")
    print("=" * 60)


if __name__ == '__main__':
    main()
