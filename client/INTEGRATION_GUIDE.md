# Integration Guide: Connecting Dashboard to TRACE Agents

This guide explains how to integrate the React dashboard with your existing TRACE multi-agent system.

## Architecture Overview

```
Principal Agent (Python)
    ↓ WebSocket/REST API
Dashboard Backend (Flask)
    ↓ WebSocket
Dashboard Frontend (React)
```

## Step 1: Expose Principal Agent API

Add these endpoints to your `principal_agent/agent.py`:

```python
from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/api/telemetry', methods=['GET'])
def get_telemetry():
    """Get telemetry from monitoring agent"""
    # Use your existing monitoring agent tool
    from tools.json_data_processor import process_telemetry
    data = process_telemetry()
    return jsonify(data)

@app.route('/api/remediation/trigger', methods=['POST'])
def trigger_remediation():
    """Trigger remediation through Principal Agent"""
    data = request.json
    issue_id = data['issueId']
    action = data['action']
    
    # Call your existing remediation tools
    from tools.remediation import execute_remediation
    result = execute_remediation(issue_id, action)
    
    # Emit resolution event
    socketio.emit('resolution', {
        'id': f'resolution-{time.time()}',
        'timestamp': datetime.now().isoformat(),
        'summary': result['message'],
    })
    
    return jsonify(result)

# Stream telemetry to dashboard
def stream_telemetry():
    while True:
        socketio.sleep(1)
        # Get data from your monitoring agent
        telemetry = get_latest_telemetry()
        socketio.emit('telemetry', telemetry)
```

## Step 2: Update Dashboard WebSocket Service

Modify `client/src/services/websocket.js`:

```javascript
connect(onConnect) {
  // Connect to your Principal Agent API
  this.socket = io('http://your-principal-agent:5000', {
    transports: ['websocket'],
    reconnection: true,
  });
  
  // ... rest of the code
}
```

## Step 3: Map Your Data Format

Update components to match your data structure. Example for telemetry:

### Your TRACE Data Format:
```json
{
  "tower_id": "Tower-123",
  "metrics": {
    "energy_consumption": 85.5,
    "congestion_level": 45.2,
    "anomaly_detected": false
  }
}
```

### Dashboard Expected Format:
```json
{
  "timestamp": "2024-11-16T10:30:00",
  "energy": 85.5,
  "congestion": 45.2,
  "anomaly_score": 0,
  "traffic_load": 50,
  "trx_utilization": 60,
  "power_draw": 85.5
}
```

### Create Data Mapper:

Create `client/src/services/dataMapper.js`:

```javascript
export const mapTelemetryData = (traceData) => {
  return {
    timestamp: new Date().toISOString(),
    energy: traceData.metrics.energy_consumption,
    congestion: traceData.metrics.congestion_level,
    anomaly_score: traceData.metrics.anomaly_detected ? 100 : 0,
    traffic_load: traceData.metrics.congestion_level,
    trx_utilization: traceData.metrics.trx_usage || 0,
    power_draw: traceData.metrics.energy_consumption,
  };
};

export const mapIssueData = (traceIssue) => {
  return {
    id: traceIssue.issue_id,
    title: traceIssue.description,
    severity: traceIssue.priority.toLowerCase(),
    description: traceIssue.details,
    affectedTowers: traceIssue.affected_resources,
    impactScore: `${traceIssue.impact_percentage}%`,
    status: 'Active',
    agentTrace: traceIssue.agent_chain || [],
    activeAgent: traceIssue.current_agent,
    suggestedAction: traceIssue.recommended_action,
  };
};
```

Use in components:

```javascript
import { mapTelemetryData } from '../services/dataMapper';

ws.on('telemetry', (data) => {
  const mappedData = mapTelemetryData(data);
  setTelemetryData(prev => [...prev.slice(-100), mappedData]);
});
```

## Step 4: Connect to Your RAG System

Integrate with your existing RAG processor:

```python
# In principal_agent/agent.py

from tools.rag_file_processor import query_rag_system

@app.route('/api/issues/analyze', methods=['POST'])
def analyze_issue():
    """Use RAG to analyze issue context"""
    issue_description = request.json['description']
    
    # Query your RAG system
    context = query_rag_system(issue_description)
    
    return jsonify({
        'context': context,
        'recommendations': extract_recommendations(context),
        'similar_cases': find_similar_cases(context),
    })
```

Update `IssueCommandCenter.jsx`:

```javascript
const handleViewMore = async (issue) => {
  // Fetch additional context from RAG
  const response = await dashboardAPI.analyzeIssue(issue.description);
  setSelectedIssue({
    ...issue,
    ragContext: response.data.context,
    recommendations: response.data.recommendations,
  });
  setDialogOpen(true);
};
```

## Step 5: Agent Communication Flow

Display real agent interactions:

```python
# In your agent communication code
def agent_communicate(sender, receiver, message):
    """Log agent communication for dashboard"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'sender': sender,
        'receiver': receiver,
        'message': message,
        'type': 'agent_communication'
    }
    
    # Emit to dashboard
    socketio.emit('agent_log', log_entry)
    
    # Continue with your existing logic
    execute_communication(sender, receiver, message)
```

Capture in dashboard:

```javascript
ws.on('agent_log', (log) => {
  setAgentLogs(prev => [...prev, log]);
});
```

## Step 6: Use Real JSON Data

Load your `data/trace_reduced_20.json`:

```python
import json

# In dashboard_server.py
def load_trace_data():
    with open('../data/trace_reduced_20.json', 'r') as f:
        return json.load(f)

@app.route('/api/historical-data', methods=['GET'])
def get_historical_data():
    """Serve actual TRACE data"""
    data = load_trace_data()
    # Transform to dashboard format
    formatted = [format_trace_record(record) for record in data]
    return jsonify(formatted)
```

## Step 7: Health Monitor Integration

Connect to your health monitor:

```python
from tools.health_monitor import get_system_health

@app.route('/api/health/<region>', methods=['GET'])
def get_health(region):
    health_data = get_system_health(region)
    return jsonify({
        'score': health_data.overall_score,
        'status': health_data.status_label,
        'details': health_data.component_health,
    })
```

## Step 8: Testing Integration

Create an integration test:

```python
# test_dashboard_integration.py

import requests
import json

def test_dashboard_api():
    base_url = 'http://localhost:8000'
    
    # Test telemetry endpoint
    response = requests.get(f'{base_url}/api/telemetry')
    assert response.status_code == 200
    
    # Test remediation trigger
    response = requests.post(
        f'{base_url}/api/remediation/trigger',
        json={'issueId': 'test-123', 'action': 'restart_agent'}
    )
    assert response.status_code == 200
    
    print('✓ All dashboard API tests passed')

if __name__ == '__main__':
    test_dashboard_api()
```

## Step 9: Environment Configuration

Update `.env` for production:

```env
# Backend configuration
PRINCIPAL_AGENT_URL=http://your-agent-host:5000
RAG_SYSTEM_URL=http://your-rag-host:8080
DATABASE_URL=postgresql://user:pass@host:5432/trace

# Frontend configuration
VITE_API_URL=http://your-backend:8000
VITE_WS_URL=ws://your-backend:8000
```

## Step 10: Deployment

### Option A: Run with existing TRACE system

```bash
# Start your TRACE agents
cd trace_aws_production
python chat_with_agent.py

# Start dashboard backend (integrated)
cd ../client/server
python dashboard_server.py

# Start dashboard frontend
cd ..
npm run dev
```

### Option B: Standalone deployment

```bash
# Build frontend
cd client
npm run build

# Serve with backend
python dashboard_server.py --serve-static
```

## Common Integration Patterns

### Pattern 1: Event-Driven Updates
```python
# When agent detects anomaly
def on_anomaly_detected(anomaly):
    socketio.emit('issue', {
        'id': anomaly.id,
        'title': f'{anomaly.type} Detected',
        'severity': anomaly.severity,
        # ... map rest of fields
    })
```

### Pattern 2: Request-Response
```javascript
const triggerRemediation = async (issueId) => {
  const response = await fetch('/api/remediation/trigger', {
    method: 'POST',
    body: JSON.stringify({ issueId }),
  });
  return response.json();
};
```

### Pattern 3: Polling Fallback
```javascript
// If WebSocket unavailable
const pollTelemetry = () => {
  setInterval(async () => {
    const data = await dashboardAPI.getTelemetry(region);
    setTelemetryData(data);
  }, 1000);
};
```

## Troubleshooting Integration

### Issue: Data format mismatch
**Solution**: Use dataMapper.js to transform data

### Issue: CORS errors
**Solution**: Add to Principal Agent:
```python
CORS(app, resources={r"/*": {"origins": "*"}})
```

### Issue: WebSocket disconnects
**Solution**: Implement reconnection logic
```javascript
socket.on('disconnect', () => {
  setTimeout(() => socket.connect(), 1000);
});
```

## Next Steps

1. Test with mock data first
2. Gradually replace mock endpoints with real agent APIs
3. Monitor performance and optimize queries
4. Add authentication layer
5. Implement data persistence
6. Scale horizontally as needed

## Support

- Check `client/QUICKSTART.md` for setup
- See component files for data format examples
- Review `principal_agent/` for agent integration points
