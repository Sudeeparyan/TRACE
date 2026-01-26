import {
  Box,
  Paper,
  Typography,
  FormControl,
  Select,
  MenuItem,
  Chip,
  Grid,
  LinearProgress,
} from '@mui/material';
import SignalCellularAltIcon from '@mui/icons-material/SignalCellularAlt';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import SpeedIcon from '@mui/icons-material/Speed';
import SecurityIcon from '@mui/icons-material/Security';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';

const regions = [
  { id: 'us-east-1', name: 'US East (Virginia)', flag: '🇺🇸' },
  { id: 'us-west-2', name: 'US West (Oregon)', flag: '🇺🇸' },
  { id: 'eu-west-1', name: 'EU West (Ireland)', flag: '🇪🇺' },
  { id: 'ap-south-1', name: 'AP South (Mumbai)', flag: '🇮🇳' },
];

function HeroStrip({ selectedRegion, onRegionChange, globalHealth, systemStatus, lastRemediation }) {
  const getHealthColor = () => {
    if (globalHealth >= 90) return 'success';
    if (globalHealth >= 70) return 'warning';
    return 'error';
  };

  const getHealthGradient = () => {
    if (globalHealth >= 90) return 'linear-gradient(135deg, #00e676 0%, #00c853 100%)';
    if (globalHealth >= 70) return 'linear-gradient(135deg, #ff9100 0%, #ff6d00 100%)';
    return 'linear-gradient(135deg, #ff5252 0%, #d50000 100%)';
  };

  const getStatusIcon = () => {
    if (systemStatus === 'Operational' || systemStatus === 'Healthy') return <CheckCircleIcon />;
    if (systemStatus === 'Degraded') return <WarningIcon />;
    return <ErrorIcon />;
  };

  return (
    <Paper 
      sx={{ 
        p: 3, 
        background: 'linear-gradient(135deg, rgba(20, 30, 60, 0.95) 0%, rgba(30, 45, 90, 0.95) 100%)',
        backdropFilter: 'blur(20px)',
        borderRadius: 3,
        border: '1px solid rgba(255, 255, 255, 0.1)',
        mx: 3,
        mt: 3,
        boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)',
      }}
    >
      <Grid container spacing={3} alignItems="center">
        {/* Region Selector */}
        <Grid item xs={12} md={3}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
            <SignalCellularAltIcon sx={{ color: '#00e5ff', fontSize: 28 }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Network Region
            </Typography>
          </Box>
          <FormControl size="small" fullWidth>
            <Select
              value={selectedRegion}
              onChange={(e) => onRegionChange(e.target.value)}
              sx={{ 
                bgcolor: 'rgba(0, 0, 0, 0.2)',
                borderRadius: 2,
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255, 255, 255, 0.1)',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(0, 229, 255, 0.5)',
                },
              }}
            >
              {regions.map((region) => (
                <MenuItem key={region.id} value={region.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <span>{region.flag}</span>
                    <span>{region.name}</span>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        {/* Global Health Score */}
        <Grid item xs={12} md={3}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
            <SpeedIcon sx={{ color: '#7c4dff', fontSize: 28 }} />
            <Typography variant="body2" color="text.secondary">
              Global Health Score
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ position: 'relative', display: 'inline-flex' }}>
              <Box
                sx={{
                  width: 70,
                  height: 70,
                  borderRadius: '50%',
                  background: getHealthGradient(),
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: globalHealth >= 90 
                    ? '0 0 20px rgba(0, 230, 118, 0.5)' 
                    : globalHealth >= 70 
                    ? '0 0 20px rgba(255, 145, 0, 0.5)'
                    : '0 0 20px rgba(255, 82, 82, 0.5)',
                }}
              >
                <Typography variant="h5" sx={{ fontWeight: 700, color: 'white' }}>
                  {globalHealth}
                </Typography>
              </Box>
            </Box>
            <Box>
              <Chip 
                label={systemStatus} 
                color={getHealthColor()} 
                icon={getStatusIcon()}
                size="small"
                sx={{ 
                  fontWeight: 600,
                  '& .MuiChip-icon': { fontSize: 18 }
                }}
              />
              <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 0.5 }}>
                All systems nominal
              </Typography>
            </Box>
          </Box>
        </Grid>

        {/* AI Status */}
        <Grid item xs={12} md={3}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
            <SecurityIcon sx={{ color: '#00e676', fontSize: 28 }} />
            <Typography variant="body2" color="text.secondary">
              AI Agents Status
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box className="status-online" />
              <Typography variant="body2">Principal Agent</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box className="status-online" />
              <Typography variant="body2">5 Edge Agents Active</Typography>
            </Box>
          </Box>
        </Grid>

        {/* Last Remediation */}
        <Grid item xs={12} md={3}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
            <AutoFixHighIcon sx={{ color: '#ff9100', fontSize: 28 }} />
            <Typography variant="body2" color="text.secondary">
              Last Auto-Remediation
            </Typography>
          </Box>
          <Typography 
            variant="body2" 
            sx={{ 
              p: 1.5,
              bgcolor: 'rgba(255, 145, 0, 0.1)',
              borderRadius: 2,
              border: '1px solid rgba(255, 145, 0, 0.2)',
              lineHeight: 1.5,
            }}
          >
            {lastRemediation || 'No recent actions'}
          </Typography>
        </Grid>
      </Grid>
    </Paper>
  );
}

export default HeroStrip;
