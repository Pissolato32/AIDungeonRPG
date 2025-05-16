"""
Action validator module.

This module provides functions for validating player actions using artificial intelligence.
"""

from flask import flash  # Import flash for error messages
import logging
from typing import Dict, Any, Optional
from ai.response_processor import (
    process_ai_response,
)  # Moved import to the top for clarity

logger = logging.getLogger(__name__)


def validate_action_with_ai(
    action: str, details: str, location: str, ai_client=None
) -> Dict[str, Any]:
    """
    Validate if an action makes sense using artificial intelligence.

    Args:
        action: The type of action (move, look, etc.)
        details: The details of the action
        location: Current location of the player
        ai_client: Optional artificial intelligence client to use

    Returns:
        Dictionary with validation result
    """
    if not ai_client:
        # If there is no artificial intelligence client, assume that the action is valid
        return {"valid": True}

    try:
        # Create prompt for action validation
        prompt = f"""
        Você é um validador de ações em um jogo RPG. Sua tarefa é verificar se a ação do jogador faz sentido no contexto.
        
        Detalhes:
        - Ação: {action}
        - Descrição: {details}
        - Local atual: {location}
        
        Verifique se esta ação:
        1. Faz sentido logicamente
        2. É fisicamente possível
        3. Tem detalhes suficientes para ser executada
        
        Responda APENAS com um JSON no seguinte formato:
        {{
            "valid": true/false,
            "reason": "Explicação breve se não for válida"
        }}
        """

        flash("Ação validada com sucesso.", "success")  # Flash success message
        # Enviar para a inteligência artificial
        response = ai_client.generate_response(prompt)

        # Processar resposta com tratamento de erro
        result = process_ai_response(response)
        if not isinstance(result, dict) or "valid" not in result:
            logger.warning(
                "Formato de resposta inesperado", extra={"response": str(result)[:100]}
            )
            return {"valid": True}

    except Exception as e:
        logger.error(f"Error validating action with artificial intelligence: {e}")
        # In case of error, assume that the action is valid
        return {"valid": True}
