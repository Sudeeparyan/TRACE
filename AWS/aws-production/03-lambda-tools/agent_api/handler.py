"""
TRACE Agent API Lambda - Production Version

This Lambda function provides the chat interface for Bedrock Agents:
- Routes requests to the Principal Agent
- Manages session state
- Handles conversation context

Integrates with Amazon Bedrock Agents for AI-powered responses.
"""

import json
import boto3
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

# Initialize AWS clients
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
dynamodb = boto3.resource('dynamodb')

# Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'production')
PRINCIPAL_AGENT_ID = os.getenv('TRACE_PRINCIPAL_AGENT_ID')
PRINCIPAL_AGENT_ALIAS = os.getenv('TRACE_PRINCIPAL_AGENT_ALIAS', 'TSTALIASID')
SESSION_TABLE = os.getenv('SESSION_TABLE', f'TRACE-Sessions-{ENVIRONMENT}')


def lambda_handler(event, context):
    """
    Main Lambda handler for agent chat API.
    """
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, {})
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
        
        message = body.get('message', '')
        session_id = body.get('session_id') or str(uuid.uuid4())
        context_data = body.get('context', {})
        
        if not message:
            return cors_response(400, {
                'error': 'Message is required',
                'status': 'error'
            })
        
        # Invoke Bedrock Agent
        result = invoke_agent(message, session_id, context_data)
        
        return cors_response(200, result)
        
    except Exception as e:
        return cors_response(500, {
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })


def invoke_agent(message: str, session_id: str, context: dict = None) -> dict:
    """
    Invoke the Principal Agent via Bedrock Agent Runtime.
    """
    if not PRINCIPAL_AGENT_ID:
        # Fallback to direct Bedrock model if agent not configured
        return invoke_bedrock_direct(message, session_id, context)
    
    try:
        # Prepare input with context
        input_text = message
        if context:
            context_str = f"\n\nContext: {json.dumps(context)}"
            input_text = message + context_str
        
        # Invoke agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=PRINCIPAL_AGENT_ID,
            agentAliasId=PRINCIPAL_AGENT_ALIAS,
            sessionId=session_id,
            inputText=input_text
        )
        
        # Process streaming response
        completion = ""
        actions_taken = []
        
        for event in response.get('completion', []):
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    completion += chunk['bytes'].decode('utf-8')
            
            # Capture any action group invocations
            if 'trace' in event:
                trace = event['trace']
                if 'orchestrationTrace' in trace:
                    orch = trace['orchestrationTrace']
                    if 'invocationInput' in orch:
                        actions_taken.append({
                            'type': 'action_group',
                            'details': orch['invocationInput']
                        })
        
        # Log session
        log_session(session_id, message, completion)
        
        return {
            'status': 'success',
            'response': completion,
            'session_id': session_id,
            'actions_taken': actions_taken,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
    except bedrock_agent_runtime.exceptions.ValidationException as e:
        # Agent might not exist, fall back to direct model
        return invoke_bedrock_direct(message, session_id, context)
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }


def invoke_bedrock_direct(message: str, session_id: str, context: dict = None) -> dict:
    """
    Fallback to direct Bedrock model invocation if agent not available.
    """
    bedrock_runtime = boto3.client('bedrock-runtime')
    model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
    
    # Build system prompt
    system_prompt = """You are the TRACE Principal Agent - the global orchestrator for a hierarchical multi-agent telecom network management system deployed on AWS.

You manage:
- 50 cell towers across 5 regions (North, South, East, West, Central)
- Real-time telemetry from AWS Timestream
- Automated remediation through Lambda and IoT Core
- Energy optimization workflows

Current system status should be queried from AWS Timestream.
Remediation actions should be executed through the TRACE Lambda functions.

Provide specific, actionable responses with actual metrics when possible."""

    # Prepare messages
    messages = [
        {"role": "user", "content": message}
    ]
    
    # Add context if provided
    if context:
        system_prompt += f"\n\nCurrent context: {json.dumps(context)}"
    
    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "system": system_prompt,
                "messages": messages
            })
        )
        
        response_body = json.loads(response['body'].read())
        completion = response_body.get('content', [{}])[0].get('text', '')
        
        # Log session
        log_session(session_id, message, completion)
        
        return {
            'status': 'success',
            'response': completion,
            'session_id': session_id,
            'actions_taken': [],
            'model': model_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }


def log_session(session_id: str, user_message: str, agent_response: str):
    """
    Log conversation to DynamoDB for audit and analytics.
    """
    try:
        table = dynamodb.Table(SESSION_TABLE)
        
        table.put_item(
            Item={
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'user_message': user_message[:1000],  # Truncate for storage
                'agent_response': agent_response[:5000],
                'environment': ENVIRONMENT
            }
        )
    except Exception:
        # Don't fail the request if logging fails
        pass


def cors_response(status_code: int, body: dict) -> dict:
    """Return response with CORS headers."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Requested-With',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body)
    }
