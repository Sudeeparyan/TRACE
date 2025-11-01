# TRACE AWS Integration - Testing Checklist

## ✅ Pre-Deployment Tests

### Environment Setup
- [ ] Python 3.9+ installed
- [ ] AWS CLI installed and configured
- [ ] Virtual environment created
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with AWS credentials

### AWS Credentials
- [ ] AWS_ACCESS_KEY_ID is set
- [ ] AWS_SECRET_ACCESS_KEY is set
- [ ] AWS_REGION is set to us-east-1
- [ ] Can run `aws sts get-caller-identity` successfully
- [ ] IAM user has necessary permissions

## ✅ Deployment Tests

### MCP Server Deployment
- [ ] Principal Tools Server deploys without errors
- [ ] Regional Coordinator Server deploys without errors
- [ ] IAM roles created successfully
- [ ] Cognito user pools created
- [ ] ECR repositories created (if needed)
- [ ] Docker images built and pushed

### Configuration Storage
- [ ] SSM parameters created (`/trace/*/agent_arn`)
- [ ] SSM parameters created (`/trace/*/client_id`)
- [ ] Secrets Manager secrets created
- [ ] Cognito test user created successfully
- [ ] Authentication works (bearer token received)

## ✅ Connection Tests

### MCP Connectivity
- [ ] Can connect to Principal Tools MCP server
- [ ] Can connect to Regional Coordinator MCP server
- [ ] JWT authentication succeeds
- [ ] Tools list retrieved successfully
- [ ] At least 12 tools from Principal Tools
- [ ] At least 16 tools from Regional Coordinator

**Test Command:**
```bash
python tests/test_mcp_connection.py
```

**Expected Result:**
```
✅ Authentication successful
✅ MCP connection established
✅ Found 12 tools (principal)
✅ Found 16 tools (regional)
✅ All tests passed!
```

## ✅ Tool Tests

### Principal Tools Server

#### Health Monitoring Tools
- [ ] `check_system_health()` - Returns overall status
- [ ] `get_agent_status(agent_id)` - Returns specific agent status

**Test:**
```python
python principal_agent_aws.py "Check system health"
```

#### Remediation Tools
- [ ] `restart_agent(agent_id)` - Simulates agent restart
- [ ] `redeploy_agent(agent_id, version)` - Simulates redeployment
- [ ] `reroute_traffic(from, to, pct)` - Simulates rerouting

**Test:**
```python
python principal_agent_aws.py "Restart monitoring_agent_tower_1"
```

#### Dashboard Tools
- [ ] `generate_health_dashboard()` - Returns dashboard data
- [ ] `get_system_metrics(range, types)` - Returns metrics

**Test:**
```python
python principal_agent_aws.py "Show health dashboard"
```

#### JSON Processing Tools
- [ ] `add_json_data(path)` - Loads JSON file
- [ ] `analyze_json_data_with_llm(type, focus)` - Analyzes data
- [ ] `get_recommendations_from_json(tower, region, metric)` - Gets recommendations
- [ ] `compare_json_datasets(path1, path2)` - Compares datasets

**Test:**
```python
python principal_agent_aws.py "Load data/trace_reduced_20.json and analyze"
```

### Regional Coordinator Server

#### Regional Coordination Tools
- [ ] `aggregate_telemetry(region, towers)` - Aggregates data
- [ ] `get_regional_metrics(region, time)` - Gets metrics
- [ ] `enforce_policy(name, region, params)` - Enforces policy
- [ ] `validate_action(type, tower, params)` - Validates action
- [ ] `balance_load(region, strategy)` - Balances load
- [ ] `get_tower_status(tower_id)` - Gets tower status

**Test:**
```python
python principal_agent_aws.py "Balance load across region_east"
```

#### Edge Agent Tools
- [ ] Monitoring: `collect_ran_kpis`, `collect_power_metrics`
- [ ] Prediction: `forecast_traffic_load`, `detect_traffic_surge`
- [ ] Decision: `make_energy_decision`, `make_congestion_decision`
- [ ] Action: `shutdown_trx`, `activate_backup_cell`
- [ ] Learning: `analyze_performance`, `retrain_model`

**Test:**
```python
python principal_agent_aws.py "Forecast traffic for tower_5 for next 4 hours"
```

## ✅ Workflow Tests

### Energy Optimization Workflow
- [ ] Load telemetry data
- [ ] Analyze for energy opportunities
- [ ] Make energy decision
- [ ] Execute TRX shutdown
- [ ] Verify energy savings

**Test Sequence:**
```
Load data/trace_reduced_20.json
Analyze for energy optimization
Make energy decision for tower_1 with current load 45% forecast 25%
Execute shutdown for identified transceivers
```

### Congestion Management Workflow
- [ ] Detect traffic surge
- [ ] Forecast traffic load
- [ ] Make congestion decision
- [ ] Balance load across towers
- [ ] Activate backup cells if needed

**Test Sequence:**
```
Detect traffic surges in region_east
Forecast traffic for next 4 hours
Make congestion decision for high-load tower
Balance load across region
```

### Self-Healing Workflow
- [ ] Check system health
- [ ] Detect agent failure (simulated)
- [ ] Restart failed agent
- [ ] Verify recovery
- [ ] Update health status

**Test Sequence:**
```
Check system health
Get agent status for monitoring_agent_tower_1
Restart monitoring_agent_tower_1
Verify agent is healthy
```

## ✅ Integration Tests

### End-to-End Scenarios

#### Scenario 1: Energy Optimization
```bash
# Step 1: Check initial state
python principal_agent_aws.py "Check system health"

# Step 2: Load data
python principal_agent_aws.py "Load data/trace_reduced_20.json"

# Step 3: Analyze
python principal_agent_aws.py "Analyze for energy optimization"

# Step 4: Get recommendations
python principal_agent_aws.py "Get recommendations for tower TX001"

# Step 5: Execute (simulated)
python principal_agent_aws.py "Make energy decision for TX001 with current 40% forecast 25%"
```

**Expected Results:**
- ✅ Health check shows system operational
- ✅ JSON data loaded successfully
- ✅ Analysis identifies energy opportunities
- ✅ Recommendations include energy-saving actions
- ✅ Decision recommends TRX shutdown

#### Scenario 2: Congestion Management
```bash
# Step 1: Monitor region
python principal_agent_aws.py "Get regional metrics for region_east"

# Step 2: Detect surge
python principal_agent_aws.py "Detect traffic surges in region_east"

# Step 3: Forecast
python principal_agent_aws.py "Forecast traffic for tower_5 for 6 hours"

# Step 4: Decide
python principal_agent_aws.py "Make congestion decision for tower_5"

# Step 5: Act
python principal_agent_aws.py "Balance load across region_east"
```

**Expected Results:**
- ✅ Regional metrics retrieved
- ✅ Surge detection runs (may or may not detect surge)
- ✅ Traffic forecast shows predicted loads
- ✅ Decision recommends load balancing or backup activation
- ✅ Load balancing executes successfully

#### Scenario 3: Self-Healing
```bash
# Step 1: Check all agents
python principal_agent_aws.py "Check system health"

# Step 2: Simulate failure
python principal_agent_aws.py "Get agent status for monitoring_agent_tower_1"

# Step 3: Restart
python principal_agent_aws.py "Restart monitoring_agent_tower_1"

# Step 4: Verify
python principal_agent_aws.py "Check system health"

# Step 5: Redeploy if needed
python principal_agent_aws.py "Redeploy regional_coordinator_west to latest"
```

**Expected Results:**
- ✅ Initial health check shows status
- ✅ Agent status retrieved
- ✅ Restart completes successfully
- ✅ Health check shows improvement
- ✅ Redeployment executes if needed

## ✅ Performance Tests

### Latency
- [ ] Agent response time < 2 seconds
- [ ] Tool call latency < 500ms
- [ ] MCP connection < 1 second
- [ ] Authentication < 500ms
- [ ] End-to-end workflow < 30 seconds

**Measurement:**
```bash
time python principal_agent_aws.py "Check system health"
```

### Concurrency
- [ ] Can handle 10 concurrent requests
- [ ] MCP connections pooled correctly
- [ ] No connection leaks

### Data Processing
- [ ] Can process 20-record JSON (trace_reduced_20.json)
- [ ] Can analyze up to 100 records
- [ ] Sampling works for large datasets

## ✅ Error Handling Tests

### Network Errors
- [ ] Handles MCP connection timeout gracefully
- [ ] Retries failed connections
- [ ] Shows clear error messages

**Test:**
```bash
# Stop one MCP server and test
python principal_agent_aws.py "Check system health"
```

### Authentication Errors
- [ ] Handles expired JWT tokens
- [ ] Re-authenticates automatically
- [ ] Shows clear auth errors

### Tool Errors
- [ ] Handles missing required parameters
- [ ] Shows validation errors clearly
- [ ] Doesn't crash on tool failure

## ✅ AWS Resource Tests

### IAM Roles
- [ ] Roles created with correct permissions
- [ ] Assume role policy correct
- [ ] No overly permissive policies

**Check:**
```bash
aws iam get-role --role-name agentcore-principal_tools-role
```

### Cognito
- [ ] User pool created
- [ ] App client configured
- [ ] Test user can authenticate

**Check:**
```bash
aws cognito-idp list-user-pools --max-results 10
```

### SSM Parameters
- [ ] All parameters created
- [ ] Values are correct
- [ ] Accessible by agent

**Check:**
```bash
aws ssm get-parameters-by-path --path /trace/ --recursive
```

### Secrets Manager
- [ ] Secrets created
- [ ] Credentials stored securely
- [ ] Accessible by agent

**Check:**
```bash
aws secretsmanager list-secrets --filter Key=name,Values=/trace/
```

### CloudWatch Logs
- [ ] Log groups created
- [ ] Logs are being written
- [ ] Can view agent logs

**Check:**
```bash
aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore
aws logs tail /aws/bedrock-agentcore/runtimes/principal_tools --follow
```

## ✅ Documentation Tests

### README Files
- [ ] AWS_SETUP_GUIDE.md is complete
- [ ] README_AWS.md is accurate
- [ ] QUICK_REFERENCE.md is helpful
- [ ] IMPLEMENTATION_SUMMARY.md is comprehensive

### Code Documentation
- [ ] All functions have docstrings
- [ ] Parameter descriptions clear
- [ ] Return values documented
- [ ] Examples provided

### Deployment Scripts
- [ ] deploy_mcp_servers.py documented
- [ ] quick_start.bat has comments
- [ ] Error messages are clear

## ✅ Security Tests

### Credentials
- [ ] AWS credentials not hardcoded in code
- [ ] Credentials only in .env file
- [ ] .env file in .gitignore

### Authentication
- [ ] JWT tokens expire appropriately
- [ ] Re-authentication works
- [ ] No tokens in logs

### IAM Permissions
- [ ] Principle of least privilege followed
- [ ] No wildcard permissions
- [ ] Resource-specific when possible

## 📊 Test Results Summary

| Category | Tests | Passed | Failed | Notes |
|----------|-------|--------|--------|-------|
| Pre-Deployment | 5 | | | |
| Deployment | 11 | | | |
| Connection | 6 | | | |
| Principal Tools | 11 | | | |
| Regional Tools | 12 | | | |
| Workflows | 15 | | | |
| Integration | 3 scenarios | | | |
| Performance | 5 | | | |
| Error Handling | 3 | | | |
| AWS Resources | 5 | | | |
| Documentation | 7 | | | |
| Security | 6 | | | |

**Total**: 89 tests

## 🎯 Success Criteria

### Minimum for Production
- ✅ All deployment tests pass
- ✅ All connection tests pass
- ✅ At least 80% of tool tests pass
- ✅ All 3 integration scenarios pass
- ✅ Performance meets targets
- ✅ Security tests pass

### Recommended
- ✅ 100% of tool tests pass
- ✅ All error handling tests pass
- ✅ All AWS resource tests pass
- ✅ Documentation complete and accurate

## 📝 Notes

### Common Issues
1. **Connection timeouts**: Increase timeout in streamablehttp_client
2. **Authentication failures**: Check Cognito user is created
3. **Tool not found**: Verify MCP server deployment
4. **Slow responses**: Check AWS region latency

### Tips for Testing
- Start with connection tests before tool tests
- Test tools individually before workflows
- Use verbose logging during testing
- Check CloudWatch logs for errors
- Test with small JSON files first

---

**Testing Status**: ⬜ Not Started | 🔄 In Progress | ✅ Complete | ❌ Failed

**Last Updated**: [Date]
**Tested By**: [Name]
**Environment**: [Dev/Staging/Production]
