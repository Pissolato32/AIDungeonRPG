"""
Game state management module.

This module provides functionality for managing game state.
"""

import logging
from typing import Optional

from core.game_state_model import GameState  # Direct import

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
    def create_initial_game_state() -> GameState:
        """
        Create an initial game state for a new character.

        Returns:
            GameState: A newly initialized game state
        """
        game_state = GameState()

        # Set initial location with unique name and coordinates
        game_state.current_location = "Abrigo Subterrâneo"
        game_state.location_id = "bunker_main"  # Set the initial location ID
        game_state.coordinates = {"x": 0, "y": 0, "z": 0}
        game_state.scene_description = "Você está na sala principal de um abrigo subterrâneo improvisado. As paredes de concreto são úmidas e a única luz vem de algumas lâmpadas de emergência piscando. Há um portão de metal reforçado ao norte que leva à superfície, uma enfermaria improvisada a leste e um depósito de suprimentos a oeste."

        # Set NPCs and environmental elements
        game_state.npcs_present = [
            "Velho Sobrevivente Cansado",
            "Médica de Campo Apavorada",
        ]
        game_state.events = [
            "Ouve-se o gotejar constante de água em algum lugar próximo.",
            "Um gerador falha e a luz pisca antes de voltar.",
        ]

        # Set welcome message in the new format
        game_state.messages = [
            {
                "role": "assistant",
                "content": "Você acorda no abrigo. O mundo lá fora mudou. Sobreviva.",
            }
        ]

        # Initialize world map with the starting location
        game_state.world_map = {
            "bunker_main": {
                "name": "Abrigo Subterrâneo - Principal",
                "coordinates": {"x": 0, "y": 0, "z": 0},
                "connections": {
                    "north": "bunker_exit_tunnel",  # Saída para a superfície
                    "east": "bunker_infirmary",
                    "west": "bunker_storage",
                },
            },
            "bunker_exit_tunnel": {
                "name": "Túnel de Saída do Abrigo",
                "coordinates": {"x": 0, "y": 1, "z": 0},
                "connections": {
                    "south": "bunker_main",
                    "north": "ruined_street_01",
                },  # Leva para a rua
            },
            "bunker_infirmary": {
                "name": "Enfermaria do Abrigo",
                "coordinates": {"x": 1, "y": 0, "z": 0},
                "connections": {"west": "bunker_main"},
            },
            "bunker_storage": {
                "name": "Depósito do Abrigo",
                "coordinates": {"x": -1, "y": 0, "z": 0},
                "connections": {"east": "bunker_main"},
            },
            # Example of an outside location
            "ruined_street_01": {
                "name": "Rua Devastada Próxima ao Abrigo",
                # Assuming surface is y=2
                "coordinates": {"x": 0, "y": 2, "z": 0},
                "connections": {"south": "bunker_exit_tunnel"},
            },
        }

        # Mark the starting location as visited
        game_state.visited_locations = {
            "bunker_main": {
                "name": "Abrigo Subterrâneo - Principal",
                "last_visited": "initial",
                "description": game_state.scene_description,
                "npcs_seen": game_state.npcs_present.copy(),
                "events_seen": game_state.events.copy(),
                "search_results": [],  # Initialize search_results
            }
        }

        logger.info("Created initial game state.")
        return game_state

    @staticmethod
    def load_game_state(game_engine, user_id: str) -> Optional[GameState]:
        """
        Load game state for a user.

        Args:
            game_engine: Game engine instance
            user_id: The user's unique identifier

        Returns:
            GameState object
        """
        game_state = game_engine.load_game_state(user_id)

        if game_state:
            logger.debug(
                # Language attribute might not exist anymore
                f"Loaded game state for user {user_id[:8]}..."
            )
        else:
            logger.warning(f"No game state found for user {user_id[:8]}...")

        return game_state
