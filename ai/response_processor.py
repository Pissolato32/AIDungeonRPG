"""
AI
Response processor module.

This module handles processing and validation of AI-generated responses,
including JSON extraction and error handling.
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Dict, Optional, TypedDict, cast

logger = logging.getLogger(__name__)


class AIResponse(TypedDict, total=False):
    """Type definition for AI response data."""

    success: bool
    message: str
    error: Optional[str]
    details: Optional[Dict[str, str]]


@dataclass
class JsonExtractionResult:
    """Result of JSON extraction attempt."""

    data: Optional[Dict[str, str]]
    error: Optional[str]
    source: str = "none"


def process_ai_response(response_text: str) -> AIResponse:
    """Process AI response text, attempting to extract JSON if present.

    Args:
        response_text: Raw response text from the AI

    Returns:
        A structured response object
    """
    try:
        # Try to extract JSON from the response
        result = extract_json_from_text(response_text)

        if result.data:
            response = cast(AIResponse, result.data)
            if "success" not in response:
                response["success"] = True
            return response

        # If no JSON found, return as message
        return AIResponse(success=True, message=response_text)

    except Exception as e:
        logger.error(
            "Error processing AI response",
            extra={"error": str(e), "response_length": len(response_text)},
        )
        return AIResponse(
            success=False, message="Failed to process response", error=str(e)
        )


def extract_json_from_text(text: str) -> JsonExtractionResult:
    """Extract JSON from text that might contain other content.

    Args:
        text: Text that might contain JSON

    Returns:
        JsonExtractionResult containing extracted data or error info
    """
    # Strategy 1: Parse entire text as JSON
    try:
        data = json.loads(text.strip())
        return JsonExtractionResult(data=data, error=None, source="full_text")
    except json.JSONDecodeError:
        pass

    # Strategy 2: Look for JSON in code blocks
    if "```" in text:
        result = _extract_from_code_blocks(text)
        if result.data:
            return result

    # Strategy 3: Look for JSON-like structures
    if "{" in text and "}" in text:
        result = _extract_with_brace_matching(text)
        if result.data:
            return result

    # No valid JSON found
    return JsonExtractionResult(
        data=None, error="No valid JSON found in response", source="none"
    )


def _extract_from_code_blocks(text: str) -> JsonExtractionResult:
    """Extract JSON from markdown code blocks.

    Args:
        text: Text containing markdown code blocks

    Returns:
        JsonExtractionResult with extracted data or error
    """
    try:
        # Try ```json blocks first
        if "```json" in text:
            parts = text.split("```json")
            if len(parts) > 1:
                json_text = parts[1].split("```")[0].strip()
                data = json.loads(json_text)
                return JsonExtractionResult(
                    data=data, error=None, source="json_block")

        # Try generic ``` blocks
        parts = text.split("```")
        for part in parts[1::2]:
            try:
                data = json.loads(part.strip())
                return JsonExtractionResult(
                    data=data, error=None, source="code_block")
            except json.JSONDecodeError:
                continue

    except Exception as e:
        logger.warning(
            "Error extracting from code blocks",
            extra={
                "error": str(e)})

    return JsonExtractionResult(
        data=None, error="No valid JSON in code blocks", source="none"
    )


def _extract_with_brace_matching(text: str) -> JsonExtractionResult:
    """Extract JSON using brace matching.

    Looks for matching pairs of curly braces and attempts to parse
    the content between them as JSON.

    Args:
        text: Text to search for JSON structures

    Returns:
        JsonExtractionResult with extracted data or error
    """
    try:
        start_idx = text.find("{")
        if start_idx == -1:
            return JsonExtractionResult(
                data=None, error="No opening brace found", source="none"
            )

        # Find matching closing brace
        open_count = 0
        for i in range(start_idx, len(text)):
            if text[i] == "{":
                open_count += 1
            elif text[i] == "}":
                open_count -= 1
                if open_count == 0:
                    json_text = text[start_idx: i + 1]
                    try:
                        data = json.loads(json_text)
                        return JsonExtractionResult(
                            data=data, error=None, source="brace_matching"
                        )
                    except json.JSONDecodeError:
                        continue

    except Exception as e:
        logger.warning("Error in brace matching", extra={"error": str(e)})

    return JsonExtractionResult(
        data=None,
        error="No valid JSON found with brace matching",
        source="none")


def validate_response_content(response: AIResponse) -> AIResponse:
    """Validate if the response content is meaningful.

    Args:
        response: The response dictionary to validate

    Returns:
        Validated response or error response
    """
    patterns = [
        r"Você realizou a ação \w+: \w+",
        r"You performed the \w+ action: \w+",
        r"Action \w+ performed: \w+",
    ]

    if "message" in response and isinstance(response["message"], str):
        message = response["message"]

        if any(re.search(pattern, message) for pattern in patterns):
            return AIResponse(
                success=False,
                message=(
                    "Não foi possível processar sua ação. "
                    "Por favor, tente novamente com mais detalhes."
                ),
            )

    return response
