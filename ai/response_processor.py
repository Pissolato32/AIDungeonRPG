"""
Response processor module.

This module provides functions for processing AI responses.
"""

import json
import logging
from typing import Dict, Any, Union, Optional

logger = logging.getLogger(__name__)


def process_ai_response(response_text: str) -> Union[Dict[str, Any], str]:
    """
    Process AI response text, attempting to extract JSON if present.

    Args:
        response_text: Raw response text from AI

    Returns:
        Extracted JSON as dictionary or original text if not JSON
    """
    try:
        # Try to extract JSON from the response
        json_data = extract_json_from_text(response_text)

        if json_data:
            return json_data

        # If no JSON found, return as message
        return {"success": True, "message": response_text}
    except Exception as e:
        logger.error(f"Error processing AI response: {e}")
        return {"success": False, "message": "Failed to process response"}


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from text that might contain markdown code blocks or other text.

    Args:
        text: Text that might contain JSON

    Returns:
        Extracted JSON as dictionary or None if no valid JSON found
    """
    # Try different JSON extraction strategies
    json_data = None

    # Strategy 1: Try to parse the entire text as JSON
    try:
        json_data = json.loads(text.strip())
        logger.debug("Successfully parsed entire text as JSON")
        return json_data
    except json.JSONDecodeError:
        pass

    # Strategy 2: Look for JSON in code blocks
    try:
        # Extract content from markdown code blocks
        if "```json" in text or "```" in text:
            try:
                # Handle ```json blocks
                if "```json" in text:
                    parts = text.split("```json")
                    if len(parts) > 1:
                        json_text = parts[1].split("```")[0].strip()
                        json_data = json.loads(json_text)
                        logger.debug("Successfully extracted JSON from ```json block")
                        return json_data

                # Handle generic ``` blocks that might contain JSON
                parts = text.split("```")
                if len(parts) > 1:
                    for part in parts[1::2]:  # Check only content inside code blocks
                        try:
                            json_data = json.loads(part.strip())
                            logger.debug("Successfully extracted JSON from ``` block")
                            return json_data
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.warning("Error extracting JSON from code blocks", extra={"error": str(e)})
    except Exception as e:
        logger.warning("Error in JSON extraction strategy 2", extra={"error": str(e)})

    # Strategy 3: Look for JSON-like structures with { }
    try:
        # Find content between curly braces
        if "{" in text and "}" in text:
            start_idx = text.find("{")
            # Find matching closing brace
            open_count = 0
            for i in range(start_idx, len(text)):
                if text[i] == "{":
                    open_count += 1
                elif text[i] == "}":
                    open_count -= 1
                    if open_count == 0:
                        json_text = text[start_idx:i+1]
                        try:
                            json_data = json.loads(json_text)
                            logger.debug("Successfully extracted JSON using brace matching")
                            return json_data
                        except json.JSONDecodeError:
                            break
    except Exception as e:
        logger.warning("Error in JSON extraction strategy 3", extra={"error": str(e)})

    # No valid JSON found
    return None

def create_error_response(error_message: str) -> Dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        error_message: Error message to include

    Returns:
        Error response dictionary
    """
    return {
        "success": False,
        "message": error_message
    }