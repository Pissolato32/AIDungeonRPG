# filepath: c:\Users\rodri\Desktop\REPLIT RPG\core\game_engine.py
"""
Game engine module for handling game state and actions."""

import json
import os
import random
import logging  # Adicionado logging
from typing import Any, Dict, List, Optional, cast

# Assume GameAIClient is in ai.game_ai_client, adjust if necessary
from ai.game_ai_client import GameAIClient, AIResponse  # Import AIResponse

# Assume ActionHandler is in core.actions, adjust if necessary
from core.actions import (
    CustomActionHandler,  # Importar para verificar se é uma instância
    ActionHandler,
    get_action_handler,
)
from core.models import Character

from .game_state_model import GameState, LocationCoords, LocationData

from utils.dice import roll_dice, calculate_attribute_modifier  # Importar para rolagens

logger = logging.getLogger(__name__)  # Configurar logger para este módulo


class GameEngine:
    """Main game engine that processes actions and manages game state."""

    def __init__(self) -> None:
        """Initialize the game engine."""
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self._location_cache: Dict[str, Dict[str, Any]] = {}
        self._location_types: Dict[str, List[str]] = {
            "abrigo": ["abrigo subterrâneo", "bunker", "refúgio seguro"],
            "ruina_urbana": [
                "ruas devastadas",
                "prédio abandonado",
                "zona comercial saqueada",
            ],
            "posto_avancado": ["posto de controle", "acampamento de sobreviventes"],
            "zona_perigosa": [
                "ninho de zumbis",
                "área contaminada",
                "hospital infestado",
            ],
            "natureza_selvagem": [
                "floresta silenciosa",
                "estrada abandonada",
                "fazenda isolada",
            ],
        }

    def _get_save_path(self, user_id: str, data_type: str) -> str:
        """Helper to get the save file path for general user data (legacy or non-character specific)."""
        return os.path.join(self.data_dir, f"{user_id}_{data_type}.json")

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
        path = self._get_character_save_path(character.id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(character.to_dict(), f, indent=2)
        except IOError as e:
            logger.error(f"Error saving character {character.id}: {e}")

    def load_character(self, character_id: str) -> Optional[Character]:
        """Load character data from a file."""
        path = self._get_character_save_path(character_id)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return Character.from_dict(data)
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

    def process_action(
        self,
        action: str,
        details: str,
        character: Character,
        game_state: GameState,
        action_handler: Optional[ActionHandler] = None,
        ai_client: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Process a player action."""

        # Add player's raw input to message history before any processing
        if details and details.strip():
            game_state.add_message(role="user", content=details)

        game_state.current_action = action

        actual_handler = action_handler or get_action_handler(action)
        result_from_handler = actual_handler.handle(details, character, game_state)

        message_for_ai_narration = result_from_handler.get("message", "")
        action_succeeded_mechanically = result_from_handler.get("success", False)
        skip_ai_narration = result_from_handler.get("skip_ai_narration", False)

        # Determine the action type to send to the AI
        # If the handler performed a specific resolved action (e.g., dice roll), use that.
        # If the original action was 'custom' or 'interpret' and it did NOT resolve to something specific,
        # then GameEngine should send "interpret" to the AI with the original details.
        action_for_ai = result_from_handler.get("action_performed", action)

        if (
            action.lower() == "custom" or action.lower() == "interpret"
        ) and not result_from_handler.get("action_performed"):
            # If it was a custom/interpret action that didn't trigger specific handler logic (like social or physical)
            # then we want the AI to interpret the raw 'details' (which is the player's input).
            action_for_ai = "interpret"
            # message_for_ai_narration should be the original player input for the AI to interpret.
            message_for_ai_narration = details

        try:
            from core.survival_system import SurvivalSystem

            survival = SurvivalSystem()
            survival_result = survival.update_stats(character, action)
            if survival_result.get("messages"):
                for msg in survival_result[
                    "messages"
                ]:  # These are system/event messages
                    game_state.add_message(role="system", content=msg)
                if survival_result["messages"]:
                    message_for_ai_narration += f" ({survival_result['messages'][0]})"

        except ImportError:
            logger.warning(
                "SurvivalSystem não encontrado, pulando atualização de status de sobrevivência."
            )
        except Exception as e:
            logger.error(f"Erro ao processar SurvivalSystem: {e}", exc_info=True)

        # Add the player's action/narration cue to the message history
        # before calling the AI.
        # message_for_ai_narration is the effective player input for this turn's AI interaction.
        # Determina se a IA deve ser chamada
        should_call_ai = (
            ai_client is not None
            and not skip_ai_narration
            and (
                action_succeeded_mechanically
                or action
                in [  # Ações que podem precisar de narração da IA mesmo se a mecânica falhar
                    "look",
                    "search",
                    "talk",
                    "custom",
                    "move",
                    "use_item",
                    "flee",
                    "rest",
                    "interpret",  # Garante que a IA seja chamada para interpretação
                ]
            )
        )

        if should_call_ai:
            try:
                game_ai = GameAIClient(ai_client)
                # GameAIClient's process_action will now internally use game_state.messages
                # (which includes the latest user message) to pass to the LLM.
                # The 'details' parameter here is the user's current input content.
                current_ai_response: AIResponse = game_ai.process_action(
                    action=action_for_ai,  # Usar action_for_ai que foi determinada anteriormente
                    details=message_for_ai_narration,
                    character=character,
                    game_state=game_state,
                    # generation_params can be passed here if needed
                )

                if current_ai_response is None:
                    logger.critical(
                        "CRITICAL: game_ai.process_action (initial call) returned None. This should not happen."
                    )
                    result_from_handler["message"] = (
                        "Erro crítico de comunicação com a IA."
                    )
                    result_from_handler["success"] = False
                    return result_from_handler

                # Verifica se a resposta da IA foi bem-sucedida
                if current_ai_response.get("success"):
                    # >>> NOVO: Processar suggested_roll
                    if current_ai_response.get("suggested_roll") and isinstance(
                        actual_handler, CustomActionHandler
                    ):
                        # Usar .get() para roll_suggestion e verificar se é um dicionário válido
                        roll_suggestion_data = current_ai_response.get("suggested_roll")
                        if (
                            isinstance(roll_suggestion_data, dict)
                            and roll_suggestion_data
                        ):  # Garante que não é None e não é um dict vazio
                            attribute_to_check = roll_suggestion_data.get(
                                "attribute", "intelligence"
                            )
                            dc = roll_suggestion_data.get("dc", 15)
                            roll_description = roll_suggestion_data.get(
                                "description", "uma ação desafiadora"
                            )

                            attribute_score = character.attributes.get(
                                attribute_to_check, 10
                            )
                            modifier = calculate_attribute_modifier(attribute_score)

                            roll_result_obj = roll_dice(1, 20, modifier)
                            roll_total = roll_result_obj["total"]
                            roll_succeeded = roll_total >= dc

                            mechanical_roll_outcome_msg = (
                                f"Tentativa de '{roll_description}'. "
                                f"Teste de {attribute_to_check.capitalize()} (Rolagem: {roll_total} vs DC {dc}). "
                                f"{'Sucesso!' if roll_succeeded else 'Falha!'}"
                                f" Detalhes da rolagem: {roll_result_obj.get('result_string', '')}"
                            )

                            game_state.add_message(
                                role="system", content=mechanical_roll_outcome_msg
                            )

                            ai_response_narrated_roll: AIResponse = (
                                game_ai.process_action(
                                    action="narrate_roll_outcome",
                                    details=mechanical_roll_outcome_msg,
                                    character=character,
                                    game_state=game_state,
                                )
                            )

                            if ai_response_narrated_roll is None:
                                logger.error(
                                    "CRITICAL: game_ai.process_action (narrate_roll_outcome) returned None. "
                                    "A narração da rolagem falhou. Usando a mensagem da IA pré-rolagem."
                                )
                            elif not ai_response_narrated_roll.get("success"):
                                logger.warning(
                                    f"AI failed to narrate roll outcome successfully: {ai_response_narrated_roll.get('message')}. "
                                    "Usando a mensagem da IA pré-rolagem."
                                )
                                if ai_response_narrated_roll.get("message"):
                                    game_state.add_message(
                                        role="system",
                                        content=f"Erro na narração da IA para a rolagem: {ai_response_narrated_roll.get('message')}",
                                    )
                            else:
                                current_ai_response = ai_response_narrated_roll
                        else:  # roll_suggestion_data não era um dicionário válido ou estava vazio
                            logger.warning(
                                "current_ai_response continha 'suggested_roll', mas não era um dicionário válido ou estava vazio."
                            )
                    # <<< FIM NOVO: Processar suggested_roll

                    # Atualiza o game_state com os novos dados da IA
                    new_detailed_location = current_ai_response.get(
                        "current_detailed_location"
                    )
                    if new_detailed_location:
                        game_state.current_location = new_detailed_location

                    new_scene_description = current_ai_response.get(
                        "scene_description_update"
                    )
                    if new_scene_description:
                        game_state.scene_description = new_scene_description

                    # Add AI's response to message history
                    ai_message_content = current_ai_response.get("message")
                    if ai_message_content:
                        game_state.add_message(
                            role="assistant", content=ai_message_content
                        )
                    else:
                        logger.warning(
                            "AI response was successful but no message content found."
                        )

                    if (
                        not current_ai_response.get("message")
                        and message_for_ai_narration
                    ):
                        current_ai_response["message"] = message_for_ai_narration

                    # Adicionar outros campos do result_from_handler se não estiverem na resposta da IA
                    # e se forem relevantes para o frontend.
                    # Garantir que 'success' e 'message' da IA tenham precedência.
                    final_result = cast(
                        Dict[str, Any], current_ai_response.copy()
                    )  # Começa com a resposta da IA
                    for key, value in result_from_handler.items():
                        if (
                            key not in final_result
                        ):  # Adiciona apenas se não existir na resposta da IA
                            final_result[key] = value
                    final_result["success"] = current_ai_response.get(
                        "success", False
                    )  # Garante que o success da IA prevaleça

                    return final_result
                else:  # Falha da IA ou do processador de resposta da IA
                    logger.warning(
                        f"AI processing failed or returned success=false. AI Response: {current_ai_response}"
                    )
                    # Usar a mensagem de erro da IA se disponível, senão a do handler
                    fallback_message = current_ai_response.get(
                        "message"
                    ) or result_from_handler.get(
                        "message", "Erro ao processar com a IA."
                    )
                    result_from_handler["message"] = fallback_message
                    result_from_handler["success"] = False
                    return result_from_handler
            except ImportError:
                logger.error(
                    "GameAIClient não pôde ser importado. Verifique a instalação e o caminho.",
                    exc_info=True,
                )
                result_from_handler["message"] = (
                    result_from_handler.get("message", "")
                    + " (Erro: Componente de IA indisponível)"
                )
                result_from_handler["success"] = False
                return result_from_handler

            except Exception as e:
                logger.error(f"Erro ao processar com GameAIClient: {e}", exc_info=True)
                result_from_handler["message"] = (
                    result_from_handler.get("message", "") + f" (Erro na IA: {e})"
                )
                result_from_handler["success"] = False
                return result_from_handler

        return result_from_handler

    # Note: The GameAIClient class (in ai/game_ai_client.py) will need to be adapted
    # to use game_state.messages as the 'messages' argument for
    # self.ai_client.generate_response (where self.ai_client is an OpenRouterClient instance).
    # Example snippet for GameAIClient.process_action:
    #   messages_for_llm = game_state.messages.copy() # This now includes the latest user message
    #   raw_llm_response_str = self.ai_client.generate_response(messages=messages_for_llm, generation_params=...)

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
        if not new_location_id or new_location_id in game_state.discovered_locations:
            logger.warning(
                f"Tentativa de gerar localização já existente ou com ID inválido: {new_location_id}"
            )
            return
        new_coords = self._get_new_coordinates(game_state)
        location_name = result_from_handler.get(
            "new_location_name",
            self._generate_location_name(
                result_from_handler.get("location_type", "ruina_urbana")
            ),
        )
        location_type = result_from_handler.get("location_type", "ruina_urbana")
        description = result_from_handler.get(
            "new_location_description",
            self._generate_location_description(location_type),
        )
        # A anotação de tipo foi restaurada.
        # Garanta que LocationData em core/game_state_model.py defina todos os campos usados aqui.
        location_data: LocationData = {
            "name": location_name,
            "coordinates": new_coords,
            "type": location_type,
            "description": description,
            "visited": True,
            "connections": {},
            "resources": self._generate_location_resources(location_type),
            "danger_level": random.randint(1, 5),
            "events": self._generate_location_events(location_type),
            "npcs": self._generate_location_npcs(location_type, game_state),
        }
        game_state.discovered_locations[new_location_id] = location_data
        game_state.current_location = location_name
        game_state.scene_description = description
        game_state.coordinates = new_coords
        game_state.npcs_present = location_data.get("npcs", [])
        game_state.events = location_data.get("events", [])
        self._handle_connections(game_state, new_location_id, new_coords)

    # TODO: Este método não está sendo utilizado atualmente no código.
    # Se for necessário no futuro, a chamada para _generate_location_npcs
    # precisa ser corrigida, pois game_state=None causará um erro.
    # def _create_location_data(
    #     self, result: Dict[str, Any], new_coords: LocationCoords, loc_id: str
    # ) -> LocationData:
    #     location_type = result.get("location_type")
    #     if not location_type or location_type not in self._location_types:
    #         location_type = random.choice(list(self._location_types.keys()))
    #     return {
    #         "name": result.get(
    #             "location_name", self._generate_location_name(location_type)
    #         ),
    #         "coordinates": new_coords,
    #         "type": location_type,
    #         "description": result.get(
    #             "description", self._generate_location_description(location_type)
    #         ),
    #         "visited": True,
    #         "connections": {},
    #         "resources": self._generate_location_resources(location_type),
    #         "danger_level": random.randint(1, 5),
    #         "events": self._generate_location_events(location_type),
    #         "npcs": self._generate_location_npcs(location_type, game_state=None), # Erro aqui: game_state não pode ser None
    #     }

    def _handle_connections(
        self,
        game_state: GameState,
        new_location_id: str,
        new_coords: LocationCoords,
    ) -> None:
        if new_location_id not in game_state.discovered_locations:
            return
        new_location_data = game_state.discovered_locations[new_location_id]
        if "connections" not in new_location_data:
            new_location_data["connections"] = {}
        for existing_id, existing_loc_data in game_state.discovered_locations.items():
            if existing_id == new_location_id:
                continue
            existing_coords = existing_loc_data.get("coordinates")
            if existing_coords:
                direction_from_existing_to_new = self._get_direction(
                    existing_coords, new_coords
                )
                if direction_from_existing_to_new:
                    if "connections" not in existing_loc_data:
                        existing_loc_data["connections"] = {}
                    existing_loc_data["connections"][
                        new_location_id
                    ] = direction_from_existing_to_new
                    direction_from_new_to_existing = self._opposite_direction(
                        direction_from_existing_to_new
                    )
                    new_location_data["connections"][
                        existing_id
                    ] = direction_from_new_to_existing

    @staticmethod
    def _generate_location_name(location_type: str) -> str:
        prefixes = {
            "abrigo": ["Abrigo", "Bunker", "Refúgio"],
            "ruina_urbana": ["Ruínas de", "Distrito de", "Setor"],
            "posto_avancado": ["Posto Avançado", "Acampamento", "Barricada"],
            "zona_perigosa": ["Zona Infestada de", "Ninho de", "Covil de"],
            "natureza_selvagem": ["Estrada para", "Floresta de", "Campos de"],
        }
        suffixes = [
            "Perdido",
            "Esquecido",
            "Devastado",
            "Silencioso",
            "da Esperança",
            "do Desespero",
            "Sombrio",
            "Antigo",
        ]
        feminine_prefixes = [
            "Abrigo",
            "Refúgio",
            "Ruínas de",
            "Zona Infestada de",
            "Estrada para",
            "Floresta de",
            "Barricada",
        ]
        prefix = random.choice(prefixes.get(location_type, ["Local"]))
        if any(fp in prefix for fp in feminine_prefixes):
            feminine_suffixes = [
                "Perdida",
                "Esquecida",
                "Devastada",
                "Silenciosa",
                "da Esperança",
                "do Desespero",
                "Sombria",
                "Antiga",
            ]
            suffix = random.choice(feminine_suffixes)
        else:
            suffix = random.choice(suffixes)
        base_name = f"{prefix} {suffix}"
        if random.random() < 0.2:
            qualifier = random.choice(
                ["Alfa", "Beta", "Gama", "Delta", "Zeta", "7", "9", "X"]
            )
            base_name = f"{base_name} {qualifier}"
        return base_name

    @staticmethod
    def _generate_location_description(location_type: str) -> str:
        descriptions = {
            "abrigo": "Um refúgio improvisado, mas relativamente seguro. As paredes são frias e úmidas, e o ar é pesado com o cheiro de mofo e desinfetante barato.",
            "ruina_urbana": "Prédios em ruínas se erguem como esqueletos contra o céu cinzento. Carros abandonados e destroços bloqueiam as ruas, e um silêncio fantasmagórico é quebrado apenas pelo vento uivante.",
            "posto_avancado": "Uma barricada feita às pressas com arame farpado e sucata protege este pequeno bolsão de civilização. Sentinelas observam nervosamente os arredores, armas em punho.",
            "zona_perigosa": "Um silêncio opressor paira aqui, quebrado apenas por sons guturais distantes ou o zumbido de insetos mutantes. O cheiro de morte e decomposição é forte e nauseante.",
            "natureza_selvagem": "A natureza tenta retomar o que era seu, com vegetação densa crescendo sobre as cicatrizes da civilização. Mesmo aqui, a ameaça dos infectados e da escassez é constante.",
        }
        base_desc = descriptions.get(
            location_type,
            "Um local desolado e perigoso. Você sente um arrepio na espinha e a sensação constante de estar sendo observado.",
        )
        details = [
            "Pichações estranhas cobrem algumas paredes.",
            "Há um veículo capotado e enferrujado nas proximidades.",
            "O som de água pingando ecoa de algum lugar próximo.",
            "Um odor metálico paira no ar.",
            "Você nota rastros recentes no chão poeirento.",
            "Um vento frio varre a área, trazendo consigo sussurros indecifráveis.",
        ]
        return base_desc + " " + random.choice(details)

    @staticmethod
    def _generate_location_resources(
        location_type: str,
    ) -> Optional[Dict[str, int]]:
        if random.random() > 0.7:
            return None
        base_resources = {
            "Comida Enlatada": (1, 3),
            "Garrafa de Água": (1, 2),
            "Bandagens": (0, 2),
            "Sucata de Metal": (1, 5),
            "Retalhos de Tecido": (1, 4),
            "Componentes Eletrônicos": (0, 2),
            "Munição (Pistola)": (0, 5),
            "Munição (Espingarda)": (0, 3),
            "Gasolina (lata pequena)": (0, 1),
            "Madeira": (1, 4),
            "Ervas Medicinais": (0, 2),
            "Pilhas": (0, 3),
        }
        type_specific_boost = {
            "abrigo": {"Comida Enlatada": 2, "Garrafa de Água": 2, "Bandagens": 1},
            "ruina_urbana": {"Sucata de Metal": 2, "Componentes Eletrônicos": 1},
            "posto_avancado": {
                "Munição (Pistola)": 3,
                "Munição (Espingarda)": 2,
                "Bandagens": 1,
            },
            "zona_perigosa": {},
            "natureza_selvagem": {"Madeira": 2, "Ervas Medicinais": 1},
        }
        generated_resources: Dict[str, int] = {}
        num_resource_types_to_find = random.randint(1, 3)
        possible_resources_for_type = list(base_resources.keys())
        if location_type in type_specific_boost:
            for _ in range(2):
                possible_resources_for_type.extend(
                    type_specific_boost[location_type].keys()
                )
        for _ in range(num_resource_types_to_find):
            if not possible_resources_for_type:
                break
            resource_name = random.choice(possible_resources_for_type)
            possible_resources_for_type.remove(resource_name)
            min_q, max_q = base_resources[resource_name]
            quantity_boost = 0
            if (
                location_type in type_specific_boost
                and resource_name in type_specific_boost[location_type]
            ):
                quantity_boost = type_specific_boost[location_type][resource_name]
            quantity = random.randint(min_q, max_q + quantity_boost)
            if quantity > 0:
                generated_resources[resource_name] = quantity
        return generated_resources if generated_resources else None

    @staticmethod
    def _generate_location_events(location_type: str) -> List[str]:
        common_events = [
            "Um silêncio repentino e perturbador toma conta do ambiente.",
            "Você ouve um barulho metálico distante, como algo caindo.",
            "Uma rajada de vento traz consigo um cheiro estranho e adocicado.",
        ]
        type_specific_events = {
            "abrigo": [
                "O gerador falha por um instante, mergulhando tudo na escuridão antes de voltar.",
                "Alguém está cantando baixinho uma canção triste em um canto escuro.",
                "Uma discussão acalorada sobre o racionamento de comida pode ser ouvida de uma sala próxima.",
                "Você encontra um diário antigo com anotações sobre os primeiros dias do surto.",
            ],
            "ruina_urbana": [
                "Um bando de corvos grasna agourentamente de cima de um prédio em ruínas.",
                "O vento assobia sinistramente através das janelas quebradas de um arranha-céu esvaziado.",
                "Um barulho alto de algo desabando ecoa de um prédio vizinho, levantando uma nuvem de poeira.",
                "Você vê uma sombra se movendo rapidamente em um beco, desaparecendo antes que possa identificar.",
            ],
            "posto_avancado": [
                "Um sobrevivente está limpando sua arma meticulosamente, com um olhar determinado.",
                "A troca de guarda na barricada acontece, os novos sentinelas parecem tensos.",
                "Alguém conta uma história nostálgica sobre como era o mundo antes do apocalipse.",
                "Um alarme falso soa, causando um breve momento de pânico.",
            ],
            "zona_perigosa": [
                "Um gemido gutural e faminto ecoa de algum lugar próximo, fazendo seu sangue gelar.",
                "O cheiro de podridão e carne em decomposição se intensifica, quase o fazendo engasgar.",
                "Você vê sombras se movendo rapidamente no limite da sua visão, muito rápidas para serem humanas.",
                "O chão está coberto de uma substância viscosa e escura de origem desconhecida.",
            ],
            "natureza_selvagem": [
                "Um animal selvagem (não infectado, talvez um cervo ou coelho) cruza seu caminho e desaparece na mata.",
                "O silêncio da floresta é quase total, quebrado apenas pelo som do vento nas árvores e seus próprios passos.",
                "Você encontra rastros recentes no chão lamacento... definitivamente não são humanos.",
                "Uma revoada de pássaros assustados levanta voo de repente das árvores próximas.",
            ],
        }
        possible_events = common_events + type_specific_events.get(location_type, [])
        if not possible_events:
            return ["O ambiente parece estranhamente calmo... calmo demais."]
        num_events = random.randint(0, 2)
        if num_events == 0:
            return []
        return random.sample(possible_events, k=min(num_events, len(possible_events)))

    def _generate_location_npcs(
        self, location_type: str, game_state: GameState
    ) -> List[str]:
        if random.random() < 0.4:
            return []
        npc_archetypes = {
            "abrigo": [
                "Velho Sobrevivente Cansado",
                "Médica de Campo Apavorada",
                "Engenheiro Habilidoso",
                "Criança Assustada",
            ],
            "ruina_urbana": [
                "Catador Solitário",
                "Saqueador Desesperado",
                "Vigia Paranoico",
            ],
            "posto_avancado": [
                "Líder Carismático do Posto",
                "Guarda Leal",
                "Comerciante Oportunista",
            ],
            "zona_perigosa": [],
            "natureza_selvagem": ["Caçador Recluso", "Eremita Misterioso"],
        }
        possible_names_for_type = npc_archetypes.get(
            location_type, ["Sobrevivente Aleatório"]
        )
        if not possible_names_for_type:
            return []
        num_npcs_to_generate = random.randint(1, min(2, len(possible_names_for_type)))
        generated_npc_names: List[str] = []
        all_known_npc_names_lower = {
            name.lower() for name in game_state.known_npcs.keys()
        }
        attempts = 0
        while len(generated_npc_names) < num_npcs_to_generate and attempts < 10:
            attempts += 1
            potential_name = random.choice(possible_names_for_type)
            if potential_name.lower() in all_known_npc_names_lower:
                continue
            generated_npc_names.append(potential_name)
            all_known_npc_names_lower.add(potential_name.lower())
            if potential_name not in game_state.known_npcs:
                from core.npc import NPC

                npc_data = {
                    "name": potential_name,
                    "race": "Humano",
                    "profession": (
                        potential_name.split(" ")[-1]
                        if " " in potential_name
                        else "Sobrevivente"
                    ),
                    "personality": random.choice(
                        ["Cauteloso", "Desconfiado", "Prestativo", "Assustado"]
                    ),
                    "level": random.randint(1, 5),
                    "knowledge": [],
                    "quests": [],
                    "current_mood": "Neutro",
                    "disposition": "neutral",
                }
                game_state.add_npc(potential_name, npc_data)
        return generated_npc_names
