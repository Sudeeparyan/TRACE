#!/usr/bin/env python3
"""
Connect MCP Tools Lambda to Bedrock Agents

This script creates action groups on Bedrock agents that connect to the
trace-mcp-tools Lambda function, enabling agents to use MCP-style tools.
"""

import boto3
import json
import os

# Initialize clients
bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

# Lambda ARN
LAMBDA_ARN = "arn:aws:lambda:us-east-1:382114757306:function:trace-mcp-tools"

# Agent configurations - which tools each agent needs
AGENT_TOOL_MAPPING = {
    # Principal Agent - gets all tools for global orchestration
    "N3LVTOXSFA": {
        "name": "TRACE-Principal-Agent-dev",
        "action_groups": [
            {
                "name": "MCPTelemetry",
                "description": "Real-time tower telemetry and anomaly detection",
                "tools": ["get_tower_telemetry", "detect_tower_anomalies", "get_network_health_summary"]
            },
            {
                "name": "MCPEnergy", 
                "description": "Energy optimization and power management",
                "tools": ["get_energy_status", "get_energy_recommendations", "execute_energy_optimization"]
            },
            {
                "name": "MCPPolicy",
                "description": "Remediation policies and self-healing actions",
                "tools": ["get_policy", "execute_remediation", "get_remediation_status"]
            }
        ]
    },
    # Regional Coordinator A - telemetry and config for regional management
    "A1AK7SJQF6": {
        "name": "TRACE-Regional-Coordinator-dev",
        "action_groups": [
            {
                "name": "MCPTelemetry",
                "description": "Tower telemetry for regional monitoring",
                "tools": ["get_tower_telemetry", "detect_tower_anomalies"]
            },
            {
                "name": "MCPConfig",
                "description": "Tower configuration and TRX control",
                "tools": ["get_tower_config", "set_power_mode", "set_active_trx", "activate_warm_spare"]
            }
        ]
    },
    # Regional Coordinator B
    "JPA17IHQ0V": {
        "name": "TRACE-RegionB-Coordinator-dev",
        "action_groups": [
            {
                "name": "MCPTelemetry",
                "description": "Tower telemetry for regional monitoring",
                "tools": ["get_tower_telemetry", "detect_tower_anomalies"]
            },
            {
                "name": "MCPConfig",
                "description": "Tower configuration and TRX control",
                "tools": ["get_tower_config", "set_power_mode", "set_active_trx", "activate_warm_spare"]
            }
        ]
    },
    # Monitoring Agent - telemetry focus
    "ERZO1UFKHQ": {
        "name": "TRACE-Monitoring-Agent-dev",
        "action_groups": [
            {
                "name": "MCPTelemetry",
                "description": "Full telemetry access for monitoring",
                "tools": ["get_tower_telemetry", "detect_tower_anomalies", "get_network_health_summary", "get_power_consumption_report"]
            }
        ]
    },
    # Action Agent - config and energy for taking actions
    "PNZVYMD3MH": {
        "name": "TRACE-Action-Agent-dev",
        "action_groups": [
            {
                "name": "MCPConfig",
                "description": "Tower configuration for actions",
                "tools": ["set_power_mode", "set_active_trx", "activate_warm_spare"]
            },
            {
                "name": "MCPEnergy",
                "description": "Energy optimization actions",
                "tools": ["execute_energy_optimization"]
            }
        ]
    },
    # Decision xApp - policies for decision making
    "N2EGAGVLEM": {
        "name": "TRACE-Decision-xApp-dev",
        "action_groups": [
            {
                "name": "MCPPolicy",
                "description": "Policy access for decisions",
                "tools": ["get_policy", "get_energy_recommendations"]
            }
        ]
    }
}


def create_api_schema_for_tools(tools):
    """Create OpenAPI schema for specific tools"""
    
    # Load full schema
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(script_dir, 'mcp_action_group_schema.json')
    
    with open(schema_path, 'r') as f:
        full_schema = json.load(f)
    
    # Tool to path mapping
    tool_paths = {
        "get_tower_telemetry": "/telemetry/tower",
        "detect_tower_anomalies": "/telemetry/anomalies",
        "get_network_health_summary": "/telemetry/health",
        "get_power_consumption_report": "/telemetry/power",
        "get_tower_config": "/config/tower",
        "set_power_mode": "/config/power-mode",
        "set_active_trx": "/config/trx",
        "activate_warm_spare": "/config/warm-spare",
        "get_energy_status": "/energy/status",
        "get_energy_recommendations": "/energy/recommendations",
        "execute_energy_optimization": "/energy/optimize",
        "get_policy": "/policy/get",
        "execute_remediation": "/policy/remediate",
        "get_remediation_status": "/policy/status"
    }
    
    # Filter paths for requested tools
    filtered_paths = {}
    for tool in tools:
        path = tool_paths.get(tool)
        if path and path in full_schema.get("paths", {}):
            filtered_paths[path] = full_schema["paths"][path]
    
    # Create filtered schema
    filtered_schema = {
        "openapi": "3.0.0",
        "info": full_schema["info"],
        "paths": filtered_paths
    }
    
    return json.dumps(filtered_schema)


def add_lambda_permission(agent_id):
    """Add permission for Bedrock to invoke Lambda"""
    try:
        lambda_client.add_permission(
            FunctionName='trace-mcp-tools',
            StatementId=f'bedrock-agent-{agent_id}',
            Action='lambda:InvokeFunction',
            Principal='bedrock.amazonaws.com',
            SourceArn=f'arn:aws:bedrock:us-east-1:382114757306:agent/{agent_id}'
        )
        print(f"  ✅ Added Lambda permission for agent {agent_id}")
    except lambda_client.exceptions.ResourceConflictException:
        print(f"  ℹ️  Lambda permission already exists for agent {agent_id}")
    except Exception as e:
        print(f"  ⚠️  Could not add Lambda permission: {e}")


def create_action_group(agent_id, agent_name, action_group_config):
    """Create an action group on a Bedrock agent"""
    
    group_name = action_group_config["name"]
    description = action_group_config["description"]
    tools = action_group_config["tools"]
    
    print(f"\n  Creating action group: {group_name}")
    print(f"    Tools: {', '.join(tools)}")
    
    # Create API schema for these tools
    api_schema = create_api_schema_for_tools(tools)
    
    try:
        # Check if action group already exists
        existing_groups = bedrock_agent.list_agent_action_groups(
            agentId=agent_id,
            agentVersion='DRAFT'
        )
        
        existing_group_id = None
        for group in existing_groups.get('actionGroupSummaries', []):
            if group['actionGroupName'] == group_name:
                existing_group_id = group['actionGroupId']
                break
        
        if existing_group_id:
            # Update existing
            response = bedrock_agent.update_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                actionGroupId=existing_group_id,
                actionGroupName=group_name,
                description=description,
                actionGroupExecutor={
                    'lambda': LAMBDA_ARN
                },
                apiSchema={
                    'payload': api_schema
                },
                actionGroupState='ENABLED'
            )
            print(f"    ✅ Updated action group: {group_name}")
        else:
            # Create new
            response = bedrock_agent.create_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                actionGroupName=group_name,
                description=description,
                actionGroupExecutor={
                    'lambda': LAMBDA_ARN
                },
                apiSchema={
                    'payload': api_schema
                },
                actionGroupState='ENABLED'
            )
            print(f"    ✅ Created action group: {group_name}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False


def prepare_agent(agent_id):
    """Prepare agent after updating action groups"""
    try:
        response = bedrock_agent.prepare_agent(agentId=agent_id)
        print(f"  ✅ Agent prepared successfully")
        return True
    except Exception as e:
        print(f"  ⚠️  Could not prepare agent: {e}")
        return False


def main():
    print("=" * 60)
    print("TRACE MCP Tools - Bedrock Agent Integration")
    print("=" * 60)
    print(f"\nLambda: {LAMBDA_ARN}")
    print(f"Agents to configure: {len(AGENT_TOOL_MAPPING)}")
    
    success_count = 0
    
    for agent_id, config in AGENT_TOOL_MAPPING.items():
        agent_name = config["name"]
        action_groups = config["action_groups"]
        
        print(f"\n{'─' * 50}")
        print(f"📦 Agent: {agent_name} ({agent_id})")
        print(f"   Action groups to create: {len(action_groups)}")
        
        # Add Lambda permission
        add_lambda_permission(agent_id)
        
        # Create action groups
        all_success = True
        for ag_config in action_groups:
            if not create_action_group(agent_id, agent_name, ag_config):
                all_success = False
        
        # Prepare agent
        if all_success:
            prepare_agent(agent_id)
            success_count += 1
    
    print(f"\n{'=' * 60}")
    print(f"✅ Successfully configured {success_count}/{len(AGENT_TOOL_MAPPING)} agents")
    print("=" * 60)
    
    # Summary
    print("\n📋 Summary - MCP Tools per Agent:")
    for agent_id, config in AGENT_TOOL_MAPPING.items():
        all_tools = []
        for ag in config["action_groups"]:
            all_tools.extend(ag["tools"])
        print(f"  • {config['name']}: {len(all_tools)} tools")


if __name__ == "__main__":
    main()
