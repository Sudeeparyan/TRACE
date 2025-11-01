# TRACE Data Usage Guide

## Overview

This guide explains the data structure and how to use the reduced dataset for LLM training and agent development.

## Why Reduced Data?

The original dataset (`trace_radius_events_small.json`) contains **15,362 lines** which can overwhelm LLM context windows and slow down learning. The reduced dataset maintains all structural diversity while being more digestible for LLMs.

### Benefits of Reduced Data:
- ✅ **Faster Learning**: LLMs understand patterns with less data
- ✅ **Better Context**: Fits within LLM context windows
- ✅ **Maintained Diversity**: All event types, errors, and scenarios preserved
- ✅ **Lower Costs**: Reduced token usage for API calls
- ✅ **Faster Development**: Quicker iteration cycles

## Dataset Files

### Original Files
Located in `data/`:
- `trace_radius_events_small.json` - 480 events, ~15,362 lines
- `trace_radius_incidents_small.json` - Empty (placeholder)
- `trace_radius_schema.json` - Data schema definition

### Reduced Files
Also in `data/`:
- `trace_radius_events_reduced.json` - **146 events, ~4,674 lines** ✨
- `trace_radius_incidents_reduced.json` - Empty (placeholder)

## Data Structure

### Events Schema

Each event in the dataset contains:

```json
{
  "timestamp": "2025-10-31T00:00:00+00:00",
  "region_id": "R-A",
  "tower_id": "TX001",
  "agent_id": "agent-tx001",
  "neighbors": ["TX005", "TX002"],
  "capacity_users": 1500,
  "connected_users": 114,
  "bandwidth_utilization_pct": 8.0,
  "rsrq_db": -8.8,
  "packet_loss_pct": 0.33,
  "latency_ms": 41,
  "cpu_util_pct": 42,
  "power_voltage_v": 48.2,
  "event_type": "normal",
  "tower_radius_km": 1.27,
  "desired_radius_km": 1.07,
  "coverage_gap_pct": 45.2,
  "adjust_radius_action": "shrink",
  "adjust_reason": "low_demand_energy_save",
  "detected_error": "none",
  "detection_confidence": 0.5,
  "signals_used": [],
  "action_executed": "shrink_radius",
  "action_reason": "low_demand_energy_save",
  "healed_now": true,
  "auto": true,
  "human_in_loop": false
}
```

### Key Fields Explained

**Identifiers:**
- `timestamp`: ISO8601 UTC timestamp
- `region_id`: Regional identifier (R-A, R-B, R-C, etc.)
- `tower_id`: Tower identifier (TX001, TX002, etc.)
- `agent_id`: Edge agent identifier

**Network Metrics:**
- `connected_users`: Current active users
- `capacity_users`: Maximum tower capacity
- `bandwidth_utilization_pct`: Percentage of bandwidth in use
- `rsrq_db`: Reference Signal Received Quality (lower = worse)
- `packet_loss_pct`: Packet loss percentage
- `latency_ms`: Network latency in milliseconds
- `cpu_util_pct`: Tower CPU utilization

**Power & Coverage:**
- `power_voltage_v`: Power supply voltage (~48V nominal)
- `tower_radius_km`: Current coverage radius
- `desired_radius_km`: Optimal radius based on policy
- `coverage_gap_pct`: Unserved demand estimate

**Event Classification:**
- `event_type`: "normal", "concert", "emergency", "maintenance"
- `detected_error`: "none", "high_cpu", "packet_loss", "radio_failure", "power_outage", "coverage_gap"
- `detection_confidence`: 0.0 to 1.0

**Actions:**
- `adjust_radius_action`: "expand", "shrink", "hold"
- `action_executed`: Actual action taken
- `auto`: Whether action was automatic
- `human_in_loop`: Whether human intervention was required

## Reduced Dataset Statistics

### Event Distribution
```
Total Events: 146
Event Types:
  - normal: 144
  - emergency: 1
  - maintenance: 1

Error Types:
  - none: 146

Unique Towers: 5 (TX001, TX002, TX003, TX004, TX005)
Unique Regions: 5 (R-A, R-B, R-C, R-D, R-E)
```

### Data Coverage
- **Temporal**: Events span 24 hours with 15-minute intervals
- **Spatial**: All 5 towers and regions represented
- **Operational**: Normal operations, energy saving, radius adjustments

## How to Use the Data

### 1. For Agent Development

Load the reduced data in your agent tools:

```python
import json
from pathlib import Path

def load_trace_data():
    """Load the reduced TRACE dataset."""
    data_dir = Path(__file__).parent.parent / "data"
    events_file = data_dir / "trace_radius_events_reduced.json"
    
    with open(events_file, 'r') as f:
        events = json.load(f)
    
    return events

# Use in monitoring agent
events = load_trace_data()
# Filter events for specific tower
tower_events = [e for e in events if e['tower_id'] == 'TX001']
```

### 2. For LLM Training/Fine-tuning

Create training examples from the data:

```python
def create_training_examples(events):
    """Convert events to LLM training format."""
    examples = []
    
    for event in events:
        # Create input context
        context = f"""
Tower: {event['tower_id']}
Users: {event['connected_users']}/{event['capacity_users']}
Bandwidth: {event['bandwidth_utilization_pct']}%
RSRQ: {event['rsrq_db']} dB
Latency: {event['latency_ms']} ms
Current Radius: {event['tower_radius_km']} km
        """
        
        # Create expected output
        output = f"""
Recommended Action: {event['adjust_radius_action']}
Reason: {event['adjust_reason']}
Desired Radius: {event['desired_radius_km']} km
        """
        
        examples.append({
            "input": context.strip(),
            "output": output.strip()
        })
    
    return examples
```

### 3. For Pattern Analysis

Analyze energy-saving patterns:

```python
def analyze_energy_patterns(events):
    """Analyze energy optimization patterns."""
    shrink_events = [e for e in events if e['adjust_radius_action'] == 'shrink']
    
    avg_users_shrink = sum(e['connected_users'] for e in shrink_events) / len(shrink_events)
    avg_utilization = sum(e['bandwidth_utilization_pct'] for e in shrink_events) / len(shrink_events)
    
    print(f"Energy-saving threshold patterns:")
    print(f"  Avg users during shrink: {avg_users_shrink:.1f}")
    print(f"  Avg bandwidth during shrink: {avg_utilization:.1f}%")
    
    return {
        'shrink_user_threshold': avg_users_shrink,
        'shrink_bandwidth_threshold': avg_utilization
    }
```

### 4. For Agent Tool Integration

Example tool using the data:

```python
from google.adk.tools import tool

@tool
def analyze_tower_health(tower_id: str) -> dict:
    """
    Analyze tower health using historical TRACE data.
    
    Args:
        tower_id: Tower identifier (e.g., "TX001")
        
    Returns:
        Health analysis with recommendations
    """
    events = load_trace_data()
    tower_events = [e for e in events if e['tower_id'] == tower_id]
    
    if not tower_events:
        return {"error": f"No data found for tower {tower_id}"}
    
    # Calculate health metrics
    latest = tower_events[-1]
    avg_bandwidth = sum(e['bandwidth_utilization_pct'] for e in tower_events) / len(tower_events)
    avg_latency = sum(e['latency_ms'] for e in tower_events) / len(tower_events)
    
    # Determine health status
    health_score = 100
    if latest['packet_loss_pct'] > 1.0:
        health_score -= 20
    if latest['latency_ms'] > 80:
        health_score -= 15
    if latest['cpu_util_pct'] > 70:
        health_score -= 10
    
    return {
        "tower_id": tower_id,
        "health_score": health_score,
        "current_users": latest['connected_users'],
        "avg_bandwidth": round(avg_bandwidth, 1),
        "avg_latency": round(avg_latency, 1),
        "recommendation": "healthy" if health_score > 80 else "needs_attention"
    }
```

## Generating More Data

If you need to regenerate or create custom reduced datasets:

```bash
cd TRACE
python reduce_data.py
```

The script will:
1. Analyze the original data
2. Select diverse representative samples
3. Maintain all data structure patterns
4. Create new reduced files
5. Show statistics and diversity metrics

### Customization

Edit `reduce_data.py` to adjust:
- `target_count` parameter in `reduce_events_data()` - change from 150 to your desired size
- Sampling strategy - modify selection criteria
- Output filenames - change output paths

Example:
```python
# For even smaller dataset
reduced_events = reduce_events_data(events_info['data'], target_count=50)

# For larger dataset
reduced_events = reduce_events_data(events_info['data'], target_count=300)
```

## Best Practices

### 1. Start Small
- Begin development with the reduced dataset (146 events)
- Validate your logic and patterns
- Scale up to full dataset only when needed

### 2. Understand Patterns First
- Analyze the reduced data manually
- Identify key patterns and thresholds
- Use insights to design agent behavior

### 3. Test with Diverse Scenarios
The reduced dataset includes:
- Low traffic periods (early morning)
- Peak traffic (midday, evening)
- Different tower loads
- Energy-saving scenarios
- Normal operations

### 4. Iterate Quickly
- Use reduced data for fast prototyping
- Test agent responses
- Refine prompts and logic
- Deploy to full dataset when ready

## Integration with TRACE Agents

### Monitoring Agent
```python
# In monitoring_agent/tools.py
from pathlib import Path
import json

def get_historical_kpis(tower_id: str) -> list:
    """Get historical KPI data for tower."""
    data_dir = Path(__file__).parent.parent.parent.parent / "data"
    events_file = data_dir / "trace_radius_events_reduced.json"
    
    with open(events_file) as f:
        events = json.load(f)
    
    return [e for e in events if e['tower_id'] == tower_id]
```

### Prediction Agent
```python
# In prediction_agent/tools.py
def predict_next_demand(tower_id: str, current_hour: int) -> dict:
    """Predict demand based on historical patterns."""
    historical_data = get_historical_kpis(tower_id)
    
    # Filter for similar time periods
    similar_periods = [
        e for e in historical_data 
        if int(e['timestamp'].split('T')[1].split(':')[0]) == current_hour
    ]
    
    avg_users = sum(e['connected_users'] for e in similar_periods) / len(similar_periods)
    
    return {
        "predicted_users": int(avg_users),
        "confidence": 0.8,
        "basis": "historical_pattern"
    }
```

### Decision xApp Agent
```python
# In decision_xapp_agent/tools.py
def recommend_radius_adjustment(tower_data: dict) -> dict:
    """Recommend radius adjustment based on policy and data."""
    # Load historical patterns
    historical = get_historical_kpis(tower_data['tower_id'])
    
    # Find similar situations
    similar = [
        e for e in historical
        if abs(e['connected_users'] - tower_data['users']) < 20
    ]
    
    # Determine recommendation based on patterns
    if similar:
        most_common_action = max(
            set(e['adjust_radius_action'] for e in similar),
            key=lambda x: sum(1 for e in similar if e['adjust_radius_action'] == x)
        )
        return {"action": most_common_action, "confidence": 0.85}
    
    return {"action": "hold", "confidence": 0.5}
```

## Troubleshooting

### File Not Found
```python
# Use absolute paths
from pathlib import Path
data_dir = Path(__file__).resolve().parent.parent / "data"
```

### Large File Loading
```python
# Use streaming for very large files
import ijson

def stream_events(filename):
    with open(filename, 'rb') as f:
        for event in ijson.items(f, 'item'):
            yield event
```

### Memory Issues
```python
# Process in chunks
def process_in_chunks(events, chunk_size=50):
    for i in range(0, len(events), chunk_size):
        chunk = events[i:i+chunk_size]
        process_chunk(chunk)
```

## Summary

The reduced dataset provides:
- ✅ **4,674 lines** vs 15,362 (70% reduction)
- ✅ **146 events** covering all patterns
- ✅ **5 towers, 5 regions** - full spatial coverage
- ✅ **24-hour timeline** - full temporal coverage
- ✅ **All event types** - normal, emergency, maintenance
- ✅ **Diverse scenarios** - energy saving, peak load, normal ops

**Use `trace_radius_events_reduced.json` for:**
- LLM training and fine-tuning
- Agent development and testing
- Pattern analysis and learning
- Quick prototyping and iteration

**Switch to `trace_radius_events_small.json` for:**
- Production deployments
- Full historical analysis
- Comprehensive testing
- Final validation

---

**Happy Building! 🚀**
