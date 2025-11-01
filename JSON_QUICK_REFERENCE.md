# JSON Data Processing - Quick Reference Card

## 🚀 Quick Start (3 Steps)

```cmd
1. cd d:\AI\AI_Implementation\ADK-End-to-End\AWS\TRACE
2. adk web
3. Open http://localhost:8000 → Select "principal_agent"
```

---

## 💬 Basic Commands

### Load Data
```
Load data/trace_reduced_20.json
Add the JSON file from data/trace_llm_20.json
Import my data from d:/network_metrics.json
```

### Analyze Data
```
Analyze this data comprehensively
Analyze for energy optimization
Analyze for congestion issues
Analyze network health
Predict future trends
```

### Get Recommendations
```
Give me recommendations
Get recommendations for tower TX001
Show me energy-saving recommendations
What should I do about region R-A?
```

### Compare Datasets
```
Compare data/trace_reduced_20.json with data/trace_llm_20.json
Compare yesterday's data with today's
Show me the changes
```

---

## 🔧 4 Core Tools

| Tool | Purpose | Example |
|------|---------|---------|
| `add_json_data()` | Load & validate JSON | Load data/file.json |
| `analyze_json_data_with_llm()` | AI analysis | Analyze for energy |
| `get_recommendations_from_json()` | Get recommendations | Recommend for TX001 |
| `compare_json_datasets()` | Compare data | Compare file1 with file2 |

---

## 📊 Analysis Types

| Type | Focus | Use When |
|------|-------|----------|
| `comprehensive` | Everything | General overview |
| `energy` | Energy optimization | Want to save power |
| `congestion` | Traffic management | Managing load |
| `health` | Network health | Troubleshooting |
| `prediction` | Trends & forecasts | Planning ahead |

---

## 🎯 Focus Areas (Optional)

- `towers` - Tower-specific analysis
- `regions` - Regional analysis  
- `errors` - Error patterns
- `performance` - Performance metrics
- `recommendations` - Action items

**Example**: `Analyze for energy with focus on towers and recommendations`

---

## 📝 JSON Format (Simple)

```json
[
  {
    "timestamp": "2025-10-31T00:25:00+00:00",
    "tower_id": "TX001",
    "bandwidth_utilization_pct": 20.89,
    "latency_ms": 15,
    "detected_error": "none"
  }
]
```

**Key fields recognized**:
- `tower_id`, `region_id` - Identifiers
- `bandwidth_utilization_pct` - Usage %
- `latency_ms` - Latency
- `cpu_util_pct` - CPU usage
- `detected_error` - Error type
- `connected_users` - User count

---

## 🎨 Example Workflow

```
Step 1: Load
  "Load data/trace_reduced_20.json"
  → ✅ Loaded 20 records

Step 2: Analyze  
  "Analyze for energy optimization"
  → 📊 Found 15 low-usage records
  → 💡 30-40% savings possible

Step 3: Recommend
  "Give me top 3 recommendations"
  → 🎯 1. Energy Saving Mode (HIGH)
  → 🎯 2. Reduce Latency (MEDIUM)
  → 🎯 3. Fix Errors (HIGH)
```

---

## 📖 Output Format

### Summary
- Total records
- Unique towers/regions
- Time span

### Insights (Examples)
- "Energy Opportunity: 75% records show low usage"
- "Congestion Risk: 3 records show high bandwidth"
- "Signal Quality: 8 records show poor RSRQ"

### Recommendations
- **Priority**: High/Medium/Low
- **Category**: Energy/Performance/Reliability
- **Impact**: Expected benefits
- **Actions**: What to do

---

## ⚡ Pro Tips

✅ Load data first, then analyze  
✅ Start with comprehensive analysis  
✅ Be specific in your questions  
✅ Use sample data for testing  
✅ Compare datasets to track progress  

---

## 🐛 Troubleshooting

**"File not found"**
→ Check path, use absolute path

**"Invalid JSON"**  
→ Validate at jsonlint.com

**"No data loaded"**
→ Load data before analyzing

**Empty results**
→ Check tower_id spelling (case-sensitive)

---

## 📚 Documentation

- **Full Guide**: `JSON_DATA_GUIDE.md` (900+ lines)
- **Examples**: `example_json_usage.py` (Runnable)
- **Technical**: `JSON_IMPLEMENTATION_SUMMARY.md`
- **Quick Start**: `QUICKSTART.md`

---

## 💻 Python API (Advanced)

```python
from principal_agent.tools.json_data_processor import (
    add_json_data,
    analyze_json_data_with_llm,
    get_recommendations_from_json
)

# Load
result = add_json_data("data/trace_reduced_20.json")

# Analyze
analysis = analyze_json_data_with_llm("energy", ["towers"])

# Recommend
recs = get_recommendations_from_json(tower_id="TX001")
```

---

## 🎯 Common Use Cases

### Energy Optimization
```
Load data → Analyze energy → Get recommendations
Expected: 30-40% savings opportunities
```

### Troubleshooting
```
Load data → Analyze health → Get error fixes
Expected: Root cause identification
```

### Performance Tracking
```
Load baseline → Load current → Compare
Expected: Metric improvements shown
```

### Predictive Planning
```
Load historical → Analyze predictions → Plan ahead
Expected: Trend forecasts
```

---

## ✨ Features

✅ Any JSON structure  
✅ Natural language  
✅ AI-powered insights  
✅ Prioritized recommendations  
✅ Dataset comparison  
✅ Custom fields supported  

---

## 🎊 Sample Files Included

- `data/trace_reduced_20.json` (20 records)
- `data/trace_llm_20.json` (20 LLM pairs)
- `data/trace_reduced_20.csv` (CSV format)

---

## 📞 Need Help?

1. Check `JSON_DATA_GUIDE.md`
2. Run `example_json_usage.py`
3. Try sample data first
4. Contact: sudeeparyang@gmail.com

---

**Quick Start Again:**
```
adk web → http://localhost:8000 → "Load data/trace_reduced_20.json"
```

**That's it! Start analyzing! 🚀**
