# TRACE Demo - Prompts Cheatsheet

## Quick Reference for Live Demo

---

## 🎬 Demo Sequence

### 1. System Health Check (2 min)
```
Check the overall system health and provide a comprehensive report
```

---

### 2. Energy Optimization (3 min)
```
Analyze energy consumption patterns for tower_5. Forecast traffic for the next 4 hours and recommend optimization strategies to achieve 30-40% energy savings.
```

---

### 3. Congestion Management (3 min)
```
There's a major concert at the stadium tonight at 8 PM. Predict the traffic surge, assess congestion risk, and prepare a load balancing strategy to maintain service quality.
```

---

### 4. Self-Healing (2 min)
```
Simulate a failure scenario: The monitoring agent at tower_12 has stopped responding to heartbeat checks. Show me the self-healing response and remediation process.
```

---

### 5. JSON Data Analysis ✨ NEW (3 min)

#### 5a. Load Data
```
Load the JSON data from data/trace_reduced_20.json
```

#### 5b. Comprehensive Analysis (UPDATED - Safer)
```
Analyze this data for energy optimization and provide top recommendations with expected impact.
```

**Alternative (if above times out):**
```
Get energy recommendations from the loaded data
```

#### 5c. Specific Recommendations
```
Give me specific recommendations for energy optimization with action items and expected impact.
```

#### 5d. Tower-Specific (Optional)
```
Get detailed recommendations for tower TX005 focusing on all metrics.
```

#### 5e. Dataset Comparison (Optional)
```
Compare data/trace_reduced_20.json with data/trace_llm_20.json and show me the key differences.
```

---

## 🎯 Alternative/Backup Prompts

### Energy Optimization (Alternative)
```
Show me energy savings opportunities across all towers in region R-A for the next 6 hours.
```

### Congestion (Alternative)
```
Analyze potential congestion risks for all towers and recommend proactive load balancing strategies.
```

### Self-Healing (Alternative)
```
The action agent at tower_8 has failed. Execute the remediation workflow and restore service.
```

### JSON Analysis (Alternative)
```
Analyze the loaded data for network health issues and prioritize the most critical problems.
```

---

## 💡 Quick Tips

- **Copy prompts in advance** - have them ready to paste
- **Explain before executing** - tell audience what you're doing
- **Narrate the response** - highlight key points as system responds
- **Connect to value** - always explain WHY this matters
- **Have backups ready** - screenshots or alternative prompts

---

## ⏱️ Time Management

- Part 1 (Health): 2 min
- Part 2 (Energy): 3 min  
- Part 3 (Congestion): 3 min
- Part 4 (Self-Healing): 2 min
- Part 5 (JSON): 3 min ← **Can be skipped if short on time**
- Closing: 2 min

**Total**: 15 minutes (or 12 without JSON demo)

---

## 🎨 Presentation Notes

### After Each Prompt:

**Energy Demo**: 
- Highlight: "30-40% savings, Sequential workflow, No service impact"

**Congestion Demo**: 
- Highlight: "Proactive prevention, Zero dropped calls, Predictive capability"

**Self-Healing Demo**: 
- Highlight: "Autonomous recovery, <5 min MTTR, No human needed"

**JSON Demo**: 
- Highlight: "Natural language, Context-aware, Historical analysis"

---

## 📋 Pre-Demo Checklist

- [ ] `adk web` running
- [ ] Browser at http://localhost:8000
- [ ] `principal_agent` selected
- [ ] This cheatsheet open
- [ ] `data/trace_reduced_20.json` exists
- [ ] Backup screenshots ready
- [ ] Timer set for 15 minutes

---

## 🚨 Emergency Prompts (If Something Fails)

### If 500 Error Occurs During JSON Analysis

**Option 1: Simpler Analysis**
```
Get energy recommendations from the loaded data
```

**Option 2: Tower-Specific**
```
Get recommendations for tower TX005 focusing on energy metrics
```

**Option 3: Skip Analysis, Go to Comparison**
```
Compare data/trace_reduced_20.json with data/trace_llm_20.json
```

**Option 4: Restart Fresh**
1. Refresh browser page
2. Create new session
3. Try: `Load data/trace_reduced_20.json`
4. Then: `Get energy recommendations`

### Other Generic Fallbacks

### Generic Health Check
```
Show me the current status of all agents in the system.
```

### Simple Energy Query
```
What energy optimization opportunities exist right now?
```

### Basic Data Load
```
Load data/trace_reduced_20.json
```

### Simple Analysis
```
Analyze this data
```

---

## 🎤 Key Points to Mention

✅ Hierarchical multi-agent architecture  
✅ 7 specialized agents working together  
✅ 35+ tools (including 4 new JSON tools)  
✅ Autonomous operation  
✅ Safety-first approach  
✅ Natural language interface  
✅ Production-ready design  
✅ Real-world ROI ($4.5-7M annually)  

---

## 🎯 Closing Highlights

- **30-40% energy savings**
- **Zero service degradation**
- **<5 minute recovery**
- **AI-powered insights**
- **Natural language interface**
- **Production ready**

---

**Print this page and have it next to you during the demo! 📄**
