"""
Logging module.

This module provides functionality for logging game actions.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GameLogger:
    """
    Handles logging of game actions.

    Features:
    - Consistent log formatting
    - User ID privacy protection
    - Multi-level logging
    """

    @staticmethod
    def log_game_action(
        action: str, 
        details: str = '', 
        user_id: Optional[str] = None, 
        level: str = 'info'
    ) -> None:
        """
        Log game actions with consistent formatting and optional context.

        Args:
            action: The action being performed
            details: Additional details about the action
            user_id: Optional user ID for context
            level: Log level ('debug', 'info', 'warning', 'error', 'critical')
        """
        # Build the log message
        message_parts = [f"Action: {action}"]

        if details:
            message_parts.append(f"Details: {details}")

        if user_id:
            # Only show part of the ID for privacy
            message_parts.append(f"User: {user_id[:8]}...")

        log_message = " | ".join(message_parts)

        # Log at the appropriate level
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(log_message)
