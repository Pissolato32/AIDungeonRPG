"""
Session management module.

This module provides functionality for managing user sessions.
"""

import os
import logging
from typing import Dict, Any, Optional
from flask import session

from translations import TranslationManager

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages user sessions for the game application.

    Features:
    - User ID generation and management
    - Language preference management
    - Session initialization and validation
    """

    @staticmethod
    def ensure_session_initialized() -> str:
        """
        Ensure user session is properly initialized with required values.

        Returns:
            str: The user ID from the session
        """
        # Generate a user ID if not exists
        if 'user_id' not in session:
            session['user_id'] = os.urandom(16).hex()
            logger.debug(f"Generated new user ID: {session['user_id'][:8]}...")

        # Set default language if not set
        if 'language' not in session:
            session['language'] = TranslationManager.DEFAULT_LANGUAGE
            logger.debug(f"Set default language: {session['language']}")

        return session['user_id']

    @staticmethod
    def get_user_id() -> Optional[str]:
        """
        Get the current user ID from the session.

        Returns:
            str: User ID or None if not set
        """
        return session.get('user_id')

    @staticmethod
    def get_language() -> str:
        """
        Get the current language from the session.

        Returns:
            str: Language code
        """
        return session.get('language', TranslationManager.DEFAULT_LANGUAGE)

    @staticmethod
    def set_language(language: str) -> None:
        """
        Set the language preference in the session.

        Args:
            language: Language code
        """
        session['language'] = language
        logger.debug(f"Language set to: {language}")

    @staticmethod
    def regenerate_user_id() -> str:
        """
        Generate a new user ID and store it in the session.

        Returns:
            str: New user ID
        """
        session['user_id'] = os.urandom(16).hex()
        logger.debug(f"Regenerated user ID: {session['user_id'][:8]}...")
        return session['user_id']

    @staticmethod
    def get_session_data() -> Dict[str, Any]:
        """
        Get all session data.

        Returns:
            Dict: Session data
        """
        return dict(session)
