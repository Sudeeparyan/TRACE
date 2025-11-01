"""
MCP Server for Principal Agent Tools

This server exposes all Principal Agent tools via MCP protocol:
- Health monitoring tools
- Remediation tools
- Dashboard tools
- JSON data processing tools
"""

from mcp.server.fastmcp import FastMCP
from typing import Dict, List, Optional
import json
import random
from datetime import datetime
from pathlib import Path

# Initialize FastMCP server
mcp = FastMCP(host="0.0.0.0", stateless_http=True)

# In-memory storage for agent status
agents_db = {
    "regional_coordinator_east": {
        "status": "healthy",
        "last_heartbeat": datetime.now().isoformat(),
        "health_score": 95,
        "uptime_hours": 168,
    },
    "regional_coordinator_west": {
        "status": "healthy",
        "last_heartbeat": datetime.now().isoformat(),
        "health_score": 92,
        "uptime_hours": 156,
    },
    "monitoring_agent_tower_1": {
        "status": "healthy",
        "last_heartbeat": datetime.now().isoformat(),
        "health_score": 98,
        "uptime_hours": 240,
    },
}

# Global JSON data storage
_loaded_json_data = None


# ============================================================================
# HEALTH MONITORING TOOLS
# ============================================================================


@mcp.tool()
def check_system_health() -> dict:
    """
    Check overall system health across all agents and infrastructure.

    Returns comprehensive health status including:
    - Overall system health score
    - Number of healthy/degraded/failed agents
    - Critical alerts
    - Resource utilization
    """
    total_agents = len(agents_db)
    healthy = sum(1 for a in agents_db.values() if a["status"] == "healthy")
    degraded = sum(1 for a in agents_db.values() if a["status"] == "degraded")
    failed = sum(1 for a in agents_db.values() if a["status"] == "failed")

    avg_health_score = (
        sum(a["health_score"] for a in agents_db.values()) / total_agents
        if total_agents > 0
        else 0
    )

    return {
        "timestamp": datetime.now().isoformat(),
        "overall_status": (
            "healthy"
            if failed == 0 and degraded == 0
            else "degraded" if failed == 0 else "critical"
        ),
        "health_score": round(avg_health_score, 1),
        "agents": {
            "total": total_agents,
            "healthy": healthy,
            "degraded": degraded,
            "failed": failed,
        },
        "infrastructure": {
            "cpu_utilization_percent": random.randint(30, 70),
            "memory_utilization_percent": random.randint(40, 80),
            "network_latency_ms": random.randint(5, 50),
            "storage_available_gb": random.randint(100, 500),
        },
        "alerts": [],
    }


@mcp.tool()
def get_agent_status(agent_id: str) -> dict:
    """
    Get detailed status of a specific agent.

    Args:
        agent_id: ID of the agent to check (e.g., "regional_coordinator_east")

    Returns:
        Detailed agent status including health, uptime, and metrics
    """
    if agent_id not in agents_db:
        return {
            "status": "error",
            "message": f"Agent {agent_id} not found",
            "available_agents": list(agents_db.keys()),
        }

    agent = agents_db[agent_id]
    return {
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat(),
        "status": agent["status"],
        "health_score": agent["health_score"],
        "last_heartbeat": agent["last_heartbeat"],
        "uptime_hours": agent["uptime_hours"],
        "metrics": {
            "cpu_percent": random.randint(20, 80),
            "memory_mb": random.randint(100, 500),
            "requests_per_minute": random.randint(10, 100),
        },
    }


# ============================================================================
# REMEDIATION TOOLS
# ============================================================================


@mcp.tool()
def restart_agent(agent_id: str, reason: str = "manual restart") -> dict:
    """
    Restart a failed or degraded agent.

    Args:
        agent_id: ID of the agent to restart
        reason: Reason for restart

    Returns:
        Restart operation result
    """
    if agent_id not in agents_db:
        return {"status": "error", "message": f"Agent {agent_id} not found"}

    # Simulate restart
    agents_db[agent_id]["status"] = "healthy"
    agents_db[agent_id]["last_heartbeat"] = datetime.now().isoformat()
    agents_db[agent_id]["health_score"] = 95

    return {
        "status": "success",
        "agent_id": agent_id,
        "operation": "restart",
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
        "message": f"Agent {agent_id} restarted successfully",
        "new_status": "healthy",
    }


@mcp.tool()
def redeploy_agent(agent_id: str, version: str = "latest") -> dict:
    """
    Redeploy an agent with new configuration or version.

    Args:
        agent_id: ID of the agent to redeploy
        version: Version to deploy

    Returns:
        Redeployment operation result
    """
    if agent_id not in agents_db:
        return {"status": "error", "message": f"Agent {agent_id} not found"}

    # Simulate redeployment
    agents_db[agent_id]["status"] = "healthy"
    agents_db[agent_id]["last_heartbeat"] = datetime.now().isoformat()
    agents_db[agent_id]["health_score"] = 98
    agents_db[agent_id]["uptime_hours"] = 0

    return {
        "status": "success",
        "agent_id": agent_id,
        "operation": "redeploy",
        "version": version,
        "timestamp": datetime.now().isoformat(),
        "message": f"Agent {agent_id} redeployed successfully to version {version}",
        "new_status": "healthy",
    }


@mcp.tool()
def reroute_traffic(
    from_agent: str, to_agent: str, traffic_percentage: int = 100
) -> dict:
    """
    Reroute traffic from one agent to another during failures or maintenance.

    Args:
        from_agent: Source agent ID
        to_agent: Destination agent ID
        traffic_percentage: Percentage of traffic to reroute (0-100)

    Returns:
        Traffic rerouting result
    """
    return {
        "status": "success",
        "operation": "reroute_traffic",
        "from_agent": from_agent,
        "to_agent": to_agent,
        "traffic_percentage": traffic_percentage,
        "timestamp": datetime.now().isoformat(),
        "message": f"Rerouted {traffic_percentage}% of traffic from {from_agent} to {to_agent}",
        "estimated_completion_time": "30 seconds",
    }


# ============================================================================
# DASHBOARD TOOLS
# ============================================================================


@mcp.tool()
def generate_health_dashboard() -> dict:
    """
    Generate a comprehensive health dashboard for all systems.

    Returns:
        Dashboard data with visualizations and metrics
    """
    health_data = check_system_health()

    return {
        "dashboard_type": "system_health",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "overall_health": health_data["health_score"],
            "status": health_data["overall_status"],
            "total_agents": health_data["agents"]["total"],
            "healthy_agents": health_data["agents"]["healthy"],
        },
        "charts": {
            "agent_health_distribution": {
                "healthy": health_data["agents"]["healthy"],
                "degraded": health_data["agents"]["degraded"],
                "failed": health_data["agents"]["failed"],
            },
            "infrastructure_utilization": health_data["infrastructure"],
        },
        "recommendations": [
            "All agents operating normally",
            "System health is optimal",
            "No immediate actions required",
        ],
    }


@mcp.tool()
def get_system_metrics(time_range: str = "1h", metric_types: str = "all") -> dict:
    """
    Get comprehensive system metrics over a time range.

    Args:
        time_range: Time range for metrics (1h, 6h, 24h, 7d)
        metric_types: Types of metrics (all, performance, energy, network)

    Returns:
        System metrics data
    """
    return {
        "time_range": time_range,
        "metric_types": metric_types,
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "performance": {
                "avg_latency_ms": random.randint(10, 50),
                "throughput_mbps": random.randint(500, 2000),
                "error_rate_percent": random.uniform(0, 1),
            },
            "energy": {
                "total_consumption_kwh": random.randint(100, 500),
                "savings_percent": random.randint(25, 40),
                "optimized_towers": random.randint(15, 30),
            },
            "network": {
                "active_connections": random.randint(1000, 5000),
                "bandwidth_utilization_percent": random.randint(40, 80),
                "packet_loss_percent": random.uniform(0, 0.5),
            },
        },
        "trends": {
            "energy_savings": "increasing",
            "network_performance": "stable",
            "system_health": "stable",
        },
    }


# ============================================================================
# JSON DATA PROCESSING TOOLS
# ============================================================================


@mcp.tool()
def add_json_data(json_path: str) -> dict:
    """
    Load and validate JSON data from a file path for analysis.

    Args:
        json_path: Path to JSON file (absolute or relative)

    Returns:
        Load status with record count and sample data
    """
    global _loaded_json_data

    try:
        json_file = Path(json_path)

        # If relative path, make it relative to TRACE root
        if not json_file.is_absolute():
            # Try to find TRACE root
            trace_root = Path(__file__).parent.parent.parent
            json_file = trace_root / json_path

        if not json_file.exists():
            return {
                "status": "error",
                "message": f"File not found: {json_file}",
                "suggestion": "Please provide a valid file path",
            }

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            num_records = len(data)
            sample = data[0] if data else {}
        elif isinstance(data, dict):
            num_records = 1
            sample = data
        else:
            return {"status": "error", "message": "Invalid JSON structure"}

        _loaded_json_data = {
            "path": str(json_file),
            "data": data,
            "loaded_at": datetime.now().isoformat(),
            "num_records": num_records,
        }

        return {
            "status": "success",
            "message": f"Successfully loaded {num_records} records",
            "file_path": str(json_file),
            "num_records": num_records,
            "sample_record": sample,
            "fields": list(sample.keys()) if isinstance(sample, dict) else [],
        }

    except Exception as e:
        return {"status": "error", "message": f"Error loading file: {str(e)}"}


@mcp.tool()
def analyze_json_data_with_llm(
    analysis_type: str = "comprehensive", focus_areas: str = "all"
) -> dict:
    """
    Analyze loaded JSON data for insights and recommendations.

    Args:
        analysis_type: Type of analysis (comprehensive, energy, congestion, health, prediction)
        focus_areas: Areas to focus on (all, towers, regions, errors, performance, recommendations)

    Returns:
        Analysis results with insights and recommendations
    """
    global _loaded_json_data

    if _loaded_json_data is None:
        return {
            "status": "error",
            "message": "No JSON data loaded",
            "suggestion": "Use add_json_data() first",
        }

    data = _loaded_json_data["data"]
    records = data if isinstance(data, list) else [data]

    # Perform analysis
    analysis = {
        "status": "success",
        "analysis_type": analysis_type,
        "focus_areas": focus_areas,
        "num_records": len(records),
        "summary": _analyze_summary(records),
        "insights": _analyze_insights(records, analysis_type),
        "recommendations": _generate_recommendations(records, analysis_type),
    }

    return analysis


@mcp.tool()
def get_recommendations_from_json(
    tower_id: str = None, region_id: str = None, metric_focus: str = "all"
) -> dict:
    """
    Get specific recommendations from loaded JSON data.

    Args:
        tower_id: Specific tower to focus on
        region_id: Specific region to focus on
        metric_focus: Metric focus (all, energy, bandwidth, latency, errors)

    Returns:
        Specific recommendations with priorities
    """
    global _loaded_json_data

    if _loaded_json_data is None:
        return {"status": "error", "message": "No JSON data loaded"}

    data = _loaded_json_data["data"]
    records = data if isinstance(data, list) else [data]

    # Filter data
    if tower_id:
        records = [r for r in records if r.get("tower_id") == tower_id]
    if region_id:
        records = [r for r in records if r.get("region_id") == region_id]

    recommendations = _generate_recommendations(records, metric_focus)

    return {
        "status": "success",
        "scope": {
            "tower_id": tower_id or "all towers",
            "region_id": region_id or "all regions",
            "metric_focus": metric_focus,
        },
        "records_analyzed": len(records),
        "recommendations": recommendations,
    }


@mcp.tool()
def compare_json_datasets(json_path1: str, json_path2: str) -> dict:
    """
    Compare two JSON datasets to identify changes and trends.

    Args:
        json_path1: Path to first JSON file (baseline)
        json_path2: Path to second JSON file (comparison)

    Returns:
        Comparison analysis
    """
    # Load both datasets
    result1 = add_json_data(json_path1)
    if result1["status"] != "success":
        return result1

    data1 = _loaded_json_data["data"]

    result2 = add_json_data(json_path2)
    if result2["status"] != "success":
        return result2

    data2 = _loaded_json_data["data"]

    # Perform comparison
    records1 = data1 if isinstance(data1, list) else [data1]
    records2 = data2 if isinstance(data2, list) else [data2]

    comparison = {
        "status": "success",
        "dataset1": {"path": json_path1, "records": len(records1)},
        "dataset2": {"path": json_path2, "records": len(records2)},
        "changes": {
            "record_count_change": len(records2) - len(records1),
            "metric_changes": _compare_metrics(records1, records2),
        },
    }

    return comparison


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _analyze_summary(records: List[dict]) -> dict:
    """Generate summary statistics."""
    if not records:
        return {}

    return {
        "total_records": len(records),
        "unique_towers": len(set(r.get("tower_id", "") for r in records)),
        "avg_bandwidth_util": round(
            sum(r.get("bandwidth_utilization_pct", 0) for r in records) / len(records),
            2,
        ),
        "avg_latency_ms": round(
            sum(r.get("latency_ms", 0) for r in records) / len(records), 2
        ),
    }


def _analyze_insights(records: List[dict], analysis_type: str) -> List[str]:
    """Generate insights based on analysis type."""
    insights = []

    if analysis_type in ["comprehensive", "energy"]:
        low_usage = [r for r in records if r.get("bandwidth_utilization_pct", 100) < 30]
        if low_usage:
            insights.append(
                f"🔋 {len(low_usage)} records show energy optimization opportunity (<30% bandwidth utilization)"
            )

    if analysis_type in ["comprehensive", "congestion"]:
        high_usage = [r for r in records if r.get("bandwidth_utilization_pct", 0) > 70]
        if high_usage:
            insights.append(
                f"⚠️ {len(high_usage)} records show congestion risk (>70% bandwidth utilization)"
            )

    if analysis_type in ["comprehensive", "health"]:
        errors = [
            r for r in records if r.get("detected_error") not in ["none", None, ""]
        ]
        if errors:
            insights.append(
                f"🔴 {len(errors)} records contain errors requiring attention"
            )

    return insights


def _generate_recommendations(records: List[dict], focus: str) -> List[dict]:
    """Generate actionable recommendations."""
    recommendations = []

    if focus in ["all", "energy"]:
        low_usage = [r for r in records if r.get("bandwidth_utilization_pct", 100) < 30]
        if low_usage:
            towers = sorted(set(r.get("tower_id", "") for r in low_usage))[:5]
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Energy Optimization",
                    "title": "Implement Power Saving Mode",
                    "affected_towers": towers,
                    "expected_impact": "30-40% energy savings",
                    "action": "Schedule TRX shutdowns during low-traffic periods",
                }
            )

    if focus in ["all", "bandwidth"]:
        high_usage = [r for r in records if r.get("bandwidth_utilization_pct", 0) > 70]
        if high_usage:
            towers = sorted(set(r.get("tower_id", "") for r in high_usage))[:5]
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Congestion Management",
                    "title": "Prevent Network Congestion",
                    "affected_towers": towers,
                    "expected_impact": "Maintain QoS",
                    "action": "Enable load balancing and expand coverage",
                }
            )

    return recommendations[:5]


def _compare_metrics(records1: List[dict], records2: List[dict]) -> dict:
    """Compare metrics between two datasets."""
    if not records1 or not records2:
        return {}

    metrics = {}
    for metric in ["bandwidth_utilization_pct", "latency_ms"]:
        avg1 = sum(r.get(metric, 0) for r in records1) / len(records1)
        avg2 = sum(r.get(metric, 0) for r in records2) / len(records2)
        change = ((avg2 - avg1) / avg1 * 100) if avg1 != 0 else 0

        metrics[metric] = {
            "dataset1_avg": round(avg1, 2),
            "dataset2_avg": round(avg2, 2),
            "change_percent": round(change, 2),
        }

    return metrics


if __name__ == "__main__":
    print("Starting Principal Tools MCP Server...")
    print("Available tools:")
    print("  - Health Monitoring: check_system_health, get_agent_status")
    print("  - Remediation: restart_agent, redeploy_agent, reroute_traffic")
    print("  - Dashboard: generate_health_dashboard, get_system_metrics")
    print("  - JSON Processing: add_json_data, analyze_json_data_with_llm,")
    print("                     get_recommendations_from_json, compare_json_datasets")
    print("\nServer running on http://0.0.0.0:8000/mcp")

    mcp.run(transport="streamable-http")
