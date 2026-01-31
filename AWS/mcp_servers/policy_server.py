"""
TRACE Remediation Policy MCP Server

Exposes remediation policies and self-healing capabilities via MCP.
Enables agents to access policies, execute remediations, and track healing actions.

Updated: Now persists remediation logs to AWS DynamoDB.
Policies can be loaded from DynamoDB or use defaults.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Optional
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("policy-mcp-server")

# Initialize MCP Server
server = Server("trace-policy-server")

# AWS Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'production')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
REMEDIATION_TABLE = os.getenv('REMEDIATION_TABLE', f'TRACE-RemediationLog-{ENVIRONMENT}')
POLICY_TABLE = os.getenv('POLICY_TABLE', f'TRACE-Policies-{ENVIRONMENT}')

# Initialize AWS clients
try:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    dynamodb_client = boto3.client('dynamodb', region_name=AWS_REGION)
    remediation_table = dynamodb.Table(REMEDIATION_TABLE)
    policy_table = dynamodb.Table(POLICY_TABLE)
    AWS_AVAILABLE = True
    logger.info(f"AWS DynamoDB initialized: remediation_table={REMEDIATION_TABLE}")
except Exception as e:
    logger.warning(f"AWS DynamoDB not available: {e}")
    AWS_AVAILABLE = False


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal types from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def save_remediation_to_dynamodb(remediation: dict) -> bool:
    """Save remediation record to DynamoDB"""
    if not AWS_AVAILABLE:
        return False
    try:
        remediation_table.put_item(Item=remediation)
        return True
    except Exception as e:
        logger.error(f"Failed to save remediation: {e}")
        return False


def get_remediations_from_dynamodb(tower_id: Optional[str] = None, limit: int = 10) -> list:
    """Retrieve remediation history from DynamoDB"""
    if not AWS_AVAILABLE:
        return []
    try:
        if tower_id:
            response = remediation_table.query(
                IndexName='tower-id-index',
                KeyConditionExpression=boto3.dynamodb.conditions.Key('tower_id').eq(tower_id),
                Limit=limit,
                ScanIndexForward=False
            )
        else:
            response = remediation_table.scan(Limit=limit)
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Failed to get remediations: {e}")
        return []


def update_remediation_in_dynamodb(remediation_id: str, updates: dict) -> bool:
    """Update remediation record in DynamoDB"""
    if not AWS_AVAILABLE:
        return False
    try:
        update_expr_parts = []
        expr_attr_names = {}
        expr_attr_values = {}
        
        for i, (key, value) in enumerate(updates.items()):
            update_expr_parts.append(f"#{key} = :val{i}")
            expr_attr_names[f"#{key}"] = key
            expr_attr_values[f":val{i}"] = value
        
        remediation_table.update_item(
            Key={'remediation_id': remediation_id},
            UpdateExpression="SET " + ", ".join(update_expr_parts),
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )
        return True
    except Exception as e:
        logger.error(f"Failed to update remediation: {e}")
        return False

# Remediation policies
POLICIES = {
    "HIGH_CPU": {
        "policy_id": "POL-001",
        "name": "High CPU Remediation",
        "trigger": "cpu_usage > 80%",
        "severity": "warning",
        "actions": [
            {"step": 1, "action": "scale_resources", "description": "Increase allocated resources"},
            {"step": 2, "action": "load_balance", "description": "Redistribute traffic to nearby towers"},
            {"step": 3, "action": "restart_services", "description": "Restart non-critical services"}
        ],
        "timeout_seconds": 300,
        "rollback_enabled": True,
        "human_approval_required": False
    },
    "HIGH_LATENCY": {
        "policy_id": "POL-002",
        "name": "High Latency Remediation",
        "trigger": "latency > 100ms",
        "severity": "warning",
        "actions": [
            {"step": 1, "action": "optimize_routing", "description": "Optimize network routing paths"},
            {"step": 2, "action": "increase_bandwidth", "description": "Allocate additional bandwidth"},
            {"step": 3, "action": "activate_spare", "description": "Activate warm spare capacity"}
        ],
        "timeout_seconds": 180,
        "rollback_enabled": True,
        "human_approval_required": False
    },
    "TOWER_DOWN": {
        "policy_id": "POL-003",
        "name": "Tower Failure Remediation",
        "trigger": "tower_status == 'down'",
        "severity": "critical",
        "actions": [
            {"step": 1, "action": "failover", "description": "Initiate automatic failover"},
            {"step": 2, "action": "reroute_traffic", "description": "Reroute all traffic to backup towers"},
            {"step": 3, "action": "alert_noc", "description": "Send critical alert to NOC"},
            {"step": 4, "action": "attempt_restart", "description": "Attempt remote tower restart"}
        ],
        "timeout_seconds": 60,
        "rollback_enabled": False,
        "human_approval_required": True
    },
    "CONGESTION": {
        "policy_id": "POL-004",
        "name": "Traffic Congestion Remediation",
        "trigger": "active_connections > 90% capacity",
        "severity": "warning",
        "actions": [
            {"step": 1, "action": "activate_trx", "description": "Activate additional TRX"},
            {"step": 2, "action": "boost_power", "description": "Increase transmission power"},
            {"step": 3, "action": "load_balance", "description": "Balance load across nearby towers"},
            {"step": 4, "action": "activate_spare_cells", "description": "Activate spare cells/antennas"}
        ],
        "timeout_seconds": 120,
        "rollback_enabled": True,
        "human_approval_required": False
    },
    "HIGH_POWER": {
        "policy_id": "POL-005",
        "name": "High Power Consumption Remediation",
        "trigger": "power_consumption > threshold AND traffic < 50%",
        "severity": "info",
        "actions": [
            {"step": 1, "action": "enable_eco_mode", "description": "Switch to ECO power mode"},
            {"step": 2, "action": "reduce_trx", "description": "Reduce active TRX count"},
            {"step": 3, "action": "lower_antenna_power", "description": "Reduce antenna transmission power"}
        ],
        "timeout_seconds": 600,
        "rollback_enabled": True,
        "human_approval_required": False
    },
    "AGENT_FAILURE": {
        "policy_id": "POL-006",
        "name": "Agent Self-Healing",
        "trigger": "agent_heartbeat_missed > 3",
        "severity": "critical",
        "actions": [
            {"step": 1, "action": "restart_agent", "description": "Attempt agent restart"},
            {"step": 2, "action": "redeploy_agent", "description": "Redeploy agent from backup"},
            {"step": 3, "action": "failover_to_parent", "description": "Route requests through parent agent"},
            {"step": 4, "action": "alert_operations", "description": "Alert operations team"}
        ],
        "timeout_seconds": 120,
        "rollback_enabled": False,
        "human_approval_required": False
    }
}

# Remediation history
REMEDIATION_LOG = []


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available policy tools"""
    return [
        Tool(
            name="get_policy",
            description="Get remediation policy details for a specific issue type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_type": {
                        "type": "string",
                        "enum": ["HIGH_CPU", "HIGH_LATENCY", "TOWER_DOWN", "CONGESTION", "HIGH_POWER", "AGENT_FAILURE"],
                        "description": "Type of issue to get policy for"
                    }
                },
                "required": ["issue_type"]
            }
        ),
        Tool(
            name="list_all_policies",
            description="List all available remediation policies.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="execute_remediation",
            description="Execute a remediation policy for a specific issue. Returns the execution plan and status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_type": {
                        "type": "string",
                        "description": "Type of issue (e.g., HIGH_CPU, CONGESTION)"
                    },
                    "tower_id": {
                        "type": "string",
                        "description": "Tower ID where issue is detected"
                    },
                    "issue_details": {
                        "type": "object",
                        "description": "Additional details about the issue"
                    }
                },
                "required": ["issue_type", "tower_id"]
            }
        ),
        Tool(
            name="get_remediation_status",
            description="Get the status of an ongoing or completed remediation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "remediation_id": {
                        "type": "string",
                        "description": "Remediation ID to check"
                    }
                },
                "required": ["remediation_id"]
            }
        ),
        Tool(
            name="rollback_remediation",
            description="Rollback a remediation action if it caused issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "remediation_id": {
                        "type": "string",
                        "description": "Remediation ID to rollback"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for rollback"
                    }
                },
                "required": ["remediation_id", "reason"]
            }
        ),
        Tool(
            name="get_remediation_history",
            description="Get history of remediation actions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tower_id": {
                        "type": "string",
                        "description": "Filter by tower ID (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to return",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="approve_remediation",
            description="Approve a pending remediation that requires human approval.",
            inputSchema={
                "type": "object",
                "properties": {
                    "remediation_id": {
                        "type": "string",
                        "description": "Remediation ID to approve"
                    },
                    "approver": {
                        "type": "string",
                        "description": "Name/ID of approver"
                    }
                },
                "required": ["remediation_id", "approver"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    
    if name == "get_policy":
        issue_type = arguments.get("issue_type")
        if issue_type in POLICIES:
            return [TextContent(type="text", text=json.dumps(POLICIES[issue_type], indent=2))]
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown policy: {issue_type}"}))]
    
    elif name == "list_all_policies":
        summary = []
        for issue_type, policy in POLICIES.items():
            summary.append({
                "issue_type": issue_type,
                "policy_id": policy["policy_id"],
                "name": policy["name"],
                "severity": policy["severity"],
                "steps_count": len(policy["actions"]),
                "human_approval_required": policy["human_approval_required"]
            })
        return [TextContent(type="text", text=json.dumps(summary, indent=2))]
    
    elif name == "execute_remediation":
        issue_type = arguments.get("issue_type")
        tower_id = arguments.get("tower_id")
        issue_details = arguments.get("issue_details", {})
        
        if issue_type not in POLICIES:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown issue type: {issue_type}"}))]
        
        policy = POLICIES[issue_type]
        remediation_id = f"REM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{tower_id}"
        
        remediation = {
            "remediation_id": remediation_id,
            "issue_type": issue_type,
            "tower_id": tower_id,
            "policy_applied": policy["policy_id"],
            "started_at": datetime.now().isoformat(),
            "status": "pending_approval" if policy["human_approval_required"] else "in_progress",
            "current_step": 0 if policy["human_approval_required"] else 1,
            "total_steps": len(policy["actions"]),
            "actions_executed": [],
            "issue_details": issue_details,
            "environment": ENVIRONMENT
        }
        
        if not policy["human_approval_required"]:
            # Simulate executing first action
            first_action = policy["actions"][0]
            remediation["actions_executed"].append({
                "step": 1,
                "action": first_action["action"],
                "description": first_action["description"],
                "executed_at": datetime.now().isoformat(),
                "result": "success"
            })
            remediation["status"] = "in_progress"
        
        # Save to DynamoDB
        db_saved = save_remediation_to_dynamodb(remediation)
        
        # Also keep in memory
        REMEDIATION_LOG.append(remediation)
        
        remediation["persisted_to_dynamodb"] = db_saved
        
        return [TextContent(type="text", text=json.dumps(remediation, indent=2))]
    
    elif name == "get_remediation_status":
        remediation_id = arguments.get("remediation_id")
        
        for rem in REMEDIATION_LOG:
            if rem["remediation_id"] == remediation_id:
                return [TextContent(type="text", text=json.dumps(rem, indent=2))]
        
        return [TextContent(type="text", text=json.dumps({"error": f"Remediation {remediation_id} not found"}))]
    
    elif name == "rollback_remediation":
        remediation_id = arguments.get("remediation_id")
        reason = arguments.get("reason")
        
        for rem in REMEDIATION_LOG:
            if rem["remediation_id"] == remediation_id:
                policy = POLICIES.get(rem["issue_type"], {})
                
                if not policy.get("rollback_enabled", False):
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Rollback not enabled for this remediation type"
                    }))]
                
                rem["status"] = "rolled_back"
                rem["rollback_reason"] = reason
                rem["rolled_back_at"] = datetime.now().isoformat()
                
                # Update in DynamoDB
                db_updated = update_remediation_in_dynamodb(remediation_id, {
                    "status": "rolled_back",
                    "rollback_reason": reason,
                    "rolled_back_at": rem["rolled_back_at"]
                })
                
                return [TextContent(type="text", text=json.dumps({
                    "success": True,
                    "remediation_id": remediation_id,
                    "status": "rolled_back",
                    "reason": reason,
                    "timestamp": datetime.now().isoformat(),
                    "persisted_to_dynamodb": db_updated
                }, indent=2))]
        
        return [TextContent(type="text", text=json.dumps({"error": f"Remediation {remediation_id} not found"}))]
    
    elif name == "get_remediation_history":
        tower_id = arguments.get("tower_id")
        limit = arguments.get("limit", 10)
        
        # Try DynamoDB first
        db_history = get_remediations_from_dynamodb(tower_id, limit)
        if db_history:
            return [TextContent(type="text", text=json.dumps({
                "total_records": len(db_history),
                "remediations": db_history,
                "data_source": "dynamodb"
            }, indent=2, cls=DecimalEncoder))]
        
        # Fall back to in-memory
        history = REMEDIATION_LOG.copy()
        
        if tower_id:
            history = [r for r in history if r["tower_id"] == tower_id]
        
        history = history[-limit:]
        
        return [TextContent(type="text", text=json.dumps({
            "total_records": len(history),
            "remediations": history,
            "data_source": "memory"
        }, indent=2))]
    
    elif name == "approve_remediation":
        remediation_id = arguments.get("remediation_id")
        approver = arguments.get("approver")
        
        for rem in REMEDIATION_LOG:
            if rem["remediation_id"] == remediation_id:
                if rem["status"] != "pending_approval":
                    return [TextContent(type="text", text=json.dumps({
                        "error": "Remediation is not pending approval"
                    }))]
                
                rem["status"] = "approved"
                rem["approved_by"] = approver
                rem["approved_at"] = datetime.now().isoformat()
                rem["current_step"] = 1
                
                # Execute first action
                policy = POLICIES.get(rem["issue_type"], {})
                if policy and policy["actions"]:
                    first_action = policy["actions"][0]
                    rem["actions_executed"].append({
                        "step": 1,
                        "action": first_action["action"],
                        "description": first_action["description"],
                        "executed_at": datetime.now().isoformat(),
                        "result": "success"
                    })
                    rem["status"] = "in_progress"
                
                # Update in DynamoDB
                db_updated = update_remediation_in_dynamodb(remediation_id, {
                    "status": rem["status"],
                    "approved_by": approver,
                    "approved_at": rem["approved_at"],
                    "current_step": rem["current_step"],
                    "actions_executed": rem["actions_executed"]
                })
                
                return [TextContent(type="text", text=json.dumps({
                    "success": True,
                    "remediation_id": remediation_id,
                    "approved_by": approver,
                    "status": rem["status"],
                    "timestamp": datetime.now().isoformat(),
                    "persisted_to_dynamodb": db_updated
                }, indent=2))]
        
        return [TextContent(type="text", text=json.dumps({"error": f"Remediation {remediation_id} not found"}))]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="trace://policies/all",
            name="All Remediation Policies",
            description="Complete list of remediation policies",
            mimeType="application/json"
        ),
        Resource(
            uri="trace://policies/active-remediations",
            name="Active Remediations",
            description="Currently active remediation actions",
            mimeType="application/json"
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI"""
    if uri == "trace://policies/all":
        return json.dumps(POLICIES, indent=2)
    elif uri == "trace://policies/active-remediations":
        active = [r for r in REMEDIATION_LOG if r["status"] in ["in_progress", "pending_approval"]]
        return json.dumps(active, indent=2)
    else:
        return json.dumps({"error": f"Unknown resource: {uri}"})


async def main():
    """Run the MCP server"""
    logger.info("Starting TRACE Policy MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
