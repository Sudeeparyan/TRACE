import { Box, Typography, Paper } from '@mui/material';

function GaugeWidget({ title, value, max, unit, thresholds, color = '#00e5ff' }) {
  const percentage = (value / max) * 100;
  
  const getColor = () => {
    if (percentage >= (thresholds.critical / max) * 100) return '#ff5252';
    if (percentage >= (thresholds.warning / max) * 100) return '#ff9100';
    return color;
  };

  const displayColor = getColor();
  const circumference = 2 * Math.PI * 45;
  const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`;

  return (
    <Paper 
      sx={{ 
        p: 2, 
        textAlign: 'center',
        background: 'rgba(0, 0, 0, 0.2)',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        borderRadius: 2,
        transition: 'all 0.3s ease',
        '&:hover': {
          borderColor: `${displayColor}40`,
          boxShadow: `0 0 20px ${displayColor}20`,
        },
      }}
    >
      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
        {title}
      </Typography>
      
      <Box sx={{ position: 'relative', display: 'inline-flex', my: 2 }}>
        <svg width="100" height="100" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="rgba(255, 255, 255, 0.1)"
            strokeWidth="8"
          />
          {/* Glow effect */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke={displayColor}
            strokeWidth="8"
            strokeDasharray={strokeDasharray}
            strokeLinecap="round"
            transform="rotate(-90 50 50)"
            style={{
              transition: 'stroke-dasharray 0.5s ease, stroke 0.3s ease',
              filter: `drop-shadow(0 0 6px ${displayColor})`,
            }}
          />
          {/* Inner glow circle */}
          <circle
            cx="50"
            cy="50"
            r="35"
            fill={`${displayColor}10`}
          />
        </svg>
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography 
            variant="h5" 
            component="div" 
            sx={{ 
              fontWeight: 700,
              color: displayColor,
              textShadow: `0 0 10px ${displayColor}50`,
            }}
          >
            {value?.toFixed(1) || '0.0'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {unit}
          </Typography>
        </Box>
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mt: 1 }}>
        <Typography variant="caption" color="text.secondary">
          0
        </Typography>
        <Box sx={{ flex: 1, height: 4, bgcolor: 'rgba(255,255,255,0.1)', borderRadius: 2, position: 'relative' }}>
          <Box 
            sx={{ 
              position: 'absolute',
              left: 0,
              top: 0,
              height: '100%',
              width: `${percentage}%`,
              bgcolor: displayColor,
              borderRadius: 2,
              transition: 'width 0.5s ease',
              boxShadow: `0 0 8px ${displayColor}`,
            }}
          />
        </Box>
        <Typography variant="caption" color="text.secondary">
          {max}
        </Typography>
      </Box>
    </Paper>
  );
}

export default GaugeWidget;
