import { Box, Chip } from '@mui/material';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

const agentColors = {
  'Monitoring': '#00e676',
  'Prediction': '#00e5ff',
  'Decision xApp': '#ffd740',
  'Action': '#ff5252',
  'Learning': '#ab47bc',
};

function AgentTrace({ agents = [], activeAgent }) {
  const defaultAgents = ['Monitoring', 'Prediction', 'Decision xApp', 'Action', 'Learning'];
  const displayAgents = agents.length > 0 ? agents : defaultAgents;

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.5, my: 1 }}>
      {displayAgents.map((agent, idx) => (
        <Box key={idx} sx={{ display: 'flex', alignItems: 'center' }}>
          <Chip
            label={agent}
            size="small"
            sx={{
              bgcolor: activeAgent === agent ? agentColors[agent] : 'transparent',
              borderColor: agentColors[agent],
              color: activeAgent === agent ? '#000' : agentColors[agent],
              fontWeight: activeAgent === agent ? 600 : 400,
              border: '1px solid',
            }}
          />
          {idx < displayAgents.length - 1 && (
            <ArrowForwardIcon sx={{ fontSize: 14, mx: 0.5, color: 'text.secondary' }} />
          )}
        </Box>
      ))}
    </Box>
  );
}

export default AgentTrace;
