"""
TRACE WebSocket Handler Lambda - Production Version

Handles WebSocket connections for real-time telemetry streaming:
- $connect: New connection management
- $disconnect: Cleanup connections
- subscribe: Subscribe to telemetry streams
- unsubscribe: Unsubscribe from streams

Uses DynamoDB to track active connections and subscriptions.
"""

import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
apigateway = boto3.client('apigatewaymanagementapi')

# Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'production')
CONNECTIONS_TABLE = os.getenv('CONNECTIONS_TABLE', f'TRACE-WebSocketConnections-{ENVIRONMENT}')


def lambda_handler(event, context):
    """
    Main handler for WebSocket events.
    """
    route_key = event.get('requestContext', {}).get('routeKey', '$default')
    connection_id = event.get('requestContext', {}).get('connectionId')
    domain_name = event.get('requestContext', {}).get('domainName')
    stage = event.get('requestContext', {}).get('stage')
    
    # Update API Gateway management endpoint
    if domain_name and stage:
        global apigateway
        apigateway = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=f'https://{domain_name}/{stage}'
        )
    
    handlers = {
        '$connect': handle_connect,
        '$disconnect': handle_disconnect,
        '$default': handle_default,
        'subscribe': handle_subscribe,
        'unsubscribe': handle_unsubscribe,
        'ping': handle_ping,
    }
    
    handler = handlers.get(route_key, handle_default)
    
    try:
        return handler(event, connection_id)
    except Exception as e:
        print(f"Error handling {route_key}: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


def handle_connect(event: dict, connection_id: str) -> dict:
    """
    Handle new WebSocket connection.
    """
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        
        # Store connection
        table.put_item(
            Item={
                'connection_id': connection_id,
                'connected_at': datetime.utcnow().isoformat() + 'Z',
                'subscriptions': [],
                'last_activity': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        print(f"Connected: {connection_id}")
        return {'statusCode': 200, 'body': 'Connected'}
        
    except Exception as e:
        print(f"Connect error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}


def handle_disconnect(event: dict, connection_id: str) -> dict:
    """
    Handle WebSocket disconnection.
    """
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        
        # Remove connection
        table.delete_item(
            Key={'connection_id': connection_id}
        )
        
        print(f"Disconnected: {connection_id}")
        return {'statusCode': 200, 'body': 'Disconnected'}
        
    except Exception as e:
        print(f"Disconnect error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}


def handle_subscribe(event: dict, connection_id: str) -> dict:
    """
    Handle subscription to telemetry streams.
    """
    try:
        body = json.loads(event.get('body', '{}'))
        subscription_type = body.get('type', 'telemetry')
        tower_id = body.get('tower_id')
        region = body.get('region')
        
        table = dynamodb.Table(CONNECTIONS_TABLE)
        
        # Build subscription key
        subscription = {
            'type': subscription_type,
            'tower_id': tower_id,
            'region': region,
            'subscribed_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Update connection with subscription
        table.update_item(
            Key={'connection_id': connection_id},
            UpdateExpression='SET subscriptions = list_append(if_not_exists(subscriptions, :empty), :sub), last_activity = :now',
            ExpressionAttributeValues={
                ':sub': [subscription],
                ':empty': [],
                ':now': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        # Send confirmation
        send_to_connection(connection_id, {
            'type': 'subscription_confirmed',
            'subscription': subscription
        })
        
        print(f"Subscription added for {connection_id}: {subscription}")
        return {'statusCode': 200, 'body': 'Subscribed'}
        
    except Exception as e:
        print(f"Subscribe error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}


def handle_unsubscribe(event: dict, connection_id: str) -> dict:
    """
    Handle unsubscription from telemetry streams.
    """
    try:
        body = json.loads(event.get('body', '{}'))
        subscription_type = body.get('type', 'telemetry')
        tower_id = body.get('tower_id')
        
        table = dynamodb.Table(CONNECTIONS_TABLE)
        
        # Get current subscriptions
        response = table.get_item(Key={'connection_id': connection_id})
        item = response.get('Item', {})
        subscriptions = item.get('subscriptions', [])
        
        # Filter out matching subscription
        new_subscriptions = [
            s for s in subscriptions
            if not (s.get('type') == subscription_type and 
                   (tower_id is None or s.get('tower_id') == tower_id))
        ]
        
        # Update
        table.update_item(
            Key={'connection_id': connection_id},
            UpdateExpression='SET subscriptions = :subs, last_activity = :now',
            ExpressionAttributeValues={
                ':subs': new_subscriptions,
                ':now': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        # Send confirmation
        send_to_connection(connection_id, {
            'type': 'unsubscription_confirmed',
            'subscription_type': subscription_type,
            'tower_id': tower_id
        })
        
        print(f"Unsubscribed {connection_id} from {subscription_type}")
        return {'statusCode': 200, 'body': 'Unsubscribed'}
        
    except Exception as e:
        print(f"Unsubscribe error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}


def handle_ping(event: dict, connection_id: str) -> dict:
    """
    Handle ping for connection keepalive.
    """
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        
        # Update last activity
        table.update_item(
            Key={'connection_id': connection_id},
            UpdateExpression='SET last_activity = :now',
            ExpressionAttributeValues={
                ':now': datetime.utcnow().isoformat() + 'Z'
            }
        )
        
        send_to_connection(connection_id, {
            'type': 'pong',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        return {'statusCode': 200, 'body': 'Pong'}
        
    except Exception as e:
        return {'statusCode': 500, 'body': str(e)}


def handle_default(event: dict, connection_id: str) -> dict:
    """
    Handle unknown message types.
    """
    try:
        body = json.loads(event.get('body', '{}'))
        action = body.get('action', 'unknown')
        
        send_to_connection(connection_id, {
            'type': 'error',
            'message': f'Unknown action: {action}',
            'supported_actions': ['subscribe', 'unsubscribe', 'ping']
        })
        
        return {'statusCode': 200, 'body': 'OK'}
        
    except Exception as e:
        return {'statusCode': 500, 'body': str(e)}


def send_to_connection(connection_id: str, data: dict) -> bool:
    """
    Send message to a WebSocket connection.
    """
    try:
        apigateway.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(data).encode('utf-8')
        )
        return True
    except apigateway.exceptions.GoneException:
        # Connection no longer exists, clean up
        try:
            table = dynamodb.Table(CONNECTIONS_TABLE)
            table.delete_item(Key={'connection_id': connection_id})
        except Exception:
            pass
        return False
    except Exception as e:
        print(f"Send error to {connection_id}: {str(e)}")
        return False


def broadcast_telemetry(telemetry_data: dict):
    """
    Broadcast telemetry to all subscribed connections.
    Called from telemetry processor Lambda.
    """
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        tower_id = telemetry_data.get('tower_id')
        region = telemetry_data.get('region')
        
        # Scan for connections with matching subscriptions
        response = table.scan()
        
        message = {
            'type': 'telemetry',
            'data': telemetry_data,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        for item in response.get('Items', []):
            connection_id = item.get('connection_id')
            subscriptions = item.get('subscriptions', [])
            
            # Check if any subscription matches
            for sub in subscriptions:
                if sub.get('type') != 'telemetry':
                    continue
                
                sub_tower = sub.get('tower_id')
                sub_region = sub.get('region')
                
                # Match if subscription is for all, specific tower, or specific region
                if (sub_tower is None and sub_region is None) or \
                   (sub_tower and sub_tower == tower_id) or \
                   (sub_region and sub_region == region):
                    send_to_connection(connection_id, message)
                    break
                    
    except Exception as e:
        print(f"Broadcast error: {str(e)}")


def broadcast_alert(alert_data: dict):
    """
    Broadcast alert to all subscribed connections.
    """
    try:
        table = dynamodb.Table(CONNECTIONS_TABLE)
        
        # Scan all connections
        response = table.scan()
        
        message = {
            'type': 'alert',
            'data': alert_data,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        for item in response.get('Items', []):
            connection_id = item.get('connection_id')
            subscriptions = item.get('subscriptions', [])
            
            # Send to anyone subscribed to alerts or all
            for sub in subscriptions:
                if sub.get('type') in ['alert', 'all', 'telemetry']:
                    send_to_connection(connection_id, message)
                    break
                    
    except Exception as e:
        print(f"Alert broadcast error: {str(e)}")
