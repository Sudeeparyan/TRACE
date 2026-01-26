"""
TRACE Principal Agent (Self-Healing Agent)

The Principal Agent is the global orchestrator that monitors all Parent and Child agents,
detects anomalies, infrastructure failures, and cascading faults, and executes safe
automated remediations.

This agent uses a LoopAgent pattern for continuous monitoring and healing.

SUPPORTED MODELS (Multi-Provider):
- Google: gemini-3-flash (fast), gemini-3-pro (reasoning)
- Anthropic: claude-sonnet-4.5 (fast), claude-opus-4.5 (reasoning)
- OpenAI: gpt-5-mini (fast), gpt-5.2 (reasoning)
- DeepSeek: deepseek-v3 (fast), deepseek-reasoning (reasoning)

IMPORTANT: JSON File Upload Handling
------------------------------------
When JSON files are uploaded through ADK web interface, they come as inline_data
with mime_type="application/json". Gemini API doesn't support this mimeType.

Solution: The json_file_handler module converts JSON files to text BEFORE sending to LLM.
This happens transparently - users can upload JSON files normally.
"""

import os
from google.adk.agents import Agent, LoopAgent
from google.adk.tools.agent_tool import AgentTool

from .parent_agents.regional_coordinator.agent import regional_coordinator
from .tools.health_monitor import check_system_health, get_agent_status
from .tools.remediation import restart_agent, redeploy_agent, reroute_traffic
from .tools.dashboard import generate_health_dashboard, get_system_metrics
from .tools.json_data_processor import (
    add_json_data,
    analyze_json_data_with_llm,
    get_recommendations_from_json,
    compare_json_datasets,
)
from .tools.rag_file_processor import (
    process_uploaded_json,
    query_rag_data,
    get_rag_summary,
)

# Model configuration - supports multiple providers
# Default: gemini-2.0-flash (fast mode) or gemini-1.5-pro (reasoning mode)
# Override with TRACE_MODEL_ID environment variable
DEFAULT_MODEL = "gemini-2.0-flash"
REASONING_MODEL = "gemini-1.5-pro"
CURRENT_MODEL = os.getenv("TRACE_MODEL_ID", DEFAULT_MODEL)


# Principal Agent - Global Orchestrator
principal_agent = Agent(
    name="principal_agent",
    model=CURRENT_MODEL,
    description="Principal (Self-Healing) Agent - Global orchestrator for TRACE system",
    instruction="""
    You are the Principal Agent for TRACE - global orchestrator and health guardian.

    Responsibilities:
    • Monitor agents and detect failures
    • Execute safe automated remediations
    • Provide health dashboards
    • Analyze JSON telemetry data

    Tools Available:
    • Regional Coordinator: Regional management
    • Health: check_system_health, get_agent_status
    • Remediation: restart_agent, redeploy_agent, reroute_traffic
    • Dashboard: generate_health_dashboard, get_system_metrics
    • Data Analysis: process_uploaded_json, query_rag_data, get_rag_summary
    • File Path Tools: add_json_data, analyze_json_data_with_llm, get_recommendations_from_json

    JSON File Upload Workflow:
    1. When user uploads/pastes JSON data, you'll see it as formatted text
    2. Extract the JSON content from the message
    3. Call process_uploaded_json(json_content) to load it
    4. Use query_rag_data() or get_rag_summary() to analyze
    5. Return insights and recommendations

    Example:
    User: "Analyze this data for energy optimization" [with JSON content]
    You:  1. Extract JSON from message
          2. Call process_uploaded_json with the JSON string
          3. Call query_rag_data("What are energy optimization opportunities?")
          4. Return the analysis

    File Path Method (Alternative):
    - add_json_data("data/file.json") - Load from path
    - analyze_json_data_with_llm() - Analyze loaded data
    - get_recommendations_from_json() - Get specific recommendations

    Focus Areas:
    - Energy optimization (30-40% savings potential)
    - Congestion risk mitigation
    - Network health monitoring
    - Actionable recommendations

    Keep responses concise and actionable. Always prioritize system stability.
    """,
    sub_agents=[regional_coordinator],
    tools=[
        # Health monitoring
        check_system_health,
        get_agent_status,
        # Remediation
        restart_agent,
        redeploy_agent,
        reroute_traffic,
        # Dashboard
        generate_health_dashboard,
        get_system_metrics,
        # Data analysis tools
        process_uploaded_json,
        query_rag_data,
        get_rag_summary,
        # File path tools
        add_json_data,
        analyze_json_data_with_llm,
        get_recommendations_from_json,
        compare_json_datasets,
    ],
)

# Create a LoopAgent for continuous monitoring
monitoring_loop = LoopAgent(
    name="self_healing_loop",
    sub_agents=[principal_agent],
    max_iterations=100,
)

# Export as root_agent for ADK
root_agent = principal_agent
