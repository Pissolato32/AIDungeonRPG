"""
Error handling module.

This module provides functionality for handling errors in the web application.
"""

import logging
import traceback
from typing import Any, Dict, Optional

from flask import jsonify

logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Handles errors in the web application.

    Features:
    - Standardized error responses
    - Error logging
    - Translation support
    """

    @staticmethod
    def log_error(error: Exception, context: Optional[str] = None) -> None:
        """
        Log an error with context.

        Args:
            error: The exception to log
            context: Additional context information
        """
        error_message = f"{context + ': ' if context else ''}{error}"
        logger.error(error_message)
        logger.error(traceback.format_exc())

    @staticmethod
    def _get_error_message(
        error_key: str, language: str, error_details: str = ""
    ) -> str:
        """
        Internal helper to get a pre-defined error message.
        Since translations are removed, this will return pt-br strings.
        """
        # language parameter is kept for signature compatibility but ignored.
        messages_pt_br = {
            "errors.no_active_session": "Nenhuma sessão ativa. Por favor, reinicie.",
            "errors.no_character_found": "Nenhum personagem encontrado. Por favor, crie um novo.",
            "errors.invalid_input": f"Entrada inválida: {error_details}",
            "errors.unexpected": f"Ocorreu um erro inesperado: {error_details}",
            "errors.action_not_found": f"Ação desconhecida: {error_details}",
            "errors.route_error": f"Erro na rota: {error_details}",
            "errors.reset_error": f"Erro ao resetar o jogo: {error_details}",
            "errors.reset_error_character": f"Erro ao deletar dados do personagem durante o reset: {error_details}",
            "errors.reset_error_game_state": f"Erro ao deletar estado do jogo durante o reset: {error_details}",
            # Adicione outras chaves de erro conforme necessário
        }
        return messages_pt_br.get(
            error_key, f"Erro desconhecido: {error_key}. Detalhes: {error_details}"
        )

    @staticmethod
    def create_error_response(
        error_key: str, language: str, error_details: str = ""
    ) -> Any:
        # language parameter is kept for signature compatibility but will be
        # 'pt-br'
        message = ErrorHandler._get_error_message(
            f"errors.{error_key}", language, error_details
        )

        return jsonify({"success": False, "message": message, "error_key": error_key})

    @staticmethod
    def handle_route_error(
        e: Exception, route_name: str, language: str
    ) -> Dict[str, Any]:
        # Log the error
        ErrorHandler.log_error(e, f"Error in {route_name} route")

        # language parameter is kept for signature compatibility but will be
        # 'pt-br'
        error_message_str = ErrorHandler._get_error_message(
            "errors.route_error", language, str(e)
        )

        # Create error response
        return {
            "success": False,
            "message": error_message_str,
            "error": str(e),
        }
