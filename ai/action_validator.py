# filepath: c:\Users\rodri\Desktop\REPLIT RPG\ai\action_validator.py
"""
Action validator module.

This module provides functions for validating player actions using artificial intelligence.
"""

import logging
from typing import Any, Dict

from ai.response_processor import process_ai_response

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
        return {"valid": True, "reason": "Validação de IA não disponível."}  # Traduzido

    try:
        prompt = f"""
        Você é um validador de ações em um jogo RPG. Sua tarefa é verificar se a ação do jogador faz sentido no contexto.
        RESPONDA SEMPRE EM PORTUGUÊS DO BRASIL (pt-br).

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
            "reason": "Explicação breve em Português do Brasil se não for válida, caso contrário, uma string vazia ou uma confirmação."
        }}
        Exemplo de resposta válida: {{"valid": true, "reason": "Ação parece razoável."}}
        Exemplo de resposta inválida: {{"valid": false, "reason": "Não é possível voar sem asas."}}
        """

        response = ai_client.generate_response(
            {"role": "user", "content": prompt}
        )  # Adicionado role e content

        result = process_ai_response(response)
        if not isinstance(result, dict) or "valid" not in result:
            logger.warning(
                f"Formato de resposta inesperado da IA para validação de ação: {
                    str(result)[
                        :200]}"
            )
            return {
                "valid": True,
                "reason": "Resposta da IA para validação não foi clara.",
            }  # Traduzido

        return result

    except Exception as e:
        logger.error(f"Erro ao validar ação com IA: {e}")  # Traduzido
        return {
            "valid": True,
            "reason": "Erro interno na validação por IA.",
        }  # Traduzido
