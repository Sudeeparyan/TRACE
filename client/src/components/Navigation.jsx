import { AppBar, Toolbar, Tabs, Tab, Box, Typography, Chip } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import HubIcon from '@mui/icons-material/Hub';

function Navigation() {
  const navigate = useNavigate();
  const location = useLocation();

  const currentTab = location.pathname === '/chat' ? 1 : 0;

  const handleTabChange = (event, newValue) => {
    if (newValue === 0) {
      navigate('/');
    } else if (newValue === 1) {
      navigate('/chat');
    }
  };

  return (
    <AppBar 
      position="sticky" 
      sx={{ 
        bgcolor: 'rgba(10, 14, 26, 0.9)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        boxShadow: '0 4px 30px rgba(0, 0, 0, 0.3)',
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between' }}>
        {/* Logo & Brand */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              width: 42,
              height: 42,
              borderRadius: 2,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)',
            }}
          >
            <HubIcon sx={{ color: 'white', fontSize: 24 }} />
          </Box>
          <Box>
            <Typography 
              variant="h6" 
              sx={{ 
                fontWeight: 700,
                background: 'linear-gradient(90deg, #00e5ff, #7c4dff)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                lineHeight: 1.2,
              }}
            >
              TRACE
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
              Telecom AI Operations
            </Typography>
          </Box>
        </Box>

        {/* Navigation Tabs */}
        <Tabs 
          value={currentTab} 
          onChange={handleTabChange}
          textColor="primary"
          indicatorColor="primary"
          sx={{
            '& .MuiTabs-indicator': {
              height: 3,
              borderRadius: '3px 3px 0 0',
              background: 'linear-gradient(90deg, #00e5ff, #7c4dff)',
            },
          }}
        >
          <Tab 
            icon={<DashboardIcon />} 
            label="Dashboard" 
            iconPosition="start"
            sx={{ 
              minHeight: 64,
              px: 3,
              '&.Mui-selected': {
                color: '#00e5ff',
              },
            }}
          />
          <Tab 
            icon={<SmartToyIcon />} 
            label="AI Agent" 
            iconPosition="start"
            sx={{ 
              minHeight: 64,
              px: 3,
              '&.Mui-selected': {
                color: '#00e5ff',
              },
            }}
          />
        </Tabs>

        {/* Status Badge */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip
            icon={<Box className="status-online" sx={{ ml: 1 }} />}
            label="System Online"
            size="small"
            sx={{
              bgcolor: 'rgba(0, 230, 118, 0.1)',
              border: '1px solid rgba(0, 230, 118, 0.3)',
              color: '#00e676',
              fontWeight: 500,
            }}
          />
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default Navigation;
