"""
Agent Integration Module for TRACE Dashboard

This module provides the bridge between the dashboard server and the
Principal Agent (ADK framework). It enables:
- Real AI-powered auto-remediation when users click "Auto Remediate"
- Running ADK web separately while still integrating with the dashboard
- Intelligent analysis of issues using the principal agent

The integration supports two modes:
1. Standalone Mode: Dashboard uses mock responses when ADK is not available
2. Integrated Mode: Dashboard connects to the principal agent for real AI responses
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

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

# Add project root to path for principal_agent imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(CLIENT_DIR)

for path in (CLIENT_DIR, ROOT_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

# Try to import the principal agent for real AI integration
PRINCIPAL_AGENT_AVAILABLE = False
principal_agent = None

try:
    from principal_agent.agent import principal_agent as _principal_agent
    from principal_agent.tools.remediation import (
        restart_agent,
        redeploy_agent,
        reroute_traffic,
    )
    from principal_agent.tools.health_monitor import (
        check_system_health,
        get_agent_status,
    )
    from principal_agent.tools.dashboard import get_system_metrics

    principal_agent = _principal_agent
    PRINCIPAL_AGENT_AVAILABLE = True
    print("✅ Principal Agent integration enabled - AI-powered remediation active")
except ImportError as e:
    print(f"⚠️ Principal Agent not available: {e}")
    print("   Dashboard will use fallback mode for remediation")


# Try to import google-adk for invoking the agent
ADK_AVAILABLE = False
try:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    ADK_AVAILABLE = True
    print("✅ Google ADK available - Full agent interaction enabled")
except ImportError as e:
    print(f"⚠️ Google ADK not available: {e}")

# Import Gemini Service for direct AI integration
try:
    from gemini_service import gemini_service, GeminiService

    GEMINI_AVAILABLE = gemini_service.is_available()
    if GEMINI_AVAILABLE:
        print("✅ Gemini Service available - Direct AI responses enabled")
except ImportError as e:
    GEMINI_AVAILABLE = False
    gemini_service = None
    print(f"⚠️ Gemini Service not available: {e}")


class AgentIntegration:
    """
    Bridge between the dashboard and the Principal Agent.

    Provides methods for:
    - Sending issues to the agent for analysis
    - Getting AI-powered remediation recommendations
    - Executing remediation actions through the agent
    """

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._runner = None
        self._session_service = None
        self._initialized = False

        if PRINCIPAL_AGENT_AVAILABLE and ADK_AVAILABLE:
            self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the ADK runner for agent interaction."""
        try:
            self._session_service = InMemorySessionService()
            self._runner = Runner(
                agent=principal_agent,
                app_name="trace_dashboard",
                session_service=self._session_service,
            )
            self._initialized = True
            print("✅ Agent runner initialized successfully")
        except Exception as e:
            print(f"⚠️ Failed to initialize agent runner: {e}")
            self._initialized = False

    def is_available(self) -> bool:
        """Check if the principal agent is available for integration."""
        return PRINCIPAL_AGENT_AVAILABLE

    def is_adk_available(self) -> bool:
        """Check if full ADK interaction is available."""
        return self._initialized

    async def analyze_issue_async(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send an issue to the principal agent for AI analysis.

        Priority:
        1. ADK Runner (full agent with tools)
        2. Gemini Service (direct AI analysis)
        3. Fallback (hardcoded analysis)

        Args:
            issue: The issue data from the dashboard

        Returns:
            Analysis result with recommendations
        """
        if not self._initialized:
            # Try Gemini Service for AI analysis
            if GEMINI_AVAILABLE and gemini_service:
                try:
                    result = gemini_service.get_recommendations(issue)
                    return {
                        "success": result.get("success", True),
                        "analysis": result.get("recommendations", ""),
                        "source": "gemini",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                except Exception as e:
                    print(f"Gemini analysis failed: {e}")
            return self._fallback_analysis(issue)

        try:
            # Create a prompt for the agent
            prompt = self._build_analysis_prompt(issue)

            # Run the agent
            session = await self._session_service.create_session(
                app_name="trace_dashboard",
                user_id="dashboard_user",
            )

            response_text = ""
            async for event in self._runner.run_async(
                user_id="dashboard_user",
                session_id=session.id,
                new_message=types.Content(
                    role="user", parts=[types.Part.from_text(prompt)]
                ),
            ):
                if hasattr(event, "content") and event.content:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text

            return {
                "success": True,
                "analysis": response_text,
                "source": "principal_agent",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            print(f"Agent analysis failed: {e}")
            return self._fallback_analysis(issue)

    def analyze_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper for analyze_issue_async."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.analyze_issue_async(issue))

    async def auto_remediate_async(
        self, issue: Dict[str, Any], action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute AI-powered auto-remediation for an issue.

        Args:
            issue: The issue to remediate
            action: Optional specific action to take

        Returns:
            Remediation result with details
        """
        if not PRINCIPAL_AGENT_AVAILABLE:
            return self._fallback_remediation(issue, action)

        try:
            # Determine the action to take
            remediation_action = action or issue.get("suggestedAction", "restart_agent")

            # Execute the remediation using principal agent tools
            if self._initialized:
                # Use the agent to decide and execute remediation
                result = await self._agent_remediate(issue, remediation_action)
            else:
                # Use direct tool execution
                result = self._direct_remediate(issue, remediation_action)

            return {
                "success": result.get("success", True),
                "operation": remediation_action,
                "issueId": issue.get("id"),
                "message": result.get(
                    "message", f"Remediation {remediation_action} executed"
                ),
                "details": result,
                "source": "principal_agent" if self._initialized else "direct_tools",
                "timestamp": datetime.utcnow().isoformat(),
                "agent_response": result.get("agent_response", None),
            }

        except Exception as e:
            print(f"Remediation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "issueId": issue.get("id"),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _agent_remediate(
        self, issue: Dict[str, Any], action: str
    ) -> Dict[str, Any]:
        """Execute remediation through the principal agent."""
        prompt = self._build_remediation_prompt(issue, action)

        session = await self._session_service.create_session(
            app_name="trace_dashboard",
            user_id="dashboard_user",
        )

        response_text = ""
        async for event in self._runner.run_async(
            user_id="dashboard_user",
            session_id=session.id,
            new_message=types.Content(
                role="user", parts=[types.Part.from_text(prompt)]
            ),
        ):
            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        response_text += part.text

        return {
            "success": True,
            "message": f"Agent executed {action}",
            "agent_response": response_text,
        }

    def _direct_remediate(self, issue: Dict[str, Any], action: str) -> Dict[str, Any]:
        """Execute remediation using tools directly."""
        affected_towers = issue.get("affectedTowers", ["Tower-1"])
        primary_tower = affected_towers[0] if affected_towers else "Tower-1"

        if action == "restart_agent":
            result = restart_agent(
                agent_name=issue.get("activeAgent", "monitoring_agent"),
                reason=issue.get("title", "dashboard_triggered"),
            )
        elif action == "redeploy_agent":
            result = redeploy_agent(
                agent_name=issue.get("activeAgent", "monitoring_agent")
            )
        elif action == "reroute_traffic":
            result = reroute_traffic(
                source=primary_tower,
                target=(
                    f"Tower-{(int(primary_tower.split('-')[1]) % 10) + 1}"
                    if "-" in primary_tower
                    else "Tower-2"
                ),
                percentage=30,
            )
        else:
            # Default to restart
            result = restart_agent(
                agent_name="monitoring_agent", reason="unknown_action_fallback"
            )

        return result

    def auto_remediate(
        self, issue: Dict[str, Any], action: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synchronous wrapper for auto_remediate_async."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.auto_remediate_async(issue, action))

    async def chat_async(
        self, message: str, context: str = "general"
    ) -> Dict[str, Any]:
        """
        Send a chat message to the Principal Agent and get a response.

        Priority:
        1. ADK Runner (if initialized) - Full agent with tools
        2. Gemini Service (if available) - Direct AI responses
        3. Fallback responses (hardcoded)

        Args:
            message: The user's message
            context: The context of the chat (e.g., 'trace_dashboard', 'general')

        Returns:
            Response from the agent
        """
        # Try ADK Runner first (full agent with tools)
        if not self._initialized:
            # Try Gemini Service as secondary option
            if GEMINI_AVAILABLE and gemini_service:
                try:
                    return await gemini_service.chat_async(message, context)
                except Exception as e:
                    print(f"Gemini chat failed, using fallback: {e}")
            return self._fallback_chat(message, context)

        try:
            prompt = self._build_chat_prompt(message, context)

            session = await self._session_service.create_session(
                app_name="trace_dashboard",
                user_id="dashboard_user",
            )

            response_text = ""
            async for event in self._runner.run_async(
                user_id="dashboard_user",
                session_id=session.id,
                new_message=types.Content(
                    role="user", parts=[types.Part.from_text(prompt)]
                ),
            ):
                if hasattr(event, "content") and event.content:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text

            return {
                "success": True,
                "response": response_text,
                "source": "principal_agent",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            print(f"Chat failed: {e}")
            return self._fallback_chat(message, context)

    def chat(self, message: str, context: str = "general") -> Dict[str, Any]:
        """Synchronous wrapper for chat_async."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.chat_async(message, context))

    def _build_chat_prompt(self, message: str, context: str) -> str:
        """Build a comprehensive prompt for chat interaction."""
        return f"""You are the TRACE Principal Agent, an advanced AI-powered telecom network management system built with Google ADK.

## Your Role
You are the global orchestrator for TRACE (Traffic & Resource Agentic Control Engine), coordinating a hierarchical multi-agent system for telecom network optimization.

## Agent Hierarchy You Manage
- **Principal Agent (You)**: Global orchestrator, health monitoring, self-healing
- **Regional Coordinators (3)**: Manage tower clusters, aggregate telemetry, enforce policies
- **Edge Agents (5 per tower)**: Monitoring, Prediction, Decision xApp, Action, Learning

## Your Capabilities
1. **Energy Optimization** - Reduce tower energy by 30-40% during low demand via TRX shutdowns
2. **Congestion Management** - Predict traffic surges, pre-activate backup cells, load balancing
3. **Self-Healing** - Detect failures, execute restart/redeploy/reroute (<5 min MTTR)
4. **Data Analysis** - Analyze JSON telemetry, provide LLM-powered insights

## Available Tools
- Health: check_system_health, get_agent_status
- Remediation: restart_agent, redeploy_agent, reroute_traffic
- Dashboard: generate_health_dashboard, get_system_metrics
- Data: process_uploaded_json, query_rag_data, add_json_data, analyze_json_data_with_llm

## Context
Dashboard Context: {context}

## User Query
{message}

## Response Guidelines
1. Be concise but comprehensive - use bullet points and tables where helpful
2. Provide specific metrics and numbers when discussing status
3. Always suggest actionable next steps
4. If discussing issues, include severity and recommended remediation
5. When showing data, format it clearly with markdown
6. Mention relevant tools the user can use for more details
7. For complex operations, explain the multi-agent workflow involved

Respond helpfully and professionally as the TRACE Principal Agent."""

    def _fallback_chat(self, message: str, context: str) -> Dict[str, Any]:
        """
        Provide chat response when ADK agent is not available.

        First tries Gemini Service for real AI responses,
        then falls back to hardcoded responses if Gemini is unavailable.
        """
        # Try Gemini Service first for real AI responses
        if GEMINI_AVAILABLE and gemini_service:
            try:
                return gemini_service.chat(message, context)
            except Exception as e:
                print(f"Gemini fallback failed: {e}")

        # Hardcoded fallback responses (only if Gemini unavailable)
        msg_lower = message.lower()

        if any(word in msg_lower for word in ["health", "status", "check", "overview"]):
            response = """📊 **System Health Report**

**Overall Status:** ✅ Operational (95.7%)

| Component | Status | Count |
|-----------|--------|-------|
| Principal Agent | ✅ Active | 1/1 |
| Regional Coordinators | ✅ Healthy | 3/3 |
| Edge Agents | ✅ Running | 15/15 |
| Towers Online | ✅ Active | 48/50 |

**Performance Metrics:**
• **CPU Usage:** 45% avg
• **Memory:** 62% avg
• **Network Latency:** 42ms
• **Error Rate:** 0.02%

**Recent Activity:**
• Energy savings: 34.2% achieved today
• Congestion events prevented: 3 (last 6h)
• Auto-remediations: 2 successful

**💡 Suggested Actions:**
1. Run energy optimization for additional savings
2. Review tower_12 for minor latency spike
3. Check upcoming event calendar for surge planning

Use **Developer Mode** for advanced analysis with the full ADK interface."""

        elif any(
            word in msg_lower
            for word in ["energy", "power", "consumption", "saving", "kwh"]
        ):
            response = """⚡ **Energy Optimization Analysis**

**Current Status:**
• Total Consumption: 1,245 kWh (last hour)
• Savings Achieved: **34.2%** vs baseline
• CO₂ Reduction: 523 kg today

**🔋 Optimization Opportunities:**

| Tower | Load | Action | Expected Savings |
|-------|------|--------|-----------------|
| TX003 | 23% | Reduce TRX 40% | 85 kWh/day |
| TX007 | 18% | Sleep mode | 72 kWh/day |
| TX012 | 31% | Partial shutdown | 45 kWh/day |

**Forecast (Next 4 Hours):**
• Low traffic predicted: 2:00 AM - 5:00 AM
• Recommended: Enable Energy Saving Mode on 12 towers
• Expected additional savings: **30-40%**

**Workflow:**
```
Monitor → Predict → Decide → Act → Learn
   ↓         ↓         ↓       ↓       ↓
 Metrics   Forecast   Safe?   TRX    Retrain
                              Ctrl
```

**💡 Try:** "Analyze energy consumption for tower_5" for tower-specific insights."""

        elif any(
            word in msg_lower
            for word in [
                "congestion",
                "traffic",
                "surge",
                "load",
                "balance",
                "concert",
                "event",
            ]
        ):
            response = """🌐 **Congestion Management Analysis**

**Current Traffic Status:**
• Network Load: 67% capacity
• Peak Traffic: 485 Gbps
• Active Connections: 32,450

**Risk Assessment:**
• Current Risk Level: ⚠️ MODERATE
• Predicted surge in 4 hours: +45%

**Pre-emptive Load Balancing Strategy:**

| Action | Towers | Timing | Impact |
|--------|--------|--------|--------|
| Pre-activate backup cells | TX003, TX004 | Now | +40% capacity |
| Increase capacity | TX007, TX008 | +1h | +35% headroom |
| Traffic overflow setup | TX001, TX002 | Ready | Failover ready |

**Monitoring Plan:**
• Enhanced monitoring: 6 PM - 12 AM
• Alert threshold: 85% capacity
• Auto-scaling: Enabled

**Expected Outcomes:**
✅ Zero dropped calls during surge
✅ Maintained QoE (Quality of Experience)
✅ Seamless handoff between towers

**💡 Try:** "There's a concert tonight - prepare load balancing strategy" for event-specific planning."""

        elif any(
            word in msg_lower
            for word in [
                "remediat",
                "fix",
                "heal",
                "recover",
                "restart",
                "fail",
                "agent",
            ]
        ):
            response = """🔧 **Self-Healing & Remediation**

**Available Actions:**

| Action | Description | MTTR | Success Rate |
|--------|-------------|------|--------------|
| `restart_agent` | Restart monitoring agent | ~30s | 95% |
| `redeploy_agent` | Full agent redeployment | ~2min | 98% |
| `reroute_traffic` | Redirect to healthy nodes | ~45s | 97% |

**Self-Healing Workflow:**
```
Failure → Diagnose → Restart → Verify → (Escalate)
  <10s      Auto       Auto     Check     If needed
```

**Current Agent Status:**
| Agent Type | Status | Count |
|------------|--------|-------|
| Principal | ✅ Active | 1/1 |
| Regional | ✅ Healthy | 3/3 |
| Edge Monitoring | ✅ Running | 15/15 |
| Edge Prediction | ✅ Running | 15/15 |
| Edge Decision | ✅ Running | 15/15 |

**Recent Remediation History:**
• 2h ago: `restart_agent` on tower_7 → ✅ Success
• 5h ago: `reroute_traffic` TX003→TX004 → ✅ Success

**💡 Try:** "The monitoring agent at tower_12 stopped responding" to trigger self-healing."""

        elif any(
            word in msg_lower
            for word in ["data", "json", "analyze", "telemetry", "metric", "load"]
        ):
            response = """📊 **Data Analysis Capabilities**

**Available Data Tools:**

| Tool | Purpose | Usage |
|------|---------|-------|
| `add_json_data` | Load JSON file | `Load data/trace_reduced_20.json` |
| `analyze_json_data_with_llm` | AI analysis | `Analyze this data comprehensively` |
| `get_recommendations_from_json` | Get insights | `Get energy recommendations` |
| `compare_json_datasets` | Compare files | `Compare with trace_llm_20.json` |

**Analysis Dimensions:**
• 📈 **Energy Insights** - Utilization patterns, savings opportunities
• 🌐 **Congestion Patterns** - Peak usage, bandwidth trends
• 🔧 **Health Issues** - Signal quality, latency, errors
• 🔮 **Predictive Insights** - Forecast trends, anomaly detection

**Sample Workflow:**
```
1. Load data/trace_reduced_20.json
2. Analyze this data for energy optimization
3. Get specific recommendations for tower TX005
4. Compare with historical data
```

**💡 Try:** "Load data/trace_reduced_20.json and analyze for energy optimization" """

        elif any(
            word in msg_lower
            for word in ["help", "what can", "capabilit", "feature", "how to"]
        ):
            response = """🎯 **TRACE AI Agent - Full Capabilities**

**🔋 Energy Optimization**
• Reduce tower energy 30-40% during low demand
• Automatic TRX shutdown scheduling
• Real-time savings tracking
• *Try:* "Analyze energy consumption patterns"

**🌐 Congestion Management**
• Predict and prevent traffic surges
• Proactive load balancing
• Event-based capacity planning
• *Try:* "Prepare for concert at stadium tonight"

**🔧 Self-Healing**
• Autonomous failure detection (<10 sec)
• Automated remediation (<5 min MTTR)
• Escalation workflows
• *Try:* "Show self-healing for failed agent"

**📊 Data Analysis**
• JSON telemetry processing
• LLM-powered insights
• Historical trend analysis
• *Try:* "Load and analyze trace_reduced_20.json"

**Multi-Agent Architecture:**
```
Principal Agent (You're talking to me!)
    ├── Regional Coordinators (3)
    │   └── Edge Agents (5 per tower)
    │       ├── Monitoring
    │       ├── Prediction
    │       ├── Decision xApp
    │       ├── Action
    │       └── Learning
```

**💡 Pro Tip:** Use **Developer Mode** for the full Google ADK Web Interface!"""

        else:
            response = f"""I understand you're asking about: "{message}"

As the **TRACE Principal Agent**, I coordinate a multi-agent system for telecom network optimization.

**🎯 I can help with:**

| Category | Example Prompts |
|----------|----------------|
| 🔋 Energy | "Analyze energy patterns for tower_5" |
| 🌐 Traffic | "Prepare for tonight's concert surge" |
| 🔧 Healing | "Show remediation for failed agent" |
| 📊 Data | "Load and analyze JSON telemetry" |
| 📈 Status | "Check overall system health" |

**Quick Actions:**
• Click suggestion chips below the chat
• Use the sidebar for categorized prompts
• Try "help" for full capabilities

**💡 For advanced features:**
Use **Developer Mode** to access the Google ADK Web Interface with full agent interaction."""

        return {
            "success": True,
            "response": response,
            "source": "fallback",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _build_analysis_prompt(self, issue: Dict[str, Any]) -> str:
        """Build a prompt for the agent to analyze an issue."""
        return f"""
Analyze this network issue and provide recommendations:

Issue ID: {issue.get('id')}
Title: {issue.get('title')}
Severity: {issue.get('severity')}
Description: {issue.get('description')}
Affected Towers: {issue.get('affectedTowers', [])}
Impact Score: {issue.get('impactScore')}
Current Status: {issue.get('status')}

Detailed Analysis from monitoring:
{issue.get('detailedAnalysis', 'No detailed analysis available')}

Please provide:
1. Root cause analysis
2. Recommended remediation actions
3. Expected impact of remediation
4. Any preventive measures for the future
"""

    def _build_remediation_prompt(self, issue: Dict[str, Any], action: str) -> str:
        """Build a prompt for the agent to execute remediation."""
        return f"""
Execute remediation for the following issue:

Issue: {issue.get('title')}
Severity: {issue.get('severity')}
Affected Components: {issue.get('affectedTowers', [])}
Suggested Action: {action}

Please execute the {action} action to resolve this issue.
Provide a summary of what was done and the expected outcome.
"""

    def _fallback_analysis(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback analysis when agent is not available."""
        severity = issue.get("severity", "medium")

        analysis = f"""
**Issue Analysis** (Fallback Mode)

**Issue:** {issue.get('title', 'Unknown Issue')}
**Severity:** {severity.upper()}

**Root Cause Assessment:**
Based on the metrics patterns, this issue appears to be related to 
{issue.get('detailedAnalysis', 'elevated resource usage')}.

**Recommended Actions:**
1. {issue.get('suggestedAction', 'restart_agent').replace('_', ' ').title()}
2. Monitor system metrics for 15 minutes post-remediation
3. If issue persists, escalate to redeploy_agent

**Note:** Full AI analysis requires the Principal Agent to be running.
Start with: adk web
"""

        return {
            "success": True,
            "analysis": analysis,
            "source": "fallback",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _fallback_remediation(
        self, issue: Dict[str, Any], action: Optional[str]
    ) -> Dict[str, Any]:
        """Provide fallback remediation when agent is not available."""
        remediation_action = action or issue.get("suggestedAction", "restart_agent")

        return {
            "success": True,
            "operation": remediation_action,
            "issueId": issue.get("id"),
            "message": f"Simulated {remediation_action} - Agent not available",
            "source": "fallback",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_status(self) -> Dict[str, Any]:
        """Get the integration status."""
        # Determine mode based on available services
        if self._initialized:
            mode = "integrated"  # Full ADK agent
        elif GEMINI_AVAILABLE:
            mode = "gemini"  # Direct Gemini AI
        elif PRINCIPAL_AGENT_AVAILABLE:
            mode = "tools_only"  # Direct tool execution
        else:
            mode = "fallback"  # Hardcoded responses

        return {
            "principal_agent_available": PRINCIPAL_AGENT_AVAILABLE,
            "adk_available": ADK_AVAILABLE,
            "gemini_available": GEMINI_AVAILABLE,
            "fully_initialized": self._initialized,
            "mode": mode,
        }


# Singleton instance for use across the application
agent_integration = AgentIntegration()
