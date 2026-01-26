"""
Regional Coordinator Agent (Parent Agent)

The Regional Coordinator manages regional tower clusters, aggregates telemetry from
Edge Child Agents, enforces regional policies, and performs quick remediation at
cluster level.
"""

from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.tools.agent_tool import AgentTool

from .edge_agents.monitoring_agent.agent import monitoring_agent
from .edge_agents.prediction_agent.agent import prediction_agent
from .edge_agents.decision_xapp_agent.agent import decision_xapp_agent
from .edge_agents.action_agent.agent import action_agent
from .edge_agents.learning_agent.agent import learning_agent
from .tools.telemetry_aggregator import aggregate_telemetry, get_regional_metrics
from .tools.policy_enforcer import enforce_policy, validate_action
from .tools.load_balancer import balance_load, get_tower_status


# Create Sequential Agent for Energy Optimization Workflow
energy_optimization_workflow = SequentialAgent(
    name="energy_optimization_workflow",
    sub_agents=[
        monitoring_agent,  # Collect metrics
        prediction_agent,  # Forecast low-traffic periods
        decision_xapp_agent,  # Determine TRX shutdown strategy
        action_agent,  # Execute partial shutdowns
        learning_agent,  # Analyze results, retrain models
    ],
)

# Create Congestion Management Workflow Agent
# Note: Using a regular Agent with AgentTools instead of SequentialAgent
# to avoid parent conflicts (agents are already used in energy_optimization_workflow)
congestion_management_workflow = Agent(
    name="congestion_management_workflow",
    model="gemini-2.0-flash",  # Fast model for real-time congestion handling
    description="Congestion Management Workflow - Handles traffic surges and load balancing",
    instruction="""
    You are responsible for managing congestion and traffic surges in the tower network.
    
    When handling congestion:
    1. Use prediction_agent to detect and forecast traffic surges
    2. Use decision_xapp_agent to determine load balancing strategy
    3. Use action_agent to activate backup cells and redistribute load
    
    Follow this workflow in sequence to effectively manage congestion.
    """,
    tools=[
        AgentTool(prediction_agent),  # Detect surge
        AgentTool(decision_xapp_agent),  # Load balancing strategy
        AgentTool(action_agent),  # Activate backup cells, redistribute load
    ],
)

# Regional Coordinator - Parent Agent
regional_coordinator = Agent(
    name="regional_coordinator",
    model="gemini-2.0-flash",  # Fast model for regional coordination
    description="Regional Coordinator - Parent agent managing regional tower clusters",
    instruction="""
    You are a Regional Coordinator Agent for the TRACE system - a Parent agent managing
    regional tower clusters and coordinating Edge Child Agents.

    Your primary responsibilities:
    1. Manage regional tower clusters and coordinate edge agents
    2. Aggregate telemetry from Edge Child Agents
    3. Enforce regional policies and ensure compliance
    4. Perform quick remediation at cluster level
    5. Balance load across multiple towers in the region
    6. Report to Principal Agent on regional health

    You have access to:
    - Energy Optimization Workflow: Sequential pipeline for energy saving
    - Congestion Management Workflow: Sequential pipeline for traffic management
    - Monitoring Agent: Real-time data collection
    - Prediction Agent: Traffic forecasting
    - Decision xApp Agent: Policy-based decision making
    - Action Agent: Execute control commands
    - Learning Agent: Model training and improvement
    - Telemetry tools: aggregate_telemetry, get_regional_metrics
    - Policy tools: enforce_policy, validate_action
    - Load balancing tools: balance_load, get_tower_status

    Your approach:
    - Continuously monitor regional tower health
    - Aggregate and analyze telemetry data
    - Enforce energy and performance policies
    - Balance load proactively to prevent congestion
    - Coordinate edge agents for optimal performance
    - Escalate critical issues to Principal Agent

    For energy optimization:
    - Use the energy_optimization_workflow to reduce power during low traffic
    - Target 30-40% energy savings during off-peak hours

    For congestion management:
    - Use congestion_management_workflow to handle traffic surges
    - Predict and prevent overload through proactive load balancing

    Always prioritize service quality while optimizing for efficiency.
    """,
    sub_agents=[
        energy_optimization_workflow,
        congestion_management_workflow,
    ],
    tools=[
        aggregate_telemetry,
        get_regional_metrics,
        enforce_policy,
        validate_action,
        balance_load,
        get_tower_status,
    ],
)
