"""
TRACE Principal Agent - AWS Bedrock AgentCore Integration
Using Strands SDK with MCP for tool integration

This is the AWS-deployed version of the Principal Agent that runs on
Amazon Bedrock AgentCore and uses MCP servers for tool integration.
"""

from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import boto3
import json
import os


class TRACEPrincipalAgent:
    """
    Principal Agent for TRACE system deployed on AWS Bedrock AgentCore.

    This agent:
    - Monitors all parent and child agents
    - Executes self-healing workflows
    - Provides health dashboards
    - Analyzes JSON telemetry data
    """

    def __init__(self):
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        self.ssm_client = boto3.client("ssm", region_name=self.region)
        self.secrets_client = boto3.client("secretsmanager", region_name=self.region)

        # Initialize MCP clients for tool servers
        self.principal_tools_mcp = self._get_mcp_client("principal_tools")
        self.regional_coordinator_mcp = self._get_mcp_client("regional_coordinator")

        # Initialize Bedrock model
        model_id = os.environ.get(
            "BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        )
        self.model = BedrockModel(model_id=model_id)

        # Create agent with MCP tools
        self.agent = self._create_agent()

    def _get_mcp_client(self, server_type):
        """Get MCP client for a specific tool server."""

        def create_client():
            try:
                # Get agent ARN and client ID from SSM
                agent_arn = self.ssm_client.get_parameter(
                    Name=f"/trace/{server_type}/agent_arn"
                )["Parameter"]["Value"]

                # Get Cognito credentials from Secrets Manager
                secret = self.secrets_client.get_secret_value(
                    SecretId=f"/trace/{server_type}/cognito/credentials"
                )
                cognito_config = json.loads(secret["SecretString"])

                # Authenticate with Cognito
                cognito_client = boto3.client("cognito-idp", region_name=self.region)
                auth_response = cognito_client.initiate_auth(
                    ClientId=cognito_config["client_id"],
                    AuthFlow="USER_PASSWORD_AUTH",
                    AuthParameters={
                        "USERNAME": "testuser",
                        "PASSWORD": "MyPassword123!",
                    },
                )
                bearer_token = auth_response["AuthenticationResult"]["AccessToken"]

                # Encode ARN for URL
                encoded_arn = agent_arn.replace(":", "%3A").replace("/", "%2F")
                mcp_url = f"https://bedrock-agentcore.{self.region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"

                headers = {
                    "authorization": f"Bearer {bearer_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                }

                return streamablehttp_client(
                    mcp_url, headers, timeout=120, terminate_on_close=False
                )

            except Exception as e:
                print(f"Warning: Could not connect to MCP server {server_type}: {e}")
                # Return None to continue without this MCP server
                return None

        return MCPClient(create_client)

    def _create_agent(self):
        """Create the Strands agent with MCP tools."""

        # Collect all tools from MCP servers
        all_tools = []

        # Get tools from principal_tools MCP server
        try:
            with self.principal_tools_mcp:
                principal_tools = self.principal_tools_mcp.list_tools_sync()
                all_tools.extend(principal_tools)
                print(
                    f"Loaded {len(principal_tools)} tools from principal_tools MCP server"
                )
        except Exception as e:
            print(f"Warning: Could not load principal tools: {e}")

        # Get tools from regional_coordinator MCP server
        try:
            with self.regional_coordinator_mcp:
                coordinator_tools = self.regional_coordinator_mcp.list_tools_sync()
                all_tools.extend(coordinator_tools)
                print(
                    f"Loaded {len(coordinator_tools)} tools from regional_coordinator MCP server"
                )
        except Exception as e:
            print(f"Warning: Could not load regional coordinator tools: {e}")

        # Create agent with comprehensive instructions
        agent = Agent(
            model=self.model,
            tools=all_tools,
            system_prompt="""You are the Principal Agent for TRACE (Traffic & Resource Agentic Control Engine) - 
a global orchestrator and health guardian for telecom network optimization.

MISSION:
- Cut mobile-tower energy use by 30-40% during low demand
- Prevent congestion during traffic surges
- Provide autonomous self-healing
- Ensure 99.99% system uptime

ARCHITECTURE:
You are at the top of a hierarchical multi-agent system:
1. Principal Agent (YOU) - Global orchestrator and self-healing
2. Parent Agents (Regional Coordinators) - Manage regional tower clusters
3. Edge Child Agents - Specialized functions (monitoring, prediction, decision, action, learning)

RESPONSIBILITIES:
🔍 MONITORING & DETECTION:
- Monitor all Parent and Child agents continuously
- Detect anomalies, infrastructure failures, cascading faults
- Track system health via telemetry + A2A heartbeats

🔧 SELF-HEALING & REMEDIATION:
- Execute automated remediations: restart, redeploy, reroute
- Apply policy-driven rollback and restoration
- Escalate to human operators when needed

📊 INSIGHTS & ANALYSIS:
- Analyze JSON telemetry data for network optimization
- Generate health dashboards and reports
- Provide actionable recommendations

🎯 COORDINATION:
- Coordinate regional coordinators for energy optimization
- Manage congestion workflows across multiple regions
- Balance load proactively to prevent overload

AVAILABLE TOOLS:
From principal_tools MCP server:
- check_system_health: Monitor overall system health
- get_agent_status: Check status of specific agents
- restart_agent: Restart failed agents
- redeploy_agent: Redeploy agents with new configuration
- reroute_traffic: Reroute traffic during failures
- generate_health_dashboard: Create visual health dashboard
- get_system_metrics: Get comprehensive system metrics
- add_json_data: Load JSON telemetry data
- analyze_json_data_with_llm: AI-powered data analysis
- get_recommendations_from_json: Get specific recommendations
- compare_json_datasets: Compare data over time

From regional_coordinator MCP server:
- aggregate_telemetry: Aggregate data from multiple towers
- get_regional_metrics: Get regional performance metrics
- enforce_policy: Enforce regional policies
- validate_action: Validate proposed actions
- balance_load: Balance load across towers
- get_tower_status: Get tower-specific status
- Regional coordinator sub-agent: Delegate to regional coordinator

WORKFLOWS:
1. ENERGY OPTIMIZATION (Sequential):
   Monitor → Predict → Decide → Act → Learn
   Target: 30-40% energy reduction during low-traffic hours

2. CONGESTION MANAGEMENT (Parallel + Sequential):
   Monitor all towers → Detect surge → Balance load → Activate backups
   Target: Zero dropped calls during peak events

3. SELF-HEALING (Loop):
   Continuous monitoring → Detect failure → Diagnose → Remediate → Verify
   Target: <5 minute recovery time

JSON DATA ANALYSIS:
When users provide JSON data:
1. Use add_json_data() to load and validate
2. Use analyze_json_data_with_llm() for comprehensive AI analysis
3. Use get_recommendations_from_json() for specific recommendations
4. Use compare_json_datasets() to track changes

ANALYSIS FOCUS:
- Energy optimization opportunities (30-40% savings)
- Congestion risks and mitigation strategies
- Network health priorities
- Actionable, data-driven recommendations

COMMUNICATION STYLE:
- Be concise and actionable
- Prioritize stability and safety
- Provide clear reasoning for decisions
- Escalate critical issues appropriately
- Use emojis for visual clarity: 🔋(energy) ⚠️(congestion) 🔴(errors) ✅(success)

SAFETY CONSTRAINTS:
- Always validate actions before execution
- Maintain service quality while optimizing
- Never compromise network reliability
- Provide rollback mechanisms
- Keep human operators informed

Remember: You are the global orchestrator. Your decisions affect the entire TRACE system.
Think strategically, act decisively, and prioritize network stability.""",
        )

        return agent

    def run(self, user_input: str):
        """Run the agent with user input."""
        with self.principal_tools_mcp, self.regional_coordinator_mcp:
            result = self.agent(user_input)
            return result.message

    def run_interactive(self):
        """Run interactive chat loop."""
        print("=" * 80)
        print("TRACE Principal Agent - AWS Bedrock AgentCore")
        print("Global Orchestrator for Telecom Network Optimization")
        print("=" * 80)
        print("\nAvailable commands:")
        print("  'help' - Show available capabilities")
        print("  'health' - Check system health")
        print("  'quit' - Exit")
        print("\n" + "=" * 80 + "\n")

        with self.principal_tools_mcp, self.regional_coordinator_mcp:
            while True:
                try:
                    user_input = input("\n🎯 You: ")

                    if user_input.lower() in ["quit", "exit", "q"]:
                        print("\n👋 Goodbye! TRACE Principal Agent signing off.\n")
                        break

                    if user_input.lower() == "help":
                        print(
                            """
📚 TRACE Principal Agent Capabilities:

🔍 SYSTEM MONITORING:
   - Check system health across all agents
   - Monitor specific agent status
   - View real-time metrics and KPIs

🔧 SELF-HEALING:
   - Restart failed agents automatically
   - Redeploy agents with updated config
   - Reroute traffic during failures
   - Execute recovery workflows

📊 ANALYTICS & INSIGHTS:
   - Load and analyze JSON telemetry data
   - Generate health dashboards
   - Get AI-powered recommendations
   - Compare datasets over time

⚡ ENERGY OPTIMIZATION:
   - Identify energy saving opportunities
   - Coordinate TRX shutdowns
   - Target 30-40% energy reduction

🚦 CONGESTION MANAGEMENT:
   - Predict traffic surges
   - Balance load proactively
   - Prevent network overload

Example queries:
- "Check overall system health"
- "Load data/trace_reduced_20.json and analyze"
- "Analyze energy optimization opportunities"
- "Predict congestion for next 4 hours"
- "Show me the health dashboard"
                        """
                        )
                        continue

                    if not user_input.strip():
                        continue

                    print("\n🤖 Principal Agent:")
                    result = self.agent(user_input)
                    print(result.message)

                except KeyboardInterrupt:
                    print("\n\n👋 Interrupted. Goodbye!\n")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}\n")


def main():
    """Main entry point for AWS deployment."""
    import sys

    # Initialize agent
    print("Initializing TRACE Principal Agent on AWS Bedrock AgentCore...")
    agent = TRACEPrincipalAgent()

    # Check if running in interactive mode or with arguments
    if len(sys.argv) > 1:
        # Process command line argument
        user_input = " ".join(sys.argv[1:])
        result = agent.run(user_input)
        print(result)
    else:
        # Interactive mode
        agent.run_interactive()


if __name__ == "__main__":
    main()
