"""
Fallback response handler module.

This module provides functions for generating fallback responses when the AI service is unavailable.
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


# Map of keywords to prompt types
PROMPT_TYPE_INDICATORS = {
    "move": ["move", "go to", "travel", "walk", "enter"],
    "combat": ["combat", "attack", "fight", "battle", "enemy"],
    "talk": ["talk", "speak", "conversation", "dialogue"],
    "search": ["search", "look", "examine", "investigate"],
    "use_item": ["use", "item", "potion", "scroll", "equip"]
}

# Fallback responses by prompt type
FALLBACK_RESPONSES = {
    "default": {
        "success": True,
        "message": "Não foi possível processar a solicitação no momento."
    },
    "move": {
        "success": True,
        "new_location": "Caminho da Floresta",
        "description": "Você caminha por um caminho sinuoso através de uma floresta densa.",
        "npcs": [],
        "events": ["Uma suave brisa agita as folhas"],
        "message": "Você caminha por um caminho sinuoso através de uma floresta densa."
    },
    "combat": {
        "success": True,
        "message": "Um inimigo aparece!"
    },
    "talk": {
        "success": True,
        "npc_name": "Aldeão Local",
        "dialogue": "Olá viajante! Desculpe, não posso conversar agora.",
        "options": [{"texto": "Continuar explorando", "tema": "exploração"}],
        "message": "Olá viajante! Desculpe, não posso conversar agora."
    },
    "search": {
        "success": True,
        "findings": "Você examina a área, mas não encontra nada de especial no momento.",
        "items": [],
        "message": "Você examina a área, mas não encontra nada de especial no momento."
    },
    "use_item": {
        "success": False,
        "message": "Não foi possível usar o item no momento."
    }
}


def generate_fallback_response(prompt: str) -> Dict[str, Any]:
    """
    Generate a fallback response when the API is unavailable.

    Args:
        prompt: Original prompt

    Returns:
        Fallback response
    """
    # Identify prompt type
    prompt_type = identify_prompt_type(prompt)

    # Log with structured information
    logger.warning(
        "API fallback triggered",
        extra={
            "prompt_type": prompt_type,
            "prompt_length": len(prompt),
            "timestamp": datetime.now().isoformat()
        }
    )

    # Return appropriate fallback response
    return FALLBACK_RESPONSES.get(prompt_type, FALLBACK_RESPONSES["default"])


def identify_prompt_type(prompt: str) -> str:
    """
    Identify the type of prompt to provide appropriate fallback responses.

    Args:
        prompt: Original prompt text

    Returns:
        String identifying the prompt type
    """
    prompt_lower = prompt.lower()

    # Check for each type of prompt
    for prompt_type, keywords in PROMPT_TYPE_INDICATORS.items():
        if any(keyword in prompt_lower for keyword in keywords):
            return prompt_type

    return "default"
