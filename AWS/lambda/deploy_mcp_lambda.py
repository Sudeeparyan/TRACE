"""
Deploy MCP Lambda Function to AWS

This script creates or updates the TRACE MCP Tools Lambda function.
Run this after setting up AWS credentials.
"""

import boto3
import zipfile
import io
import json
import os

# AWS Configuration
REGION = 'us-east-1'
FUNCTION_NAME = 'trace-mcp-tools'
RUNTIME = 'python3.12'
HANDLER = 'mcp_tools_lambda.lambda_handler'
TIMEOUT = 30
MEMORY_SIZE = 256

# Initialize AWS clients
lambda_client = boto3.client('lambda', region_name=REGION)
iam_client = boto3.client('iam', region_name=REGION)


def create_lambda_role():
    """Create IAM role for Lambda execution"""
    role_name = 'trace-mcp-lambda-role'
    
    assume_role_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    })
    
    try:
        # Check if role exists
        response = iam_client.get_role(RoleName=role_name)
        print(f"✅ Using existing role: {role_name}")
        return response['Role']['Arn']
    except iam_client.exceptions.NoSuchEntityException:
        # Create role
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=assume_role_policy,
            Description='Role for TRACE MCP Lambda function'
        )
        role_arn = response['Role']['Arn']
        
        # Attach necessary policies
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
        ]
        
        for policy in policies:
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy
            )
        
        print(f"✅ Created new role: {role_name}")
        
        # Wait for role to propagate
        import time
        print("⏳ Waiting for role to propagate...")
        time.sleep(10)
        
        return role_arn


def create_deployment_package():
    """Create ZIP file for Lambda deployment"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add main Lambda handler
        script_dir = os.path.dirname(os.path.abspath(__file__))
        lambda_file = os.path.join(script_dir, 'mcp_tools_lambda.py')
        
        if os.path.exists(lambda_file):
            zip_file.write(lambda_file, 'mcp_tools_lambda.py')
        else:
            print(f"❌ Lambda file not found: {lambda_file}")
            return None
    
    zip_buffer.seek(0)
    return zip_buffer.read()


def deploy_lambda():
    """Deploy or update the Lambda function"""
    print("🚀 Deploying TRACE MCP Lambda Function...")
    
    # Create IAM role
    role_arn = create_lambda_role()
    
    # Create deployment package
    print("📦 Creating deployment package...")
    zip_bytes = create_deployment_package()
    
    if not zip_bytes:
        return
    
    try:
        # Try to update existing function
        response = lambda_client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ZipFile=zip_bytes
        )
        print(f"✅ Updated Lambda function: {FUNCTION_NAME}")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        response = lambda_client.create_function(
            FunctionName=FUNCTION_NAME,
            Runtime=RUNTIME,
            Role=role_arn,
            Handler=HANDLER,
            Code={'ZipFile': zip_bytes},
            Timeout=TIMEOUT,
            MemorySize=MEMORY_SIZE,
            Description='TRACE MCP Tools - Telemetry, Energy, Config, and Policy tools',
            Environment={
                'Variables': {
                    'TRACE_ENVIRONMENT': 'production'
                }
            },
            Tags={
                'Project': 'TRACE',
                'Component': 'MCP-Tools'
            }
        )
        print(f"✅ Created Lambda function: {FUNCTION_NAME}")
    
    print(f"\n🎉 Deployment complete!")
    print(f"   Function ARN: {response['FunctionArn']}")
    return response


def test_lambda():
    """Test the Lambda function"""
    print("\n🧪 Testing Lambda function...")
    
    test_cases = [
        {
            "name": "Get Network Health",
            "payload": {"tool": "get_network_health_summary", "parameters": {}}
        },
        {
            "name": "Get Tower Telemetry",
            "payload": {"tool": "get_tower_telemetry", "parameters": {"tower_id": "tower-001"}}
        },
        {
            "name": "Get Energy Recommendations",
            "payload": {"tool": "get_energy_recommendations", "parameters": {}}
        },
        {
            "name": "Get Policy",
            "payload": {"tool": "get_policy", "parameters": {"issue_type": "HIGH_CPU"}}
        }
    ]
    
    for test in test_cases:
        try:
            response = lambda_client.invoke(
                FunctionName=FUNCTION_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(test["payload"])
            )
            
            result = json.loads(response['Payload'].read().decode('utf-8'))
            status = "✅" if result.get('statusCode') == 200 else "❌"
            print(f"   {status} {test['name']}")
            
        except Exception as e:
            print(f"   ❌ {test['name']}: {e}")


if __name__ == '__main__':
    deploy_lambda()
    test_lambda()
