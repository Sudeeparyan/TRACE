"""
TRACE Tower Configuration MCP Server

Exposes tower configuration, status, and management capabilities via MCP.
Enables agents to discover tower details and request configuration changes.

Updated: Now queries AWS DynamoDB for real tower configurations.
Falls back to default configurations if DynamoDB is unavailable.
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
logger = logging.getLogger("tower-config-mcp-server")

# Initialize MCP Server
server = Server("trace-tower-config-server")

# AWS Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'production')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
TOWER_CONFIG_TABLE = os.getenv('TOWER_CONFIG_TABLE', f'TRACE-TowerConfig-{ENVIRONMENT}')

# Initialize AWS clients
try:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    dynamodb_client = boto3.client('dynamodb', region_name=AWS_REGION)
    tower_config_table = dynamodb.Table(TOWER_CONFIG_TABLE)
    AWS_AVAILABLE = True
    logger.info(f"AWS DynamoDB initialized: table={TOWER_CONFIG_TABLE}")
except Exception as e:
    logger.warning(f"AWS DynamoDB not available: {e}")
    AWS_AVAILABLE = False


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal types from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def get_tower_config_from_dynamodb(tower_id: Optional[str] = None) -> dict:
    """
    Query DynamoDB for tower configuration.
    
    Args:
        tower_id: Specific tower ID, or None for all towers
    
    Returns:
        Tower configuration dict or dict of all towers
    """
    if not AWS_AVAILABLE:
        logger.info("DynamoDB not available, using fallback configurations")
        return {}
    
    try:
        if tower_id:
            # Get specific tower
            response = tower_config_table.get_item(Key={'tower_id': tower_id})
            if 'Item' in response:
                return {tower_id: response['Item']}
            return {}
        else:
            # Scan all towers
            response = tower_config_table.scan()
            towers = {}
            for item in response.get('Items', []):
                tid = item.get('tower_id')
                if tid:
                    towers[tid] = item
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = tower_config_table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                for item in response.get('Items', []):
                    tid = item.get('tower_id')
                    if tid:
                        towers[tid] = item
            
            return towers
    except ClientError as e:
        logger.error(f"DynamoDB query failed: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error fetching tower config: {e}")
        return {}


def update_tower_config_in_dynamodb(tower_id: str, updates: dict) -> bool:
    """
    Update tower configuration in DynamoDB.
    
    Args:
        tower_id: Tower ID to update
        updates: Dict of field -> new value
    
    Returns:
        True if successful, False otherwise
    """
    if not AWS_AVAILABLE:
        return False
    
    try:
        # Build update expression
        update_expr_parts = []
        expr_attr_names = {}
        expr_attr_values = {}
        
        for i, (key, value) in enumerate(updates.items()):
            update_expr_parts.append(f"#{key} = :val{i}")
            expr_attr_names[f"#{key}"] = key
            expr_attr_values[f":val{i}"] = value
        
        update_expression = "SET " + ", ".join(update_expr_parts)
        
        tower_config_table.update_item(
            Key={'tower_id': tower_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )
        return True
    except Exception as e:
        logger.error(f"Failed to update tower config: {e}")
        return False


# Default tower configuration data (fallback when DynamoDB unavailable)
DEFAULT_TOWER_CONFIGS = {
    "tower-001": {
        "tower_id": "tower-001",
        "name": "Downtown Tower A",
        "region": "region-a",
        "location": {"lat": 40.7128, "lon": -74.0060},
        "capacity": 500,
        "trx_count": 4,
        "active_trx": 4,
        "antenna_count": 12,
        "frequency_bands": ["700MHz", "1900MHz", "2100MHz"],
        "status": "active",
        "power_mode": "normal",
        "last_maintenance": "2026-01-15T10:00:00Z",
        "firmware_version": "3.2.1"
    },
    "tower-002": {
        "tower_id": "tower-002",
        "name": "Uptown Tower B",
        "region": "region-a",
        "location": {"lat": 40.7831, "lon": -73.9712},
        "capacity": 400,
        "trx_count": 3,
        "active_trx": 3,
        "antenna_count": 9,
        "frequency_bands": ["700MHz", "1900MHz"],
        "status": "active",
        "power_mode": "normal",
        "last_maintenance": "2026-01-10T14:00:00Z",
        "firmware_version": "3.2.1"
    },
    "tower-003": {
        "tower_id": "tower-003",
        "name": "Harbor Tower C",
        "region": "region-b",
        "location": {"lat": 40.6892, "lon": -74.0445},
        "capacity": 600,
        "trx_count": 5,
        "active_trx": 4,
        "antenna_count": 15,
        "frequency_bands": ["700MHz", "1900MHz", "2100MHz", "2600MHz"],
        "status": "active",
        "power_mode": "eco",
        "last_maintenance": "2026-01-20T08:00:00Z",
        "firmware_version": "3.2.0"
    },
    "tower-004": {
        "tower_id": "tower-004",
        "name": "Industrial Tower D",
        "region": "region-b",
        "location": {"lat": 40.7282, "lon": -73.7949},
        "capacity": 350,
        "trx_count": 3,
        "active_trx": 2,
        "antenna_count": 9,
        "frequency_bands": ["700MHz", "1900MHz"],
        "status": "degraded",
        "power_mode": "eco",
        "last_maintenance": "2026-01-05T16:00:00Z",
        "firmware_version": "3.1.5"
    },
    "tower-005": {
        "tower_id": "tower-005",
        "name": "Suburban Tower E",
        "region": "region-a",
        "location": {"lat": 40.7589, "lon": -73.9851},
        "capacity": 450,
        "trx_count": 4,
        "active_trx": 3,
        "antenna_count": 12,
        "frequency_bands": ["700MHz", "1900MHz", "2100MHz"],
        "status": "active",
        "power_mode": "normal",
        "last_maintenance": "2026-01-18T12:00:00Z",
        "firmware_version": "3.2.1"
    }
}


def get_tower_configs() -> dict:
    """Get tower configurations, preferring DynamoDB over defaults"""
    configs = get_tower_config_from_dynamodb()
    if configs:
        logger.info(f"Loaded {len(configs)} tower configs from DynamoDB")
        return configs
    else:
        logger.info("Using default tower configurations")
        return DEFAULT_TOWER_CONFIGS.copy()


# In-memory cache for tower configs (refreshed periodically)
TOWER_CONFIGS = get_tower_configs()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tower configuration tools"""
    return [
        Tool(
            name="get_tower_config",
            description="Get configuration details for a specific tower or all towers. Includes capacity, TRX count, antenna count, frequency bands, and power mode.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tower_id": {
                        "type": "string",
                        "description": "Tower ID (e.g., 'tower-001'). If not provided, returns all towers."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_towers_by_region",
            description="Get all towers in a specific region.",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "Region ID (e.g., 'region-a' or 'region-b')"
                    }
                },
                "required": ["region"]
            }
        ),
        Tool(
            name="set_power_mode",
            description="Set the power mode for a tower. Options: 'normal', 'eco' (reduced power), 'boost' (max power), 'standby' (minimal power).",
            inputSchema={
                "type": "object",
                "properties": {
                    "tower_id": {
                        "type": "string",
                        "description": "Tower ID to configure"
                    },
                    "power_mode": {
                        "type": "string",
                        "enum": ["normal", "eco", "boost", "standby"],
                        "description": "Power mode to set"
                    }
                },
                "required": ["tower_id", "power_mode"]
            }
        ),
        Tool(
            name="set_active_trx",
            description="Set the number of active TRX (transmitters) on a tower. Used for energy optimization - reduce TRX during low demand.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tower_id": {
                        "type": "string",
                        "description": "Tower ID to configure"
                    },
                    "active_trx_count": {
                        "type": "integer",
                        "description": "Number of TRX to keep active (1 to max TRX count)"
                    }
                },
                "required": ["tower_id", "active_trx_count"]
            }
        ),
        Tool(
            name="get_nearby_towers",
            description="Find towers near a given tower for load balancing purposes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tower_id": {
                        "type": "string",
                        "description": "Reference tower ID"
                    },
                    "max_distance_km": {
                        "type": "number",
                        "description": "Maximum distance in kilometers",
                        "default": 10
                    }
                },
                "required": ["tower_id"]
            }
        ),
        Tool(
            name="activate_warm_spare",
            description="Activate a warm spare tower or additional capacity for handling traffic surge.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tower_id": {
                        "type": "string",
                        "description": "Tower ID to activate warm spare"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for activation (e.g., 'traffic_surge', 'failover', 'scheduled_event')"
                    }
                },
                "required": ["tower_id", "reason"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    global TOWER_CONFIGS
    
    # Refresh configs from DynamoDB for read operations
    if name in ["get_tower_config", "get_towers_by_region", "get_nearby_towers"]:
        TOWER_CONFIGS = get_tower_configs()
    
    if name == "get_tower_config":
        tower_id = arguments.get("tower_id")
        if tower_id:
            # Try DynamoDB first for latest data
            db_configs = get_tower_config_from_dynamodb(tower_id)
            if db_configs and tower_id in db_configs:
                return [TextContent(type="text", text=json.dumps(db_configs[tower_id], indent=2, cls=DecimalEncoder))]
            elif tower_id in TOWER_CONFIGS:
                return [TextContent(type="text", text=json.dumps(TOWER_CONFIGS[tower_id], indent=2, cls=DecimalEncoder))]
            else:
                return [TextContent(type="text", text=json.dumps({"error": f"Tower {tower_id} not found"}))]
        else:
            return [TextContent(type="text", text=json.dumps(TOWER_CONFIGS, indent=2, cls=DecimalEncoder))]
    
    elif name == "get_towers_by_region":
        region = arguments.get("region")
        regional_towers = {
            tid: config for tid, config in TOWER_CONFIGS.items()
            if config.get("region") == region
        }
        return [TextContent(type="text", text=json.dumps(regional_towers, indent=2, cls=DecimalEncoder))]
    
    elif name == "set_power_mode":
        tower_id = arguments.get("tower_id")
        power_mode = arguments.get("power_mode")
        
        if tower_id not in TOWER_CONFIGS and not get_tower_config_from_dynamodb(tower_id):
            return [TextContent(type="text", text=json.dumps({"error": f"Tower {tower_id} not found"}))]
        
        old_mode = TOWER_CONFIGS.get(tower_id, {}).get("power_mode", "unknown")
        
        # Update in DynamoDB if available
        db_success = update_tower_config_in_dynamodb(tower_id, {
            "power_mode": power_mode,
            "last_updated": datetime.now().isoformat()
        })
        
        # Update local cache
        if tower_id in TOWER_CONFIGS:
            TOWER_CONFIGS[tower_id]["power_mode"] = power_mode
        
        result = {
            "success": True,
            "tower_id": tower_id,
            "previous_mode": old_mode,
            "new_mode": power_mode,
            "timestamp": datetime.now().isoformat(),
            "persisted_to_dynamodb": db_success,
            "estimated_power_change": {
                "normal": 0,
                "eco": -30,  # 30% reduction
                "boost": 20,  # 20% increase
                "standby": -70  # 70% reduction
            }.get(power_mode, 0)
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "set_active_trx":
        tower_id = arguments.get("tower_id")
        active_trx_count = arguments.get("active_trx_count")
        
        if tower_id not in TOWER_CONFIGS and not get_tower_config_from_dynamodb(tower_id):
            return [TextContent(type="text", text=json.dumps({"error": f"Tower {tower_id} not found"}))]
        
        config = TOWER_CONFIGS.get(tower_id, {})
        max_trx = config.get("trx_count", 4)
        if active_trx_count < 1 or active_trx_count > max_trx:
            return [TextContent(type="text", text=json.dumps({
                "error": f"active_trx_count must be between 1 and {max_trx}"
            }))]
        
        old_count = config.get("active_trx", max_trx)
        
        # Update in DynamoDB if available
        db_success = update_tower_config_in_dynamodb(tower_id, {
            "active_trx": active_trx_count,
            "last_updated": datetime.now().isoformat()
        })
        
        # Update local cache
        if tower_id in TOWER_CONFIGS:
            TOWER_CONFIGS[tower_id]["active_trx"] = active_trx_count
        
        result = {
            "success": True,
            "tower_id": tower_id,
            "previous_active_trx": old_count,
            "new_active_trx": active_trx_count,
            "max_trx": max_trx,
            "timestamp": datetime.now().isoformat(),
            "persisted_to_dynamodb": db_success,
            "power_savings_percent": round((old_count - active_trx_count) / old_count * 25, 1) if old_count > active_trx_count else 0
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "get_nearby_towers":
        tower_id = arguments.get("tower_id")
        max_distance = arguments.get("max_distance_km", 10)
        
        if tower_id not in TOWER_CONFIGS and not get_tower_config_from_dynamodb(tower_id):
            return [TextContent(type="text", text=json.dumps({"error": f"Tower {tower_id} not found"}))]
        
        # Simplified distance calculation (all towers considered "nearby" for demo)
        nearby = []
        ref_tower = TOWER_CONFIGS.get(tower_id, {})
        
        for tid, config in TOWER_CONFIGS.items():
            if tid != tower_id:
                # Simplified: just check same region first, then others
                distance = 5 if config.get("region") == ref_tower.get("region") else 8
                if distance <= max_distance:
                    nearby.append({
                        "tower_id": tid,
                        "name": config.get("name", "Unknown"),
                        "distance_km": distance,
                        "available_capacity": config.get("capacity", 400) - 200,  # Estimated
                        "status": config.get("status", "unknown")
                    })
        
        result = {
            "reference_tower": tower_id,
            "max_distance_km": max_distance,
            "nearby_towers": nearby,
            "data_source": "dynamodb" if AWS_AVAILABLE else "fallback"
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2, cls=DecimalEncoder))]
    
    elif name == "activate_warm_spare":
        tower_id = arguments.get("tower_id")
        reason = arguments.get("reason")
        
        if tower_id not in TOWER_CONFIGS and not get_tower_config_from_dynamodb(tower_id):
            return [TextContent(type="text", text=json.dumps({"error": f"Tower {tower_id} not found"}))]
        
        config = TOWER_CONFIGS.get(tower_id, {})
        
        # Activate all TRX and set to boost mode
        old_active_trx = config.get("active_trx", 2)
        old_power_mode = config.get("power_mode", "normal")
        new_trx_count = config.get("trx_count", 4)
        
        # Update in DynamoDB
        db_success = update_tower_config_in_dynamodb(tower_id, {
            "active_trx": new_trx_count,
            "power_mode": "boost",
            "last_updated": datetime.now().isoformat(),
            "warm_spare_activated": True,
            "warm_spare_reason": reason
        })
        
        # Update local cache
        if tower_id in TOWER_CONFIGS:
            TOWER_CONFIGS[tower_id]["active_trx"] = new_trx_count
            TOWER_CONFIGS[tower_id]["power_mode"] = "boost"
        
        result = {
            "success": True,
            "tower_id": tower_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "persisted_to_dynamodb": db_success,
            "changes": {
                "active_trx": {"from": old_active_trx, "to": new_trx_count},
                "power_mode": {"from": old_power_mode, "to": "boost"}
            },
            "estimated_capacity_increase": round((new_trx_count - old_active_trx) / new_trx_count * 100, 1) if new_trx_count > 0 else 0,
            "message": f"Warm spare activated for {reason}"
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="trace://towers/all",
            name="All Tower Configurations",
            description="Complete configuration data for all towers (from DynamoDB or fallback)",
            mimeType="application/json"
        ),
        Resource(
            uri="trace://towers/regions",
            name="Towers by Region",
            description="Towers grouped by region",
            mimeType="application/json"
        ),
        Resource(
            uri="trace://towers/status",
            name="Data Source Status",
            description="Current data source (DynamoDB or fallback)",
            mimeType="application/json"
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI"""
    global TOWER_CONFIGS
    
    # Refresh from DynamoDB
    TOWER_CONFIGS = get_tower_configs()
    
    if uri == "trace://towers/all":
        return json.dumps(TOWER_CONFIGS, indent=2, cls=DecimalEncoder)
    elif uri == "trace://towers/regions":
        regions = {}
        for tid, config in TOWER_CONFIGS.items():
            region = config.get("region", "unknown")
            if region not in regions:
                regions[region] = []
            regions[region].append(config)
        return json.dumps(regions, indent=2, cls=DecimalEncoder)
    elif uri == "trace://towers/status":
        return json.dumps({
            "data_source": "dynamodb" if AWS_AVAILABLE else "fallback",
            "table_name": TOWER_CONFIG_TABLE if AWS_AVAILABLE else None,
            "tower_count": len(TOWER_CONFIGS),
            "environment": ENVIRONMENT
        }, indent=2)
    else:
        return json.dumps({"error": f"Unknown resource: {uri}"})


async def main():
    """Run the MCP server"""
    logger.info("Starting TRACE Tower Config MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
