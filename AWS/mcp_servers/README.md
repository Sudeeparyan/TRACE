# TRACE MCP Servers

Model Context Protocol (MCP) servers for agent-to-agent context sharing in TRACE.

## Overview

MCP enables TRACE agents to:
- Share context and state between agents
- Expose tools that other agents can discover and use
- Access shared resources (telemetry data, tower configs, policies)

## MCP Server Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TRACE MCP SERVERS                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  Telemetry MCP  │  │   Tower MCP     │  │  Policy MCP │ │
│  │     Server      │  │    Server       │  │   Server    │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘ │
│           │                    │                   │        │
│           └────────────────────┼───────────────────┘        │
│                                │                            │
│                    ┌───────────▼───────────┐                │
│                    │   MCP Hub (Gateway)   │                │
│                    └───────────┬───────────┘                │
│                                │                            │
└────────────────────────────────┼────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────────┐
        │                        │                            │
        ▼                        ▼                            ▼
 ┌──────────────┐      ┌──────────────┐            ┌──────────────┐
 │  Monitoring  │      │  Prediction  │            │    Action    │
 │    Agent     │      │    Agent     │            │    Agent     │
 └──────────────┘      └──────────────┘            └──────────────┘
```

## Servers

1. **Telemetry MCP Server** - Exposes real-time tower metrics
2. **Tower Config MCP Server** - Provides tower configuration and status
3. **Policy MCP Server** - Shares remediation policies and rules
4. **Energy MCP Server** - Energy optimization context and controls

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start MCP servers
python run_mcp_servers.py
```
