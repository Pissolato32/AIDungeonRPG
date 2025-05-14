"""
Error handling module.

This module provides functionality for handling errors in the web application.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from flask import jsonify

from translations import get_text

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
        error_message = f"{context + ': ' if context else ''}{str(error)}"
        logger.error(error_message)
        logger.error(traceback.format_exc())

    @staticmethod
    def create_error_response(error_key: str, language: str, error_details: str = '') -> Any:
        """
        Create a standardized error response.

        Args:
            error_key: Key for the error message in translations
            language: Language code
            error_details: Additional error details

        Returns:
            JSON response with error message
        """
        message = get_text(f'errors.{error_key}', language, error_details)

        return jsonify({
            'success': False,
            'message': message,
            'error_key': error_key
        })

    @staticmethod
    def handle_route_error(e: Exception, route_name: str, language: str) -> Dict[str, Any]:
        """
        Handle an error in a route.

        Args:
            e: The exception
            route_name: Name of the route where the error occurred
            language: Language code

        Returns:
            Error response dictionary
        """
        # Log the error
        ErrorHandler.log_error(e, f"Error in {route_name} route")

        # Create error response
        return {
            'success': False,
            'message': get_text('errors.route_error', language, str(e)),
            'error': str(e)
        }