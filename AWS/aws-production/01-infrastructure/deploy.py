#!/usr/bin/env python3
"""
TRACE AWS Infrastructure Deployment Script

Deploys all foundational AWS infrastructure for TRACE production:
- DynamoDB tables
- Timestream database and tables
- S3 buckets
- IAM roles and policies
- Kinesis streams
- IoT Core resources
- SNS topics
- CloudWatch dashboards

Run this script FIRST before deploying Lambda functions or Bedrock agents.
"""

import boto3
import json
import time
import os
from datetime import datetime

# Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'production')
REGION = os.getenv('AWS_REGION', 'us-east-1')

# Initialize clients
dynamodb = boto3.client('dynamodb', region_name=REGION)
timestream_write = boto3.client('timestream-write', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
iam = boto3.client('iam', region_name=REGION)
kinesis = boto3.client('kinesis', region_name=REGION)
iot = boto3.client('iot', region_name=REGION)
sns = boto3.client('sns', region_name=REGION)
cloudwatch = boto3.client('cloudwatch', region_name=REGION)
sts = boto3.client('sts', region_name=REGION)


def get_account_id():
    return sts.get_caller_identity()['Account']


def print_step(message: str):
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}")


def create_dynamodb_tables():
    """Create all DynamoDB tables for TRACE."""
    print_step("Creating DynamoDB Tables")
    
    tables = [
        {
            'name': f'TRACE-TowerConfig-{ENVIRONMENT}',
            'key_schema': [
                {'AttributeName': 'tower_id', 'KeyType': 'HASH'}
            ],
            'attributes': [
                {'AttributeName': 'tower_id', 'AttributeType': 'S'}
            ],
        },
        {
            'name': f'TRACE-AgentState-{ENVIRONMENT}',
            'key_schema': [
                {'AttributeName': 'agent_id', 'KeyType': 'HASH'}
            ],
            'attributes': [
                {'AttributeName': 'agent_id', 'AttributeType': 'S'}
            ],
        },
        {
            'name': f'TRACE-RemediationLog-{ENVIRONMENT}',
            'key_schema': [
                {'AttributeName': 'remediation_id', 'KeyType': 'HASH'}
            ],
            'attributes': [
                {'AttributeName': 'remediation_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'},
            ],
            'gsi': [
                {
                    'IndexName': 'timestamp-index',
                    'KeySchema': [
                        {'AttributeName': 'timestamp', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                }
            ]
        },
        {
            'name': f'TRACE-TelemetryAggregates-{ENVIRONMENT}',
            'key_schema': [
                {'AttributeName': 'tower_id', 'KeyType': 'HASH'},
                {'AttributeName': 'time_bucket', 'KeyType': 'RANGE'}
            ],
            'attributes': [
                {'AttributeName': 'tower_id', 'AttributeType': 'S'},
                {'AttributeName': 'time_bucket', 'AttributeType': 'S'}
            ],
        },
        {
            'name': f'TRACE-Policies-{ENVIRONMENT}',
            'key_schema': [
                {'AttributeName': 'policy_id', 'KeyType': 'HASH'}
            ],
            'attributes': [
                {'AttributeName': 'policy_id', 'AttributeType': 'S'}
            ],
        },
    ]
    
    for table_config in tables:
        table_name = table_config['name']
        try:
            # Check if table exists
            dynamodb.describe_table(TableName=table_name)
            print(f"  ✓ Table {table_name} already exists")
        except dynamodb.exceptions.ResourceNotFoundException:
            # Create table
            create_params = {
                'TableName': table_name,
                'KeySchema': table_config['key_schema'],
                'AttributeDefinitions': table_config['attributes'],
                'BillingMode': 'PAY_PER_REQUEST',
                'Tags': [
                    {'Key': 'Project', 'Value': 'TRACE'},
                    {'Key': 'Environment', 'Value': ENVIRONMENT},
                ]
            }
            
            if 'gsi' in table_config:
                create_params['GlobalSecondaryIndexes'] = table_config['gsi']
                for gsi in table_config['gsi']:
                    gsi['ProvisionedThroughput'] = {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            
            dynamodb.create_table(**create_params)
            print(f"  ✓ Created table {table_name}")
            
            # Wait for table to be active
            waiter = dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
    
    # Seed tower configuration
    seed_tower_config()


def seed_tower_config():
    """Seed initial tower configuration data."""
    print("  Seeding tower configuration...")
    
    ddb_resource = boto3.resource('dynamodb', region_name=REGION)
    table = ddb_resource.Table(f'TRACE-TowerConfig-{ENVIRONMENT}')
    
    towers = [
        {'tower_id': 'TX001', 'region_id': 'R-N', 'latitude': '40.7128', 'longitude': '-74.0060', 
         'capacity': 1000, 'total_trx': 8, 'active_trx': 8, 'power_mode': 'normal', 'min_trx': 2},
        {'tower_id': 'TX002', 'region_id': 'R-N', 'latitude': '40.7580', 'longitude': '-73.9855',
         'capacity': 1200, 'total_trx': 8, 'active_trx': 8, 'power_mode': 'normal', 'min_trx': 2},
        {'tower_id': 'TX003', 'region_id': 'R-S', 'latitude': '33.7490', 'longitude': '-84.3880',
         'capacity': 800, 'total_trx': 6, 'active_trx': 6, 'power_mode': 'normal', 'min_trx': 2},
        {'tower_id': 'TX004', 'region_id': 'R-S', 'latitude': '29.7604', 'longitude': '-95.3698',
         'capacity': 1500, 'total_trx': 10, 'active_trx': 10, 'power_mode': 'normal', 'min_trx': 2},
        {'tower_id': 'TX005', 'region_id': 'R-E', 'latitude': '42.3601', 'longitude': '-71.0589',
         'capacity': 1000, 'total_trx': 8, 'active_trx': 8, 'power_mode': 'normal', 'min_trx': 2},
        {'tower_id': 'TX006', 'region_id': 'R-E', 'latitude': '39.9526', 'longitude': '-75.1652',
         'capacity': 900, 'total_trx': 6, 'active_trx': 6, 'power_mode': 'normal', 'min_trx': 2},
        {'tower_id': 'TX007', 'region_id': 'R-W', 'latitude': '34.0522', 'longitude': '-118.2437',
         'capacity': 2000, 'total_trx': 12, 'active_trx': 12, 'power_mode': 'normal', 'min_trx': 3},
        {'tower_id': 'TX008', 'region_id': 'R-W', 'latitude': '37.7749', 'longitude': '-122.4194',
         'capacity': 1800, 'total_trx': 10, 'active_trx': 10, 'power_mode': 'normal', 'min_trx': 2},
        {'tower_id': 'TX009', 'region_id': 'R-C', 'latitude': '41.8781', 'longitude': '-87.6298',
         'capacity': 1400, 'total_trx': 8, 'active_trx': 8, 'power_mode': 'normal', 'min_trx': 2},
        {'tower_id': 'TX010', 'region_id': 'R-C', 'latitude': '39.7392', 'longitude': '-104.9903',
         'capacity': 1100, 'total_trx': 8, 'active_trx': 8, 'power_mode': 'normal', 'min_trx': 2},
    ]
    
    with table.batch_writer() as batch:
        for tower in towers:
            tower['created_at'] = datetime.utcnow().isoformat() + 'Z'
            batch.put_item(Item=tower)
    
    print(f"  ✓ Seeded {len(towers)} tower configurations")


def create_timestream_resources():
    """Create Timestream database and tables."""
    print_step("Creating Timestream Resources")
    
    database_name = f'TRACE-Telemetry-{ENVIRONMENT}'
    
    # Create database
    try:
        timestream_write.describe_database(DatabaseName=database_name)
        print(f"  ✓ Database {database_name} already exists")
    except timestream_write.exceptions.ResourceNotFoundException:
        timestream_write.create_database(
            DatabaseName=database_name,
            Tags=[
                {'Key': 'Project', 'Value': 'TRACE'},
                {'Key': 'Environment', 'Value': ENVIRONMENT},
            ]
        )
        print(f"  ✓ Created database {database_name}")
    
    # Create tables
    tables = [
        {
            'name': 'TowerMetrics',
            'retention': {
                'MemoryStoreRetentionPeriodInHours': 24,
                'MagneticStoreRetentionPeriodInDays': 365,
            }
        },
        {
            'name': 'AgentMetrics',
            'retention': {
                'MemoryStoreRetentionPeriodInHours': 24,
                'MagneticStoreRetentionPeriodInDays': 90,
            }
        },
    ]
    
    for table_config in tables:
        table_name = table_config['name']
        try:
            timestream_write.describe_table(
                DatabaseName=database_name,
                TableName=table_name
            )
            print(f"  ✓ Table {table_name} already exists")
        except timestream_write.exceptions.ResourceNotFoundException:
            timestream_write.create_table(
                DatabaseName=database_name,
                TableName=table_name,
                RetentionProperties=table_config['retention'],
                Tags=[
                    {'Key': 'Project', 'Value': 'TRACE'},
                    {'Key': 'Environment', 'Value': ENVIRONMENT},
                ]
            )
            print(f"  ✓ Created table {table_name}")


def create_s3_buckets():
    """Create S3 buckets for TRACE."""
    print_step("Creating S3 Buckets")
    
    account_id = get_account_id()
    
    buckets = [
        f'trace-data-{ENVIRONMENT}-{account_id}',
        f'trace-models-{ENVIRONMENT}-{account_id}',
        f'trace-frontend-{ENVIRONMENT}-{account_id}',
    ]
    
    for bucket_name in buckets:
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"  ✓ Bucket {bucket_name} already exists")
        except:
            create_params = {'Bucket': bucket_name}
            if REGION != 'us-east-1':
                create_params['CreateBucketConfiguration'] = {
                    'LocationConstraint': REGION
                }
            
            s3.create_bucket(**create_params)
            
            # Enable versioning
            s3.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Add tags
            s3.put_bucket_tagging(
                Bucket=bucket_name,
                Tagging={
                    'TagSet': [
                        {'Key': 'Project', 'Value': 'TRACE'},
                        {'Key': 'Environment', 'Value': ENVIRONMENT},
                    ]
                }
            )
            
            print(f"  ✓ Created bucket {bucket_name}")


def create_kinesis_streams():
    """Create Kinesis Data Streams."""
    print_step("Creating Kinesis Streams")
    
    streams = [
        {
            'name': f'TRACE-TelemetryStream-{ENVIRONMENT}',
            'shard_count': 2,
        },
        {
            'name': f'TRACE-EventStream-{ENVIRONMENT}',
            'shard_count': 1,
        },
    ]
    
    for stream_config in streams:
        stream_name = stream_config['name']
        try:
            kinesis.describe_stream(StreamName=stream_name)
            print(f"  ✓ Stream {stream_name} already exists")
        except kinesis.exceptions.ResourceNotFoundException:
            kinesis.create_stream(
                StreamName=stream_name,
                ShardCount=stream_config['shard_count'],
                StreamModeDetails={'StreamMode': 'PROVISIONED'}
            )
            print(f"  ✓ Created stream {stream_name}")
            
            # Wait for stream to be active
            waiter = kinesis.get_waiter('stream_exists')
            waiter.wait(StreamName=stream_name)


def create_sns_topics():
    """Create SNS topics for alerts."""
    print_step("Creating SNS Topics")
    
    topics = [
        f'TRACE-Alerts-{ENVIRONMENT}',
        f'TRACE-CriticalAlerts-{ENVIRONMENT}',
    ]
    
    topic_arns = {}
    
    for topic_name in topics:
        response = sns.create_topic(
            Name=topic_name,
            Tags=[
                {'Key': 'Project', 'Value': 'TRACE'},
                {'Key': 'Environment', 'Value': ENVIRONMENT},
            ]
        )
        topic_arns[topic_name] = response['TopicArn']
        print(f"  ✓ Created/verified topic {topic_name}")
    
    return topic_arns


def create_iot_resources():
    """Create IoT Core resources."""
    print_step("Creating IoT Core Resources")
    
    thing_group_name = f'TRACE-Towers-{ENVIRONMENT}'
    
    # Create thing group
    try:
        iot.describe_thing_group(thingGroupName=thing_group_name)
        print(f"  ✓ Thing group {thing_group_name} already exists")
    except iot.exceptions.ResourceNotFoundException:
        iot.create_thing_group(
            thingGroupName=thing_group_name,
            thingGroupProperties={
                'thingGroupDescription': 'TRACE Tower IoT Things'
            },
            tags=[
                {'Key': 'Project', 'Value': 'TRACE'},
                {'Key': 'Environment', 'Value': ENVIRONMENT},
            ]
        )
        print(f"  ✓ Created thing group {thing_group_name}")
    
    # Create things for each tower
    towers = ['TX001', 'TX002', 'TX003', 'TX004', 'TX005', 
              'TX006', 'TX007', 'TX008', 'TX009', 'TX010']
    
    for tower_id in towers:
        thing_name = f'TRACE-Tower-{tower_id}'
        try:
            iot.describe_thing(thingName=thing_name)
        except iot.exceptions.ResourceNotFoundException:
            iot.create_thing(
                thingName=thing_name,
                thingTypeName='',
                attributePayload={
                    'attributes': {
                        'tower_id': tower_id,
                        'environment': ENVIRONMENT,
                    }
                }
            )
            
            # Add to thing group
            iot.add_thing_to_thing_group(
                thingGroupName=thing_group_name,
                thingName=thing_name
            )
    
    print(f"  ✓ Created/verified {len(towers)} IoT things")


def create_iam_roles():
    """Create IAM roles for TRACE services."""
    print_step("Creating IAM Roles")
    
    account_id = get_account_id()
    
    # Lambda execution role
    lambda_role_name = f'TRACE-Lambda-Role-{ENVIRONMENT}'
    
    lambda_trust_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {'Service': 'lambda.amazonaws.com'},
            'Action': 'sts:AssumeRole'
        }]
    }
    
    lambda_policy = {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Effect': 'Allow',
                'Action': [
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                    'logs:PutLogEvents'
                ],
                'Resource': 'arn:aws:logs:*:*:*'
            },
            {
                'Effect': 'Allow',
                'Action': [
                    'dynamodb:GetItem',
                    'dynamodb:PutItem',
                    'dynamodb:UpdateItem',
                    'dynamodb:DeleteItem',
                    'dynamodb:Query',
                    'dynamodb:Scan'
                ],
                'Resource': f'arn:aws:dynamodb:{REGION}:{account_id}:table/TRACE-*'
            },
            {
                'Effect': 'Allow',
                'Action': [
                    'timestream:WriteRecords',
                    'timestream:DescribeEndpoints',
                    'timestream:Select',
                    'timestream:SelectValues'
                ],
                'Resource': '*'
            },
            {
                'Effect': 'Allow',
                'Action': [
                    'kinesis:GetRecords',
                    'kinesis:GetShardIterator',
                    'kinesis:DescribeStream',
                    'kinesis:ListStreams'
                ],
                'Resource': f'arn:aws:kinesis:{REGION}:{account_id}:stream/TRACE-*'
            },
            {
                'Effect': 'Allow',
                'Action': [
                    'iot:Publish',
                    'iot:Subscribe',
                    'iot:Connect',
                    'iot:Receive'
                ],
                'Resource': '*'
            },
            {
                'Effect': 'Allow',
                'Action': [
                    'sns:Publish'
                ],
                'Resource': f'arn:aws:sns:{REGION}:{account_id}:TRACE-*'
            },
            {
                'Effect': 'Allow',
                'Action': [
                    'states:StartExecution'
                ],
                'Resource': f'arn:aws:states:{REGION}:{account_id}:stateMachine:TRACE-*'
            },
            {
                'Effect': 'Allow',
                'Action': [
                    'cloudwatch:PutMetricData'
                ],
                'Resource': '*'
            },
            {
                'Effect': 'Allow',
                'Action': [
                    'bedrock:InvokeModel',
                    'bedrock:InvokeModelWithResponseStream'
                ],
                'Resource': '*'
            }
        ]
    }
    
    try:
        iam.get_role(RoleName=lambda_role_name)
        print(f"  ✓ Role {lambda_role_name} already exists")
    except iam.exceptions.NoSuchEntityException:
        iam.create_role(
            RoleName=lambda_role_name,
            AssumeRolePolicyDocument=json.dumps(lambda_trust_policy),
            Description='TRACE Lambda execution role',
            Tags=[
                {'Key': 'Project', 'Value': 'TRACE'},
                {'Key': 'Environment', 'Value': ENVIRONMENT},
            ]
        )
        
        iam.put_role_policy(
            RoleName=lambda_role_name,
            PolicyName='TRACE-Lambda-Policy',
            PolicyDocument=json.dumps(lambda_policy)
        )
        
        print(f"  ✓ Created role {lambda_role_name}")
    
    # Bedrock Agent role
    agent_role_name = f'TRACE-BedrockAgent-Role-{ENVIRONMENT}'
    
    agent_trust_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {'Service': 'bedrock.amazonaws.com'},
            'Action': 'sts:AssumeRole'
        }]
    }
    
    agent_policy = {
        'Version': '2012-10-17',
        'Statement': [
            {
                'Effect': 'Allow',
                'Action': [
                    'bedrock:InvokeModel',
                    'bedrock:InvokeModelWithResponseStream'
                ],
                'Resource': '*'
            },
            {
                'Effect': 'Allow',
                'Action': [
                    'lambda:InvokeFunction'
                ],
                'Resource': f'arn:aws:lambda:{REGION}:{account_id}:function:TRACE-*'
            }
        ]
    }
    
    try:
        iam.get_role(RoleName=agent_role_name)
        print(f"  ✓ Role {agent_role_name} already exists")
    except iam.exceptions.NoSuchEntityException:
        iam.create_role(
            RoleName=agent_role_name,
            AssumeRolePolicyDocument=json.dumps(agent_trust_policy),
            Description='TRACE Bedrock Agent execution role',
            Tags=[
                {'Key': 'Project', 'Value': 'TRACE'},
                {'Key': 'Environment', 'Value': ENVIRONMENT},
            ]
        )
        
        iam.put_role_policy(
            RoleName=agent_role_name,
            PolicyName='TRACE-BedrockAgent-Policy',
            PolicyDocument=json.dumps(agent_policy)
        )
        
        print(f"  ✓ Created role {agent_role_name}")
    
    return {
        'lambda_role_arn': f'arn:aws:iam::{account_id}:role/{lambda_role_name}',
        'agent_role_arn': f'arn:aws:iam::{account_id}:role/{agent_role_name}',
    }


def save_outputs(outputs: dict):
    """Save deployment outputs to file."""
    output_file = os.path.join(os.path.dirname(__file__), '..', 'infrastructure-outputs.json')
    
    with open(output_file, 'w') as f:
        json.dump(outputs, f, indent=2)
    
    print(f"\n✓ Outputs saved to {output_file}")


def main():
    print("\n" + "="*60)
    print("  TRACE AWS Infrastructure Deployment")
    print("="*60)
    print(f"  Environment: {ENVIRONMENT}")
    print(f"  Region: {REGION}")
    print(f"  Account: {get_account_id()}")
    print("="*60)
    
    outputs = {
        'environment': ENVIRONMENT,
        'region': REGION,
        'account_id': get_account_id(),
        'deployed_at': datetime.utcnow().isoformat() + 'Z',
    }
    
    # Deploy all infrastructure
    create_dynamodb_tables()
    create_timestream_resources()
    create_s3_buckets()
    create_kinesis_streams()
    topic_arns = create_sns_topics()
    outputs['sns_topics'] = topic_arns
    create_iot_resources()
    role_arns = create_iam_roles()
    outputs['iam_roles'] = role_arns
    
    # Save outputs
    save_outputs(outputs)
    
    print("\n" + "="*60)
    print("  ✅ Infrastructure Deployment Complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Deploy Lambda functions: python 03-lambda-tools/deploy.py")
    print("  2. Deploy Bedrock agents: python 04-bedrock-agents/deploy.py")
    print("  3. Deploy Step Functions: python 05-step-functions/deploy.py")
    print("  4. Start telemetry simulation: python scripts/telemetry_simulator.py")


if __name__ == '__main__':
    main()
