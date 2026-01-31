#!/usr/bin/env python3
"""
TRACE API Gateway Deployment Script

Creates:
1. REST API - For synchronous agent interactions
2. WebSocket API - For real-time telemetry streaming
3. Custom domain configuration
4. API Keys and usage plans
"""

import boto3
import json
import os
import sys
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_config

# Configuration
CONFIG = get_config()
ENVIRONMENT = CONFIG['environment']
REGION = os.getenv('AWS_REGION', 'us-east-1')

# Initialize clients
apigateway = boto3.client('apigateway', region_name=REGION)
apigatewayv2 = boto3.client('apigatewayv2', region_name=REGION)  # For WebSocket/HTTP APIs
lambda_client = boto3.client('lambda', region_name=REGION)
iam = boto3.client('iam', region_name=REGION)
sts = boto3.client('sts', region_name=REGION)

ACCOUNT_ID = sts.get_caller_identity()['Account']


# ============================================================
# OpenAPI Specification for REST API
# ============================================================
def get_openapi_spec():
    """Generate OpenAPI specification for TRACE API."""
    return {
        "openapi": "3.0.1",
        "info": {
            "title": f"TRACE API - {ENVIRONMENT}",
            "description": "Traffic & Resource Agentic Control Engine API",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": f"https://{{api_id}}.execute-api.{REGION}.amazonaws.com/{ENVIRONMENT}",
                "description": f"TRACE API - {ENVIRONMENT} environment"
            }
        ],
        "paths": {
            "/agent/chat": {
                "post": {
                    "summary": "Chat with TRACE Principal Agent",
                    "operationId": "agentChat",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["message"],
                                    "properties": {
                                        "message": {"type": "string", "description": "User message"},
                                        "session_id": {"type": "string", "description": "Session ID for context"},
                                        "context": {"type": "object", "description": "Additional context"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Agent response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "response": {"type": "string"},
                                            "actions_taken": {"type": "array", "items": {"type": "object"}},
                                            "session_id": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "x-amazon-apigateway-integration": {
                        "type": "aws_proxy",
                        "httpMethod": "POST",
                        "uri": f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:TRACE-AgentAPI-{ENVIRONMENT}/invocations"
                    }
                }
            },
            "/health/system": {
                "get": {
                    "summary": "Get system-wide health status",
                    "operationId": "getSystemHealth",
                    "responses": {
                        "200": {
                            "description": "System health data"
                        }
                    },
                    "x-amazon-apigateway-integration": {
                        "type": "aws_proxy",
                        "httpMethod": "POST",
                        "uri": f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:TRACE-HealthMonitor-{ENVIRONMENT}/invocations"
                    }
                }
            },
            "/health/region/{regionId}": {
                "get": {
                    "summary": "Get regional health status",
                    "operationId": "getRegionHealth",
                    "parameters": [
                        {
                            "name": "regionId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Regional health data"}
                    },
                    "x-amazon-apigateway-integration": {
                        "type": "aws_proxy",
                        "httpMethod": "POST",
                        "uri": f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:TRACE-HealthMonitor-{ENVIRONMENT}/invocations"
                    }
                }
            },
            "/health/tower/{towerId}": {
                "get": {
                    "summary": "Get tower health status",
                    "operationId": "getTowerHealth",
                    "parameters": [
                        {
                            "name": "towerId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Tower health data"}
                    },
                    "x-amazon-apigateway-integration": {
                        "type": "aws_proxy",
                        "httpMethod": "POST",
                        "uri": f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:TRACE-HealthMonitor-{ENVIRONMENT}/invocations"
                    }
                }
            },
            "/telemetry/history": {
                "get": {
                    "summary": "Get telemetry history",
                    "operationId": "getTelemetryHistory",
                    "parameters": [
                        {"name": "tower_id", "in": "query", "schema": {"type": "string"}},
                        {"name": "metric", "in": "query", "schema": {"type": "string"}},
                        {"name": "period", "in": "query", "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {"description": "Telemetry history data"}
                    },
                    "x-amazon-apigateway-integration": {
                        "type": "aws_proxy",
                        "httpMethod": "POST",
                        "uri": f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:TRACE-Analytics-{ENVIRONMENT}/invocations"
                    }
                }
            },
            "/remediate": {
                "post": {
                    "summary": "Execute remediation action",
                    "operationId": "executeRemediation",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["action", "tower_id"],
                                    "properties": {
                                        "action": {"type": "string"},
                                        "tower_id": {"type": "string"},
                                        "parameters": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Remediation result"}
                    },
                    "x-amazon-apigateway-integration": {
                        "type": "aws_proxy",
                        "httpMethod": "POST",
                        "uri": f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:TRACE-Remediation-{ENVIRONMENT}/invocations"
                    }
                }
            },
            "/alerts": {
                "get": {
                    "summary": "Get active alerts",
                    "operationId": "getAlerts",
                    "parameters": [
                        {"name": "severity", "in": "query", "schema": {"type": "string"}},
                        {"name": "region", "in": "query", "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {"description": "Active alerts"}
                    },
                    "x-amazon-apigateway-integration": {
                        "type": "aws_proxy",
                        "httpMethod": "POST",
                        "uri": f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:TRACE-HealthMonitor-{ENVIRONMENT}/invocations"
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "x-api-key"
                }
            }
        },
        "security": [
            {"ApiKeyAuth": []}
        ]
    }


def create_api_role() -> str:
    """Create IAM role for API Gateway."""
    role_name = f"TRACE-APIGatewayRole-{ENVIRONMENT}"
    print(f"  Creating IAM role: {role_name}")
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "apigateway.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="IAM role for TRACE API Gateway"
        )
        
        # Attach Lambda invoke policy
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
        )
        
        # Add Lambda invoke permission
        lambda_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "lambda:InvokeFunction",
                    "Resource": f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:TRACE-*"
                }
            ]
        }
        
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=f"{role_name}-lambda",
            PolicyDocument=json.dumps(lambda_policy)
        )
        
        print(f"  ✅ Role created")
        
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"  ℹ️  Role already exists")
    
    return f"arn:aws:iam::{ACCOUNT_ID}:role/{role_name}"


def create_rest_api() -> dict:
    """Create REST API for TRACE."""
    api_name = f"TRACE-API-{ENVIRONMENT}"
    print(f"\n  Creating REST API: {api_name}")
    
    # Check if API exists
    existing_apis = apigateway.get_rest_apis()
    for api in existing_apis['items']:
        if api['name'] == api_name:
            print(f"  ℹ️  API already exists: {api['id']}")
            return api
    
    # Create API
    response = apigateway.create_rest_api(
        name=api_name,
        description=f"TRACE API - {ENVIRONMENT}",
        endpointConfiguration={'types': ['REGIONAL']},
        tags={
            'Project': 'TRACE',
            'Environment': ENVIRONMENT
        }
    )
    
    api_id = response['id']
    print(f"  ✅ API created: {api_id}")
    
    return response


def create_api_resources(api_id: str, role_arn: str):
    """Create API resources and methods."""
    print("\n  Creating API resources...")
    
    # Get root resource
    resources = apigateway.get_resources(restApiId=api_id)
    root_id = None
    for resource in resources['items']:
        if resource['path'] == '/':
            root_id = resource['id']
            break
    
    # Define resource structure
    resource_tree = {
        '/agent': {
            '/chat': {'POST': f'TRACE-AgentAPI-{ENVIRONMENT}'}
        },
        '/health': {
            '/system': {'GET': f'TRACE-HealthMonitor-{ENVIRONMENT}'},
            '/region': {
                '/{regionId}': {'GET': f'TRACE-HealthMonitor-{ENVIRONMENT}'}
            },
            '/tower': {
                '/{towerId}': {'GET': f'TRACE-HealthMonitor-{ENVIRONMENT}'}
            }
        },
        '/telemetry': {
            '/history': {'GET': f'TRACE-Analytics-{ENVIRONMENT}'}
        },
        '/remediate': {'POST': f'TRACE-Remediation-{ENVIRONMENT}'},
        '/alerts': {'GET': f'TRACE-HealthMonitor-{ENVIRONMENT}'}
    }
    
    def create_resource_recursive(parent_id: str, path: str, config: dict, full_path: str = ''):
        """Recursively create resources and methods."""
        for key, value in config.items():
            if key.startswith('/'):
                # This is a sub-resource
                resource_path = key.lstrip('/')
                new_full_path = full_path + key
                
                # Check if resource exists
                existing = None
                resources = apigateway.get_resources(restApiId=api_id)
                for r in resources['items']:
                    if r['path'] == new_full_path:
                        existing = r
                        break
                
                if existing:
                    resource_id = existing['id']
                else:
                    try:
                        response = apigateway.create_resource(
                            restApiId=api_id,
                            parentId=parent_id,
                            pathPart=resource_path
                        )
                        resource_id = response['id']
                        print(f"    Created resource: {new_full_path}")
                    except apigateway.exceptions.ConflictException:
                        # Resource already exists, find it
                        resources = apigateway.get_resources(restApiId=api_id)
                        for r in resources['items']:
                            if r['path'] == new_full_path:
                                resource_id = r['id']
                                break
                
                # Recurse
                if isinstance(value, dict):
                    create_resource_recursive(resource_id, key, value, new_full_path)
            else:
                # This is a method
                http_method = key
                lambda_name = value
                
                try:
                    # Create method
                    apigateway.put_method(
                        restApiId=api_id,
                        resourceId=parent_id,
                        httpMethod=http_method,
                        authorizationType='NONE',
                        apiKeyRequired=True
                    )
                    
                    # Create Lambda integration
                    lambda_arn = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{lambda_name}"
                    
                    apigateway.put_integration(
                        restApiId=api_id,
                        resourceId=parent_id,
                        httpMethod=http_method,
                        type='AWS_PROXY',
                        integrationHttpMethod='POST',
                        uri=f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
                    )
                    
                    print(f"    Created method: {http_method} {full_path} -> {lambda_name}")
                    
                except apigateway.exceptions.ConflictException:
                    print(f"    ℹ️  Method already exists: {http_method} {full_path}")
    
    # Create resources
    create_resource_recursive(root_id, '', resource_tree)
    
    # Add CORS
    print("\n  Adding CORS configuration...")
    try:
        # This is simplified - in production you'd add OPTIONS methods
        pass
    except Exception as e:
        print(f"    ⚠️  CORS setup: {str(e)}")


def deploy_api(api_id: str) -> str:
    """Deploy API to a stage."""
    print(f"\n  Deploying API to stage: {ENVIRONMENT}")
    
    try:
        response = apigateway.create_deployment(
            restApiId=api_id,
            stageName=ENVIRONMENT,
            description=f"Deployment at {datetime.utcnow().isoformat()}"
        )
        
        print(f"  ✅ Deployed: {response['id']}")
        
        # Get invoke URL
        invoke_url = f"https://{api_id}.execute-api.{REGION}.amazonaws.com/{ENVIRONMENT}"
        return invoke_url
        
    except Exception as e:
        print(f"  ❌ Deployment failed: {str(e)}")
        return None


def create_api_key(api_id: str) -> dict:
    """Create API key for authentication."""
    key_name = f"TRACE-APIKey-{ENVIRONMENT}"
    print(f"\n  Creating API key: {key_name}")
    
    try:
        # Create API key
        key_response = apigateway.create_api_key(
            name=key_name,
            enabled=True,
            description=f"API key for TRACE {ENVIRONMENT}"
        )
        
        api_key_id = key_response['id']
        api_key_value = key_response['value']
        
        # Create usage plan
        plan_response = apigateway.create_usage_plan(
            name=f"TRACE-UsagePlan-{ENVIRONMENT}",
            description=f"Usage plan for TRACE {ENVIRONMENT}",
            throttle={
                'burstLimit': 100,
                'rateLimit': 50
            },
            quota={
                'limit': 10000,
                'period': 'DAY'
            },
            apiStages=[
                {
                    'apiId': api_id,
                    'stage': ENVIRONMENT
                }
            ]
        )
        
        # Associate key with plan
        apigateway.create_usage_plan_key(
            usagePlanId=plan_response['id'],
            keyId=api_key_id,
            keyType='API_KEY'
        )
        
        print(f"  ✅ API key created")
        print(f"    Key ID: {api_key_id}")
        print(f"    Key Value: {api_key_value[:10]}...{api_key_value[-5:]}")
        
        return {
            'keyId': api_key_id,
            'keyValue': api_key_value,
            'usagePlanId': plan_response['id']
        }
        
    except apigateway.exceptions.ConflictException:
        print(f"  ℹ️  API key already exists")
        return {'keyId': 'existing'}


def create_websocket_api() -> dict:
    """Create WebSocket API for real-time telemetry."""
    api_name = f"TRACE-WebSocket-{ENVIRONMENT}"
    print(f"\n  Creating WebSocket API: {api_name}")
    
    # Check if exists
    existing = apigatewayv2.get_apis()
    for api in existing.get('Items', []):
        if api['Name'] == api_name:
            print(f"  ℹ️  WebSocket API already exists: {api['ApiId']}")
            return api
    
    # Create WebSocket API
    response = apigatewayv2.create_api(
        Name=api_name,
        ProtocolType='WEBSOCKET',
        RouteSelectionExpression='$request.body.action',
        Description=f"TRACE WebSocket API - {ENVIRONMENT}",
        Tags={
            'Project': 'TRACE',
            'Environment': ENVIRONMENT
        }
    )
    
    api_id = response['ApiId']
    print(f"  ✅ WebSocket API created: {api_id}")
    
    # Create routes
    routes = ['$connect', '$disconnect', '$default', 'subscribe', 'unsubscribe']
    
    for route in routes:
        try:
            apigatewayv2.create_route(
                ApiId=api_id,
                RouteKey=route
            )
            print(f"    Created route: {route}")
        except Exception as e:
            print(f"    ⚠️  Route {route}: {str(e)}")
    
    # Deploy
    try:
        apigatewayv2.create_stage(
            ApiId=api_id,
            StageName=ENVIRONMENT,
            AutoDeploy=True
        )
        print(f"  ✅ Stage created: {ENVIRONMENT}")
    except Exception as e:
        print(f"  ⚠️  Stage: {str(e)}")
    
    ws_url = f"wss://{api_id}.execute-api.{REGION}.amazonaws.com/{ENVIRONMENT}"
    response['WebSocketUrl'] = ws_url
    
    return response


def add_lambda_permissions(api_id: str):
    """Add Lambda permissions for API Gateway to invoke functions."""
    print("\n  Adding Lambda permissions...")
    
    lambdas = [
        f'TRACE-HealthMonitor-{ENVIRONMENT}',
        f'TRACE-Remediation-{ENVIRONMENT}',
        f'TRACE-Analytics-{ENVIRONMENT}',
        f'TRACE-AgentAPI-{ENVIRONMENT}'
    ]
    
    for lambda_name in lambdas:
        try:
            lambda_client.add_permission(
                FunctionName=lambda_name,
                StatementId=f'apigateway-{api_id}-{ENVIRONMENT}',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{REGION}:{ACCOUNT_ID}:{api_id}/*'
            )
            print(f"    ✅ Permission added for {lambda_name}")
        except lambda_client.exceptions.ResourceConflictException:
            print(f"    ℹ️  Permission exists for {lambda_name}")
        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"    ⚠️  Lambda not found: {lambda_name}")


def save_api_config(rest_api: dict, ws_api: dict, api_key: dict, invoke_url: str):
    """Save API configuration to file."""
    config_file = os.path.join(
        os.path.dirname(__file__),
        f"api-config-{ENVIRONMENT}.json"
    )
    
    config = {
        'environment': ENVIRONMENT,
        'region': REGION,
        'deployedAt': datetime.utcnow().isoformat() + 'Z',
        'restApi': {
            'id': rest_api['id'],
            'name': rest_api['name'],
            'invokeUrl': invoke_url
        },
        'webSocketApi': {
            'id': ws_api.get('ApiId'),
            'url': ws_api.get('WebSocketUrl')
        },
        'apiKey': {
            'id': api_key.get('keyId'),
            'usagePlanId': api_key.get('usagePlanId')
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n📄 API configuration saved to: {config_file}")
    return config


def main():
    """Main deployment function."""
    print("=" * 60)
    print("  TRACE API Gateway Deployment")
    print("=" * 60)
    print(f"  Environment: {ENVIRONMENT}")
    print(f"  Region: {REGION}")
    print(f"  Account: {ACCOUNT_ID}")
    print("=" * 60)
    
    # Create IAM role
    role_arn = create_api_role()
    time.sleep(5)  # Wait for propagation
    
    # Create REST API
    rest_api = create_rest_api()
    
    # Create resources and methods
    create_api_resources(rest_api['id'], role_arn)
    
    # Deploy API
    invoke_url = deploy_api(rest_api['id'])
    
    # Create API key
    api_key = create_api_key(rest_api['id'])
    
    # Add Lambda permissions
    add_lambda_permissions(rest_api['id'])
    
    # Create WebSocket API
    ws_api = create_websocket_api()
    
    # Save configuration
    config = save_api_config(rest_api, ws_api, api_key, invoke_url)
    
    # Summary
    print("\n" + "=" * 60)
    print("  API GATEWAY DEPLOYMENT COMPLETE")
    print("=" * 60)
    print(f"\n  REST API URL: {invoke_url}")
    print(f"  WebSocket URL: {ws_api.get('WebSocketUrl')}")
    print(f"\n  API Key ID: {api_key.get('keyId')}")
    print("\n  ENDPOINTS:")
    print(f"    POST {invoke_url}/agent/chat")
    print(f"    GET  {invoke_url}/health/system")
    print(f"    GET  {invoke_url}/health/region/{{regionId}}")
    print(f"    GET  {invoke_url}/health/tower/{{towerId}}")
    print(f"    GET  {invoke_url}/telemetry/history")
    print(f"    POST {invoke_url}/remediate")
    print(f"    GET  {invoke_url}/alerts")
    print("\n  NEXT STEPS:")
    print("  1. Update frontend configuration with API URLs")
    print("  2. Store API key securely")
    print("  3. Test endpoints with Postman or curl")
    print("=" * 60)


if __name__ == '__main__':
    main()
