# TRACE Demo Dashboard - Client

React-based real-time dashboard for TRACE telemetry visualization and autonomous remediation demonstration.

## Features

- **Real-time Telemetry Streaming**: Live visualization of energy, congestion, and anomaly metrics
- **Active Users Monitoring**: Neon-style area chart with predictive surge detection
- **Issue Command Center**: Automated issue detection with agent trace visualization
- **Resolution Timeline**: Historical view of automated remediations
- **Multi-Agent Architecture Display**: Visual representation of agent interactions

## Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000` (or configure via environment variables)

## Installation

```bash
cd client
npm install
```

## Configuration

Create a `.env` file in the client directory:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## Development

Start the development server:

```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`

## Mock Mode

If the backend is not available, the dashboard will use mock data generators to simulate real-time streaming. This is useful for demos and development.

## Build for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

## Dashboard Components

### Hero Strip
- Region selector
- Global health score with color-coded status
- System status indicator
- Last remediation summary

### Streaming Telemetry Canvas
- Multi-line chart for energy, congestion, and anomaly signals
- Toggle between metric views
- Gauge widgets for traffic load, TRX utilization, and power draw
- Color-coded thresholds

### Active Users Stream
- Real-time concurrent subscribers graph
- Moving average overlay
- Peak and average statistics
- Surge detection indicator

### Issue Command Center
- Live issues grid with severity color coding
- Agent trace visualization
- "Take Action" and "View More" controls
- Detailed modal with remediation steps and agent logs

### Resolution Timeline
- Chronological view of completed remediations
- Expandable details for each resolution
- Safety validations and learning notes

## Technology Stack

- **React 18**: UI framework
- **Material-UI (MUI)**: Component library
- **Recharts**: Data visualization
- **Socket.IO**: WebSocket client
- **Vite**: Build tool
- **Axios**: HTTP client

## Integration with Backend

The dashboard expects the following WebSocket events:

- `telemetry`: Real-time metrics
- `activeUsers`: User count updates
- `issue`: New issue notifications
- `resolution`: Remediation completions
- `health`: System health updates

API endpoints:

- `GET /api/telemetry`: Historical telemetry data
- `GET /api/issues`: Active issues list
- `POST /api/remediation/trigger`: Trigger remediation action
- `GET /api/resolutions`: Resolution history
- `GET /api/health/:region`: Regional health status

## Demo Mode

For presentations without live data, uncomment the mock service import in `Dashboard.jsx`:

```javascript
import { MockWebSocketService as WebSocketService } from '../services/mockData';
```

This will generate synthetic data streams that demonstrate all dashboard features.

## Customization

### Theme Colors
Edit `src/App.jsx` to modify the Material-UI theme configuration.

### Chart Styles
Customize chart appearance in individual component files under `src/components/`.

### WebSocket Configuration
Modify `src/services/websocket.js` for custom connection logic.

## Troubleshooting

### WebSocket Connection Failed
- Ensure backend is running
- Check CORS configuration on backend
- Verify WebSocket URL in environment variables

### Chart Not Rendering
- Check browser console for errors
- Ensure data format matches component expectations
- Verify Recharts is properly installed

### Styling Issues
- Clear browser cache
- Rebuild with `npm run build`
- Check Material-UI version compatibility

## License

Part of the TRACE project.
