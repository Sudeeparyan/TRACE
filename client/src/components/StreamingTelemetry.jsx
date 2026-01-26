import { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  Grid,
  ToggleButton,
  ToggleButtonGroup,
  Chip,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import GaugeWidget from './GaugeWidget';
import { format } from 'date-fns';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import BoltIcon from '@mui/icons-material/Bolt';
import TrafficIcon from '@mui/icons-material/Traffic';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

function StreamingTelemetry({ data, region }) {
  const [metric, setMetric] = useState('all');

  const handleMetricChange = (event, newMetric) => {
    if (newMetric !== null) {
      setMetric(newMetric);
    }
  };

  const formattedData = data.map(d => ({
    ...d,
    time: format(new Date(d.timestamp || Date.now()), 'HH:mm:ss'),
  }));

  const latestData = data[data.length - 1] || {
    traffic_load: 0,
    trx_utilization: 0,
    power_draw: 0,
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <Box
          sx={{
            bgcolor: 'rgba(10, 14, 26, 0.95)',
            p: 2,
            borderRadius: 2,
            border: '1px solid rgba(0, 229, 255, 0.3)',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
          }}
        >
          <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 1 }}>
            {label}
          </Typography>
          {payload.map((entry, index) => (
            <Typography key={index} variant="body2" sx={{ color: entry.color }}>
              {entry.name}: {entry.value?.toFixed(2)}
            </Typography>
          ))}
        </Box>
      );
    }
    return null;
  };

  return (
    <Box sx={{ p: 3, height: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
            <ShowChartIcon sx={{ color: '#00e5ff' }} />
            Streaming Telemetry
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Real-time network metrics for {region}
          </Typography>
        </Box>
        <ToggleButtonGroup
          value={metric}
          exclusive
          onChange={handleMetricChange}
          size="small"
          sx={{
            '& .MuiToggleButton-root': {
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: 'text.secondary',
              px: 2,
              '&.Mui-selected': {
                bgcolor: 'rgba(0, 229, 255, 0.15)',
                color: '#00e5ff',
                borderColor: 'rgba(0, 229, 255, 0.5)',
              },
            },
          }}
        >
          <ToggleButton value="all">All</ToggleButton>
          <ToggleButton value="energy">
            <BoltIcon sx={{ fontSize: 16, mr: 0.5 }} /> Energy
          </ToggleButton>
          <ToggleButton value="congestion">
            <TrafficIcon sx={{ fontSize: 16, mr: 0.5 }} /> Traffic
          </ToggleButton>
          <ToggleButton value="anomaly">
            <WarningAmberIcon sx={{ fontSize: 16, mr: 0.5 }} /> Anomaly
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Multi-line Chart */}
      <Box sx={{ height: 280, mb: 3 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData}>
            <defs>
              <linearGradient id="energyGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00e676" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#00e676" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="congestionGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ff9100" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#ff9100" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="anomalyGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ff5252" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#ff5252" stopOpacity={0}/>
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
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              wrapperStyle={{ paddingTop: 10 }}
              formatter={(value) => <span style={{ color: 'rgba(255,255,255,0.7)' }}>{value}</span>}
            />
            {(metric === 'all' || metric === 'energy') && (
              <Line 
                type="monotone" 
                dataKey="energy" 
                stroke="#00e676" 
                strokeWidth={2}
                dot={false}
                name="Energy %"
                activeDot={{ r: 6, fill: '#00e676', stroke: '#fff', strokeWidth: 2 }}
              />
            )}
            {(metric === 'all' || metric === 'congestion') && (
              <Line 
                type="monotone" 
                dataKey="congestion" 
                stroke="#ff9100" 
                strokeWidth={2}
                dot={false}
                name="Congestion %"
                activeDot={{ r: 6, fill: '#ff9100', stroke: '#fff', strokeWidth: 2 }}
              />
            )}
            {(metric === 'all' || metric === 'anomaly') && (
              <Line 
                type="monotone" 
                dataKey="anomaly_score" 
                stroke="#ff5252" 
                strokeWidth={2}
                dot={false}
                name="Anomaly Score"
                activeDot={{ r: 6, fill: '#ff5252', stroke: '#fff', strokeWidth: 2 }}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </Box>

      {/* Gauge Widgets */}
      <Grid container spacing={2}>
        <Grid item xs={4}>
          <GaugeWidget
            title="Traffic Load"
            value={latestData.traffic_load}
            max={100}
            unit="%"
            thresholds={{ warning: 70, critical: 85 }}
            color="#00e5ff"
          />
        </Grid>
        <Grid item xs={4}>
          <GaugeWidget
            title="TRX Utilization"
            value={latestData.trx_utilization}
            max={100}
            unit="%"
            thresholds={{ warning: 75, critical: 90 }}
            color="#7c4dff"
          />
        </Grid>
        <Grid item xs={4}>
          <GaugeWidget
            title="Power Draw"
            value={latestData.power_draw}
            max={150}
            unit="kW"
            thresholds={{ warning: 100, critical: 130 }}
            color="#00e676"
          />
        </Grid>
      </Grid>
    </Box>
  );
}

export default StreamingTelemetry;
