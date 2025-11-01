"""
JSON Data Processor Tool for TRACE System

This tool allows users to:
1. Add/upload JSON files with network telemetry data
2. Process and validate the JSON data
3. Send the data to LLM for context-aware analysis
4. Get intelligent recommendations based on the data
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


def add_json_data(json_path: str) -> dict:
    """
    Load and validate JSON data from a file path.

    This tool reads a JSON file containing network telemetry data and validates
    its structure. Use this when you want to add new data for analysis.

    Args:
        json_path: Absolute or relative path to the JSON file

    Returns:
        dict: Status information including number of records loaded and sample data

    Example:
        add_json_data("data/trace_reduced_20.json")
        add_json_data("d:/path/to/my_network_data.json")
    """
    try:
        # Convert to Path object
        json_file = Path(json_path)

        # If relative path, make it relative to TRACE root
        if not json_file.is_absolute():
            trace_root = Path(__file__).parent.parent.parent
            json_file = trace_root / json_path

        # Check if file exists
        if not json_file.exists():
            return {
                "status": "error",
                "message": f"File not found: {json_file}",
                "suggestion": "Please provide a valid file path",
            }

        # Load JSON data
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate data structure
        if isinstance(data, list):
            num_records = len(data)
            data_type = "array of records"
            sample = data[0] if data else {}
        elif isinstance(data, dict):
            num_records = 1
            data_type = "single record"
            sample = data
        else:
            return {
                "status": "error",
                "message": "Invalid JSON structure",
                "suggestion": "JSON should be an array of objects or a single object",
            }

        # Store data in session for later use (simplified - in production use proper state management)
        global _loaded_json_data
        _loaded_json_data = {
            "path": str(json_file),
            "data": data,
            "loaded_at": datetime.now().isoformat(),
            "num_records": num_records,
        }

        return {
            "status": "success",
            "message": f"Successfully loaded {num_records} records from {json_file.name}",
            "file_path": str(json_file),
            "num_records": num_records,
            "data_type": data_type,
            "sample_record": sample,
            "fields": list(sample.keys()) if isinstance(sample, dict) else [],
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}",
            "suggestion": "Please check if the file contains valid JSON",
        }
    except Exception as e:
        return {"status": "error", "message": f"Error loading file: {str(e)}"}


def analyze_json_data_with_llm(
    analysis_type: str = "comprehensive", focus_areas: Optional[List[str]] = None
) -> dict:
    """
    Analyze previously loaded JSON data for network insights and recommendations.

    This tool provides intelligent analysis of the loaded telemetry data with
    actionable recommendations for optimization and issue resolution.

    Args:
        analysis_type: Type of analysis to perform:
            - "comprehensive": Full analysis (default)
            - "energy": Energy optimization focus
            - "congestion": Traffic management focus
            - "health": Network health focus
            - "prediction": Trend analysis
        focus_areas: Optional list of aspects to focus on:
            - "towers": Tower-specific analysis
            - "regions": Regional analysis
            - "errors": Error patterns
            - "performance": Performance metrics
            - "recommendations": Actionable items

    Returns:
        dict: Structured analysis with insights and recommendations

    Example:
        analyze_json_data_with_llm("energy", ["towers", "recommendations"])
        analyze_json_data_with_llm("comprehensive")
    """
    try:
        # Check if data is loaded
        global _loaded_json_data
        if "_loaded_json_data" not in globals() or _loaded_json_data is None:
            return {
                "status": "error",
                "message": "No JSON data loaded",
                "suggestion": "Please use add_json_data() first to load a JSON file",
            }

        data = _loaded_json_data["data"]
        num_records = _loaded_json_data["num_records"]

        # Set default focus areas if not provided
        if focus_areas is None:
            focus_areas = ["performance", "recommendations"]

        # Limit data size to prevent API overload
        max_records = 50
        if isinstance(data, list) and len(data) > max_records:
            # Sample data intelligently
            data_sample = _sample_data_intelligently(data, max_records)
            sampled = True
        else:
            data_sample = data
            sampled = False

        # Perform analysis based on type (using summarized data, not raw)
        analysis_results = _perform_analysis(data, analysis_type, focus_areas)

        return {
            "status": "success",
            "analysis_type": analysis_type,
            "focus_areas": focus_areas,
            "data_source": _loaded_json_data["path"],
            "num_records_analyzed": num_records,
            "sampled": sampled,
            "loaded_at": _loaded_json_data["loaded_at"],
            "analysis": analysis_results,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Analysis error: {str(e)}",
            "suggestion": "Try with a smaller dataset or specific analysis_type",
        }


def get_recommendations_from_json(
    tower_id: Optional[str] = None,
    region_id: Optional[str] = None,
    metric_focus: str = "all",
) -> dict:
    """
    Get specific recommendations based on loaded JSON data.

    This tool provides actionable recommendations for specific towers, regions,
    or metrics based on the patterns found in the loaded JSON data.

    Args:
        tower_id: Optional specific tower ID to focus on (e.g., "TX001")
        region_id: Optional specific region ID to focus on (e.g., "R-A")
        metric_focus: Which metrics to focus recommendations on:
            - "all": All metrics
            - "energy": Energy efficiency
            - "bandwidth": Bandwidth optimization
            - "latency": Latency improvements
            - "errors": Error resolution

    Returns:
        dict: Specific recommendations with priorities and action items

    Example:
        get_recommendations_from_json(tower_id="TX001")
        get_recommendations_from_json(region_id="R-A", metric_focus="energy")
        get_recommendations_from_json(metric_focus="errors")
    """
    try:
        # Check if data is loaded
        global _loaded_json_data
        if "_loaded_json_data" not in globals() or _loaded_json_data is None:
            return {
                "status": "error",
                "message": "No JSON data loaded",
                "suggestion": "Please use add_json_data() first to load a JSON file",
            }

        data = _loaded_json_data["data"]

        # Filter data based on parameters
        filtered_data = _filter_data(data, tower_id, region_id)

        if not filtered_data:
            return {
                "status": "warning",
                "message": "No data found matching the criteria",
                "tower_id": tower_id,
                "region_id": region_id,
            }

        # Generate recommendations
        recommendations = _generate_recommendations(filtered_data, metric_focus)

        return {
            "status": "success",
            "scope": {
                "tower_id": tower_id or "all towers",
                "region_id": region_id or "all regions",
                "metric_focus": metric_focus,
            },
            "records_analyzed": len(filtered_data),
            "recommendations": recommendations,
        }

    except Exception as e:
        return {"status": "error", "message": f"Recommendation error: {str(e)}"}


def compare_json_datasets(json_path1: str, json_path2: str) -> dict:
    """
    Compare two JSON datasets to identify changes, trends, and anomalies.

    This tool is useful for comparing before/after scenarios, different time periods,
    or different network configurations.

    Args:
        json_path1: Path to first JSON file (baseline)
        json_path2: Path to second JSON file (comparison)

    Returns:
        dict: Comparison analysis with changes and trends

    Example:
        compare_json_datasets("data/trace_reduced_20.json", "data/trace_llm_20.json")
    """
    try:
        # Load both datasets
        result1 = add_json_data(json_path1)
        if result1["status"] != "success":
            return result1

        data1 = _loaded_json_data["data"]

        result2 = add_json_data(json_path2)
        if result2["status"] != "success":
            return result2

        data2 = _loaded_json_data["data"]

        # Perform comparison
        comparison = _compare_datasets(data1, data2)

        return {
            "status": "success",
            "dataset1": {
                "path": json_path1,
                "records": len(data1) if isinstance(data1, list) else 1,
            },
            "dataset2": {
                "path": json_path2,
                "records": len(data2) if isinstance(data2, list) else 1,
            },
            "comparison": comparison,
        }

    except Exception as e:
        return {"status": "error", "message": f"Comparison error: {str(e)}"}


# Helper function to perform analysis
def _perform_analysis(data: Any, analysis_type: str, focus_areas: List[str]) -> dict:
    """Perform efficient analysis on the data without sending raw data to LLM."""

    results = {"summary": {}, "insights": [], "recommendations": [], "key_findings": []}

    # Convert data to list if single record
    records = data if isinstance(data, list) else [data]

    if not records:
        return results

    # Summary statistics
    results["summary"] = {
        "total_records": len(records),
        "unique_towers": len(set(r.get("tower_id", "unknown") for r in records)),
        "unique_regions": len(set(r.get("region_id", "unknown") for r in records)),
        "time_span": {
            "start": records[0].get("timestamp", "unknown"),
            "end": records[-1].get("timestamp", "unknown"),
        },
        "avg_bandwidth_utilization": round(
            sum(r.get("bandwidth_utilization_pct", 0) for r in records) / len(records),
            2,
        ),
        "avg_latency_ms": round(
            sum(r.get("latency_ms", 0) for r in records) / len(records), 2
        ),
    }

    # Analysis based on type
    if analysis_type == "energy":
        results["insights"] = _analyze_energy(records)
        results["key_findings"] = _extract_energy_findings(records)
    elif analysis_type == "congestion":
        results["insights"] = _analyze_congestion(records)
        results["key_findings"] = _extract_congestion_findings(records)
    elif analysis_type == "health":
        results["insights"] = _analyze_health(records)
        results["key_findings"] = _extract_health_findings(records)
    elif analysis_type == "prediction":
        results["insights"] = _analyze_predictions(records)
        results["key_findings"] = _extract_prediction_findings(records)
    else:  # comprehensive
        results["insights"] = (
            _analyze_energy(records)
            + _analyze_congestion(records)
            + _analyze_health(records)
        )
        results["key_findings"] = (
            _extract_energy_findings(records)
            + _extract_congestion_findings(records)
            + _extract_health_findings(records)
        )

    # Generate recommendations
    results["recommendations"] = _generate_recommendations(records, "all")

    return results


def _sample_data_intelligently(data: List[dict], max_records: int) -> List[dict]:
    """Sample data intelligently to reduce payload while preserving insights."""
    if len(data) <= max_records:
        return data

    # Strategy: Include diverse samples
    # - Records with errors (high priority)
    # - Records with extreme values (outliers)
    # - Evenly distributed time samples

    sample = []

    # 1. Get all error records (high priority)
    error_records = [
        r for r in data if r.get("detected_error") not in ["none", None, ""]
    ]
    sample.extend(error_records[: max_records // 3])

    # 2. Get high/low utilization outliers
    sorted_by_bandwidth = sorted(
        data, key=lambda x: x.get("bandwidth_utilization_pct", 0)
    )
    sample.extend(sorted_by_bandwidth[:5])  # Low utilization
    sample.extend(sorted_by_bandwidth[-5:])  # High utilization

    # 3. Fill remaining with evenly distributed samples
    remaining = max_records - len(sample)
    if remaining > 0:
        step = len(data) // remaining
        for i in range(0, len(data), step):
            if len(sample) >= max_records:
                break
            if data[i] not in sample:
                sample.append(data[i])

    return sample[:max_records]


def _extract_energy_findings(records: List[dict]) -> List[str]:
    """Extract key energy findings."""
    findings = []

    low_usage = [r for r in records if r.get("bandwidth_utilization_pct", 100) < 30]
    if low_usage:
        towers = sorted(set(r.get("tower_id", "unknown") for r in low_usage))
        findings.append(
            f"🔋 {len(low_usage)}/{len(records)} records show energy-saving opportunity. "
            f"Towers: {', '.join(towers[:5])}{'...' if len(towers) > 5 else ''}"
        )

    return findings


def _extract_congestion_findings(records: List[dict]) -> List[str]:
    """Extract key congestion findings."""
    findings = []

    high_usage = [r for r in records if r.get("bandwidth_utilization_pct", 0) > 70]
    if high_usage:
        towers = sorted(set(r.get("tower_id", "unknown") for r in high_usage))
        findings.append(
            f"⚠️ {len(high_usage)}/{len(records)} records show congestion risk. "
            f"Towers: {', '.join(towers[:5])}{'...' if len(towers) > 5 else ''}"
        )

    return findings


def _extract_health_findings(records: List[dict]) -> List[str]:
    """Extract key health findings."""
    findings = []

    errors = [r for r in records if r.get("detected_error") not in ["none", None, ""]]
    if errors:
        error_types = {}
        for r in errors:
            err = r.get("detected_error", "unknown")
            error_types[err] = error_types.get(err, 0) + 1
        findings.append(
            f"🔴 {len(errors)}/{len(records)} records with errors. "
            f"Most common: {max(error_types.items(), key=lambda x: x[1])[0]}"
        )

    return findings


def _extract_prediction_findings(records: List[dict]) -> List[str]:
    """Extract prediction insights."""
    findings = []

    if len(records) >= 3:
        bw_values = [r.get("bandwidth_utilization_pct", 0) for r in records[:3]]
        if bw_values[-1] > bw_values[0] * 1.2:
            findings.append(
                f"📈 Bandwidth trending upward: {bw_values[0]:.1f}% → {bw_values[-1]:.1f}%"
            )
        elif bw_values[-1] < bw_values[0] * 0.8:
            findings.append(
                f"📉 Bandwidth trending downward: {bw_values[0]:.1f}% → {bw_values[-1]:.1f}%"
            )

    return findings


# Helper function to perform analysis
def _analyze_energy(records: List[dict]) -> List[str]:
    """Analyze energy optimization opportunities."""
    insights = []

    # Calculate energy metrics
    low_usage = [r for r in records if r.get("bandwidth_utilization_pct", 100) < 30]
    shrink_actions = [r for r in records if r.get("adjust_radius_action") == "shrink"]

    if low_usage:
        pct = (len(low_usage) / len(records)) * 100
        insights.append(
            f"Energy Opportunity: {len(low_usage)} records ({pct:.1f}%) show low bandwidth "
            f"utilization (<30%), indicating potential for energy savings through radius reduction."
        )

    if shrink_actions:
        pct = (len(shrink_actions) / len(records)) * 100
        insights.append(
            f"Energy Actions: {len(shrink_actions)} records ({pct:.1f}%) recommend shrinking "
            f"tower radius for energy efficiency. Average potential savings: 30-40%."
        )

    return insights


def _analyze_congestion(records: List[dict]) -> List[str]:
    """Analyze congestion and traffic patterns."""
    insights = []

    # Calculate congestion metrics
    high_usage = [r for r in records if r.get("bandwidth_utilization_pct", 0) > 70]
    expand_actions = [r for r in records if r.get("adjust_radius_action") == "expand"]
    errors = [r for r in records if r.get("detected_error") not in ["none", None, ""]]

    if high_usage:
        pct = (len(high_usage) / len(records)) * 100
        insights.append(
            f"Congestion Risk: {len(high_usage)} records ({pct:.1f}%) show high bandwidth "
            f"utilization (>70%), indicating potential congestion risk."
        )

    if expand_actions:
        towers = set(r.get("tower_id", "unknown") for r in expand_actions)
        insights.append(
            f"Coverage Expansion: {len(expand_actions)} records recommend expanding coverage. "
            f"Affected towers: {', '.join(sorted(towers))}"
        )

    if errors:
        error_types = {}
        for r in errors:
            err = r.get("detected_error", "unknown")
            error_types[err] = error_types.get(err, 0) + 1
        insights.append(
            f"Errors Detected: {len(errors)} error events found. "
            f"Most common: {max(error_types.items(), key=lambda x: x[1])[0]} ({max(error_types.values())} occurrences)"
        )

    return insights


def _analyze_health(records: List[dict]) -> List[str]:
    """Analyze network health indicators."""
    insights = []

    # Calculate health metrics
    poor_quality = [r for r in records if r.get("rsrq_db", 0) < -10]
    high_latency = [r for r in records if r.get("latency_ms", 0) > 80]
    packet_loss = [r for r in records if r.get("packet_loss_pct", 0) > 1.0]

    if poor_quality:
        pct = (len(poor_quality) / len(records)) * 100
        insights.append(
            f"Signal Quality: {len(poor_quality)} records ({pct:.1f}%) show poor RSRQ "
            f"(<-10 dB), indicating signal quality issues."
        )

    if high_latency:
        avg_latency = sum(r.get("latency_ms", 0) for r in high_latency) / len(
            high_latency
        )
        insights.append(
            f"Latency Issues: {len(high_latency)} records show high latency (>80ms). "
            f"Average: {avg_latency:.1f}ms"
        )

    if packet_loss:
        avg_loss = sum(r.get("packet_loss_pct", 0) for r in packet_loss) / len(
            packet_loss
        )
        insights.append(
            f"Packet Loss: {len(packet_loss)} records show significant packet loss (>1%). "
            f"Average: {avg_loss:.2f}%"
        )

    return insights


def _analyze_predictions(records: List[dict]) -> List[str]:
    """Analyze patterns for predictions."""
    insights = []

    # Analyze patterns over time
    if len(records) >= 5:
        insights.append(
            f"Pattern Analysis: Analyzing {len(records)} records for trend detection. "
            f"Data spans from {records[0].get('timestamp', 'unknown')} to "
            f"{records[-1].get('timestamp', 'unknown')}"
        )

        # Bandwidth trend
        bw_values = [r.get("bandwidth_utilization_pct", 0) for r in records]
        if len(bw_values) > 1:
            trend = "increasing" if bw_values[-1] > bw_values[0] else "decreasing"
            insights.append(
                f"Bandwidth Trend: {trend} ({bw_values[0]:.1f}% → {bw_values[-1]:.1f}%)"
            )

    return insights


def _generate_recommendations(records: List[dict], metric_focus: str) -> List[dict]:
    """Generate actionable recommendations (limited to top 5 to reduce payload)."""
    recommendations = []

    if not records:
        return recommendations

    # Energy recommendations
    if metric_focus in ["all", "energy"]:
        low_usage = [r for r in records if r.get("bandwidth_utilization_pct", 100) < 30]
        if low_usage:
            tower_ids = sorted(set(r.get("tower_id", "unknown") for r in low_usage))[:5]
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Energy Optimization",
                    "title": "Implement Power Saving Mode",
                    "affected_towers": tower_ids,
                    "count": len(low_usage),
                    "expected_impact": "30-40% energy savings",
                    "action": "Schedule TRX shutdowns during low-traffic periods",
                }
            )

    # Performance recommendations
    if metric_focus in ["all", "latency"]:
        high_latency = [r for r in records if r.get("latency_ms", 0) > 80]
        if high_latency:
            avg_latency = sum(r.get("latency_ms", 0) for r in high_latency) / len(
                high_latency
            )
            tower_ids = sorted(set(r.get("tower_id", "unknown") for r in high_latency))[
                :5
            ]
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "category": "Performance",
                    "title": "Reduce Network Latency",
                    "affected_towers": tower_ids,
                    "count": len(high_latency),
                    "avg_latency_ms": round(avg_latency, 1),
                    "expected_impact": "20-30% latency reduction",
                    "action": "Optimize routing and check backhaul",
                }
            )

    # Congestion recommendations
    if metric_focus in ["all", "bandwidth"]:
        high_usage = [r for r in records if r.get("bandwidth_utilization_pct", 0) > 70]
        if high_usage:
            tower_ids = sorted(set(r.get("tower_id", "unknown") for r in high_usage))[
                :5
            ]
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Congestion Management",
                    "title": "Prevent Network Congestion",
                    "affected_towers": tower_ids,
                    "count": len(high_usage),
                    "expected_impact": "Maintain QoS",
                    "action": "Enable load balancing and expand coverage",
                }
            )

    # Error handling recommendations
    if metric_focus in ["all", "errors"]:
        errors = [
            r for r in records if r.get("detected_error") not in ["none", None, ""]
        ]
        if errors:
            error_types = {}
            for r in errors:
                err = r.get("detected_error", "unknown")
                error_types[err] = error_types.get(err, 0) + 1

            top_error = max(error_types.items(), key=lambda x: x[1])
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Reliability",
                    "title": "Address Network Errors",
                    "error_count": len(errors),
                    "top_error": top_error[0],
                    "top_error_count": top_error[1],
                    "expected_impact": "Improved stability",
                    "action": f"Investigate {top_error[0]} errors and schedule maintenance",
                }
            )

    # Limit to top 5 recommendations
    return recommendations[:5]


def _filter_data(
    data: Any, tower_id: Optional[str], region_id: Optional[str]
) -> List[dict]:
    """Filter data based on tower_id and region_id."""
    records = data if isinstance(data, list) else [data]

    filtered = records

    if tower_id:
        filtered = [r for r in filtered if r.get("tower_id") == tower_id]

    if region_id:
        filtered = [r for r in filtered if r.get("region_id") == region_id]

    return filtered


def _compare_datasets(data1: Any, data2: Any) -> dict:
    """Compare two datasets and find differences."""
    records1 = data1 if isinstance(data1, list) else [data1]
    records2 = data2 if isinstance(data2, list) else [data2]

    comparison = {
        "size_change": len(records2) - len(records1),
        "towers": {
            "dataset1": set(r.get("tower_id", "unknown") for r in records1),
            "dataset2": set(r.get("tower_id", "unknown") for r in records2),
        },
        "metrics": {},
    }

    # Compare average metrics
    if records1 and records2:
        for metric in ["bandwidth_utilization_pct", "latency_ms", "cpu_util_pct"]:
            avg1 = sum(r.get(metric, 0) for r in records1) / len(records1)
            avg2 = sum(r.get(metric, 0) for r in records2) / len(records2)
            change = ((avg2 - avg1) / avg1 * 100) if avg1 != 0 else 0

            comparison["metrics"][metric] = {
                "dataset1_avg": round(avg1, 2),
                "dataset2_avg": round(avg2, 2),
                "change_percent": round(change, 2),
            }

    return comparison


# Global variable to store loaded data (in production, use proper state management)
_loaded_json_data = None
