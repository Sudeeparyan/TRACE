"""
TRACE Analytics Lambda - Production Version

This Lambda function provides analytics and reporting:
- Historical telemetry trends from Timestream
- Traffic analysis for energy optimization
- Energy savings calculations
- Predictive issue detection

All data comes from REAL AWS services (Timestream, DynamoDB, CloudWatch).
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional

# Initialize AWS clients
timestream_query = boto3.client('timestream-query')
dynamodb = boto3.resource('dynamodb')
cloudwatch = boto3.client('cloudwatch')

# Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'production')
TIMESTREAM_DATABASE = os.getenv('TIMESTREAM_DATABASE', f'TRACE-Telemetry-{ENVIRONMENT}')
TIMESTREAM_TABLE = os.getenv('TIMESTREAM_TABLE', 'TowerMetrics')
ENERGY_LOG_TABLE = os.getenv('ENERGY_LOG_TABLE', f'TRACE-EnergyLog-{ENVIRONMENT}')

# Tower power specifications (in kW)
TOWER_POWER_SPECS = {
    'full_power_kw': 4.5,
    'eco_power_kw': 2.8,
    'sleep_power_kw': 1.2,
    'trx_power_kw': 0.35,  # per active TRX
}


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def lambda_handler(event, context):
    """
    Main Lambda handler for analytics.
    
    Supported actions:
    - get_telemetry_history: Historical metrics from Timestream
    - analyze_traffic: Traffic pattern analysis
    - calculate_energy_savings: Energy savings from optimizations
    - get_trends: Metric trends over time
    - predict_issues: Predictive issue detection
    """
    
    action = event.get('action', 'get_telemetry_history')
    parameters = event.get('parameters', {})
    
    # Handle API Gateway format
    if 'httpMethod' in event:
        path = event.get('path', '')
        query_params = event.get('queryStringParameters', {}) or {}
        
        if '/telemetry/history' in path:
            action = 'get_telemetry_history'
            parameters = query_params
        elif '/analytics/trends' in path:
            action = 'get_trends'
            parameters = query_params
    
    # Handle Bedrock action group format
    if 'actionGroup' in event:
        action = event.get('function', 'get_telemetry_history')
        parameters = {p['name']: p['value'] for p in event.get('parameters', [])}
    
    handlers = {
        'get_telemetry_history': get_telemetry_history,
        'analyze_traffic': analyze_traffic,
        'calculate_energy_savings': calculate_energy_savings,
        'get_trends': get_trends,
        'predict_issues': predict_issues,
        'get_capacity_forecast': get_capacity_forecast,
    }
    
    handler = handlers.get(action, get_telemetry_history)
    
    try:
        result = handler(parameters)
        return format_response(200, result)
    except Exception as e:
        return format_response(500, {
            'error': str(e),
            'status': 'error',
            'action': action
        })


def get_telemetry_history(params: dict) -> dict:
    """
    Get historical telemetry data from Timestream.
    """
    tower_id = params.get('tower_id')
    metric = params.get('metric', 'cpu_utilization')
    period = params.get('period', '24h')
    
    # Parse period
    period_mapping = {
        '1h': '1h',
        '6h': '6h',
        '24h': '24h',
        '7d': '7d',
        '30d': '30d'
    }
    time_ago = period_mapping.get(period, '24h')
    
    # Map metric names
    metric_mapping = {
        'cpu': 'cpu_utilization',
        'cpu_utilization': 'cpu_utilization',
        'latency': 'latency_ms',
        'latency_ms': 'latency_ms',
        'power': 'power_consumption_kw',
        'power_consumption': 'power_consumption_kw',
        'users': 'connected_users',
        'traffic': 'connected_users',
        'temperature': 'temperature_celsius'
    }
    measure_name = metric_mapping.get(metric, metric)
    
    # Build query
    tower_filter = f"AND tower_id = '{tower_id}'" if tower_id else ""
    
    query = f"""
        SELECT 
            tower_id,
            bin(time, 5m) AS time_bucket,
            AVG(measure_value::double) AS avg_value,
            MIN(measure_value::double) AS min_value,
            MAX(measure_value::double) AS max_value
        FROM "{TIMESTREAM_DATABASE}"."{TIMESTREAM_TABLE}"
        WHERE measure_name = '{measure_name}'
          AND time > ago({time_ago})
          {tower_filter}
        GROUP BY tower_id, bin(time, 5m)
        ORDER BY time_bucket DESC
        LIMIT 1000
    """
    
    try:
        response = timestream_query.query(QueryString=query)
        
        # Parse results
        data_points = []
        for row in response.get('Rows', []):
            data = row.get('Data', [])
            if len(data) >= 5:
                data_points.append({
                    'tower_id': data[0].get('ScalarValue', ''),
                    'timestamp': data[1].get('ScalarValue', ''),
                    'avg_value': float(data[2].get('ScalarValue', 0)),
                    'min_value': float(data[3].get('ScalarValue', 0)),
                    'max_value': float(data[4].get('ScalarValue', 0)),
                })
        
        return {
            'status': 'success',
            'metric': measure_name,
            'period': period,
            'tower_id': tower_id,
            'data_points': data_points,
            'count': len(data_points),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
    except timestream_query.exceptions.ValidationException as e:
        # Database might not exist yet
        return {
            'status': 'no_data',
            'message': 'Telemetry database not initialized or no data available',
            'metric': measure_name,
            'period': period,
            'data_points': [],
            'count': 0
        }


def analyze_traffic(params: dict) -> dict:
    """
    Analyze traffic patterns for energy optimization decisions.
    """
    region = params.get('region', 'all')
    time_window = params.get('time_window', '1h')
    
    # Get current traffic levels per tower
    region_filter = f"AND tower_id LIKE '%-{region[0].upper()}-%'" if region != 'all' else ""
    
    query = f"""
        SELECT 
            tower_id,
            AVG(CASE WHEN measure_name = 'connected_users' THEN measure_value::double END) AS avg_users,
            MAX(CASE WHEN measure_name = 'capacity_users' THEN measure_value::double END) AS capacity,
            AVG(CASE WHEN measure_name = 'cpu_utilization' THEN measure_value::double END) AS avg_cpu,
            MAX(CASE WHEN measure_name = 'active_trx' THEN measure_value::double END) AS active_trx,
            AVG(CASE WHEN measure_name = 'power_consumption_kw' THEN measure_value::double END) AS avg_power
        FROM "{TIMESTREAM_DATABASE}"."{TIMESTREAM_TABLE}"
        WHERE time > ago({time_window})
          {region_filter}
        GROUP BY tower_id
    """
    
    try:
        response = timestream_query.query(QueryString=query)
        
        towers = []
        total_users = 0
        total_capacity = 0
        
        for row in response.get('Rows', []):
            data = row.get('Data', [])
            if len(data) >= 6:
                tower_id = data[0].get('ScalarValue', '')
                users = float(data[1].get('ScalarValue', 0) or 0)
                capacity = float(data[2].get('ScalarValue', 100) or 100)
                cpu = float(data[3].get('ScalarValue', 0) or 0)
                trx = int(float(data[4].get('ScalarValue', 8) or 8))
                power = float(data[5].get('ScalarValue', 0) or 0)
                
                utilization = (users / capacity * 100) if capacity > 0 else 0
                
                towers.append({
                    'tower_id': tower_id,
                    'connected_users': int(users),
                    'capacity_users': int(capacity),
                    'current_utilization': round(utilization, 2),
                    'cpu_utilization': round(cpu, 2),
                    'active_trx': trx,
                    'power_kw': round(power, 2),
                    'power_mode': 'full' if cpu > 75 else ('eco' if cpu < 40 else 'normal')
                })
                
                total_users += users
                total_capacity += capacity
        
        # Determine overall traffic level
        overall_utilization = (total_users / total_capacity * 100) if total_capacity > 0 else 0
        
        if overall_utilization < 30:
            traffic_level = 'low'
        elif overall_utilization < 60:
            traffic_level = 'medium'
        else:
            traffic_level = 'high'
        
        return {
            'status': 'success',
            'region': region,
            'time_window': time_window,
            'traffic_level': traffic_level,
            'overall_utilization': round(overall_utilization, 2),
            'total_users': int(total_users),
            'total_capacity': int(total_capacity),
            'towers': towers,
            'tower_count': len(towers),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
    except timestream_query.exceptions.ValidationException:
        return {
            'status': 'no_data',
            'region': region,
            'traffic_level': 'unknown',
            'towers': [],
            'message': 'No telemetry data available'
        }


def calculate_energy_savings(params: dict) -> dict:
    """
    Calculate energy savings from optimization actions.
    """
    optimization_results = params.get('optimization_results', [])
    region = params.get('region', 'all')
    
    total_before_kw = 0
    total_after_kw = 0
    towers_optimized = 0
    
    for result in optimization_results:
        if isinstance(result, dict):
            # Get power before/after
            if result.get('action') == 'skipped':
                continue
            
            tower = result.get('tower', result)
            power_before = tower.get('power_kw', TOWER_POWER_SPECS['full_power_kw'])
            
            # Calculate new power based on mode
            mode = result.get('mode', 'eco')
            if mode == 'eco':
                power_after = TOWER_POWER_SPECS['eco_power_kw']
            elif mode == 'sleep':
                power_after = TOWER_POWER_SPECS['sleep_power_kw']
            else:
                power_after = power_before
            
            total_before_kw += power_before
            total_after_kw += power_after
            towers_optimized += 1
    
    # Calculate savings
    savings_kw = total_before_kw - total_after_kw
    savings_percent = (savings_kw / total_before_kw * 100) if total_before_kw > 0 else 0
    
    # Estimate daily/monthly savings
    hours_per_day = 24
    days_per_month = 30
    kwh_cost = 0.12  # $/kWh estimate
    
    daily_kwh_savings = savings_kw * hours_per_day
    monthly_kwh_savings = daily_kwh_savings * days_per_month
    monthly_cost_savings = monthly_kwh_savings * kwh_cost
    
    return {
        'status': 'success',
        'region': region,
        'towers_optimized': towers_optimized,
        'power_before_kw': round(total_before_kw, 2),
        'power_after_kw': round(total_after_kw, 2),
        'estimated_kwh': round(daily_kwh_savings, 2),
        'percentage': round(savings_percent, 2),
        'monthly_kwh_savings': round(monthly_kwh_savings, 2),
        'monthly_cost_savings_usd': round(monthly_cost_savings, 2),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }


def get_trends(params: dict) -> dict:
    """
    Get metric trends over time.
    """
    metric = params.get('metric', 'cpu')
    period = params.get('period', '24h')
    tower_id = params.get('tower_id')
    
    # Map metric names
    metric_mapping = {
        'cpu': 'cpu_utilization',
        'latency': 'latency_ms',
        'power': 'power_consumption_kw',
        'signal': 'rsrp_dbm',
        'traffic': 'connected_users'
    }
    measure_name = metric_mapping.get(metric, metric)
    
    # Time bucket based on period
    bucket_mapping = {
        '1h': '5m',
        '6h': '15m',
        '24h': '1h',
        '7d': '6h'
    }
    bucket = bucket_mapping.get(period, '1h')
    
    tower_filter = f"AND tower_id = '{tower_id}'" if tower_id else ""
    
    query = f"""
        SELECT 
            bin(time, {bucket}) AS time_bucket,
            AVG(measure_value::double) AS avg_value,
            STDDEV(measure_value::double) AS stddev_value
        FROM "{TIMESTREAM_DATABASE}"."{TIMESTREAM_TABLE}"
        WHERE measure_name = '{measure_name}'
          AND time > ago({period})
          {tower_filter}
        GROUP BY bin(time, {bucket})
        ORDER BY time_bucket ASC
    """
    
    try:
        response = timestream_query.query(QueryString=query)
        
        trend_data = []
        values = []
        
        for row in response.get('Rows', []):
            data = row.get('Data', [])
            if len(data) >= 3:
                timestamp = data[0].get('ScalarValue', '')
                avg_val = float(data[1].get('ScalarValue', 0) or 0)
                stddev_val = float(data[2].get('ScalarValue', 0) or 0)
                
                trend_data.append({
                    'timestamp': timestamp,
                    'value': round(avg_val, 2),
                    'stddev': round(stddev_val, 2)
                })
                values.append(avg_val)
        
        # Calculate trend direction
        if len(values) >= 2:
            first_half = sum(values[:len(values)//2]) / (len(values)//2) if values else 0
            second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2) if values else 0
            
            if second_half > first_half * 1.1:
                trend = 'increasing'
            elif second_half < first_half * 0.9:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'status': 'success',
            'metric': measure_name,
            'period': period,
            'tower_id': tower_id,
            'trend': trend,
            'data': trend_data,
            'summary': {
                'avg': round(sum(values) / len(values), 2) if values else 0,
                'min': round(min(values), 2) if values else 0,
                'max': round(max(values), 2) if values else 0
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
    except timestream_query.exceptions.ValidationException:
        return {
            'status': 'no_data',
            'metric': measure_name,
            'period': period,
            'trend': 'unknown',
            'data': []
        }


def predict_issues(params: dict) -> dict:
    """
    Predict potential issues based on current trends.
    """
    tower_id = params.get('tower_id')
    horizon = params.get('horizon', '1h')
    
    # Get recent trends for key metrics
    predictions = []
    
    metrics_to_check = [
        ('cpu_utilization', 90, 'CPU overload'),
        ('latency_ms', 150, 'High latency'),
        ('temperature_celsius', 65, 'Overheating'),
        ('packet_loss_pct', 3, 'Network degradation')
    ]
    
    tower_filter = f"AND tower_id = '{tower_id}'" if tower_id else ""
    
    for metric, threshold, issue_name in metrics_to_check:
        query = f"""
            SELECT 
                tower_id,
                AVG(measure_value::double) AS recent_avg,
                MAX(measure_value::double) AS recent_max,
                STDDEV(measure_value::double) AS stddev
            FROM "{TIMESTREAM_DATABASE}"."{TIMESTREAM_TABLE}"
            WHERE measure_name = '{metric}'
              AND time > ago(1h)
              {tower_filter}
            GROUP BY tower_id
        """
        
        try:
            response = timestream_query.query(QueryString=query)
            
            for row in response.get('Rows', []):
                data = row.get('Data', [])
                if len(data) >= 4:
                    tid = data[0].get('ScalarValue', '')
                    avg_val = float(data[1].get('ScalarValue', 0) or 0)
                    max_val = float(data[2].get('ScalarValue', 0) or 0)
                    stddev = float(data[3].get('ScalarValue', 0) or 0)
                    
                    # Predict if trending toward threshold
                    predicted_value = avg_val + (stddev * 1.5)  # Simple prediction
                    
                    if predicted_value >= threshold or max_val >= threshold * 0.95:
                        risk = 'high' if max_val >= threshold else 'medium'
                        predictions.append({
                            'tower_id': tid,
                            'issue': issue_name,
                            'metric': metric,
                            'current_avg': round(avg_val, 2),
                            'current_max': round(max_val, 2),
                            'predicted': round(predicted_value, 2),
                            'threshold': threshold,
                            'risk_level': risk,
                            'horizon': horizon,
                            'recommended_action': get_recommended_action(metric)
                        })
                        
        except Exception:
            continue
    
    return {
        'status': 'success',
        'tower_id': tower_id,
        'horizon': horizon,
        'predictions': predictions,
        'prediction_count': len(predictions),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }


def get_capacity_forecast(params: dict) -> dict:
    """
    Forecast capacity needs based on historical patterns.
    """
    tower_id = params.get('tower_id')
    horizon = params.get('horizon', '24h')
    
    tower_filter = f"AND tower_id = '{tower_id}'" if tower_id else ""
    
    # Get hourly patterns from past week
    query = f"""
        SELECT 
            tower_id,
            DATE_TRUNC('hour', time) AS hour,
            AVG(measure_value::double) AS avg_users
        FROM "{TIMESTREAM_DATABASE}"."{TIMESTREAM_TABLE}"
        WHERE measure_name = 'connected_users'
          AND time > ago(7d)
          {tower_filter}
        GROUP BY tower_id, DATE_TRUNC('hour', time)
        ORDER BY hour
    """
    
    try:
        response = timestream_query.query(QueryString=query)
        
        # Process and create forecast
        hourly_patterns = {}
        
        for row in response.get('Rows', []):
            data = row.get('Data', [])
            if len(data) >= 3:
                tid = data[0].get('ScalarValue', '')
                hour_str = data[1].get('ScalarValue', '')
                users = float(data[2].get('ScalarValue', 0) or 0)
                
                if tid not in hourly_patterns:
                    hourly_patterns[tid] = []
                hourly_patterns[tid].append({
                    'hour': hour_str,
                    'users': round(users)
                })
        
        return {
            'status': 'success',
            'tower_id': tower_id,
            'horizon': horizon,
            'forecasts': hourly_patterns,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'forecasts': {}
        }


def get_recommended_action(metric: str) -> str:
    """Get recommended action for a metric issue."""
    recommendations = {
        'cpu_utilization': 'Scale up compute resources or reroute traffic',
        'latency_ms': 'Check backhaul connection, consider traffic rerouting',
        'temperature_celsius': 'Increase cooling or reduce power mode',
        'packet_loss_pct': 'Check radio hardware, adjust antenna configuration'
    }
    return recommendations.get(metric, 'Monitor and investigate')


def format_response(status_code: int, body: dict) -> dict:
    """Format Lambda response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }
