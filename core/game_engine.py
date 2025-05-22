# filepath: c:\Users\rodri\Desktop\REPLIT RPG\core\game_engine.py
"""
Game engine module for handling game state and actions."""

import json
import logging
import os
import random
from typing import Any, Dict, List, Optional, Tuple, cast  # Added Tuple

# Assume GameAIClient is in ai.game_ai_client, adjust if necessary
from ai.game_ai_client import AIResponse, GameAIClient  # Import AIResponse

# Assume ActionHandler is in core.actions, adjust if necessary
from core.actions import (
    CustomActionHandler,  # Importar para verificar se é uma instância
)
from core.actions import ActionHandler, get_action_handler
from core.models import Character
from utils.dice import calculate_attribute_modifier, roll_dice  # Importar para rolagens

from .game_state_model import GameState, LocationCoords, LocationData
from .location_generator import (  # Adicionado para geração de localização
    LocationGenerator,
)

logger = logging.getLogger(__name__)  # Configurar logger para este módulo

# Constante para o número máximo de mensagens recentes de um NPC a serem lembradas
# para evitar repetição.

MAX_NPC_HISTORY = (
    3  # Número de mensagens recentes do NPC a serem lembradas para evitar repetição
)


class GameEngine:
    """Main game engine that processes actions and manages game state."""

    def __init__(self) -> None:
        """Initialize the game engine."""
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        # _location_types foi movido para LocationGenerator

    def _get_character_save_path(self, character_id: str) -> str:
        """Helper to get the save file path for a specific character."""
        return os.path.join(self.data_dir, f"character_{character_id}.json")

    def _get_gamestate_save_path(self, character_id: str) -> str:
        """Helper to get the save file path for a specific character's game state."""
        return os.path.join(self.data_dir, f"gamestate_{character_id}.json")

    def save_character(self, character: Character) -> None:
        """Save character data to a file."""
        if not character.id:
            logger.error("Character has no ID, cannot save.")
            return
        character_data_to_save = None  # Para logging em caso de erro
        path = self._get_character_save_path(character.id)
        try:
            character_data_to_save = character.to_dict()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(character_data_to_save, f, indent=2)
            logger.info(f"Character {character.id} saved successfully to {path}")
        except (
            IOError,
            TypeError,
            ValueError,
        ) as e:  # Captura erros de I/O e serialização JSON
            logger.error(f"Error saving character {character.id} to {path}: {e}")
            if character_data_to_save is not None:
                logger.error(
                    f"Data that failed to save: {str(character_data_to_save)[:500]}..."
                )
        except Exception as e:  # Captura quaisquer outros erros inesperados
            logger.error(
                f"Unexpected error saving character {character.id} to {path}: {e}",
                exc_info=True,
            )
            if character_data_to_save is not None:
                logger.error(
                    f"Data that failed to save (unexpected error): {str(character_data_to_save)[:500]}..."
                )

    def load_character(self, character_id: str) -> Optional[Character]:
        """Load character data from a file."""
        path = self._get_character_save_path(character_id)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if not content:
                        logger.error(f"Character file {character_id} is empty.")
                        return None
                    data = json.loads(content)
                    character = Character.from_dict(data)
                    return character
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Error loading character {character_id}: {e}")
        return None

    def delete_character(self, character_id: str) -> None:
        """Delete character data file."""
        path = self._get_character_save_path(character_id)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError as e:
                logger.error(f"Error deleting character file {character_id}: {e}")

    def get_characters_by_owner(self, owner_session_id: str) -> List[Character]:
        """Load all characters belonging to a specific owner_session_id."""
        characters: List[Character] = []
        if not os.path.exists(self.data_dir):
            return characters

        for filename in os.listdir(self.data_dir):
            if filename.startswith("character_") and filename.endswith(".json"):
                character_id_from_file = filename[len("character_") : -len(".json")]
                char = self.load_character(character_id_from_file)
                if char and char.owner_session_id == owner_session_id:
                    characters.append(char)
        return characters

    def save_game_state(self, character_id: str, game_state: GameState) -> None:
        """Save game state data to a file."""
        path = self._get_gamestate_save_path(character_id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(game_state.to_dict(), f, indent=2)
        except IOError as e:
            logger.error(f"Error saving game state for character {character_id}: {e}")

    def load_game_state(self, character_id: str) -> Optional[GameState]:
        """Load game state data from a file."""
        path = self._get_gamestate_save_path(character_id)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return GameState.from_dict(data)
            except (IOError, json.JSONDecodeError) as e:
                logger.error(
                    f"Error loading game state for character {character_id}: {e}"
                )
        return None

    def delete_game_state(self, character_id: str) -> None:
        """Delete game state data file."""
        path = self._get_gamestate_save_path(character_id)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError as e:
                logger.error(
                    f"Error deleting game state file for character {character_id}: {e}"
                )

    def _handle_survival_updates(
        self, character: Character, action: str, game_state: GameState
    ) -> str:
        """
        Handles survival system updates and returns a message part for AI narration.
        """
        try:
            # Import local para flexibilidade, caso o sistema de sobrevivência seja opcional.
            from core.survival_system import SurvivalManager as SurvivalSystem

            survival = SurvivalSystem()
            survival_result = survival.update_stats(character, action)
            if survival_result.get("messages"):
                for msg in survival_result[
                    "messages"
                ]:  # Estas são mensagens de sistema/evento
                    game_state.add_message(role="system", content=msg)
                # Retorna a primeira mensagem para concatenação na narração da IA
                return f" ({survival_result['messages'][0]})"
            return ""
        except ImportError:
            logger.warning("SurvivalSystem not found, skipping survival status update.")
            return " (Survival system unavailable)"
        except Exception as e:
            logger.error(f"Error processing SurvivalSystem: {e}", exc_info=True)
            return " (Error in survival system)"

    def _process_npc_repetition(
        self,
        ai_message_content: Optional[str],
        npc_name: Optional[str],
        game_state: GameState,
    ) -> Tuple[Optional[str], bool]:
        """
        Checks for NPC message repetition and updates NPC message history.
        Returns the (potentially modified) message and a boolean indicating if it was a repetition.
        """
        if not ai_message_content or not npc_name:
            return ai_message_content, False

        is_repetition = False
        history = game_state.npc_message_history.get(npc_name, [])

        # Normalize messages for comparison (simple strip and lower for now)
        normalized_ai_message = ai_message_content.strip().lower()

        # Check for exact or very similar repetition (can be made more sophisticated)
        # For now, we check if the stripped message is in the stripped history.
        if any(normalized_ai_message == msg.strip().lower() for msg in history):
            is_repetition = True
            logger.warning(
                f"[Repetição Detectada] NPC '{npc_name}' tentou repetir: {ai_message_content}"
            )
            # Modify message to indicate repetition
            # ai_message_content = f"{npc_name} parece se repetir, reafirmando o que já disse."
            # Ou, para um efeito mais sutil, podemos apenas logar e deixar o prompt da IA tentar lidar com isso.
            # Por enquanto, vamos apenas logar e retornar a mensagem original, confiando no prompt.
            # Se a repetição persistir, podemos ativar a modificação da mensagem aqui.

        # Update history
        if npc_name not in game_state.npc_message_history:
            game_state.npc_message_history[npc_name] = []

        game_state.npc_message_history[npc_name].append(
            ai_message_content
        )  # Store original for more accurate future checks
        if len(game_state.npc_message_history[npc_name]) > MAX_NPC_HISTORY:
            game_state.npc_message_history[npc_name].pop(0)

        return ai_message_content, is_repetition

    def _determine_npc_for_repetition_check(
        self, action_for_ai: str, message_for_ai_narration: str, game_state: GameState
    ) -> Optional[str]:
        """Determines the NPC name for message repetition history based on action and context."""
        if action_for_ai.lower() == "talk":
            potential_npc_name = message_for_ai_narration.strip()
            if (
                potential_npc_name in game_state.known_npcs
                or potential_npc_name in game_state.npcs_present
            ):
                return potential_npc_name
        return None

    def _process_suggested_roll(
        self,
        current_ai_response: AIResponse,
        character: Character,
        game_state: GameState,
        ai_client: GameAIClient,
    ) -> Optional[AIResponse]:
        """Processes a suggested roll from the AI, narrates it, and returns the updated AI response."""
        roll_suggestion_data = current_ai_response.get("suggested_roll")
        if not isinstance(roll_suggestion_data, dict) or not roll_suggestion_data:
            logger.debug(  # Changed to debug as this can be a normal case if no roll is suggested
                "Suggested_roll was present but not a valid dictionary or was empty."
            )
            return current_ai_response

        attribute_to_check = roll_suggestion_data.get("attribute", "intelligence")
        dc = roll_suggestion_data.get("dc", 15)
        roll_description = roll_suggestion_data.get(
            "description", "a challenging action"
        )

        # Corrigido: Buscar o atributo em character.stats
        # Usar getattr para buscar dinamicamente o atributo de character.stats
        attribute_score = getattr(character.stats, attribute_to_check, 10)
        modifier = calculate_attribute_modifier(attribute_score)

        roll_result_obj = roll_dice(1, 20, modifier)
        roll_total = roll_result_obj["total"]
        roll_succeeded = roll_total >= dc

        mechanical_roll_outcome_msg = (
            f"Attempt for '{roll_description}'. "
            f"{attribute_to_check.capitalize()} check (Roll: {roll_total} vs DC {dc}). "
            f"{'Success!' if roll_succeeded else 'Failure!'}"
            f" Roll details: {roll_result_obj.get('result_string', '')}"
        )
        game_state.add_message(role="system", content=mechanical_roll_outcome_msg)

        ai_response_narrated_roll: Optional[AIResponse] = ai_client.process_action(
            action="narrate_roll_outcome",
            details=mechanical_roll_outcome_msg,
            character=character,
            game_state=game_state,
        )

        if ai_response_narrated_roll is None:
            logger.error(
                "CRITICAL: AI (narrate_roll_outcome) returned None. Narration failed. Using pre-roll AI message."
            )
            return current_ai_response
        elif not ai_response_narrated_roll.get("success"):
            logger.warning(
                f"AI failed to narrate roll outcome: {ai_response_narrated_roll.get('message')}. Using pre-roll AI message."
            )
            if ai_response_narrated_roll.get("message"):
                game_state.add_message(
                    role="system",
                    content=f"AI narration error for roll: {ai_response_narrated_roll.get('message')}",
                )
            return current_ai_response
        else:
            return ai_response_narrated_roll

    def _handle_ai_interaction(
        self,
        action_for_ai: str,
        message_for_ai_narration: str,
        character: Character,
        game_state: GameState,
        ai_client: Optional[GameAIClient],
        result_from_handler: Dict[str, Any],
        actual_handler: ActionHandler,
    ) -> Dict[str, Any]:
        """Handles the interaction with the AI, including narration and suggested rolls."""
        if ai_client is None:
            logger.warning("AI client not provided, skipping AI interaction.")
            result_from_handler["message"] = (
                result_from_handler.get("message", "")
                + " (AI interaction skipped: client not available)"
            )
            return result_from_handler

        try:
            current_ai_response: Optional[AIResponse] = ai_client.process_action(
                action=action_for_ai,
                details=message_for_ai_narration,
                character=character,
                game_state=game_state,
            )

            if current_ai_response is None:
                logger.critical("CRITICAL: AI process_action returned None.")
                result_from_handler["message"] = "Critical AI communication error."
                result_from_handler["success"] = False
                return result_from_handler

            if current_ai_response.get("success"):
                self._apply_ai_updates_to_gamestate(
                    current_ai_response, game_state, action_for_ai
                )

                if current_ai_response.get("suggested_roll") and isinstance(
                    actual_handler, CustomActionHandler
                ):
                    updated_response_after_roll = self._process_suggested_roll(
                        current_ai_response, character, game_state, ai_client
                    )
                    if (
                        updated_response_after_roll is None
                    ):  # Erro crítico no processamento do roll
                        result_from_handler["message"] = (
                            result_from_handler.get("message", "")
                            + " (AI error after suggested roll)"
                        )
                        result_from_handler["success"] = False
                        return result_from_handler
                    current_ai_response = updated_response_after_roll

                original_ai_message_content = current_ai_response.get("message")
                npc_name_for_history = self._determine_npc_for_repetition_check(
                    action_for_ai, message_for_ai_narration, game_state
                )
                processed_message_content, _ = self._process_npc_repetition(
                    original_ai_message_content, npc_name_for_history, game_state
                )

                final_ai_message = (
                    processed_message_content
                    if processed_message_content is not None
                    else original_ai_message_content
                )

                if final_ai_message:
                    current_ai_response["message"] = final_ai_message
                    game_state.add_message(role="assistant", content=final_ai_message)
                elif (
                    original_ai_message_content is None
                ):  # Apenas loga se a msg original já era None
                    logger.warning(
                        "AI response was successful but no message content found."
                    )

                if not current_ai_response.get("message") and message_for_ai_narration:
                    current_ai_response["message"] = message_for_ai_narration

                final_result = cast(Dict[str, Any], current_ai_response.copy())
                for key, value in result_from_handler.items():
                    if key not in final_result:
                        final_result[key] = value
                final_result["success"] = current_ai_response.get("success", False)
                return final_result
            else:  # Falha da IA
                logger.warning(
                    f"AI processing failed or returned success=false. AI Response: {current_ai_response}"
                )
                fallback_message = current_ai_response.get(
                    "message"
                ) or result_from_handler.get("message", "Error processing with AI.")
                result_from_handler["message"] = fallback_message
                result_from_handler["success"] = False
                return result_from_handler
        except Exception as e:  # Captura outras exceções da interação com IA
            logger.error(f"Error during AI interaction: {e}", exc_info=True)
            result_from_handler["message"] = (
                result_from_handler.get("message", "") + f" (AI Error: {e})"
            )
            result_from_handler["success"] = False
            return result_from_handler

    def _apply_ai_updates_to_gamestate(
        self, ai_response: AIResponse, game_state: GameState, action_for_ai: str
    ) -> None:
        """
        Applies updates from the AIResponse to the GameState.
        This includes location, scene description, and potentially NPCs/events if
        the AI is empowered to suggest them directly.
        """
        # Apenas atualize a localização a partir da IA se a ação NÃO foi uma ação de 'move'.
        # Para 'move', o handler já definiu a localização correta.
        new_detailed_location = ai_response.get("current_detailed_location")

        if new_detailed_location and action_for_ai.lower() != "move":
            # A lógica de _update_location já existe e é mais completa,
            # precisamos de uma forma de mapear nome para ID ou atualizar diretamente.
            # Por enquanto, vamos atualizar os campos diretos do game_state.
            # Idealmente, a IA retornaria um location_id ou o GameEngine
            # resolveria o nome para um ID.
            if game_state.current_location != new_detailed_location:
                logger.info(
                    f"AI updated location from '{game_state.current_location}' to '{new_detailed_location}'"
                )
                game_state.current_location = new_detailed_location

        # Sempre atualize a descrição da cena a partir da IA, se fornecida
        # A descrição da IA é a descrição narrativa da cena,
        # que é seu papel principal após um movimento.
        # Isso NÃO deve ser pulado para ações de 'move'.

        new_scene_description = ai_response.get("scene_description_update")
        if new_scene_description:
            game_state.scene_description = new_scene_description

    def _update_location(self, game_state: GameState, new_location: str) -> None:
        if new_location in game_state.discovered_locations:
            loc_data = game_state.discovered_locations[new_location]
            game_state.location_id = new_location
            game_state.current_location = loc_data.get("name", "Local Desconhecido")
            game_state.scene_description = loc_data.get(
                "description", "Uma área misteriosa."
            )
            game_state.coordinates = loc_data.get(
                "coordinates", {"x": 0, "y": 0, "z": 0}
            )
            game_state.npcs_present = loc_data.get("npcs", [])
            game_state.events = loc_data.get("events", [])
            if not loc_data.get("visited"):
                loc_data["visited"] = True
        else:
            logger.warning(
                f"Tentativa de atualizar para localização desconhecida (ID): {new_location}"
            )

    def _get_new_coordinates(self, game_state: GameState) -> LocationCoords:
        current = game_state.coordinates
        x, y, z = (
            current.get("x", 0),
            current.get("y", 0),
            current.get("z", 0),
        )
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)
        for dx, dy in directions:
            new_x, new_y = x + dx, y + dy
            if self._is_valid_location(new_x, new_y, z, game_state):
                return {"x": new_x, "y": new_y, "z": z}
        for _ in range(10):
            rand_dx = random.choice([-2, -1, 1, 2])
            rand_dy = random.choice([-2, -1, 1, 2])
            if rand_dx == 0 and rand_dy == 0:
                continue
            new_x, new_y = x + rand_dx, y + rand_dy
            if self._is_valid_location(new_x, new_y, z, game_state):
                return {"x": new_x, "y": new_y, "z": z}
        return {"x": x + 1, "y": y, "z": z}

    @staticmethod
    def _is_valid_location(x: int, y: int, z: int, game_state: GameState) -> bool:
        for loc_data in game_state.discovered_locations.values():
            coords = loc_data.get("coordinates")
            if (
                coords
                and coords.get("x") == x
                and coords.get("y") == y
                and coords.get("z") == z
            ):
                return False
        return True

    @staticmethod
    def _get_direction(
        from_coords: LocationCoords, to_coords: LocationCoords
    ) -> Optional[str]:
        dx = to_coords.get("x", 0) - from_coords.get("x", 0)
        dy = to_coords.get("y", 0) - from_coords.get("y", 0)
        if abs(dx) > abs(dy):
            return "leste" if dx > 0 else "oeste"
        if dy != 0:
            return "norte" if dy > 0 else "sul"
        return None

    @staticmethod
    def _opposite_direction(direction: str) -> str:
        opposites = {
            "norte": "sul",
            "sul": "norte",
            "leste": "oeste",
            "oeste": "leste",
        }
        return opposites.get(direction, direction)

    def _generate_location(
        self, game_state: GameState, result_from_handler: Dict[str, Any]
    ) -> None:
        new_location_id = game_state.location_id
        if (
            not new_location_id or new_location_id in game_state.discovered_locations
        ):  # ID deve ser novo
            logger.warning(
                f"Attempt to generate location with invalid or existing ID: {new_location_id}"
            )
            return

        location_type_suggestion = result_from_handler.get(
            "location_type", "ruina_urbana"
        )
        name_suggestion = result_from_handler.get("new_location_name")
        description_suggestion = result_from_handler.get("new_location_description")

        # Usa LocationGenerator para criar os dados da localização.
        # game_state é passado para que LocationGenerator possa adicionar NPCs a game_state.known_npcs.
        location_data = LocationGenerator.generate_new_location_data(
            location_id=new_location_id,
            game_state=game_state,
            location_type_suggestion=location_type_suggestion,
            name_suggestion=name_suggestion,
            description_suggestion=description_suggestion,
        )

        # GameEngine define coordenadas e lida com conexões
        new_coords = self._get_new_coordinates(game_state)
        location_data["coordinates"] = new_coords

        game_state.discovered_locations[new_location_id] = location_data

        # Safely access 'name' and 'description' from location_data
        game_state.current_location = location_data.get("name", "Local Desconhecido")
        game_state.scene_description = location_data.get(
            "description", "Uma área misteriosa."
        )
        game_state.coordinates = new_coords
        game_state.npcs_present = location_data.get("npcs", [])
        game_state.events = location_data.get("events", [])

        self._handle_connections(game_state, new_location_id, new_coords)

    def _handle_connections(
        self, game_state: GameState, location_id: str, coords: LocationCoords
    ) -> None:
        """
        Placeholder for handling connections between locations.
        This method should be implemented to establish or update connections
        when a new location is generated or an existing one is modified.
        """
        logger.warning(
            f"_handle_connections called for location {location_id} at {coords}, but it's not fully implemented."
        )
        # TODO: Implement logic to create/update connections in game_state.world_map
        # based on the new location and its coordinates, potentially linking it
        # to nearby existing locations.
