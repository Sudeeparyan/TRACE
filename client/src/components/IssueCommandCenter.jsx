import { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  IconButton,
  Tooltip,
  Snackbar,
  Alert,
  TextField,
  Drawer,
  Tabs,
  Tab,
  Divider,
  Avatar,
  Collapse,
  CircularProgress,
  Fade,
  Slide,
  Paper,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import VisibilityIcon from '@mui/icons-material/Visibility';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import CellTowerIcon from '@mui/icons-material/CellTower';
import CloseIcon from '@mui/icons-material/Close';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import EditIcon from '@mui/icons-material/Edit';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import CodeIcon from '@mui/icons-material/Code';
import ChatIcon from '@mui/icons-material/Chat';
import SendIcon from '@mui/icons-material/Send';
import PersonIcon from '@mui/icons-material/Person';
import TimelineIcon from '@mui/icons-material/Timeline';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import BuildIcon from '@mui/icons-material/Build';
import RefreshIcon from '@mui/icons-material/Refresh';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import AgentTrace from './AgentTrace';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const ADK_WEB_URL = 'http://localhost:8001';

// Agent colors for pipeline visualization
const agentColors = {
  'Monitoring': '#00e676',
  'Prediction': '#00e5ff',
  'Decision xApp': '#ffd740',
  'Action': '#ff5252',
  'Learning': '#ab47bc',
};

// Agent pipeline stages
const AGENT_PIPELINE = ['Monitoring', 'Prediction', 'Decision xApp', 'Action', 'Learning'];

function IssueCommandCenter({ issues, onIssueResolved }) {
  // State management
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeDrawerTab, setActiveDrawerTab] = useState(0);
  const [actionLoading, setActionLoading] = useState(null);
  const [agentResponse, setAgentResponse] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [integrationStatus, setIntegrationStatus] = useState(null);
  
  // Chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);
  
  // AI Analysis state
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  
  // Agent pipeline state
  const [activeAgentIndex, setActiveAgentIndex] = useState(-1);
  const [agentLogs, setAgentLogs] = useState([]);
  const [remediationSteps, setRemediationSteps] = useState([]);
  const [currentStep, setCurrentStep] = useState(-1);

  // Fetch integration status on mount
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/integration/status`)
      .then(res => res.json())
      .then(data => setIntegrationStatus(data))
      .catch(() => setIntegrationStatus({ mode: 'unknown' }));
  }, []);

  // Auto scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Reset state when issue changes
  useEffect(() => {
    if (selectedIssue) {
      setChatMessages([{
        id: Date.now(),
        role: 'assistant',
        content: `I'm analyzing **${selectedIssue.title}**. How can I help you resolve this issue?

**Quick Actions:**
- Ask me to analyze the root cause
- Request remediation recommendations
- Get impact assessment
- View historical patterns`,
        timestamp: new Date().toISOString(),
      }]);
      setAiAnalysis(null);
      setAgentLogs([]);
      setRemediationSteps([]);
      setCurrentStep(-1);
    }
  }, [selectedIssue]);

  // Severity helpers
  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      default: return 'default';
    }
  };

  const getSeverityGlow = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return '0 0 20px rgba(255, 82, 82, 0.4)';
      case 'high': return '0 0 20px rgba(255, 145, 0, 0.4)';
      default: return '0 0 20px rgba(0, 229, 255, 0.2)';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return <ErrorIcon />;
      case 'high': return <WarningIcon />;
      default: return <CheckCircleIcon />;
    }
  };

  // Simulate agent pipeline processing
  const simulateAgentPipeline = async (issue) => {
    const logs = [];
    
    for (let i = 0; i < AGENT_PIPELINE.length; i++) {
      setActiveAgentIndex(i);
      
      const log = {
        agent: AGENT_PIPELINE[i],
        message: getAgentMessage(AGENT_PIPELINE[i], issue),
        timestamp: new Date(Date.now() + i * 15000).toISOString(),
      };
      
      logs.push(log);
      setAgentLogs([...logs]);
      
      await new Promise(resolve => setTimeout(resolve, 800));
    }
    
    return logs;
  };

  const getAgentMessage = (agent, issue) => {
    const messages = {
      'Monitoring': `Monitoring reviewed telemetry for incident ${issue.id}`,
      'Prediction': `Prediction reviewed telemetry for incident ${issue.id}`,
      'Decision xApp': `Decision xApp reviewed telemetry for incident ${issue.id}`,
      'Action': `Action reviewed telemetry for incident ${issue.id}`,
      'Learning': `Learning reviewed telemetry for incident ${issue.id}`,
    };
    return messages[agent] || `${agent} processed the issue`;
  };

  // Handle AI-powered remediation
  const handleAIRemediation = async (issue) => {
    setActionLoading(issue.id);
    setAgentResponse(null);
    setAgentLogs([]);
    setRemediationSteps([]);
    setCurrentStep(-1);
    setActiveAgentIndex(-1);

    // Define remediation steps
    const steps = [
      { id: 1, name: 'Analyzing Issue', description: 'AI is analyzing the root cause...' },
      { id: 2, name: 'Agent Pipeline', description: 'Running through agent pipeline...' },
      { id: 3, name: 'Executing Remediation', description: 'Executing remediation action...' },
      { id: 4, name: 'Verification', description: 'Verifying resolution...' },
    ];
    setRemediationSteps(steps);

    try {
      // Step 1: Analysis
      setCurrentStep(0);
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Step 2: Agent Pipeline
      setCurrentStep(1);
      await simulateAgentPipeline(issue);

      // Step 3: Execute Remediation
      setCurrentStep(2);
      const response = await fetch(`${API_BASE_URL}/api/remediation/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          issueId: issue.id,
          action: issue.suggestedAction || 'auto_remediate',
          region: 'us-east-1',
        }),
      });

      const data = await response.json();

      // Step 4: Verification
      setCurrentStep(3);
      await new Promise(resolve => setTimeout(resolve, 1000));

      const isSuccess = response.ok && (data.success === true || data.success === undefined);

      if (isSuccess) {
        if (data.agent_response) {
          setAgentResponse({
            issueId: issue.id,
            response: data.agent_response,
            source: data.source,
          });
        }

        const sourceLabel = data.source === 'principal_agent' ? 'AI Agent' :
                           data.source === 'direct_tools' ? 'Direct Tools' :
                           data.source === 'fallback' ? 'Fallback Mode' : 'System';

        setSnackbar({
          open: true,
          message: `✅ Remediation completed successfully via ${sourceLabel}`,
          severity: 'success',
        });

        // Add success to chat
        setChatMessages(prev => [...prev, {
          id: Date.now(),
          role: 'assistant',
          content: `🎉 **Remediation Successful!**

The issue has been resolved automatically by the AI agent.

**Action Taken:** ${data.action || issue.suggestedAction || 'Auto Remediate'}
**Source:** ${sourceLabel}
${data.agent_response ? `\n**Agent Response:**\n${data.agent_response}` : ''}

The issue will be removed from the active issues list.`,
          timestamp: new Date().toISOString(),
        }]);

        setTimeout(() => {
          onIssueResolved(issue.id);
          setActionLoading(null);
          setCurrentStep(-1);
        }, 2000);
      } else {
        throw new Error(data.error || data.message || 'Remediation failed');
      }
    } catch (error) {
      console.error('Failed to trigger remediation:', error);
      setSnackbar({
        open: true,
        message: `❌ ${error.message || 'Failed to connect to remediation service'}`,
        severity: 'error',
      });
      
      setChatMessages(prev => [...prev, {
        id: Date.now(),
        role: 'assistant',
        content: `❌ **Remediation Failed**

${error.message || 'An error occurred during remediation.'}

**Suggestions:**
- Try manual remediation via ADK
- Check system connectivity
- Review the issue details and retry`,
        timestamp: new Date().toISOString(),
      }]);
      
      setActionLoading(null);
      setCurrentStep(-1);
    }
  };

  // Handle chat with AI about the issue
  const handleSendMessage = async () => {
    if (!chatInput.trim() || chatLoading || !selectedIssue) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: chatInput,
      timestamp: new Date().toISOString(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setChatLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `Regarding issue "${selectedIssue.title}" (ID: ${selectedIssue.id}, Severity: ${selectedIssue.severity}): ${chatInput}`,
          context: 'issue_resolution',
          issueId: selectedIssue.id,
          issue: selectedIssue,
        }),
      });

      const data = await response.json();

      setChatMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response || data.message || 'I apologize, but I could not process your request. Please try again.',
        source: data.source,
        timestamp: new Date().toISOString(),
      }]);
    } catch (error) {
      console.error('Chat error:', error);
      setChatMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please check if the backend server is running.',
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Handle AI Analysis request
  const handleAnalyzeIssue = async (issue) => {
    setAnalysisLoading(true);
    setAiAnalysis(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/issue/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          issueId: issue.id,
          issue: issue,
          region: 'us-east-1',
        }),
      });

      const data = await response.json();

      if (data.success) {
        setAiAnalysis({
          content: data.analysis,
          source: data.source,
          timestamp: data.timestamp,
        });
      } else {
        setAiAnalysis({
          content: generateFallbackAnalysis(issue),
          source: 'fallback',
          timestamp: new Date().toISOString(),
        });
      }
    } catch (error) {
      console.error('Analysis error:', error);
      setAiAnalysis({
        content: generateFallbackAnalysis(issue),
        source: 'fallback',
        timestamp: new Date().toISOString(),
      });
    } finally {
      setAnalysisLoading(false);
    }
  };

  // Generate fallback analysis
  const generateFallbackAnalysis = (issue) => {
    return `## Root Cause Analysis

**Issue:** ${issue.title}
**Severity:** ${issue.severity?.toUpperCase() || 'MEDIUM'}
**Impact Score:** ${issue.impactScore || 'N/A'}

### Analysis Summary

Based on the telemetry data and system metrics, this issue appears to be caused by:
${issue.severity === 'critical' || issue.severity === 'high' 
  ? '- **Resource Exhaustion:** System resources are nearing capacity limits\n- **Cascade Risk:** High potential for affecting dependent services'
  : '- **Performance Degradation:** Gradual decline in system performance metrics\n- **Monitoring Alert:** Threshold-based alert triggered'}

### Affected Components
- ${issue.affectedTowers?.join('\n- ') || 'Multiple towers affected'}

### Recommended Actions
1. **Immediate:** ${issue.suggestedAction || 'Scale resources or restart affected services'}
2. **Short-term:** Monitor system metrics closely for the next 30 minutes
3. **Long-term:** Review capacity planning and auto-scaling policies

### Risk Assessment
- **Current Impact:** ${issue.impactScore > 70 ? 'High' : issue.impactScore > 40 ? 'Medium' : 'Low'}
- **Escalation Risk:** ${issue.severity === 'critical' ? 'Very High' : issue.severity === 'high' ? 'High' : 'Moderate'}
`;
  };

  // Open issue detail drawer
  const handleViewDetails = (issue) => {
    setSelectedIssue(issue);
    setDrawerOpen(true);
    setActiveDrawerTab(0);
    handleAnalyzeIssue(issue);
  };

  // Handle ADK modification
  const handleModifyInADK = (issue) => {
    const prompt = generateIssuePrompt(issue);
    navigator.clipboard.writeText(prompt).then(() => {
      setSnackbar({
        open: true,
        message: '📋 Issue prompt copied to clipboard! Paste it in the ADK Web interface.',
        severity: 'info',
      });
    }).catch(() => {
      console.log('Clipboard write failed');
    });
    window.open(ADK_WEB_URL, '_blank', 'noopener,noreferrer');
  };

  // Generate prompt for ADK
  const generateIssuePrompt = (issue) => {
    return `Analyze and remediate the following network issue:

**Issue Title:** ${issue.title}
**Severity:** ${issue.severity?.toUpperCase() || 'MEDIUM'}
**Description:** ${issue.description || 'No description available'}
**Affected Towers:** ${issue.affectedTowers?.join(', ') || 'Unknown'}
**Impact Score:** ${issue.impactScore || 'N/A'}
**Suggested Action:** ${issue.suggestedAction || 'auto-remediate'}

Please provide:
1. Root cause analysis
2. Step-by-step remediation plan
3. Expected outcome and impact
4. Preventive measures for the future

Execute the recommended remediation action when ready.`;
  };

  // Close handlers
  const handleCloseSnackbar = () => setSnackbar({ ...snackbar, open: false });
  const handleCloseDrawer = () => {
    setDrawerOpen(false);
    setSelectedIssue(null);
    setChatMessages([]);
    setAiAnalysis(null);
    setAgentLogs([]);
    setRemediationSteps([]);
  };

  // Empty state
  if (issues.length === 0) {
    return (
      <Box 
        sx={{ 
          textAlign: 'center', 
          py: 6,
          background: 'rgba(0, 230, 118, 0.05)',
          borderRadius: 3,
          border: '1px dashed rgba(0, 230, 118, 0.3)',
        }}
      >
        <Box
          sx={{
            width: 80,
            height: 80,
            mx: 'auto',
            mb: 2,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, rgba(0, 230, 118, 0.2) 0%, rgba(0, 200, 83, 0.2) 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <CheckCircleIcon sx={{ fontSize: 40, color: '#00e676' }} />
        </Box>
        <Typography variant="h6" sx={{ color: '#00e676', fontWeight: 600, mb: 1 }}>
          All Systems Operational
        </Typography>
        <Typography variant="body2" color="text.secondary">
          No active issues detected • AI agents monitoring continuously
        </Typography>
      </Box>
    );
  }

  return (
    <>
      {/* Issue Cards Grid */}
      <Grid container spacing={2}>
        {issues.map((issue, index) => (
          <Grid item xs={12} md={6} lg={4} key={issue.id}>
            <Card 
              sx={{ 
                height: '100%',
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderLeft: `4px solid`,
                borderLeftColor: `${getSeverityColor(issue.severity)}.main`,
                position: 'relative',
                transition: 'all 0.3s ease',
                cursor: 'pointer',
                animation: `slideUp 0.5s ease-out ${index * 0.1}s both`,
                '@keyframes slideUp': {
                  from: { opacity: 0, transform: 'translateY(20px)' },
                  to: { opacity: 1, transform: 'translateY(0)' },
                },
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: getSeverityGlow(issue.severity),
                  borderColor: 'rgba(255, 255, 255, 0.15)',
                },
              }}
              onClick={() => handleViewDetails(issue)}
            >
              <CardContent sx={{ p: 2.5 }}>
                {/* Header with severity and status */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Chip
                    label={issue.severity?.toUpperCase() || 'MEDIUM'}
                    color={getSeverityColor(issue.severity)}
                    size="small"
                    icon={getSeverityIcon(issue.severity)}
                    sx={{ fontWeight: 600 }}
                  />
                  <Chip
                    label={issue.status || 'Investigating'}
                    size="small"
                    variant="outlined"
                    sx={{ 
                      borderColor: 'rgba(0, 229, 255, 0.5)',
                      color: '#00e5ff',
                    }}
                  />
                </Box>

                {/* Issue Title */}
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1, lineHeight: 1.3 }}>
                  {issue.title}
                </Typography>

                {/* Description */}
                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  sx={{ 
                    mb: 2,
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}
                >
                  {issue.description}
                </Typography>

                {/* Stats */}
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <CellTowerIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                    <Typography variant="caption" color="text.secondary">
                      {issue.affectedTowers?.length || 0} towers
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Typography variant="caption" color="text.secondary">
                      Impact: 
                    </Typography>
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        color: issue.impactScore > 70 ? '#ff5252' : issue.impactScore > 40 ? '#ff9100' : '#00e676',
                        fontWeight: 600,
                      }}
                    >
                      {issue.impactScore || 'N/A'}%
                    </Typography>
                  </Box>
                </Box>

                {/* Agent Pipeline */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                    Agent Pipeline:
                  </Typography>
                  <AgentTrace 
                    agents={issue.agentTrace || AGENT_PIPELINE}
                    activeAgent={issue.activeAgent || 'Monitoring'}
                  />
                </Box>

                {/* Loading indicator */}
                {actionLoading === issue.id && (
                  <LinearProgress 
                    sx={{ 
                      my: 2, 
                      borderRadius: 1,
                      bgcolor: 'rgba(0, 229, 255, 0.1)',
                      '& .MuiLinearProgress-bar': {
                        background: 'linear-gradient(90deg, #00e5ff, #7c4dff)',
                      }
                    }} 
                  />
                )}

                {/* Action Buttons */}
                <Box sx={{ display: 'flex', gap: 1, mt: 2 }} onClick={(e) => e.stopPropagation()}>
                  <Button
                    variant="contained"
                    size="small"
                    startIcon={<AutoFixHighIcon />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAIRemediation(issue);
                    }}
                    disabled={actionLoading === issue.id}
                    sx={{
                      flex: 1,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      boxShadow: '0 4px 15px rgba(102, 126, 234, 0.3)',
                      '&:hover': {
                        background: 'linear-gradient(135deg, #7c8ff5 0%, #8a5cb8 100%)',
                      },
                    }}
                  >
                    {actionLoading === issue.id ? 'Processing...' : 'Auto Remediate'}
                  </Button>
                  <Tooltip title="Edit in ADK">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleModifyInADK(issue);
                      }}
                      sx={{
                        borderColor: 'rgba(124, 77, 255, 0.5)',
                        border: '1px solid',
                        color: '#7c4dff',
                        '&:hover': {
                          borderColor: '#7c4dff',
                          bgcolor: 'rgba(124, 77, 255, 0.1)',
                        },
                      }}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="View Details & Chat">
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewDetails(issue);
                      }}
                      sx={{
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        '&:hover': {
                          borderColor: '#00e5ff',
                          bgcolor: 'rgba(0, 229, 255, 0.1)',
                        },
                      }}
                    >
                      <VisibilityIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Issue Detail Drawer */}
      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={handleCloseDrawer}
        PaperProps={{
          sx: {
            width: { xs: '100%', md: 650 },
            background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.98) 0%, rgba(30, 41, 59, 0.98) 100%)',
            backdropFilter: 'blur(20px)',
            borderLeft: '1px solid rgba(255, 255, 255, 0.1)',
          }
        }}
      >
        {selectedIssue && (
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* Drawer Header */}
            <Box sx={{ 
              p: 3, 
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              background: 'linear-gradient(180deg, rgba(102, 126, 234, 0.1) 0%, transparent 100%)',
            }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Chip
                      label={selectedIssue.severity?.toUpperCase() || 'MEDIUM'}
                      color={getSeverityColor(selectedIssue.severity)}
                      size="small"
                      icon={getSeverityIcon(selectedIssue.severity)}
                    />
                    <Chip
                      label={selectedIssue.status || 'Investigating'}
                      size="small"
                      variant="outlined"
                      sx={{ borderColor: 'rgba(0, 229, 255, 0.5)', color: '#00e5ff' }}
                    />
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
                    {selectedIssue.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {selectedIssue.description}
                  </Typography>
                </Box>
                <IconButton onClick={handleCloseDrawer} sx={{ color: 'text.secondary' }}>
                  <CloseIcon />
                </IconButton>
              </Box>

              {/* Quick Stats */}
              <Box sx={{ display: 'flex', gap: 3, mt: 2 }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">Affected Towers</Typography>
                  <Typography variant="h6" sx={{ color: '#00e5ff' }}>
                    {selectedIssue.affectedTowers?.length || 0}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">Impact Score</Typography>
                  <Typography variant="h6" sx={{ 
                    color: selectedIssue.impactScore > 70 ? '#ff5252' : 
                           selectedIssue.impactScore > 40 ? '#ff9100' : '#00e676' 
                  }}>
                    {selectedIssue.impactScore || 'N/A'}%
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">Issue ID</Typography>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>
                    {selectedIssue.id}
                  </Typography>
                </Box>
              </Box>
            </Box>

            {/* Tabs */}
            <Tabs 
              value={activeDrawerTab} 
              onChange={(e, v) => setActiveDrawerTab(v)}
              sx={{
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                '& .MuiTabs-indicator': {
                  height: 3,
                  background: 'linear-gradient(90deg, #00e5ff, #7c4dff)',
                },
              }}
            >
              <Tab 
                icon={<AnalyticsIcon />} 
                label="Analysis" 
                iconPosition="start"
                sx={{ '&.Mui-selected': { color: '#00e5ff' } }}
              />
              <Tab 
                icon={<ChatIcon />} 
                label="Chat with AI" 
                iconPosition="start"
                sx={{ '&.Mui-selected': { color: '#00e5ff' } }}
              />
              <Tab 
                icon={<TimelineIcon />} 
                label="Agent Logs" 
                iconPosition="start"
                sx={{ '&.Mui-selected': { color: '#00e5ff' } }}
              />
            </Tabs>

            {/* Tab Content */}
            <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
              {/* Analysis Tab */}
              {activeDrawerTab === 0 && (
                <Box>
                  {/* AI Analysis Section */}
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
                        <SmartToyIcon sx={{ color: '#7c4dff' }} />
                        AI Analysis
                      </Typography>
                      <Button
                        size="small"
                        startIcon={analysisLoading ? <CircularProgress size={16} /> : <RefreshIcon />}
                        onClick={() => handleAnalyzeIssue(selectedIssue)}
                        disabled={analysisLoading}
                        sx={{ color: '#00e5ff' }}
                      >
                        {analysisLoading ? 'Analyzing...' : 'Re-analyze'}
                      </Button>
                    </Box>
                    
                    <Paper sx={{ 
                      p: 2, 
                      bgcolor: 'rgba(0, 0, 0, 0.3)', 
                      borderRadius: 2,
                      border: '1px solid rgba(124, 77, 255, 0.2)',
                    }}>
                      {analysisLoading ? (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 4, justifyContent: 'center' }}>
                          <CircularProgress size={24} sx={{ color: '#7c4dff' }} />
                          <Typography color="text.secondary">AI is analyzing the issue...</Typography>
                        </Box>
                      ) : aiAnalysis ? (
                        <Box>
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              whiteSpace: 'pre-wrap',
                              color: 'text.secondary',
                              '& strong': { color: '#fff' },
                              '& h2, & h3': { color: '#00e5ff', mt: 2, mb: 1 },
                            }}
                            dangerouslySetInnerHTML={{ 
                              __html: aiAnalysis.content
                                .replace(/##\s*(.*)/g, '<h3>$1</h3>')
                                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                .replace(/\n/g, '<br/>')
                            }}
                          />
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, pt: 2, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                            <Chip 
                              label={aiAnalysis.source === 'principal_agent' ? 'AI Agent' : 'Fallback'} 
                              size="small" 
                              sx={{ bgcolor: 'rgba(124, 77, 255, 0.2)', color: '#a78bfa' }}
                            />
                            <Typography variant="caption" color="text.secondary">
                              {new Date(aiAnalysis.timestamp).toLocaleString()}
                            </Typography>
                          </Box>
                        </Box>
                      ) : (
                        <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                          Click "Re-analyze" to get AI analysis
                        </Typography>
                      )}
                    </Paper>
                  </Box>

                  {/* Remediation Steps */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <BuildIcon sx={{ color: '#ffd740' }} />
                      Remediation Steps
                    </Typography>
                    <Paper sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.3)', borderRadius: 2 }}>
                      {remediationSteps.length > 0 ? (
                        remediationSteps.map((step, idx) => (
                          <Box 
                            key={step.id}
                            sx={{ 
                              display: 'flex', 
                              alignItems: 'center', 
                              gap: 2, 
                              mb: idx < remediationSteps.length - 1 ? 2 : 0,
                              opacity: currentStep >= idx ? 1 : 0.4,
                            }}
                          >
                            <Box
                              sx={{
                                width: 32,
                                height: 32,
                                borderRadius: '50%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                bgcolor: currentStep > idx ? 'rgba(0, 230, 118, 0.2)' : 
                                         currentStep === idx ? 'rgba(0, 229, 255, 0.2)' : 'rgba(255, 255, 255, 0.1)',
                                border: '2px solid',
                                borderColor: currentStep > idx ? '#00e676' : 
                                             currentStep === idx ? '#00e5ff' : 'rgba(255, 255, 255, 0.2)',
                              }}
                            >
                              {currentStep > idx ? (
                                <CheckCircleIcon sx={{ fontSize: 18, color: '#00e676' }} />
                              ) : currentStep === idx ? (
                                <CircularProgress size={16} sx={{ color: '#00e5ff' }} />
                              ) : (
                                <Typography variant="caption" sx={{ fontWeight: 600 }}>{idx + 1}</Typography>
                              )}
                            </Box>
                            <Box>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>{step.name}</Typography>
                              <Typography variant="caption" color="text.secondary">{step.description}</Typography>
                            </Box>
                          </Box>
                        ))
                      ) : (
                        <Box>
                          {selectedIssue.remediationSteps?.map((step, idx) => (
                            <Box key={idx} sx={{ display: 'flex', gap: 2, mb: 1.5 }}>
                              <Box
                                sx={{
                                  width: 24,
                                  height: 24,
                                  borderRadius: '50%',
                                  bgcolor: 'rgba(0, 229, 255, 0.2)',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  flexShrink: 0,
                                }}
                              >
                                <Typography variant="caption" sx={{ color: '#00e5ff', fontWeight: 600 }}>
                                  {idx + 1}
                                </Typography>
                              </Box>
                              <Typography variant="body2" color="text.secondary">{step}</Typography>
                            </Box>
                          )) || (
                            <Typography variant="body2" color="text.secondary">
                              Click "Auto Remediate" to start the AI-powered remediation process.
                            </Typography>
                          )}
                        </Box>
                      )}
                    </Paper>
                  </Box>
                </Box>
              )}

              {/* Chat Tab */}
              {activeDrawerTab === 1 && (
                <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  {/* Chat Messages */}
                  <Box sx={{ 
                    flex: 1, 
                    overflow: 'auto', 
                    mb: 2,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2,
                  }}>
                    {chatMessages.map((msg) => (
                      <Box 
                        key={msg.id}
                        sx={{ 
                          display: 'flex',
                          gap: 1.5,
                          flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                        }}
                      >
                        <Avatar
                          sx={{
                            width: 32,
                            height: 32,
                            bgcolor: msg.role === 'user' ? 'rgba(0, 229, 255, 0.2)' : 'rgba(124, 77, 255, 0.2)',
                          }}
                        >
                          {msg.role === 'user' ? <PersonIcon sx={{ fontSize: 18 }} /> : <SmartToyIcon sx={{ fontSize: 18, color: '#7c4dff' }} />}
                        </Avatar>
                        <Paper
                          sx={{
                            p: 2,
                            maxWidth: '80%',
                            bgcolor: msg.role === 'user' ? 'rgba(0, 229, 255, 0.1)' : 'rgba(124, 77, 255, 0.1)',
                            borderRadius: 2,
                            border: '1px solid',
                            borderColor: msg.role === 'user' ? 'rgba(0, 229, 255, 0.2)' : 'rgba(124, 77, 255, 0.2)',
                          }}
                        >
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              whiteSpace: 'pre-wrap',
                              '& strong': { color: '#fff' },
                            }}
                            dangerouslySetInnerHTML={{ 
                              __html: msg.content
                                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                .replace(/\n/g, '<br/>')
                            }}
                          />
                          {msg.source && (
                            <Chip 
                              label={msg.source} 
                              size="small" 
                              sx={{ mt: 1, height: 20, fontSize: '0.65rem', bgcolor: 'rgba(255,255,255,0.05)' }}
                            />
                          )}
                        </Paper>
                      </Box>
                    ))}
                    {chatLoading && (
                      <Box sx={{ display: 'flex', gap: 1.5 }}>
                        <Avatar sx={{ width: 32, height: 32, bgcolor: 'rgba(124, 77, 255, 0.2)' }}>
                          <SmartToyIcon sx={{ fontSize: 18, color: '#7c4dff' }} />
                        </Avatar>
                        <Paper sx={{ p: 2, bgcolor: 'rgba(124, 77, 255, 0.1)', borderRadius: 2 }}>
                          <Box sx={{ display: 'flex', gap: 0.5 }}>
                            <CircularProgress size={8} sx={{ color: '#7c4dff' }} />
                            <CircularProgress size={8} sx={{ color: '#7c4dff', animationDelay: '0.2s' }} />
                            <CircularProgress size={8} sx={{ color: '#7c4dff', animationDelay: '0.4s' }} />
                          </Box>
                        </Paper>
                      </Box>
                    )}
                    <div ref={chatEndRef} />
                  </Box>

                  {/* Quick Suggestions */}
                  <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {['Analyze root cause', 'Recommend fix', 'Show impact', 'Preventive actions'].map((suggestion) => (
                      <Chip
                        key={suggestion}
                        label={suggestion}
                        size="small"
                        onClick={() => {
                          setChatInput(suggestion);
                          setTimeout(handleSendMessage, 100);
                        }}
                        sx={{
                          cursor: 'pointer',
                          bgcolor: 'rgba(0, 229, 255, 0.1)',
                          borderColor: 'rgba(0, 229, 255, 0.3)',
                          '&:hover': { bgcolor: 'rgba(0, 229, 255, 0.2)' },
                        }}
                        variant="outlined"
                      />
                    ))}
                  </Box>

                  {/* Chat Input */}
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <TextField
                      fullWidth
                      size="small"
                      placeholder="Ask about this issue..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                      disabled={chatLoading}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          bgcolor: 'rgba(0, 0, 0, 0.3)',
                          '& fieldset': { borderColor: 'rgba(255, 255, 255, 0.1)' },
                          '&:hover fieldset': { borderColor: 'rgba(0, 229, 255, 0.3)' },
                          '&.Mui-focused fieldset': { borderColor: '#00e5ff' },
                        },
                      }}
                    />
                    <IconButton 
                      onClick={handleSendMessage}
                      disabled={chatLoading || !chatInput.trim()}
                      sx={{
                        bgcolor: 'rgba(0, 229, 255, 0.2)',
                        '&:hover': { bgcolor: 'rgba(0, 229, 255, 0.3)' },
                        '&.Mui-disabled': { bgcolor: 'rgba(255, 255, 255, 0.05)' },
                      }}
                    >
                      <SendIcon sx={{ color: '#00e5ff' }} />
                    </IconButton>
                  </Box>
                </Box>
              )}

              {/* Agent Logs Tab */}
              {activeDrawerTab === 2 && (
                <Box>
                  {/* Agent Pipeline Visualization */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                      Agent Pipeline Status
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
                      {AGENT_PIPELINE.map((agent, idx) => (
                        <Box key={agent} sx={{ display: 'flex', alignItems: 'center' }}>
                          <Chip
                            label={agent}
                            size="small"
                            sx={{
                              bgcolor: activeAgentIndex === idx ? agentColors[agent] : 
                                       activeAgentIndex > idx ? 'rgba(0, 230, 118, 0.2)' : 'transparent',
                              borderColor: agentColors[agent],
                              color: activeAgentIndex === idx ? '#000' : agentColors[agent],
                              fontWeight: activeAgentIndex === idx ? 600 : 400,
                              border: '1px solid',
                              transition: 'all 0.3s ease',
                            }}
                          />
                          {idx < AGENT_PIPELINE.length - 1 && (
                            <ArrowForwardIcon sx={{ 
                              fontSize: 14, 
                              mx: 0.5, 
                              color: activeAgentIndex > idx ? '#00e676' : 'text.secondary',
                              transition: 'color 0.3s ease',
                            }} />
                          )}
                        </Box>
                      ))}
                    </Box>
                  </Box>

                  {/* Agent Logs */}
                  <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2 }}>
                    Communication Log
                  </Typography>
                  <Paper sx={{ 
                    p: 2, 
                    bgcolor: 'rgba(0, 0, 0, 0.4)', 
                    borderRadius: 2,
                    maxHeight: 400,
                    overflow: 'auto',
                    fontFamily: 'monospace',
                  }}>
                    {agentLogs.length > 0 ? (
                      agentLogs.map((log, idx) => (
                        <Typography 
                          key={idx} 
                          variant="caption" 
                          display="block" 
                          sx={{ mb: 1, color: 'text.secondary' }}
                        >
                          <span style={{ color: '#00e5ff' }}>[{new Date(log.timestamp).toLocaleTimeString()}]</span>{' '}
                          <span style={{ color: agentColors[log.agent] || '#7c4dff' }}>{log.agent}:</span>{' '}
                          {log.message}
                        </Typography>
                      ))
                    ) : selectedIssue.agentLogs?.length > 0 ? (
                      selectedIssue.agentLogs.map((log, idx) => (
                        <Typography 
                          key={idx} 
                          variant="caption" 
                          display="block" 
                          sx={{ mb: 1, color: 'text.secondary' }}
                        >
                          <span style={{ color: '#00e5ff' }}>[{log.timestamp}]</span>{' '}
                          <span style={{ color: '#7c4dff' }}>{log.agent}:</span>{' '}
                          {log.message}
                        </Typography>
                      ))
                    ) : (
                      <Typography variant="caption" color="text.secondary">
                        Agent communication logs will appear here when remediation is triggered...
                      </Typography>
                    )}
                  </Paper>
                </Box>
              )}
            </Box>

            {/* Drawer Footer Actions */}
            <Box sx={{ 
              p: 2, 
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              gap: 1,
              bgcolor: 'rgba(0, 0, 0, 0.2)',
            }}>
              <Button 
                onClick={handleCloseDrawer}
                sx={{ color: 'text.secondary' }}
              >
                Close
              </Button>
              <Button 
                variant="outlined"
                startIcon={<CodeIcon />}
                endIcon={<OpenInNewIcon sx={{ fontSize: 16 }} />}
                onClick={() => handleModifyInADK(selectedIssue)}
                sx={{
                  borderColor: 'rgba(124, 77, 255, 0.5)',
                  color: '#7c4dff',
                  '&:hover': {
                    borderColor: '#7c4dff',
                    bgcolor: 'rgba(124, 77, 255, 0.1)',
                  },
                }}
              >
                Modify in ADK
              </Button>
              <Button 
                variant="contained"
                startIcon={actionLoading === selectedIssue?.id ? <CircularProgress size={18} sx={{ color: '#fff' }} /> : <AutoFixHighIcon />}
                onClick={() => handleAIRemediation(selectedIssue)}
                disabled={actionLoading === selectedIssue?.id}
                sx={{
                  flex: 1,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #7c8ff5 0%, #8a5cb8 100%)',
                  },
                }}
              >
                {actionLoading === selectedIssue?.id ? 'Executing...' : 'Execute Remediation'}
              </Button>
            </Box>
          </Box>
        )}
      </Drawer>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleCloseSnackbar} 
          severity={snackbar.severity}
          sx={{ 
            width: '100%',
            bgcolor: snackbar.severity === 'success' ? 'rgba(0, 230, 118, 0.1)' : 
                     snackbar.severity === 'error' ? 'rgba(255, 82, 82, 0.1)' : 'rgba(0, 229, 255, 0.1)',
            border: `1px solid ${snackbar.severity === 'success' ? 'rgba(0, 230, 118, 0.3)' : 
                                  snackbar.severity === 'error' ? 'rgba(255, 82, 82, 0.3)' : 'rgba(0, 229, 255, 0.3)'}`,
          }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Integration Status Indicator */}
      {integrationStatus && (
        <Box 
          sx={{ 
            position: 'fixed', 
            bottom: 20, 
            left: 20, 
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            bgcolor: 'rgba(0, 0, 0, 0.6)',
            px: 2,
            py: 1,
            borderRadius: 2,
            border: '1px solid rgba(255, 255, 255, 0.1)',
            zIndex: 1000,
          }}
        >
          <SmartToyIcon sx={{ 
            fontSize: 16, 
            color: integrationStatus.fully_initialized ? '#00e676' : 
                   integrationStatus.principal_agent_available ? '#ff9100' : '#ff5252' 
          }} />
          <Typography variant="caption" color="text.secondary">
            AI: {integrationStatus.mode?.toUpperCase() || 'Unknown'}
          </Typography>
        </Box>
      )}
    </>
  );
}

export default IssueCommandCenter;
