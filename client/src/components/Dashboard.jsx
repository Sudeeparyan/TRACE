import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Tab,
  Tabs,
  Typography,
  Fade,
} from '@mui/material';
import HeroStrip from './HeroStrip';
import StreamingTelemetry from './StreamingTelemetry';
import ActiveUsersStream from './ActiveUsersStream';
import IssueCommandCenter from './IssueCommandCenter';
import ResolutionTimeline from './ResolutionTimeline';
import { WebSocketService } from '../services/websocket';
import { dashboardAPI } from '../services/api';

console.log('Dashboard.jsx: Module loaded');

function Dashboard() {
  console.log('Dashboard: Component rendering...');
  
  const [selectedRegion, setSelectedRegion] = useState('us-east-1');
  const [telemetryData, setTelemetryData] = useState([]);
  const [activeUsers, setActiveUsers] = useState([]);
  const [issues, setIssues] = useState([]);
  const [resolutions, setResolutions] = useState([]);
  const [globalHealth, setGlobalHealth] = useState(95);
  const [systemStatus, setSystemStatus] = useState('Operational');
  const [lastRemediation, setLastRemediation] = useState('No recent actions');
  const [activeTab, setActiveTab] = useState(0);
  const [isConnected, setIsConnected] = useState(false);

  // Fetch initial issues from API
  const fetchInitialIssues = useCallback(async (region) => {
    try {
      const response = await dashboardAPI.getIssues(region);
      const fetchedIssues = response.data || [];
      console.log('Dashboard: Fetched initial issues:', fetchedIssues.length);
      setIssues(fetchedIssues.filter(i => i.status !== 'Resolved'));
    } catch (error) {
      console.error('Dashboard: Failed to fetch initial issues:', error);
    }
  }, []);

  useEffect(() => {
    console.log('Dashboard: useEffect - Initializing WebSocket...');
    const ws = WebSocketService.getInstance();
    
    try {
      ws.connect(() => {
        console.log('Dashboard: WebSocket connected successfully');
        setIsConnected(true);
        ws.subscribeToRegion(selectedRegion);
        // Fetch initial issues after connection
        fetchInitialIssues(selectedRegion);
      });

      ws.on('telemetry', (data) => {
        console.log('Dashboard: Received telemetry data', data);
        setTelemetryData(prev => [...prev.slice(-100), data]);
      });

      ws.on('activeUsers', (data) => {
        console.log('Dashboard: Received activeUsers data', data);
        setActiveUsers(prev => [...prev.slice(-60), data]);
      });

      ws.on('issue', (data) => {
        console.log('Dashboard: Received issue', data);
        // Deduplicate: only add if not already present (by id or title)
        setIssues(prev => {
          const exists = prev.some(i => i.id === data.id || i.title === data.title);
          if (exists || data.status === 'Resolved') {
            return prev;
          }
          return [data, ...prev];
        });
      });

      ws.on('resolution', (data) => {
        console.log('Dashboard: Received resolution', data);
        setResolutions(prev => [data, ...prev]);
        setLastRemediation(data.summary);
        // Remove resolved issue from active issues
        if (data.issueId) {
          setIssues(prev => prev.filter(i => i.id !== data.issueId));
        }
      });

      ws.on('health', (data) => {
        console.log('Dashboard: Received health data', data);
        setGlobalHealth(data.score);
        setSystemStatus(data.status);
      });

      return () => {
        console.log('Dashboard: Cleaning up WebSocket...');
        ws.disconnect();
      };
    } catch (error) {
      console.error('Dashboard: Error setting up WebSocket:', error);
    }
  }, [selectedRegion, fetchInitialIssues]);

  const handleRegionChange = (region) => {
    setSelectedRegion(region);
    const ws = WebSocketService.getInstance();
    ws.subscribeToRegion(region);
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <Box 
      sx={{ 
        minHeight: '100vh', 
        bgcolor: 'transparent',
        pb: 4,
        background: 'radial-gradient(ellipse at top, rgba(102, 126, 234, 0.08) 0%, transparent 50%)',
      }}
    >
      {/* Hero Strip */}
      <Fade in={true} timeout={800}>
        <Box>
          <HeroStrip
            selectedRegion={selectedRegion}
            onRegionChange={handleRegionChange}
            globalHealth={globalHealth}
            systemStatus={systemStatus}
            lastRemediation={lastRemediation}
          />
        </Box>
      </Fade>
      
      <Container maxWidth="xl" sx={{ mt: 3 }}>
        <Grid container spacing={3}>
          {/* Streaming Telemetry - Left 60% */}
          <Grid item xs={12} lg={7}>
            <Fade in={true} timeout={1000}>
              <Paper 
                sx={{ 
                  p: 0, 
                  height: '100%',
                  background: 'linear-gradient(135deg, rgba(20, 30, 60, 0.9) 0%, rgba(25, 35, 70, 0.9) 100%)',
                  borderRadius: 3,
                  overflow: 'hidden',
                }}
              >
                <StreamingTelemetry data={telemetryData} region={selectedRegion} />
              </Paper>
            </Fade>
          </Grid>

          {/* Active Users Stream - Right 40% */}
          <Grid item xs={12} lg={5}>
            <Fade in={true} timeout={1200}>
              <Paper 
                sx={{ 
                  p: 0, 
                  height: '100%',
                  background: 'linear-gradient(135deg, rgba(20, 30, 60, 0.9) 0%, rgba(25, 35, 70, 0.9) 100%)',
                  borderRadius: 3,
                  overflow: 'hidden',
                }}
              >
                <ActiveUsersStream data={activeUsers} region={selectedRegion} />
              </Paper>
            </Fade>
          </Grid>

          {/* Issue Command Center - Bottom Full Width */}
          <Grid item xs={12}>
            <Fade in={true} timeout={1400}>
              <Paper 
                sx={{ 
                  p: 3,
                  background: 'linear-gradient(135deg, rgba(20, 30, 60, 0.9) 0%, rgba(25, 35, 70, 0.9) 100%)',
                  borderRadius: 3,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Typography 
                    variant="h5" 
                    sx={{ 
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                    }}
                  >
                    🎯 Issue Command Center
                  </Typography>
                  <Tabs 
                    value={activeTab} 
                    onChange={handleTabChange}
                    sx={{
                      '& .MuiTabs-indicator': {
                        height: 3,
                        borderRadius: 2,
                        background: 'linear-gradient(90deg, #00e5ff, #7c4dff)',
                      },
                    }}
                  >
                    <Tab 
                      label="Live Issues" 
                      sx={{ 
                        fontWeight: 600,
                        '&.Mui-selected': { color: '#00e5ff' }
                      }}
                    />
                    <Tab 
                      label="Resolution Timeline" 
                      sx={{ 
                        fontWeight: 600,
                        '&.Mui-selected': { color: '#00e5ff' }
                      }}
                    />
                  </Tabs>
                </Box>

                {activeTab === 0 && (
                  <IssueCommandCenter 
                    issues={issues} 
                    onIssueResolved={(issueId) => {
                      setIssues(prev => prev.filter(i => i.id !== issueId));
                    }}
                  />
                )}

                {activeTab === 1 && (
                  <ResolutionTimeline resolutions={resolutions} />
                )}
              </Paper>
            </Fade>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default Dashboard;
