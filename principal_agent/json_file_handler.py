"""
JSON File Upload Handler for ADK Web Interface

This module provides a custom preprocessing layer that converts JSON file uploads
to text format, fixing the Gemini API error:
"Unable to submit request because it has a mimeType parameter with value application/json"

The handler intercepts Content objects before they reach the LLM and converts
inline JSON files to formatted text.

Enhanced with direct Gemini AI integration for JSON data analysis.
"""

import json
import base64
import os
import sys
from typing import Optional, Any, Dict

# Add paths for imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
CLIENT_SERVER_DIR = os.path.join(ROOT_DIR, "client", "server")

for path in [ROOT_DIR, CLIENT_SERVER_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Try to import Gemini Service
try:
    from gemini_service import gemini_service, GEMINI_AVAILABLE
except ImportError:
    GEMINI_AVAILABLE = False
    gemini_service = None

from google.genai import types


def preprocess_content_for_json_files(content: types.Content) -> types.Content:
    """
    Convert JSON file uploads (inline_data) to text format.

    This function is called before content is sent to the LLM to avoid the
    "application/json mimeType not supported" error.

    Args:
        content: ADK Content object that may contain inline_data parts

    Returns:
        Modified Content with JSON files converted to text
    """
    if not hasattr(content, "parts") or not content.parts:
        return content

    new_parts = []
    text_parts = []
    has_json_file = False

    for part in content.parts:
        # Handle text parts
        if hasattr(part, "text") and part.text:
            text_parts.append(part.text)

        # Handle inline_data parts (file uploads)
        elif hasattr(part, "inline_data") and part.inline_data:
            inline_data = part.inline_data
            mime_type = getattr(inline_data, "mime_type", "")

            # Convert JSON files to text
            if mime_type == "application/json":
                has_json_file = True
                json_content = extract_json_content_from_inline_data(inline_data)

                if json_content:
                    # Add the JSON content as formatted text
                    text_parts.append("\n\n" + json_content + "\n\n")
                else:
                    # If extraction fails, add error message
                    text_parts.append(
                        "\n\n⚠️ Error: Could not extract JSON file content.\n\n"
                    )
            else:
                # Keep other file types (though Gemini may reject non-image types)
                new_parts.append(part)
        else:
            # Keep other part types as-is
            new_parts.append(part)

    # Combine all text into a single text part
    if text_parts:
        combined_text = "".join(text_parts)

        # If we converted a JSON file, add instructions for the agent
        if has_json_file:
            combined_text += "\n[System Note: JSON file was uploaded. Please use the process_uploaded_json tool with the JSON content above to analyze it.]\n"

        new_parts.insert(0, types.Part(text=combined_text))

    # Return new Content object with modified parts
    return types.Content(role=content.role, parts=new_parts)


def extract_json_content_from_inline_data(inline_data) -> Optional[str]:
    """
    Extract and format JSON content from inline_data.

    Args:
        inline_data: Inline data object with base64 encoded JSON data

    Returns:
        Formatted JSON string ready to be sent to LLM, or None if extraction fails
    """
    try:
        # Get base64 data
        data_b64 = getattr(inline_data, "data", "")

        if not data_b64:
            return None

        # Decode base64
        json_bytes = base64.b64decode(data_b64)
        json_str = json_bytes.decode("utf-8")

        # Parse and validate JSON
        json_obj = json.loads(json_str)

        # Format for readability (limit size to avoid token limits)
        return format_json_for_llm(json_obj)

    except Exception as e:
        return f"❌ Error extracting JSON: {str(e)}"


def format_json_for_llm(json_obj) -> str:
    """
    Format JSON object for LLM consumption with size limits.

    For large datasets, shows a sample + summary to avoid exceeding token limits.
    For small datasets, shows the full content.

    Args:
        json_obj: Parsed JSON object (dict or list)

    Returns:
        Formatted string representation
    """
    formatted = "📊 JSON Data Uploaded:\n\n"

    if isinstance(json_obj, list):
        num_records = len(json_obj)

        if num_records > 5:
            # Large dataset: show sample + summary
            sample = json_obj[:3]
            formatted += (
                f"```json\n{json.dumps(sample, indent=2, ensure_ascii=False)}\n```\n\n"
            )
            formatted += f"... ({num_records - 3} more records)\n\n"
            formatted += f"**Data Summary:**\n"
            formatted += f"- Total records: {num_records}\n"

            if sample:
                fields = list(sample[0].keys()) if isinstance(sample[0], dict) else []
                if fields:
                    formatted += f'- Fields per record: {", ".join(fields[:10])}'
                    if len(fields) > 10:
                        formatted += f"... (+{len(fields) - 10} more)"
                    formatted += "\n"
        else:
            # Small dataset: show everything
            formatted += (
                f"```json\n{json.dumps(json_obj, indent=2, ensure_ascii=False)}\n```\n"
            )
            formatted += f"\nTotal records: {num_records}\n"

    elif isinstance(json_obj, dict):
        # Single record or config object
        formatted += (
            f"```json\n{json.dumps(json_obj, indent=2, ensure_ascii=False)}\n```\n"
        )

    else:
        # Primitive value
        formatted += (
            f"```json\n{json.dumps(json_obj, indent=2, ensure_ascii=False)}\n```\n"
        )

    return formatted


def should_preprocess_content(content) -> bool:
    """
    Check if content needs preprocessing for JSON files.

    Args:
        content: Content object to check

    Returns:
        True if content contains JSON inline_data that needs conversion
    """
    if not hasattr(content, "parts") or not content.parts:
        return False

    for part in content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            mime_type = getattr(part.inline_data, "mime_type", "")
            if mime_type == "application/json":
                return True

    return False


# =============================================================================
# Gemini AI Integration for JSON Analysis
# =============================================================================


def analyze_json_data_with_llm(
    json_data: Any,
    query: str = "comprehensive analysis",
    analysis_type: str = "comprehensive",
) -> Dict[str, Any]:
    """
    Analyze JSON data using Gemini AI.

    This function connects to the Gemini service for real AI-powered analysis
    of network telemetry and other JSON data.

    Args:
        json_data: Parsed JSON data (list or dict)
        query: Specific analysis query or question
        analysis_type: Type of analysis ('comprehensive', 'energy', 'congestion', 'health')

    Returns:
        Dict containing:
        - success: bool
        - analysis: str (AI-generated analysis)
        - source: str ('gemini' or 'fallback')
        - timestamp: str
    """
    if GEMINI_AVAILABLE and gemini_service:
        try:
            # Use Gemini service for AI analysis
            result = gemini_service.analyze_json_data(json_data, query)
            return result
        except Exception as e:
            print(f"Gemini JSON analysis failed: {e}")

    # Fallback response when Gemini is not available
    record_count = len(json_data) if isinstance(json_data, list) else 1

    # Build a basic analysis without AI
    analysis = f"""## JSON Data Analysis (Fallback Mode)

**Data Overview:**
- Records: {record_count}
- Query: {query}

**Basic Statistics:**
"""

    if isinstance(json_data, list) and json_data:
        sample = json_data[0] if json_data else {}
        if isinstance(sample, dict):
            analysis += f"- Fields: {', '.join(sample.keys())}\n"

            # Try to extract some numeric stats
            for key in sample.keys():
                try:
                    values = [
                        r.get(key)
                        for r in json_data
                        if isinstance(r.get(key), (int, float))
                    ]
                    if values:
                        avg = sum(values) / len(values)
                        analysis += f"- {key}: avg={avg:.2f}, min={min(values):.2f}, max={max(values):.2f}\n"
                except:
                    pass

    analysis += "\n**Note:** Connect Gemini API for full AI-powered analysis."

    from datetime import datetime

    return {
        "success": True,
        "analysis": analysis,
        "query": query,
        "data_records": record_count,
        "source": "fallback",
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_recommendations_from_json(
    json_data: Any, focus_area: str = "general"
) -> Dict[str, Any]:
    """
    Get AI-powered recommendations based on JSON telemetry data.

    Args:
        json_data: Network telemetry data
        focus_area: Area to focus on ('energy', 'congestion', 'health', 'general')

    Returns:
        Dict with recommendations
    """
    query_map = {
        "energy": "Analyze this data for energy optimization opportunities. What towers can reduce power consumption? What TRX optimizations are possible?",
        "congestion": "Analyze this data for congestion patterns. What are the peak traffic times? Which towers need load balancing?",
        "health": "Analyze this data for health issues. What anomalies exist? What preventive maintenance is needed?",
        "general": "Provide comprehensive recommendations for network optimization based on this telemetry data.",
    }

    query = query_map.get(focus_area, query_map["general"])
    return analyze_json_data_with_llm(json_data, query, focus_area)


def compare_json_datasets(
    dataset1: Any,
    dataset2: Any,
    comparison_query: str = "Compare these two datasets and highlight differences",
) -> Dict[str, Any]:
    """
    Compare two JSON datasets using AI analysis.

    Args:
        dataset1: First dataset
        dataset2: Second dataset
        comparison_query: Specific comparison question

    Returns:
        Dict with comparison analysis
    """
    combined_data = {
        "dataset1": dataset1[:5] if isinstance(dataset1, list) else dataset1,
        "dataset2": dataset2[:5] if isinstance(dataset2, list) else dataset2,
        "dataset1_count": len(dataset1) if isinstance(dataset1, list) else 1,
        "dataset2_count": len(dataset2) if isinstance(dataset2, list) else 1,
    }

    return analyze_json_data_with_llm(combined_data, comparison_query, "comprehensive")
