"""Fallback response handler module.

This module provides functions for generating graceful fallback responses when
the AI service is temporarily unavailable or experiencing issues.
"""

import logging
from datetime import datetime
from typing import Dict, List, Literal, Optional, TypedDict

logger = logging.getLogger(__name__)

# Type definitions
PromptType = Literal["move", "combat", "talk", "search", "use_item", "default"]


class DialogueOption(TypedDict):
    """Type definition for dialogue options."""

    texto: str
    tema: str


class FallbackResponse(TypedDict, total=False):
    """Type definition for fallback responses."""

    success: bool
    message: str
    current_detailed_location: Optional[str]  # Alinhado com AIResponse
    scene_description_update: Optional[str]  # Alinhado com AIResponse
    interpreted_action_type: Optional[str]  # Alinhado com AIResponse
    interactable_elements: Optional[List[str]]  # Alinhado com AIResponse
    # Campos antigos que podem ser mapeados ou removidos se não forem mais usados diretamente
    # pelo GameAIClient._handle_ai_failure
    # new_location: Optional[str] # Pode ser substituído por current_detailed_location
    # description: Optional[str] # Pode ser substituído por scene_description_update
    # npcs: Optional[List[str]] # Pode ser mapeado para interactable_elements ou details
    # events: Optional[List[str]] # Pode ser mapeado para details
    # npc_name: Optional[str] # Pode ser parte de details
    # dialogue: Optional[str] # A message principal já cobre isso
    # options: Optional[List[DialogueOption]] # Pode ser parte de details
    # findings: Optional[str] # Pode ser parte de details
    # items: Optional[List[str]] # Pode ser mapeado para interactable_elements


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
        "success": True,  # Ou False se quiser sinalizar um problema maior
        "message": "Não foi possível processar a solicitação no momento.",
        # Adicionar campos para completar AIResponse
        "current_detailed_location": None,  # Será preenchido pelo game_state atual no GameAIClient
        "scene_description_update": None,  # Será preenchido pelo game_state atual no GameAIClient
        "interpreted_action_type": "unknown_fallback",
        "interactable_elements": [],
    },
    "move": {
        "success": True,
        "message": "Você caminha por um caminho sinuoso através de uma floresta densa.",
        "current_detailed_location": "Caminho da Floresta (Fallback)",  # Nome do novo local
        "scene_description_update": "Uma floresta densa com um caminho sinuoso. Uma suave brisa agita as folhas.",  # Descrição do novo local
        "interpreted_action_type": "move_fallback",
        "interactable_elements": ["Árvore Antiga", "Riacho Próximo"],  # Exemplo
        # 'npcs' e 'events' do seu fallback original podem ser mapeados para interactable_elements ou uma nova chave em details
    },
    "combat": {
        "success": True,
        "message": "Um inimigo hostil surge das sombras, pronto para atacar!",
        "current_detailed_location": None,  # Mantém o local atual
        "scene_description_update": "A tensão aumenta com a presença ameaçadora.",
        "interpreted_action_type": "combat_fallback_start",
        "interactable_elements": ["Inimigo Agressivo"],
    },
    "talk": {
        "success": True,
        "message": "Um sobrevivente próximo olha para você, mas parece muito ocupado ou desconfiado para uma conversa longa agora. Ele apenas acena com a cabeça.",
        "current_detailed_location": None,  # Mantém o local atual
        "scene_description_update": None,  # Mantém a descrição atual
        "interpreted_action_type": "talk_fallback_brief",
        "interactable_elements": ["Sobrevivente Ocupado"],  # Exemplo de NPC
        # "options" e "npc_name" podem ir para um campo "details" se necessário
    },
    "search": {
        "success": True,
        "message": "Você examina a área, mas não encontra nada de especial no momento.",
        "current_detailed_location": None,  # Mantém o local atual
        "scene_description_update": "Após uma busca rápida, o local parece o mesmo.",
        "interpreted_action_type": "search_fallback_nothing",
        "interactable_elements": [],  # Ou talvez ["Escombros", "Caixa Vazia"]
    },
    "use_item": {
        "success": True,  # A ação de tentar usar foi "processada", mesmo que o item não tenha efeito
        "message": "Não foi possível usar o item no momento.",
        "current_detailed_location": None,
        "scene_description_update": None,
        "interpreted_action_type": "use_item_fallback_fail",
        "interactable_elements": [],
    },
}


def generate_fallback_response(prompt: str) -> FallbackResponse:
    """Generate a fallback response when the AI service is unavailable.

    This function identifies the type of prompt and returns an appropriate
    scripted response to maintain a basic level of interaction.

    Args:
        prompt: The original prompt text that would have been sent to the AI.

    Returns:
        A FallbackResponse TypedDict structured based on the identified prompt type.
    """
    prompt_type = identify_prompt_type(prompt)
    logger.warning(
        "API fallback triggered",
        extra={
            "prompt_type": prompt_type,
            "prompt_length": len(prompt),
            "timestamp": datetime.now().isoformat(),
        },
    )

    return FALLBACK_RESPONSES.get(prompt_type, FALLBACK_RESPONSES["default"])


def identify_prompt_type(prompt: str) -> PromptType:
    """Identify the type of prompt for fallback response selection.

    This function analyzes the input text for keywords to determine the
    most appropriate type of fallback response to provide.

    Args:
        prompt: The original prompt text to analyze.

    Returns:
        The identified PromptType (e.g., "move", "combat", "default").
    """
    prompt_lower = prompt.lower()
    for prompt_type, indicators in PROMPT_TYPE_INDICATORS.items():
        for indicator in indicators:
            if indicator in prompt_lower:
                return prompt_type

    return "default"
