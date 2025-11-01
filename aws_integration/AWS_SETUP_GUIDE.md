# TRACE AWS Integration - Complete Setup Guide

## 📋 Overview

This guide will walk you through deploying the TRACE (Traffic & Resource Agentic Control Engine) system to AWS Bedrock AgentCore with full MCP (Model Context Protocol) integration.

**Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│  AWS Bedrock AgentCore (Strands SDK)                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Principal Agent (principal_agent_aws.py)          │    │
│  │  - Global orchestrator                             │    │
│  │  - Self-healing workflows                          │    │
│  │  - Energy optimization (30-40% savings)            │    │
│  │  - Congestion management                           │    │
│  └────────────────────────────────────────────────────┘    │
│           │                                                  │
│           ├─── MCP Protocol ───┐                            │
│           │                     │                            │
│           ▼                     ▼                            │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Principal Tools  │  │ Regional Coord   │                │
│  │ MCP Server       │  │ MCP Server       │                │
│  │ - Health check   │  │ - Edge agents    │                │
│  │ - Remediation    │  │ - Telemetry      │                │
│  │ - Dashboard      │  │ - Load balancing │                │
│  │ - JSON analysis  │  │ - Policy enforce │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
           │                     │
           └─────────┬───────────┘
                     ▼
         ┌──────────────────────┐
         │  AWS Services        │
         │  - SSM Parameter     │
         │  - Secrets Manager   │
         │  - Cognito           │
         │  - IAM               │
         │  - CloudWatch        │
         └──────────────────────┘
```

---

## 🚀 Quick Start (5 Steps)

### Prerequisites
- AWS Account with admin access
- Python 3.9+
- AWS CLI configured
- AWS Credentials (configure in `.env` file):
  - AWS_ACCESS_KEY_ID=your-access-key-id
  - AWS_SECRET_ACCESS_KEY=your-secret-access-key
  - AWS_REGION=us-east-1

### Step 1: Environment Setup

```bash
# Navigate to aws_integration directory
cd d:\AI\trace\TRACE\aws_integration

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure AWS Credentials

The `.env` file is already configured with your credentials. Verify:

```bash
# Windows CMD
type .env

# Verify AWS access
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "...",
    "Account": "...",
    "Arn": "..."
}
```

### Step 3: Deploy MCP Servers

Deploy both MCP servers to AWS Bedrock AgentCore:

```bash
python deployment/deploy_mcp_servers.py --server all
```

This will:
1. ✅ Create IAM roles with necessary permissions
2. ✅ Set up Cognito user pools for authentication
3. ✅ Deploy Principal Tools MCP server
4. ✅ Deploy Regional Coordinator MCP server
5. ✅ Store configuration in AWS Systems Manager
6. ✅ Store secrets in AWS Secrets Manager

**Deployment takes 5-10 minutes per server.**

### Step 4: Test MCP Connections

Verify that MCP servers are accessible:

```bash
python tests/test_mcp_connection.py
```

Expected output:
```
Testing principal_tools MCP Server
✅ Agent ARN: arn:aws:bedrock-agentcore:...
✅ Authentication successful
✅ MCP connection established
✅ Found 12 tools

Testing regional_coordinator MCP Server
✅ Agent ARN: arn:aws:bedrock-agentcore:...
✅ Authentication successful
✅ MCP connection established
✅ Found 16 tools

✅ All tests passed! MCP servers are ready.
```

### Step 5: Run the Principal Agent

```bash
# Interactive mode
python principal_agent_aws.py

# Or with a specific query
python principal_agent_aws.py "Check system health"
```

---

## 📚 Detailed Setup Guide

### AWS SageMaker Code Editor Setup

If you're running in AWS SageMaker Code Editor:

1. **Clone/Upload the Repository:**
   ```bash
   cd /home/sagemaker-user
   # Upload the TRACE folder
   cd TRACE/aws_integration
   ```

2. **Configure Python Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Set Environment Variables:**
   ```bash
   export AWS_REGION=us-east-1
   export BEDROCK_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0
   ```

4. **Deploy and Run:**
   ```bash
   python deployment/deploy_mcp_servers.py
   python tests/test_mcp_connection.py
   python principal_agent_aws.py
   ```

### Local Development Setup

For local testing before AWS deployment:

1. **Test MCP Servers Locally:**
   ```bash
   # Terminal 1 - Start principal tools server
   cd mcp_servers
   python principal_tools_server.py

   # Terminal 2 - Start regional coordinator server
   cd mcp_servers
   python regional_coordinator_server.py

   # Terminal 3 - Test connection
   cd tests
   python test_local_mcp.py
   ```

2. **Test with Google ADK (Original Implementation):**
   ```bash
   cd ..  # Back to TRACE root
   adk web
   # Access http://localhost:8000
   ```

---

## 🎯 Using the Principal Agent

### Interactive Mode

```bash
python principal_agent_aws.py
```

**Example interactions:**

```
🎯 You: Check system health

🤖 Principal Agent:
📊 System Health Report:
- Overall Status: ✅ Healthy
- Health Score: 95.3/100
- Active Agents: 42/42
- Infrastructure: Optimal
- No critical alerts

🎯 You: Load data/trace_reduced_20.json and analyze for energy optimization

🤖 Principal Agent:
✅ Loaded 20 network telemetry records

📊 Energy Optimization Analysis:
🔋 15 records (75%) show energy saving opportunity
   - Low bandwidth utilization (<30%)
   - Affected towers: TX001, TX002, TX003, TX005, TX007

💡 Recommendations:
1. [HIGH] Implement Power Saving Mode
   - Expected savings: 30-40% energy
   - Action: Schedule TRX shutdowns during low-traffic periods
   
2. [MEDIUM] Optimize transceiver allocation
   - 8 idle transceivers detected
   - Potential savings: 15-20%

🎯 You: Execute energy optimization for TX001

🤖 Principal Agent:
🔍 Validating action for tower TX001...
✅ Safety checks passed (safety score: 0.94)

⚡ Executing TRX shutdown:
- Tower: TX001
- Transceivers shutdown: TRX-2, TRX-3
- Estimated energy savings: 24.5 kWh
- Service impact: Minimal
- Rollback available: Yes

✅ Operation completed successfully
```

### Command-Line Mode

```bash
# Single query
python principal_agent_aws.py "Show health dashboard"

# JSON analysis
python principal_agent_aws.py "Load and analyze data/trace_reduced_20.json"

# Specific action
python principal_agent_aws.py "Predict traffic for next 4 hours"
```

---

## 🔧 Available Commands and Capabilities

### System Monitoring
- `"Check system health"` - Overall system status
- `"Show health dashboard"` - Visual dashboard
- `"Get agent status for regional_coordinator_east"` - Specific agent status
- `"Show system metrics for last 24 hours"` - Metrics over time

### Self-Healing
- `"Restart monitoring_agent_tower_1"` - Restart failed agent
- `"Redeploy regional_coordinator_west to latest version"` - Redeploy agent
- `"Reroute traffic from tower_5 to tower_6"` - Traffic rerouting

### JSON Data Analysis
- `"Load data/trace_reduced_20.json"` - Load telemetry data
- `"Analyze this data comprehensively"` - Full AI analysis
- `"Analyze for energy optimization"` - Energy-focused analysis
- `"Analyze for congestion risks"` - Congestion-focused analysis
- `"Get recommendations for tower TX001"` - Tower-specific recommendations
- `"Compare data/file1.json with data/file2.json"` - Compare datasets

### Energy Optimization
- `"Identify energy saving opportunities"` - Find optimization chances
- `"Execute energy optimization workflow"` - Run full workflow
- `"Forecast traffic for tower_3 for next 6 hours"` - Traffic prediction
- `"Make energy decision for tower_2 with current load 45% forecast 25%"` - Decide action

### Congestion Management
- `"Detect traffic surges in region_east"` - Surge detection
- `"Balance load across region_west"` - Load balancing
- `"Activate backup cell on tower_4"` - Emergency activation
- `"Predict congestion for next 4 hours"` - Congestion forecast

---

## 📊 Understanding MCP Tools

### Principal Tools Server (12 tools)

**Health Monitoring:**
- `check_system_health()` - Overall system health
- `get_agent_status(agent_id)` - Specific agent status

**Remediation:**
- `restart_agent(agent_id, reason)` - Restart agent
- `redeploy_agent(agent_id, version)` - Redeploy agent
- `reroute_traffic(from, to, percentage)` - Traffic rerouting

**Dashboard:**
- `generate_health_dashboard()` - Visual dashboard
- `get_system_metrics(time_range, types)` - Metrics data

**JSON Processing:**
- `add_json_data(path)` - Load JSON file
- `analyze_json_data_with_llm(type, focus)` - AI analysis
- `get_recommendations_from_json(tower_id, region_id, focus)` - Recommendations
- `compare_json_datasets(path1, path2)` - Compare files

### Regional Coordinator Server (16 tools)

**Regional Coordination:**
- `aggregate_telemetry(region_id, tower_ids)` - Aggregate data
- `get_regional_metrics(region_id, time_range)` - Regional metrics
- `enforce_policy(name, region_id, params)` - Apply policy
- `validate_action(type, tower, params)` - Validate action
- `balance_load(region_id, strategy)` - Load balancing
- `get_tower_status(tower_id)` - Tower status

**Monitoring Agent:**
- `collect_ran_kpis(tower_id)` - RAN KPIs
- `collect_power_metrics(tower_id)` - Power metrics

**Prediction Agent:**
- `forecast_traffic_load(tower_id, hours)` - Traffic forecast
- `detect_traffic_surge(region_id, threshold)` - Surge detection

**Decision Agent:**
- `make_energy_decision(tower_id, current, forecast)` - Energy decision
- `make_congestion_decision(tower_id, load, surge)` - Congestion decision

**Action Agent:**
- `shutdown_trx(tower_id, trx_ids)` - Shutdown transceivers
- `activate_backup_cell(tower_id, cell_id)` - Activate backup

**Learning Agent:**
- `analyze_performance(workflow_type, days)` - Performance analysis
- `retrain_model(model_name, dataset_size)` - Model retraining

---

## 🔍 Troubleshooting

### Issue: Deployment fails with IAM permissions error

**Solution:**
```bash
# Verify IAM permissions
aws iam get-user

# Check if you have admin access
aws iam list-attached-user-policies --user-name YOUR_USERNAME
```

Required IAM permissions:
- `bedrock:*`
- `iam:CreateRole`, `iam:PutRolePolicy`
- `cognito-idp:*`
- `ecr:*`
- `ssm:PutParameter`
- `secretsmanager:CreateSecret`

### Issue: MCP connection timeout

**Solution:**
```bash
# Check if agent is running
aws bedrock-agentcore list-runtimes --region us-east-1

# Re-authenticate Cognito
python tests/reauthenticate.py

# Restart MCP server
python deployment/deploy_mcp_servers.py --server principal
```

### Issue: Tool calls failing

**Solution:**
```bash
# Test tool directly
python tests/test_individual_tool.py check_system_health

# Check CloudWatch logs
aws logs tail /aws/bedrock-agentcore/runtimes/principal_tools --follow

# Validate tool schemas
python tests/validate_tool_schemas.py
```

### Issue: Python dependency conflicts

**Solution:**
```bash
# Clean environment
deactivate
rm -rf venv

# Recreate with specific versions
python -m venv venv
venv\Scripts\activate
pip install --no-cache-dir -r requirements.txt
```

---

## 📈 Performance Optimization

### Reduce Latency
```python
# In principal_agent_aws.py, adjust timeout
streamablehttp_client(mcp_url, headers, timeout=60)  # Reduce from 120
```

### Cache MCP Connections
```python
# Use connection pooling
from mcp.client import ConnectionPool
pool = ConnectionPool(max_size=10)
```

### Batch Tool Calls
```python
# Call multiple tools in parallel
results = await asyncio.gather(
    session.call_tool("check_system_health"),
    session.call_tool("get_regional_metrics", {"region_id": "east"}),
    session.call_tool("get_tower_status", {"tower_id": "tower_1"})
)
```

---

## 🔐 Security Best Practices

1. **Rotate Cognito Credentials:**
   ```bash
   python deployment/rotate_cognito_password.py
   ```

2. **Enable CloudTrail Logging:**
   ```bash
   aws cloudtrail create-trail --name trace-audit --s3-bucket-name YOUR_BUCKET
   ```

3. **Set up VPC Endpoints:**
   ```bash
   # Restrict AgentCore to VPC only
   aws ec2 create-vpc-endpoint --service-name com.amazonaws.us-east-1.bedrock-agentcore
   ```

4. **Monitor IAM Usage:**
   ```bash
   aws iam get-credential-report
   ```

---

## 📊 Monitoring and Logging

### CloudWatch Dashboards

1. **Create Dashboard:**
   ```bash
   python monitoring/create_cloudwatch_dashboard.py
   ```

2. **View Logs:**
   ```bash
   # Principal Tools logs
   aws logs tail /aws/bedrock-agentcore/runtimes/principal_tools --follow

   # Regional Coordinator logs
   aws logs tail /aws/bedrock-agentcore/runtimes/regional_coordinator --follow
   ```

### Metrics to Monitor
- Agent invocation count
- Tool call latency
- Error rates
- MCP connection pool utilization
- Cognito authentication success rate

---

## 🎓 Additional Resources

### Documentation
- [AWS Bedrock AgentCore Docs](https://docs.aws.amazon.com/bedrock/)
- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [Strands SDK Guide](https://github.com/amazon/strands)
- [TRACE Architecture](../docs/architecture.md)

### Example Workflows
- `examples/energy_optimization_workflow.py` - Energy saving
- `examples/congestion_management_workflow.py` - Traffic management
- `examples/self_healing_workflow.py` - Auto-recovery

### Support
- GitHub Issues: [Create Issue](https://github.com/your-repo/issues)
- Email: sudeeparyang@gmail.com
- AWS Support: [Open Case](https://console.aws.amazon.com/support)

---

## ✅ Next Steps

After successful deployment:

1. **Test Basic Workflows:**
   ```bash
   python examples/test_energy_optimization.py
   python examples/test_congestion_management.py
   python examples/test_self_healing.py
   ```

2. **Load Real Data:**
   ```bash
   # Upload your JSON telemetry data to data/
   python principal_agent_aws.py "Load data/my_telemetry.json and analyze"
   ```

3. **Set up Monitoring:**
   ```bash
   python monitoring/setup_alarms.py
   python monitoring/create_dashboard.py
   ```

4. **Enable Auto-Scaling:**
   ```bash
   aws application-autoscaling register-scalable-target \
     --service-namespace bedrock-agentcore \
     --resource-id runtime/principal_tools \
     --scalable-dimension agentcore:runtime:DesiredCount \
     --min-capacity 1 \
     --max-capacity 10
   ```

---

**🎉 Congratulations! Your TRACE system is now running on AWS Bedrock AgentCore!**

For questions or issues, contact: sudeeparyang@gmail.com
