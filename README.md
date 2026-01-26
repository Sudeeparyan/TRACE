# T.R.A.C.E. – Traffic & Resource Agentic Control Engine

**Team**: Vinay Dangeti, Sudeep Aryan, G S Neelam, Ramya, Aishwarya  
**Contact**: sudeeparyang@gmail.com  
**Project**: Breaking Barriers for Agentic Networks

---

## ⚡ Quick Start (JSON Upload Fix Included!)

```bash
# Test the JSON upload fix
python test_json_upload_fix.py

# Start TRACE (patch auto-applies)
start_trace.bat   # Windows
# OR
adk web           # Direct start

# Open browser: http://localhost:8000
# Upload JSON files - they work now! 🎉
```

**✅ JSON File Upload Issue RESOLVED:**  
The `400 INVALID_ARGUMENT - application/json mimeType not supported` error has been fixed with an automatic conversion patch. See [`JSON_UPLOAD_FIX_COMPLETE.md`](JSON_UPLOAD_FIX_COMPLETE.md) for details.

---

## 📋 Summary

TRACE is an agentic multi-agent system that cuts mobile-tower energy use by 30–40% during low demand and prevents congestion during traffic surges by coordinating Agent-to-Agent (A2A) communication via Model Context Protocol (MCP), leveraging Amazon Bedrock AgentCore and implementing intelligent cloud-edge control using Google's Agent Development Kit (ADK).

---

## 🎯 Problem Statement

Modern mobile networks face three major challenges:

### 1. Energy Inefficiency
- Towers consume power continuously, even during low traffic hours
- Results in high energy costs and carbon emissions
- Idle transmitters and radios remain active without demand-aware control

### 2. Network Congestion During High Demand
- Events like concerts, festivals, or emergencies overload specific towers
- Causes dropped calls and poor Quality of Experience (QoE)
- Requires predictive and proactive load balancing

**During peak traffic:**
- ML-based agents forecast surges and pre-activate backup cells or antennas
- Load is balanced across nearby towers to prevent overload
- Service continuity and QoE are maintained through real-time coordination

### 3. Self-Healing & Resilience
- Failures at any level—agents, servers, or sites—can disrupt service
- Requires autonomous recovery and fault tolerance

**TRACE introduces self-healing through a hierarchical Principal Agent structure:**
- Monitors agent and infrastructure health continuously
- Diagnoses root causes and executes recovery workflows (restarts, redeploys, reroutes)
- Applies policy-driven rollback and restoration with operator visibility and auditability

This framework ensures **energy efficiency**, **congestion resilience**, and **autonomous recovery** for modern RAN (Radio Access Network) systems.

---

## 🏗️ Proposed Solution

TRACE employs a **hierarchical multi-agent architecture** built with Google's Agent Development Kit (ADK):

### Agent Hierarchy

#### 🎖️ Principal (Self-Healing) Agent
**Role**: Global orchestrator and system health guardian

**Responsibilities:**
- Monitors all Parent and Child agents
- Detects anomalies, infrastructure failures, and cascading faults using telemetry + A2A heartbeats
- Executes safe automated remediations (restart, redeploy, reroute) via Amazon Bedrock AgentCore and A2A
- Provides dashboards, rollback capabilities, and human-in-the-loop overrides
- Maintains system-wide policy enforcement

**Communication:**
- Agents communicate securely via Google A2A protocol
- Share context through Model Context Protocol (MCP)
- Run on AWS Bedrock AgentCore, Strands SDK, and SageMaker/Kinesis for data streams and model serving

#### 🏢 Parent Agents (Regional Coordinators)
**Role**: Manage regional clusters and intermediate orchestration

**Responsibilities:**
- Manage regional tower clusters
- Aggregate telemetry from Edge Child Agents
- Enforce regional policies
- Perform quick remediation at cluster level
- Balance load across multiple towers in region
- Report to Principal Agent

#### 🔧 Edge Child Agents (Tower-Level Specialists)

##### 1. Monitoring Agent
**Purpose**: Real-time data collection and streaming

**Functions:**
- Streams RAN Key Performance Indicators (KPIs)
- Collects power consumption metrics
- Monitors tower health indicators
- Tracks environmental conditions
- Sends telemetry to Parent Agent

##### 2. Prediction Agent
**Purpose**: Forecasting and demand prediction

**Functions:**
- Short-term load forecasting using hybrid rule + ML models
- Traffic pattern analysis
- Event detection and prediction
- Peak demand forecasting
- Anomaly prediction

##### 3. Decision xApp Agent
**Purpose**: Policy-based decision making

**Functions:**
- Policy engine for safe control actions (via A2A)
- Energy optimization decision logic
- Congestion avoidance strategies
- Resource allocation decisions
- Safety constraint enforcement

##### 4. Action Agent
**Purpose**: Execute control commands

**Functions:**
- Executes partial TRX (Transceiver) shutdowns
- Activates warm-spare transceivers
- Implements load balancing actions
- Controls antenna configurations
- Applies power management policies

##### 5. Learning Agent
**Purpose**: Continuous improvement and adaptation

**Functions:**
- Retrains models based on historical data
- Manages canary rollouts via MCP metadata
- A/B testing of optimization strategies
- Model performance monitoring
- Feedback loop integration

---

## 🚀 Implementation Architecture

### Multi-Agent System Design

TRACE uses a **hybrid multi-agent architecture** combining:

1. **Hierarchical Delegation**: Principal → Parent → Child agents
2. **Parallel Execution**: Multiple Edge agents work concurrently
3. **Sequential Workflows**: Monitoring → Prediction → Decision → Action
4. **Loop Agents**: Continuous monitoring and healing cycles

### Technology Stack

- **Agent Framework**: Google Agent Development Kit (ADK)
- **LLM Models**: Google Gemini 2.0 Flash
- **Cloud Infrastructure**: AWS Bedrock AgentCore
- **Agent Communication**: A2A Protocol + MCP
- **Data Processing**: Amazon SageMaker + Kinesis
- **State Management**: ADK Sessions & State
- **Telemetry**: Real-time streaming analytics

---

## 📁 Project Structure

```
TRACE/
│
├── README.md                           # This documentation
├── DATA_USAGE_GUIDE.md                # Guide to using reduced datasets ✨
├── JSON_DATA_GUIDE.md                 # Guide to JSON data processing & LLM analysis ✨ NEW
├── reduce_data.py                      # Script to reduce data files
├── example_json_usage.py              # Example script for JSON processing ✨ NEW
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment variables template
│
├── data/                               # TRACE datasets
│   ├── trace_radius_events_small.json       # Original: 480 events, ~15k lines
│   ├── trace_radius_events_reduced.json     # Reduced: 146 events, ~4.7k lines ✨
│   ├── trace_radius_incidents_small.json    # Incidents data
│   ├── trace_radius_incidents_reduced.json  # Reduced incidents
│   └── trace_radius_schema.json            # Data schema definition
│
├── principal_agent/                    # Principal (Self-Healing) Agent
│   ├── __init__.py
│   ├── agent.py                        # Principal agent definition
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── health_monitor.py          # System health monitoring
│   │   ├── remediation.py             # Auto-remediation tools
│   │   ├── dashboard.py               # Monitoring dashboard
│   │   └── json_data_processor.py     # JSON data processing & LLM analysis ✨ NEW
│   │
│   └── parent_agents/                  # Regional Parent Agents
│       ├── __init__.py
│       │
│       ├── regional_coordinator/      # Parent agent for regional management
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   └── tools/
│       │       ├── __init__.py
│       │       ├── telemetry_aggregator.py
│       │       ├── policy_enforcer.py
│       │       └── load_balancer.py
│       │
│       └── edge_agents/               # Edge Child Agents (Tower-level)
│           ├── __init__.py
│           │
│           ├── monitoring_agent/      # Real-time monitoring
│           │   ├── __init__.py
│           │   ├── agent.py
│           │   └── tools/
│           │       ├── __init__.py
│           │       ├── kpi_collector.py
│           │       └── power_monitor.py
│           │
│           ├── prediction_agent/      # Traffic forecasting
│           │   ├── __init__.py
│           │   ├── agent.py
│           │   └── tools/
│           │       ├── __init__.py
│           │       ├── load_forecaster.py
│           │       └── pattern_analyzer.py
│           │
│           ├── decision_xapp_agent/   # Policy-based decisions
│           │   ├── __init__.py
│           │   ├── agent.py
│           │   └── tools/
│           │       ├── __init__.py
│           │       ├── policy_engine.py
│           │       └── optimization_logic.py
│           │
│           ├── action_agent/          # Execute control commands
│           │   ├── __init__.py
│           │   ├── agent.py
│           │   └── tools/
│           │       ├── __init__.py
│           │       ├── trx_controller.py
│           │       └── resource_allocator.py
│           │
│           └── learning_agent/        # Model training & improvement
│               ├── __init__.py
│               ├── agent.py
│               └── tools/
│                   ├── __init__.py
│                   ├── model_trainer.py
│                   └── canary_deployer.py
│
├── workflows/                          # Workflow agents
│   ├── __init__.py
│   ├── energy_optimization_workflow.py # Energy saving pipeline
│   ├── congestion_management_workflow.py # Traffic management
│   └── self_healing_workflow.py       # Auto-recovery loop
│
├── shared/                            # Shared utilities
│   ├── __init__.py
│   ├── mcp_client.py                  # Model Context Protocol client
│   ├── a2a_protocol.py                # Agent-to-Agent communication
│   ├── telemetry.py                   # Telemetry streaming
│   └── models.py                      # Data models
│
├── tests/                             # Test suite
│   ├── __init__.py
│   ├── test_principal_agent.py
│   ├── test_parent_agents.py
│   └── test_edge_agents.py
│
└── docs/                              # Additional documentation
    ├── architecture.md
    ├── deployment.md
    └── api_reference.md
```

---

## 🎯 Key Features & Workflows

### 1. Energy Optimization Workflow (Sequential)

**Pipeline**: Monitoring → Prediction → Decision → Action → Learning

```
Edge Monitoring Agent (collect metrics)
    ↓
Prediction Agent (forecast low-traffic periods)
    ↓
Decision xApp Agent (determine TRX shutdown strategy)
    ↓
Action Agent (execute partial shutdowns)
    ↓
Learning Agent (analyze results, retrain models)
```

**Expected Outcome**: 30-40% energy reduction during low-traffic hours

### 2. Congestion Management Workflow (Parallel + Sequential)

**Phase 1 - Parallel Monitoring**: Multiple towers monitored concurrently

```
Tower 1 Monitoring ─┐
Tower 2 Monitoring ─┼─→ Telemetry Aggregation
Tower 3 Monitoring ─┘
```

**Phase 2 - Sequential Response**:
```
Prediction Agent (detect surge)
    ↓
Decision xApp (load balancing strategy)
    ↓
Action Agent (activate backup cells, redistribute load)
```

**Expected Outcome**: Prevent overload, maintain QoE during peak events

### 3. Self-Healing Loop (Loop Agent)

**Continuous Cycle**:
```
Principal Agent monitors health
    ↓
Detect anomaly/failure
    ↓
Diagnose root cause
    ↓
Execute remediation (restart/redeploy/reroute)
    ↓
Verify recovery
    ↓
Update policies
    ↓
[Repeat]
```

**Expected Outcome**: Autonomous recovery from failures with minimal downtime

---

## 🆕 JSON Data Processing & LLM Analysis (NEW!)

TRACE now supports uploading custom JSON files with network telemetry data and using LLM-powered analysis for intelligent, context-aware recommendations.

### Key Features:
- ✅ **Upload JSON Data**: Add custom network telemetry files
- ✅ **LLM Analysis**: AI-powered comprehensive analysis of your data
- ✅ **Smart Recommendations**: Get actionable recommendations based on patterns
- ✅ **Compare Datasets**: Track changes over time or between configurations
- ✅ **Context Awareness**: LLM understands your specific network conditions

### Quick Start:

```
# Load your JSON data
Load data/trace_reduced_20.json

# Get comprehensive analysis
Analyze this data comprehensively

# Get specific recommendations
Give me energy optimization recommendations

# Compare datasets
Compare yesterday's data with today's data
```

### Example Workflow:

```
User: "Load data/trace_reduced_20.json"
Agent: ✅ Successfully loaded 20 records

User: "Analyze for energy optimization opportunities"
Agent: 📊 Found 15 records (75%) with low bandwidth utilization
      💡 Potential for 30-40% energy savings through radius reduction

User: "Give me the top recommendations"
Agent: 🎯 Recommendations:
      1. [HIGH] Implement Energy Saving Mode
         - Affected towers: TX001, TX002, TX003, TX005
         - Expected savings: 30-40%
      2. [MEDIUM] Reduce Network Latency
         - Optimize routing paths
         - Expected improvement: 20-30%
```

### Available Tools:
1. **add_json_data()** - Load and validate JSON files
2. **analyze_json_data_with_llm()** - AI-powered analysis
3. **get_recommendations_from_json()** - Specific recommendations
4. **compare_json_datasets()** - Compare data over time

**📖 For detailed documentation, see [JSON_DATA_GUIDE.md](JSON_DATA_GUIDE.md)**

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.9 or higher
- Google API Key (for Gemini models)
- AWS Account (for Bedrock AgentCore)
- Virtual environment recommended

### Installation

1. **Clone/Navigate to the TRACE directory**:
```bash
cd d:\AI\AI_Implementation\ADK-End-to-End\TRACE
```

2. **Create and activate virtual environment**:
```bash
# Windows CMD
python -m venv .venv
.venv\Scripts\activate.bat

# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
# Copy the example file
copy .env.example .env

# Edit .env and add your credentials:
# GOOGLE_API_KEY=your_google_api_key
# AWS_ACCESS_KEY_ID=your_aws_access_key
# AWS_SECRET_ACCESS_KEY=your_aws_secret_key
# AWS_REGION=your_aws_region
```

### Running TRACE

1. **Start the interactive web UI**:
```bash
adk web
```

2. **Access the web interface**:
   - Open your browser to `http://localhost:8000`
   - Select "principal_agent" from the dropdown menu

3. **Interact with TRACE**:
   - Ask about system health
   - Request energy optimization analysis
   - Query traffic predictions
   - Test self-healing scenarios

### Example Prompts

**Energy Optimization:**
```
Analyze current energy usage and recommend optimization strategies for low-traffic hours
```

**Congestion Management:**
```
There's a concert at Stadium X tonight. Predict traffic surge and prepare load balancing plan
```

**Self-Healing:**
```
Simulate a tower failure at Site 123 and show the self-healing response
```

**System Health:**
```
Provide comprehensive health report for all towers in Region East
```

**JSON Data Analysis (NEW!):**
```
Load data/trace_reduced_20.json and analyze it for energy optimization opportunities
```

```
Add my JSON file from d:/network_data.json and give me comprehensive recommendations
```

```
Analyze the loaded data for congestion patterns and predict future issues
```

---

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test module
python -m pytest tests/test_principal_agent.py

# Run with coverage
python -m pytest --cov=. tests/
```

---

## 📊 Expected Outcomes

### Energy Efficiency
- **Target**: 30-40% reduction in energy consumption during low-traffic hours
- **Mechanism**: Intelligent TRX shutdown based on predicted demand
- **Benefit**: Lower operational costs, reduced carbon footprint

### Congestion Prevention
- **Target**: Zero dropped calls during predicted surge events
- **Mechanism**: Proactive load balancing and backup cell activation
- **Benefit**: Improved QoE, customer satisfaction

### Self-Healing
- **Target**: <5 minute recovery time from common failures
- **Mechanism**: Automated detection, diagnosis, and remediation
- **Benefit**: Reduced downtime, lower maintenance costs

### System Resilience
- **Target**: 99.99% uptime
- **Mechanism**: Multi-level redundancy and fault tolerance
- **Benefit**: Reliable service delivery

---

## 🌟 Why TRACE is Novel & Relevant

TRACE unifies **energy optimization**, **congestion avoidance**, and **self-healing orchestration** in one agentic, A2A + MCP + Bedrock-compliant framework.

### Key Innovations:

1. **Hierarchical Multi-Agent Architecture**: Three-tier system (Principal → Parent → Child) providing scalability and fault isolation

2. **Hybrid Workflow Patterns**: Combines sequential, parallel, and loop agents for optimal performance

3. **A2A + MCP Integration**: Secure agent communication with context sharing via Model Context Protocol

4. **Autonomous Self-Healing**: No human intervention required for common failure scenarios

5. **Energy-Aware Optimization**: First system to combine traffic prediction with energy management in real-time

6. **Production-Ready**: Built on AWS Bedrock AgentCore and Google ADK for enterprise deployment

### Alignment with Hackathon Challenge

"Breaking Barriers for Agentic Networks" - TRACE delivers:
- ✅ Measurable sustainability gains (30-40% energy reduction)
- ✅ Operational resilience (autonomous self-healing)
- ✅ Advanced automation (intelligent agent coordination)
- ✅ Real-world impact (applicable to telecom operators worldwide)

---

## 📚 Additional Resources

### ADK Documentation
- [ADK Multi-Agent Systems](https://google.github.io/adk-docs/agents/multi-agent-systems/)
- [Sequential Agents](https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/)
- [Parallel Agents](https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/)
- [Loop Agents](https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/)

### Reference Implementations
- `7-multi-agent/`: Multi-agent delegation patterns
- `10-sequential-agent/`: Sequential workflow implementation
- `11-parallel-agent/`: Parallel execution patterns
- `12-loop-agent/`: Loop-based workflows

### External Resources
- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [Agent-to-Agent Communication (A2A)](https://github.com/google/a2a-protocol)

---

## 🤝 Contributing

This is a hackathon project. For questions or collaboration:

**Contact**: sudeeparyang@gmail.com

**Team Members**:
- Vinay Dangeti
- Sudeep Aryan
- G S Neelam
- Ramya
- Aishwarya

---

## 📄 License

This project is created for the "Breaking Barriers for Agentic Networks" hackathon.

---

## 🎉 Next Steps

### Phase 1: Core Implementation
1. ✅ Project structure and documentation
2. ⏳ Implement Principal Agent with health monitoring
3. ⏳ Create Parent Agent for regional coordination
4. ⏳ Build Edge Child Agents (Monitoring, Prediction, Decision, Action, Learning)

### Phase 2: Workflows
5. ⏳ Energy optimization workflow (Sequential)
6. ⏳ Congestion management workflow (Parallel + Sequential)
7. ⏳ Self-healing loop (Loop Agent)

### Phase 3: Integration
8. ⏳ MCP client integration
9. ⏳ A2A protocol implementation
10. ⏳ AWS Bedrock AgentCore integration

### Phase 4: Testing & Validation
11. ⏳ Unit tests for all agents
12. ⏳ Integration tests for workflows
13. ⏳ Performance benchmarking
14. ⏳ Demo scenarios

### Phase 5: Deployment
15. ⏳ AWS deployment configuration
16. ⏳ Monitoring and observability
17. ⏳ Documentation finalization
18. ⏳ Presentation preparation

---

**Built with ❤️ using Google Agent Development Kit (ADK)**
