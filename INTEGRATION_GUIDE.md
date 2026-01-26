# TRACE - Principal Agent Integration Guide

## Overview

TRACE now integrates with the Principal Agent (ADK Framework) for AI-powered auto-remediation. When you click "Auto Remediate" in the dashboard, the request goes to the Principal Agent for intelligent analysis and action.

## Quick Start

### Option 1: Run Dashboard Only (Recommended for Demo)
```batch
start_all.bat
```
This starts:
- Dashboard Backend (Port 8000)
- React Frontend (Port 5173)

### Option 2: Run Full System with ADK Web
```batch
start_full_system.bat
```
This starts:
- Dashboard Backend (Port 8000)
- ADK Web Interface (Port 8001) - For direct agent chat
- React Frontend (Port 5173)

### Option 3: Run Individual Components
```batch
start_all.bat backend   # Backend only
start_all.bat frontend  # Frontend only
start_all.bat adk       # ADK Web only
```

## Integration Modes

The system operates in three modes based on available dependencies:

### 1. **Integrated Mode** (Best Experience)
- Requires: `google-adk` package installed
- Features: Full AI-powered remediation via Principal Agent
- Agent responses are shown in the dashboard

### 2. **Tools Only Mode**
- Requires: Principal Agent tools available
- Features: Direct tool execution (restart, redeploy, reroute)
- No natural language AI responses

### 3. **Fallback Mode**
- Default when Principal Agent not available
- Features: Simulated remediation responses
- Dashboard fully functional for demo purposes

## API Endpoints

### Remediation
- **POST** `/api/remediation/trigger`
  - Triggers AI-powered auto-remediation
  - Body: `{ issueId, action, region }`
  - Response includes `agent_response` when AI is available

### Issue Analysis
- **POST** `/api/issue/analyze`
  - Get AI analysis of an issue
  - Body: `{ issueId, issue, region }`

### Integration Status
- **GET** `/api/integration/status`
  - Check Principal Agent availability
  - Response: `{ principal_agent_available, adk_available, mode }`

## Dashboard Features

### Auto Remediate Button
When clicked:
1. Sends issue to Principal Agent
2. Agent analyzes the issue
3. Agent executes appropriate remediation
4. Response shown in dashboard notification
5. Agent response dialog shows detailed AI analysis

### Integration Status Indicator
Located in the bottom-left corner:
- 🟢 Green: Full AI integration active
- 🟠 Orange: Tools-only mode
- 🔴 Red: Fallback mode

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Dashboard (Port 5173)               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ IssueCommandCenter                                       ││
│  │   - Auto Remediate Button → API call                     ││
│  │   - Shows agent response in dialog                       ││
│  └─────────────────────────────────────────────────────────┘│
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                Dashboard Backend (Port 8000)                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ agent_integration.py                                     ││
│  │   - AgentIntegration class                               ││
│  │   - Handles all agent communication                      ││
│  │   - Fallback for offline mode                            ││
│  └─────────────────────────────────────────────────────────┘│
└──────────────────────────┬──────────────────────────────────┘
                           │ Google ADK
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Principal Agent (ADK)                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Tools: restart_agent, redeploy_agent, reroute_traffic   ││
│  │ Sub-agents: Regional Coordinator, Edge Agents           ││
│  │ AI Model: gemini-2.5-flash                              ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Agent Not Available
```
⚠️ Principal Agent not available
```
**Solution:** Install google-adk: `pip install google-adk`

### ADK Not Available
```
⚠️ Google ADK not available
```
**Solution:** Ensure you have google-adk and proper credentials set up.

### Connection Refused
Ensure both backend and frontend are running:
```batch
start_all.bat
```

## Environment Variables

Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY=your_api_key_here
```

## Files Modified for Integration

- `client/server/agent_integration.py` - New: Agent integration layer
- `client/server/dashboard_server.py` - Updated: Uses agent for remediation
- `client/src/services/api.js` - Updated: New API methods
- `client/src/components/IssueCommandCenter.jsx` - Updated: Shows agent responses
- `start_all.bat` - New: Unified start script
- `start_full_system.bat` - New: Full system with ADK web
