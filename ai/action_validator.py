"""
Action validator module.

This module provides functions for validating player actions using artificial intelligence.
"""

import logging
from typing import Any, Dict

from ai.response_processor import (  # Moved import to the top for clarity
    process_ai_response,
)

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
        # If there is no artificial intelligence client, assume that the action
        # is valid
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
            "valid": true,  // ou false
            "reason": "Explicação breve se não for válida, caso contrário, uma string vazia ou uma confirmação."
        }}
        Exemplo de resposta válida: {{"valid": true, "reason": "Ação parece razoável."}}
        Exemplo de resposta inválida: {{"valid": false, "reason": "Não é possível voar sem asas."}}
        """

        # Enviar para a inteligência artificial
        response = ai_client.generate_response(prompt)

        # Processar resposta com tratamento de erro
        result = process_ai_response(response)
        if not isinstance(result, dict) or "valid" not in result:
            logger.warning(
                f"Formato de resposta inesperado da IA para validação de ação: {
                    str(result)[
                        :200]}"
            )
            # Mantendo o comportamento de fallback para True, mas idealmente
            # isso seria False ou tratado de forma diferente.
            return {"valid": True}

        # Se a ação for válida, podemos logar ou retornar a razão fornecida pela IA.
        # Se a ação for inválida, a razão é importante.
        # Não usaremos flash aqui, o chamador decide como usar a informação.
        return result

    except Exception as e:
        logger.error(f"Error validating action with artificial intelligence: {e}")
        # In case of error, assume that the action is valid
        return {"valid": True}
