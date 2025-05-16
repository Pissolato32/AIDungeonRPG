"""
Conversation manager module.

Handles NPC-player conversation history tracking, memory updates,
and prompt generation.
"""

import logging
from typing import Dict, List, Any, Optional, Set
from typing_extensions import TypedDict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ConversationMessage(TypedDict, total=True):
    """Type definition for conversation messages."""

    role: str
    content: str
    # Define the role of the message (user or assistant)


class NPCMemory(TypedDict, total=True):
    """Type definition for NPC conversation memory."""

    topics: Set[str]
    shared_info: Set[str]
    mentioned_quests: Set[str]
    trust_level: int


class NPCDetails(TypedDict, total=True):
    """Type definition for NPC details."""

    race: str
    profession: str
    personality: str
    knowledge: List[str]
    current_mood: str


@dataclass
class ConversationContext:
    """Context for a conversation with an NPC."""

    character_id: str
    npc_name: str
    npc_details: NPCDetails
    recent_context: List[str]


class ConversationManager:
    """Manages conversation history and context for NPC interactions."""

    def __init__(self, max_history_length: int = 20) -> None:
        """Initialize the conversation manager.

        Args:
            max_history_length: Maximum messages to keep in history
        """
        self.max_history_length = max_history_length
        self.conversation_history: Dict[str, List[ConversationMessage]] = {}
        self.npc_memory: Dict[str, NPCMemory] = {}

    def get_conversation_prompt(self, context: ConversationContext) -> str:
        """Generate a contextual conversation prompt.

        Args:
            context: Current conversation context and NPC details

        Returns:
            str: Formatted prompt for AI model
        """
        if context.npc_name not in self.npc_memory:
            self.npc_memory[context.npc_name] = NPCMemory(
                topics=set(), shared_info=set(), mentioned_quests=set(), trust_level=0
            )

        npc_memory = self.npc_memory[context.npc_name]
        history = self._get_conversation_history(context.character_id)
        knowledge = ", ".join(context.npc_details.get("knowledge", []))

        # Split long lines for readability
        npc_profession = context.npc_details.get("profession", "Unknown")
        npc_personality = context.npc_details.get("personality", "Neutral")
        npc_current_mood = context.npc_details.get("current_mood", "normal")

        prompt = (
            f"Você é um NPC chamado {context.npc_name} em um RPG "
            "medieval.\n\n"
            "Sua personalidade:\n"
            f"- Raça: {context.npc_details.get('race', 'Unknown')}\n"
            f"- Profissão: {npc_profession}\n"
            f"- Personalidade: {npc_personality}\n"
            f"- Conhecimento sobre: {knowledge}\n"
            f"- Estado atual: {npc_current_mood}\n\n"
            "Memória da conversa:\n"
        )

        # Add memory sections
        topics = ", ".join(npc_memory["topics"])
        info = ", ".join(npc_memory["shared_info"])
        quests = ", ".join(npc_memory["mentioned_quests"])

        prompt += (
            f"- Tópicos: {topics}\n"
            f"- Info: {info}\n"
            f"- Quests: {quests}\n\n"
            "Contexto recente:\n"
        )

        # Add recent context
        for ctx in context.recent_context:
            prompt += f"- {ctx}\n"

        # Add conversation history
        if history:
            prompt += "\nHistórico da conversa:\n"
            for msg in history[-5:]:
                prompt += f"{msg['content']}\n"

        prompt += (
            "\nResponda naturalmente e consistentemente.\n"
            "Mantenha a conversa interessante.\n"
            "Revele informações baseado na confiança.\n"
        )

        return prompt

    def add_user_message(self, character_id: str, message: str) -> None:
        """Add a user message to conversation history.

        Args:
            character_id: Unique identifier for the player character
            message: Content of the player's message
        """
        if character_id not in self.conversation_history:
            self.conversation_history[character_id] = []

        new_message = ConversationMessage(role="user", content=message)
        self.conversation_history[character_id].append(new_message)
        self._trim_conversation_history(character_id)

    def add_assistant_message(
        self,
        character_id: str,
        npc_name: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an NPC response to conversation history.

        Args:
            character_id: Unique identifier for the player character
            npc_name: Name of the responding NPC
            message: Content of the NPC's response
            context: Optional additional context for memory updates
        """
        if character_id not in self.conversation_history:
            self.conversation_history[character_id] = []

        new_message = ConversationMessage(role="assistant", content=message)
        self.conversation_history[character_id].append(new_message)
        self._trim_conversation_history(character_id)

        # Update NPC memory
        self._update_npc_memory(npc_name, message, context)

    def _get_conversation_history(self, character_id: str) -> List[ConversationMessage]:
        """Retrieve conversation history for a character.

        Args:
            character_id: Unique identifier for the player character

        Returns:
            List of conversation messages
        """
        return self.conversation_history.get(character_id, [])

    def _trim_conversation_history(self, character_id: str) -> None:
        """Trim conversation history to maximum length.

        Args:
            character_id: Unique identifier for the player character
        """
        history = self.conversation_history[character_id]
        if len(history) > self.max_history_length:
            start = len(history) - self.max_history_length
            self.conversation_history[character_id] = history[start:]

    def _update_npc_memory(
        self, npc_name: str, message: str, context: Dict[str, Any]
    ) -> None:
        """Update NPC's memory based on conversation context.

        Args:
            npc_name: Name of the NPC
            message: Content of the message
            context: Additional context for memory updates
        """
        if npc_name not in self.npc_memory:
            self.npc_memory[npc_name] = NPCMemory(
                topics=set(), shared_info=set(), mentioned_quests=set(), trust_level=0
            )

        memory = self.npc_memory[npc_name]

        # Update memory sets
        if "topics" in context:
            memory["topics"].update(context["topics"])
        if "shared_info" in context:
            memory["shared_info"].update(context["shared_info"])
        if "quests" in context:
            memory["mentioned_quests"].update(context["quests"])

        # Update trust level with boundaries
        if "trust_change" in context:
            current = memory["trust_level"]
            delta = context["trust_change"]
            memory["trust_level"] = max(-100, min(100, current + delta))
