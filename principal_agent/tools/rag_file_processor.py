"""
RAG (Retrieval Augmented Generation) File Processor for TRACE System

This tool implements a simple RAG system that:
1. Accepts file content directly (not just file paths)
2. Processes JSON data for analysis
3. Uses text-based queries compatible with ADK web interface
4. Returns intelligent, context-aware recommendations

Compatible with ADK web file uploads and text-based interactions.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime


def process_uploaded_json(json_content: str) -> dict:
    """
    Process JSON content uploaded via ADK web interface.

    This tool accepts raw JSON content as a string and processes it for analysis.
    Use this when uploading files through the ADK web interface.

    Args:
        json_content: Raw JSON content as a string (paste or upload)

    Returns:
        dict: Processed data summary with insights

    Example:
        process_uploaded_json('[{"tower_id": "TX001", "bandwidth_utilization_pct": 25, ...}]')
    """
    try:
        # Parse JSON content
        data = json.loads(json_content)

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

        # Store data globally for RAG queries
        global _rag_data
        _rag_data = {
            "content": data,
            "loaded_at": datetime.now().isoformat(),
            "num_records": num_records,
        }

        # Perform initial analysis
        analysis = _analyze_rag_data(data)

        return {
            "status": "success",
            "message": f"✅ Successfully processed {num_records} records",
            "num_records": num_records,
            "data_type": data_type,
            "fields": list(sample.keys()) if isinstance(sample, dict) else [],
            "initial_insights": analysis["summary"],
            "key_findings": analysis["key_findings"][:3],  # Top 3 findings
            "next_steps": [
                "Ask: 'Give me energy optimization recommendations'",
                "Ask: 'What towers need attention?'",
                "Ask: 'Analyze congestion patterns'",
            ],
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}",
            "suggestion": "Please ensure the content is valid JSON. Check for missing commas, brackets, or quotes.",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Processing error: {str(e)}",
            "suggestion": "Try with a smaller dataset or check the JSON structure",
        }


def query_rag_data(question: str) -> dict:
    """
    Query the uploaded data with natural language questions.

    This tool implements a simple RAG system that answers questions about
    the previously uploaded JSON data using intelligent analysis.

    Args:
        question: Natural language question about the data
            Examples:
            - "What towers have high energy consumption?"
            - "Give me congestion recommendations"
            - "Which towers have errors?"
            - "Show me bandwidth utilization patterns"

    Returns:
        dict: Answer with relevant data insights and recommendations

    Example:
        query_rag_data("What towers need energy optimization?")
    """
    try:
        # Check if data is loaded
        global _rag_data
        if "_rag_data" not in globals() or _rag_data is None:
            return {
                "status": "error",
                "message": "No data loaded",
                "suggestion": "Please upload JSON data first using process_uploaded_json()",
            }

        data = _rag_data["content"]
        records = data if isinstance(data, list) else [data]

        # Parse question and determine intent
        question_lower = question.lower()

        # Energy-related queries
        if any(
            word in question_lower
            for word in ["energy", "power", "optimization", "saving", "efficiency"]
        ):
            return _answer_energy_query(records, question)

        # Congestion-related queries
        elif any(
            word in question_lower
            for word in ["congestion", "bandwidth", "traffic", "load", "utilization"]
        ):
            return _answer_congestion_query(records, question)

        # Error-related queries
        elif any(
            word in question_lower
            for word in ["error", "problem", "issue", "fault", "failure"]
        ):
            return _answer_error_query(records, question)

        # Tower-specific queries
        elif any(word in question_lower for word in ["tower", "tx", "site"]):
            return _answer_tower_query(records, question)

        # Recommendation queries
        elif any(
            word in question_lower
            for word in ["recommend", "suggest", "action", "what should", "how to"]
        ):
            return _answer_recommendation_query(records, question)

        # General/summary queries
        else:
            return _answer_general_query(records, question)

    except Exception as e:
        return {
            "status": "error",
            "message": f"Query error: {str(e)}",
            "suggestion": "Try rephrasing your question or be more specific",
        }


def get_rag_summary() -> dict:
    """
    Get a summary of the currently loaded data.

    Returns a comprehensive overview of the uploaded data including
    key metrics, patterns, and high-priority items.

    Returns:
        dict: Data summary with key insights

    Example:
        get_rag_summary()
    """
    try:
        global _rag_data
        if "_rag_data" not in globals() or _rag_data is None:
            return {
                "status": "error",
                "message": "No data loaded",
                "suggestion": "Please upload JSON data first",
            }

        data = _rag_data["content"]
        records = data if isinstance(data, list) else [data]

        analysis = _analyze_rag_data(records)

        return {
            "status": "success",
            "loaded_at": _rag_data["loaded_at"],
            "summary": analysis["summary"],
            "key_findings": analysis["key_findings"],
            "top_recommendations": analysis["recommendations"][:5],
            "high_priority_towers": analysis["priority_towers"][:5],
        }

    except Exception as e:
        return {"status": "error", "message": f"Summary error: {str(e)}"}


# ==================== HELPER FUNCTIONS ====================


def _analyze_rag_data(records: List[dict]) -> dict:
    """Perform comprehensive analysis on the data."""

    if not records:
        return {
            "summary": {},
            "key_findings": [],
            "recommendations": [],
            "priority_towers": [],
        }

    # Calculate summary metrics
    summary = {
        "total_records": len(records),
        "unique_towers": len(set(r.get("tower_id", "unknown") for r in records)),
        "unique_regions": len(set(r.get("region_id", "unknown") for r in records)),
        "avg_bandwidth_utilization": round(
            sum(r.get("bandwidth_utilization_pct", 0) for r in records) / len(records),
            2,
        ),
        "avg_latency_ms": round(
            sum(r.get("latency_ms", 0) for r in records) / len(records), 2
        ),
    }

    # Find key patterns
    key_findings = []

    # Energy findings
    low_usage = [r for r in records if r.get("bandwidth_utilization_pct", 100) < 30]
    if low_usage:
        pct = (len(low_usage) / len(records)) * 100
        towers = sorted(set(r.get("tower_id", "unknown") for r in low_usage))[:5]
        key_findings.append(
            {
                "category": "Energy",
                "priority": "HIGH",
                "finding": f"{len(low_usage)} records ({pct:.1f}%) show energy-saving opportunity",
                "affected_towers": towers,
                "potential_savings": "30-40%",
            }
        )

    # Congestion findings
    high_usage = [r for r in records if r.get("bandwidth_utilization_pct", 0) > 70]
    if high_usage:
        pct = (len(high_usage) / len(records)) * 100
        towers = sorted(set(r.get("tower_id", "unknown") for r in high_usage))[:5]
        key_findings.append(
            {
                "category": "Congestion",
                "priority": "HIGH",
                "finding": f"{len(high_usage)} records ({pct:.1f}%) show congestion risk",
                "affected_towers": towers,
                "impact": "QoS degradation risk",
            }
        )

    # Error findings
    errors = [r for r in records if r.get("detected_error") not in ["none", None, ""]]
    if errors:
        error_types = {}
        for r in errors:
            err = r.get("detected_error", "unknown")
            error_types[err] = error_types.get(err, 0) + 1
        top_error = max(error_types.items(), key=lambda x: x[1])
        key_findings.append(
            {
                "category": "Reliability",
                "priority": "HIGH",
                "finding": f"{len(errors)} error events detected",
                "top_error_type": top_error[0],
                "top_error_count": top_error[1],
            }
        )

    # Generate recommendations
    recommendations = _generate_rag_recommendations(records)

    # Identify priority towers
    priority_towers = _identify_priority_towers(records)

    return {
        "summary": summary,
        "key_findings": key_findings,
        "recommendations": recommendations,
        "priority_towers": priority_towers,
    }


def _answer_energy_query(records: List[dict], question: str) -> dict:
    """Answer energy-related questions."""
    low_usage = [r for r in records if r.get("bandwidth_utilization_pct", 100) < 30]
    shrink_actions = [r for r in records if r.get("adjust_radius_action") == "shrink"]

    towers_with_opportunity = sorted(
        set(r.get("tower_id", "unknown") for r in low_usage)
    )

    return {
        "status": "success",
        "question": question,
        "answer": {
            "summary": f"Found {len(low_usage)} records with energy optimization opportunities",
            "affected_towers": towers_with_opportunity[:10],
            "potential_savings": "30-40% energy reduction",
            "details": {
                "low_utilization_count": len(low_usage),
                "shrink_recommended": len(shrink_actions),
                "percentage": (
                    round((len(low_usage) / len(records)) * 100, 1) if records else 0
                ),
            },
            "recommendations": [
                {
                    "action": "Implement energy-saving mode",
                    "towers": towers_with_opportunity[:5],
                    "expected_impact": "30-40% energy savings",
                    "priority": "HIGH",
                },
                {
                    "action": "Schedule TRX shutdowns during low-traffic periods",
                    "impact": "Reduce idle power consumption",
                    "priority": "MEDIUM",
                },
            ],
        },
    }


def _answer_congestion_query(records: List[dict], question: str) -> dict:
    """Answer congestion-related questions."""
    high_usage = [r for r in records if r.get("bandwidth_utilization_pct", 0) > 70]
    expand_actions = [r for r in records if r.get("adjust_radius_action") == "expand"]

    towers_at_risk = sorted(set(r.get("tower_id", "unknown") for r in high_usage))

    return {
        "status": "success",
        "question": question,
        "answer": {
            "summary": f"Found {len(high_usage)} records with congestion risk",
            "towers_at_risk": towers_at_risk[:10],
            "details": {
                "high_utilization_count": len(high_usage),
                "expansion_recommended": len(expand_actions),
                "percentage": (
                    round((len(high_usage) / len(records)) * 100, 1) if records else 0
                ),
                "avg_utilization": (
                    round(
                        sum(r.get("bandwidth_utilization_pct", 0) for r in high_usage)
                        / len(high_usage),
                        2,
                    )
                    if high_usage
                    else 0
                ),
            },
            "recommendations": [
                {
                    "action": "Enable load balancing",
                    "towers": towers_at_risk[:5],
                    "expected_impact": "Prevent QoS degradation",
                    "priority": "HIGH",
                },
                {
                    "action": "Expand coverage for high-demand towers",
                    "towers": [r.get("tower_id") for r in expand_actions[:5]],
                    "priority": "MEDIUM",
                },
            ],
        },
    }


def _answer_error_query(records: List[dict], question: str) -> dict:
    """Answer error-related questions."""
    errors = [r for r in records if r.get("detected_error") not in ["none", None, ""]]

    error_breakdown = {}
    for r in errors:
        err = r.get("detected_error", "unknown")
        if err not in error_breakdown:
            error_breakdown[err] = {
                "count": 0,
                "towers": set(),
            }
        error_breakdown[err]["count"] += 1
        error_breakdown[err]["towers"].add(r.get("tower_id", "unknown"))

    error_summary = [
        {
            "error_type": err_type,
            "count": data["count"],
            "affected_towers": sorted(list(data["towers"]))[:5],
        }
        for err_type, data in sorted(
            error_breakdown.items(), key=lambda x: x[1]["count"], reverse=True
        )
    ]

    return {
        "status": "success",
        "question": question,
        "answer": {
            "summary": f"Found {len(errors)} error events across {len(error_breakdown)} error types",
            "error_breakdown": error_summary,
            "recommendations": (
                [
                    {
                        "action": f"Investigate {error_summary[0]['error_type']} errors",
                        "affected_towers": error_summary[0]["affected_towers"],
                        "priority": "HIGH",
                    }
                ]
                if error_summary
                else []
            ),
        },
    }


def _answer_tower_query(records: List[dict], question: str) -> dict:
    """Answer tower-specific questions."""
    # Extract tower ID from question if present
    tower_id = None
    words = question.split()
    for word in words:
        if word.upper().startswith("TX"):
            tower_id = word.upper()
            break

    if tower_id:
        tower_records = [r for r in records if r.get("tower_id") == tower_id]
        if tower_records:
            latest = tower_records[-1]
            return {
                "status": "success",
                "question": question,
                "answer": {
                    "tower_id": tower_id,
                    "records_found": len(tower_records),
                    "latest_metrics": {
                        "bandwidth_utilization": f"{latest.get('bandwidth_utilization_pct', 0):.1f}%",
                        "latency": f"{latest.get('latency_ms', 0)} ms",
                        "connected_users": latest.get("connected_users", 0),
                        "detected_error": latest.get("detected_error", "none"),
                    },
                    "status": (
                        "Normal"
                        if latest.get("detected_error") in ["none", None, ""]
                        else "Needs Attention"
                    ),
                },
            }
        else:
            return {
                "status": "warning",
                "message": f"No data found for tower {tower_id}",
                "suggestion": "Check tower ID or try another tower",
            }
    else:
        # General tower summary
        all_towers = set(r.get("tower_id", "unknown") for r in records)
        return {
            "status": "success",
            "question": question,
            "answer": {
                "total_towers": len(all_towers),
                "tower_list": sorted(list(all_towers)),
                "suggestion": "Ask about a specific tower like 'What about tower TX001?'",
            },
        }


def _answer_recommendation_query(records: List[dict], question: str) -> dict:
    """Answer recommendation queries."""
    recommendations = _generate_rag_recommendations(records)

    return {
        "status": "success",
        "question": question,
        "answer": {
            "summary": f"Generated {len(recommendations)} recommendations based on data analysis",
            "recommendations": recommendations[:5],  # Top 5
            "priority_breakdown": {
                "high": len([r for r in recommendations if r["priority"] == "HIGH"]),
                "medium": len(
                    [r for r in recommendations if r["priority"] == "MEDIUM"]
                ),
                "low": len([r for r in recommendations if r["priority"] == "LOW"]),
            },
        },
    }


def _answer_general_query(records: List[dict], question: str) -> dict:
    """Answer general queries with comprehensive overview."""
    analysis = _analyze_rag_data(records)

    return {
        "status": "success",
        "question": question,
        "answer": {
            "summary": analysis["summary"],
            "key_findings": analysis["key_findings"][:3],
            "top_recommendations": analysis["recommendations"][:3],
            "high_priority_towers": analysis["priority_towers"][:5],
            "suggestion": "Ask specific questions about energy, congestion, errors, or towers",
        },
    }


def _generate_rag_recommendations(records: List[dict]) -> List[dict]:
    """Generate actionable recommendations from data."""
    recommendations = []

    if not records:
        return recommendations

    # Energy recommendations
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
    high_latency = [r for r in records if r.get("latency_ms", 0) > 80]
    if high_latency:
        tower_ids = sorted(set(r.get("tower_id", "unknown") for r in high_latency))[:5]
        recommendations.append(
            {
                "priority": "MEDIUM",
                "category": "Performance",
                "title": "Reduce Network Latency",
                "affected_towers": tower_ids,
                "count": len(high_latency),
                "expected_impact": "20-30% latency reduction",
                "action": "Optimize routing and check backhaul",
            }
        )

    # Congestion recommendations
    high_usage = [r for r in records if r.get("bandwidth_utilization_pct", 0) > 70]
    if high_usage:
        tower_ids = sorted(set(r.get("tower_id", "unknown") for r in high_usage))[:5]
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

    # Error recommendations
    errors = [r for r in records if r.get("detected_error") not in ["none", None, ""]]
    if errors:
        error_types = {}
        for r in errors:
            err = r.get("detected_error", "unknown")
            error_types[err] = error_types.get(err, 0) + 1

        if error_types:
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

    return recommendations


def _identify_priority_towers(records: List[dict]) -> List[dict]:
    """Identify towers that need immediate attention."""
    priority_towers = []

    tower_metrics = {}
    for r in records:
        tower_id = r.get("tower_id", "unknown")
        if tower_id not in tower_metrics:
            tower_metrics[tower_id] = {
                "tower_id": tower_id,
                "issues": [],
                "priority_score": 0,
            }

        metrics = tower_metrics[tower_id]

        # Check for issues
        if r.get("detected_error") not in ["none", None, ""]:
            metrics["issues"].append(f"Error: {r.get('detected_error')}")
            metrics["priority_score"] += 10

        if r.get("bandwidth_utilization_pct", 0) > 80:
            metrics["issues"].append("High bandwidth utilization")
            metrics["priority_score"] += 8

        if r.get("latency_ms", 0) > 100:
            metrics["issues"].append("High latency")
            metrics["priority_score"] += 5

        if r.get("packet_loss_pct", 0) > 1.0:
            metrics["issues"].append("Packet loss")
            metrics["priority_score"] += 7

    # Sort by priority score
    priority_towers = sorted(
        [m for m in tower_metrics.values() if m["priority_score"] > 0],
        key=lambda x: x["priority_score"],
        reverse=True,
    )

    return priority_towers


# Global variable to store RAG data
_rag_data = None
