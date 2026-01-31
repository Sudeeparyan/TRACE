"""
TRACE AWS Production Configuration

Centralized configuration for all AWS services used in TRACE.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AWSConfig:
    """AWS Service Configuration"""
    
    # Environment
    environment: str = os.getenv('TRACE_ENV', 'production')
    region: str = os.getenv('AWS_REGION', 'us-east-1')
    
    # Bedrock Configuration
    bedrock_model_id: str = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
    bedrock_embedding_model: str = os.getenv('BEDROCK_EMBEDDING_MODEL', 'amazon.titan-embed-text-v2:0')
    
    # Timestream Configuration
    timestream_database: str = f"TRACE-Telemetry-{os.getenv('TRACE_ENV', 'production')}"
    timestream_tower_table: str = "TowerMetrics"
    timestream_agent_table: str = "AgentMetrics"
    timestream_retention_hours: int = 24  # Memory store retention
    timestream_retention_days: int = 365  # Magnetic store retention
    
    # DynamoDB Tables
    dynamodb_tower_config: str = f"TRACE-TowerConfig-{os.getenv('TRACE_ENV', 'production')}"
    dynamodb_agent_state: str = f"TRACE-AgentState-{os.getenv('TRACE_ENV', 'production')}"
    dynamodb_remediation_log: str = f"TRACE-RemediationLog-{os.getenv('TRACE_ENV', 'production')}"
    dynamodb_policies: str = f"TRACE-Policies-{os.getenv('TRACE_ENV', 'production')}"
    
    # Kinesis Configuration
    kinesis_telemetry_stream: str = f"TRACE-TelemetryStream-{os.getenv('TRACE_ENV', 'production')}"
    kinesis_shard_count: int = 2
    
    # IoT Core Configuration
    iot_thing_group: str = f"TRACE-Towers-{os.getenv('TRACE_ENV', 'production')}"
    iot_topic_prefix: str = "trace/telemetry"
    
    # S3 Buckets
    s3_data_bucket: str = f"trace-data-{os.getenv('TRACE_ENV', 'production')}"
    s3_models_bucket: str = f"trace-models-{os.getenv('TRACE_ENV', 'production')}"
    s3_frontend_bucket: str = f"trace-frontend-{os.getenv('TRACE_ENV', 'production')}"
    
    # Lambda Functions
    lambda_telemetry_processor: str = f"TRACE-TelemetryProcessor-{os.getenv('TRACE_ENV', 'production')}"
    lambda_health_monitor: str = f"TRACE-HealthMonitor-{os.getenv('TRACE_ENV', 'production')}"
    lambda_remediation: str = f"TRACE-Remediation-{os.getenv('TRACE_ENV', 'production')}"
    lambda_telemetry_query: str = f"TRACE-TelemetryQuery-{os.getenv('TRACE_ENV', 'production')}"
    lambda_energy_optimizer: str = f"TRACE-EnergyOptimizer-{os.getenv('TRACE_ENV', 'production')}"
    
    # API Gateway
    api_gateway_name: str = f"TRACE-API-{os.getenv('TRACE_ENV', 'production')}"
    websocket_api_name: str = f"TRACE-WebSocket-{os.getenv('TRACE_ENV', 'production')}"
    
    # Step Functions
    sfn_self_healing: str = f"TRACE-SelfHealing-{os.getenv('TRACE_ENV', 'production')}"
    sfn_energy_optimization: str = f"TRACE-EnergyOptimization-{os.getenv('TRACE_ENV', 'production')}"
    sfn_congestion_management: str = f"TRACE-CongestionManagement-{os.getenv('TRACE_ENV', 'production')}"
    
    # SNS Topics
    sns_alerts_topic: str = f"TRACE-Alerts-{os.getenv('TRACE_ENV', 'production')}"
    sns_critical_alerts: str = f"TRACE-CriticalAlerts-{os.getenv('TRACE_ENV', 'production')}"
    
    # SQS Queues
    sqs_remediation_queue: str = f"TRACE-RemediationQueue-{os.getenv('TRACE_ENV', 'production')}"
    
    # CloudWatch
    cloudwatch_namespace: str = "TRACE/Production"
    cloudwatch_log_group: str = f"/aws/trace/{os.getenv('TRACE_ENV', 'production')}"
    
    # Thresholds for anomaly detection
    threshold_cpu_warning: float = 75.0
    threshold_cpu_critical: float = 90.0
    threshold_latency_warning: float = 80.0  # ms
    threshold_latency_critical: float = 150.0  # ms
    threshold_utilization_warning: float = 75.0  # %
    threshold_utilization_critical: float = 90.0  # %
    threshold_packet_loss_warning: float = 1.0  # %
    threshold_packet_loss_critical: float = 3.0  # %
    threshold_temperature_warning: float = 55.0  # Celsius
    threshold_temperature_critical: float = 65.0  # Celsius


# Global configuration instance
config = AWSConfig()


def get_config() -> dict:
    """Get configuration as dictionary for easy access."""
    return {
        'environment': config.environment,
        'region': config.region,
        'bedrock_model_id': config.bedrock_model_id,
        'timestream_database': config.timestream_database,
        'timestream_tower_table': config.timestream_tower_table,
        'dynamodb_tower_config': config.dynamodb_tower_config,
        'dynamodb_agent_state': config.dynamodb_agent_state,
        'dynamodb_remediation_log': config.dynamodb_remediation_log,
        'kinesis_telemetry_stream': config.kinesis_telemetry_stream,
        'iot_thing_group': config.iot_thing_group,
        'iot_topic_prefix': config.iot_topic_prefix,
        's3_data_bucket': config.s3_data_bucket,
        'sns_alerts_topic': config.sns_alerts_topic,
        'cloudwatch_namespace': config.cloudwatch_namespace,
        'thresholds': {
            'cpu_warning': config.threshold_cpu_warning,
            'cpu_critical': config.threshold_cpu_critical,
            'latency_warning': config.threshold_latency_warning,
            'latency_critical': config.threshold_latency_critical,
            'utilization_warning': config.threshold_utilization_warning,
            'utilization_critical': config.threshold_utilization_critical,
            'packet_loss_warning': config.threshold_packet_loss_warning,
            'packet_loss_critical': config.threshold_packet_loss_critical,
            'temperature_warning': config.threshold_temperature_warning,
            'temperature_critical': config.threshold_temperature_critical,
        }
    }


# Bedrock Agent IDs (populated after deployment)
BEDROCK_AGENT_IDS = {
    'principal_agent': os.getenv('TRACE_PRINCIPAL_AGENT_ID'),
    'regional_coordinator': os.getenv('TRACE_REGIONAL_COORDINATOR_ID'),
    'monitor_agent': os.getenv('TRACE_MONITOR_AGENT_ID'),
    'predict_agent': os.getenv('TRACE_PREDICT_AGENT_ID'),
    'action_agent': os.getenv('TRACE_ACTION_AGENT_ID'),
}


# Tower Configuration (initial setup)
TOWER_CONFIG = {
    'TX001': {'region': 'R-N', 'latitude': 40.7128, 'longitude': -74.0060, 'capacity': 1000},
    'TX002': {'region': 'R-N', 'latitude': 40.7580, 'longitude': -73.9855, 'capacity': 1200},
    'TX003': {'region': 'R-S', 'latitude': 33.7490, 'longitude': -84.3880, 'capacity': 800},
    'TX004': {'region': 'R-S', 'latitude': 29.7604, 'longitude': -95.3698, 'capacity': 1500},
    'TX005': {'region': 'R-E', 'latitude': 42.3601, 'longitude': -71.0589, 'capacity': 1000},
    'TX006': {'region': 'R-E', 'latitude': 39.9526, 'longitude': -75.1652, 'capacity': 900},
    'TX007': {'region': 'R-W', 'latitude': 34.0522, 'longitude': -118.2437, 'capacity': 2000},
    'TX008': {'region': 'R-W', 'latitude': 37.7749, 'longitude': -122.4194, 'capacity': 1800},
    'TX009': {'region': 'R-C', 'latitude': 41.8781, 'longitude': -87.6298, 'capacity': 1400},
    'TX010': {'region': 'R-C', 'latitude': 39.7392, 'longitude': -104.9903, 'capacity': 1100},
}


# Region Configuration
REGION_CONFIG = {
    'R-N': {'name': 'North', 'coordinator': 'coord-north', 'towers': ['TX001', 'TX002']},
    'R-S': {'name': 'South', 'coordinator': 'coord-south', 'towers': ['TX003', 'TX004']},
    'R-E': {'name': 'East', 'coordinator': 'coord-east', 'towers': ['TX005', 'TX006']},
    'R-W': {'name': 'West', 'coordinator': 'coord-west', 'towers': ['TX007', 'TX008']},
    'R-C': {'name': 'Central', 'coordinator': 'coord-central', 'towers': ['TX009', 'TX010']},
}
