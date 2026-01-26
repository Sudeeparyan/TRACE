"""
Content Preprocessor for TRACE System

This module preprocesses user input to handle file uploads correctly.
It converts JSON file uploads (inline_data with application/json) to text format
before sending to the LLM, avoiding the Gemini API mimeType error.
"""

import json
import base64
from typing import Any, Dict, List, Optional


def preprocess_user_input(content: Any) -> Any:
    """
    Preprocess user input to convert JSON file uploads to text.

    When users upload JSON files through ADK web, they come as:
    {
        "parts": [
            {"text": "Analyze this data..."},
            {"inline_data": {"mime_type": "application/json", "data": "base64..."}}
        ]
    }

    This function converts them to:
    {
        "parts": [
            {"text": "Analyze this data...\n\nJSON Data:\n{actual json content}"}
        ]
    }

    Args:
        content: User input content (can be string, dict, or list)

    Returns:
        Preprocessed content with JSON files converted to text
    """

    # If content is a string, return as-is
    if isinstance(content, str):
        return content

    # If content is a dict with 'parts', process it
    if isinstance(content, dict) and "parts" in content:
        return _process_parts(content)

    # If content is a list, process each item
    if isinstance(content, list):
        return [preprocess_user_input(item) for item in content]

    return content


def _process_parts(content: Dict) -> Dict:
    """Process content with 'parts' field."""

    if "parts" not in content or not isinstance(content["parts"], list):
        return content

    new_parts = []
    text_accumulator = []

    for part in content["parts"]:
        if isinstance(part, dict):
            # Handle text parts
            if "text" in part:
                text_accumulator.append(part["text"])

            # Handle inline_data parts (file uploads)
            elif "inline_data" in part:
                inline_data = part["inline_data"]
                mime_type = inline_data.get("mime_type", "")

                # Convert JSON files to text
                if mime_type == "application/json":
                    json_text = _convert_json_inline_to_text(inline_data)
                    if json_text:
                        text_accumulator.append("\n\n" + json_text)
                    else:
                        # Keep original if conversion fails
                        new_parts.append(part)
                else:
                    # Keep other file types as-is (images, etc.)
                    new_parts.append(part)
            else:
                # Keep other part types
                new_parts.append(part)
        else:
            new_parts.append(part)

    # Combine all text into a single text part
    if text_accumulator:
        combined_text = "\n".join(text_accumulator)
        new_parts.insert(0, {"text": combined_text})

    # Create new content dict
    new_content = content.copy()
    new_content["parts"] = new_parts

    return new_content


def _convert_json_inline_to_text(inline_data: Dict) -> Optional[str]:
    """
    Convert inline JSON data to text format.

    Args:
        inline_data: Dict with 'mime_type' and 'data' (base64 encoded)

    Returns:
        JSON content as formatted text, or None if conversion fails
    """
    try:
        # Get base64 data
        data_b64 = inline_data.get("data", "")

        if not data_b64:
            return None

        # Decode base64
        json_bytes = base64.b64decode(data_b64)
        json_str = json_bytes.decode("utf-8")

        # Parse JSON to validate
        json_obj = json.loads(json_str)

        # Format nicely for readability (but not too verbose)
        if isinstance(json_obj, list) and len(json_obj) > 5:
            # Show first few items + summary
            sample = json_obj[:3]
            formatted = f"📊 JSON Data (showing 3 of {len(json_obj)} records):\n\n"
            formatted += json.dumps(sample, indent=2, ensure_ascii=False)
            formatted += f"\n\n... ({len(json_obj) - 3} more records)\n"

            # Add summary stats
            formatted += f"\nData Summary:\n"
            formatted += f"- Total records: {len(json_obj)}\n"
            if json_obj:
                formatted += f"- Fields: {list(json_obj[0].keys())}\n"
        else:
            # Show full data for small datasets
            formatted = (
                f"📊 JSON Data:\n\n{json.dumps(json_obj, indent=2, ensure_ascii=False)}"
            )

        return formatted

    except Exception as e:
        # If conversion fails, return error message
        return f"⚠️ Error processing JSON file: {str(e)}"


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON content from text if it contains JSON.

    This is useful when users paste JSON directly in chat.

    Args:
        text: User input text that might contain JSON

    Returns:
        Extracted JSON string, or None if no valid JSON found
    """
    try:
        # Look for JSON array or object patterns
        import re

        # Try to find JSON array
        array_match = re.search(r"\[\s*\{.*?\}\s*\]", text, re.DOTALL)
        if array_match:
            potential_json = array_match.group(0)
            try:
                json.loads(potential_json)
                return potential_json
            except:
                pass

        # Try to find JSON object
        object_match = re.search(r'\{\s*".*?"\s*:.*?\}', text, re.DOTALL)
        if object_match:
            potential_json = object_match.group(0)
            try:
                json.loads(potential_json)
                return potential_json
            except:
                pass

        return None

    except Exception:
        return None
