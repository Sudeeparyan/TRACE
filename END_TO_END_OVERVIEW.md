# TRACE — End‑to‑End Overview (Start → Finish, Inputs → Outputs)

This guide explains the full flow of the TRACE system in this repo: where execution starts, what happens step‑by‑step across agents, and what the inputs and outputs are in both local/dev and AWS production modes. Links point to the exact files/scripts in this workspace.

---

## What TRACE Does (one paragraph)
TRACE (Traffic & Resource Agentic Control Engine) is a hierarchical multi‑agent system for telecom networks. A Principal Agent orchestrates Regional Coordinators, which in turn coordinate Edge Agents (Monitor, Predict, Decide, Act, Learn). Together they reduce energy use during low demand (target 30–40%), prevent congestion during surges, and self‑heal failures. Agents communicate via A2A and share context via MCP when available; in AWS production they run on Bedrock AgentCore, with logs/traces in CloudWatch and state in DynamoDB.

Key architecture docs:
- README.md — project overview and features
- docs/architecture.md — hierarchy, workflows, data flow
- trace_aws_production/DOCUMENTATION_INDEX.md — doc map for production
- trace_aws_production/FILE_EXECUTION_SEQUENCE.md — exact deployment/run order

---

## Two Ways to Run TRACE
You’ll see two parallel implementations in the repo:

1) Local/ADK (developer mode)
- Code: principal_agent/agent.py (ADK Agent definitions)
- Typical usage: “adk web” to explore the Principal Agent and workflows locally

2) AWS Production (Bedrock AgentCore + Strands)
- Code and scripts: trace_aws_production/agents/*.py, deployment/*, utilities
- Typical usage: deploy with deploy.py, then invoke agents via CLI or helper scripts

Both follow the same high‑level flows and roles, but the production path adds AWS resources, CloudWatch Observability, and A2A/MCP integration when enabled.

---

## Start → End: Control Flow at a Glance

1) User provides an input (prompt or task)
- Local/ADK: via web UI (“adk web”), or ADK Runner calling root_agent
- AWS Production: via AgentCore CLI, helper scripts (chat_with_agent.py, test_multi_agent.py), or direct API call

2) Principal Agent receives the request
- ADK version: principal_agent/agent.py exports root_agent (the orchestrator)
- AWS production: agents/principal_agent.py creates a Strands Agent wrapped by Bedrock AgentCore entrypoint

3) Orchestration and delegation
- Principal Agent may call Regional Coordinator(s)
- Regional may coordinate multiple Edge Agents in sequence or parallel:
  - Monitor → Predict → Decide → Act → Learn

4) Tools and data access
- Tools include health checks, remediation, dashboards, JSON telemetry analysis
- If MCP servers are present, expanded toolsets are loaded; otherwise basic tools are used

5) Aggregation and response
- Regional aggregates Edge results and returns to Principal
- Principal summarizes and returns a final consolidated response to the user

6) Outputs recorded
- Console output in your terminal
- In production: CloudWatch logs and traces, optional DynamoDB tables for state/memory, optional S3 artifacts

---

## Inputs and Outputs (by mode)

### Local / ADK mode
- Entry: principal_agent/agent.py → root_agent (ADK)
- Inputs:
  - User prompt (e.g., “Analyze energy optimization opportunities”)
  - Optional local JSON telemetry file (data/trace_reduced_20.json, trace_llm_20.json)
- Processing:
  - Principal Agent coordinates sub‑agents and tools
  - JSON tools (add_json_data, analyze_json_data_with_llm, get_recommendations_from_json, compare_json_datasets)
- Outputs:
  - Textual reasoning and recommendations in the ADK web UI
  - No AWS resources required

References:
- README.md (Getting Started → adk web)
- principal_agent/agent.py — ADK agent, tools, sub‑agents

### AWS Production mode (Bedrock AgentCore + Strands)
- Entrypoints:
  - Deploy: trace_aws_production/deployment/deploy.py
  - Agent runtimes: trace_aws_production/agents/*.py
  - Invoke helpers: trace_aws_production/test_multi_agent.py, chat_with_agent.py, view_agent_to_agent.py
- Inputs:
  - User prompt (string payload to agent runtime)
  - Environment: AWS credentials/region, model access
  - Optional JSON telemetry files (for LLM analysis features)
- Processing:
  - agents/principal_agent.py: Creates a Strands Agent, registers a BedrockAgentCore entrypoint, loads tools (MCP/A2A if available or basic tools otherwise)
  - agents/regional_coordinator.py: Coordinates regional actions/tools
  - Edge agents (edge_monitor_agent.py, edge_predict_agent.py, edge_decide_agent.py, edge_action_agent.py, edge_learn_agent.py): Provide specialized capabilities
  - A2A: optional inter‑agent messages and registry
- Outputs:
  - Terminal: pretty‑printed JSON responses
  - CloudWatch Logs/GenAI Observability: traces of agent‑to‑agent calls and timings
  - DynamoDB: agent memory/registry/state tables (if enabled by deployment)
  - S3: artifacts or packaged code (deployment)

References:
- trace_aws_production/FILE_EXECUTION_SEQUENCE.md — exact steps to deploy and validate
- trace_aws_production/agents/principal_agent.py — production Principal Agent
- trace_aws_production/agents/regional_coordinator.py — production Regional Coordinator
- trace_aws_production/agents/edge_*.py — edge agents
- trace_aws_production/chat_with_agent.py — invoke via AWS CLI and read response.json
- trace_aws_production/test_multi_agent.py — invoke via agentcore.exe (local AgentCore)
- trace_aws_production/view_agent_to_agent.py — demo end‑to‑end A2A flows and where to view traces

---

## Where It Starts (entrypoints)

- Local/ADK development
  - Start the ADK web app and select the principal agent:
    - ADK loads root_agent from principal_agent/agent.py
    - You interact in a browser, ADK routes inputs to the Principal Agent

- AWS Production
  - First deploy per trace_aws_production/FILE_EXECUTION_SEQUENCE.md
  - Then choose one of the following ways to invoke:
    - chat_with_agent.py (uses AWS CLI bedrock‑agentcore invoke‑agent‑runtime)
    - test_multi_agent.py (uses local AgentCore CLI agentcore.exe to invoke installed agents)
    - view_agent_to_agent.py (runs curated prompts that trigger multi‑agent A2A and tells you where to observe traces/logs)

---

## What Happens Inside (functional flow)

1) Principal Agent
- ADK version: principal_agent/agent.py
  - Tools: health monitoring, remediation, dashboards, JSON data analysis
  - Sub‑agent: Regional Coordinator (imported from parent_agents)
- Production: agents/principal_agent.py
  - Wraps a Strands Agent in Bedrock AgentCore
  - Loads MCP/A2A tools when available or uses built‑ins (get_system_status, analyze_network)
  - Exposes an entrypoint registered with BedrockAgentCoreApp

2) Regional Coordinator
- ADK: parent_agents/regional_coordinator/agent.py (tools: telemetry aggregation, policy, load balance)
- Production: agents/regional_coordinator.py (basic tools: get_regional_status, analyze_regional_performance, coordinate_edge_agents)
- Role: divides work across Edge agents and aggregates results back up to Principal

3) Edge Agents
- Monitor: collect metrics, detect anomalies (agents/edge_monitor_agent.py)
- Predict: forecast load/surge (agents/edge_predict_agent.py)
- Decide: evaluate policies and select actions
- Action: execute TRX shutdown/activation, power adjustments
- Learn: analyze outcomes, retrain models

4) A2A and MCP
- When enabled, Principal/Regional/Edge communicate via A2A protocol and share state via MCP servers/tools
- Production code gracefully degrades if MCP/A2A not present (basic tools still work)

5) Aggregation and Response
- Edge → Regional: metrics, forecasts, recommendations
- Regional consolidates and returns to Principal
- Principal formats final response with explanations, metrics, and suggestions

---

## Inputs: What You Provide
- Prompt text: the natural‑language request
  - Examples (from docs and scripts):
    - “Check overall system health”
    - “Analyze energy optimization opportunities”
    - “Coordinate edge agents for TX001”
- Optional data files for analysis:
  - data/trace_reduced_20.json — small telemetry subset for demos/tests
  - data/trace_llm_20.json — 20 LLM prompt→completion pairs for Decision xApp testing
- Environment / configuration:
  - AWS credentials and region for production
  - Bedrock model access (enable Anthropic Sonnet, etc.)
  - .env variables if used by scripts

---

## Outputs: What You Get
- Human‑readable responses
  - Console output from test_multi_agent.py, chat_with_agent.py
  - ADK web UI responses when running locally
- JSON payloads
  - chat_with_agent.py writes a response.json and also prints parsed content
  - test_multi_agent.py extracts the JSON from agentcore.exe stdout
- Observability in AWS (production)
  - CloudWatch Logs: raw conversations per runtime (principal/regional/edge)
  - CloudWatch GenAI Observability Traces: end‑to‑end spans for A2A flows
  - DynamoDB tables: agent memory/registry/state (as created by deployment)
  - S3 buckets: deployment artifacts, optional data

Quick pointers from the A2A viewer:
- trace_aws_production/view_agent_to_agent.py prints URLs and log group names to inspect multi‑agent traces

---

## Concrete “Happy Path” Examples

1) Ask the Principal for a full multi‑agent optimization report (production)
- Script: trace_aws_production/view_agent_to_agent.py
- What happens:
  - Your prompt → Principal → Regional → Edge (Monitor/Predict/Decide) → back up → consolidated response
- Where to observe:
  - Console output shows the final text
  - CloudWatch GenAI Observability shows the chain of agent calls and timings

2) Quick status checks (production)
- Script: trace_aws_production/chat_with_agent.py
- Principal, Regional, and Edge agent prompts return structured JSON/text, and write response.json for debugging

3) ADK exploration (local)
- Select the principal agent in ADK Web and try prompts from README.md
- JSON tools let you load data/trace_reduced_20.json for LLM‑driven insights

---

## Error Modes and Safety
- If MCP/A2A aren’t installed in production, the Principal/Regional agents fall back to basic tools (no crash)
- If a tool fails at runtime, agents return a JSON error with status=error; logs appear in CloudWatch
- Self‑healing workflows (when enabled) aim to restart/redeploy/reroute based on health reports

---

## File Index (most relevant)
- principal_agent/agent.py — ADK Principal Agent (root_agent) with JSON tools and regional sub‑agent
- trace_aws_production/agents/principal_agent.py — Production Principal Agent (Strands + Bedrock AgentCore)
- trace_aws_production/agents/regional_coordinator.py — Regional coordinator (production)
- trace_aws_production/agents/edge_*.py — Edge Monitoring/Predict/Decide/Action/Learn agents
- trace_aws_production/test_multi_agent.py — Lightweight invoke helper via agentcore.exe
- trace_aws_production/chat_with_agent.py — AWS CLI invocation helper; writes response.json
- trace_aws_production/view_agent_to_agent.py — Demonstrates A2A and where to inspect traces
- trace_aws_production/FILE_EXECUTION_SEQUENCE.md — exact deployment order
- docs/architecture.md — full diagrams and rationale
- data/trace_reduced_20.json — demo telemetry; data/README_20.txt for schema

---

## TL;DR
- Start: User prompt → Principal Agent
- Middle: Principal delegates to Regional → Edge agents with tools and (optionally) A2A/MCP
- End: Principal aggregates and returns a final JSON/text response; production runs record logs/traces/tables in AWS
- Inputs: user prompt (+ optional JSON telemetry files; + AWS creds in prod)
- Outputs: human‑readable answer, JSON payloads, and (in prod) CloudWatch traces/logs plus DynamoDB/S3 artifacts
