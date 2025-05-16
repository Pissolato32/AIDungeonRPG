"""
Action handlers for game actions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import random


class ActionHandler(ABC):
    """Base class for all action handlers."""

    @abstractmethod
    def handle(
            self,
            details: str,
            character: Any,
            game_state: Any) -> Dict[str, Any]:
        """Handle the action."""
        pass


class DefaultActionHandler(ActionHandler):
    """Default handler for basic game actions."""

    def handle(
            self,
            details: str,
            character: Any,
            game_state: Any) -> Dict[str, Any]:
        """Handle basic game actions."""
        action = getattr(game_state, "current_action", "unknown")

        if action == "move":
            return self._format_movement_description(details, game_state)
        elif action == "look":
            return self._generate_look_response(details, game_state)
        elif action == "search":
            return self._generate_search_response(details, game_state)
        else:
            return {
                "success": False,
                "message": "Ação não reconhecida."
            }

    def _format_movement_description(
            self,
            details: str,
            game_state: Any) -> Dict[str, Any]:
        """Format movement description based on direction."""
        details_lower = details.lower()
        direction_descriptions = {
            "norte": "ao norte",
            "sul": "ao sul",
            "leste": "a leste",
            "oeste": "a oeste",
            "frente": "à frente",
            "trás": "atrás",
        }

        for direction, description in direction_descriptions.items():
            if direction in details_lower:
                return {
                    "success": True,
                    "message": (
                        f"Você se move {description}. "
                        f"{game_state.scene_description}"
                    )
                }

        # Generic response for other movements
        return {
            "success": True,
            "message": (
                f"Você se move para {details}. "
                f"{game_state.scene_description}"
            )
        }

    def _generate_move_response(
            self,
            details: str,
            game_state: Any) -> Dict[str, Any]:
        """Generate response for move actions."""
        direction = details.lower()
        direction_map = {
            "norte": "ao norte",
            "sul": "ao sul",
            "leste": "a leste",
            "oeste": "a oeste",
            "frente": "à frente",
            "trás": "atrás",
        }

        direction_desc = direction_map.get(
            direction,
            f"em direção a {details}"
        )

        return {
            "success": True,
            "message": (
                f"Você se move {direction_desc}. "
                f"{game_state.scene_description}"
            )
        }

    def _generate_look_response(
            self,
            details: str,
            game_state: Any) -> Dict[str, Any]:
        """Generate response for look actions."""
        details_lower = details.lower()

        # Check for NPCs
        if hasattr(game_state, "npcs_present"):
            for npc in game_state.npcs_present:
                if npc.lower() in details_lower:
                    return {
                        "success": True,
                        "message": (
                            f"Você observa {npc} atentamente. "
                            "Parece ser alguém importante neste local."
                        )
                    }

        # Environment descriptions
        if "céu" in details_lower:
            return {
                "success": True,
                "message": (
                    "Você olha para o céu. Está parcialmente nublado, "
                    "com o sol entre as nuvens."
                )
            }
        elif "chão" in details_lower:
            return {
                "success": True,
                "message": (
                    "O chão é feito de pedras bem colocadas, "
                    "típicas de uma área urbana."
                )
            }

        # Generic look response
        return {
            "success": True,
            "message": (
                f"Você examina {details} cuidadosamente. "
                "Nada incomum chama sua atenção."
            )
        }

    def _generate_search_response(
            self,
            details: str,
            game_state: Any) -> Dict[str, Any]:
        """Generate response for search actions."""
        if random.random() < 0.3:  # 30% chance to find something
            items = [
                "uma moeda de cobre",
                "um pedaço de pergaminho",
                "uma pedra interessante"
            ]
            found = random.choice(items)
            return {
                "success": True,
                "message": f"Após procurar, você encontra {found}!"
            }

        return {
            "success": True,
            "message": (
                f"Você procura por {details}, "
                "mas não encontra nada interessante."
            )
        }


class AIActionHandler(ActionHandler):
    """Handler for AI-assisted actions."""

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    def handle(
            self,
            details: str,
            character: Any,
            game_state: Any) -> Dict[str, Any]:
        """Handle action using AI processing."""
        if not self.ai_client:
            return {
                "success": False,
                "message": "Ações baseadas em IA estão desativadas."
            }

        try:
            result = self.ai_client.process_player_action(
                action=game_state.current_action,
                details=details,
                character=character,
                game_state=game_state
            )

            if isinstance(result, dict):
                return result
            return {"success": True, "message": str(result)}

        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao processar ação: {str(e)}"
            }


class UnknownActionHandler(ActionHandler):
    """Handler for unknown actions."""

    def handle(
            self,
            details: str,
            character: Any,
            game_state: Any) -> Dict[str, Any]:
        """Handle unknown action."""
        return {
            "success": False,
            "message": (
                "Ação não reconhecida. "
                "Use 'ajuda' para ver comandos disponíveis."
            )
        }
