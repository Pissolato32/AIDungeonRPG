"""
Game state management module.

This module provides functionality for managing game state.
"""

import logging
from typing import Optional

from game_engine import GameState
from translations import TranslationManager

logger = logging.getLogger(__name__)


class GameStateManager:
    """
    Manages game state creation and loading.

    Features:
    - Initial game state creation
    - Language-specific game state loading
    - Game state initialization
    """

    @staticmethod
    def create_initial_game_state(language: str) -> GameState:
        """
        Create an initial game state for a new character.

        Args:
            language: The language to use for the game state

        Returns:
            GameState: A newly initialized game state
        """
        game_state = GameState()

        # Set initial location with unique name and coordinates
        game_state.current_location = "Aldeia de Rivenbrook"
        game_state.location_id = "village_center"
        game_state.coordinates = {"x": 0, "y": 0, "z": 0}
        game_state.scene_description = "Você está no centro de uma pequena aldeia chamada Rivenbrook. Há uma taverna ao norte chamada 'O Javali Dourado', uma ferraria a leste, e o portão da aldeia ao sul."

        # Set NPCs and environmental elements
        game_state.npcs_present = ["Ancião da Aldeia", "Mercador Viajante"]
        game_state.events = ["Uma brisa suave sopra pela aldeia."]

        # Set welcome message and language
        game_state.messages = [
            "Bem-vindo a Rivenbrook! Você pode explorar usando as ações abaixo."
        ]
        game_state.language = language

        # Initialize world map with the starting location
        game_state.world_map = {
            "village_center": {
                "name": "Aldeia de Rivenbrook",
                "coordinates": {"x": 0, "y": 0, "z": 0},
                "connections": {
                    "north": "golden_boar_tavern",
                    "east": "blacksmith_shop",
                    "south": "village_gate",
                },
            },
            "golden_boar_tavern": {
                "name": "Taverna O Javali Dourado",
                "coordinates": {"x": 0, "y": 1, "z": 0},
                "connections": {"south": "village_center"},
            },
            "blacksmith_shop": {
                "name": "Ferraria do Martelo Flamejante",
                "coordinates": {"x": 1, "y": 0, "z": 0},
                "connections": {"west": "village_center"},
            },
            "village_gate": {
                "name": "Portão da Aldeia",
                "coordinates": {"x": 0, "y": -1, "z": 0},
                "connections": {"north": "village_center", "south": "crossroads"},
            },
        }

        # Mark the starting location as visited
        game_state.visited_locations = {
            "village_center": {
                "name": "Aldeia de Rivenbrook",
                "last_visited": "initial",
                "description": game_state.scene_description,
                "npcs_seen": game_state.npcs_present.copy(),
                "events_seen": game_state.events.copy(),
            }
        }

        logger.info(f"Created initial game state with language: {language}")
        return game_state

    @staticmethod
    def load_game_state_with_language(
        game_engine, user_id: str, language: str
    ) -> Optional[GameState]:
        """
        Load game state for a user and set the current language.

        Args:
            game_engine: Game engine instance
            user_id: The user's unique identifier
            language: Language to set

        Returns:
            GameState object with language set from session
        """
        game_state = game_engine.load_game_state(user_id)

        if game_state:
            # Update language
            game_state.language = language or TranslationManager.DEFAULT_LANGUAGE
            logger.debug(
                f"Loaded game state for user {user_id[:8]}... with language: {game_state.language}"
            )
        else:
            logger.warning(f"No game state found for user {user_id[:8]}...")

        return game_state
