# web/error_handler.py
import logging
import traceback
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ErrorHandler:
    def __init__(self):
        # Configurações adicionais podem ser feitas aqui
        pass

    def handle_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Handle generic errors, logging them with optional context."""
        context_info = f" Context: {context}" if context else ""
        logger.error(f"Erro ocorreu: {error}{context_info}")
        logger.debug(traceback.format_exc())

    def handle_exception(
        self, exception: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Handle exceptions with full traceback and optional context."""
        context_info = f" Context: {context}" if context else ""
        logger.critical(f"Exceção ocorreu: {exception}{context_info}")
        logger.critical(traceback.format_exc())

    @staticmethod
    def format_error_response(
        message: str, code: int = 500, details: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a standardized error response (for APIs)."""
        response = {
            "success": False,
            "error": {
                "message": message,
                "code": code,
            },
        }
        if details:
            response["error"]["details"] = details
        return response
