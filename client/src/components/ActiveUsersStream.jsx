import {
  Paper,
  Typography,
  Box,
  Tooltip,
  Chip,
} from '@mui/material';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from 'recharts';
import { format } from 'date-fns';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import PeopleIcon from '@mui/icons-material/People';
import BoltIcon from '@mui/icons-material/Bolt';

function ActiveUsersStream({ data, region }) {
  const formattedData = data.map(d => ({
    ...d,
    time: format(new Date(d.timestamp || Date.now()), 'HH:mm:ss'),
  }));

  // Calculate moving average
  const dataWithAverage = formattedData.map((d, idx) => {
    const start = Math.max(0, idx - 4);
    const slice = formattedData.slice(start, idx + 1);
    const avg = slice.reduce((sum, item) => sum + (item.activeUsers || 0), 0) / slice.length;
    return { ...d, movingAverage: avg };
  });

  const latestData = data[data.length - 1] || { activeUsers: 0 };
  const previousData = data[data.length - 2] || { activeUsers: 0 };
  const trend = latestData.activeUsers - previousData.activeUsers;
  const trendPercentage = previousData.activeUsers > 0 
    ? ((trend / previousData.activeUsers) * 100).toFixed(1) 
    : 0;

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const tooltipData = payload[0].payload;
      return (
        <Box
          sx={{
            bgcolor: 'rgba(10, 14, 26, 0.95)',
            p: 2,
            borderRadius: 2,
            border: '1px solid rgba(0, 229, 255, 0.3)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
            minWidth: 180,
          }}
        >
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
            {tooltipData.time}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <PeopleIcon sx={{ color: '#00e5ff', fontSize: 18 }} />
            <Typography variant="body1" sx={{ color: '#00e5ff', fontWeight: 600 }}>
              {tooltipData.activeUsers?.toLocaleString() || 0}
            </Typography>
          </Box>
          <Typography variant="caption" color="text.secondary" display="block">
            Tower: {tooltipData.towerCluster || 'N/A'}
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block">
            Optimization: {tooltipData.lastOptimization || 'None'}
          </Typography>
          {tooltipData.surgeDetected && (
            <Chip 
              label="Surge Detected" 
              size="small" 
              color="warning" 
              sx={{ mt: 1, fontSize: '0.7rem' }}
            />
          )}
        </Box>
      );
    }
    return null;
  };

  const peakUsers = Math.max(...data.map(d => d.activeUsers || 0), 0);
  const avgUsers = data.length > 0 
    ? Math.round(data.reduce((sum, d) => sum + (d.activeUsers || 0), 0) / data.length)
    : 0;

  return (
    <Box sx={{ p: 3, height: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
            <PeopleIcon sx={{ color: '#7c4dff' }} />
            Active Users
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Real-time concurrent subscribers • {region}
          </Typography>
        </Box>
        <Box sx={{ textAlign: 'right' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, justifyContent: 'flex-end' }}>
            {trend >= 0 ? (
              <TrendingUpIcon sx={{ color: '#00e676', fontSize: 28 }} />
            ) : (
              <TrendingDownIcon sx={{ color: '#ff5252', fontSize: 28 }} />
            )}
            <Typography 
              variant="h4" 
              sx={{ 
                fontWeight: 700,
                color: trend >= 0 ? '#00e676' : '#ff5252',
              }}
            >
              {latestData.activeUsers?.toLocaleString() || 0}
            </Typography>
          </Box>
          <Typography 
            variant="caption" 
            sx={{ 
              color: trend >= 0 ? '#00e676' : '#ff5252',
              fontWeight: 500,
            }}
          >
            {trend >= 0 ? '+' : ''}{trendPercentage}% vs last
          </Typography>
        </Box>
      </Box>

      <Box sx={{ height: 320 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={dataWithAverage}>
            <defs>
              <linearGradient id="colorUsersGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#00e5ff" stopOpacity={0.4} />
                <stop offset="50%" stopColor="#7c4dff" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#7c4dff" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorAverageGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ff9100" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ff9100" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis 
              dataKey="time" 
              stroke="rgba(255,255,255,0.3)"
              tick={{ fontSize: 11, fill: 'rgba(255,255,255,0.5)' }}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            />
            <YAxis 
              stroke="rgba(255,255,255,0.3)"
              tick={{ fontSize: 11, fill: 'rgba(255,255,255,0.5)' }}
              tickFormatter={(value) => value >= 1000 ? `${(value/1000).toFixed(0)}k` : value}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            />
            <RechartsTooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="activeUsers"
              stroke="#00e5ff"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorUsersGradient)"
            />
            <Area
              type="monotone"
              dataKey="movingAverage"
              stroke="#ff9100"
              strokeWidth={1.5}
              strokeDasharray="5 5"
              fillOpacity={0.3}
              fill="url(#colorAverageGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </Box>

      {/* Stats Row */}
      <Box 
        sx={{ 
          mt: 3, 
          display: 'grid', 
          gridTemplateColumns: 'repeat(3, 1fr)', 
          gap: 2,
        }}
      >
        <Box 
          sx={{ 
            p: 2, 
            bgcolor: 'rgba(0, 229, 255, 0.1)', 
            borderRadius: 2,
            border: '1px solid rgba(0, 229, 255, 0.2)',
            textAlign: 'center',
          }}
        >
          <Typography variant="caption" color="text.secondary" display="block">
            Peak Today
          </Typography>
          <Typography variant="h6" sx={{ color: '#00e5ff', fontWeight: 600 }}>
            {peakUsers.toLocaleString()}
          </Typography>
        </Box>
        <Box 
          sx={{ 
            p: 2, 
            bgcolor: 'rgba(255, 145, 0, 0.1)', 
            borderRadius: 2,
            border: '1px solid rgba(255, 145, 0, 0.2)',
            textAlign: 'center',
          }}
        >
          <Typography variant="caption" color="text.secondary" display="block">
            Average
          </Typography>
          <Typography variant="h6" sx={{ color: '#ff9100', fontWeight: 600 }}>
            {avgUsers.toLocaleString()}
          </Typography>
        </Box>
        <Box 
          sx={{ 
            p: 2, 
            bgcolor: latestData.surgeDetected 
              ? 'rgba(255, 82, 82, 0.1)' 
              : 'rgba(0, 230, 118, 0.1)', 
            borderRadius: 2,
            border: latestData.surgeDetected 
              ? '1px solid rgba(255, 82, 82, 0.2)'
              : '1px solid rgba(0, 230, 118, 0.2)',
            textAlign: 'center',
          }}
        >
          <Typography variant="caption" color="text.secondary" display="block">
            AI Status
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
            <BoltIcon sx={{ 
              fontSize: 18, 
              color: latestData.surgeDetected ? '#ff5252' : '#00e676' 
            }} />
            <Typography 
              variant="body2" 
              sx={{ 
                color: latestData.surgeDetected ? '#ff5252' : '#00e676',
                fontWeight: 600,
              }}
            >
              {latestData.surgeDetected ? 'Surge Alert' : 'Optimized'}
            </Typography>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

export default ActiveUsersStream;
