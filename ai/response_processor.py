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
from typing import Dict, Optional, TypedDict, cast, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .schemas import AIResponsePydantic  # Usar o schema Pydantic para type hinting

logger = logging.getLogger(__name__)


# Movido para game_ai_client.py para evitar duplicidade e import circular
# class AIResponse(TypedDict, total=False):
#     """Type definition for AI response data."""
#
#     success: bool
#     message: str
#     error: Optional[str]
#     details: Optional[Dict[str, str]]
#
# Se você precisar do tipo AIResponse aqui, importe-o de game_ai_client
# from .game_ai_client import AIResponse


# No entanto, para validate_ai_response, um Dict[str, Any] genérico é suficiente
@dataclass
class JsonExtractionResult:
    """Result of JSON extraction attempt."""

    data: Optional[Dict[str, Any]]  # Changed from Dict[str, str] to Dict[str, Any]
    error: Optional[str]
    source: str = "none"


def process_ai_response(
    response_text: str,
) -> Dict[str, Any]:  # Retorna um Dict agora, Pydantic valida depois
    """Process AI response text, attempting to extract JSON if present.
    This function now primarily focuses on extracting the JSON data.
    The GameAIClient will handle parsing this data into a Pydantic model and providing defaults.

    Args:
        response_text: Raw response text from the AI

    Returns:
        A dictionary representing the parsed JSON if successful.
        If JSON extraction fails, it returns a dictionary indicating failure,
        which the GameAIClient will then use to construct a fallback AIResponsePydantic.
    """
    try:
        result = extract_json_from_text(response_text)
        if result.data:
            return result.data  # Retorna o dict bruto
        else:
            # Se não conseguiu extrair JSON, retorna um dict indicando falha na extração
            # para que o GameAIClient possa usar o _handle_ai_failure.
            # Ou, podemos retornar uma estrutura básica que o Pydantic tentará validar (e provavelmente falhará de forma controlada).
            # Melhor retornar um dict que o GameAIClient possa identificar como falha de extração.
            # No entanto, o GameAIClient já verifica json_extraction_result.data.
            # Se chegarmos aqui, é porque extract_json_from_text retornou data=None.
            # O GameAIClient já lida com isso. Esta função não deveria ser chamada se data for None.
            # Mas, para segurança, se for chamada com texto que não é JSON:
            logger.warning(
                f"process_ai_response: No JSON extracted, returning basic error structure. Text: {response_text[:100]}"
            )
            return {
                "success": False,
                "message": "Falha ao extrair JSON da resposta da IA.",
                "error": "JSON_EXTRACTION_FAILED",
                "current_detailed_location": "Desconhecido",  # Default para Pydantic
                "scene_description_update": "Inalterada",  # Default para Pydantic
                "details": {},
            }
    except Exception as e:
        logger.error(
            "Error processing AI response",
            extra={"error": str(e), "response_length": len(response_text)},
        )
        return {  # Estrutura de erro para Pydantic
            "success": False,
            "message": f"Erro ao processar resposta da IA: {e}",
            "error": str(e),
            "current_detailed_location": "Erro",
            "scene_description_update": "Erro",
            "details": {},
        }


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
                return JsonExtractionResult(data=data, error=None, source="json_block")

        # Try generic ``` blocks
        parts = text.split("```")
        for part in parts[1::2]:
            try:
                data = json.loads(part.strip())
                return JsonExtractionResult(data=data, error=None, source="code_block")
            except json.JSONDecodeError:
                continue

    except Exception as e:
        logger.warning("Error extracting from code blocks", extra={"error": str(e)})

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
                    json_text = text[start_idx : i + 1]
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
        data=None, error="No valid JSON found with brace matching", source="none"
    )


def validate_response_content(
    response: "AIResponsePydantic",
) -> "AIResponsePydantic":  # Agora espera Pydantic
    """Validate if the response content is meaningful.
    NOTA: Com Pydantic, grande parte desta validação pode ser feita no próprio modelo.
    Esta função pode ser simplificada ou focada em validações semânticas que Pydantic não cobre.

    Args:
        response: The AIResponsePydantic object
    Returns:
        The same response if valid, or a modified one if an issue is auto-corrected or flagged.
    """
    patterns = [
        r"Você realizou a ação \w+: \w+",
        r"You performed the \w+ action: \w+",
        r"Action \w+ performed: \w+",
    ]

    # Assumindo que 'response' é um AIResponsePydantic ou um dict que será validado por ele.
    message_content = response.message

    if isinstance(message_content, str):
        if any(re.search(pattern, message_content) for pattern in patterns):
            logger.warning(
                f"Conteúdo de mensagem inválido detectado: {message_content[:100]}"
            )
            new_message = "Não foi possível processar sua ação. Por favor, tente novamente com mais detalhes."
            error_msg = "Conteúdo de mensagem inválido detectado pelo validador."
            # Retorna uma nova instância de AIResponsePydantic com os campos atualizados
            return response.model_copy(
                update={"success": False, "message": new_message, "error": error_msg}
            )

    return response
