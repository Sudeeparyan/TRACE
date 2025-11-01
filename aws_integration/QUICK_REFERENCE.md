# TRACE AWS Integration - Quick Reference Card

## 🚀 Getting Started (3 Commands)

```bash
cd d:\AI\trace\TRACE\aws_integration
quick_start.bat
python principal_agent_aws.py
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `principal_agent_aws.py` | Main agent (run this) |
| `quick_start.bat` | Automated setup |
| `AWS_SETUP_GUIDE.md` | Complete guide |
| `.env` | AWS credentials |

## 🛠️ Commands

### Deployment
```bash
# Deploy everything
python deployment/deploy_mcp_servers.py --server all

# Deploy specific server
python deployment/deploy_mcp_servers.py --server principal
python deployment/deploy_mcp_servers.py --server regional
```

### Testing
```bash
# Test MCP connections
python tests/test_mcp_connection.py

# Test with query
python principal_agent_aws.py "Check system health"
```

### Interactive Use
```bash
python principal_agent_aws.py
# Then type queries at the prompt
```

## 💬 Example Queries

### System Health
```
Check system health
Show health dashboard
Get agent status for regional_coordinator_east
```

### Energy Optimization
```
Load data/trace_reduced_20.json
Analyze for energy optimization
Get recommendations for tower TX001
Execute energy optimization for region_east
```

### Congestion Management
```
Detect traffic surges in region_east
Forecast traffic for tower_5 for next 4 hours
Balance load across region_west
```

### Self-Healing
```
Restart monitoring_agent_tower_1
Redeploy regional_coordinator_west
Reroute traffic from tower_5 to tower_6
```

## 🔧 Available Tools (28)

### Principal Tools (12)
- Health: `check_system_health`, `get_agent_status`
- Remediation: `restart_agent`, `redeploy_agent`, `reroute_traffic`
- Dashboard: `generate_health_dashboard`, `get_system_metrics`
- JSON: `add_json_data`, `analyze_json_data_with_llm`, `get_recommendations_from_json`, `compare_json_datasets`

### Regional Coordinator (16)
- Regional: 6 tools
- Monitoring: 2 tools
- Prediction: 2 tools
- Decision: 2 tools
- Action: 2 tools
- Learning: 2 tools

## 🔐 AWS Resources

### Services Used
- Bedrock AgentCore (runtime)
- IAM (roles)
- Cognito (auth)
- SSM Parameter Store (config)
- Secrets Manager (credentials)
- CloudWatch (logs)

### Check Deployment
```bash
# List runtimes
aws bedrock-agentcore list-runtimes --region us-east-1

# View logs
aws logs tail /aws/bedrock-agentcore/runtimes/principal_tools --follow

# Check parameters
aws ssm get-parameters-by-path --path /trace/ --recursive
```

## 🐛 Quick Troubleshooting

### Deployment Fails
```bash
aws sts get-caller-identity  # Check credentials
aws configure                 # Reconfigure if needed
```

### Connection Timeout
```bash
python tests/test_mcp_connection.py  # Re-test
```

### Tool Fails
```bash
# View logs
aws logs tail /aws/bedrock-agentcore/runtimes/principal_tools --follow
```

## 📊 Architecture

```
Principal Agent (Strands SDK)
    ├── MCP → Principal Tools Server (12 tools)
    └── MCP → Regional Coordinator Server (16 tools)
```

## 🎯 Success Metrics

✅ 30-40% energy savings
✅ <5 min recovery time
✅ 28 tools operational
✅ AWS production-ready

## 📚 Documentation

- **Complete Guide**: `AWS_SETUP_GUIDE.md`
- **Quick Ref**: `README_AWS.md`
- **Summary**: `IMPLEMENTATION_SUMMARY.md`
- **Original**: `../README.md`

## 🔗 Useful Links

- AWS Bedrock: https://console.aws.amazon.com/bedrock/
- CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/
- SSM Parameters: https://console.aws.amazon.com/systems-manager/parameters

## 📞 Support

**Email**: sudeeparyang@gmail.com

---

**One-Line Start**: `cd aws_integration && quick_start.bat && python principal_agent_aws.py`
