"""
AWS Bedrock AI Service for TRACE Dashboard

This module provides direct integration with Amazon Bedrock for:
- Real-time chat with Claude 3.5 (replaces Google Gemini)
- Network telemetry analysis using AWS Timestream data
- Anomaly detection powered by AI
- Intelligent remediation recommendations

Can be used as a drop-in replacement for gemini_service.py
"""

from __future__ import annotations

import os
import sys
import json
import time
import asyncio
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Generator, AsyncGenerator
from functools import wraps
from collections import OrderedDict
from threading import Lock

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import boto3

# Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
BEDROCK_FAST_MODEL = os.getenv('BEDROCK_FAST_MODEL', 'anthropic.claude-3-haiku-20240307-v1:0')
ENVIRONMENT = os.getenv('TRACE_ENV', 'production')
TIMESTREAM_DATABASE = os.getenv('TIMESTREAM_DATABASE', f'TRACE-Telemetry-{ENVIRONMENT}')

# Rate limiting
RATE_LIMIT = int(os.getenv('BEDROCK_RATE_LIMIT', '60'))
CACHE_TTL = int(os.getenv('BEDROCK_CACHE_TTL', '300'))
STREAMING_ENABLED = os.getenv('BEDROCK_STREAMING_ENABLED', 'true').lower() == 'true'

# Flag to check if Bedrock is available
BEDROCK_AVAILABLE = False


class RateLimiter:
    """Simple rate limiter using sliding window."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[float] = []
        self.lock = Lock()

    def can_proceed(self) -> bool:
        with self.lock:
            now = time.time()
            self.requests = [r for r in self.requests if now - r < self.window_seconds]
            return len(self.requests) < self.max_requests

    def record_request(self):
        with self.lock:
            self.requests.append(time.time())

    def wait_time(self) -> float:
        with self.lock:
            if len(self.requests) < self.max_requests:
                return 0
            oldest = min(self.requests)
            return max(0, self.window_seconds - (time.time() - oldest))


class LRUCache:
    """Simple LRU cache with TTL."""

    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.lock = Lock()

    def _make_key(self, *args, **kwargs) -> str:
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key not in self.cache:
                return None
            if time.time() - self.timestamps[key] > self.ttl:
                del self.cache[key]
                del self.timestamps[key]
                return None
            self.cache.move_to_end(key)
            return self.cache[key]

    def set(self, key: str, value: Any):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.max_size:
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    del self.timestamps[oldest_key]
            self.cache[key] = value
            self.timestamps[key] = time.time()


# Initialize rate limiter and cache
rate_limiter = RateLimiter(max_requests=RATE_LIMIT)
response_cache = LRUCache(max_size=100, ttl=CACHE_TTL)

# System prompt for TRACE context
SYSTEM_PROMPT = """You are the TRACE Principal Agent - the global orchestrator and health guardian for a hierarchical multi-agent telecom network management system deployed on AWS.

## Your Role
Principal (Self-Healing) Agent for TRACE (Traffic & Resource Agentic Control Engine):
• Monitor agents and towers using real-time telemetry from AWS Timestream
• Execute safe automated remediations through AWS Lambda and IoT Core
• Provide health dashboards from CloudWatch metrics
• Analyze telemetry data for energy optimization and anomaly detection

## AWS Infrastructure You Manage
- **Timestream**: Real-time telemetry storage (tower metrics, agent metrics)
- **DynamoDB**: Tower configuration, agent state, remediation logs
- **IoT Core**: Tower command and control
- **Step Functions**: Self-healing and energy optimization workflows
- **CloudWatch**: Monitoring and alerting

## Agent Hierarchy
- **Principal Agent (You)**: Global orchestrator, health monitoring, self-healing
- **Regional Coordinators (5)**: Manage tower clusters by region (R-N, R-S, R-E, R-W, R-C)
- **Edge Agents (5 per tower × 10 towers)**:
  - Monitoring Agent: Real-time telemetry collection
  - Prediction Agent: Traffic forecasting, anomaly detection
  - Decision Agent: Policy decisions, optimization
  - Action Agent: Execute TRX control, load balancing
  - Learning Agent: Model updates, pattern learning

## Your Capabilities
1. **Energy Optimization** - Reduce tower energy by 30-40% during low demand via TRX shutdowns
2. **Congestion Management** - Predict traffic surges, pre-activate backup cells, load balancing
3. **Self-Healing** - Detect failures, execute restart/redeploy/reroute (<5 min MTTR)
4. **Real-Time Analysis** - Query Timestream for live metrics, CloudWatch for alerts

## Response Guidelines
1. Be concise but comprehensive - use bullet points, tables, and markdown formatting
2. Provide specific metrics from REAL AWS data sources
3. Always suggest actionable next steps with expected impact
4. If discussing issues, include severity (critical/high/medium/low) and recommended remediation
5. Reference actual tower IDs (TX001-TX010) and regions (R-N, R-S, R-E, R-W, R-C)
6. For complex operations, explain the AWS workflow involved

## Current Context
You are responding through the TRACE Dashboard, helping operators manage their telecom network efficiently using real-time AWS telemetry. Keep responses actionable and prioritize system stability."""


# Initialize AWS clients
bedrock_runtime = None
timestream_query = None
dynamodb = None

def initialize_aws_clients():
    """Initialize AWS clients."""
    global bedrock_runtime, timestream_query, dynamodb, BEDROCK_AVAILABLE
    
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name=AWS_REGION)
        timestream_query = boto3.client('timestream-query', region_name=AWS_REGION)
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        BEDROCK_AVAILABLE = True
        print("✅ AWS Bedrock service initialized successfully")
        return True
    except Exception as e:
        print(f"⚠️ AWS Bedrock initialization failed: {e}")
        BEDROCK_AVAILABLE = False
        return False


def is_available() -> bool:
    """Check if Bedrock service is available."""
    global BEDROCK_AVAILABLE
    if not BEDROCK_AVAILABLE:
        return initialize_aws_clients()
    return BEDROCK_AVAILABLE


def _get_real_time_context() -> Dict[str, Any]:
    """Get real-time context from AWS services."""
    context = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'data_source': 'aws_timestream',
    }
    
    if not timestream_query:
        context['data_source'] = 'unavailable'
        return context
    
    try:
        # Query recent metrics summary
        query = f"""
            SELECT 
                tower_id, region_id,
                AVG(cpu_util_pct) as avg_cpu,
                AVG(latency_ms) as avg_latency,
                AVG(connected_users) as avg_users
            FROM "{TIMESTREAM_DATABASE}"."TowerMetrics"
            WHERE time > ago(5m)
            GROUP BY tower_id, region_id
        """
        
        response = timestream_query.query(QueryString=query)
        columns = [col['Name'] for col in response.get('ColumnInfo', [])]
        
        towers = []
        for row in response.get('Rows', []):
            values = [datum.get('ScalarValue') for datum in row.get('Data', [])]
            row_dict = dict(zip(columns, values))
            
            cpu = float(row_dict.get('avg_cpu', 0) or 0)
            latency = float(row_dict.get('avg_latency', 0) or 0)
            
            towers.append({
                'tower_id': row_dict.get('tower_id'),
                'region': row_dict.get('region_id'),
                'cpu': round(cpu, 1),
                'latency': round(latency, 1),
                'users': int(float(row_dict.get('avg_users', 0) or 0)),
                'status': 'critical' if cpu > 90 or latency > 150 else 'warning' if cpu > 75 else 'healthy'
            })
        
        context['tower_count'] = len(towers)
        context['towers'] = towers
        context['summary'] = {
            'healthy': sum(1 for t in towers if t['status'] == 'healthy'),
            'warning': sum(1 for t in towers if t['status'] == 'warning'),
            'critical': sum(1 for t in towers if t['status'] == 'critical'),
        }
        
    except Exception as e:
        context['error'] = str(e)
        context['data_source'] = 'unavailable'
    
    return context


def chat(
    message: str,
    context: str = "general",
    use_fast_model: bool = False,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """
    Send a chat message to Bedrock and get a response.
    
    Args:
        message: User's message
        context: Context for the conversation
        use_fast_model: Use faster Claude Haiku model
        temperature: Response temperature
    
    Returns:
        Dict with response and metadata
    """
    if not is_available():
        return {
            'success': False,
            'error': 'AWS Bedrock is not available',
            'response': 'I apologize, but the AI service is currently unavailable. Please check AWS credentials and try again.',
        }
    
    if not rate_limiter.can_proceed():
        wait_time = rate_limiter.wait_time()
        return {
            'success': False,
            'error': f'Rate limited. Please wait {wait_time:.1f} seconds.',
            'response': f'I need a moment before I can respond again. Please wait {wait_time:.1f} seconds.',
        }
    
    try:
        rate_limiter.record_request()
        
        # Get real-time context
        context_data = _get_real_time_context()
        
        model_id = BEDROCK_FAST_MODEL if use_fast_model else BEDROCK_MODEL_ID
        
        enhanced_prompt = f"""Context: {context}

Current System Status (from AWS Timestream):
{json.dumps(context_data, indent=2)}

User Query: {message}

Respond based on real-time data from AWS Timestream and DynamoDB. Be specific about tower IDs and metrics."""

        request_body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 4096,
            'system': SYSTEM_PROMPT,
            'messages': [
                {'role': 'user', 'content': enhanced_prompt}
            ],
            'temperature': temperature,
            'top_p': 0.9,
        }
        
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        
        return {
            'success': True,
            'response': response_body.get('content', [{}])[0].get('text', ''),
            'model': model_id,
            'usage': {
                'input_tokens': response_body.get('usage', {}).get('input_tokens', 0),
                'output_tokens': response_body.get('usage', {}).get('output_tokens', 0),
            },
            'context_data': context_data,
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'response': f'I encountered an error accessing the AI service: {str(e)}',
        }


def chat_stream(
    message: str,
    context: str = "general",
    use_fast_model: bool = False,
) -> Generator[str, None, None]:
    """
    Stream chat response for real-time typing effect.
    
    Args:
        message: User's message
        context: Context for the conversation
        use_fast_model: Use faster model
    
    Yields:
        Response text chunks
    """
    if not is_available():
        yield "I apologize, but the AI service is currently unavailable."
        return
    
    if not rate_limiter.can_proceed():
        yield f"Rate limited. Please wait {rate_limiter.wait_time():.1f} seconds."
        return
    
    try:
        rate_limiter.record_request()
        
        context_data = _get_real_time_context()
        model_id = BEDROCK_FAST_MODEL if use_fast_model else BEDROCK_MODEL_ID
        
        enhanced_prompt = f"""Context: {context}

Current System Status (from AWS Timestream):
{json.dumps(context_data, indent=2)}

User Query: {message}"""

        request_body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 4096,
            'system': SYSTEM_PROMPT,
            'messages': [
                {'role': 'user', 'content': enhanced_prompt}
            ],
            'temperature': 0.7,
        }
        
        response = bedrock_runtime.invoke_model_with_response_stream(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )
        
        for event in response.get('body', []):
            chunk = event.get('chunk')
            if chunk:
                chunk_data = json.loads(chunk.get('bytes', b'{}').decode('utf-8'))
                if chunk_data.get('type') == 'content_block_delta':
                    text = chunk_data.get('delta', {}).get('text', '')
                    if text:
                        yield text
                        
    except Exception as e:
        yield f"Error: {str(e)}"


async def chat_async(
    message: str,
    context: str = "general",
    use_fast_model: bool = False,
) -> Dict[str, Any]:
    """Async version of chat function."""
    # Run sync chat in executor
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: chat(message, context, use_fast_model)
    )


async def chat_stream_async(
    message: str,
    context: str = "general",
) -> AsyncGenerator[str, None]:
    """Async streaming chat."""
    for chunk in chat_stream(message, context):
        yield chunk
        await asyncio.sleep(0)  # Allow other tasks to run


def analyze_telemetry(data: Any, analysis_type: str = "general") -> Dict[str, Any]:
    """
    Analyze telemetry data using Bedrock AI.
    
    Args:
        data: Telemetry data to analyze
        analysis_type: Type of analysis (general, energy, congestion, health)
    
    Returns:
        Analysis results
    """
    analysis_prompts = {
        'general': 'Analyze this telemetry data and identify any issues or patterns.',
        'energy': 'Analyze this telemetry data for energy optimization opportunities. Identify towers where TRX can be reduced or power mode changed.',
        'congestion': 'Analyze this telemetry data for congestion patterns. Identify towers at risk of overload and recommend load balancing actions.',
        'health': 'Analyze this telemetry data for health issues. Identify failing components and recommend remediation actions.',
    }
    
    prompt = f"""{analysis_prompts.get(analysis_type, analysis_prompts['general'])}

Telemetry Data:
```json
{json.dumps(data, indent=2) if isinstance(data, dict) else str(data)}
```

Provide a structured analysis with:
1. Summary of findings
2. Specific issues identified (if any)
3. Recommended actions with priority
4. Expected impact of recommendations"""

    return chat(prompt, context=f"telemetry_analysis_{analysis_type}")


# Initialize on import
initialize_aws_clients()


# Compatibility with gemini_service interface
def get_status() -> Dict[str, Any]:
    """Get service status (compatible with gemini_service)."""
    return {
        'available': BEDROCK_AVAILABLE,
        'model': BEDROCK_MODEL_ID,
        'region': AWS_REGION,
        'environment': ENVIRONMENT,
    }


if __name__ == "__main__":
    # Test the service
    print("\n" + "=" * 60)
    print("  TRACE AWS Bedrock Service Test")
    print("=" * 60)
    
    if is_available():
        print("✅ Service is available")
        
        print("\n📊 Getting real-time context...")
        context = _get_real_time_context()
        print(f"   Data source: {context.get('data_source')}")
        print(f"   Towers: {context.get('tower_count', 0)}")
        
        print("\n💬 Testing chat...")
        response = chat("What is the current network status?", context="test")
        if response['success']:
            print(f"   Response length: {len(response['response'])} chars")
            print(f"   Model: {response.get('model')}")
        else:
            print(f"   Error: {response.get('error')}")
    else:
        print("❌ Service is not available")
        print("   Check AWS credentials and Bedrock access")
