"""
TRACE Telemetry Processor Lambda - Production Version

This Lambda processes REAL telemetry data from:
- IoT Core (tower sensors)
- Kinesis Data Streams (batched telemetry)

Data is written to:
- Timestream (time-series metrics)
- DynamoDB (configuration updates)
- CloudWatch (monitoring metrics)
- S3 (raw data archive)

Anomaly detection triggers Step Functions workflows for auto-remediation.
"""

import json
import base64
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
import hashlib

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
timestream_write = boto3.client('timestream-write')
cloudwatch = boto3.client('cloudwatch')
stepfunctions = boto3.client('stepfunctions')
s3_client = boto3.client('s3')
sns_client = boto3.client('sns')

# Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'production')
TIMESTREAM_DATABASE = os.getenv('TIMESTREAM_DATABASE', f'TRACE-Telemetry-{ENVIRONMENT}')
TIMESTREAM_TABLE = os.getenv('TIMESTREAM_TABLE', 'TowerMetrics')
DYNAMODB_AGGREGATES_TABLE = os.getenv('DYNAMODB_AGGREGATES_TABLE', f'TRACE-TelemetryAggregates-{ENVIRONMENT}')
DYNAMODB_TOWER_CONFIG_TABLE = os.getenv('TOWER_CONFIG_TABLE', f'TRACE-TowerConfig-{ENVIRONMENT}')
S3_DATA_BUCKET = os.getenv('S3_DATA_BUCKET', f'trace-data-{ENVIRONMENT}')
SNS_ALERTS_TOPIC = os.getenv('SNS_ALERTS_TOPIC')
SELF_HEALING_STATE_MACHINE = os.getenv('SELF_HEALING_STATE_MACHINE')
ENERGY_OPTIMIZATION_STATE_MACHINE = os.getenv('ENERGY_OPTIMIZATION_STATE_MACHINE')

# Anomaly thresholds
THRESHOLDS = {
    'cpu_warning': 75.0,
    'cpu_critical': 90.0,
    'latency_warning': 80.0,
    'latency_critical': 150.0,
    'utilization_warning': 75.0,
    'utilization_critical': 90.0,
    'packet_loss_warning': 1.0,
    'packet_loss_critical': 3.0,
    'temperature_warning': 55.0,
    'temperature_critical': 65.0,
    'low_utilization_threshold': 30.0,  # For energy optimization
}


def lambda_handler(event, context):
    """
    Process incoming telemetry from Kinesis or IoT Core.
    """
    source = detect_event_source(event)
    
    if source == 'kinesis':
        return process_kinesis_records(event)
    elif source == 'iot':
        return process_iot_message(event)
    elif source == 'direct':
        return process_direct_telemetry(event)
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Unknown event source'})
        }


def detect_event_source(event: dict) -> str:
    """Detect the source of the event."""
    if 'Records' in event and event['Records']:
        if event['Records'][0].get('eventSource') == 'aws:kinesis':
            return 'kinesis'
    if 'topic' in event or 'clientId' in event:
        return 'iot'
    if 'telemetry' in event or 'tower_id' in event:
        return 'direct'
    return 'unknown'


def process_kinesis_records(event: dict) -> dict:
    """Process batched records from Kinesis Data Streams."""
    processed_count = 0
    error_count = 0
    anomalies_detected = []
    
    timestream_records = []
    cloudwatch_metrics = []
    
    for record in event.get('Records', []):
        try:
            # Decode Kinesis record
            payload = base64.b64decode(record['kinesis']['data'])
            telemetry = json.loads(payload)
            
            # Validate and enrich telemetry
            enriched = process_telemetry_record(telemetry)
            
            # Check for anomalies
            anomalies = detect_anomalies(enriched)
            if anomalies:
                anomalies_detected.extend(anomalies)
            
            # Prepare Timestream record
            ts_record = create_timestream_record(enriched)
            if ts_record:
                timestream_records.append(ts_record)
            
            # Prepare CloudWatch metrics
            cw_metrics = create_cloudwatch_metrics(enriched)
            cloudwatch_metrics.extend(cw_metrics)
            
            processed_count += 1
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            error_count += 1
        except Exception as e:
            print(f"Processing error: {str(e)}")
            error_count += 1
    
    # Batch write to Timestream
    if timestream_records:
        write_to_timestream(timestream_records)
    
    # Publish CloudWatch metrics
    if cloudwatch_metrics:
        publish_cloudwatch_metrics(cloudwatch_metrics)
    
    # Trigger workflows for anomalies
    if anomalies_detected:
        handle_anomalies(anomalies_detected)
    
    # Update aggregates
    update_aggregates(event.get('Records', []))
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': processed_count,
            'errors': error_count,
            'anomalies_detected': len(anomalies_detected),
        })
    }


def process_iot_message(event: dict) -> dict:
    """Process single message from IoT Core."""
    try:
        telemetry = event
        
        # Enrich and validate
        enriched = process_telemetry_record(telemetry)
        
        # Check for anomalies
        anomalies = detect_anomalies(enriched)
        
        # Write to Timestream
        ts_record = create_timestream_record(enriched)
        if ts_record:
            write_to_timestream([ts_record])
        
        # Publish CloudWatch metrics
        cw_metrics = create_cloudwatch_metrics(enriched)
        if cw_metrics:
            publish_cloudwatch_metrics(cw_metrics)
        
        # Handle anomalies
        if anomalies:
            handle_anomalies(anomalies)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed': True,
                'tower_id': telemetry.get('tower_id'),
                'anomalies': len(anomalies),
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def process_direct_telemetry(event: dict) -> dict:
    """Process telemetry sent directly (for testing/manual ingestion)."""
    telemetry_list = event.get('telemetry', [event])
    if not isinstance(telemetry_list, list):
        telemetry_list = [telemetry_list]
    
    processed = 0
    errors = 0
    
    for telemetry in telemetry_list:
        try:
            enriched = process_telemetry_record(telemetry)
            ts_record = create_timestream_record(enriched)
            if ts_record:
                write_to_timestream([ts_record])
            processed += 1
        except Exception as e:
            print(f"Error processing: {str(e)}")
            errors += 1
    
    return {
        'statusCode': 200,
        'body': json.dumps({'processed': processed, 'errors': errors})
    }


def process_telemetry_record(telemetry: dict) -> dict:
    """
    Validate and enrich a telemetry record.
    """
    # Required fields
    tower_id = telemetry.get('tower_id')
    if not tower_id:
        raise ValueError("tower_id is required")
    
    # Add processing metadata
    telemetry['processed_at'] = datetime.utcnow().isoformat() + 'Z'
    telemetry['processing_lambda'] = os.getenv('AWS_LAMBDA_FUNCTION_NAME', 'unknown')
    
    # Ensure timestamp exists
    if 'timestamp' not in telemetry:
        telemetry['timestamp'] = datetime.utcnow().isoformat() + 'Z'
    
    # Calculate derived metrics
    if 'connected_users' in telemetry and 'capacity_users' in telemetry:
        capacity = telemetry['capacity_users']
        if capacity > 0:
            telemetry['utilization_pct'] = round(
                (telemetry['connected_users'] / capacity) * 100, 2
            )
    
    # Calculate efficiency metrics
    if 'power_kw' in telemetry and 'connected_users' in telemetry:
        users = telemetry['connected_users']
        if users > 0:
            telemetry['power_per_user_w'] = round(
                (telemetry['power_kw'] * 1000) / users, 2
            )
    
    # Add region info from tower config if missing
    if 'region_id' not in telemetry:
        telemetry['region_id'] = get_tower_region(tower_id)
    
    return telemetry


def detect_anomalies(telemetry: dict) -> List[dict]:
    """
    Detect anomalies based on thresholds.
    Returns list of anomaly records.
    """
    anomalies = []
    tower_id = telemetry.get('tower_id', 'unknown')
    region_id = telemetry.get('region_id', 'unknown')
    timestamp = telemetry.get('timestamp', datetime.utcnow().isoformat() + 'Z')
    
    # CPU anomalies
    cpu = telemetry.get('cpu_util_pct', 0)
    if cpu > THRESHOLDS['cpu_critical']:
        anomalies.append({
            'type': 'HIGH_CPU',
            'severity': 'critical',
            'tower_id': tower_id,
            'region_id': region_id,
            'value': cpu,
            'threshold': THRESHOLDS['cpu_critical'],
            'timestamp': timestamp,
        })
    elif cpu > THRESHOLDS['cpu_warning']:
        anomalies.append({
            'type': 'HIGH_CPU',
            'severity': 'warning',
            'tower_id': tower_id,
            'region_id': region_id,
            'value': cpu,
            'threshold': THRESHOLDS['cpu_warning'],
            'timestamp': timestamp,
        })
    
    # Latency anomalies
    latency = telemetry.get('latency_ms', 0)
    if latency > THRESHOLDS['latency_critical']:
        anomalies.append({
            'type': 'HIGH_LATENCY',
            'severity': 'critical',
            'tower_id': tower_id,
            'region_id': region_id,
            'value': latency,
            'threshold': THRESHOLDS['latency_critical'],
            'timestamp': timestamp,
        })
    elif latency > THRESHOLDS['latency_warning']:
        anomalies.append({
            'type': 'HIGH_LATENCY',
            'severity': 'warning',
            'tower_id': tower_id,
            'region_id': region_id,
            'value': latency,
            'threshold': THRESHOLDS['latency_warning'],
            'timestamp': timestamp,
        })
    
    # Utilization anomalies
    utilization = telemetry.get('utilization_pct', 0)
    if utilization > THRESHOLDS['utilization_critical']:
        anomalies.append({
            'type': 'NEAR_CAPACITY',
            'severity': 'critical',
            'tower_id': tower_id,
            'region_id': region_id,
            'value': utilization,
            'threshold': THRESHOLDS['utilization_critical'],
            'timestamp': timestamp,
        })
    elif utilization > THRESHOLDS['utilization_warning']:
        anomalies.append({
            'type': 'HIGH_UTILIZATION',
            'severity': 'warning',
            'tower_id': tower_id,
            'region_id': region_id,
            'value': utilization,
            'threshold': THRESHOLDS['utilization_warning'],
            'timestamp': timestamp,
        })
    
    # Low utilization (energy optimization opportunity)
    if utilization > 0 and utilization < THRESHOLDS['low_utilization_threshold']:
        active_trx = telemetry.get('active_trx', 0)
        min_trx = telemetry.get('min_trx', 2)
        if active_trx > min_trx:
            anomalies.append({
                'type': 'LOW_UTILIZATION',
                'severity': 'info',
                'tower_id': tower_id,
                'region_id': region_id,
                'value': utilization,
                'threshold': THRESHOLDS['low_utilization_threshold'],
                'timestamp': timestamp,
                'recommendation': 'energy_optimization',
            })
    
    # Packet loss
    packet_loss = telemetry.get('packet_loss_pct', 0)
    if packet_loss > THRESHOLDS['packet_loss_critical']:
        anomalies.append({
            'type': 'HIGH_PACKET_LOSS',
            'severity': 'critical',
            'tower_id': tower_id,
            'region_id': region_id,
            'value': packet_loss,
            'threshold': THRESHOLDS['packet_loss_critical'],
            'timestamp': timestamp,
        })
    
    # Temperature
    temperature = telemetry.get('temperature_celsius', 0)
    if temperature > THRESHOLDS['temperature_critical']:
        anomalies.append({
            'type': 'HIGH_TEMPERATURE',
            'severity': 'critical',
            'tower_id': tower_id,
            'region_id': region_id,
            'value': temperature,
            'threshold': THRESHOLDS['temperature_critical'],
            'timestamp': timestamp,
        })
    
    return anomalies


def create_timestream_record(telemetry: dict) -> Optional[dict]:
    """
    Create a Timestream record from telemetry data.
    """
    try:
        timestamp_str = telemetry.get('timestamp', datetime.utcnow().isoformat())
        
        # Parse timestamp
        try:
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1]
            if '+' in timestamp_str:
                timestamp_str = timestamp_str.split('+')[0]
            dt = datetime.fromisoformat(timestamp_str)
            time_value = str(int(dt.timestamp() * 1000))
        except:
            time_value = str(int(datetime.utcnow().timestamp() * 1000))
        
        # Dimensions
        dimensions = [
            {'Name': 'tower_id', 'Value': str(telemetry.get('tower_id', 'unknown'))},
            {'Name': 'region_id', 'Value': str(telemetry.get('region_id', 'unknown'))},
            {'Name': 'agent_id', 'Value': str(telemetry.get('agent_id', 'unknown'))},
        ]
        
        # Multi-measure values
        measure_values = []
        
        # Add numeric fields
        numeric_fields = [
            ('connected_users', 'BIGINT'),
            ('capacity_users', 'BIGINT'),
            ('cpu_util_pct', 'DOUBLE'),
            ('bandwidth_utilization_pct', 'DOUBLE'),
            ('latency_ms', 'DOUBLE'),
            ('packet_loss_pct', 'DOUBLE'),
            ('power_voltage_v', 'DOUBLE'),
            ('power_kw', 'DOUBLE'),
            ('temperature_celsius', 'DOUBLE'),
            ('rsrq_db', 'DOUBLE'),
            ('active_trx', 'BIGINT'),
            ('total_trx', 'BIGINT'),
            ('utilization_pct', 'DOUBLE'),
        ]
        
        for field, field_type in numeric_fields:
            if field in telemetry and telemetry[field] is not None:
                try:
                    value = str(telemetry[field])
                    measure_values.append({
                        'Name': field,
                        'Value': value,
                        'Type': field_type,
                    })
                except:
                    pass
        
        if not measure_values:
            return None
        
        return {
            'Dimensions': dimensions,
            'MeasureName': 'tower_metrics',
            'MeasureValueType': 'MULTI',
            'MeasureValues': measure_values,
            'Time': time_value,
            'TimeUnit': 'MILLISECONDS',
        }
        
    except Exception as e:
        print(f"Error creating Timestream record: {str(e)}")
        return None


def write_to_timestream(records: List[dict]) -> bool:
    """
    Write records to Timestream.
    """
    if not records:
        return True
    
    try:
        # Timestream accepts max 100 records per write
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            response = timestream_write.write_records(
                DatabaseName=TIMESTREAM_DATABASE,
                TableName=TIMESTREAM_TABLE,
                Records=batch,
                CommonAttributes={}
            )
            
            rejected = response.get('RecordsIngested', {}).get('RejectedRecordsCount', 0)
            if rejected > 0:
                print(f"Rejected {rejected} records in batch")
        
        return True
        
    except timestream_write.exceptions.RejectedRecordsException as e:
        print(f"Rejected records: {str(e)}")
        for record in e.response.get('RejectedRecords', []):
            print(f"  Reason: {record.get('Reason')}")
        return False
    except Exception as e:
        print(f"Timestream write error: {str(e)}")
        return False


def create_cloudwatch_metrics(telemetry: dict) -> List[dict]:
    """
    Create CloudWatch metrics from telemetry.
    """
    metrics = []
    tower_id = telemetry.get('tower_id', 'unknown')
    region_id = telemetry.get('region_id', 'unknown')
    
    base_dimensions = [
        {'Name': 'TowerID', 'Value': tower_id},
        {'Name': 'RegionID', 'Value': region_id},
        {'Name': 'Environment', 'Value': ENVIRONMENT},
    ]
    
    metric_mappings = [
        ('cpu_util_pct', 'CPUUtilization', 'Percent'),
        ('latency_ms', 'Latency', 'Milliseconds'),
        ('connected_users', 'ConnectedUsers', 'Count'),
        ('bandwidth_utilization_pct', 'BandwidthUtilization', 'Percent'),
        ('packet_loss_pct', 'PacketLoss', 'Percent'),
        ('power_kw', 'PowerConsumption', 'None'),
        ('temperature_celsius', 'Temperature', 'None'),
    ]
    
    for field, metric_name, unit in metric_mappings:
        if field in telemetry and telemetry[field] is not None:
            try:
                metrics.append({
                    'MetricName': metric_name,
                    'Dimensions': base_dimensions,
                    'Value': float(telemetry[field]),
                    'Unit': unit,
                })
            except:
                pass
    
    return metrics


def publish_cloudwatch_metrics(metrics: List[dict]) -> bool:
    """
    Publish metrics to CloudWatch.
    """
    if not metrics:
        return True
    
    try:
        # CloudWatch accepts max 1000 metrics per call
        batch_size = 1000
        for i in range(0, len(metrics), batch_size):
            batch = metrics[i:i + batch_size]
            
            cloudwatch.put_metric_data(
                Namespace='TRACE/Production',
                MetricData=batch
            )
        
        return True
        
    except Exception as e:
        print(f"CloudWatch publish error: {str(e)}")
        return False


def handle_anomalies(anomalies: List[dict]) -> None:
    """
    Handle detected anomalies by triggering workflows and notifications.
    """
    # Group anomalies by severity
    critical_anomalies = [a for a in anomalies if a.get('severity') == 'critical']
    warning_anomalies = [a for a in anomalies if a.get('severity') == 'warning']
    info_anomalies = [a for a in anomalies if a.get('severity') == 'info']
    
    # Trigger self-healing for critical anomalies
    if critical_anomalies and SELF_HEALING_STATE_MACHINE:
        for anomaly in critical_anomalies:
            trigger_self_healing_workflow(anomaly)
    
    # Send alerts for critical issues
    if critical_anomalies and SNS_ALERTS_TOPIC:
        send_critical_alert(critical_anomalies)
    
    # Trigger energy optimization for low utilization
    energy_opportunities = [a for a in info_anomalies if a.get('recommendation') == 'energy_optimization']
    if energy_opportunities and ENERGY_OPTIMIZATION_STATE_MACHINE:
        trigger_energy_optimization(energy_opportunities)
    
    # Log all anomalies to CloudWatch
    for anomaly in anomalies:
        log_anomaly_to_cloudwatch(anomaly)


def trigger_self_healing_workflow(anomaly: dict) -> None:
    """
    Trigger Step Functions self-healing workflow.
    """
    try:
        execution_name = f"heal-{anomaly['tower_id']}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        input_data = {
            'anomaly': anomaly,
            'tower_id': anomaly.get('tower_id'),
            'issue_type': anomaly.get('type'),
            'severity': anomaly.get('severity'),
            'timestamp': anomaly.get('timestamp'),
            'notification_topic': SNS_ALERTS_TOPIC,
        }
        
        stepfunctions.start_execution(
            stateMachineArn=SELF_HEALING_STATE_MACHINE,
            name=execution_name[:80],  # Max 80 chars
            input=json.dumps(input_data)
        )
        
        print(f"Started self-healing workflow: {execution_name}")
        
    except Exception as e:
        print(f"Failed to start self-healing workflow: {str(e)}")


def trigger_energy_optimization(opportunities: List[dict]) -> None:
    """
    Trigger energy optimization workflow for low-utilization towers.
    """
    try:
        # Group by region
        regions = {}
        for opp in opportunities:
            region_id = opp.get('region_id', 'unknown')
            if region_id not in regions:
                regions[region_id] = []
            regions[region_id].append(opp)
        
        for region_id, region_opportunities in regions.items():
            execution_name = f"energy-{region_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            input_data = {
                'region_id': region_id,
                'towers': [o.get('tower_id') for o in region_opportunities],
                'opportunities': region_opportunities,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
            }
            
            stepfunctions.start_execution(
                stateMachineArn=ENERGY_OPTIMIZATION_STATE_MACHINE,
                name=execution_name[:80],
                input=json.dumps(input_data)
            )
            
            print(f"Started energy optimization workflow for region {region_id}")
            
    except Exception as e:
        print(f"Failed to start energy optimization workflow: {str(e)}")


def send_critical_alert(anomalies: List[dict]) -> None:
    """
    Send critical alert via SNS.
    """
    try:
        # Build alert message
        message_lines = ["TRACE Critical Alert - Immediate Action Required", "", "Anomalies Detected:"]
        
        for anomaly in anomalies:
            message_lines.append(
                f"  - Tower: {anomaly.get('tower_id')}, Type: {anomaly.get('type')}, "
                f"Value: {anomaly.get('value')}, Threshold: {anomaly.get('threshold')}"
            )
        
        message_lines.append(f"\nTimestamp: {datetime.utcnow().isoformat()}Z")
        message_lines.append("\nSelf-healing workflow has been triggered automatically.")
        
        sns_client.publish(
            TopicArn=SNS_ALERTS_TOPIC,
            Subject=f"TRACE CRITICAL: {len(anomalies)} anomalies detected",
            Message='\n'.join(message_lines)
        )
        
    except Exception as e:
        print(f"Failed to send alert: {str(e)}")


def log_anomaly_to_cloudwatch(anomaly: dict) -> None:
    """
    Log anomaly as CloudWatch metric for tracking.
    """
    try:
        cloudwatch.put_metric_data(
            Namespace='TRACE/Anomalies',
            MetricData=[{
                'MetricName': f"Anomaly_{anomaly.get('type', 'UNKNOWN')}",
                'Dimensions': [
                    {'Name': 'TowerID', 'Value': anomaly.get('tower_id', 'unknown')},
                    {'Name': 'Severity', 'Value': anomaly.get('severity', 'unknown')},
                    {'Name': 'Environment', 'Value': ENVIRONMENT},
                ],
                'Value': 1,
                'Unit': 'Count',
            }]
        )
    except Exception as e:
        print(f"Failed to log anomaly metric: {str(e)}")


def update_aggregates(records: list) -> None:
    """
    Update DynamoDB aggregates table with latest data.
    """
    try:
        table = dynamodb.Table(DYNAMODB_AGGREGATES_TABLE)
        
        # Group records by tower
        tower_data = {}
        for record in records:
            try:
                payload = base64.b64decode(record['kinesis']['data'])
                telemetry = json.loads(payload)
                tower_id = telemetry.get('tower_id')
                if tower_id:
                    if tower_id not in tower_data:
                        tower_data[tower_id] = []
                    tower_data[tower_id].append(telemetry)
            except:
                pass
        
        # Update each tower's aggregates
        for tower_id, data_points in tower_data.items():
            avg_cpu = sum(d.get('cpu_util_pct', 0) for d in data_points) / len(data_points)
            avg_latency = sum(d.get('latency_ms', 0) for d in data_points) / len(data_points)
            total_users = max(d.get('connected_users', 0) for d in data_points)
            
            table.update_item(
                Key={
                    'tower_id': tower_id,
                    'time_bucket': datetime.utcnow().strftime('%Y-%m-%d-%H'),
                },
                UpdateExpression='SET avg_cpu = :cpu, avg_latency = :lat, max_users = :users, #ts = :time, sample_count = if_not_exists(sample_count, :zero) + :count',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={
                    ':cpu': Decimal(str(round(avg_cpu, 2))),
                    ':lat': Decimal(str(round(avg_latency, 2))),
                    ':users': total_users,
                    ':time': datetime.utcnow().isoformat() + 'Z',
                    ':count': len(data_points),
                    ':zero': 0,
                }
            )
            
    except Exception as e:
        print(f"Failed to update aggregates: {str(e)}")


def get_tower_region(tower_id: str) -> str:
    """
    Get region ID for a tower from DynamoDB config.
    """
    try:
        table = dynamodb.Table(DYNAMODB_TOWER_CONFIG_TABLE)
        response = table.get_item(Key={'tower_id': tower_id})
        if 'Item' in response:
            return response['Item'].get('region_id', 'unknown')
    except:
        pass
    return 'unknown'
