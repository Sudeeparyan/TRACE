"""
Gemini AI Service for TRACE Dashboard

This module provides direct integration with Google's Gemini API for:
- Real-time chat with streaming responses
- Network telemetry analysis
- Anomaly detection and issue identification
- Remediation recommendations

Features:
- Rate limiting to respect API quotas
- Response caching for frequently requested data
- Streaming support for real-time typing effect
- Error handling with graceful fallbacks
- Integration with principal_agent tools for analysis logic
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

# Add paths for principal_agent imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(CLIENT_DIR)
for path in [ROOT_DIR, CLIENT_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Import Google Generative AI
import google.generativeai as genai

# Try to import principal_agent analysis functions
try:
    from principal_agent.tools.json_data_processor import (
        _perform_analysis,
        _generate_recommendations,
        _analyze_energy,
        _analyze_congestion,
        _analyze_health,
    )

    ANALYSIS_TOOLS_AVAILABLE = True
except ImportError:
    ANALYSIS_TOOLS_AVAILABLE = False
    print("⚠️ Principal agent analysis tools not available - using built-in analysis")

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_REASONING_MODEL = os.getenv("GEMINI_REASONING_MODEL", "gemini-1.5-pro")
RATE_LIMIT = int(os.getenv("GEMINI_RATE_LIMIT", "60"))  # requests per minute
CACHE_TTL = int(os.getenv("GEMINI_CACHE_TTL", "300"))  # seconds
STREAMING_ENABLED = os.getenv("GEMINI_STREAMING_ENABLED", "true").lower() == "true"

# Flag to check if Gemini is available (will be set after initialization)
GEMINI_AVAILABLE = False


class RateLimiter:
    """Simple rate limiter using sliding window."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[float] = []
        self.lock = Lock()

    def can_proceed(self) -> bool:
        """Check if a request can proceed."""
        with self.lock:
            now = time.time()
            # Remove old requests outside the window
            self.requests = [r for r in self.requests if now - r < self.window_seconds]
            return len(self.requests) < self.max_requests

    def record_request(self):
        """Record a new request."""
        with self.lock:
            self.requests.append(time.time())

    def wait_time(self) -> float:
        """Get time to wait before next request."""
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
        """Create a cache key from arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            if key not in self.cache:
                return None
            if time.time() - self.timestamps[key] > self.ttl:
                del self.cache[key]
                del self.timestamps[key]
                return None
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]

    def set(self, key: str, value: Any):
        """Set value in cache."""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.max_size:
                    # Remove oldest
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    del self.timestamps[oldest_key]
            self.cache[key] = value
            self.timestamps[key] = time.time()


class GeminiService:
    """
    Main service class for Gemini AI integration.

    Provides methods for:
    - chat(): Interactive conversation with streaming
    - analyze_telemetry(): Network metrics analysis
    - detect_anomalies(): AI-powered anomaly detection
    - get_recommendations(): Remediation recommendations
    """

    # System prompt for TRACE context - aligned with principal_agent
    SYSTEM_PROMPT = """You are the TRACE Principal Agent - the global orchestrator and health guardian for a hierarchical multi-agent telecom network management system.

## Your Role
Principal (Self-Healing) Agent for TRACE (Traffic & Resource Agentic Control Engine):
• Monitor agents and detect failures
• Execute safe automated remediations
• Provide health dashboards
• Analyze JSON telemetry data

## Agent Hierarchy You Manage
- **Principal Agent (You)**: Global orchestrator, health monitoring, self-healing
- **Regional Coordinators (3)**: Manage tower clusters, aggregate telemetry, enforce policies  
- **Edge Agents (5 per tower × N towers)**:
  - Monitoring Agent: Real-time telemetry collection
  - Prediction Agent: Traffic forecasting, anomaly detection
  - Decision xApp Agent: Policy decisions, optimization
  - Action Agent: Execute TRX control, load balancing
  - Learning Agent: Model updates, pattern learning

## Your Capabilities
1. **Energy Optimization** - Reduce tower energy by 30-40% during low demand via TRX shutdowns
2. **Congestion Management** - Predict traffic surges, pre-activate backup cells, load balancing
3. **Self-Healing** - Detect failures, execute restart/redeploy/reroute (<5 min MTTR)
4. **Data Analysis** - Analyze JSON telemetry, provide LLM-powered insights

## Available Actions
- Health: check_system_health, get_agent_status
- Remediation: restart_agent (~30s), redeploy_agent (~2min), reroute_traffic (~45s)
- Dashboard: generate_health_dashboard, get_system_metrics
- Data Analysis: process_uploaded_json, analyze_json_data_with_llm, get_recommendations_from_json

## Response Guidelines
1. Be concise but comprehensive - use bullet points, tables, and markdown formatting
2. Provide specific metrics and numbers when discussing status
3. Always suggest actionable next steps with expected impact
4. If discussing issues, include severity (critical/high/medium/low) and recommended remediation
5. When showing data, format it clearly with markdown tables
6. For complex operations, explain the multi-agent workflow involved
7. Focus on: Energy optimization (30-40% savings), Congestion risk mitigation, Network health

## Current Context
You are responding to queries from the TRACE Dashboard, helping operators manage their telecom network efficiently. Keep responses actionable and prioritize system stability."""

    def __init__(self):
        """Initialize the Gemini service."""
        self.api_key = GOOGLE_API_KEY
        self.model_name = GEMINI_MODEL
        self.reasoning_model_name = GEMINI_REASONING_MODEL
        self.rate_limiter = RateLimiter(max_requests=RATE_LIMIT)
        self.cache = LRUCache(max_size=100, ttl=CACHE_TTL)
        self._initialized = False
        self._model = None
        self._reasoning_model = None

        self._initialize()

    def _initialize(self):
        """Initialize the Gemini API client."""
        if not self.api_key:
            print("⚠️ GOOGLE_API_KEY not set - Gemini service will not be available")
            return

        try:
            genai.configure(api_key=self.api_key)

            # Configure model with safety settings
            generation_config = genai.GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
            )

            # Initialize fast model for general chat
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                system_instruction=self.SYSTEM_PROMPT,
            )

            # Initialize reasoning model for complex analysis
            self._reasoning_model = genai.GenerativeModel(
                model_name=self.reasoning_model_name,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,  # Lower temperature for analysis
                    top_p=0.95,
                    max_output_tokens=16384,
                ),
                system_instruction=self.SYSTEM_PROMPT,
            )

            self._initialized = True
            print(f"✅ Gemini Service initialized with model: {self.model_name}")

        except Exception as e:
            print(f"❌ Failed to initialize Gemini service: {e}")
            self._initialized = False

    def is_available(self) -> bool:
        """Check if the Gemini service is available."""
        return self._initialized

    def _wait_for_rate_limit(self):
        """Wait if rate limit would be exceeded."""
        wait_time = self.rate_limiter.wait_time()
        if wait_time > 0:
            time.sleep(wait_time)
        self.rate_limiter.record_request()

    # -------------------------------------------------------------------------
    # Chat Methods
    # -------------------------------------------------------------------------

    def chat(self, message: str, context: str = "general") -> Dict[str, Any]:
        """
        Send a chat message and get a response.

        Args:
            message: User's message
            context: Context for the conversation (e.g., 'dashboard', 'analysis')

        Returns:
            Dict with response, success status, and metadata
        """
        if not self._initialized:
            return self._fallback_response(message, context)

        try:
            self._wait_for_rate_limit()

            # Build contextual prompt
            prompt = self._build_chat_prompt(message, context)

            # Generate response
            response = self._model.generate_content(prompt)

            return {
                "success": True,
                "response": response.text,
                "source": "gemini",
                "model": self.model_name,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            print(f"Gemini chat error: {e}")
            return self._fallback_response(message, context)

    async def chat_async(
        self, message: str, context: str = "general"
    ) -> Dict[str, Any]:
        """Async version of chat."""
        if not self._initialized:
            return self._fallback_response(message, context)

        try:
            self._wait_for_rate_limit()

            prompt = self._build_chat_prompt(message, context)
            response = await self._model.generate_content_async(prompt)

            return {
                "success": True,
                "response": response.text,
                "source": "gemini",
                "model": self.model_name,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            print(f"Gemini async chat error: {e}")
            return self._fallback_response(message, context)

    def chat_stream(
        self, message: str, context: str = "general"
    ) -> Generator[str, None, None]:
        """
        Stream chat response for real-time typing effect.

        Args:
            message: User's message
            context: Context for the conversation

        Yields:
            Response text chunks
        """
        if not self._initialized:
            fallback = self._fallback_response(message, context)
            yield fallback["response"]
            return

        try:
            self._wait_for_rate_limit()

            prompt = self._build_chat_prompt(message, context)
            response = self._model.generate_content(prompt, stream=True)

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            print(f"Gemini stream error: {e}")
            fallback = self._fallback_response(message, context)
            yield fallback["response"]

    async def chat_stream_async(
        self, message: str, context: str = "general"
    ) -> AsyncGenerator[str, None]:
        """Async streaming chat response."""
        if not self._initialized:
            fallback = self._fallback_response(message, context)
            yield fallback["response"]
            return

        try:
            self._wait_for_rate_limit()

            prompt = self._build_chat_prompt(message, context)
            response = await self._model.generate_content_async(prompt, stream=True)

            async for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            print(f"Gemini async stream error: {e}")
            fallback = self._fallback_response(message, context)
            yield fallback["response"]

    def _build_chat_prompt(self, message: str, context: str) -> str:
        """Build a contextual prompt for chat."""
        context_info = ""
        if context == "dashboard":
            context_info = (
                "\n[Context: User is on the TRACE Dashboard monitoring network health]"
            )
        elif context == "analysis":
            context_info = "\n[Context: User is analyzing telemetry data]"
        elif context == "remediation":
            context_info = "\n[Context: User is troubleshooting an issue]"

        return f"{context_info}\n\nUser: {message}"

    # -------------------------------------------------------------------------
    # Telemetry Analysis Methods
    # -------------------------------------------------------------------------

    def analyze_telemetry(
        self, telemetry_data: Dict[str, Any], analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Analyze network telemetry data using AI.

        Args:
            telemetry_data: Network metrics and telemetry
            analysis_type: Type of analysis ('comprehensive', 'energy', 'congestion', 'health')

        Returns:
            Analysis results with insights and recommendations
        """
        if not self._initialized:
            return self._fallback_telemetry_analysis(telemetry_data, analysis_type)

        # Check cache first
        cache_key = self.cache._make_key(telemetry_data, analysis_type)
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            self._wait_for_rate_limit()

            prompt = self._build_telemetry_prompt(telemetry_data, analysis_type)

            # Use reasoning model for complex analysis
            response = self._reasoning_model.generate_content(prompt)

            result = {
                "success": True,
                "analysis": response.text,
                "analysis_type": analysis_type,
                "source": "gemini",
                "model": self.reasoning_model_name,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Cache the result
            self.cache.set(cache_key, result)
            return result

        except Exception as e:
            print(f"Telemetry analysis error: {e}")
            return self._fallback_telemetry_analysis(telemetry_data, analysis_type)

    def _build_telemetry_prompt(
        self, telemetry_data: Dict[str, Any], analysis_type: str
    ) -> str:
        """Build prompt for telemetry analysis."""
        data_str = json.dumps(telemetry_data, indent=2)

        analysis_instructions = {
            "comprehensive": """Provide a comprehensive analysis including:
1. Overall network health assessment
2. Energy consumption patterns and optimization opportunities
3. Traffic/congestion analysis
4. Anomaly detection
5. Specific recommendations with expected impact""",
            "energy": """Focus on energy analysis:
1. Current energy consumption vs optimal levels
2. Towers/cells that can be powered down
3. TRX optimization opportunities
4. Expected savings percentage
5. Recommended actions with timing""",
            "congestion": """Focus on congestion analysis:
1. Current traffic load vs capacity
2. Predicted traffic patterns (next 4 hours)
3. Bottlenecks and hotspots
4. Load balancing recommendations
5. Pre-emptive actions to prevent issues""",
            "health": """Focus on system health:
1. Component status summary
2. Potential failures or degradation
3. Self-healing recommendations
4. MTTR estimates
5. Escalation priorities""",
        }

        return f"""Analyze the following network telemetry data:

```json
{data_str}
```

{analysis_instructions.get(analysis_type, analysis_instructions['comprehensive'])}

Format your response with clear markdown headings, bullet points, and tables where appropriate."""

    # -------------------------------------------------------------------------
    # Anomaly Detection Methods
    # -------------------------------------------------------------------------

    def detect_anomalies(
        self, metrics: Dict[str, Any], historical_context: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Detect anomalies in network metrics using AI.

        Args:
            metrics: Current network metrics
            historical_context: Optional historical data for comparison

        Returns:
            Detected anomalies with severity and recommendations
        """
        if not self._initialized:
            return self._fallback_anomaly_detection(metrics)

        try:
            self._wait_for_rate_limit()

            prompt = self._build_anomaly_prompt(metrics, historical_context)
            response = self._model.generate_content(prompt)

            # Parse the response to extract structured anomaly data
            anomalies = self._parse_anomaly_response(response.text, metrics)

            return {
                "success": True,
                "anomalies": anomalies,
                "raw_analysis": response.text,
                "source": "gemini",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            print(f"Anomaly detection error: {e}")
            return self._fallback_anomaly_detection(metrics)

    def _build_anomaly_prompt(
        self, metrics: Dict[str, Any], historical_context: Optional[List[Dict]]
    ) -> str:
        """Build prompt for anomaly detection."""
        metrics_str = json.dumps(metrics, indent=2)

        history_str = ""
        if historical_context:
            history_str = f"\n\nHistorical context (recent readings):\n```json\n{json.dumps(historical_context[-5:], indent=2)}\n```"

        return f"""Analyze these network metrics for anomalies:

Current metrics:
```json
{metrics_str}
```
{history_str}

Identify any anomalies and for each provide:
1. Type of anomaly (energy spike, congestion, signal degradation, etc.)
2. Severity (critical, high, medium, low)
3. Affected component/tower
4. Recommended action

Format as a structured analysis with clear severity ratings."""

    def _parse_anomaly_response(
        self, response_text: str, metrics: Dict[str, Any]
    ) -> List[Dict]:
        """Parse AI response to extract structured anomaly data."""
        # This is a simplified parser - in production, you'd want more robust parsing
        anomalies = []

        # Check for common keywords in the response
        response_lower = response_text.lower()

        if any(word in response_lower for word in ["critical", "severe", "emergency"]):
            anomalies.append(
                {
                    "severity": "critical",
                    "type": "detected_by_ai",
                    "description": "Critical issue detected in network metrics",
                    "affected_component": metrics.get("region", "unknown"),
                    "recommendation": "Immediate attention required",
                }
            )
        elif any(word in response_lower for word in ["high", "elevated", "concerning"]):
            anomalies.append(
                {
                    "severity": "high",
                    "type": "detected_by_ai",
                    "description": "Elevated risk detected in network metrics",
                    "affected_component": metrics.get("region", "unknown"),
                    "recommendation": "Monitor closely and prepare remediation",
                }
            )
        elif any(
            word in response_lower for word in ["medium", "moderate", "attention"]
        ):
            anomalies.append(
                {
                    "severity": "medium",
                    "type": "detected_by_ai",
                    "description": "Moderate issue detected in network metrics",
                    "affected_component": metrics.get("region", "unknown"),
                    "recommendation": "Schedule maintenance window",
                }
            )

        return anomalies

    # -------------------------------------------------------------------------
    # Recommendations Methods
    # -------------------------------------------------------------------------

    def get_recommendations(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get AI-powered remediation recommendations for an issue.

        Args:
            issue: Issue details including severity, affected components, etc.

        Returns:
            Recommendations with steps and expected outcomes
        """
        if not self._initialized:
            return self._fallback_recommendations(issue)

        try:
            self._wait_for_rate_limit()

            prompt = self._build_recommendations_prompt(issue)
            response = self._model.generate_content(prompt)

            return {
                "success": True,
                "recommendations": response.text,
                "issue_id": issue.get("id"),
                "source": "gemini",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            print(f"Recommendations error: {e}")
            return self._fallback_recommendations(issue)

    def _build_recommendations_prompt(self, issue: Dict[str, Any]) -> str:
        """Build prompt for getting recommendations."""
        issue_str = json.dumps(issue, indent=2)

        return f"""Analyze this network issue and provide remediation recommendations:

Issue Details:
```json
{issue_str}
```

Provide:
1. Root cause analysis (brief)
2. Recommended remediation steps (prioritized)
3. Expected outcome for each step
4. Estimated time to resolution
5. Preventive measures for the future

Available remediation actions:
- restart_agent: Restart the affected monitoring agent (~30s)
- redeploy_agent: Full agent redeployment (~2min)
- reroute_traffic: Redirect traffic to healthy nodes (~45s)

Format with clear markdown and actionable steps."""

    # -------------------------------------------------------------------------
    # JSON Data Analysis (for uploaded files)
    # -------------------------------------------------------------------------

    def analyze_json_data(
        self, json_data: Any, query: str = "comprehensive analysis"
    ) -> Dict[str, Any]:
        """
        Analyze uploaded JSON data using AI + principal_agent analysis tools.

        Args:
            json_data: Parsed JSON data (list or dict)
            query: Specific analysis query

        Returns:
            Analysis results with AI insights and structured analysis
        """
        # First, perform structured analysis using principal_agent tools if available
        structured_analysis = None
        if ANALYSIS_TOOLS_AVAILABLE:
            try:
                records = json_data if isinstance(json_data, list) else [json_data]
                # Determine analysis type from query
                query_lower = query.lower()
                if any(word in query_lower for word in ["energy", "power", "saving"]):
                    analysis_type = "energy"
                elif any(
                    word in query_lower
                    for word in ["congestion", "traffic", "bandwidth"]
                ):
                    analysis_type = "congestion"
                elif any(
                    word in query_lower for word in ["health", "error", "failure"]
                ):
                    analysis_type = "health"
                else:
                    analysis_type = "comprehensive"

                structured_analysis = _perform_analysis(
                    records, analysis_type, ["performance", "recommendations"]
                )
            except Exception as e:
                print(f"Structured analysis error: {e}")

        if not self._initialized:
            return self._fallback_json_analysis(json_data, query, structured_analysis)

        try:
            self._wait_for_rate_limit()

            # Format data for the prompt
            records = json_data if isinstance(json_data, list) else [json_data]

            # Include structured analysis in the prompt if available
            analysis_context = ""
            if structured_analysis:
                analysis_context = f"""
## Pre-computed Analysis Results:
{json.dumps(structured_analysis, indent=2)}
"""

            if len(records) > 10:
                # For large datasets, show sample
                sample = records[:5]
                data_str = f"Sample (5 of {len(records)} records):\n{json.dumps(sample, indent=2)}"
            else:
                data_str = json.dumps(records, indent=2)

            prompt = f"""Analyze this network telemetry data for the TRACE system:

```json
{data_str}
```
{analysis_context}

Query: {query}

Provide insights as the TRACE Principal Agent:
1. **Data Overview**: Key patterns and summary statistics
2. **Energy Optimization**: Towers with <30% utilization = energy saving opportunity (30-40% savings)
3. **Congestion Risk**: Towers with >70% utilization = congestion risk
4. **Health Issues**: Errors, latency spikes, packet loss
5. **Actionable Recommendations**: Prioritized actions with expected impact

Format with markdown tables and bullet points. Be specific about tower IDs and metrics."""

            # Use reasoning model for data analysis
            response = self._reasoning_model.generate_content(prompt)

            return {
                "success": True,
                "analysis": response.text,
                "query": query,
                "data_records": len(json_data) if isinstance(json_data, list) else 1,
                "source": "gemini",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            print(f"JSON analysis error: {e}")
            return self._fallback_json_analysis(json_data, query)

    # -------------------------------------------------------------------------
    # Fallback Methods (when Gemini is unavailable)
    # -------------------------------------------------------------------------

    def _fallback_response(self, message: str, context: str) -> Dict[str, Any]:
        """Provide intelligent fallback response."""
        msg_lower = message.lower()

        if any(word in msg_lower for word in ["health", "status", "check"]):
            response = """📊 **System Health Summary**

| Component | Status | Score |
|-----------|--------|-------|
| Principal Agent | ✅ Active | 98% |
| Regional Coordinators | ✅ Healthy | 95% |
| Edge Agents | ✅ Running | 96% |

**Note:** Connect Gemini API for real-time AI analysis."""

        elif any(word in msg_lower for word in ["energy", "power", "consumption"]):
            response = """⚡ **Energy Overview**

• Current Savings: ~34% vs baseline
• Optimization Opportunities: 3 towers identified
• Recommended: Enable energy saver mode during 2-5 AM

**Note:** Full AI analysis requires Gemini API connection."""

        elif any(word in msg_lower for word in ["help", "what can", "capabilities"]):
            response = """🎯 **TRACE AI Agent Capabilities**

• **Energy Optimization** - 30-40% savings
• **Congestion Management** - Predictive load balancing
• **Self-Healing** - <5 min MTTR
• **Data Analysis** - JSON telemetry insights

Type your question to get started!"""

        else:
            response = f"""I received your message: "{message}"

I'm the TRACE Principal Agent. I can help with:
• Network health monitoring
• Energy optimization
• Traffic management
• Issue remediation

**Note:** Gemini API connection required for full AI capabilities."""

        return {
            "success": True,
            "response": response,
            "source": "fallback",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _fallback_telemetry_analysis(
        self, telemetry_data: Dict[str, Any], analysis_type: str
    ) -> Dict[str, Any]:
        """Fallback telemetry analysis."""
        return {
            "success": True,
            "analysis": f"**{analysis_type.title()} Analysis** (Fallback Mode)\n\nTelemetry received with {len(telemetry_data)} metrics.\nConnect Gemini API for AI-powered insights.",
            "analysis_type": analysis_type,
            "source": "fallback",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _fallback_anomaly_detection(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback anomaly detection."""
        return {
            "success": True,
            "anomalies": [],
            "raw_analysis": "No AI anomaly detection available. Connect Gemini API for intelligent monitoring.",
            "source": "fallback",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _fallback_recommendations(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback recommendations."""
        action = issue.get("suggestedAction", "restart_agent")
        return {
            "success": True,
            "recommendations": f"""**Recommended Action:** {action}

1. Execute `{action}` for affected component
2. Monitor metrics for 5 minutes
3. Escalate if issue persists

Connect Gemini API for detailed AI recommendations.""",
            "issue_id": issue.get("id"),
            "source": "fallback",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _fallback_json_analysis(
        self, json_data: Any, query: str, structured_analysis: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Fallback JSON analysis using principal_agent tools when AI is unavailable."""
        record_count = len(json_data) if isinstance(json_data, list) else 1

        # If we have structured analysis from principal_agent tools, use it
        if structured_analysis:
            analysis_text = f"""## JSON Data Analysis (Using Local Analysis Engine)

**Query:** {query}

### Summary
- **Records Analyzed:** {record_count}
- **Unique Towers:** {structured_analysis.get('summary', {}).get('unique_towers', 'N/A')}
- **Avg Bandwidth:** {structured_analysis.get('summary', {}).get('avg_bandwidth_utilization', 'N/A')}%
- **Avg Latency:** {structured_analysis.get('summary', {}).get('avg_latency_ms', 'N/A')}ms

### Key Findings
"""
            for finding in structured_analysis.get("key_findings", [])[:5]:
                analysis_text += f"- {finding}\n"

            analysis_text += "\n### Insights\n"
            for insight in structured_analysis.get("insights", [])[:5]:
                analysis_text += f"- {insight}\n"

            analysis_text += "\n### Recommendations\n"
            for rec in structured_analysis.get("recommendations", [])[:3]:
                if isinstance(rec, dict):
                    analysis_text += f"- **{rec.get('category', 'General')}** [{rec.get('priority', 'MEDIUM')}]: {rec.get('title', 'Action needed')}\n"
                    analysis_text += f"  - Expected Impact: {rec.get('expected_impact', 'Improvement')}\n"
                else:
                    analysis_text += f"- {rec}\n"

            return {
                "success": True,
                "analysis": analysis_text,
                "structured_analysis": structured_analysis,
                "query": query,
                "data_records": record_count,
                "source": "local_analysis",
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Basic fallback without structured analysis
        return {
            "success": True,
            "analysis": f"Received {record_count} data records.\nQuery: {query}\n\nConnect Gemini API for AI-powered data analysis.",
            "query": query,
            "data_records": record_count,
            "source": "fallback",
            "timestamp": datetime.utcnow().isoformat(),
        }


# Singleton instance for use across the application
gemini_service = GeminiService()

# Update global availability flag
GEMINI_AVAILABLE = gemini_service.is_available()


# Convenience functions for direct use
def chat(message: str, context: str = "general") -> Dict[str, Any]:
    """Send a chat message to Gemini."""
    return gemini_service.chat(message, context)


def chat_stream(message: str, context: str = "general") -> Generator[str, None, None]:
    """Stream chat response from Gemini."""
    return gemini_service.chat_stream(message, context)


def analyze_telemetry(
    telemetry_data: Dict[str, Any], analysis_type: str = "comprehensive"
) -> Dict[str, Any]:
    """Analyze network telemetry data."""
    return gemini_service.analyze_telemetry(telemetry_data, analysis_type)


def detect_anomalies(
    metrics: Dict[str, Any], historical_context: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """Detect anomalies in network metrics."""
    return gemini_service.detect_anomalies(metrics, historical_context)


def get_recommendations(issue: Dict[str, Any]) -> Dict[str, Any]:
    """Get AI-powered remediation recommendations."""
    return gemini_service.get_recommendations(issue)


def analyze_json_data(
    json_data: Any, query: str = "comprehensive analysis"
) -> Dict[str, Any]:
    """Analyze uploaded JSON data."""
    return gemini_service.analyze_json_data(json_data, query)
