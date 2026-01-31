# TRACE AWS Production Implementation

## Overview

This is the **production-ready** AWS implementation of TRACE (Traffic & Resource Agentic Control Engine). 

### Key Improvements Over Previous Implementation:
✅ **Queries REAL data** from AWS Timestream and DynamoDB (no more `random.uniform()`)  
✅ **Uses Amazon Bedrock** (Claude 3.5) instead of Google Gemini  
✅ **Implements actual remediation** via IoT Core, ECS, and Lambda  
✅ **Includes production workflows** with Step Functions  
✅ **Provides real-time streaming** via Kinesis and WebSocket API  
✅ **MCP Servers integrated** with AWS Timestream for real telemetry  

## Migration from Google to AWS

| Google Service | AWS Replacement | Status |
|---------------|-----------------|--------|
| Gemini AI | Amazon Bedrock (Claude 3.5/Titan) | ✅ Implemented |
| Google ADK | Amazon Bedrock Agents | ✅ Implemented |
| Local Data | AWS Timestream + DynamoDB | ✅ Implemented |
| Local Analysis | SageMaker Inference + Bedrock | ✅ Implemented |
| WebSocket Server | API Gateway WebSocket + Lambda | ✅ Implemented |
| Random Values | Pattern-based + Real Timestream Data | ✅ Fixed |

## Files Modified (No More Random Values)

The following files have been updated to use **REAL AWS data** instead of random values:

### MCP Servers
- `AWS/mcp_servers/telemetry_server.py` - Now queries Timestream, falls back to pattern-based data
- `AWS/mcp_servers/energy_server.py` - Uses real traffic data from Timestream
- `AWS/mcp_servers/policy_server.py` - Queries DynamoDB for policies
- `AWS/mcp_servers/tower_config_server.py` - Reads from DynamoDB TowerConfig table

### Lambda Functions
- `AWS/lambda/mcp_tools_lambda.py` - Queries Timestream and DynamoDB
- `AWS/aws-production/03-lambda-tools/health_monitor/handler.py` - Already uses Timestream
- `AWS/aws-production/03-lambda-tools/remediation/handler.py` - Uses real AWS services
- `AWS/aws-production/03-lambda-tools/analytics/handler.py` - Queries Timestream

### Client Integration
- `client/server/bedrock_service.py` - NEW: AWS Bedrock integration for dashboard
- `client/server/dashboard_server.py` - Updated to support both Gemini and Bedrock

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
export AWS_REGION=us-east-1
export TRACE_ENV=production
export TRACE_AI_BACKEND=bedrock  # or 'gemini' for local testing

# 3. Verify AWS integration
python scripts/verify_aws_integration.py

# 4. Deploy infrastructure (if not already deployed)
python 01-infrastructure/deploy.py

# 5. Start telemetry simulator
python scripts/telemetry_simulator.py --continuous

# 6. Deploy Bedrock agents
python 04-bedrock-agents/deploy.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AWS Production Architecture                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐        │
│  │   IoT Core       │────▶│   Kinesis Data   │────▶│   Lambda         │        │
│  │   (Telemetry)    │     │   Streams        │     │   (Processor)    │        │
│  └──────────────────┘     └──────────────────┘     └────────┬─────────┘        │
│                                                              │                   │
│                           ┌──────────────────────────────────┼──────────────┐   │
│                           ▼                                  ▼              │   │
│  ┌──────────────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────┐     │   │
│  │   Timestream     │  │  DynamoDB   │  │  CloudWatch  │  │    S3    │     │   │
│  │   (Time-Series)  │  │  (Config)   │  │  (Metrics)   │  │  (Store) │     │   │
│  └────────┬─────────┘  └──────┬──────┘  └──────────────┘  └──────────┘     │   │
│           │                   │                                             │   │
│           └───────────────────┼─────────────────────────────────────────────┘   │
│                               │                                                  │
│  ┌────────────────────────────▼─────────────────────────────────────────────┐   │
│  │                       BEDROCK AGENTS                                      │   │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   │   │
│  │  │  Principal  │──▶│  Regional   │──▶│    Edge     │──▶│   Action    │   │   │
│  │  │   Agent     │   │ Coordinator │   │   Agents    │   │   Groups    │   │   │
│  │  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                               │                                                  │
│  ┌────────────────────────────▼─────────────────────────────────────────────┐   │
│  │                         MCP SERVERS                                       │   │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   │   │
│  │  │ Telemetry   │   │   Energy    │   │   Policy    │   │   Tower     │   │   │
│  │  │   Server    │   │   Server    │   │   Server    │   │  Config     │   │   │
│  │  │ (Timestream)│   │ (Timestream)│   │ (DynamoDB)  │   │  Server     │   │   │
│  │  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                               │                                                  │
│                               ▼                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                       STEP FUNCTIONS                                      │   │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────┐     │   │
│  │  │  Self-Healing   │   │     Energy      │   │    Congestion       │     │   │
│  │  │    Workflow     │   │   Optimization  │   │    Management       │     │   │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────────┘     │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                               │                                                  │
│                               ▼                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                          API LAYER                                        │   │
│  │  ┌────────────────────┐   ┌───────────────────────┐                      │   │
│  │  │   API Gateway      │   │   API Gateway         │                      │   │
│  │  │   (REST)           │   │   (WebSocket)         │                      │   │
│  │  └────────────────────┘   └───────────────────────┘                      │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                               │                                                  │
│                               ▼                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                        FRONTEND                                           │   │
│  │  ┌────────────────────┐   ┌───────────────────────┐                      │   │
│  │  │   CloudFront       │   │   Amplify Hosting     │                      │   │
│  │  │   (CDN)            │   │   (React Dashboard)   │                      │   │
│  │  └────────────────────┘   └───────────────────────┘                      │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
aws-production/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── config.py                    # Global configuration
│
├── 01-infrastructure/           # CloudFormation/CDK templates
│   └── deploy.py               # Creates DynamoDB, Timestream, S3, IAM
│
├── 02-data-pipeline/            # Real-time data ingestion
│   └── telemetry_processor/    # Lambda that processes Kinesis → Timestream
│
├── 03-lambda-tools/             # Lambda functions with real AWS data
│   ├── health_monitor/         # Queries Timestream for health metrics
│   ├── remediation/            # Executes real remediations via IoT/ECS
│   ├── analytics/              # Historical analysis from Timestream
│   ├── agent_api/              # Agent communication endpoints
│   └── websocket/              # WebSocket connection handler
│
├── 04-bedrock-agents/           # Bedrock agent configurations
│   └── deploy.py               # Creates Principal & Regional agents
│
├── 05-step-functions/           # Workflow definitions
│   ├── self-healing-workflow.json
│   └── energy-optimization-workflow.json
│
├── 06-api-layer/                # API Gateway configurations
│   └── deploy.py               # REST & WebSocket APIs
│
├── 07-frontend/                 # AWS-integrated frontend config
│   └── aws-config.js           # Frontend AWS endpoints
│
├── services/                    # Shared service modules
│   └── bedrock_service.py      # Bedrock AI service wrapper
│
└── scripts/                     # Deployment and utility scripts
    ├── deploy_all.py           # Master deployment script
    ├── telemetry_simulator.py  # Generates realistic telemetry
    └── verify_aws_integration.py # Verifies all AWS components
```

## Environment Variables

```bash
# Required
export AWS_REGION=us-east-1
export TRACE_ENV=production

# Optional
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
export BEDROCK_FAST_MODEL=anthropic.claude-3-haiku-20240307-v1:0
export TIMESTREAM_DATABASE=TRACE-Telemetry-production
export TOWER_CONFIG_TABLE=TRACE-TowerConfig-production
export TRACE_AI_BACKEND=bedrock  # or 'gemini' or 'auto'
```

## Verification

Run the integration verification script to ensure all components are working:

```bash
python scripts/verify_aws_integration.py
```

This will check:
- ✅ AWS credentials
- ✅ DynamoDB tables
- ✅ Timestream database and tables
- ✅ Timestream has recent data
- ✅ Lambda functions deployed
- ✅ Step Functions state machines
- ✅ Bedrock model access
- ✅ Bedrock agents configured

## Deployment

```bash
# 1. Configure AWS credentials
aws configure

# 2. Set environment variables
export TRACE_ENV=production
export AWS_REGION=us-east-1

# 3. Run full deployment
cd aws-production
python scripts/deploy_all.py

# 4. Start telemetry simulator (in separate terminal)
python scripts/telemetry_simulator.py --continuous
```

## Troubleshooting

### No data in Timestream
Run the telemetry simulator:
```bash
python scripts/telemetry_simulator.py --continuous
```

### Bedrock access denied
Enable Claude models in AWS Console:
1. Go to Amazon Bedrock console
2. Click "Model access"
3. Enable Claude 3.5 Sonnet and Claude 3 Haiku

### MCP servers not connecting
Ensure environment variables are set:
```bash
export TRACE_ENV=production
export AWS_REGION=us-east-1
```
