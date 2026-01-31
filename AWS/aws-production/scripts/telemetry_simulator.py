#!/usr/bin/env python3
"""
TRACE Real-Time Telemetry Simulator

This script generates REALISTIC telemetry data based on actual patterns:
- Time-of-day traffic patterns (peak hours, off-peak)
- Geographic patterns (different usage per region)
- Realistic metric correlations (CPU with users, power with TRX, etc.)
- Occasional anomalies based on configurable probability

Data is sent to REAL AWS services:
- Kinesis Data Streams (for Lambda processing)
- IoT Core (simulating tower sensors)

This replaces random.uniform() simulations with pattern-based realistic data.
"""

import json
import time
import math
import random
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse

# Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'production')
REGION = os.getenv('AWS_REGION', 'us-east-1')
KINESIS_STREAM = os.getenv('KINESIS_STREAM', f'TRACE-TelemetryStream-{ENVIRONMENT}')
IOT_TOPIC_PREFIX = os.getenv('IOT_TOPIC_PREFIX', 'trace/telemetry')

# Initialize AWS clients
kinesis = boto3.client('kinesis', region_name=REGION)
iot_client = boto3.client('iot-data', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)


# Tower configuration with realistic parameters
TOWER_CONFIG = {
    'TX001': {
        'region_id': 'R-N', 'capacity': 1000, 'total_trx': 8,
        'base_users': 450, 'peak_multiplier': 1.8, 'variance': 0.15,
        'lat': 40.7128, 'lon': -74.0060, 'city': 'New York'
    },
    'TX002': {
        'region_id': 'R-N', 'capacity': 1200, 'total_trx': 8,
        'base_users': 520, 'peak_multiplier': 1.6, 'variance': 0.12,
        'lat': 40.7580, 'lon': -73.9855, 'city': 'Manhattan'
    },
    'TX003': {
        'region_id': 'R-S', 'capacity': 800, 'total_trx': 6,
        'base_users': 300, 'peak_multiplier': 1.5, 'variance': 0.18,
        'lat': 33.7490, 'lon': -84.3880, 'city': 'Atlanta'
    },
    'TX004': {
        'region_id': 'R-S', 'capacity': 1500, 'total_trx': 10,
        'base_users': 680, 'peak_multiplier': 1.7, 'variance': 0.14,
        'lat': 29.7604, 'lon': -95.3698, 'city': 'Houston'
    },
    'TX005': {
        'region_id': 'R-E', 'capacity': 1000, 'total_trx': 8,
        'base_users': 400, 'peak_multiplier': 1.6, 'variance': 0.16,
        'lat': 42.3601, 'lon': -71.0589, 'city': 'Boston'
    },
    'TX006': {
        'region_id': 'R-E', 'capacity': 900, 'total_trx': 6,
        'base_users': 350, 'peak_multiplier': 1.5, 'variance': 0.17,
        'lat': 39.9526, 'lon': -75.1652, 'city': 'Philadelphia'
    },
    'TX007': {
        'region_id': 'R-W', 'capacity': 2000, 'total_trx': 12,
        'base_users': 900, 'peak_multiplier': 1.9, 'variance': 0.13,
        'lat': 34.0522, 'lon': -118.2437, 'city': 'Los Angeles'
    },
    'TX008': {
        'region_id': 'R-W', 'capacity': 1800, 'total_trx': 10,
        'base_users': 780, 'peak_multiplier': 1.8, 'variance': 0.14,
        'lat': 37.7749, 'lon': -122.4194, 'city': 'San Francisco'
    },
    'TX009': {
        'region_id': 'R-C', 'capacity': 1400, 'total_trx': 8,
        'base_users': 550, 'peak_multiplier': 1.7, 'variance': 0.15,
        'lat': 41.8781, 'lon': -87.6298, 'city': 'Chicago'
    },
    'TX010': {
        'region_id': 'R-C', 'capacity': 1100, 'total_trx': 8,
        'base_users': 420, 'peak_multiplier': 1.5, 'variance': 0.16,
        'lat': 39.7392, 'lon': -104.9903, 'city': 'Denver'
    },
}


def get_time_multiplier(hour: int) -> float:
    """
    Get traffic multiplier based on time of day.
    Models realistic usage patterns:
    - Low: 2am-6am (0.3-0.5x)
    - Rising: 6am-9am (0.5-1.0x)
    - Peak: 9am-12pm, 5pm-9pm (1.0-1.2x)
    - Medium: 12pm-5pm (0.8-1.0x)
    - Declining: 9pm-2am (0.6-0.3x)
    """
    if 2 <= hour < 6:
        return 0.3 + (hour - 2) * 0.05
    elif 6 <= hour < 9:
        return 0.5 + (hour - 6) * 0.17
    elif 9 <= hour < 12:
        return 1.0 + (hour - 9) * 0.07
    elif 12 <= hour < 17:
        return 0.9 - (hour - 12) * 0.02
    elif 17 <= hour < 21:
        return 0.8 + (hour - 17) * 0.1
    elif 21 <= hour < 24:
        return 1.1 - (hour - 21) * 0.2
    else:  # 0-2am
        return 0.5 - hour * 0.1


def calculate_connected_users(tower_config: dict, hour: int) -> int:
    """
    Calculate realistic connected users based on:
    - Base user count for the tower
    - Time of day multiplier
    - Random variance
    - Peak multiplier for busy towers
    """
    time_mult = get_time_multiplier(hour)
    base = tower_config['base_users']
    peak_mult = tower_config['peak_multiplier']
    variance = tower_config['variance']
    
    # Apply time multiplier with peak adjustment
    users = base * time_mult * (1 + (peak_mult - 1) * time_mult)
    
    # Add realistic variance
    users = users * (1 + random.uniform(-variance, variance))
    
    # Clamp to capacity
    return int(min(max(users, 0), tower_config['capacity']))


def calculate_cpu_usage(connected_users: int, capacity: int, active_trx: int) -> float:
    """
    CPU correlates with:
    - User load (primary factor)
    - Active TRX count
    """
    utilization = connected_users / capacity
    base_cpu = 25 + (utilization * 50)  # 25-75% based on utilization
    trx_factor = active_trx / 8 * 10  # +0-10% based on TRX
    
    return round(min(max(base_cpu + trx_factor + random.uniform(-5, 5), 15), 98), 2)


def calculate_latency(connected_users: int, capacity: int, cpu_usage: float) -> float:
    """
    Latency correlates with:
    - User load
    - CPU usage (processing delay)
    """
    utilization = connected_users / capacity
    base_latency = 15 + (utilization * 40)  # 15-55ms base
    cpu_factor = (cpu_usage - 50) * 0.5 if cpu_usage > 50 else 0  # +ms when CPU high
    
    return round(max(base_latency + cpu_factor + random.uniform(-5, 10), 10), 2)


def calculate_bandwidth_utilization(connected_users: int, capacity: int, hour: int) -> float:
    """
    Bandwidth usage patterns:
    - Correlates with users
    - Higher during peak streaming hours (evening)
    """
    user_factor = (connected_users / capacity) * 70
    
    # Evening streaming boost (7pm-11pm)
    streaming_boost = 10 if 19 <= hour <= 23 else 0
    
    return round(min(max(user_factor + streaming_boost + random.uniform(-5, 5), 5), 95), 2)


def calculate_power_consumption(active_trx: int, cpu_usage: float, temperature: float) -> float:
    """
    Power consumption based on:
    - Active TRX count (2.5 kW per TRX base)
    - CPU usage (processing power)
    - Cooling needs (temperature)
    """
    trx_power = active_trx * 2.5
    cpu_power = cpu_usage * 0.02  # Small additional for processing
    cooling_power = 0.1 * max(0, temperature - 40)  # Cooling kicks in above 40°C
    
    return round(trx_power + cpu_power + cooling_power + random.uniform(-0.5, 0.5), 2)


def calculate_temperature(ambient_temp: float, cpu_usage: float, active_trx: int) -> float:
    """
    Equipment temperature based on:
    - Ambient temperature
    - CPU usage (heat generation)
    - Active TRX (heat generation)
    """
    base_temp = ambient_temp + 10  # Equipment runs hotter than ambient
    cpu_heat = (cpu_usage - 50) * 0.1 if cpu_usage > 50 else 0
    trx_heat = active_trx * 0.5
    
    return round(base_temp + cpu_heat + trx_heat + random.uniform(-2, 2), 2)


def get_ambient_temperature(lat: float, hour: int) -> float:
    """
    Realistic ambient temperature based on latitude and time.
    """
    # Base temperature varies by latitude (warmer near equator)
    base_temp = 35 - abs(lat - 35) * 0.3
    
    # Daily temperature variation (cooler at night)
    if 6 <= hour <= 18:
        time_factor = math.sin((hour - 6) / 12 * math.pi) * 10
    else:
        time_factor = -5
    
    return base_temp + time_factor + random.uniform(-2, 2)


def inject_anomaly(telemetry: dict, anomaly_type: str) -> dict:
    """
    Inject a specific anomaly into telemetry data.
    """
    if anomaly_type == 'high_cpu':
        telemetry['cpu_util_pct'] = round(random.uniform(88, 98), 2)
        telemetry['latency_ms'] = round(telemetry['latency_ms'] * 1.5, 2)
    elif anomaly_type == 'high_latency':
        telemetry['latency_ms'] = round(random.uniform(120, 250), 2)
    elif anomaly_type == 'near_capacity':
        telemetry['connected_users'] = int(telemetry['capacity_users'] * random.uniform(0.92, 0.99))
        telemetry['cpu_util_pct'] = round(random.uniform(85, 95), 2)
    elif anomaly_type == 'packet_loss':
        telemetry['packet_loss_pct'] = round(random.uniform(2, 5), 2)
    elif anomaly_type == 'high_temperature':
        telemetry['temperature_celsius'] = round(random.uniform(58, 68), 2)
    elif anomaly_type == 'trx_failure':
        current_trx = telemetry.get('active_trx', 8)
        telemetry['active_trx'] = max(2, current_trx - random.randint(1, 3))
        telemetry['power_kw'] = round(telemetry['active_trx'] * 2.5, 2)
    
    telemetry['anomaly_injected'] = anomaly_type
    return telemetry


def generate_tower_telemetry(tower_id: str, tower_config: dict, 
                             inject_anomaly_type: Optional[str] = None) -> dict:
    """
    Generate realistic telemetry for a single tower.
    """
    now = datetime.utcnow()
    hour = now.hour
    
    # Get tower state from DynamoDB (for active_trx)
    active_trx = get_tower_active_trx(tower_id, tower_config['total_trx'])
    
    # Calculate correlated metrics
    connected_users = calculate_connected_users(tower_config, hour)
    capacity = tower_config['capacity']
    
    cpu_usage = calculate_cpu_usage(connected_users, capacity, active_trx)
    latency = calculate_latency(connected_users, capacity, cpu_usage)
    bandwidth = calculate_bandwidth_utilization(connected_users, capacity, hour)
    
    ambient_temp = get_ambient_temperature(tower_config['lat'], hour)
    temperature = calculate_temperature(ambient_temp, cpu_usage, active_trx)
    power = calculate_power_consumption(active_trx, cpu_usage, temperature)
    
    # RSRQ (signal quality) - generally good, occasional degradation
    rsrq = round(random.uniform(-12, -6) if random.random() > 0.1 else random.uniform(-18, -14), 2)
    
    # Packet loss - normally very low
    packet_loss = round(random.uniform(0, 0.5) if random.random() > 0.05 else random.uniform(0.5, 2), 3)
    
    telemetry = {
        'tower_id': tower_id,
        'region_id': tower_config['region_id'],
        'agent_id': f'agent-{tower_id.lower()}',
        'timestamp': now.isoformat() + 'Z',
        'connected_users': connected_users,
        'capacity_users': capacity,
        'utilization_pct': round((connected_users / capacity) * 100, 2),
        'cpu_util_pct': cpu_usage,
        'bandwidth_utilization_pct': bandwidth,
        'latency_ms': latency,
        'packet_loss_pct': packet_loss,
        'rsrq_db': rsrq,
        'power_voltage_v': round(48 + random.uniform(-0.5, 0.5), 2),
        'power_kw': power,
        'temperature_celsius': temperature,
        'active_trx': active_trx,
        'total_trx': tower_config['total_trx'],
    }
    
    # Inject anomaly if specified
    if inject_anomaly_type:
        telemetry = inject_anomaly(telemetry, inject_anomaly_type)
    
    return telemetry


def get_tower_active_trx(tower_id: str, default_total: int) -> int:
    """
    Get active TRX count from DynamoDB config.
    """
    try:
        table = dynamodb.Table(f'TRACE-TowerConfig-{ENVIRONMENT}')
        response = table.get_item(Key={'tower_id': tower_id})
        if 'Item' in response:
            return int(response['Item'].get('active_trx', default_total))
    except:
        pass
    return default_total


def send_to_kinesis(records: List[dict]) -> dict:
    """
    Send telemetry records to Kinesis Data Stream.
    """
    try:
        kinesis_records = [
            {
                'Data': json.dumps(record).encode('utf-8'),
                'PartitionKey': record.get('tower_id', 'default')
            }
            for record in records
        ]
        
        response = kinesis.put_records(
            StreamName=KINESIS_STREAM,
            Records=kinesis_records
        )
        
        failed = response.get('FailedRecordCount', 0)
        return {
            'success': True,
            'sent': len(records) - failed,
            'failed': failed
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def send_to_iot(tower_id: str, telemetry: dict) -> bool:
    """
    Publish telemetry to IoT Core (simulating tower sensor).
    """
    try:
        topic = f'{IOT_TOPIC_PREFIX}/{tower_id}'
        iot_client.publish(
            topic=topic,
            qos=1,
            payload=json.dumps(telemetry)
        )
        return True
    except Exception as e:
        print(f"  ⚠️ IoT publish failed: {str(e)}")
        return False


def run_simulation(duration_seconds: int = 300, interval: float = 5.0,
                   anomaly_probability: float = 0.05, verbose: bool = True):
    """
    Run continuous telemetry simulation.
    """
    print("=" * 70)
    print("  TRACE Real-Time Telemetry Simulator")
    print("=" * 70)
    print(f"  Environment: {ENVIRONMENT}")
    print(f"  Region: {REGION}")
    print(f"  Kinesis Stream: {KINESIS_STREAM}")
    print(f"  Duration: {duration_seconds}s | Interval: {interval}s")
    print(f"  Anomaly Probability: {anomaly_probability * 100}%")
    print(f"  Towers: {len(TOWER_CONFIG)}")
    print("=" * 70)
    
    start_time = time.time()
    iteration = 0
    total_sent = 0
    total_anomalies = 0
    
    anomaly_types = ['high_cpu', 'high_latency', 'near_capacity', 
                     'packet_loss', 'high_temperature', 'trx_failure']
    
    while (time.time() - start_time) < duration_seconds:
        iteration += 1
        
        if verbose:
            print(f"\n📊 Iteration {iteration} ({datetime.now().strftime('%H:%M:%S')})")
        
        records = []
        iteration_anomalies = 0
        
        for tower_id, tower_config in TOWER_CONFIG.items():
            # Determine if this tower gets an anomaly
            anomaly_type = None
            if random.random() < anomaly_probability:
                anomaly_type = random.choice(anomaly_types)
                iteration_anomalies += 1
                total_anomalies += 1
                if verbose:
                    print(f"  ⚠️ Injecting {anomaly_type} anomaly on {tower_id}")
            
            # Generate telemetry
            telemetry = generate_tower_telemetry(tower_id, tower_config, anomaly_type)
            records.append(telemetry)
            
            # Also send to IoT Core
            send_to_iot(tower_id, telemetry)
        
        # Send batch to Kinesis
        result = send_to_kinesis(records)
        
        if result['success']:
            total_sent += result['sent']
            if verbose:
                # Summary stats
                avg_cpu = sum(r['cpu_util_pct'] for r in records) / len(records)
                avg_users = sum(r['connected_users'] for r in records)
                avg_latency = sum(r['latency_ms'] for r in records) / len(records)
                
                print(f"  📤 Sent {result['sent']}/{len(records)} records to Kinesis")
                print(f"  📈 Avg CPU: {avg_cpu:.1f}% | Total Users: {avg_users} | Avg Latency: {avg_latency:.1f}ms")
                if iteration_anomalies > 0:
                    print(f"  🔴 Anomalies this iteration: {iteration_anomalies}")
        else:
            print(f"  ❌ Kinesis error: {result.get('error')}")
        
        # Wait for next interval
        time.sleep(interval)
    
    # Final summary
    print("\n" + "=" * 70)
    print("  ✅ Simulation Complete!")
    print("=" * 70)
    print(f"  Total Iterations: {iteration}")
    print(f"  Total Records Sent: {total_sent}")
    print(f"  Total Anomalies Injected: {total_anomalies}")
    print(f"  Duration: {time.time() - start_time:.1f}s")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='TRACE Telemetry Simulator')
    parser.add_argument('--duration', type=int, default=300,
                       help='Simulation duration in seconds (default: 300)')
    parser.add_argument('--interval', type=float, default=5.0,
                       help='Interval between data points in seconds (default: 5)')
    parser.add_argument('--anomaly-rate', type=float, default=0.05,
                       help='Probability of anomaly per tower per iteration (default: 0.05)')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously (ignore duration)')
    
    args = parser.parse_args()
    
    if args.continuous:
        duration = float('inf')
    else:
        duration = args.duration
    
    run_simulation(
        duration_seconds=duration if duration != float('inf') else 86400 * 365,
        interval=args.interval,
        anomaly_probability=args.anomaly_rate,
        verbose=not args.quiet
    )


if __name__ == '__main__':
    main()
