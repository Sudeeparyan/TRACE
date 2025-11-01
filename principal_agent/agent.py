"""
TRACE Principal Agent (Self-Healing Agent)

The Principal Agent is the global orchestrator that monitors all Parent and Child agents,
detects anomalies, infrastructure failures, and cascading faults, and executes safe
automated remediations.

This agent uses a LoopAgent pattern for continuous monitoring and healing.
"""

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


# Principal Agent - Global Orchestrator
principal_agent = Agent(
    name="principal_agent",
    model="gemini-2.0-flash-exp",  # Using more stable model
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
    • JSON: add_json_data, analyze_json_data_with_llm, get_recommendations_from_json, compare_json_datasets

    Workflow:
    1. Detection: Gather diagnostics → Identify root cause
    2. Remediation: Determine approach → Execute → Verify
    3. JSON: Load → Analyze → Recommend

    JSON Usage:
    • add_json_data("path.json") - Load data
    • analyze_json_data_with_llm(type, focus) - Analyze
    • get_recommendations_from_json(tower, metric) - Get recommendations
    • compare_json_datasets(file1, file2) - Compare

    Analysis Focus:
    - Energy optimization (30-40% savings)
    - Congestion risks and mitigation
    - Network health priorities
    - Actionable recommendations

    Keep responses concise and actionable. Prioritize stability.
    """,
    sub_agents=[regional_coordinator],
    tools=[
        check_system_health,
        get_agent_status,
        restart_agent,
        redeploy_agent,
        reroute_traffic,
        generate_health_dashboard,
        get_system_metrics,
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
    max_iterations=100,  # Run up to 100 monitoring cycles
)

# Export the principal agent as root_agent for ADK
root_agent = principal_agent
