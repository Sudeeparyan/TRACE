"""
JSON File Upload Handler for ADK Web Interface

This module provides a custom preprocessing layer that converts JSON file uploads
to text format, fixing the Gemini API error:
"Unable to submit request because it has a mimeType parameter with value application/json"

The handler intercepts Content objects before they reach the LLM and converts
inline JSON files to formatted text.
"""

import json
import base64
from typing import Optional
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
