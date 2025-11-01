# TRACE - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Setup Environment

1. **Navigate to TRACE directory**:
```cmd
cd d:\AI\AI_Implementation\ADK-End-to-End\TRACE
```

2. **Create virtual environment**:
```cmd
python -m venv .venv
```

3. **Activate virtual environment**:
```cmd
.venv\Scripts\activate.bat
```

4. **Install dependencies**:
```cmd
pip install -r requirements.txt
```

### Step 2: Configure API Keys

1. **Copy environment template**:
```cmd
copy .env.example .env
```

2. **Edit `.env` file** and add your Google API key:
```
GOOGLE_API_KEY=your_actual_google_api_key_here
```

### Step 3: Run TRACE

1. **Start the ADK web interface**:
```cmd
adk web
```

2. **Open your browser** to: `http://localhost:8000`

3. **Select agent** from dropdown: `principal_agent`

### Step 4: Try Example Prompts

**System Health Check:**
```
Check the overall system health and provide a comprehensive report
```

**Energy Optimization:**
```
Analyze energy consumption patterns and recommend optimization strategies for the next 4 hours
```

**Traffic Prediction:**
```
Forecast traffic load for tower_5 for the next 6 hours and identify opportunities for energy savings
```

**Congestion Management:**
```
There's a major concert happening tonight at the stadium. Predict potential congestion and prepare a load balancing strategy
```

**Self-Healing Scenario:**
```
Simulate a failure scenario: tower_7 agent is unresponsive. Show me the self-healing response
```

**Performance Analysis:**
```
Analyze the performance of our energy optimization over the last 24 hours
```

**JSON Data Analysis (NEW!):**
```
Load data/trace_reduced_20.json
```

```
Analyze this data for energy optimization opportunities
```

```
Get recommendations for tower TX001
```

```
Compare data/trace_reduced_20.json with data/trace_llm_20.json
```

## 📋 Agent Hierarchy

When interacting with TRACE, you can:

1. **Talk to Principal Agent** (recommended): Gets system-wide view and can coordinate all agents
2. **Access Parent Agent**: For regional-level operations
3. **Query Edge Agents**: For specific tower or function details

### Available Agents:

- **principal_agent** - Global orchestrator (start here!)
- **regional_coordinator** - Regional management
- **monitoring_agent** - Data collection
- **prediction_agent** - Traffic forecasting
- **decision_xapp_agent** - Policy decisions
- **action_agent** - Execute commands
- **learning_agent** - Model training

## 🎯 Common Tasks

### Check System Status
```
Generate a health dashboard for all systems
```

### Energy Optimization
```
What are the current energy savings? Can we optimize further?
```

### Handle Traffic Surge
```
Detect any predicted traffic surges and prepare contingency plans
```

### Model Performance
```
How are our prediction models performing? Do they need retraining?
```

## 🔧 Troubleshooting

### Issue: `Module not found` errors
**Solution**: Make sure virtual environment is activated and dependencies are installed
```cmd
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Issue: `GOOGLE_API_KEY not found`
**Solution**: Ensure `.env` file exists with valid API key
```cmd
copy .env.example .env
# Edit .env and add your key
```

### Issue: ADK web not starting
**Solution**: Check if port 8000 is available
```cmd
# Try with different port
adk web --port 8080
```

### Issue: Agent not appearing in dropdown
**Solution**: Verify directory structure and __init__.py files
```cmd
# Check that you're in TRACE directory
cd d:\AI\AI_Implementation\ADK-End-to-End\TRACE
# Restart adk web
adk web
```

## 📚 Next Steps

1. **Explore Workflows**: Try the sequential and parallel workflow examples
2. **Customize Tools**: Modify tools in `tools/` directories to match your needs
3. **Add Real Data**: Replace simulated data with real telemetry integration
4. **Deploy to AWS**: Follow deployment guide for production setup

## 💡 Tips

- The Principal Agent can coordinate all other agents - it's your main entry point
- Each Edge Agent specializes in one aspect (monitoring, prediction, decisions, actions, learning)
- Workflows combine multiple agents for complex tasks (energy optimization, congestion management)
- The self-healing loop runs automatically to detect and fix issues
- **NEW**: Upload your own JSON data for custom analysis and recommendations

## 🆕 JSON Data Processing (NEW!)

TRACE can now analyze your custom JSON data files! 

**Try it:**
1. Load sample data: `Load data/trace_reduced_20.json`
2. Analyze: `Analyze for energy optimization`
3. Get recommendations: `Give me the top recommendations`

**Learn more**: See `JSON_DATA_GUIDE.md` for complete documentation

## 🤝 Need Help?

- Check `README.md` for detailed documentation
- Review `docs/architecture.md` for system design
- Contact: sudeeparyang@gmail.com

---

**Enjoy using TRACE! 🎉**
