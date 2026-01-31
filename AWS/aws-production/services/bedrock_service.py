"""
TRACE Bedrock AI Service - Production Version

This module replaces Google Gemini with Amazon Bedrock for:
- Real-time chat with Claude 3.5 / Claude Instant
- Network telemetry analysis
- Anomaly detection powered by AI
- Intelligent remediation recommendations

Fully integrated with AWS services - NO Google dependencies.
"""

import json
import boto3
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Generator
from functools import lru_cache

# Initialize Bedrock clients
bedrock_runtime = boto3.client('bedrock-runtime')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
timestream_query = boto3.client('timestream-query')
dynamodb = boto3.resource('dynamodb')

# Configuration
ENVIRONMENT = os.getenv('TRACE_ENV', 'production')
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
BEDROCK_FAST_MODEL = os.getenv('BEDROCK_FAST_MODEL', 'anthropic.claude-3-haiku-20240307-v1:0')
PRINCIPAL_AGENT_ID = os.getenv('TRACE_PRINCIPAL_AGENT_ID')
PRINCIPAL_AGENT_ALIAS = os.getenv('TRACE_PRINCIPAL_AGENT_ALIAS', 'TSTALIASID')
TIMESTREAM_DATABASE = os.getenv('TIMESTREAM_DATABASE', f'TRACE-Telemetry-{ENVIRONMENT}')

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


class BedrockService:
    """
    Main service class for Amazon Bedrock AI integration.
    Replaces Google Gemini with AWS-native AI services.
    """
    
    def __init__(self):
        self.model_id = BEDROCK_MODEL_ID
        self.fast_model_id = BEDROCK_FAST_MODEL
        self.principal_agent_id = PRINCIPAL_AGENT_ID
        self.principal_agent_alias = PRINCIPAL_AGENT_ALIAS
        self._session_id = None
    
    @property
    def session_id(self) -> str:
        """Get or create a session ID for conversation continuity."""
        if not self._session_id:
            self._session_id = f"session-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        return self._session_id
    
    def is_available(self) -> bool:
        """Check if Bedrock service is available."""
        try:
            # Test with a minimal request
            bedrock_runtime.invoke_model(
                modelId=self.fast_model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 10,
                    'messages': [{'role': 'user', 'content': 'hi'}]
                })
            )
            return True
        except Exception as e:
            print(f"Bedrock availability check failed: {str(e)}")
            return False
    
    def chat(self, message: str, context: str = "general", use_agent: bool = False) -> Dict[str, Any]:
        """
        Send a chat message and get a response.
        
        Args:
            message: User's message
            context: Context for the conversation
            use_agent: If True, use Bedrock Agent; otherwise direct model invocation
        
        Returns:
            Dict with response and metadata
        """
        if use_agent and self.principal_agent_id:
            return self._invoke_agent(message)
        else:
            return self._invoke_model(message, context)
    
    def _invoke_model(self, message: str, context: str) -> Dict[str, Any]:
        """
        Invoke Bedrock model directly for chat.
        """
        try:
            # Build contextual prompt
            context_data = self._get_real_time_context()
            
            enhanced_prompt = f"""Context: {context}

Current System Status:
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
                'temperature': 0.7,
                'top_p': 0.9,
            }
            
            response = bedrock_runtime.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            
            return {
                'success': True,
                'response': response_body.get('content', [{}])[0].get('text', ''),
                'model': self.model_id,
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
                'response': f"I encountered an error accessing the AI service: {str(e)}",
            }
    
    def _invoke_agent(self, message: str) -> Dict[str, Any]:
        """
        Invoke Bedrock Agent for tool-augmented responses.
        """
        try:
            response = bedrock_agent_runtime.invoke_agent(
                agentId=self.principal_agent_id,
                agentAliasId=self.principal_agent_alias,
                sessionId=self.session_id,
                inputText=message,
                enableTrace=True,
            )
            
            # Process streaming response
            full_response = ""
            traces = []
            
            for event in response.get('completion', []):
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        full_response += chunk['bytes'].decode('utf-8')
                if 'trace' in event:
                    traces.append(event['trace'])
            
            return {
                'success': True,
                'response': full_response,
                'agent_id': self.principal_agent_id,
                'session_id': self.session_id,
                'traces': traces,
            }
            
        except Exception as e:
            # Fall back to direct model invocation
            print(f"Agent invocation failed, falling back to direct model: {str(e)}")
            return self._invoke_model(message, "agent_fallback")
    
    def chat_stream(self, message: str, context: str = "general") -> Generator[str, None, None]:
        """
        Stream chat response for real-time typing effect.
        """
        try:
            context_data = self._get_real_time_context()
            
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
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            for event in response.get('body', []):
                chunk = json.loads(event['chunk']['bytes'])
                if chunk.get('type') == 'content_block_delta':
                    delta = chunk.get('delta', {})
                    if 'text' in delta:
                        yield delta['text']
                        
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def analyze_telemetry(self, tower_id: str = None, region_id: str = None, 
                         analysis_type: str = "health") -> Dict[str, Any]:
        """
        Analyze real telemetry data using AI.
        """
        try:
            # Get real data from Timestream
            telemetry_data = self._query_telemetry(tower_id, region_id)
            
            analysis_prompt = f"""Analyze this REAL telemetry data from AWS Timestream:

{json.dumps(telemetry_data, indent=2)}

Analysis Type: {analysis_type}

Provide:
1. Current status assessment
2. Key issues or concerns (with specific metrics)
3. Recommended actions (prioritized)
4. Expected impact of recommendations

Base your analysis ONLY on this real data, not assumptions."""

            request_body = {
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 4096,
                'system': SYSTEM_PROMPT,
                'messages': [{'role': 'user', 'content': analysis_prompt}],
                'temperature': 0.3,  # Lower temp for analysis
            }
            
            response = bedrock_runtime.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            
            return {
                'success': True,
                'analysis': response_body.get('content', [{}])[0].get('text', ''),
                'data_source': 'aws_timestream',
                'data_analyzed': telemetry_data,
                'analysis_type': analysis_type,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def get_recommendations(self, focus: str = "all") -> Dict[str, Any]:
        """
        Get AI-powered recommendations based on current system state.
        """
        try:
            # Get comprehensive system state
            system_state = self._get_comprehensive_state()
            
            recommendation_prompt = f"""Based on this REAL system state from AWS:

{json.dumps(system_state, indent=2)}

Focus Area: {focus}

Generate specific, actionable recommendations:
1. Immediate actions (if any critical issues)
2. Energy optimization opportunities
3. Capacity planning suggestions
4. Preventive maintenance recommendations

For each recommendation, include:
- Priority (critical/high/medium/low)
- Specific action (with tower IDs, values)
- Expected impact
- AWS resources involved"""

            request_body = {
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 4096,
                'system': SYSTEM_PROMPT,
                'messages': [{'role': 'user', 'content': recommendation_prompt}],
                'temperature': 0.4,
            }
            
            response = bedrock_runtime.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            
            return {
                'success': True,
                'recommendations': response_body.get('content', [{}])[0].get('text', ''),
                'data_source': 'aws_multi_source',
                'system_state': system_state,
                'focus': focus,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def _get_real_time_context(self) -> Dict[str, Any]:
        """
        Get real-time context data from AWS services.
        """
        context = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'data_source': 'aws_timestream',
        }
        
        try:
            # Query latest metrics from Timestream
            query = f"""
                SELECT 
                    region_id,
                    COUNT(DISTINCT tower_id) as tower_count,
                    AVG(cpu_util_pct) as avg_cpu,
                    AVG(latency_ms) as avg_latency,
                    SUM(connected_users) as total_users
                FROM "{TIMESTREAM_DATABASE}"."TowerMetrics"
                WHERE time > ago(5m)
                GROUP BY region_id
            """
            
            response = timestream_query.query(QueryString=query)
            
            regions = []
            for row in response.get('Rows', []):
                data = {}
                for i, col in enumerate(response.get('ColumnInfo', [])):
                    value = row['Data'][i].get('ScalarValue')
                    data[col['Name']] = value
                regions.append(data)
            
            context['regions'] = regions
            context['total_towers'] = sum(int(r.get('tower_count', 0)) for r in regions)
            context['total_users'] = sum(int(float(r.get('total_users', 0))) for r in regions)
            
        except Exception as e:
            context['error'] = f"Timestream query failed: {str(e)}"
            context['regions'] = []
        
        return context
    
    def _query_telemetry(self, tower_id: str = None, region_id: str = None) -> Dict[str, Any]:
        """
        Query telemetry data from Timestream.
        """
        try:
            filters = []
            if tower_id:
                filters.append(f"tower_id = '{tower_id}'")
            if region_id:
                filters.append(f"region_id = '{region_id}'")
            
            where_clause = f"AND {' AND '.join(filters)}" if filters else ""
            
            query = f"""
                SELECT 
                    tower_id,
                    region_id,
                    time,
                    connected_users,
                    cpu_util_pct,
                    bandwidth_utilization_pct,
                    latency_ms,
                    packet_loss_pct,
                    power_kw,
                    active_trx,
                    total_trx
                FROM "{TIMESTREAM_DATABASE}"."TowerMetrics"
                WHERE time > ago(1h)
                {where_clause}
                ORDER BY time DESC
                LIMIT 100
            """
            
            response = timestream_query.query(QueryString=query)
            
            records = []
            for row in response.get('Rows', []):
                record = {}
                for i, col in enumerate(response.get('ColumnInfo', [])):
                    value = row['Data'][i].get('ScalarValue')
                    record[col['Name']] = value
                records.append(record)
            
            return {
                'query_time': datetime.utcnow().isoformat() + 'Z',
                'record_count': len(records),
                'records': records[:20],  # Limit for AI context
                'summary': self._summarize_records(records) if records else {},
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'query_time': datetime.utcnow().isoformat() + 'Z',
            }
    
    def _summarize_records(self, records: List[dict]) -> Dict[str, Any]:
        """
        Create summary statistics from records.
        """
        if not records:
            return {}
        
        cpu_values = [float(r.get('cpu_util_pct', 0)) for r in records if r.get('cpu_util_pct')]
        latency_values = [float(r.get('latency_ms', 0)) for r in records if r.get('latency_ms')]
        user_values = [int(float(r.get('connected_users', 0))) for r in records if r.get('connected_users')]
        
        return {
            'avg_cpu': round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else 0,
            'max_cpu': max(cpu_values) if cpu_values else 0,
            'avg_latency': round(sum(latency_values) / len(latency_values), 2) if latency_values else 0,
            'max_latency': max(latency_values) if latency_values else 0,
            'total_users': sum(user_values) if user_values else 0,
            'unique_towers': len(set(r.get('tower_id') for r in records)),
        }
    
    def _get_comprehensive_state(self) -> Dict[str, Any]:
        """
        Get comprehensive system state from multiple AWS sources.
        """
        state = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        
        # Get telemetry summary
        state['telemetry'] = self._query_telemetry()
        
        # Get tower configs from DynamoDB
        try:
            table = dynamodb.Table(f'TRACE-TowerConfig-{ENVIRONMENT}')
            response = table.scan()
            state['tower_configs'] = response.get('Items', [])
        except Exception as e:
            state['tower_configs_error'] = str(e)
        
        # Get agent states from DynamoDB
        try:
            table = dynamodb.Table(f'TRACE-AgentState-{ENVIRONMENT}')
            response = table.scan()
            items = response.get('Items', [])
            state['agents'] = {
                'total': len(items),
                'active': sum(1 for i in items if i.get('status') == 'active'),
                'inactive': sum(1 for i in items if i.get('status') != 'active'),
            }
        except Exception as e:
            state['agents_error'] = str(e)
        
        return state


# Create singleton instance
bedrock_service = BedrockService()


def get_service() -> BedrockService:
    """Get the Bedrock service instance."""
    return bedrock_service
