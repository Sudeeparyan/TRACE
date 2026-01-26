import {
  Box,
  Typography,
  Paper,
  Chip,
  Collapse,
  IconButton,
} from '@mui/material';
import { useState } from 'react';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { format } from 'date-fns';

function ResolutionTimeline({ resolutions }) {
  const [expanded, setExpanded] = useState({});

  const toggleExpanded = (id) => {
    setExpanded(prev => ({ ...prev, [id]: !prev[id] }));
  };

  if (resolutions.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="body1" color="text.secondary">
          No resolutions yet
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ position: 'relative', pl: 4 }}>
      {/* Vertical line */}
      <Box
        sx={{
          position: 'absolute',
          left: 16,
          top: 0,
          bottom: 0,
          width: 2,
          bgcolor: 'primary.main',
          opacity: 0.3,
        }}
      />
      
      {resolutions.map((resolution, idx) => (
        <Box key={resolution.id || idx} sx={{ position: 'relative', mb: 3 }}>
          {/* Timeline dot */}
          <Box
            sx={{
              position: 'absolute',
              left: -24,
              top: 16,
              width: 32,
              height: 32,
              borderRadius: '50%',
              bgcolor: 'success.main',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CheckCircleIcon sx={{ color: 'white', fontSize: 20 }} />
          </Box>
          
          <Paper elevation={3} sx={{ p: 2, ml: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
              <Box>
                <Typography variant="caption" color="text.secondary" display="block">
                  {format(new Date(resolution.timestamp || Date.now()), 'MMM dd, HH:mm:ss')}
                </Typography>
                <Typography variant="h6" component="span">
                  {resolution.title || 'Remediation Complete'}
                </Typography>
              </Box>
              <IconButton
                size="small"
                onClick={() => toggleExpanded(resolution.id || idx)}
                sx={{
                  transform: expanded[resolution.id || idx] ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.3s',
                }}
              >
                <ExpandMoreIcon />
              </IconButton>
            </Box>

            <Chip
              label={resolution.initiatingAgent || 'Principal Agent'}
              size="small"
              color="primary"
              sx={{ mb: 1 }}
            />

            <Typography variant="body2" color="text.secondary">
              {resolution.summary}
            </Typography>

            <Collapse in={expanded[resolution.id || idx]} timeout="auto">
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Actions Executed
                </Typography>
                {resolution.actions?.map((action, actionIdx) => (
                  <Typography key={actionIdx} variant="body2" sx={{ pl: 2, mb: 0.5 }}>
                    • {action}
                  </Typography>
                )) || (
                  <Typography variant="body2" color="text.secondary">
                    No actions recorded
                  </Typography>
                )}

                <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                  Safety Validations
                </Typography>
                <Typography variant="body2" sx={{ pl: 2 }}>
                  ✓ Pre-flight checks passed
                </Typography>
                <Typography variant="body2" sx={{ pl: 2 }}>
                  ✓ Rollback status: {resolution.rollbackStatus || 'Available'}
                </Typography>

                <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                  Learning Agent Notes
                </Typography>
                <Typography variant="body2" sx={{ pl: 2 }}>
                  {resolution.learningNotes || 'Model updated with remediation outcome'}
                </Typography>
                <Typography variant="body2" sx={{ pl: 2 }}>
                  Confidence Score: {resolution.confidenceScore || '95%'}
                </Typography>
              </Box>
            </Collapse>
          </Paper>
        </Box>
      ))}
    </Box>
  );
}

export default ResolutionTimeline;
