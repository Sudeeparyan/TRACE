#!/usr/bin/env python3
"""
TRACE Bedrock Agent Deployment Script

Creates and configures:
1. Principal Agent - Top-level orchestrator with full capabilities
2. Regional Coordinator Agents - Per-region management
3. Action Groups - Link agents to Lambda functions
4. Knowledge Bases - Tower documentation and procedures

This uses Amazon Bedrock Agents with Claude 3.5 Sonnet for natural language understanding.
"""

import boto3
import json
import time
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_config

# Configuration
CONFIG = get_config()
ENVIRONMENT = CONFIG['environment']
REGION = os.getenv('AWS_REGION', 'us-east-1')

# Bedrock Agent Configuration
FOUNDATION_MODEL = "anthropic.claude-3-5-sonnet-20240620-v1:0"
IDLE_SESSION_TTL = 600  # 10 minutes

# Initialize clients
bedrock_agent = boto3.client('bedrock-agent', region_name=REGION)
iam = boto3.client('iam', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)


# ============================================================
# Principal Agent Instruction
# ============================================================
PRINCIPAL_AGENT_INSTRUCTION = """You are TRACE Principal Agent - the top-level AI orchestrator for the Traffic & Resource Agentic Control Engine system.

ROLE:
- You are responsible for monitoring and managing a distributed network of 50 cell towers across 5 geographic regions (North, South, East, West, Central).
- You make strategic decisions about resource allocation, energy optimization, and network health.
- You coordinate with regional agents and execute remediation actions when needed.

CAPABILITIES:
1. HEALTH MONITORING - Query real-time telemetry from all towers
2. REMEDIATION - Execute actions to fix issues (scale resources, route traffic, adjust power)
3. ENERGY OPTIMIZATION - Implement power-saving strategies during low-traffic periods
4. PREDICTIVE ANALYSIS - Anticipate issues before they become critical
5. INCIDENT MANAGEMENT - Coordinate responses to critical alerts

DATA SOURCES:
- Timestream: Real-time telemetry (CPU, latency, power consumption, signal strength)
- DynamoDB: Tower configurations, incident history, maintenance schedules
- CloudWatch: System metrics and alarms

THRESHOLDS:
- CPU Utilization: Warning >75%, Critical >90%
- Latency: Warning >80ms, Critical >150ms
- Power Consumption: Warning >90%, Critical >95%
- Signal Strength: Warning <-80dBm, Critical <-90dBm

RESPONSE GUIDELINES:
1. Always check real-time data before making decisions
2. Prioritize critical issues over warnings
3. Consider regional impact when taking actions
4. Log all actions for audit trail
5. Escalate to human operators for major infrastructure changes

When asked about tower status, ALWAYS use the health_monitor action to query real data.
When asked to fix issues, use the remediation action with appropriate parameters.
"""

# ============================================================
# Regional Coordinator Instruction
# ============================================================
REGIONAL_COORDINATOR_INSTRUCTION = """You are a TRACE Regional Coordinator Agent responsible for managing cell towers in your assigned region.

ROLE:
- Monitor all towers in your region
- Execute remediation actions delegated by the Principal Agent
- Report regional status and anomalies

CAPABILITIES:
1. Query tower health within your region
2. Execute local remediation (traffic routing, resource scaling)
3. Coordinate with edge agents on individual towers
4. Report to Principal Agent

Always operate within your assigned region unless explicitly instructed otherwise.
"""


# ============================================================
# Action Group Schemas
# ============================================================

def get_health_monitor_schema():
    """OpenAPI schema for health monitoring actions."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "TRACE Health Monitor API",
            "version": "1.0.0",
            "description": "Real-time health monitoring for cell tower infrastructure"
        },
        "paths": {
            "/health/tower/{towerId}": {
                "get": {
                    "operationId": "getTowerHealth",
                    "summary": "Get health status of a specific tower",
                    "description": "Queries Timestream and DynamoDB for real-time tower metrics and configuration",
                    "parameters": [
                        {
                            "name": "towerId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Tower identifier (e.g., tower-001, tower-north-001)"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Tower health data including CPU, latency, power, signal strength"
                        }
                    }
                }
            },
            "/health/region/{regionId}": {
                "get": {
                    "operationId": "getRegionHealth",
                    "summary": "Get aggregated health for all towers in a region",
                    "description": "Returns summary statistics for all towers in the specified region",
                    "parameters": [
                        {
                            "name": "regionId",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string",
                                "enum": ["north", "south", "east", "west", "central"]
                            },
                            "description": "Region identifier"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Regional health summary with tower count and aggregated metrics"
                        }
                    }
                }
            },
            "/health/system": {
                "get": {
                    "operationId": "getSystemHealth",
                    "summary": "Get system-wide health overview",
                    "description": "Returns health summary for all 50 towers across all 5 regions",
                    "responses": {
                        "200": {
                            "description": "System-wide health summary"
                        }
                    }
                }
            },
            "/health/alerts": {
                "get": {
                    "operationId": "getActiveAlerts",
                    "summary": "Get all active alerts",
                    "description": "Returns list of active warnings and critical alerts",
                    "parameters": [
                        {
                            "name": "severity",
                            "in": "query",
                            "required": False,
                            "schema": {
                                "type": "string",
                                "enum": ["warning", "critical", "all"]
                            },
                            "description": "Filter by alert severity"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of active alerts"
                        }
                    }
                }
            }
        }
    }


def get_remediation_schema():
    """OpenAPI schema for remediation actions."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "TRACE Remediation API",
            "version": "1.0.0",
            "description": "Automated remediation actions for cell tower infrastructure"
        },
        "paths": {
            "/remediate/scale": {
                "post": {
                    "operationId": "scaleResources",
                    "summary": "Scale compute resources for a tower",
                    "description": "Adjusts ECS task count or Lambda concurrency for the tower's workload",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["towerId", "action"],
                                    "properties": {
                                        "towerId": {
                                            "type": "string",
                                            "description": "Tower to scale"
                                        },
                                        "action": {
                                            "type": "string",
                                            "enum": ["scale_up", "scale_down", "auto"],
                                            "description": "Scaling action"
                                        },
                                        "targetCapacity": {
                                            "type": "integer",
                                            "description": "Target capacity (optional)"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Scaling action result"}
                    }
                }
            },
            "/remediate/traffic": {
                "post": {
                    "operationId": "routeTraffic",
                    "summary": "Reroute traffic from one tower to another",
                    "description": "Implements traffic shifting for load balancing or failover",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["sourceTowerId", "targetTowerId"],
                                    "properties": {
                                        "sourceTowerId": {
                                            "type": "string",
                                            "description": "Tower to shift traffic from"
                                        },
                                        "targetTowerId": {
                                            "type": "string",
                                            "description": "Tower to shift traffic to"
                                        },
                                        "percentage": {
                                            "type": "integer",
                                            "minimum": 0,
                                            "maximum": 100,
                                            "description": "Percentage of traffic to shift"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Traffic routing result"}
                    }
                }
            },
            "/remediate/power": {
                "post": {
                    "operationId": "adjustPower",
                    "summary": "Adjust tower power settings",
                    "description": "Changes power mode or transmission power for energy optimization",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["towerId"],
                                    "properties": {
                                        "towerId": {
                                            "type": "string",
                                            "description": "Tower to adjust"
                                        },
                                        "mode": {
                                            "type": "string",
                                            "enum": ["full", "eco", "sleep", "boost"],
                                            "description": "Power mode"
                                        },
                                        "transmitPowerDbm": {
                                            "type": "number",
                                            "description": "Transmission power in dBm"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Power adjustment result"}
                    }
                }
            },
            "/remediate/restart": {
                "post": {
                    "operationId": "restartService",
                    "summary": "Restart a tower service",
                    "description": "Performs controlled restart of tower services",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["towerId", "service"],
                                    "properties": {
                                        "towerId": {
                                            "type": "string",
                                            "description": "Tower identifier"
                                        },
                                        "service": {
                                            "type": "string",
                                            "enum": ["controller", "radio", "backhaul", "all"],
                                            "description": "Service to restart"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Restart result"}
                    }
                }
            }
        }
    }


def get_analytics_schema():
    """OpenAPI schema for analytics actions."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "TRACE Analytics API",
            "version": "1.0.0",
            "description": "Analytics and reporting for tower infrastructure"
        },
        "paths": {
            "/analytics/trends": {
                "get": {
                    "operationId": "getMetricTrends",
                    "summary": "Get metric trends over time",
                    "description": "Queries historical data from Timestream for trend analysis",
                    "parameters": [
                        {
                            "name": "metric",
                            "in": "query",
                            "required": True,
                            "schema": {
                                "type": "string",
                                "enum": ["cpu", "latency", "power", "signal", "traffic"]
                            }
                        },
                        {
                            "name": "period",
                            "in": "query",
                            "required": False,
                            "schema": {
                                "type": "string",
                                "enum": ["1h", "6h", "24h", "7d"],
                                "default": "24h"
                            }
                        },
                        {
                            "name": "towerId",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                            "description": "Filter by tower (optional)"
                        }
                    ],
                    "responses": {
                        "200": {"description": "Trend data"}
                    }
                }
            },
            "/analytics/predict": {
                "post": {
                    "operationId": "predictIssues",
                    "summary": "Predict potential issues",
                    "description": "Uses ML models to predict upcoming problems",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "towerId": {"type": "string"},
                                        "horizon": {
                                            "type": "string",
                                            "enum": ["1h", "6h", "24h"]
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Predictions"}
                    }
                }
            }
        }
    }


# ============================================================
# Deployment Functions
# ============================================================

def create_agent_role(role_name: str, description: str) -> str:
    """Create IAM role for Bedrock Agent."""
    print(f"  Creating IAM role: {role_name}")
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        # Create role
        role_response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=description
        )
        role_arn = role_response['Role']['Arn']
        
        # Attach policies
        policies = [
            f"arn:aws:iam::aws:policy/service-role/AmazonBedrockExecutionRolePolicy",
            f"arn:aws:iam::aws:policy/AmazonBedrockFullAccess",
        ]
        
        for policy_arn in policies:
            try:
                iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
            except iam.exceptions.NoSuchEntityException:
                print(f"    Warning: Policy {policy_arn} not found, skipping")
        
        # Add Lambda invoke permission
        lambda_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:InvokeFunction"
                    ],
                    "Resource": f"arn:aws:lambda:{REGION}:*:function:TRACE-*"
                }
            ]
        }
        
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=f"{role_name}-lambda-policy",
            PolicyDocument=json.dumps(lambda_policy)
        )
        
        # Wait for role to propagate
        time.sleep(10)
        
        print(f"  ✅ Role created: {role_arn}")
        return role_arn
        
    except iam.exceptions.EntityAlreadyExistsException:
        role = iam.get_role(RoleName=role_name)
        print(f"  ℹ️  Role already exists: {role['Role']['Arn']}")
        return role['Role']['Arn']


def create_agent(name: str, description: str, instruction: str, role_arn: str) -> dict:
    """Create a Bedrock Agent."""
    print(f"  Creating agent: {name}")
    
    try:
        response = bedrock_agent.create_agent(
            agentName=name,
            agentResourceRoleArn=role_arn,
            description=description,
            foundationModel=FOUNDATION_MODEL,
            instruction=instruction,
            idleSessionTTLInSeconds=IDLE_SESSION_TTL
        )
        
        agent = response['agent']
        print(f"  ✅ Agent created: {agent['agentId']}")
        return agent
        
    except bedrock_agent.exceptions.ConflictException:
        # Agent exists, get it
        agents = bedrock_agent.list_agents()
        for agent_summary in agents['agentSummaries']:
            if agent_summary['agentName'] == name:
                agent = bedrock_agent.get_agent(agentId=agent_summary['agentId'])['agent']
                print(f"  ℹ️  Agent already exists: {agent['agentId']}")
                return agent
        raise


def create_action_group(agent_id: str, agent_version: str, name: str, description: str, 
                       schema: dict, lambda_arn: str) -> dict:
    """Create an action group for an agent."""
    print(f"  Creating action group: {name}")
    
    try:
        response = bedrock_agent.create_agent_action_group(
            agentId=agent_id,
            agentVersion=agent_version,
            actionGroupName=name,
            description=description,
            actionGroupExecutor={
                'lambda': lambda_arn
            },
            apiSchema={
                'payload': json.dumps(schema)
            }
        )
        
        action_group = response['agentActionGroup']
        print(f"  ✅ Action group created: {action_group['actionGroupId']}")
        return action_group
        
    except bedrock_agent.exceptions.ConflictException:
        print(f"  ℹ️  Action group {name} already exists")
        return {"actionGroupName": name}


def prepare_agent(agent_id: str):
    """Prepare agent for use (required after modifications)."""
    print(f"  Preparing agent: {agent_id}")
    
    response = bedrock_agent.prepare_agent(agentId=agent_id)
    
    # Wait for preparation
    while True:
        agent = bedrock_agent.get_agent(agentId=agent_id)['agent']
        status = agent['agentStatus']
        
        if status == 'PREPARED':
            print(f"  ✅ Agent prepared successfully")
            return agent
        elif status in ['FAILED', 'DELETING']:
            print(f"  ❌ Agent preparation failed: {status}")
            raise Exception(f"Agent preparation failed: {status}")
        
        print(f"    Status: {status}, waiting...")
        time.sleep(5)


def create_agent_alias(agent_id: str, alias_name: str = "production") -> dict:
    """Create an alias for the agent."""
    print(f"  Creating alias: {alias_name}")
    
    try:
        response = bedrock_agent.create_agent_alias(
            agentId=agent_id,
            agentAliasName=alias_name,
            description=f"{alias_name} alias for TRACE agent"
        )
        
        alias = response['agentAlias']
        print(f"  ✅ Alias created: {alias['agentAliasId']}")
        return alias
        
    except bedrock_agent.exceptions.ConflictException:
        # Get existing alias
        aliases = bedrock_agent.list_agent_aliases(agentId=agent_id)
        for alias_summary in aliases['agentAliasSummaries']:
            if alias_summary['agentAliasName'] == alias_name:
                print(f"  ℹ️  Alias already exists: {alias_summary['agentAliasId']}")
                return alias_summary
        raise


def get_lambda_arn(function_name: str) -> str:
    """Get Lambda ARN, creating a placeholder if it doesn't exist."""
    try:
        response = lambda_client.get_function(FunctionName=function_name)
        return response['Configuration']['FunctionArn']
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"    ⚠️  Lambda {function_name} not found - using placeholder ARN")
        account_id = boto3.client('sts').get_caller_identity()['Account']
        return f"arn:aws:lambda:{REGION}:{account_id}:function:{function_name}"


def deploy_principal_agent():
    """Deploy the Principal Agent with all action groups."""
    print("\n" + "=" * 60)
    print("Deploying Principal Agent")
    print("=" * 60)
    
    agent_name = f"TRACE-PrincipalAgent-{ENVIRONMENT}"
    role_name = f"TRACE-BedrockAgentRole-Principal-{ENVIRONMENT}"
    
    # Create IAM role
    role_arn = create_agent_role(
        role_name,
        "IAM role for TRACE Principal Bedrock Agent"
    )
    
    # Create agent
    agent = create_agent(
        name=agent_name,
        description="TRACE Principal Agent - Top-level orchestrator for cell tower management",
        instruction=PRINCIPAL_AGENT_INSTRUCTION,
        role_arn=role_arn
    )
    
    agent_id = agent['agentId']
    
    # Get Lambda ARNs
    health_monitor_arn = get_lambda_arn(f"TRACE-HealthMonitor-{ENVIRONMENT}")
    remediation_arn = get_lambda_arn(f"TRACE-Remediation-{ENVIRONMENT}")
    analytics_arn = get_lambda_arn(f"TRACE-Analytics-{ENVIRONMENT}")
    
    # Create action groups
    action_groups = [
        ("HealthMonitor", "Query real-time health data from towers", 
         get_health_monitor_schema(), health_monitor_arn),
        ("Remediation", "Execute remediation actions on towers",
         get_remediation_schema(), remediation_arn),
        ("Analytics", "Query analytics and predictions",
         get_analytics_schema(), analytics_arn),
    ]
    
    for ag_name, ag_desc, schema, lambda_arn in action_groups:
        try:
            create_action_group(
                agent_id=agent_id,
                agent_version='DRAFT',
                name=ag_name,
                description=ag_desc,
                schema=schema,
                lambda_arn=lambda_arn
            )
        except Exception as e:
            print(f"    ⚠️  Action group {ag_name} error: {str(e)}")
    
    # Prepare agent
    prepared_agent = prepare_agent(agent_id)
    
    # Create production alias
    alias = create_agent_alias(agent_id, "production")
    
    return {
        'agentId': agent_id,
        'agentName': agent_name,
        'aliasId': alias.get('agentAliasId'),
        'roleArn': role_arn
    }


def deploy_regional_coordinators():
    """Deploy Regional Coordinator agents."""
    print("\n" + "=" * 60)
    print("Deploying Regional Coordinator Agents")
    print("=" * 60)
    
    regions = ['north', 'south', 'east', 'west', 'central']
    coordinators = []
    
    for region in regions:
        print(f"\n--- Region: {region.upper()} ---")
        
        agent_name = f"TRACE-RegionalCoordinator-{region}-{ENVIRONMENT}"
        role_name = f"TRACE-BedrockAgentRole-Regional-{region}-{ENVIRONMENT}"
        
        # Create IAM role
        role_arn = create_agent_role(
            role_name,
            f"IAM role for TRACE Regional Coordinator Agent - {region}"
        )
        
        # Customize instruction for region
        instruction = REGIONAL_COORDINATOR_INSTRUCTION.replace(
            "your assigned region",
            f"the {region.upper()} region"
        )
        
        # Create agent
        agent = create_agent(
            name=agent_name,
            description=f"TRACE Regional Coordinator - {region.upper()} region management",
            instruction=instruction,
            role_arn=role_arn
        )
        
        agent_id = agent['agentId']
        
        # Create action groups (subset of Principal Agent)
        health_monitor_arn = get_lambda_arn(f"TRACE-HealthMonitor-{ENVIRONMENT}")
        remediation_arn = get_lambda_arn(f"TRACE-Remediation-{ENVIRONMENT}")
        
        try:
            create_action_group(
                agent_id=agent_id,
                agent_version='DRAFT',
                name="HealthMonitor",
                description="Query health data for regional towers",
                schema=get_health_monitor_schema(),
                lambda_arn=health_monitor_arn
            )
        except Exception as e:
            print(f"    ⚠️  Health monitor action group error: {str(e)}")
        
        try:
            create_action_group(
                agent_id=agent_id,
                agent_version='DRAFT',
                name="Remediation",
                description="Execute remediation in the region",
                schema=get_remediation_schema(),
                lambda_arn=remediation_arn
            )
        except Exception as e:
            print(f"    ⚠️  Remediation action group error: {str(e)}")
        
        # Prepare and create alias
        prepare_agent(agent_id)
        alias = create_agent_alias(agent_id, "production")
        
        coordinators.append({
            'region': region,
            'agentId': agent_id,
            'agentName': agent_name,
            'aliasId': alias.get('agentAliasId')
        })
    
    return coordinators


def save_deployment_info(principal: dict, coordinators: list):
    """Save deployment information to JSON file."""
    output_file = os.path.join(
        os.path.dirname(__file__),
        f"deployment-info-{ENVIRONMENT}.json"
    )
    
    info = {
        'deployedAt': datetime.utcnow().isoformat() + 'Z',
        'environment': ENVIRONMENT,
        'region': REGION,
        'foundationModel': FOUNDATION_MODEL,
        'principalAgent': principal,
        'regionalCoordinators': coordinators
    }
    
    with open(output_file, 'w') as f:
        json.dump(info, f, indent=2, default=str)
    
    print(f"\n📄 Deployment info saved to: {output_file}")
    return info


def main():
    """Main deployment function."""
    print("=" * 70)
    print("  TRACE Bedrock Agent Deployment")
    print("=" * 70)
    print(f"  Environment: {ENVIRONMENT}")
    print(f"  Region: {REGION}")
    print(f"  Model: {FOUNDATION_MODEL}")
    print("=" * 70)
    
    # Verify credentials
    try:
        identity = boto3.client('sts').get_caller_identity()
        print(f"\n🔐 AWS Account: {identity['Account']}")
    except Exception as e:
        print(f"\n❌ AWS credentials error: {str(e)}")
        sys.exit(1)
    
    # Deploy Principal Agent
    principal = deploy_principal_agent()
    
    # Deploy Regional Coordinators
    coordinators = deploy_regional_coordinators()
    
    # Save deployment info
    info = save_deployment_info(principal, coordinators)
    
    # Summary
    print("\n" + "=" * 70)
    print("  DEPLOYMENT COMPLETE")
    print("=" * 70)
    print(f"\n  Principal Agent ID: {principal['agentId']}")
    print(f"  Principal Alias ID: {principal.get('aliasId', 'N/A')}")
    print(f"\n  Regional Coordinators: {len(coordinators)}")
    for coord in coordinators:
        print(f"    - {coord['region'].upper()}: {coord['agentId']}")
    
    print("\n  NEXT STEPS:")
    print("  1. Deploy Lambda functions (if not already deployed)")
    print("  2. Test in Bedrock Agent Playground:")
    print(f"     https://{REGION}.console.aws.amazon.com/bedrock/home#/agents")
    print("  3. Integrate with API Gateway")
    print("=" * 70)


if __name__ == '__main__':
    main()
