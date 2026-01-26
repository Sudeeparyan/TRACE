# TRACE Dashboard - Quick Start Guide

## Overview
This client dashboard implements the CLIENT_DEMO_DASHBOARD.md blueprint with a React frontend and Flask backend for real-time telemetry streaming and autonomous remediation visualization.

## Project Structure

```
client/
├── src/
│   ├── components/          # React components
│   │   ├── Dashboard.jsx    # Main dashboard container
│   │   ├── HeroStrip.jsx    # Top status bar
│   │   ├── StreamingTelemetry.jsx  # Telemetry charts
│   │   ├── ActiveUsersStream.jsx   # User metrics
│   │   ├── IssueCommandCenter.jsx  # Issue cards
│   │   ├── ResolutionTimeline.jsx  # Resolution history
│   │   ├── AgentTrace.jsx   # Agent flow visualization
│   │   └── GaugeWidget.jsx  # Circular gauge
│   ├── services/
│   │   ├── websocket.js     # WebSocket client
│   │   ├── api.js           # REST API client
│   │   └── mockData.js      # Mock data generators
│   ├── App.jsx              # Root component
│   ├── main.jsx             # Entry point
│   └── index.css            # Global styles
├── server/
│   ├── dashboard_server.py  # Flask backend
│   └── requirements.txt     # Python dependencies
├── package.json             # Node dependencies
├── vite.config.js           # Vite configuration
└── index.html              # HTML template
```

## Installation

### Option 1: Quick Setup (Windows)
```bash
cd client
setup.bat
```

### Option 2: Manual Setup

1. **Install Frontend Dependencies**
   ```bash
   cd client
   npm install
   ```

2. **Install Backend Dependencies**
   ```bash
   cd client/server
   pip install -r requirements.txt
   ```

## Running the Dashboard

### Option 1: With Backend Server (Full Features)

1. **Start Backend Server** (Terminal 1)
   ```bash
   cd client
   start_server.bat
   ```
   Or manually:
   ```bash
   cd client/server
   python dashboard_server.py
   ```

2. **Start Frontend** (Terminal 2)
   ```bash
   cd client
   npm run dev
   ```

3. **Open Browser**
   Navigate to `http://localhost:3000`

### Option 2: Mock Mode (No Backend Required)

1. **Configure Mock Mode**
   Create `client/.env` file:
   ```env
   VITE_USE_MOCK=true
   ```

2. **Update Dashboard Component**
   In `src/components/Dashboard.jsx`, uncomment:
   ```javascript
   import { MockWebSocketService as WebSocketService } from '../services/mockData';
   ```

3. **Start Frontend**
   ```bash
   npm run dev
   ```

## Features Implemented

### ✅ Hero Strip (Top Bar)
- Region selector dropdown (US East, US West, EU West, AP South)
- Global health score with color-coded status
- System status indicator (Operational/Degraded/Critical)
- Last remediation summary

### ✅ Streaming Telemetry Canvas (Left 60%)
- Multi-line chart with energy, congestion, and anomaly metrics
- Toggle view filters (All, Energy, Congestion, Anomaly)
- Real-time updates every 1 second
- Three gauge widgets:
  - Traffic Load (0-100%)
  - TRX Utilization (0-100%)
  - Power Draw (0-150 kW)
- Color-coded thresholds (green/yellow/red)

### ✅ Active Users Stream (Right 40%)
- Neon-style area chart showing concurrent users
- Moving average overlay for trend analysis
- Peak and average statistics
- Surge detection indicator
- Tower cluster and optimization tooltips

### ✅ Issue Command Center (Bottom - Live Issues Tab)
- Prioritized issue cards with severity badges
- Agent trace visualization showing workflow
- "Take Action" button to trigger remediation
- "View More" modal with:
  - Detailed analysis
  - Remediation steps
  - Agent communication logs
- Auto-removal when resolved

### ✅ Resolution Timeline (Bottom - Resolution Timeline Tab)
- Chronological timeline of completed remediations
- Expandable details for each resolution:
  - Actions executed
  - Safety validations
  - Learning agent notes
  - Confidence scores

### ✅ Real-time WebSocket Streaming
- Telemetry updates every 1 second
- Active users every 2 seconds
- Health status every 5 seconds
- Random issue generation for demo

## API Endpoints

### REST API
- `GET /api/health/:region` - Get system health
- `GET /api/telemetry` - Historical telemetry data
- `GET /api/active-users/:region` - Active user metrics
- `GET /api/issues` - Get active issues
- `POST /api/remediation/trigger` - Trigger remediation
- `GET /api/resolutions` - Resolution history
- `GET /api/agents/status` - Agent status

### WebSocket Events
- `telemetry` - Real-time metrics
- `activeUsers` - User count updates
- `issue` - New issue notifications
- `resolution` - Remediation completions
- `health` - System health updates

## Customization

### Change Theme Colors
Edit `src/App.jsx`:
```javascript
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#00e5ff' },  // Cyan
    secondary: { main: '#ff1744' }, // Red
    // ... customize more colors
  },
});
```

### Add New Regions
Edit `src/components/HeroStrip.jsx`:
```javascript
const regions = [
  { id: 'us-east-1', name: 'US East (Virginia)' },
  { id: 'new-region', name: 'New Region' },
  // ... add more regions
];
```

### Modify Update Intervals
Edit `client/server/dashboard_server.py`:
```python
socketio.sleep(1)  # Change telemetry update interval
```

## Demo Presentation Flow

Follow the script from CLIENT_DEMO_DASHBOARD.md:

1. **Intro (30s)**: Show hero strip, global health
2. **Telemetry (60s)**: Zoom into charts, explain metrics
3. **Issue Center (90s)**: Trigger issue, click "Take Action", watch agents
4. **Active Users (45s)**: Highlight surge curve, explain prediction
5. **Wrap-up (30s)**: Show resolution timeline

## Integration with Existing TRACE System

To connect to your actual TRACE agents:

1. **Update WebSocket Connection**
   Modify `src/services/websocket.js` to connect to your agent system

2. **Update API Endpoints**
   Point `src/services/api.js` to your Principal Agent API

3. **Map Data Format**
   Ensure your agent output matches the expected format in components

## Troubleshooting

### Port Already in Use
```bash
# Change frontend port in vite.config.js
server: { port: 3001 }

# Change backend port in dashboard_server.py
socketio.run(app, port=8001)
```

### CORS Issues
Backend already configured with CORS. If issues persist:
```python
CORS(app, resources={r"/*": {"origins": "*"}})
```

### WebSocket Connection Failed
- Ensure backend is running on port 8000
- Check firewall settings
- Try using mock mode

### npm Install Errors
```bash
# Clear cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

## Production Build

```bash
cd client
npm run build
```

Serve the `dist/` folder with your preferred web server.

## Next Steps

- Integrate with real TRACE agent system
- Add authentication and user management
- Implement data persistence
- Add more visualization options
- Create mobile-responsive views
- Add export/reporting features

## Support

Refer to:
- `CLIENT_DEMO_DASHBOARD.md` - Original blueprint
- `client/README.md` - Detailed documentation
- Component files - Inline comments and documentation
