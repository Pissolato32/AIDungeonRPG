# filepath: c:\Users\rodri\Desktop\REPLIT RPG\core\game_engine.py
"""
Game engine module for handling game state and actions."""

import json
import logging
import os
import random
from typing import Any, Dict, List, Optional, Tuple  # Added Tuple, removed cast

# Assume GameAIClient is in ai.game_ai_client, adjust if necessary
from ai.game_ai_client import GameAIClient
from ai.schemas import AIResponsePydantic  # Importar o schema Pydantic

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

MAX_NPC_HISTORY = 3

ACTION_DETAIL_KEYS_FOR_INTERPRETATION = {
    "move": "direction",
    "talk": "target_npc",
    "use_item": "item_name",
    # Adicione outras ações e suas chaves de detalhes específicas aqui
}


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
            ValueError,  # type: ignore
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
                    logger.info(f"Character {character_id} loaded successfully.")
                    return character
            except (
                IOError,
                json.JSONDecodeError,
                TypeError,
                ValueError,
            ) as e:  # Added TypeError, ValueError
                logger.error(
                    f"Error loading or parsing character {character_id}: {e}",
                    exc_info=True,
                )
            except Exception as e:  # Captura quaisquer outros erros inesperados
                logger.error(
                    f"Unexpected error loading character {character_id}: {e}",
                    exc_info=True,
                )
        return None

    def delete_character(self, character_id: str) -> None:
        """Delete character data file."""
        path = self._get_character_save_path(character_id)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError as e:
                logger.error(
                    f"Error deleting character file {character_id}: {e}", exc_info=True
                )

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
        game_state_data_to_save = None  # For logging in case of error
        try:
            game_state_data_to_save = game_state.to_dict()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(game_state_data_to_save, f, indent=2)
            logger.info(f"Game state for {character_id} saved successfully to {path}")
        except (
            IOError,
            TypeError,
            ValueError,  # type: ignore
        ) as e:  # Captura erros de I/O e serialização JSON
            logger.error(
                f"Error saving game state for character {character_id} to {path}: {e}"
            )
            if game_state_data_to_save is not None:
                logger.error(
                    f"Game state data that failed to save: {str(game_state_data_to_save)[:500]}..."
                )
        except Exception as e:  # Captura quaisquer outros erros inesperados
            logger.error(
                f"Unexpected error saving game state for {character_id} to {path}: {e}",
                exc_info=True,
            )
            if game_state_data_to_save is not None:
                logger.error(
                    f"Game state data that failed to save (unexpected error): {str(game_state_data_to_save)[:500]}..."
                )

    def load_game_state(self, character_id: str) -> Optional[GameState]:
        """Load game state data from a file."""
        path = self._get_gamestate_save_path(character_id)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    gs = GameState.from_dict(data)
                    logger.info(
                        f"Game state for character {character_id} loaded successfully."
                    )
                    return gs
            except (
                IOError,
                json.JSONDecodeError,
                TypeError,
                ValueError,
            ) as e:  # Added TypeError, ValueError
                logger.error(
                    f"Error loading or parsing game state for character {character_id}: {e}",
                    exc_info=True,
                )
            except Exception as e:  # Captura quaisquer outros erros inesperados
                logger.error(
                    f"Unexpected error loading game state for {character_id}: {e}",
                    exc_info=True,
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
                    f"Error deleting game state file for {character_id}: {e}",
                    exc_info=True,
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
        self,
        action_for_ai: str,
        handler_result_dict: Dict[str, Any],
        game_state: GameState,
    ) -> Optional[str]:
        """Determines the NPC name for message repetition history based on action and context."""
        # Se a ação envolveu um NPC falando, o mechanical_handler_result deve indicar o NPC.
        # Isso depende dos ActionHandlers (como TalkHandler) fornecerem "npc_name" em seu resultado.
        # This method is called *after* the mechanical handler, so its result is available. # type: ignore
        npc_name = handler_result_dict.get("npc_name", None)  # type: ignore
        if npc_name and isinstance(npc_name, str):
            # Validação adicional: este NPC é conhecido ou está presente?
            logger.debug(
                f"NPC identified for repetition check: {npc_name} from handler result for action {action_for_ai}"  # type: ignore # type: ignore
            )
            return npc_name
        else:
            logger.debug(
                f"NPC '{npc_name}' from handler result for action {action_for_ai} not in known_npcs or npcs_present."  # type: ignore # type: ignore
            )
        return None  # NPC name provided but not recognized in current context

    def _process_suggested_roll(
        self,
        current_ai_response: AIResponsePydantic,
        character: Character,
        game_state: GameState,
        ai_client: GameAIClient,
    ) -> Optional[AIResponsePydantic]:
        """Processes a suggested roll from the AI, narrates it, and returns the updated AI response."""
        suggested_roll_data = current_ai_response.suggested_roll
        if not suggested_roll_data:
            logger.debug("No suggested_roll data found in AI response or it was empty.")
            return current_ai_response

        # Access attributes directly from the Pydantic model
        attribute_to_check = suggested_roll_data.attribute
        dc = suggested_roll_data.dc
        roll_description = suggested_roll_data.description

        # Buscar o atributo em character.stats
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

        ai_response_narrated_roll: AIResponsePydantic = ai_client.process_action(
            action="narrate_roll_outcome",
            details=mechanical_roll_outcome_msg,
            character=character,
            game_state=game_state,
        )

        if ai_response_narrated_roll is None:
            # This case should ideally not happen if ai_client.process_action always returns AIResponsePydantic
            logger.error(
                "CRITICAL: AI (narrate_roll_outcome) returned None. Narration failed. Using pre-roll AI message."
            )
            return current_ai_response
        elif not ai_response_narrated_roll.success:
            logger.warning(
                f"AI failed to narrate roll outcome: {ai_response_narrated_roll.message}. Using pre-roll AI message."
            )
            if ai_response_narrated_roll.message:
                game_state.add_message(
                    role="system",
                    content=f"AI narration error for roll: {ai_response_narrated_roll.message}",
                )
            return current_ai_response
        else:
            return ai_response_narrated_roll

    def _apply_ai_updates_to_gamestate(
        self, ai_response: AIResponsePydantic, game_state: GameState, action_for_ai: str
    ) -> None:
        """
        Applies updates from the AIResponse to the GameState.
        This includes location, scene description, and potentially NPCs/events if
        the AI is empowered to suggest them directly.
        """
        # Apenas atualize a localização a partir da IA se a ação NÃO foi uma ação de 'move'.
        # Para 'move', o handler já definiu a localização correta.
        new_detailed_location = ai_response.current_detailed_location

        # Se a ação mecânica foi 'move', o MoveActionHandler já atualizou
        # current_location e scene_description no game_state.
        # A IA deve apenas narrar a chegada.
        # Se a IA, mesmo para uma ação de 'move', retornar um current_detailed_location
        # diferente do que o handler definiu, isso pode ser um problema de prompt ou IA.
        # Por enquanto, vamos confiar que se action_for_ai foi 'move', o game_state está correto.
        if (
            new_detailed_location
            and action_for_ai.lower() != "move"
            and game_state.current_location != new_detailed_location
        ):
            # A lógica de _update_location já existe e é mais completa,
            # precisamos de uma forma de mapear nome para ID ou atualizar diretamente.
            # Por enquanto, vamos atualizar os campos diretos do game_state.
            if game_state.current_location != new_detailed_location:
                logger.info(
                    f"AI updated location from '{game_state.current_location}' to '{new_detailed_location}'"
                )
                game_state.current_location = new_detailed_location

        # Sempre atualize a descrição da cena a partir da IA, se fornecida
        # No entanto, se a ação foi 'move', o MoveActionHandler já deve ter
        # definido a descrição da *nova* cena. A IA deve apenas narrar.
        # Se a IA fornecer uma scene_description_update, ela sobrescreverá.
        # Isso pode ser desejável se a IA adicionar detalhes dinâmicos à descrição base.
        # Se a ação mecânica foi 'move', a descrição da cena já foi definida pelo MoveActionHandler.
        # A IA deve apenas narrar a chegada. Não devemos sobrescrever a descrição do novo local
        # com uma descrição da IA que pode ser do local antigo.
        if action_for_ai.lower() != "move":
            new_scene_description = ai_response.scene_description_update
            if (
                new_scene_description
                and game_state.scene_description != new_scene_description
            ):
                game_state.scene_description = new_scene_description
                logger.info(f"AI updated scene description for non-move action.")

        # Validar e aplicar interactable_elements
        ai_interactables = ai_response.interactable_elements
        if isinstance(ai_interactables, list):
            logger.info(f"AI suggested interactable elements: {ai_interactables}")
            game_state.current_scene_interactables = ai_interactables
        elif ai_interactables is not None:  # Se não for lista mas também não for None
            logger.warning(
                f"AI provided interactable_elements in an unexpected format: {type(ai_interactables)}. Expected list."
            )

        # Processar novos fatos para memória longa, se fornecidos pela IA
        new_facts_from_ai = ai_response.new_facts
        if isinstance(new_facts_from_ai, dict) and new_facts_from_ai:
            if (
                not hasattr(game_state, "long_term_memory")
                or game_state.long_term_memory is None
            ):
                game_state.long_term_memory = (
                    {}
                )  # Garantir que o atributo exista e seja um dict

            # Atualiza/adiciona as chaves. Pode precisar de lógica mais sofisticada no futuro
            # (ex: evitar sobrescrever fatos importantes, versionamento).
            for key, value in new_facts_from_ai.items():
                game_state.long_term_memory[key] = value
            logger.info(
                f"AI provided new facts for long term memory: {new_facts_from_ai}"
            )

    def _update_location(self, game_state: GameState, new_location_id: str) -> None:
        """
        Updates the game state to reflect moving to a new location.
        This method assumes new_location_id is a valid key in game_state.world_map
        or game_state.discovered_locations.
        It also updates game_state.occupied_coordinates if the location is newly "discovered"
        or if its data implies a new coordinate.
        """
        loc_data = game_state.world_map.get(new_location_id)
        if not loc_data:
            loc_data = game_state.discovered_locations.get(new_location_id)

        if loc_data:
            game_state.location_id = new_location_id
            game_state.current_location = loc_data.get("name", "Local Desconhecido")
            game_state.scene_description = loc_data.get(
                "description", "Uma área misteriosa."
            )
            new_coords_dict = loc_data.get("coordinates")
            if new_coords_dict:
                game_state.coordinates = new_coords_dict
                # Atualizar occupied_coordinates se esta localização não estava lá ou se as coordenadas mudaram
                # (embora as coordenadas de uma localização existente não devam mudar frequentemente)
                coord_tuple = (
                    new_coords_dict.get("x", 0),
                    new_coords_dict.get("y", 0),
                    new_coords_dict.get("z", 0),
                )
                if coord_tuple not in game_state.occupied_coordinates:
                    game_state.occupied_coordinates.add(coord_tuple)
                    logger.debug(
                        f"Added {coord_tuple} to occupied_coordinates via _update_location."
                    )

            game_state.npcs_present = loc_data.get("npcs", [])
            game_state.events = loc_data.get("events", [])

            if not loc_data.get("visited"):
                loc_data["visited"] = True
                # Se for a primeira visita, garantir que esteja em discovered_locations
                if new_location_id not in game_state.discovered_locations:
                    game_state.discover_location(new_location_id, loc_data)
        else:
            logger.warning(
                f"Tentativa de atualizar para localização desconhecida (ID): {new_location_id}"
            )

    def _get_new_coordinates(self, game_state: GameState) -> LocationCoords:
        current = game_state.coordinates
        x, y, z = (
            current.get("x", 0),
            current.get("y", 0),
            current.get("z", 0),
        )
        directions = [(0, 1, 0), (1, 0, 0), (0, -1, 0), (-1, 0, 0)]  # dx, dy, dz
        random.shuffle(directions)
        for dx, dy, dz_offset in directions:  # dz_offset é sempre 0 por enquanto
            new_x, new_y, new_z = x + dx, y + dy, z + dz_offset
            if self._is_valid_location(new_x, new_y, new_z, game_state):
                return {"x": new_x, "y": new_y, "z": new_z}

        # Fallback: Tentar coordenadas mais distantes se as adjacentes estiverem ocupadas
        for _ in range(10):  # Tentar algumas vezes
            rand_dx = random.choice([-2, -1, 1, 2])
            rand_dy = random.choice([-2, -1, 1, 2])
            # rand_dz = random.choice([-1, 0, 1]) # Se movimento 3D for mais complexo
            if rand_dx == 0 and rand_dy == 0:  # Evitar ficar no mesmo lugar
                continue
            new_x, new_y, new_z = x + rand_dx, y + rand_dy, z  # Mantendo z por enquanto
            if self._is_valid_location(new_x, new_y, new_z, game_state):
                return {"x": new_x, "y": new_y, "z": new_z}

        # Último fallback: apenas mover para uma direção padrão se tudo falhar
        # (isso pode indicar um mapa muito cheio ou lógica de _is_valid_location precisando de ajuste)
        logger.warning(
            f"Could not find a valid new coordinate near ({x},{y},{z}) after several attempts. Defaulting to x+1."
        )
        return {"x": x + 1, "y": y, "z": z}

    @staticmethod
    def _is_valid_location(x: int, y: int, z: int, game_state: GameState) -> bool:
        """Checks if the given coordinates are already occupied."""
        # A verificação agora usa o conjunto otimizado em GameState.
        # logger.debug(f"Checking validity for ({x},{y},{z}). Occupied: {game_state.occupied_coordinates}")
        return (x, y, z) not in game_state.occupied_coordinates

    @staticmethod
    def _get_direction(
        from_coords: LocationCoords, to_coords: LocationCoords
    ) -> Optional[str]:
        dx = to_coords.get("x", 0) - from_coords.get("x", 0)
        dy = to_coords.get("y", 0) - from_coords.get("y", 0)
        # dz = to_coords.get("z", 0) - from_coords.get("z", 0) # Para movimento 3D

        # Priorizar movimento no plano XY por enquanto
        if abs(dx) > abs(dy):
            return "leste" if dx > 0 else "oeste"
        if dy != 0:  # dy pode ser 0 se o movimento for apenas em x
            return "norte" if dy > 0 else "sul"
        # Adicionar lógica para 'cima'/'baixo' se dz for significativo
        # if abs(dz) > abs(dx) and abs(dz) > abs(dy):
        # return "cima" if dz > 0 else "baixo"
        return None

    @staticmethod
    def _opposite_direction(direction: str) -> str:
        opposites = {
            "norte": "sul",
            "sul": "norte",
            "leste": "oeste",
            "oeste": "leste",
            "cima": "baixo",
            "baixo": "cima",
        }
        return opposites.get(direction.lower(), direction)  # .lower() para robustez

    def _generate_location(
        self, game_state: GameState, result_from_handler: Dict[str, Any]
    ) -> None:
        """
        Generates a new location, adds it to the game state, and updates occupied coordinates.
        The new location_id is expected to be set in game_state.location_id by the caller
        or determined here if not provided.
        """
        new_location_id = (
            game_state.location_id
        )  # Assumindo que o handler de movimento definiu isso
        if not new_location_id:
            # Gerar um ID único se não foi fornecido (improvável para 'move', mas para segurança)
            new_location_id = f"loc_{random.randint(10000, 99999)}"
            while (
                new_location_id in game_state.world_map
                or new_location_id in game_state.discovered_locations
            ):
                new_location_id = f"loc_{random.randint(10000, 99999)}"
            game_state.location_id = (
                new_location_id  # Definir no game_state para consistência
            )

        if (
            new_location_id in game_state.discovered_locations
            or new_location_id in game_state.world_map
        ):
            logger.warning(
                f"Attempt to generate location with existing ID: {new_location_id}. This should be a new, undiscovered location."
            )
            # Se já existe, _update_location deveria ter sido chamado pelo handler.
            # Não deveríamos estar aqui para um ID existente.
            return

        location_type_suggestion = result_from_handler.get(
            "location_type", "ruina_urbana"
        )
        name_suggestion = result_from_handler.get("new_location_name")
        description_suggestion = result_from_handler.get("new_location_description")

        # Usa LocationGenerator para criar os dados da localização.
        location_data = LocationGenerator.generate_new_location_data(
            location_id=new_location_id,
            game_state=game_state,  # Passado para que NPCs possam ser adicionados a known_npcs
            location_type_suggestion=location_type_suggestion,
            name_suggestion=name_suggestion,
            description_suggestion=description_suggestion,
        )

        # GameEngine define coordenadas e lida com conexões
        new_coords = self._get_new_coordinates(
            game_state
        )  # Encontra coordenadas válidas
        location_data["coordinates"] = new_coords
        location_data["visited"] = True  # Ao gerar, o jogador está visitando

        # Adicionar a nova localização ao GameState usando o método que atualiza occupied_coordinates
        game_state.discover_location(new_location_id, location_data)
        # discover_location já adiciona a discovered_locations, world_map (se não existir) e occupied_coordinates.

        # Atualizar o estado atual do jogo para refletir a nova localização
        game_state.current_location = location_data.get("name", "Local Desconhecido")
        game_state.scene_description = location_data.get(
            "description", "Uma área misteriosa."
        )
        game_state.coordinates = new_coords
        game_state.npcs_present = location_data.get("npcs", [])
        game_state.events = location_data.get("events", [])

        # Lidar com conexões (ex: conectar esta nova localização à anterior)
        # O handler de movimento (MoveActionHandler) deve ter o ID da localização anterior.
        previous_location_id = result_from_handler.get("previous_location_id")
        direction_of_travel = result_from_handler.get("direction_moved")

        if previous_location_id and direction_of_travel:
            # Conectar nova localização de volta à anterior
            opposite_dir = self._opposite_direction(direction_of_travel)
            if "connections" not in location_data:
                location_data["connections"] = {}
            location_data["connections"][opposite_dir] = previous_location_id

            # Conectar localização anterior à nova
            prev_loc_data = game_state.world_map.get(
                previous_location_id
            ) or game_state.discovered_locations.get(previous_location_id)
            if prev_loc_data:
                if "connections" not in prev_loc_data:
                    prev_loc_data["connections"] = {}
                prev_loc_data["connections"][direction_of_travel] = new_location_id
            else:
                logger.warning(
                    f"Could not find previous location data for ID: {previous_location_id} to update connections."
                )
        else:
            logger.warning(
                f"Missing previous_location_id or direction_of_travel in handler result for _generate_location. Connections might be incomplete."
            )

        logger.info(
            f"Generated new location '{location_data.get('name')}' (ID: {new_location_id}) at {new_coords}"
        )

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

    def _handle_ai_interaction(
        self,
        action_type_for_ai: str,  # Ex: "talk_result", "examine_npc_response", "interpret_needed"
        text_input_for_ai: str,  # The text/message for the AI to process/narrate
        character: Character,
        game_state: GameState,
        ai_client: Optional[GameAIClient],
        # Full dictionary result from the preceding mechanical action handler or a dummy dict for initial interpretation.
        source_mechanical_handler_result: Dict[str, Any],
        actual_handler: Optional[ActionHandler] = None,
    ) -> AIResponsePydantic:
        """
        Handles the interaction with the AI client, processes its response,
        and updates the game state accordingly.
        """
        if not ai_client:
            logger.warning(
                "AI client is not available. Returning a basic success response without AI narration."
            )
            # Retornar uma resposta Pydantic básica indicando sucesso mecânico, mas sem narração da IA.
            return AIResponsePydantic(
                success=True,
                message=source_mechanical_handler_result.get(
                    "message", "Ação processada."
                ),  # Mensagem do handler mecânico
                current_detailed_location=game_state.current_location,
                scene_description_update=game_state.scene_description,
                details={"warning": "AI client not available for narration"},
                interpreted_action_type=action_type_for_ai,
            )

        # Lógica de sobrevivência (se aplicável antes da chamada da IA)
        # survival_message_part = self._handle_survival_updates(character, action_for_ai, game_state)
        # message_for_ai_with_survival = f"{message_for_ai_narration}{survival_message_part}"
        # Nota: A lógica de sobrevivência pode ser melhor integrada dependendo se afeta o prompt da IA
        # ou se é apenas uma mensagem de sistema. Por ora, vamos manter como estava,
        # mas é um ponto a se considerar.

        # Chamar a IA para narrar o resultado da ação mecânica
        current_ai_response: AIResponsePydantic = ai_client.process_action(
            action=action_type_for_ai,
            details=text_input_for_ai,  # Pass the string directly
            character=character,
            game_state=game_state,
        )

        if not current_ai_response.success:
            logger.warning(
                f"AI narration failed for action '{action_type_for_ai}'. AI Response: {current_ai_response.message}"
            )
            # Mesmo que a narração da IA falhe, a ação mecânica pode ter sido um sucesso.
            # Retornamos a resposta da IA que indica a falha na narração.
            # O GameState já foi modificado pelo handler mecânico.
            # Adicionamos a mensagem do handler mecânico aos detalhes se não estiver lá.
            if "original_handler_message" not in current_ai_response.details:
                current_ai_response.details["original_handler_message"] = (
                    text_input_for_ai  # Or more contextually, the message from source_mechanical_handler_result if available
                )
            return current_ai_response

        # Processar sugestão de rolagem de dados, se houver
        # _process_suggested_roll pode retornar uma nova AIResponsePydantic com a narração da rolagem
        ai_response_after_roll = self._process_suggested_roll(
            current_ai_response, character, game_state, ai_client
        )
        # Se _process_suggested_roll retornou uma nova resposta (após narrar a rolagem), use-a.
        # Caso contrário (sem rolagem ou falha na narração da rolagem), continue com current_ai_response.
        final_ai_response = ai_response_after_roll or current_ai_response

        # Aplicar atualizações da IA ao GameState (localização, descrição da cena, fatos, etc.)
        # Isso deve acontecer *depois* de qualquer rolagem, pois a rolagem pode influenciar o que a IA descreve.
        self._apply_ai_updates_to_gamestate(
            final_ai_response, game_state, action_type_for_ai
        )

        # Adicionar mensagem da IA ao histórico do GameState
        if final_ai_response.message:
            # Verificar repetição de NPC antes de adicionar a mensagem
            npc_for_repetition_check = self._determine_npc_for_repetition_check(
                action_type_for_ai,  # Ação que a IA narrou (ex: "talk_result")
                source_mechanical_handler_result,  # Resultado do handler mecânico
                game_state,
            )
            processed_message_content, _ = self._process_npc_repetition(
                final_ai_response.message, npc_for_repetition_check, game_state
            )
            # Atualizar a mensagem na resposta final apenas se processed_message_content não for None.
            # Dado que final_ai_response.message é str, e _process_npc_repetition
            # (com a lógica atual) não transforma um str em None, processed_message_content deveria ser str.
            # Esta verificação torna o código mais robusto à assinatura de _process_npc_repetition.
            if processed_message_content is not None:
                final_ai_response.message = processed_message_content

            game_state.add_message(role="assistant", content=final_ai_response.message)

        # Lógica de sobrevivência (se aplicável após a chamada da IA e atualização do estado)
        # Isso pode ser mais apropriado se o status de sobrevivência deve ser comunicado ao jogador
        # como uma mensagem de sistema separada, após a narração da IA.
        survival_message_part = self._handle_survival_updates(
            character, action_type_for_ai, game_state
        )
        if survival_message_part and "survival_info" not in final_ai_response.details:
            # Adiciona informação de sobrevivência aos detalhes da resposta da IA
            # ou envia como uma mensagem de sistema separada no game_state.add_message
            final_ai_response.details["survival_info"] = survival_message_part.strip()

        return final_ai_response

    def process_action(
        self,
        action: str,
        details: str,
        character: Character,
        game_state: GameState,
        ai_client: Optional[GameAIClient] = None,
    ) -> AIResponsePydantic:
        """
        Processes a player action by finding the appropriate handler,
        executing mechanical game logic, and then interacting with the AI
        for narrative generation.
        """
        logger.info(
            f"GameEngine initial processing action: {action}, details: {details}, char: {character.name}"
        )
        game_state.current_action = action  # Store current action in game_state

        # Passo 1: Se a ação inicial é 'interpret', obter a interpretação da IA primeiro.
        if action.lower() == "interpret" and ai_client:
            # Usar _handle_ai_interaction para obter a interpretação da IA
            # O prompt para "interpret_needed" já pede à IA para interpretar a ação.
            initial_ai_response = self._handle_ai_interaction(
                action_type_for_ai="interpret_needed",  # Instrução para a IA interpretar
                text_input_for_ai=details,  # O texto bruto do jogador
                character=character,
                game_state=game_state,
                ai_client=ai_client,
                source_mechanical_handler_result={
                    "success": True
                },  # Handler inicial é como um "pass-through"
                actual_handler=get_action_handler(
                    "interpret"
                ),  # Handler de interpretação
            )

            if not initial_ai_response.success:
                logger.warning(
                    f"AI interpretation failed: {initial_ai_response.message}"
                )
                return initial_ai_response  # Retorna o erro da IA

            # A IA deve ter retornado 'interpreted_action_type' e 'interpreted_action_details'
            interpreted_action_type = initial_ai_response.interpreted_action_type
            interpreted_action_details_dict = (
                initial_ai_response.interpreted_action_details or {}
            )

            if interpreted_action_type:
                logger.info(
                    f"AI interpreted action as: {interpreted_action_type} with details: {interpreted_action_details_dict}"
                )
                # Agora, use o tipo de ação interpretado para chamar o handler mecânico apropriado.
                action_to_handle_mechanically = interpreted_action_type

                # Os 'details' para o handler mecânico podem vir de 'interpreted_action_details'
                details_for_handler = details  # Fallback para os detalhes originais
                if isinstance(interpreted_action_details_dict, dict):
                    action_key = action_to_handle_mechanically.lower()
                    detail_key_for_action = ACTION_DETAIL_KEYS_FOR_INTERPRETATION.get(
                        action_key
                    )
                    if detail_key_for_action:
                        details_for_handler = interpreted_action_details_dict.get(
                            detail_key_for_action, details
                        )

                actual_handler = get_action_handler(action_to_handle_mechanically)
                logger.debug(
                    f"Using mechanical handler: {type(actual_handler).__name__} for interpreted action: {action_to_handle_mechanically}"
                )

                try:
                    result_from_mechanical_handler = actual_handler.handle(
                        details_for_handler, character, game_state
                    )
                except Exception as e:
                    logger.error(
                        f"Error in mechanical handler {type(actual_handler).__name__} for action {action_to_handle_mechanically}: {e}",
                        exc_info=True,
                    )
                    # Update the existing AIResponsePydantic object with error details
                    # Pydantic models allow field assignment by default
                    original_ai_message = initial_ai_response.message
                    initial_ai_response.success = False
                    initial_ai_response.message = f"Erro ao executar ação interpretada '{action_to_handle_mechanically}': {e}. Narrativa da IA original: {original_ai_message}"
                    initial_ai_response.error = f"Mechanical handler error for {action_to_handle_mechanically}: {str(e)}"
                    # Ensure current location and scene are from game_state as AI might not have updated them if interpretation failed early
                    initial_ai_response.current_detailed_location = (
                        game_state.current_location
                    )
                    initial_ai_response.scene_description_update = (
                        game_state.scene_description
                    )
                    return initial_ai_response  # Return the modified AIResponsePydantic

                # Se o handler mecânico foi bem-sucedido, a IA narra o resultado.
                # O GameState já foi modificado pelo handler mecânico.
                if result_from_mechanical_handler.get("success"):
                    action_for_narration = result_from_mechanical_handler.get(
                        "action_performed", action_to_handle_mechanically
                    )
                    message_for_narration = result_from_mechanical_handler.get(
                        "message", "A ação foi realizada."
                    )

                    final_narration_result = self._handle_ai_interaction(
                        action_type_for_ai=action_for_narration,
                        text_input_for_ai=message_for_narration,
                        character=character,
                        game_state=game_state,  # game_state já está atualizado
                        ai_client=ai_client,
                        source_mechanical_handler_result=result_from_mechanical_handler,
                        actual_handler=actual_handler,
                    )
                    # Adicionar a mensagem da interpretação inicial ao resultado final
                    # A mensagem de interpretação já está em initial_ai_response.message.
                    # Se quisermos anexá-la ou prefixá-la, podemos fazer aqui.
                    # Por ora, a resposta da IA interpretada já foi retornada se houve falha.
                    # Se chegou aqui, a interpretação foi bem-sucedida e a narração final é o foco.
                    return final_narration_result  # initial_ai_response.message foi a interpretação.
                else:
                    # Se o handler mecânico falhou, a IA deve narrar essa falha.
                    message_for_narration_failure = result_from_mechanical_handler.get(
                        "message", "A ação não pôde ser completada."
                    )
                    action_for_narration_failure = result_from_mechanical_handler.get(
                        "action_performed", f"{action_to_handle_mechanically}_failed"
                    )

                    final_narration_failure = self._handle_ai_interaction(
                        action_type_for_ai=action_for_narration_failure,
                        text_input_for_ai=message_for_narration_failure,
                        character=character,
                        game_state=game_state,
                        ai_client=ai_client,
                        source_mechanical_handler_result=result_from_mechanical_handler,
                        actual_handler=actual_handler,
                    )
                    # Adicionar a mensagem da interpretação inicial ao resultado final
                    return final_narration_failure  # Similar ao caso de sucesso acima.
            else:
                # Se a IA não interpretou um tipo de ação específico,
                # apenas retorne a resposta inicial da IA (que pode ser uma narrativa genérica).
                logger.info(
                    "AI did not return a specific interpreted_action_type. Returning initial AI response."
                )
                return initial_ai_response
        else:
            # Para ações que não são 'interpret' (ex: 'attack' direto do frontend, 'rest')
            # ou se não houver ai_client
            actual_handler = get_action_handler(action)
            logger.debug(
                f"Using direct handler: {type(actual_handler).__name__} for action: {action}"
            )
            try:
                result_from_handler = actual_handler.handle(
                    details, character, game_state
                )
            except Exception as e:
                logger.error(
                    f"Error in direct handler {type(actual_handler).__name__} for action {action}: {e}",
                    exc_info=True,
                )
                return AIResponsePydantic(
                    success=False,
                    message=f"Erro ao processar a ação '{action}' no handler: {e}",
                    current_detailed_location=game_state.current_location,
                    scene_description_update=game_state.scene_description,
                    error=f"Direct handler error for {action}: {str(e)}",
                    details={"handler_exception": str(e)},
                    interpreted_action_type=action,  # The action that failed
                    interpreted_action_details=None,
                    suggested_roll=None,
                    suggested_location_data=None,
                    interactable_elements=None,
                    new_facts=None,
                    # Não há mensagem de interpretação aqui, pois não houve fase de interpretação.
                )

            if result_from_handler.get("success"):  # Sucesso mecânico
                action_for_ai = result_from_handler.get("action_performed", action)
                message_for_ai_narration = result_from_handler.get("message", details)

                final_result = self._handle_ai_interaction(
                    action_type_for_ai=action_for_ai,
                    text_input_for_ai=message_for_ai_narration,
                    character=character,
                    game_state=game_state,
                    ai_client=ai_client,
                    source_mechanical_handler_result=result_from_handler,
                    actual_handler=actual_handler,
                )
                return final_result
            else:
                logger.info(  # Pode ser normal uma ação mecânica falhar (ex: tentar abrir porta trancada)
                    f"Direct mechanical action '{action}' failed. Handler result: {result_from_handler}"
                )
                # Tentar narrar a falha mecânica
                message_for_narration_failure = result_from_handler.get(
                    "message", "A ação não pôde ser completada."
                )
                action_for_narration_failure = result_from_handler.get(
                    "action_performed", f"{action}_failed"
                )

                final_narration_failure = self._handle_ai_interaction(
                    action_type_for_ai=action_for_narration_failure,
                    text_input_for_ai=message_for_narration_failure,
                    character=character,
                    game_state=game_state,
                    ai_client=ai_client,
                    source_mechanical_handler_result=result_from_handler,
                    actual_handler=actual_handler,
                )
                return final_narration_failure
