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
        action: The type of action the player is attempting (e.g., "move", "look").
        details: Specific details of the action (e.g., "north", "the strange altar").
        location: The current location of the player in the game.
        ai_client: An optional AI client instance for making the validation call.
                   If None, validation defaults to True.
    Returns:
        A dictionary with 'valid' (boolean) and 'reason' (string) keys.
    """
    if not ai_client:
        return {"valid": True, "reason": "Validação de IA não disponível."}  # Traduzido

    try:
        prompt = f"""
        Você é um validador de ações em um jogo de RPG. Sua tarefa é verificar se a ação do jogador faz sentido no contexto atual do jogo.
        RESPONDA SEMPRE EM PORTUGUÊS DO BRASIL (pt-br).

        Contexto da Ação do Jogador:
        - Ação: {action}
        - Detalhes da Ação: {details}
        - Local Atual do Jogador: {location}

        Verifique se esta ação:
        1. Faz sentido lógico dentro do universo do jogo.
        2. É fisicamente possível para um humano em um apocalipse zumbi.
        3. Possui detalhes suficientes para ser compreendida e executada (ou narrada).

        Responda APENAS com um JSON no seguinte formato:
        {{
            "valid": true,  // ou false se a ação for completamente sem sentido ou impossível
            "reason": "Explicação breve em Português do Brasil se 'valid' for false. Se 'valid' for true, uma breve confirmação como 'Ação parece razoável.' ou uma string vazia."
        }}
        Exemplo de resposta válida: {{"valid": true, "reason": "Ação parece razoável."}}
        Exemplo de resposta inválida: {{"valid": false, "reason": "Não é possível voar sem asas."}}
        """

        response = ai_client.generate_response(
            messages=[{"role": "user", "content": prompt}]
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
