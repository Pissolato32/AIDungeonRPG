"""
Conversation manager module.

Handles NPC-player conversation history tracking, memory updates,
and prompt generation.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from typing_extensions import TypedDict

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
                topics=set(),  # Explicitly initialize as empty sets
                shared_info=set(),
                mentioned_quests=set(),
                trust_level=0,
            )

        npc_memory = self.npc_memory[context.npc_name]
        history = self._get_conversation_history(context.character_id)
        knowledge = ", ".join(context.npc_details.get("knowledge", []))

        npc_profession = context.npc_details.get("profession", "Desconhecida")
        npc_personality = context.npc_details.get("personality", "Neutra")
        npc_current_mood = context.npc_details.get("current_mood", "normal")

        prompt = (
            f"Você é {context.npc_name}, um personagem (NPC) em um jogo de RPG com tema de apocalipse zumbi. "
            "Interaja com o jogador de forma natural e consistente com sua personalidade e o contexto do mundo devastado.\n\n"
            "Sua personalidade:\n"
            f"- Raça: {context.npc_details.get('race', 'Humano')}\n"
            f"- Profissão/Papel: {npc_profession}\n"
            f"- Traços de Personalidade: {npc_personality}\n"
            f"- Conhecimento principal sobre: {knowledge if knowledge else 'Assuntos gerais de sobrevivência'}\n"
            f"- Estado emocional atual: {npc_current_mood}\n\n"
            "Memória da conversa com este jogador:\n"
        )

        topics = ", ".join(npc_memory["topics"])
        info = ", ".join(npc_memory["shared_info"])
        quests = ", ".join(npc_memory["mentioned_quests"])

        prompt += (
            f"- Tópicos já discutidos: {topics if topics else 'Nenhum'}\n"
            f"- Informações importantes compartilhadas: {info if info else 'Nenhuma'}\n"
            f"- Tarefas/Missões mencionadas: {quests if quests else 'Nenhuma'}\n"
            f"- Nível de confiança do jogador em você (de -100 a 100): {npc_memory['trust_level']}\n\n"
            "Contexto recente da situação no jogo (eventos ou observações):\n"
        )

        for ctx_item in context.recent_context:
            prompt += f"- {ctx_item}\n"

        if history:
            prompt += "\nHistórico da conversa (mais recente primeiro, últimas 5 interações):\n"
            for msg in reversed(history[-5:]):  # Mostrar as mais recentes primeiro
                role_prefix = (
                    "Jogador:"
                    if msg["role"] == "user"
                    else f"{
                        context.npc_name}:"
                )
                prompt += f"{role_prefix} {msg['content']}\n"

        prompt += (
            f"\nAgora, como {context.npc_name}, responda à última mensagem do jogador de forma natural e consistente com sua personalidade e o que já foi dito. "
            "Mantenha a conversa interessante e imersiva no tema de apocalipse zumbi. "
            "Revele informações gradualmente, talvez baseado na confiança ou no rumo da conversa. "
            "Seja breve e direto quando apropriado, mas também capaz de elaborar se o jogador demonstrar interesse. "
            "Lembre-se do perigo constante e da escassez de recursos."
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

        if context:  # Only update memory if context is provided
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
        if character_id in self.conversation_history:  # Check if key exists
            history = self.conversation_history[character_id]
            if len(history) > self.max_history_length:
                start_index = len(history) - self.max_history_length
                self.conversation_history[character_id] = history[start_index:]

    def _update_npc_memory(
        self, npc_name: str, message: str, context: Dict[str, Any]
    ) -> None:
        """Update NPC's memory based on conversation context.
        'message' (NPC's own response) is currently unused here but kept for potential future use
        (e.g., sentiment analysis on NPC response to adjust mood or extract entities).
        """
        if npc_name not in self.npc_memory:
            self.npc_memory[npc_name] = NPCMemory(
                topics=set(), shared_info=set(), mentioned_quests=set(), trust_level=0
            )

        memory = self.npc_memory[npc_name]

        # Ensure context is a dictionary before proceeding
        if not isinstance(context, dict):
            logger.warning(
                f"Context for NPC memory update is not a dict for {npc_name}. Context: {context}"
            )
            return

        # Update memory sets safely
        new_topics = context.get("topics")
        if isinstance(new_topics, (list, set)):
            memory["topics"].update(new_topics)
        elif new_topics is not None:
            logger.warning(
                f"Invalid type for 'topics' in context for {npc_name}: {
                    type(new_topics)}"
            )

        new_shared_info = context.get("shared_info")
        if isinstance(new_shared_info, (list, set)):
            memory["shared_info"].update(new_shared_info)
        elif new_shared_info is not None:
            logger.warning(
                f"Invalid type for 'shared_info' in context for {npc_name}: {
                    type(new_shared_info)}"
            )

        new_mentioned_quests = context.get(
            "quests"
        )  # Assuming 'quests' key in context maps to mentioned_quests
        if isinstance(new_mentioned_quests, (list, set)):
            memory["mentioned_quests"].update(new_mentioned_quests)
        elif new_mentioned_quests is not None:
            logger.warning(
                f"Invalid type for 'quests' in context for {npc_name}: {
                    type(new_mentioned_quests)}"
            )

        # Update trust level with boundaries
        trust_change = context.get("trust_change")
        if isinstance(trust_change, (int, float)):
            current_trust = memory["trust_level"]
            memory["trust_level"] = max(
                -100, min(100, int(current_trust + trust_change))
            )
        elif trust_change is not None:
            logger.warning(
                f"Invalid type for 'trust_change' in context for {npc_name}: {
                    type(trust_change)}"
            )
