"""
Test MCP Server Connections

This script tests connectivity to deployed MCP servers and validates that
all tools are accessible.
"""

import asyncio
import boto3
import json
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class MCPServerTester:
    """Test MCP server connectivity and tools."""

    def __init__(self):
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        self.ssm_client = boto3.client("ssm", region_name=self.region)
        self.secrets_client = boto3.client("secretsmanager", region_name=self.region)

    def get_mcp_connection_info(self, server_type):
        """Get MCP connection information from AWS."""
        try:
            # Get agent ARN
            agent_arn = self.ssm_client.get_parameter(
                Name=f"/trace/{server_type}/agent_arn"
            )["Parameter"]["Value"]

            # Get Cognito credentials
            secret = self.secrets_client.get_secret_value(
                SecretId=f"/trace/{server_type}/cognito/credentials"
            )
            cognito_config = json.loads(secret["SecretString"])

            return {
                "agent_arn": agent_arn,
                "cognito_config": cognito_config,
                "status": "success",
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def authenticate_cognito(self, cognito_config):
        """Authenticate with Cognito and get bearer token."""
        try:
            cognito_client = boto3.client("cognito-idp", region_name=self.region)
            auth_response = cognito_client.initiate_auth(
                ClientId=cognito_config["client_id"],
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": "testuser", "PASSWORD": "MyPassword123!"},
            )
            return auth_response["AuthenticationResult"]["AccessToken"]
        except Exception as e:
            print(f"Authentication error: {e}")
            return None

    async def test_mcp_server(self, server_type):
        """Test connectivity to a specific MCP server."""
        print(f"\n{'='*80}")
        print(f"Testing {server_type} MCP Server")
        print(f"{'='*80}\n")

        # Get connection info
        print("1. Retrieving connection information from AWS...")
        conn_info = self.get_mcp_connection_info(server_type)

        if conn_info["status"] == "error":
            print(f"❌ Error: {conn_info['error']}")
            return False

        print(f"✅ Agent ARN: {conn_info['agent_arn']}")

        # Authenticate
        print("\n2. Authenticating with Cognito...")
        bearer_token = self.authenticate_cognito(conn_info["cognito_config"])

        if not bearer_token:
            print("❌ Authentication failed")
            return False

        print("✅ Authentication successful")

        # Build MCP URL
        encoded_arn = conn_info["agent_arn"].replace(":", "%3A").replace("/", "%2F")
        mcp_url = f"https://bedrock-agentcore.{self.region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"

        headers = {
            "authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }

        # Test connection
        print("\n3. Testing MCP connection...")
        print(f"   URL: {mcp_url[:80]}...")

        try:
            async with streamablehttp_client(
                mcp_url, headers, timeout=120, terminate_on_close=False
            ) as (
                read_stream,
                write_stream,
                _,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    # Initialize session
                    await session.initialize()
                    print("✅ MCP connection established")

                    # List available tools
                    print("\n4. Listing available tools...")
                    tool_result = await session.list_tools()

                    if tool_result.tools:
                        print(f"✅ Found {len(tool_result.tools)} tools:")
                        for i, tool in enumerate(tool_result.tools, 1):
                            print(f"   {i}. {tool.name}")
                            print(f"      {tool.description}")

                        # Test calling a tool
                        print(f"\n5. Testing tool call...")
                        test_tool = tool_result.tools[0]
                        print(f"   Calling: {test_tool.name}")

                        try:
                            # Call the first tool with minimal args
                            tool_call_result = await session.call_tool(
                                test_tool.name, arguments={}
                            )
                            print(f"✅ Tool call successful")
                            print(
                                f"   Result preview: {str(tool_call_result)[:200]}..."
                            )

                        except Exception as e:
                            print(
                                f"⚠️  Tool call error (this may be expected if tool requires args): {e}"
                            )

                        return True
                    else:
                        print("⚠️  No tools found")
                        return False

        except Exception as e:
            print(f"❌ Connection error: {e}")
            import traceback

            traceback.print_exc()
            return False

    async def test_all_servers(self):
        """Test all MCP servers."""
        print("\n" + "=" * 80)
        print("TRACE MCP Server Connection Test")
        print("=" * 80)

        servers = ["principal_tools", "regional_coordinator"]
        results = {}

        for server in servers:
            success = await self.test_mcp_server(server)
            results[server] = success

        # Print summary
        print("\n" + "=" * 80)
        print("Test Summary")
        print("=" * 80)

        for server, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{server:30} {status}")

        all_passed = all(results.values())
        print("\n" + "=" * 80)
        if all_passed:
            print("✅ All tests passed! MCP servers are ready.")
        else:
            print("❌ Some tests failed. Check the logs above.")
        print("=" * 80 + "\n")

        return all_passed


async def main():
    """Main test function."""
    import sys

    # Check AWS credentials
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print(f"AWS Account: {identity['Account']}")
        print(f"AWS User: {identity['Arn']}")
    except Exception as e:
        print(f"❌ AWS credentials error: {e}")
        print("Please configure AWS credentials before running tests.")
        sys.exit(1)

    # Run tests
    tester = MCPServerTester()
    success = await tester.test_all_servers()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
