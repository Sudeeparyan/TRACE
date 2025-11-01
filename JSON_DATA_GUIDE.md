# JSON Data Processing & LLM Analysis Guide

## Overview

TRACE now supports uploading JSON files containing network telemetry data and using LLM-powered analysis to get intelligent, context-aware recommendations for network optimization.

## Features

✅ **Load JSON Data**: Upload and validate JSON files with network metrics  
✅ **LLM Analysis**: AI-powered analysis of your network data  
✅ **Smart Recommendations**: Get actionable recommendations based on data patterns  
✅ **Compare Datasets**: Track changes between different time periods or configurations  
✅ **Context-Aware**: LLM understands your specific network conditions  

---

## Quick Start

### Step 1: Load Your JSON Data

```
Load the JSON data from data/trace_reduced_20.json
```

or

```
Add JSON data from d:/my_network_data.json
```

### Step 2: Get LLM Analysis

```
Analyze the loaded JSON data comprehensively
```

or for specific analysis:

```
Analyze the data for energy optimization opportunities
```

### Step 3: Get Recommendations

```
Give me recommendations based on the loaded data
```

or for specific towers:

```
Get recommendations for tower TX001
```

---

## Available Commands

### 1. Add/Load JSON Data

**Command**: `add_json_data(json_path)`

**What it does**: Loads and validates a JSON file

**Examples**:
```
Load data/trace_reduced_20.json
Add JSON file data/trace_llm_20.json
Import the JSON from d:/AI/network_metrics.json
```

**What you'll get**:
- ✅ Number of records loaded
- ✅ Sample data structure
- ✅ Available fields
- ✅ Validation status

---

### 2. Analyze Data with LLM

**Command**: `analyze_json_data_with_llm(analysis_type, focus_areas)`

**Analysis Types**:
- `comprehensive` - Full analysis (default)
- `energy` - Energy optimization focus
- `congestion` - Traffic and congestion management
- `health` - Network health and issues
- `prediction` - Trend prediction and forecasting

**Focus Areas** (optional):
- `towers` - Tower-specific analysis
- `regions` - Regional analysis
- `errors` - Error and failure patterns
- `performance` - Performance metrics
- `recommendations` - Actionable recommendations

**Examples**:
```
Analyze the data comprehensively

Analyze for energy optimization with focus on towers and recommendations

Give me a health analysis of the network

Predict future trends based on the loaded data

Analyze congestion patterns focusing on regions
```

**What you'll get**:
- 📊 Summary statistics (towers, regions, time span)
- 💡 Key insights and patterns
- 🎯 Actionable recommendations
- 📈 Trend analysis
- ⚠️ Risk identification

---

### 3. Get Specific Recommendations

**Command**: `get_recommendations_from_json(tower_id, region_id, metric_focus)`

**Parameters**:
- `tower_id` - Specific tower (e.g., "TX001")
- `region_id` - Specific region (e.g., "R-A")
- `metric_focus` - "all", "energy", "bandwidth", "latency", "errors"

**Examples**:
```
Get recommendations for all towers

Get recommendations for tower TX001

Give me energy recommendations for region R-A

What are the latency improvement recommendations?

Show me error resolution recommendations
```

**What you'll get**:
- 🔴 High priority actions
- 🟡 Medium priority improvements
- 📋 Specific action items
- 📍 Affected towers/regions
- 📊 Expected impact metrics

---

### 4. Compare Datasets

**Command**: `compare_json_datasets(json_path1, json_path2)`

**What it does**: Compares two JSON datasets to find changes and trends

**Examples**:
```
Compare data/trace_reduced_20.json with data/trace_llm_20.json

Compare yesterday's data with today's data

Show me the changes between baseline.json and current.json
```

**What you'll get**:
- 📈 Metric changes (bandwidth, latency, CPU)
- 🔄 Tower/region differences
- 📊 Percentage changes
- 📉 Trend direction (improving/degrading)

---

## Sample Workflows

### Workflow 1: Comprehensive Network Analysis

```
User: "Load data/trace_reduced_20.json"
→ System loads 20 records

User: "Analyze this data comprehensively"
→ LLM analyzes all aspects

User: "Give me the top 3 recommendations"
→ System provides prioritized actions
```

### Workflow 2: Energy Optimization Focus

```
User: "Add the JSON data from data/trace_reduced_20.json"
→ Data loaded successfully

User: "Analyze for energy optimization opportunities"
→ LLM identifies energy-saving patterns

User: "Get energy recommendations for all towers"
→ Specific energy-saving actions provided
```

### Workflow 3: Troubleshooting Specific Issues

```
User: "Load data/trace_reduced_20.json"
→ Data loaded

User: "Analyze network health focusing on errors"
→ Error patterns identified

User: "Get recommendations for error resolution"
→ Specific fixes suggested
```

### Workflow 4: Performance Tracking

```
User: "Compare last week's data with this week's data"
→ Loads both datasets

User: "What are the performance changes?"
→ Shows metrics that improved or degraded

User: "Give me recommendations based on the trends"
→ Proactive recommendations provided
```

---

## JSON Data Format

### Supported Formats

#### 1. Array of Records (Recommended)
```json
[
  {
    "timestamp": "2025-10-31T00:25:00+00:00",
    "region_id": "R-E",
    "tower_id": "TX005",
    "connected_users": 146,
    "bandwidth_utilization_pct": 20.89,
    "rsrq_db": -9.61,
    "latency_ms": 15,
    "detected_error": "high_cpu"
  },
  {
    "timestamp": "2025-10-31T01:25:00+00:00",
    "tower_id": "TX002",
    ...
  }
]
```

#### 2. Single Record
```json
{
  "timestamp": "2025-10-31T00:25:00+00:00",
  "tower_id": "TX001",
  "connected_users": 250,
  ...
}
```

### Key Fields (Recognized by LLM)

**Identifiers**:
- `timestamp` - Event timestamp
- `tower_id` - Tower identifier
- `region_id` - Region identifier

**Performance Metrics**:
- `connected_users` - Current users
- `bandwidth_utilization_pct` - Bandwidth usage %
- `latency_ms` - Network latency
- `cpu_util_pct` - CPU utilization %
- `rsrq_db` - Signal quality (dB)
- `packet_loss_pct` - Packet loss %

**Network State**:
- `tower_radius_km` - Current coverage radius
- `desired_radius_km` - Optimal radius
- `adjust_radius_action` - Recommended action ("expand", "shrink", "hold")
- `adjust_reason` - Reason for action
- `detected_error` - Error type ("none", "high_cpu", "packet_loss", etc.)

**Actions**:
- `action_executed` - Action taken
- `healed_now` - Whether issue was resolved
- `auto` - Automatic or manual action
- `human_in_loop` - Human intervention required

---

## Example Prompts

### Basic Loading
```
- "Load the JSON file data/trace_reduced_20.json"
- "Add data from data/trace_llm_20.json"
- "Import JSON from d:/network_data/tower_metrics.json"
```

### Analysis Requests
```
- "Analyze this data and tell me what you find"
- "Give me energy optimization insights from the data"
- "What congestion issues do you see?"
- "Analyze network health and identify problems"
- "Predict what will happen in the next hour based on patterns"
```

### Specific Recommendations
```
- "What should I do to optimize tower TX001?"
- "Give me recommendations for region R-A"
- "How can I reduce energy consumption?"
- "What can I do to improve latency?"
- "Show me error resolution steps"
```

### Comparisons
```
- "Compare yesterday's data with today's"
- "Has performance improved since last week?"
- "Show me the differences between baseline and current state"
```

### Combined Workflows
```
- "Load data/trace_reduced_20.json, analyze it for energy opportunities, and give me the top recommendations"
- "Import the data, analyze health issues, and tell me which towers need attention"
- "Load the JSON, compare it with last week's data, and recommend improvements"
```

---

## Understanding the Analysis Output

### Summary Section
- **Total Records**: Number of data points analyzed
- **Unique Towers**: Distinct towers in dataset
- **Unique Regions**: Distinct regions covered
- **Time Span**: Start and end timestamps

### Insights Section
Examples of insights you might see:

**Energy Insights**:
- "Energy Opportunity: 15 records (75%) show low bandwidth utilization (<30%), indicating potential for energy savings through radius reduction."
- "Energy Actions: 12 records (60%) recommend shrinking tower radius for energy efficiency. Average potential savings: 30-40%."

**Congestion Insights**:
- "Congestion Risk: 3 records (15%) show high bandwidth utilization (>70%), indicating potential congestion risk."
- "Coverage Expansion: 5 records recommend expanding coverage. Affected towers: TX001, TX003, TX005"

**Health Insights**:
- "Signal Quality: 8 records (40%) show poor RSRQ (<-10 dB), indicating signal quality issues."
- "Latency Issues: 4 records show high latency (>80ms). Average: 95.5ms"
- "Packet Loss: 2 records show significant packet loss (>1%). Average: 1.45%"

### Recommendations Section
Each recommendation includes:

- **Priority**: High, Medium, Low
- **Category**: Energy, Performance, Reliability, etc.
- **Title**: Brief summary
- **Description**: Detailed explanation
- **Affected Towers**: Specific towers impacted
- **Expected Impact**: Quantified benefits
- **Action Items**: Step-by-step actions

---

## Advanced Usage

### Custom Data Fields

The LLM can work with custom fields beyond the standard schema. Just include them in your JSON:

```json
{
  "tower_id": "TX001",
  "custom_metric": 42.5,
  "my_field": "important_value"
}
```

Ask questions like:
```
"Analyze the custom_metric field"
"What patterns do you see in my_field?"
```

### Multiple File Analysis

Load and compare multiple files:

```
User: "Load data/monday.json"
User: "Now load data/tuesday.json"
User: "Compare the two datasets"
```

### Time Series Analysis

For time-series data with timestamps:

```
User: "Load data/hourly_metrics.json"
User: "Analyze this as a time series and predict trends"
User: "What patterns emerge over the 24-hour period?"
```

---

## Troubleshooting

### "File not found" Error

**Problem**: JSON file path is incorrect

**Solutions**:
- Use absolute path: `d:/AI/data/file.json`
- Use relative path from TRACE root: `data/file.json`
- Check file exists: verify the file location

### "Invalid JSON format" Error

**Problem**: JSON syntax error

**Solutions**:
- Validate JSON at jsonlint.com
- Check for missing commas, brackets, or quotes
- Ensure UTF-8 encoding

### "No data loaded" Error

**Problem**: Trying to analyze before loading data

**Solution**:
- Always load data first: `Load data/trace_reduced_20.json`
- Then analyze: `Analyze the data`

### Empty or Unexpected Results

**Problem**: Filtering too aggressively

**Solutions**:
- Check tower_id spelling: "TX001" not "tx001"
- Verify region_id: "R-A" not "RA"
- Try broader queries first

---

## Best Practices

### 1. Start with Sample Data
Begin with the provided sample files:
- `data/trace_reduced_20.json` - 20 representative records
- `data/trace_llm_20.json` - 20 prompt-completion pairs

### 2. Load Before Analysis
Always follow this order:
1. Load data
2. Analyze data
3. Get recommendations

### 3. Be Specific
Instead of: "Analyze the data"
Try: "Analyze energy optimization opportunities focusing on towers with high CPU usage"

### 4. Iterate
```
1. Load data → Get overview
2. Analyze comprehensively → Identify areas
3. Focus on specific issues → Get detailed recommendations
4. Act on recommendations → Compare results
```

### 5. Use Context
The LLM remembers your conversation:
```
User: "Load data/trace_reduced_20.json"
User: "Analyze for energy"
User: "Now give me recommendations"  ← knows which data and analysis
```

---

## Integration Examples

### Python Script Integration

```python
# In your custom script
from principal_agent.tools.json_data_processor import (
    add_json_data,
    analyze_json_data_with_llm,
    get_recommendations_from_json
)

# Load data
result = add_json_data("data/trace_reduced_20.json")
print(f"Loaded {result['num_records']} records")

# Analyze
analysis = analyze_json_data_with_llm("energy", ["towers", "recommendations"])
print(analysis['analysis']['insights'])

# Get recommendations
recs = get_recommendations_from_json(metric_focus="energy")
for rec in recs['recommendations']:
    print(f"{rec['priority']}: {rec['title']}")
```

### Workflow Agent Integration

Add JSON processing to your custom workflow agents by importing the tools.

---

## Example Session

```
🧑 User: Hi! I have some network data I'd like to analyze.

🤖 Agent: Great! I can help you analyze your network data. Please provide the path to your JSON file, or use one of our sample datasets like data/trace_reduced_20.json.

🧑 User: Load data/trace_reduced_20.json

🤖 Agent: ✅ Successfully loaded 20 records from trace_reduced_20.json
- Data type: array of records
- Fields: timestamp, region_id, tower_id, connected_users, bandwidth_utilization_pct, rsrq_db, latency_ms, cpu_util_pct, detected_error, and more
- Time span: 2025-10-31T00:25:00 to 2025-10-31T13:45:00

🧑 User: Analyze this data for energy optimization

🤖 Agent: 📊 Analysis Results:

Summary:
- Total records: 20
- Unique towers: 5 (TX001, TX002, TX003, TX005, TX008)
- Unique regions: 5 (R-A, R-B, R-C, R-D, R-E)

Key Insights:
✅ Energy Opportunity: 15 records (75%) show low bandwidth utilization (<30%), indicating potential for 30-40% energy savings through radius reduction
✅ 12 records recommend shrinking tower radius during identified low-traffic periods

Would you like specific recommendations?

🧑 User: Yes, give me the top recommendations

🤖 Agent: 🎯 Top Recommendations:

1. 🔴 HIGH PRIORITY - Implement Energy Saving Mode
   - Category: Energy Optimization
   - Affected towers: TX001, TX002, TX003, TX005, TX008
   - Expected impact: 30-40% energy savings
   - Action items:
     • Schedule partial TRX shutdowns during low-traffic periods (identified in analysis)
     • Monitor user experience metrics during optimization
     • Gradually expand energy-saving periods

2. 🟡 MEDIUM PRIORITY - Reduce Network Latency
   - Category: Performance
   - Affected towers: TX002, TX005
   - Expected impact: 20-30% latency reduction
   - Action items:
     • Optimize routing paths
     • Check for backhaul congestion
     • Review QoS policies

3. 🔴 HIGH PRIORITY - Address Network Errors
   - Category: Reliability
   - 5 error events detected (high_cpu, packet_loss)
   - Action items:
     • Investigate high_cpu errors (most common)
     • Schedule preventive maintenance
     • Review error thresholds and alerts

🧑 User: Perfect! Let me work on these recommendations.

🤖 Agent: Excellent! I'll be here if you need further analysis or want to compare results after implementing these changes. You can always use compare_json_datasets() to track improvements over time.
```

---

## Summary

You now have powerful LLM-driven JSON analysis capabilities in TRACE:

✅ **Load any JSON file** with network telemetry data  
✅ **Get AI-powered insights** from your specific data  
✅ **Receive actionable recommendations** tailored to your network  
✅ **Compare datasets** to track improvements  
✅ **Context-aware analysis** that understands your network conditions  

Start with: `Load data/trace_reduced_20.json` and explore!

---

**Need Help?**
- Check the example prompts above
- Try the sample workflows
- Start simple and iterate

**Happy Analyzing! 🚀**
