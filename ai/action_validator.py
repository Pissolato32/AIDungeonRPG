"""
Action validator module.

This module provides functions for validating player actions using AI.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def validate_action_with_ai(
    action: str, details: str, location: str, ai_client=None
) -> Dict[str, Any]:
    """
    Validate if an action makes sense using AI.

    Args:
        action: The type of action (move, look, etc.)
        details: The details of the action
        location: Current location of the player
        ai_client: Optional AI client to use

    Returns:
        Dictionary with validation result
    """
    if not ai_client:
        # Se não tiver cliente AI, assume que a ação é válida
        return {"valid": True}

    try:
        # Criar prompt para validação
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

        # Enviar para a IA
        response = ai_client.generate_response(prompt)

        # Processar resposta
        from ai.response_processor import process_ai_response

        result = process_ai_response(response)

        # Verificar se o resultado tem o formato esperado
        if isinstance(result, dict) and "valid" in result:
            return result

        # Formato inesperado, retornar resultado padrão
        logger.warning(
            "Unexpected validation response format",
            extra={"response": str(result)[:100]},
        )
        return {"valid": True}

    except Exception as e:
        logger.error(f"Error validating action with AI: {e}")
        # Em caso de erro, assume que a ação é válida
        return {"valid": True}
