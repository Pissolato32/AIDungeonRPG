"""Fallback response handler module.

This module provides functions for generating graceful fallback responses when
the AI service is temporarily unavailable or experiencing issues.
"""

import logging
from typing import Dict, List, TypedDict, Literal, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Type definitions
PromptType = Literal[
    "move",
    "combat",
    "talk",
    "search",
    "use_item",
    "default"
]


class DialogueOption(TypedDict):
    """Type definition for dialogue options."""

    texto: str
    tema: str


class FallbackResponse(TypedDict, total=False):
    """Type definition for fallback responses."""

    success: bool
    message: str
    new_location: Optional[str]
    description: Optional[str]
    npcs: List[str]
    events: List[str]
    npc_name: Optional[str]
    dialogue: Optional[str]
    options: Optional[List[DialogueOption]]
    findings: Optional[str]
    items: List[str]


# Action type indicators
PROMPT_TYPE_INDICATORS: Dict[PromptType, List[str]] = {
    "move": ["move", "go to", "travel", "walk", "enter"],
    "combat": ["combat", "attack", "fight", "battle", "enemy"],
    "talk": ["talk", "speak", "conversation", "dialogue"],
    "search": ["search", "look", "examine", "investigate"],
    "use_item": ["use", "item", "potion", "scroll", "equip"],
}


# Default responses for different action types
FALLBACK_RESPONSES: Dict[PromptType, FallbackResponse] = {
    "default": {
        "success": True,
        "message": "Não foi possível processar a solicitação no momento.",
    },
    "move": {
        "success": True,
        "new_location": "Caminho da Floresta",
        "description": (
            "Você caminha por um caminho sinuoso através de uma"
            " floresta densa."
        ),
        "npcs": [],
        "events": ["Uma suave brisa agita as folhas"],
        "message": (
            "Você caminha por um caminho sinuoso através de uma"
            " floresta densa."
        ),
    },
    "combat": {
        "success": True,
        "message": "Um inimigo aparece!"
    },
    "talk": {
        "success": True,
        "npc_name": "Aldeão Local",
        "dialogue": "Olá viajante! Desculpe, não posso conversar agora.",
        "options": [
            {
                "texto": "Continuar explorando",
                "tema": "exploração"
            }
        ],
        "message": "Olá viajante! Desculpe, não posso conversar agora.",
    },
    "search": {
        "success": True,
        "findings": (
            "Você examina a área, mas não encontra nada de especial"
            " no momento."
        ),
        "items": [],
        "message": (
            "Você examina a área, mas não encontra nada de especial"
            " no momento."
        ),
    },
    "use_item": {
        "success": False,
        "message": "Não foi possível usar o item no momento.",
    },
}


def generate_fallback_response(prompt: str) -> FallbackResponse:
    """Generate a fallback response when the AI service is unavailable.

    This function identifies the type of prompt and returns an appropriate
    scripted response to maintain a basic level of interaction.

    Args:
        prompt: The original prompt text that would have been sent to the AI

    Returns:
        A structured fallback response based on the identified prompt type
    """
    prompt_type = identify_prompt_type(prompt)

    logger.warning(
        "API fallback triggered",
        extra={
            "prompt_type": prompt_type,
            "prompt_length": len(prompt),
            "timestamp": datetime.now().isoformat(),
        }
    )

    return FALLBACK_RESPONSES.get(
        prompt_type,
        FALLBACK_RESPONSES["default"]
    )


def identify_prompt_type(prompt: str) -> PromptType:
    """Identify the type of prompt for fallback response selection.

    This function analyzes the input text for keywords to determine the
    most appropriate type of fallback response to provide.

    Args:
        prompt: The original prompt text to analyze

    Returns:
        The identified prompt type for response selection
    """
    prompt_lower = prompt.lower()

    for prompt_type, indicators in PROMPT_TYPE_INDICATORS.items():
        for indicator in indicators:
            if indicator in prompt_lower:
                return prompt_type

    return "default"
