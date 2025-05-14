"""
Conversation manager module.

This module provides functionality for managing conversation history with AI models.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages conversation history for AI interactions.

    Features:
    - Maintains separate conversation histories for different characters
    - Limits conversation history length to prevent token overflow
    - Provides methods for adding and retrieving messages
    """

    def __init__(self, max_history_length: int = 20, system_message: Optional[Dict[str, str]] = None):
        """
        Initialize the conversation manager.

        Args:
            max_history_length: Maximum number of messages to keep in history
            system_message: System message to include at the start of conversations
        """
        self.max_history_length = max_history_length
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}

        # Default system message if none provided
        self.system_message = system_message or {
            "role": "system",
            "content": (
                "You are an RPG assistant that generates narrative content. "
                "Always respond in the exact format requested. "
                "Be descriptive, engaging, and creative. "
                "Always return valid JSON when requested. "
                "Never include additional text outside the JSON structure."
            )
        }

    def reset_conversation(self, character_id: str) -> None:
        """
        Reset the conversation history for a character.

        Args:
            character_id: Unique identifier for the character
        """
        self.conversation_history[character_id] = [self.system_message]
        logger.debug("Conversation reset", extra={"character_id": character_id})

    def add_user_message(self, character_id: str, message: str) -> None:
        """
        Add a user message to the conversation history.

        Args:
            character_id: Unique identifier for the character
            message: User message content
        """
        # Initialize history if it doesn't exist
        if character_id not in self.conversation_history:
            self.reset_conversation(character_id)

        # Add message
        self.conversation_history[character_id].append({
            "role": "user",
            "content": message
        })

        # Trim history if needed
        self._trim_conversation_history(character_id)

    def add_assistant_message(self, character_id: str, message: str) -> None:
        """
        Add an assistant message to the conversation history.

        Args:
            character_id: Unique identifier for the character
            message: Assistant message content
        """
        # Initialize history if it doesn't exist
        if character_id not in self.conversation_history:
            self.reset_conversation(character_id)

        # Add message
        self.conversation_history[character_id].append({
            "role": "assistant",
            "content": message
        })

        # Trim history if needed
        self._trim_conversation_history(character_id)

    def get_conversation_history(self, character_id: str) -> List[Dict[str, str]]:
        """
        Get the conversation history for a character.

        Args:
            character_id: Unique identifier for the character

        Returns:
            List of conversation messages
        """
        # Initialize history if it doesn't exist
        if character_id not in self.conversation_history:
            self.reset_conversation(character_id)

        return self.conversation_history[character_id]

    def _trim_conversation_history(self, character_id: str) -> None:
        """
        Reduce conversation history by keeping only the most recent messages.

        Args:
            character_id: Unique identifier for the character
        """
        history = self.conversation_history.get(character_id, [self.system_message])

        if len(history) > self.max_history_length:
            # Keep system message and the most recent messages
            self.conversation_history[character_id] = [
                self.system_message
            ] + history[-(self.max_history_length-1):]

            logger.debug("Trimmed conversation history", extra={"character_id": character_id})

    def set_system_message(self, system_message: Dict[str, str]) -> None:
        """
        Update the system message used for all conversations.

        Args:
            system_message: New system message
        """
        self.system_message = system_message

        # Update system message in all existing conversations
        for character_id in self.conversation_history:
            if self.conversation_history[character_id]:
                self.conversation_history[character_id][0] = system_message