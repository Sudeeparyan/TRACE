"""
Deploy TRACE MCP Servers to AWS Bedrock AgentCore

This script deploys both MCP servers:
1. Principal Tools Server - Health, remediation, dashboard, JSON tools
2. Regional Coordinator Server - Regional coordination and edge agent tools
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "AWS-Hackathon"))

import logging

logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session
import time
import boto3
import json
import argparse
from cognito_utils import create_agentcore_role, setup_cognito_user_pool


def deploy_mcp_server(server_name, server_file, port=8000):
    """
    Deploy a single MCP server to AWS Bedrock AgentCore.

    Args:
        server_name: Name of the server (e.g., 'principal_tools', 'regional_coordinator')
        server_file: Path to the server file
        port: Port number for the server

    Returns:
        Deployment result with ARN and configuration
    """
    print(f"\n{'='*80}")
    print(f"Deploying {server_name} MCP Server to AWS Bedrock AgentCore")
    print(f"{'='*80}\n")

    boto_session = Session()
    region = boto_session.region_name

    # Check if server file exists
    if not os.path.exists(server_file):
        raise FileNotFoundError(f"Server file not found: {server_file}")

    # Create IAM role for AgentCore
    print(f"Creating IAM role for {server_name}...")
    agentcore_role = create_agentcore_role(agent_name=server_name)
    print(f"✅ IAM role created: {agentcore_role['Role']['Arn']}")

    # Set up Cognito user pool for authentication
    print(f"\nSetting up Cognito authentication...")
    cognito_config = setup_cognito_user_pool()
    print(f"✅ Cognito configured:")
    print(f"   Pool ID: {cognito_config['pool_id']}")
    print(f"   Client ID: {cognito_config['client_id']}")

    # Configure authentication
    auth_config = {
        "customJWTAuthorizer": {
            "allowedClients": [cognito_config["client_id"]],
            "discoveryUrl": cognito_config["discovery_url"],
        }
    }

    # Create requirements.txt for the server
    requirements_file = os.path.join(os.path.dirname(server_file), "requirements.txt")
    if not os.path.exists(requirements_file):
        print(f"\nCreating requirements.txt for {server_name}...")
        with open(requirements_file, "w") as f:
            f.write(
                """mcp>=1.0.0
fastmcp>=0.1.0
boto3>=1.35.50
"""
            )
        print(f"✅ Requirements file created")

    # Configure AgentCore runtime
    print(f"\nConfiguring AgentCore runtime...")
    agentcore_runtime = Runtime()
    agentcore_runtime.configure(
        entrypoint=server_file,
        execution_role=agentcore_role["Role"]["Arn"],
        auto_create_ecr=True,
        requirements_file=requirements_file,
        region=region,
        authorizer_configuration=auth_config,
        agent_name=server_name,
    )

    # Launch the runtime
    print(f"\nLaunching AgentCore runtime...")
    print("This may take several minutes...")
    launch_result = agentcore_runtime.launch()

    print(f"\n✅ {server_name} deployed successfully!")
    print(f"   Agent ARN: {launch_result.agent_arn}")

    # Store configuration in AWS Systems Manager Parameter Store
    print(f"\nStoring configuration in AWS Systems Manager...")
    ssm_client = boto3.client("ssm", region_name=region)
    secrets_client = boto3.client("secretsmanager", region_name=region)

    # Store Cognito credentials in Secrets Manager
    try:
        secrets_client.create_secret(
            Name=f"/trace/{server_name}/cognito/credentials",
            Description=f"Cognito credentials for {server_name} MCP server",
            SecretString=json.dumps(cognito_config),
        )
        print(f"✅ Cognito credentials stored in Secrets Manager")
    except secrets_client.exceptions.ResourceExistsException:
        secrets_client.update_secret(
            SecretId=f"/trace/{server_name}/cognito/credentials",
            SecretString=json.dumps(cognito_config),
        )
        print(f"✅ Cognito credentials updated in Secrets Manager")

    # Store agent ARN in Parameter Store
    ssm_client.put_parameter(
        Name=f"/trace/{server_name}/agent_arn",
        Value=launch_result.agent_arn,
        Type="String",
        Description=f"Agent ARN for {server_name} MCP server",
        Overwrite=True,
    )

    ssm_client.put_parameter(
        Name=f"/trace/{server_name}/client_id",
        Value=cognito_config["client_id"],
        Type="String",
        Description=f"Cognito client ID for {server_name}",
        Overwrite=True,
    )

    print(f"✅ Configuration stored in Parameter Store")

    return {
        "server_name": server_name,
        "agent_arn": launch_result.agent_arn,
        "cognito_config": cognito_config,
        "region": region,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Deploy TRACE MCP Servers to AWS Bedrock AgentCore"
    )
    parser.add_argument(
        "--server",
        choices=["principal", "regional", "all"],
        default="all",
        help="Which server to deploy (default: all)",
    )
    parser.add_argument(
        "--skip-confirmation", action="store_true", help="Skip deployment confirmation"
    )
    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("TRACE MCP Server Deployment to AWS Bedrock AgentCore")
    print("=" * 80)

    # Get AWS region
    boto_session = Session()
    region = boto_session.region_name
    account_id = boto3.client("sts").get_caller_identity()["Account"]

    print(f"\nAWS Configuration:")
    print(f"  Region: {region}")
    print(f"  Account ID: {account_id}")

    # Determine which servers to deploy
    servers_to_deploy = []

    if args.server in ["principal", "all"]:
        servers_to_deploy.append(
            {
                "name": "principal_tools",
                "file": os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "mcp_servers",
                    "principal_tools_server.py",
                ),
                "port": 8000,
            }
        )

    if args.server in ["regional", "all"]:
        servers_to_deploy.append(
            {
                "name": "regional_coordinator",
                "file": os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "mcp_servers",
                    "regional_coordinator_server.py",
                ),
                "port": 8001,
            }
        )

    print(f"\nServers to deploy:")
    for server in servers_to_deploy:
        print(f"  - {server['name']} ({server['file']})")

    if not args.skip_confirmation:
        confirm = input("\nProceed with deployment? (yes/no): ")
        if confirm.lower() not in ["yes", "y"]:
            print("Deployment cancelled.")
            return

    # Deploy servers
    results = []
    for server in servers_to_deploy:
        try:
            result = deploy_mcp_server(
                server_name=server["name"],
                server_file=server["file"],
                port=server["port"],
            )
            results.append(result)
            print(f"\n✅ {server['name']} deployed successfully!\n")
        except Exception as e:
            print(f"\n❌ Error deploying {server['name']}: {e}")
            import traceback

            traceback.print_exc()

    # Print summary
    print("\n" + "=" * 80)
    print("Deployment Summary")
    print("=" * 80)

    for result in results:
        print(f"\n{result['server_name']}:")
        print(f"  Agent ARN: {result['agent_arn']}")
        print(f"  Region: {result['region']}")
        print(f"  Parameter Store: /trace/{result['server_name']}/*")
        print(f"  Secrets Manager: /trace/{result['server_name']}/cognito/credentials")

    print(f"\n{'='*80}")
    print("Next Steps:")
    print("1. Test the MCP servers with: python test_mcp_connection.py")
    print("2. Deploy the principal agent with: python deploy_principal_agent.py")
    print("3. Run interactive agent: python ../principal_agent_aws.py")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
