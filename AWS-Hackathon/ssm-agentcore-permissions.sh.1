#!/bin/bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Set variables
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region || echo "us-east-1")

# Accept agent role name as argument, default to oran_agent
AGENT_NAME="${1:-oran_agent}"
AGENT_ROLE="agentcore-${AGENT_NAME}-role"

echo "Adding permissions to role: $AGENT_ROLE"

# Add SSM permissions for MCP parameter access
aws iam put-role-policy --role-name "$AGENT_ROLE" --policy-name agent-ssm-access --policy-document "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [{
    \"Effect\": \"Allow\",
    \"Action\": [\"ssm:GetParameter\", \"ssm:GetParameters\"],
    \"Resource\": [
      \"arn:aws:ssm:${REGION}:${ACCOUNT_ID}:parameter/mcp_server/r1/runtime/*\",
      \"arn:aws:ssm:${REGION}:${ACCOUNT_ID}:parameter/mcp_server/o2/runtime/*\"
    ]
  }]
}"

# Add AgentCore memory permissions
aws iam put-role-policy --role-name "$AGENT_ROLE" --policy-name agent-memory-access --policy-document "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [{
    \"Effect\": \"Allow\",
    \"Action\": [
      \"bedrock-agentcore:CreateMemory\",
      \"bedrock-agentcore:GetMemory\",
      \"bedrock-agentcore:ListMemories\",
      \"bedrock-agentcore:DeleteMemory\",
      \"bedrock-agentcore:CreateEvent\",
      \"bedrock-agentcore:GetLastKTurns\",
      \"bedrock-agentcore:ListEvents\"
    ],
    \"Resource\": \"*\"
  }]
}"

echo "✅ Permissions added successfully"