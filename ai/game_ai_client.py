"""Game AI client module.

This module handles AI model interactions for generating game content
and responses."""

import logging
from typing import Dict, Any, TypedDict, Optional, cast
from core.game_engine import GameState

logger = logging.getLogger(__name__)


class AIPrompt(TypedDict):
    """Type definition for AI prompt data."""

    role: str
    content: str


class AIResponse(TypedDict, total=False):
    """Type definition for AI response data."""

    success: bool
    message: str
    error: Optional[str]
    details: Optional[Dict[str, str]]


class GameAIClient:
    """Client for handling AI model interactions in the game."""

    def __init__(self, ai_client: Any = None) -> None:
        """Initialize the Game AI Client.

        Args:
            ai_client: External AI client to use
        """
        self.ai_client = ai_client

    def _create_action_prompt(
        self,
        action: str,
        details: str,
        character: Any,
        game_state: GameState
    ) -> AIPrompt:
        """Create a formatted prompt for the AI model.

        Args:
            action: Type of action being performed
            details: Additional action details
            character: Player character data
            game_state: Current game state

        Returns:
            Formatted prompt for the AI model
        """        # Get state variables from GameState dataclass
        location = game_state.current_location or "Unknown"
        messages = game_state.messages[-5:] if game_state.messages else []

        # Get current location data
        loc_data = game_state.discovered_locations.get(location, {})
        events = loc_data.get("events", [])

        # Format state info
        state_dict = {
            "current_location": location,
            "scene_description": game_state.scene_description,
            "npcs_present": game_state.npcs_present,
            "events": events,
            "messages": messages
        }

        # Build the base prompt
        prompt = (
            "Você é o Mestre de um RPG medieval de fantasia. "
            "Mantenha o tom narrativo e imersivo em suas respostas.\n\n"
        )

        # Add game state information
        prompt += (
            f"Local atual: {state_dict['current_location']}\n"
            f"Descrição: {state_dict['scene_description']}\n"
        )

        # Format NPCs and events with proper line wrapping
        npcs = state_dict["npcs_present"]
        npcs_text = ", ".join(npcs) if npcs else "Nenhum"
        prompt += f"NPCs presentes: {npcs_text}\n"

        events = state_dict["events"]
        events_text = ", ".join(events) if events else "Nenhum"
        prompt += f"Eventos ativos: {events_text}\n\n"

        # Add character information
        prompt += (
            "Personagem do jogador:\n"
            f"- Nome: {character.name}\n"
            f"- Raça: {character.race}\n"
            f"- Classe: {character.character_class}\n"
            f"- Nível: {character.level}\n"
            f"- HP: {character.current_hp}/{character.max_hp}\n\n"
        )

        # Add action information
        prompt += (
            f"Ação atual: {action}\n"
            f"Detalhes: {details}\n\n"
            "Diretrizes:\n"
            "1. Crie respostas vívidas e envolventes\n"
            "2. Seja consistente com o mundo\n"
            "3. Mantenha o tom do RPG\n"
            "4. Evite respostas vagas\n"
            "5. Use detalhes sensoriais\n\n"
        )

        return AIPrompt(role="user", content=prompt)

    def process_action(
        self,
        action: str,
        details: str,
        character: Any,
        game_state: GameState
    ) -> AIResponse:
        """Process a player action using AI.

        Args:
            action: Type of action being performed
            details: Additional action details
            character: Player character data
            game_state: Current game state

        Returns:
            AI response containing action results
        """
        if not self.ai_client:
            return AIResponse(
                success=False,
                message="AI client not initialized",
                error="No AI client available"
            )

        try:
            # Create and send prompt
            prompt = self._create_action_prompt(
                action,
                details,
                character,
                game_state
            )
            response = self.ai_client.generate_response(prompt)

            # Process the response
            from .response_processor import process_ai_response
            result = process_ai_response(response)

            # Ensure proper typing
            return cast(AIResponse, result)

        except Exception as e:
            logger.error(f"Error processing action: {e}")
            return AIResponse(
                success=False,
                message="Failed to process action",
                error=str(e)
            )
