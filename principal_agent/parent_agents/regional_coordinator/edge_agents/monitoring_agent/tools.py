"""
Monitoring Agent Tools

Tools for collecting RAN KPIs and power metrics.
"""

import random
from datetime import datetime
from typing import Any, Dict


def collect_ran_kpis(tower_id: str = "tower_1") -> Dict[str, Any]:
    """
    Collect Radio Access Network Key Performance Indicators.

    Args:
        tower_id: ID of the tower to monitor

    Returns:
        Dict containing RAN KPIs.
    """
    return {
        "tower_id": tower_id,
        "timestamp": datetime.now().isoformat(),
        "kpis": {
            "active_connections": random.randint(500, 2500),
            "throughput_mbps": random.uniform(100, 1000),
            "latency_ms": random.randint(10, 100),
            "packet_loss_percent": random.uniform(0, 2),
            "signal_strength_dbm": random.uniform(-90, -50),
            "handover_success_rate": random.uniform(0.95, 0.99),
            "call_drop_rate": random.uniform(0, 0.02),
            "resource_utilization_percent": random.uniform(30, 90),
        },
    }


def collect_power_metrics(tower_id: str = "tower_1") -> Dict[str, Any]:
    """
    Collect power consumption metrics from tower equipment.

    Args:
        tower_id: ID of the tower to monitor

    Returns:
        Dict containing power metrics.
    """
    return {
        "tower_id": tower_id,
        "timestamp": datetime.now().isoformat(),
        "power_metrics": {
            "total_consumption_kwh": random.uniform(50, 250),
            "active_transceivers": random.randint(4, 12),
            "idle_transceivers": random.randint(0, 4),
            "power_saving_mode": random.choice([True, False]),
            "efficiency_percent": random.uniform(70, 95),
            "temperature_celsius": random.randint(35, 65),
            "cooling_power_kwh": random.uniform(10, 50),
        },
    }


def stream_telemetry(
    data: str = "{}", destination: str = "parent_agent"
) -> Dict[str, Any]:
    """
    Stream telemetry data to parent agent or monitoring system.

    Args:
        data: Telemetry data as JSON string to stream
        destination: Destination for the data

    Returns:
        Dict containing streaming status.
    """
    import json

    try:
        data_dict = json.loads(data) if isinstance(data, str) else data
    except json.JSONDecodeError:
        data_dict = {}

    success = random.choice([True, True, True, True, False])  # 80% success rate

    return {
        "operation": "stream_telemetry",
        "destination": destination,
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "bytes_sent": random.randint(1000, 10000) if success else 0,
        "latency_ms": random.randint(5, 50) if success else None,
        "message": "Telemetry streamed successfully" if success else "Streaming failed",
    }
