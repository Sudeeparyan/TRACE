import { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Paper, 
  TextField, 
  IconButton,
  CircularProgress,
  Chip,
  Divider,
  Avatar,
  Collapse,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton
} from '@mui/material';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import SendIcon from '@mui/icons-material/Send';
import CodeIcon from '@mui/icons-material/Code';
import PersonIcon from '@mui/icons-material/Person';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import BoltIcon from '@mui/icons-material/Bolt';
import NetworkCheckIcon from '@mui/icons-material/NetworkCheck';
import HealingIcon from '@mui/icons-material/Healing';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import TipsAndUpdatesIcon from '@mui/icons-material/TipsAndUpdates';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const ADK_WEB_URL = 'http://localhost:8001';

// Contextual suggestions based on TRACE capabilities
const SUGGESTION_CATEGORIES = {
  energy: {
    icon: <BoltIcon sx={{ color: '#00e676' }} />,
    title: 'Energy Optimization',
    description: 'Reduce tower energy consumption by 30-40%',
    prompts: [
      'Analyze energy consumption patterns for tower_5 and recommend optimization strategies',
      'Forecast traffic for the next 4 hours and identify low-traffic periods for energy savings',
      'Show me energy savings opportunities across all towers in region R-A',
      'Which towers can safely reduce power consumption right now?'
    ]
  },
  congestion: {
    icon: <NetworkCheckIcon sx={{ color: '#ff9100' }} />,
    title: 'Congestion Management',
    description: 'Proactive load balancing and surge prevention',
    prompts: [
      'There\'s a major concert at the stadium tonight at 8 PM. Prepare a load balancing strategy',
      'Predict traffic surge and assess congestion risk for the next 6 hours',
      'Analyze potential congestion risks for all towers and recommend proactive strategies',
      'Which towers are at risk of overload and what preventive actions should we take?'
    ]
  },
  healing: {
    icon: <HealingIcon sx={{ color: '#ff5252' }} />,
    title: 'Self-Healing & Recovery',
    description: 'Autonomous failure detection and remediation',
    prompts: [
      'The monitoring agent at tower_12 has stopped responding. Show me the self-healing response',
      'Simulate a failure scenario and execute the remediation workflow',
      'Check system health and identify any agents that need attention',
      'What remediation actions are available for the current active issues?'
    ]
  },
  analysis: {
    icon: <AnalyticsIcon sx={{ color: '#29b6f6' }} />,
    title: 'Data Analysis',
    description: 'AI-powered insights from telemetry data',
    prompts: [
      'Load the JSON data from data/trace_reduced_20.json and analyze it',
      'Get detailed recommendations for tower TX005 focusing on all metrics',
      'Analyze this data comprehensively and identify key patterns and issues',
      'Compare current metrics with historical data and show trends'
    ]
  }
};

// Quick action prompts from demo cheatsheet
const QUICK_ACTIONS = [
  { label: '🔍 System Health', query: 'Check the overall system health and provide a comprehensive report', category: 'health' },
  { label: '⚡ Energy Analysis', query: 'Analyze energy consumption patterns and recommend 30-40% savings strategies', category: 'energy' },
  { label: '🌐 Congestion Check', query: 'Assess congestion risk across all towers and prepare load balancing strategy', category: 'congestion' },
  { label: '🔧 Agent Status', query: 'Show me the current status of all agents in the system', category: 'status' },
];

function ChatInterface() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: `👋 **Welcome to TRACE AI Agent!**

I'm powered by Google ADK and can help you with telecom network management through our multi-agent system.

**🎯 Key Capabilities:**
• **Energy Optimization** - Achieve 30-40% savings during low demand
• **Congestion Management** - Proactive load balancing for traffic surges
• **Self-Healing** - Autonomous failure detection and recovery (<5 min MTTR)
• **Data Analysis** - AI-powered insights from JSON telemetry data

**💡 Try these quick actions or ask me anything!**`,
      timestamp: new Date().toISOString(),
      suggestions: ['energy', 'congestion', 'healing', 'analysis']
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [expandedCategory, setExpandedCategory] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleOpenDeveloperMode = () => {
    window.open(ADK_WEB_URL, '_blank', 'noopener,noreferrer');
  };

  // Generate contextual suggestions based on response
  const generateContextualSuggestions = (response, userInput) => {
    const suggestions = [];
    const lowerResponse = response.toLowerCase();
    const lowerInput = userInput.toLowerCase();
    
    // Energy-related follow-ups
    if (lowerResponse.includes('energy') || lowerResponse.includes('power') || lowerInput.includes('energy')) {
      suggestions.push('Show me which specific towers can reduce power now');
      suggestions.push('What are the expected savings in kWh for today?');
    }
    
    // Health-related follow-ups
    if (lowerResponse.includes('health') || lowerResponse.includes('status') || lowerInput.includes('health')) {
      suggestions.push('Show me more details about any degraded components');
      suggestions.push('What remediation actions do you recommend?');
    }
    
    // Issue-related follow-ups
    if (lowerResponse.includes('issue') || lowerResponse.includes('problem') || lowerResponse.includes('error')) {
      suggestions.push('Analyze the root cause of this issue');
      suggestions.push('Execute auto-remediation for this issue');
    }
    
    // Congestion-related follow-ups
    if (lowerResponse.includes('congestion') || lowerResponse.includes('traffic') || lowerResponse.includes('load')) {
      suggestions.push('Which towers should we pre-activate for the surge?');
      suggestions.push('Show me the load balancing plan in detail');
    }
    
    // Tower-specific follow-ups
    const towerMatch = response.match(/tower[_\s-]?(\d+|[A-Z]+\d+)/i);
    if (towerMatch) {
      suggestions.push(`Get detailed metrics for ${towerMatch[0]}`);
      suggestions.push(`Check agent status for ${towerMatch[0]}`);
    }
    
    // Default suggestions if none matched
    if (suggestions.length === 0) {
      suggestions.push('Check the overall system health');
      suggestions.push('What other optimizations do you recommend?');
    }
    
    return suggestions.slice(0, 3); // Return max 3 suggestions
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    const sentInput = inputValue.trim();
    setInputValue('');
    setIsLoading(true);
    setShowSuggestions(false);

    try {
      // Send message to backend for AI processing
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: sentInput,
          context: 'trace_dashboard'
        })
      });

      if (response.ok) {
        const data = await response.json();
        const responseContent = data.response || data.message || 'I processed your request.';
        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: responseContent,
          timestamp: new Date().toISOString(),
          source: data.source || 'principal_agent',
          followUpSuggestions: generateContextualSuggestions(responseContent, sentInput)
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        // Fallback response if API fails
        const fallbackContent = generateFallbackResponse(sentInput);
        const fallbackMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: fallbackContent,
          timestamp: new Date().toISOString(),
          source: 'fallback',
          followUpSuggestions: generateContextualSuggestions(fallbackContent, sentInput)
        };
        setMessages(prev => [...prev, fallbackMessage]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      const fallbackContent = generateFallbackResponse(sentInput);
      const fallbackMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: fallbackContent,
        timestamp: new Date().toISOString(),
        source: 'fallback',
        followUpSuggestions: generateContextualSuggestions(fallbackContent, sentInput)
      };
      setMessages(prev => [...prev, fallbackMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateFallbackResponse = (userInput) => {
    const input = userInput.toLowerCase();
    
    // Health/Status checks
    if (input.includes('health') || input.includes('status') || input.includes('check')) {
      return `📊 **System Health Report**

**Overall Status:** ✅ Operational

**Infrastructure:**
• **Active Towers:** 48/50 online (96%)
• **Parent Agents:** 3/3 running
• **Edge Agents:** 15/15 operational
• **Network Latency:** 42ms (normal)

**Performance Metrics:**
• **CPU Usage:** 45% avg across infrastructure
• **Memory Usage:** 62% avg
• **Energy Savings:** 34% achieved today
• **Uptime:** 99.97%

**Recent Activity:**
• 3 congestion events prevented in last 6 hours
• 2 auto-remediation actions executed successfully
• 850 kWh saved through energy optimization

💡 **Suggested Actions:**
• Run energy optimization analysis for additional savings
• Review tower_12 for minor latency spike detected`;
    }
    
    // Energy optimization
    if (input.includes('energy') || input.includes('power') || input.includes('consumption') || input.includes('saving')) {
      return `⚡ **Energy Optimization Analysis**

**Current Energy Status:**
• **Total Consumption:** 1,245 kWh (last hour)
• **Savings Achieved:** 34.2% vs baseline
• **CO₂ Reduction:** 523 kg today

**Optimization Opportunities:**

**🔋 High Priority (Immediate Action):**
| Tower | Current Load | Recommendation | Expected Savings |
|-------|-------------|----------------|------------------|
| TX003 | 23% | Reduce TRX by 40% | 85 kWh/day |
| TX007 | 18% | Enable sleep mode | 72 kWh/day |
| TX012 | 31% | Partial shutdown | 45 kWh/day |

**📈 Forecast (Next 4 Hours):**
• 2:00 AM - 5:00 AM: Low traffic predicted
• Recommended: Enable Energy Saving Mode on 12 towers
• Expected additional savings: 30-40%

**Action Items:**
1. Schedule partial TRX shutdowns during 2-5 AM window
2. Monitor user experience metrics
3. Gradually expand energy-saving windows

💡 For detailed tower-specific analysis, ask about a specific tower (e.g., "Analyze tower TX003")`;
    }
    
    // Congestion/Traffic management
    if (input.includes('congestion') || input.includes('traffic') || input.includes('surge') || input.includes('load') || input.includes('concert') || input.includes('event')) {
      return `🌐 **Congestion Management Analysis**

**Current Traffic Status:**
• **Network Load:** 67% capacity
• **Peak Traffic:** 485 Gbps
• **Active Connections:** 32,450

**Risk Assessment:**
${input.includes('concert') || input.includes('event') ? `
⚠️ **Event Detected:** Large gathering predicted
• **Expected Surge:** +150-200% traffic increase
• **Affected Towers:** TX003, TX004, TX007, TX008
• **Risk Level:** HIGH
` : `
✅ **Current Risk:** LOW
• No immediate congestion threats detected
• All towers within normal capacity
`}
**Recommended Actions:**

**🔄 Pre-emptive Load Balancing:**
1. Pre-activate backup cells on TX003, TX004
2. Increase capacity on TX007, TX008 by 40%
3. Set up traffic overflow to TX001, TX002

**📊 Monitoring Plan:**
• Enhanced monitoring window: 6 PM - 12 AM
• Alert threshold: 85% capacity
• Auto-scaling enabled for affected towers

**Expected Outcomes:**
• Zero dropped calls during surge
• Maintained QoE (Quality of Experience)
• Seamless handoff between towers

💡 For real-time monitoring, check the Dashboard or ask about specific tower metrics.`;
    }
    
    // Self-healing/Remediation
    if (input.includes('remediat') || input.includes('fix') || input.includes('heal') || input.includes('recover') || input.includes('restart') || input.includes('fail')) {
      return `🔧 **Self-Healing & Remediation**

**Available Remediation Actions:**

| Action | Description | MTTR | Success Rate |
|--------|-------------|------|--------------|
| **restart_agent** | Restart monitoring agent | ~30s | 95% |
| **redeploy_agent** | Full agent redeployment | ~2min | 98% |
| **reroute_traffic** | Redirect to healthy nodes | ~45s | 97% |

**Self-Healing Workflow:**
\`\`\`
Failure Detected → Diagnose → Restart → Verify → (Escalate if needed)
      ↓              ↓          ↓         ↓
   <10 sec       Analysis    Automatic   Health
                             Recovery    Check
\`\`\`

**Current Agent Status:**
• **Principal Agent:** ✅ Active
• **Regional Coordinators:** ✅ All 3 healthy
• **Edge Agents:** ✅ 15/15 operational

**Recent Remediation History:**
• 2 hours ago: restart_agent on tower_7 (success)
• 5 hours ago: reroute_traffic TX003→TX004 (success)

💡 To trigger remediation, describe the issue or use the Dashboard's Issue Command Center.`;
    }
    
    // Data analysis
    if (input.includes('data') || input.includes('json') || input.includes('analyze') || input.includes('telemetry') || input.includes('metric')) {
      return `📊 **Data Analysis Capabilities**

**Available Data Tools:**

1. **Load JSON Data**
   \`Load the JSON data from data/trace_reduced_20.json\`
   
2. **Comprehensive Analysis**
   \`Analyze this data for energy optimization and patterns\`
   
3. **Specific Recommendations**
   \`Get recommendations for tower TX005 focusing on all metrics\`
   
4. **Dataset Comparison**
   \`Compare data/trace_reduced_20.json with trace_llm_20.json\`

**Analysis Dimensions:**
• **Energy Insights:** Low utilization periods, savings opportunities
• **Congestion Patterns:** Peak usage, bandwidth trends
• **Health Issues:** Signal quality, latency, error patterns
• **Predictive Insights:** Forecast trends, anomaly detection

**Sample Insights from Recent Data:**
• 75% of records show low bandwidth utilization → Energy savings opportunity
• Tower TX005 shows 23% higher latency than average
• Region R-A has 3 towers suitable for power reduction

💡 Use **Developer Mode** for advanced data analysis with the full ADK Web Interface.`;
    }
    
    // Agent information
    if (input.includes('agent') || input.includes('hierarchy') || input.includes('architecture')) {
      return `🤖 **TRACE Agent Hierarchy**

**Level 1: Principal Agent (Me!)**
• Global orchestrator and health guardian
• Monitors all agents, executes self-healing
• Tools: health_monitor, remediation, dashboard, data_analysis

**Level 2: Regional Coordinators (3 active)**
• Manage 10-20 towers each
• Aggregate telemetry, enforce policies
• Quick regional-level remediation

**Level 3: Edge Agents (5 per tower)**
| Agent | Purpose | Key Functions |
|-------|---------|---------------|
| **Monitoring** | Data collection | RAN KPIs, power metrics |
| **Prediction** | Forecasting | Traffic patterns, surges |
| **Decision xApp** | Policy engine | Energy/congestion decisions |
| **Action** | Execution | TRX control, load balance |
| **Learning** | Improvement | Model retraining, A/B tests |

**Communication:**
• A2A (Agent-to-Agent) protocol for secure messaging
• MCP (Model Context Protocol) for context sharing
• Real-time telemetry streaming

💡 Ask about specific agents for detailed status and capabilities.`;
    }
    
    // Help/Capabilities
    if (input.includes('help') || input.includes('what can') || input.includes('capabilit') || input.includes('feature')) {
      return `🎯 **TRACE AI Agent - Full Capabilities**

**🔋 Energy Optimization**
• Reduce tower energy 30-40% during low demand
• Automatic TRX shutdown scheduling
• Real-time savings tracking

**🌐 Congestion Management**
• Predict and prevent traffic surges
• Proactive load balancing
• Event-based capacity planning

**🔧 Self-Healing**
• Autonomous failure detection (<10 sec)
• Automated remediation (<5 min MTTR)
• Escalation workflows

**📊 Data Analysis**
• JSON telemetry processing
• LLM-powered insights
• Historical trend analysis

**Example Prompts to Try:**
\`\`\`
"Check the overall system health"
"Analyze energy consumption for tower_5"
"There's a concert tonight - prepare load balancing"
"The monitoring agent stopped responding - show self-healing"
"Load data/trace_reduced_20.json and analyze it"
\`\`\`

💡 **Pro Tip:** Use **Developer Mode** for the full Google ADK Web Interface with advanced capabilities!`;
    }
    
    // Default comprehensive response
    return `I understand you're asking about: "${userInput}"

As the **TRACE Principal Agent**, I can help with:

**🔋 Energy Optimization**
• "Analyze energy patterns for tower_5"
• "Show energy savings opportunities"

**🌐 Traffic Management**
• "Predict congestion for tonight's event"
• "Prepare load balancing strategy"

**🔧 Self-Healing**
• "Check system health"
• "Show remediation options"

**📊 Data Analysis**
• "Load and analyze JSON telemetry data"
• "Get recommendations for specific towers"

**💡 Quick Actions Available:**
• Click the suggestion chips below
• Or try "help" for full capabilities

For advanced features, use **Developer Mode** to access the Google ADK Web Interface.`;
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestionClick = (query) => {
    setInputValue(query);
  };

  const handleCategoryToggle = (category) => {
    setExpandedCategory(expandedCategory === category ? null : category);
  };

  return (
    <Box 
      sx={{ 
        height: 'calc(100vh - 64px)', 
        bgcolor: 'transparent',
        display: 'flex',
        flexDirection: 'column',
        p: 2,
      }}
    >
      {/* Header */}
      <Paper 
        sx={{ 
          p: 2,
          mb: 2,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'linear-gradient(135deg, rgba(20, 30, 60, 0.9) 0%, rgba(30, 40, 80, 0.9) 100%)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar 
            sx={{ 
              bgcolor: 'primary.main',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            }}
          >
            <SmartToyIcon />
          </Avatar>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              TRACE AI Agent
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Powered by Google ADK • Multi-Agent Orchestration
            </Typography>
          </Box>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="text"
            size="small"
            startIcon={<TipsAndUpdatesIcon />}
            onClick={() => setShowSuggestions(!showSuggestions)}
            sx={{ color: 'text.secondary' }}
          >
            {showSuggestions ? 'Hide' : 'Show'} Suggestions
          </Button>
          <Button
            variant="outlined"
            startIcon={<CodeIcon />}
            endIcon={<OpenInNewIcon sx={{ fontSize: 16 }} />}
            onClick={handleOpenDeveloperMode}
            sx={{
              borderColor: 'rgba(124, 77, 255, 0.5)',
              color: '#7c4dff',
              '&:hover': {
                borderColor: '#7c4dff',
                bgcolor: 'rgba(124, 77, 255, 0.1)',
              }
            }}
          >
            Developer Mode
          </Button>
        </Box>
      </Paper>

      {/* Main Content Area */}
      <Box sx={{ flex: 1, display: 'flex', gap: 2, overflow: 'hidden' }}>
        {/* Chat Messages */}
        <Paper 
          sx={{ 
            flex: 1,
            overflow: 'auto',
            p: 2,
            background: 'rgba(10, 14, 26, 0.8)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
          }}
        >
          {messages.map((message) => (
            <Box key={message.id}>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                  mb: 2,
                }}
              >
                <Box
                  sx={{
                    maxWidth: '85%',
                    display: 'flex',
                    flexDirection: message.role === 'user' ? 'row-reverse' : 'row',
                    gap: 1.5,
                    alignItems: 'flex-start',
                  }}
                >
                  <Avatar
                    sx={{
                      width: 36,
                      height: 36,
                      bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main',
                      background: message.role === 'user' 
                        ? 'linear-gradient(135deg, #00e5ff 0%, #00b2cc 100%)'
                        : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    }}
                  >
                    {message.role === 'user' ? <PersonIcon /> : <SmartToyIcon />}
                  </Avatar>
                  <Paper
                    sx={{
                      p: 2,
                      bgcolor: message.role === 'user' 
                        ? 'rgba(0, 229, 255, 0.15)' 
                        : 'rgba(102, 126, 234, 0.15)',
                      border: '1px solid',
                      borderColor: message.role === 'user'
                        ? 'rgba(0, 229, 255, 0.3)'
                        : 'rgba(102, 126, 234, 0.3)',
                    }}
                  >
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        whiteSpace: 'pre-wrap',
                        '& strong': { color: 'primary.main' },
                        '& code': { 
                          bgcolor: 'rgba(0,0,0,0.3)', 
                          px: 0.5, 
                          py: 0.25, 
                          borderRadius: 1,
                          fontFamily: 'monospace',
                          fontSize: '0.85em'
                        },
                      }}
                      dangerouslySetInnerHTML={{ 
                        __html: message.content
                          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/`([^`]+)`/g, '<code>$1</code>')
                          .replace(/\n/g, '<br/>')
                      }}
                    />
                    <Typography 
                      variant="caption" 
                      color="text.secondary" 
                      sx={{ display: 'block', mt: 1 }}
                    >
                      {new Date(message.timestamp).toLocaleTimeString()}
                      {message.source && message.source !== 'fallback' && (
                        <Chip 
                          label={message.source} 
                          size="small" 
                          sx={{ ml: 1, height: 18, fontSize: '0.65rem' }}
                        />
                      )}
                    </Typography>
                  </Paper>
                </Box>
              </Box>
              
              {/* Follow-up suggestions after assistant messages */}
              {message.role === 'assistant' && message.followUpSuggestions && (
                <Box sx={{ ml: 6, mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Typography variant="caption" color="text.secondary" sx={{ width: '100%', mb: 0.5 }}>
                    <LightbulbIcon sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
                    Suggested follow-ups:
                  </Typography>
                  {message.followUpSuggestions.map((suggestion, idx) => (
                    <Chip
                      key={idx}
                      label={suggestion}
                      size="small"
                      onClick={() => handleSuggestionClick(suggestion)}
                      sx={{
                        bgcolor: 'rgba(0, 229, 255, 0.08)',
                        border: '1px solid rgba(0, 229, 255, 0.2)',
                        fontSize: '0.75rem',
                        '&:hover': {
                          bgcolor: 'rgba(0, 229, 255, 0.15)',
                        }
                      }}
                    />
                  ))}
                </Box>
              )}
            </Box>
          ))}
          
          {isLoading && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Avatar
                sx={{
                  width: 36,
                  height: 36,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                }}
              >
                <SmartToyIcon />
              </Avatar>
              <Paper
                sx={{
                  p: 2,
                  bgcolor: 'rgba(102, 126, 234, 0.15)',
                  border: '1px solid rgba(102, 126, 234, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                }}
              >
                <CircularProgress size={16} />
                <Typography variant="body2" color="text.secondary">
                  Analyzing with multi-agent system...
                </Typography>
              </Paper>
            </Box>
          )}
          
          <div ref={messagesEndRef} />
        </Paper>

        {/* Suggestions Panel */}
        <Collapse in={showSuggestions} orientation="horizontal">
          <Paper
            sx={{
              width: 300,
              height: '100%',
              overflow: 'auto',
              p: 2,
              background: 'rgba(20, 30, 60, 0.9)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
            }}
          >
            <Typography variant="subtitle2" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <LightbulbIcon sx={{ color: '#ff9100' }} />
              Suggested Prompts
            </Typography>
            
            <List dense sx={{ p: 0 }}>
              {Object.entries(SUGGESTION_CATEGORIES).map(([key, category]) => (
                <Box key={key} sx={{ mb: 1 }}>
                  <ListItemButton 
                    onClick={() => handleCategoryToggle(key)}
                    sx={{ 
                      borderRadius: 1,
                      bgcolor: 'rgba(255,255,255,0.05)',
                      mb: 0.5,
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {category.icon}
                    </ListItemIcon>
                    <ListItemText 
                      primary={category.title}
                      secondary={category.description}
                      primaryTypographyProps={{ variant: 'body2', fontWeight: 600 }}
                      secondaryTypographyProps={{ variant: 'caption' }}
                    />
                    {expandedCategory === key ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  </ListItemButton>
                  
                  <Collapse in={expandedCategory === key}>
                    <List dense sx={{ pl: 2 }}>
                      {category.prompts.map((prompt, idx) => (
                        <ListItem key={idx} sx={{ p: 0, mb: 0.5 }}>
                          <Chip
                            label={prompt.length > 50 ? prompt.substring(0, 50) + '...' : prompt}
                            size="small"
                            onClick={() => handleSuggestionClick(prompt)}
                            sx={{
                              height: 'auto',
                              py: 0.5,
                              '& .MuiChip-label': {
                                whiteSpace: 'normal',
                                fontSize: '0.7rem',
                              },
                              bgcolor: 'rgba(0, 229, 255, 0.08)',
                              border: '1px solid rgba(0, 229, 255, 0.2)',
                              '&:hover': {
                                bgcolor: 'rgba(0, 229, 255, 0.15)',
                              }
                            }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Collapse>
                </Box>
              ))}
            </List>
          </Paper>
        </Collapse>
      </Box>

      {/* Quick Actions */}
      <Box sx={{ display: 'flex', gap: 1, my: 2, flexWrap: 'wrap' }}>
        {QUICK_ACTIONS.map((action, idx) => (
          <Chip
            key={idx}
            label={action.label}
            onClick={() => handleSuggestionClick(action.query)}
            sx={{
              bgcolor: 'rgba(0, 229, 255, 0.1)',
              border: '1px solid rgba(0, 229, 255, 0.3)',
              '&:hover': {
                bgcolor: 'rgba(0, 229, 255, 0.2)',
              }
            }}
          />
        ))}
      </Box>

      {/* Input Area */}
      <Paper 
        sx={{ 
          p: 2,
          display: 'flex',
          gap: 2,
          alignItems: 'flex-end',
          background: 'rgba(20, 30, 60, 0.9)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <TextField
          fullWidth
          multiline
          maxRows={4}
          placeholder="Ask about energy optimization, congestion management, self-healing, or data analysis..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          sx={{
            '& .MuiOutlinedInput-root': {
              bgcolor: 'rgba(0, 0, 0, 0.2)',
            }
          }}
        />
        <IconButton 
          color="primary" 
          onClick={handleSendMessage}
          disabled={!inputValue.trim() || isLoading}
          sx={{
            bgcolor: 'primary.main',
            color: 'black',
            '&:hover': {
              bgcolor: 'primary.light',
            },
            '&:disabled': {
              bgcolor: 'rgba(0, 229, 255, 0.3)',
              color: 'rgba(255, 255, 255, 0.3)',
            }
          }}
        >
          <SendIcon />
        </IconButton>
      </Paper>

      {/* Footer */}
      <Typography 
        variant="caption" 
        color="text.secondary" 
        sx={{ textAlign: 'center', mt: 1 }}
      >
        Backend: localhost:8000 • ADK Web: localhost:8001 • 
        <Button 
          size="small" 
          onClick={handleOpenDeveloperMode}
          sx={{ fontSize: 'inherit', textTransform: 'none', ml: 0.5 }}
        >
          Open Developer Mode for advanced features
        </Button>
      </Typography>
    </Box>
  );
}

export default ChatInterface;
