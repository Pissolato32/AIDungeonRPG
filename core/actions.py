# filepath: c:\Users\rodri\Desktop\REPLIT RPG\core\actions.py
import logging
import os
import random
import re
from typing import Any, Dict, List, Optional, Tuple  # Added Tuple

from core.enemy import Enemy  # Import Enemy class
from core.models import Character
from utils.dice import (  # Importar funções de dado
    calculate_attribute_modifier,
    calculate_damage,
    roll_dice,
)
from utils.quest_generator import generate_quest  # Direct import for generate_quest

from .recipes import CRAFTING_RECIPES  # For CraftActionHandler
from .skills import SkillManager  # For SkillActionHandler
from .world_generator import WorldGenerator

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ActionHandler:
    """
    Default action handler that provides basic action handling.

    This class provides a basic implementation of an action handler,
    which can be used as a base for more specific action handlers.
    """

    VALID_ACTIONS = {"move", "look", "talk", "search", "attack"}

    def handle(
        self, details: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        """Handle an action with default behavior."""
        logger.info(f"Handling action with details: {details}")

        # Default response for unhandled actions
        return {
            "success": False,
            "message": f"A ação '{details if details else 'desconhecida'}' não é reconhecida ou não foi implementada.",
        }

    def ai_response(
        self, action: str, details: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        """Fallback AI response if a specific handler doesn't fully process."""
        return {
            "success": False,
            "message": f"A ação '{details}' não é reconhecida ou não foi implementada.",
        }

    def log_action(self, action: str, character: "Character") -> None:
        """Log the action performed by the character."""
        logger.info(
            f"{character.name} realizou a ação: {action} (handler: {self.__class__.__name__})"
        )

    def validate_action(self, action: str) -> bool:
        """Validate the action before processing."""
        return action in self.VALID_ACTIONS

    def handle_action(
        self, action: str, details: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        """Handle the action based on its type."""
        if not self.validate_action(action):
            logger.warning(f"Tentativa de ação inválida: {action}")
            return {"success": False, "message": f"Ação inválida '{action}'."}

        self.log_action(action, character)
        return self.handle(details, character, game_state)


class MoveActionHandler(ActionHandler):
    """Handler for the 'move' action."""

    def handle(
        self, details: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        # Init world generator
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        world_generator = WorldGenerator(data_dir)

        destination = details.strip().lower() if isinstance(details, str) else ""
        current_location_id = game_state.location_id
        directions = ["norte", "sul", "leste", "oeste"]  # Traduzido

        # Normalize input
        normalized_direction: Optional[str] = next(
            (d for d in directions if d in destination), None
        )

        # Process world map
        if (
            not hasattr(game_state, "world_map")
            or "locations" not in game_state.world_map
            or not game_state.world_map.get(
                "locations"
            )  # Adiciona verificação se 'locations' está vazio
        ):
            logger.warning(
                "MoveActionHandler: game_state.world_map não está configurado corretamente ou não contém 'locations'. "
                f"world_map atual: {getattr(game_state, 'world_map', 'Não definido')}"
            )
            return self.ai_response("move", details, character, game_state)

        current_location = game_state.world_map["locations"].get(
            current_location_id, {}
        )
        connections = current_location.get("connections", {})

        next_location_id: Optional[str] = None

        # Try existing connections
        for dir_key, loc_id in connections.items():
            if dir_key.lower() == normalized_direction:
                next_location_id = loc_id
                break
            if (
                normalized_direction is None
                and loc_id in game_state.world_map["locations"]
                and game_state.world_map["locations"][loc_id]["name"].lower()
                in destination
            ):
                next_location_id = loc_id
                break

        # If not found, generate adjacent location
        if next_location_id is None and normalized_direction:
            new_location = world_generator.generate_adjacent_location(
                current_location_id, normalized_direction, game_state.world_map
            )
            game_state.world_map["locations"][new_location["id"]] = new_location
            current_location.setdefault("connections", {})[normalized_direction] = (
                new_location["id"]
            )
            world_generator.save_world(game_state.world_map)
            next_location_id = new_location["id"]

        # If found or generated
        if next_location_id and next_location_id in game_state.world_map["locations"]:
            next_location = game_state.world_map["locations"][next_location_id]
            game_state.location_id = next_location_id
            game_state.current_location = next_location["name"]
            game_state.coordinates = next_location["coordinates"].copy()

            visited_info = (
                game_state.visited_locations.get(next_location_id)
                if hasattr(game_state, "visited_locations")
                else None
            )

            if visited_info:
                visited_info["last_visited"] = "revisited"
                game_state.scene_description = visited_info["description"]
                game_state.npcs_present = visited_info["npcs_seen"]

                # Optional: add new events
                if random.random() < 0.3:
                    game_state.events = world_generator.generate_events(
                        next_location["name"], next_location.get("type", "unknown")
                    )
                else:
                    game_state.events = visited_info.get("events_seen", [])

                game_state.visited_locations[next_location_id] = visited_info

                return {
                    "success": True,
                    "message": f"Você se move para {next_location['name']}. {next_location['description']}",
                    "new_location": next_location["name"],
                    "description": next_location["description"],
                    "npcs": game_state.npcs_present,
                    "events": game_state.events,
                }
            # First visit
            game_state.scene_description = next_location["description"]
            game_state.npcs_present = next_location["npcs"]
            game_state.events = next_location["events"]

            if hasattr(game_state, "visited_locations"):
                game_state.visited_locations[next_location_id] = {
                    "name": game_state.current_location,
                    "last_visited": "first_time",
                    "description": game_state.scene_description,
                    "npcs_seen": game_state.npcs_present.copy(),
                    "events_seen": game_state.events.copy(),
                    "search_results": [],  # Initialize search_results
                }

            return {
                "success": True,
                "message": f"Você chega em {next_location['name']}. {next_location['description']}",
                "new_location": next_location["name"],
                "description": next_location["description"],
                "npcs": game_state.npcs_present,
                "events": game_state.events,
            }

        return self.ai_response("move", details, character, game_state)


class LookActionHandler(ActionHandler):
    """Handler for the 'look' action."""

    def handle(
        self, details: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        """Handle the 'look' action, either observing an NPC or the environment."""

        # Normaliza e valida o texto fornecido
        target = details.strip().lower() if isinstance(details, str) else ""

        # Se o jogador tentar olhar para algo específico
        if target and hasattr(game_state, "npcs_present") and game_state.npcs_present:
            # Verifica se o alvo está entre os NPCs presentes
            npc_name = next(
                (npc for npc in game_state.npcs_present if npc.lower() == target), None
            )

            if npc_name:  # Se o alvo é um NPC conhecido
                npc_details = self.get_npc_details(npc_name, character, game_state)
                return {
                    "success": True,
                    "message": (
                        f"Você observa {npc_name} atentamente. "
                        f"Um(a) {npc_details.get('race', 'Humanoide')} que trabalha como {npc_details.get('profession', 'desconhecido(a)')}. "
                        f"{npc_name} parece {npc_details.get('personality', 'comum')}. "
                        f"Pela aparência e postura, você estima que ele(a) seja nível {npc_details.get('level', '?')}."
                    ),
                }
            else:  # Se o alvo foi especificado mas não é um NPC conhecido
                if (
                    not target.strip()
                    or len(target.strip()) < 2
                    or re.fullmatch(r"[^a-zA-Z\s]+", target.strip())
                ):
                    return {
                        "success": False,
                        "message": "Não entendi o que você quer olhar. Por favor, seja mais específico ou use palavras reconhecíveis.",
                    }
                return {
                    "success": True,
                    "message": f"Você olha atentamente, mas não vê nada específico chamado '{details.capitalize()}' por aqui.",
                }
        return self.ai_response("look", details, character, game_state)

    def get_npc_details(
        self, npc_name: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        """
        Placeholder para obter os detalhes de um NPC.
        Essa função deve ser implementada de acordo com seu sistema de NPCs.
        """
        return {
            "race": "Humano",
            "profession": "catador",
            "personality": "desconfiado",
            "level": (
                random.randint(character.level - 1, character.level + 2)
                if character.level > 1
                else 1
            ),
        }


class TalkActionHandler(ActionHandler):
    """Handler for 'talk' action."""

    def handle(
        self, details: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        if details and details.strip():
            npc_query_name = details.strip()
            npc_query_name_lower = npc_query_name.lower()

            if game_state.npcs_present and any(
                npc.lower() == npc_query_name_lower for npc in game_state.npcs_present
            ):
                actual_npc_name: Optional[str] = None
                try:
                    actual_npc_name = next(
                        npc
                        for npc in game_state.npcs_present
                        if npc.lower() == npc_query_name_lower
                    )
                except StopIteration:
                    logger.error(
                        f"Alvo da conversa '{npc_query_name_lower}' inconsistência: encontrado por 'any' mas não por 'next'."
                    )

                if actual_npc_name:
                    if (
                        hasattr(game_state, "known_npcs")
                        and actual_npc_name in game_state.known_npcs
                    ):
                        npc_details = game_state.known_npcs[actual_npc_name]
                        npc_details["interactions"] = (
                            npc_details.get("interactions", 0) + 1
                        )
                        result = self.ai_response(
                            "talk", actual_npc_name, character, game_state
                        )
                        if "message" in result:
                            if npc_details["interactions"] <= 2:
                                result["message"] += (
                                    f"\n\nVocê reconhece {actual_npc_name}, um(a) {npc_details['race']} {npc_details['profession']}."
                                )
                            else:
                                result["message"] += (
                                    f"\n\n{actual_npc_name} sorri para um rosto familiar. Como um(a) experiente {npc_details['profession']}, {actual_npc_name} tem muitas histórias para contar."
                                )
                                if npc_details.get("quests") and random.random() < 0.7:
                                    result["message"] += (
                                        f" {actual_npc_name} menciona precisar de ajuda com '{random.choice(npc_details['quests'])}'."
                                    )
                        game_state.known_npcs[actual_npc_name] = npc_details
                        return result

                    npc_details = self.get_npc_details(
                        actual_npc_name, character, game_state
                    )
                    result = self.ai_response(
                        "talk", actual_npc_name, character, game_state
                    )
                    if "message" in result:
                        result["message"] += (
                            f"\n\nVocê nota que {actual_npc_name} é um(a) {npc_details['race']} {npc_details['profession']}."
                        )
                        if npc_details.get("knowledge"):
                            result["message"] += (
                                f" Parece que {actual_npc_name} sabe sobre {', '.join(npc_details['knowledge'][:2])}."
                            )
                        if npc_details.get("quests"):
                            result["message"] += (
                                f" {actual_npc_name} menciona algo sobre '{npc_details['quests'][0]}'."
                            )
                    if hasattr(game_state, "known_npcs"):
                        npc_details["interactions"] = 1
                        game_state.known_npcs[actual_npc_name] = npc_details
                    return result
        return self.ai_response("talk", details, character, game_state)

    def get_npc_details(
        self, npc_name: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        return game_state.known_npcs.get(
            npc_name,
            {
                "race": "Humano",
                "profession": "Sobrevivente",
                "personality": "Cauteloso",
                "level": character.level,
                "knowledge": [],
                "quests": [],
            },
        )


class SearchActionHandler(ActionHandler):
    """Handler for 'search' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        details_lower = details.lower() if isinstance(details, str) else ""
        if "missão" in details_lower or "tarefa" in details_lower:  # Traduzido "quest"
            if not hasattr(game_state, "npcs_present") or not game_state.npcs_present:
                return {
                    "success": False,
                    "message": "Não há ninguém por perto que possa oferecer missões no momento.",
                }
            if not hasattr(game_state, "quests"):
                game_state.quests = []
            quest_giver = random.choice(game_state.npcs_present)
            new_quest = generate_quest(
                location=game_state.current_location,
                difficulty=character.level,
            )
            new_quest["giver"] = quest_giver
            new_quest["location"] = game_state.current_location
            game_state.quests.append(new_quest)
            return {
                "success": True,
                "message": f"{quest_giver} oferece uma nova missão: {new_quest['name']}. {new_quest['description']} Recompensa: {new_quest['reward_gold']} moedas de ouro.",
            }

        result = self.ai_response("search", details, character, game_state)
        if (
            hasattr(game_state, "visited_locations")
            and game_state.location_id in game_state.visited_locations
        ):
            location_info = game_state.visited_locations[game_state.location_id]
            if "search_results" not in location_info:
                location_info["search_results"] = []
            location_info["search_results"].append(
                {"query": details, "result": result.get("message", "")}
            )
        return result


class AttackActionHandler(ActionHandler):
    """Handler for 'attack' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        if details and details.strip():
            target_npc_lower = (
                details.strip().lower() if isinstance(details, str) else ""
            )
            if game_state.combat and game_state.combat.get("enemy"):
                current_enemy_name = game_state.combat.get("enemy").name.lower()
                if not details or target_npc_lower == current_enemy_name:
                    enemy = game_state.combat.get("enemy")
                    attacker_stats = character.attributes
                    str_modifier = calculate_attribute_modifier(
                        attacker_stats.get("strength", 10)
                    )
                    to_hit_dc = 10 + getattr(enemy, "level", 1)
                    attack_roll_result = roll_dice(1, 20, str_modifier)
                    attack_roll = attack_roll_result["total"]

                    if attack_roll >= to_hit_dc:
                        weapon_damage_dice_num = 1
                        weapon_damage_dice_sides = 6
                        equipped_weapon_name = character.equipment.get("weapon")
                        if equipped_weapon_name:
                            from utils.item_generator import ItemGenerator

                            item_gen = ItemGenerator(
                                os.path.join(
                                    os.path.dirname(os.path.abspath(__file__)), "data"
                                )
                            )
                            weapon_data = item_gen.get_item_by_name(
                                equipped_weapon_name
                            )
                            if weapon_data and weapon_data.get("type") == "weapon":
                                dmg_min = weapon_data.get("damage_min", 1)
                                dmg_max = weapon_data.get("damage_max", 4)
                                damage_roll_result = roll_dice(
                                    1,
                                    (dmg_max - dmg_min + 1),
                                    dmg_min - 1 + str_modifier,
                                )
                            else:
                                damage_roll_result = roll_dice(
                                    weapon_damage_dice_num,
                                    weapon_damage_dice_sides,
                                    str_modifier,
                                )
                        else:
                            damage_roll_result = roll_dice(1, 4, str_modifier)
                        damage_dealt = max(
                            1,
                            damage_roll_result["total"] - getattr(enemy, "defense", 0),
                        )
                        enemy.health = max(0, enemy.health - damage_dealt)
                        game_state.combat["log"].append(
                            f"Você atacou {enemy.name} e causou {damage_dealt} de dano! (Rolagem de ataque: {attack_roll} vs DC {to_hit_dc})"
                        )
                        if enemy.health <= 0:
                            game_state.combat["log"].append(
                                f"{enemy.name} foi derrotado!"
                            )
                            message_to_narrate = f"Você derrotou {enemy.name}!"
                            game_state.combat = None
                            return {
                                "success": True,
                                "message": message_to_narrate,
                                "combat_ended": True,
                                "action_performed": "attack_kill",
                            }
                        message_to_narrate = f"Você acertou {enemy.name} causando {damage_dealt} de dano. (Rolagem: {attack_roll} vs DC {to_hit_dc})"
                    else:
                        damage_dealt = 0
                        game_state.combat["log"].append(
                            f"Você tentou atacar {enemy.name}, mas errou! (Rolagem de ataque: {attack_roll} vs DC {to_hit_dc})"
                        )
                        message_to_narrate = f"Você errou o ataque contra {enemy.name}. (Rolagem: {attack_roll} vs DC {to_hit_dc})"
                    return {
                        "success": True,
                        "message": message_to_narrate,
                        "combat_ongoing": True,
                        "damage_dealt": damage_dealt,
                        "enemy_hp": enemy.health,
                        "action_performed": "attack_resolved",
                    }

            target_npc_lower = (
                details.strip().lower() if isinstance(details, str) else ""
            )
            if game_state.npcs_present and any(
                npc.lower() == target_npc_lower for npc in game_state.npcs_present
            ):
                npc_to_attack: Optional[str] = None
                try:
                    npc_to_attack = next(
                        npc
                        for npc in game_state.npcs_present
                        if npc.lower() == target_npc_lower
                    )
                except StopIteration:
                    logger.error(
                        f"Alvo do ataque '{target_npc_lower}' inconsistência: encontrado por 'any' mas não por 'next'."
                    )
                if npc_to_attack:
                    enemy = Enemy(
                        name=npc_to_attack,
                        level=random.randint(character.level, character.level + 2),
                        max_health=random.randint(20, 50),
                        health=random.randint(20, 50),
                        attack_damage_min=random.randint(3, 8),
                        attack_damage_max=random.randint(9, 15),
                        defense=random.randint(3, 10),
                        description=f"Um(a) hostil {npc_to_attack} que você decidiu atacar.",
                    )
                    if not hasattr(game_state, "combat") or not game_state.combat:
                        game_state.combat = {
                            "enemy": enemy,
                            "round": 1,
                            "log": [f"Você iniciou combate com {npc_to_attack}!"],
                        }
                        return {
                            "success": True,
                            "message": f"Você atacou {npc_to_attack} e iniciou um combate! Prepare-se para lutar!",
                            "combat": True,
                        }
            enemy_types = [
                "Walker Lento",
                "Corredor Ágil",
                "Devorador Inchado",
                "Cão Infectado Raivoso",
                "Saqueador Oportunista",
                "Membro de Gangue Brutal",
                "Rato Mutante Gigante",
            ]
            enemy_name = random.choice(enemy_types)
            enemy = Enemy(
                name=enemy_name,
                level=random.randint(character.level, character.level + 2),
                max_health=random.randint(20, 50),
                health=random.randint(20, 50),
                attack_damage_min=random.randint(3, 8),
                attack_damage_max=random.randint(9, 15),
                defense=random.randint(3, 10),
                description=f"Um(a) hostil {enemy_name} que apareceu de repente.",
            )
            if not hasattr(game_state, "combat") or not game_state.combat:
                game_state.combat = {
                    "enemy": enemy,
                    "round": 1,
                    "log": [f"Um(a) {enemy_name} apareceu e você o(a) atacou!"],
                }
                return {
                    "success": True,
                    "message": f"Você procurou por inimigos e encontrou um(a) {enemy_name}! Combate iniciado!",
                    "combat": True,
                }
        return self.ai_response("attack", details, character, game_state)


class UseItemActionHandler(ActionHandler):
    """Handler for 'use_item' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        from utils.item_generator import ItemGenerator

        item_generator = ItemGenerator(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        )
        if (
            not details
            or not hasattr(character, "inventory")
            or not character.inventory
        ):
            return {
                "success": False,
                "message": "Você não tem esse item no seu inventário.",
            }
        item_name_query = details.strip() if isinstance(details, str) else ""
        item_found = False
        item_index = -1
        item_data = None
        actual_item_name: Optional[str] = None
        for i, inv_item in enumerate(character.inventory):
            if isinstance(inv_item, str) and (
                inv_item.lower() == item_name_query.lower()
                or (item_name_query and inv_item.lower() in item_name_query.lower())
            ):
                item_found = True
                item_index = i
                actual_item_name = inv_item
                item_data = item_generator.get_item_by_name(actual_item_name)
                break
            if (
                isinstance(inv_item, dict)
                and inv_item.get("name", "").lower() == item_name_query.lower()
            ):
                item_found = True
                item_index = i
                actual_item_name = inv_item.get("name")
                item_data = inv_item
                break
        if not item_found or actual_item_name is None:
            return {
                "success": False,
                "message": f"Você não tem '{item_name_query}' no seu inventário.",
            }
        if item_data:
            item_type = item_data.get("type", "")
            item_subtype = item_data.get("subtype", "")
            item_description = item_data.get("description", "")
            if item_type == "weapon":
                if not hasattr(character, "equipment") or character.equipment is None:
                    character.equipment = {}
                old_item = character.equipment.get("weapon")
                character.equipment["weapon"] = actual_item_name
                if old_item:
                    character.inventory.append(old_item)
                character.inventory.pop(item_index)
                damage_info = ""
                if "damage_min" in item_data and "damage_max" in item_data:
                    min_damage = item_data["damage_min"]
                    max_damage = item_data["damage_max"]
                    damage_info = f" Dano: {min_damage}-{max_damage}."
                return {
                    "success": True,
                    "message": f"Você equipou {actual_item_name}.{damage_info} {item_description} {f'Seu {old_item} foi guardado no inventário.' if old_item else ''}",
                }
            if item_type == "protection":
                if not hasattr(character, "equipment") or character.equipment is None:
                    character.equipment = {}
                slot = "body_armor"
                if item_subtype and "capacete" in item_subtype.lower():
                    slot = "helmet"
                old_item = character.equipment.get(slot)
                character.equipment[slot] = actual_item_name
                if old_item:
                    character.inventory.append(old_item)
                character.inventory.pop(item_index)
                defense_info = ""
                if "defense" in item_data:
                    defense_info = f" Defesa: +{item_data['defense']}."
                return {
                    "success": True,
                    "message": f"Você equipou {actual_item_name}.{defense_info} {item_description} {f'Seu {old_item} foi guardado no inventário.' if old_item else ''}",
                }
            if item_type == "consumable":
                effects_applied_messages = []
                for effect in item_data.get("effects", []):
                    effect_type = effect.get("type", "")
                    effect_value = effect.get("value", 0)
                    if effect_type == "heal_hp":
                        old_hp = character.attributes.get("current_hp", 0)
                        max_hp = character.attributes.get("max_hp", old_hp)
                        character.attributes["current_hp"] = min(
                            old_hp + effect_value, max_hp
                        )
                        healed_amount = character.attributes["current_hp"] - old_hp
                        effects_applied_messages.append(
                            f"restaurou {healed_amount} pontos de vida"
                        )
                    elif effect_type == "restore_hunger":
                        stat_key = "current_hunger"
                        max_stat_key = "max_hunger"
                        old_value = character.survival_stats.get(stat_key, 0)
                        max_value = character.survival_stats.get(max_stat_key, 100)
                        character.survival_stats[stat_key] = min(
                            old_value + effect_value, max_value
                        )
                        effects_applied_messages.append(
                            f"reduziu a fome em {effect_value}"
                        )
                    elif effect_type == "restore_thirst":
                        stat_key = "current_thirst"
                        max_stat_key = "max_thirst"
                        old_value = character.survival_stats.get(stat_key, 0)
                        max_value = character.survival_stats.get(max_stat_key, 100)
                        character.survival_stats[stat_key] = min(
                            old_value + effect_value, max_value
                        )
                        effects_applied_messages.append(
                            f"reduziu a sede em {effect_value}"
                        )
                character.inventory.pop(item_index)
                message_summary = f"Você usou {actual_item_name}."
                if effects_applied_messages:
                    message_summary += (
                        " Ele " + ", e ".join(effects_applied_messages) + "."
                    )
                message_summary += f" {item_description}"
                return {"success": True, "message": message_summary}
            if item_type == "quest":
                if (
                    item_subtype in ["documento", "mapa", "carta"]  # Traduzido
                    and "content" in item_data
                ):
                    return {
                        "success": True,
                        "message": f"Você examina {actual_item_name}. {item_description}\n\nConteúdo: {item_data['content']}",
                    }
                return {
                    "success": True,
                    "message": f"Você examina {actual_item_name}. {item_description}",
                }
        item_name_lower = actual_item_name.lower() if actual_item_name else ""
        if any(
            p in item_name_lower
            for p in ["bandagem", "kit médico", "analgésicos", "primeiros socorros"]
        ):
            heal_amount = (
                item_data.get("effect", {}).get("value", 20)
                if item_data and item_data.get("type") == "consumable"
                else 20
            )
            old_hp = character.attributes.get("current_hp", 0)
            max_hp = character.attributes.get("max_hp", old_hp)
            character.attributes["current_hp"] = min(old_hp + heal_amount, max_hp)
            healed_amount = character.attributes["current_hp"] - old_hp
            current_hp_display = character.attributes.get("current_hp", 0)
            max_hp_display = character.attributes.get("max_hp", 0)
            character.inventory.pop(item_index)
            return {
                "success": True,
                "message": f"Você usou {actual_item_name} e recuperou {healed_amount} de vida. HP Atual: {current_hp_display}/{max_hp_display}.",
            }
        if isinstance(actual_item_name, str) and any(
            eq in actual_item_name.lower()
            for eq in [
                "faca",
                "canivete",
                "machado",
                "pé de cabra",
                "cano",
                "bastão",
                "pistola",
                "revólver",
                "espingarda",
                "rifle",
                "arco",
                "besta",
                "jaqueta",
                "colete",
                "capacete",
            ]
        ):
            equip_type = "weapon"
            if any(
                w in actual_item_name.lower()
                for w in [
                    "faca",
                    "canivete",
                    "machado",
                    "pé de cabra",
                    "cano",
                    "bastão",
                    "pistola",
                    "revólver",
                    "espingarda",
                    "rifle",
                    "arco",
                    "besta",
                ]
            ) and isinstance(actual_item_name, str):
                equip_type = "weapon"
            elif isinstance(actual_item_name, str) and any(
                a in actual_item_name.lower() for a in ["jaqueta", "colete"]
            ):
                equip_type = "body_armor"
            elif isinstance(actual_item_name, str) and any(
                h in actual_item_name.lower()
                for h in ["capacete", "helmet", "chapéu"]  # Traduzido "hat"
            ):
                equip_type = "helmet"
            if not hasattr(character, "equipment") or character.equipment is None:
                character.equipment = {}
            old_item = character.equipment.get(equip_type)
            character.equipment[equip_type] = actual_item_name
            if old_item:
                character.inventory.append(old_item)
            character.inventory.pop(item_index)
            return {
                "success": True,
                "message": f"Você equipou {actual_item_name}. {f'Seu {old_item} foi guardado no inventário.' if old_item else ''}",
            }
        if isinstance(actual_item_name, str) and any(
            f in actual_item_name.lower()
            for f in [
                "comida",
                "lata",
                "ração",
                "barra",
                "água",
                "garrafa",
                "refrigerante",
                "suco",
            ]
        ):
            if (
                "current_hunger" in character.survival_stats
                and "max_hunger" in character.survival_stats
            ):
                hunger_restore = 20
                character.survival_stats["current_hunger"] = min(
                    character.survival_stats["current_hunger"] + hunger_restore,
                    character.survival_stats["max_hunger"],
                )
            if (
                "current_thirst" in character.survival_stats
                and "max_thirst" in character.survival_stats
            ):
                thirst_restore = 20
                character.survival_stats["current_thirst"] = min(
                    character.survival_stats["current_thirst"] + thirst_restore,
                    character.survival_stats["max_thirst"],
                )
            character.inventory.pop(item_index)
            return {
                "success": True,
                "message": f"Você consumiu {actual_item_name} e se sente revigorado(a).",
            }
        details_lower = details.lower() if isinstance(details, str) else ""
        if (
            "arremessar" in details_lower or "jogar" in details_lower
        ):  # Traduzido "throw"
            target = None
            if "em " in details_lower:  # Traduzido "at "
                target_part = details_lower.split("em ", 1)[1]
                target = target_part.strip()
            character.inventory.pop(item_index)
            return {
                "success": True,
                "message": f"Você arremessou {actual_item_name}{f' em {target}' if target else ''}.",
            }
        result = self.ai_response("use_item", details, character, game_state)
        if result.get("success", False):
            character.inventory.pop(item_index)
        return result


class FleeActionHandler(ActionHandler):
    """Handler for 'flee' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        if (
            not hasattr(game_state, "combat")
            or not game_state.combat
            or not game_state.combat.get("enemy")
        ):
            return self.ai_response("flee", details, character, game_state)
        dex_modifier = (character.attributes.get("dexterity", 10) - 10) // 2
        flee_chance = 0.5 + (dex_modifier * 0.05)
        flee_chance = max(0.1, min(0.9, flee_chance))
        if random.random() < flee_chance:
            enemy_name = game_state.combat["enemy"].name
            game_state.combat = None
            message = f"Você conseguiu escapar de {enemy_name}!"
            return {
                "success": True,
                "message": message,
                "combat_ended": True,
                "action_performed": "flee_success",
            }
        else:
            enemy_name = game_state.combat["enemy"].name
            message = f"Você tentou fugir, mas {enemy_name} bloqueou seu caminho!"
            return {
                "success": True,
                "message": message,
                "combat_ended": False,
                "action_performed": "flee_fail",
            }


class RestActionHandler(ActionHandler):
    """Handler for 'rest' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        if (
            hasattr(game_state, "combat")
            and game_state.combat
            and game_state.combat.get("enemy")
        ):
            return {
                "success": False,
                "message": "Você não pode descansar durante o combate!",
            }
        if random.random() < 0.2:
            message = "Você tenta encontrar um lugar para descansar, mas os barulhos ao redor e a tensão no ar tornam impossível relaxar."
            return {
                "success": True,
                "message": message,
                "rested": False,
                "action_performed": "rest_fail",
            }
        hp_to_restore = max(1, character.max_hp // 10)
        stamina_to_restore = max(1, character.max_stamina // 5)
        character.attributes["current_hp"] = min(
            character.max_hp, character.current_hp + hp_to_restore
        )
        character.attributes["current_stamina"] = min(
            character.max_stamina, character.current_stamina + stamina_to_restore
        )
        message = f"Você encontra um momento de relativa calma para descansar. Você recupera {hp_to_restore} HP e {stamina_to_restore} de Vigor."
        return {
            "success": True,
            "message": message,
            "rested": True,
            "action_performed": "rest_success",
        }


class CustomActionHandler(ActionHandler):
    """Handler for 'custom' (freeform) actions."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        details_lower = details.lower() if isinstance(details, str) else ""
        inventory_keywords = [
            "pegar",
            "coletar",
            "guardar",
            "inventário",
            "apanhar",
            "saquear",
        ]
        if any(keyword in details_lower for keyword in inventory_keywords):
            items_to_add = []
            common_items = [
                "sucata de metal",
                "fita adesiva",
                "bandagens",
                "analgésicos",
                "kit médico",
                "comida enlatada",
                "garrafa de água",
                "balas",
                "cartuchos de espingarda",
                "flechas",
                "gasolina",
                "bateria",
                "pilha",
                "corda",
                "retalhos de tecido",
                "tábuas de madeira",
                "pregos",
                "ferramentas",
                "grampo",
                "kit de arrombamento",
                "pé de cabra",
                "cano de metal",
                "taco de beisebol",
                "facão",
                "faca",
                "mochila",
                "lanterna",
                "isqueiro",
                "fósforos",
                "fragmento de mapa",
                "bilhete",
                "nota",
                "peças de rádio",
                "arame",
            ]
            for item in common_items:
                if item in details_lower:
                    items_to_add.append(item.capitalize())
            if not items_to_add and any(
                verb in details.lower()
                for verb in ["pegar", "coletar", "apanhar", "saquear"]
            ):
                scene_items: List[str] = []
                if hasattr(game_state, "scene_description"):
                    scene_text = game_state.scene_description.lower()
                    for item in common_items:
                        if item in scene_text and item not in scene_items:
                            scene_items.append(item.capitalize())
                if scene_items:
                    items_to_add = scene_items
            if items_to_add:
                if not hasattr(character, "inventory"):
                    character.inventory = []
                for item in items_to_add:
                    character.inventory.append(item)
                return {
                    "success": True,
                    "message": f"Você adicionou os seguintes itens ao seu inventário: {', '.join(items_to_add)}.",
                }
        combat_keywords = [
            "atacar",
            "lutar",
            "combate",
            "matar",
            "batalha",
            "enfrentar",
        ]
        if any(keyword in details_lower for keyword in combat_keywords):
            target = None
            if game_state.npcs_present:
                for npc in game_state.npcs_present:
                    if npc.lower() in details_lower:
                        target = npc
                        break
            if target:
                enemy = Enemy(
                    name=target,
                    level=random.randint(character.level, character.level + 2),
                    max_health=random.randint(20, 50),
                    health=random.randint(20, 50),
                    attack_damage_min=random.randint(3, 8),
                    attack_damage_max=random.randint(9, 15),
                    defense=random.randint(3, 10),
                    description=f"Um(a) hostil {target} que você decidiu atacar.",
                )
                if not hasattr(game_state, "combat") or not game_state.combat:
                    game_state.combat = {
                        "enemy": enemy,
                        "round": 1,
                        "log": [f"Você iniciou combate com {target}!"],
                    }
                    return {
                        "success": True,
                        "message": f"Você atacou {target} e iniciou um combate! Prepare-se para lutar!",
                        "combat": True,
                    }
            else:
                enemy_types = [
                    "Walker Lento",
                    "Corredor Ágil",
                    "Devorador Inchado",
                    "Cão Infectado Raivoso",
                    "Saqueador Oportunista",
                    "Membro de Gangue Brutal",
                    "Rato Mutante Gigante",
                ]
                enemy_name = random.choice(enemy_types)
                enemy = Enemy(
                    name=enemy_name,
                    level=random.randint(character.level, character.level + 2),
                    max_health=random.randint(20, 50),
                    health=random.randint(20, 50),
                    attack_damage_min=random.randint(3, 8),
                    attack_damage_max=random.randint(9, 15),
                    defense=random.randint(3, 10),
                    description=f"Um(a) hostil {enemy_name} que apareceu de repente.",
                )
                if not hasattr(game_state, "combat") or not game_state.combat:
                    game_state.combat = {
                        "enemy": enemy,
                        "round": 1,
                        "log": [f"Um(a) {enemy_name} apareceu e você o(a) atacou!"],
                    }
                    return {
                        "success": True,
                        "message": f"Você procurou por inimigos e encontrou um(a) {enemy_name}! Combate iniciado!",
                        "combat": True,
                    }
        details_lower = details.lower() if isinstance(details, str) else ""
        if (
            "mapa" in details_lower
            or "onde estou" in details_lower
            or "localização" in details_lower
        ):
            has_map_item = False
            if hasattr(character, "inventory"):
                map_items = [
                    "Mapa",
                    "Fragmento de Mapa",
                    "Bússola",
                    "GPS Quebrado",
                ]
                has_map_item = any(item in character.inventory for item in map_items)
            if has_map_item:
                if hasattr(game_state, "coordinates") and hasattr(
                    game_state, "world_map"
                ):
                    coords = game_state.coordinates
                    known_locations = []
                    if hasattr(game_state, "visited_locations"):
                        for loc_id, loc_info in game_state.visited_locations.items():
                            if loc_id in game_state.world_map["locations"]:
                                loc_coords = game_state.world_map["locations"][
                                    loc_id
                                ].get("coordinates", {})
                                distance = (
                                    (loc_coords.get("x", 0) - coords.get("x", 0)) ** 2
                                    + (loc_coords.get("y", 0) - coords.get("y", 0)) ** 2
                                ) ** 0.5
                                if distance <= 2:
                                    known_locations.append(
                                        f"{loc_info['name']} ({loc_coords.get('x', 0)}, {loc_coords.get('y', 0)})"
                                    )
                    return {
                        "success": True,
                        "message": f"Você consulta seu mapa. Você está em {game_state.current_location}, nas coordenadas ({coords.get('x', 0)}, {coords.get('y', 0)}). "
                        + f"Locais próximos que você conhece: {', '.join(known_locations) if known_locations else 'nenhum além deste'}.",
                    }
                return {
                    "success": True,
                    "message": f"Você consulta seu mapa. Você está em {game_state.current_location}.",
                }
            return {
                "success": False,
                "message": "Você não tem um mapa ou bússola para determinar sua localização exata. Você sabe que está em "
                + f"{game_state.current_location}, mas não consegue identificar suas coordenadas.",
            }
        influence_keywords = [
            "exigir",
            "convencer",
            "persuadir",
            "intimidar",
            "forçar",
            "ameaçar",
        ]
        target_object_keywords = ["portão", "sair", "passagem"]
        attempting_influence = any(kw in details_lower for kw in influence_keywords)
        targeting_exit_action = any(
            kw in details_lower for kw in target_object_keywords
        )
        if attempting_influence and game_state.npcs_present:
            targeted_npc_name: Optional[str] = None
            for npc_name_in_scene in game_state.npcs_present:
                if npc_name_in_scene.lower() in details_lower:
                    targeted_npc_name = npc_name_in_scene
                    break
            if (
                not targeted_npc_name
                and "velho" in details_lower
                and targeting_exit_action
            ):
                if "Velho Sobrevivente Cansado" in game_state.npcs_present:
                    targeted_npc_name = "Velho Sobrevivente Cansado"
            if targeted_npc_name:
                npc_details = game_state.known_npcs.get(targeted_npc_name)
                if not npc_details:
                    return {
                        "success": False,
                        "message": f"Não tenho detalhes suficientes sobre {targeted_npc_name}.",
                    }
                contest_stat = "charisma"
                contest_type_message = "tentativa de intimidação"
                if "persuadir" in details_lower or "convencer" in details_lower:
                    contest_type_message = "tentativa de persuasão"
                elif "forçar" in details_lower:
                    contest_stat = "strength"
                    contest_type_message = "tentativa de forçar"
                player_modifier = calculate_attribute_modifier(
                    character.attributes.get(contest_stat, 10)
                )
                player_roll_result = roll_dice(1, 20, player_modifier)
                player_roll_total = player_roll_result["total"]
                npc_level = npc_details.get("level", 1)
                npc_personality = npc_details.get("personality", "Neutro").lower()
                base_dc = 10 + npc_level
                if "cansado" in npc_personality:
                    base_dc -= 1
                if "apavorada" in npc_personality:
                    base_dc -= 2
                if "desconfiado" in npc_personality:
                    base_dc += 2
                if "brutal" in npc_personality:
                    base_dc += 3
                npc_dc = max(5, base_dc)
                mechanical_outcome_message = ""
                if player_roll_total >= npc_dc:
                    mechanical_outcome_message = (
                        f"Sua {contest_type_message} contra {targeted_npc_name} teve sucesso! "
                        f"(Rolagem: {player_roll_total} vs DC: {npc_dc}). "
                        f"{targeted_npc_name} parece reconsiderar..."
                    )
                else:
                    mechanical_outcome_message = (
                        f"Sua {contest_type_message} contra {targeted_npc_name} falhou. "
                        f"(Rolagem: {player_roll_total} vs DC: {npc_dc}). "
                        f"{targeted_npc_name} não se convenceu ou resistiu à sua tentativa."
                    )
                return {
                    "success": True,
                    "message": mechanical_outcome_message,
                    "action_performed": "social_contest_resolved",
                }
        return self.ai_response("custom", details, character, game_state)


class UnknownActionHandler(ActionHandler):
    """Handler for unknown actions."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        return self.ai_response("unknown", details, character, game_state)


class SkillActionHandler(ActionHandler):
    """Handler for 'skill' action."""

    def __init__(self) -> None:
        """Initialize the skill handler."""
        self.skill_manager = SkillManager()

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        if not details:
            available_skills = self.skill_manager.get_available_skills(character)
            skill_names = [skill.name for skill in available_skills]
            return {
                "success": True,
                "message": f"Habilidades disponíveis: {', '.join(skill_names) if skill_names else 'Nenhuma'}",  # Traduzido
            }
        skill_id = details.lower().replace(" ", "_")
        target = None
        if hasattr(game_state, "combat") and game_state.combat:
            target = game_state.combat.get("enemy")
        result = self.skill_manager.use_skill(character, skill_id, target)
        if result["success"]:
            if (
                hasattr(game_state, "combat")
                and game_state.combat
                and "log" in game_state.combat
            ):
                game_state.combat["log"].append(result["message"])
            if target and hasattr(game_state, "combat") and game_state.combat:
                log_entries_from_effects = self._apply_combat_effects(
                    result, game_state, character
                )
                if "log" in game_state.combat:
                    game_state.combat["log"].extend(log_entries_from_effects)
        return result

    @staticmethod
    def _apply_combat_effects(
        result: Dict[str, Any], game_state: Any, character: Character
    ) -> List[str]:
        combat_log_entries = []
        if not game_state.combat or not game_state.combat.get("enemy"):
            return combat_log_entries
        enemy = game_state.combat["enemy"]
        raw_effects = result.get("raw_effects", [])
        for effect_data in raw_effects:
            target_entity: Optional[Any] = None
            target_name: str = "Desconhecido"  # Traduzido
            effect_target_type = effect_data.get("target")
            if effect_target_type == "enemy":
                if enemy:
                    target_entity = enemy
                    target_name = enemy.name
                else:
                    combat_log_entries.append(
                        "Habilidade mira um inimigo, mas nenhum inimigo está presente para afetar."  # Traduzido
                    )
                    continue
            elif effect_target_type == "self":
                target_entity = character
                target_name = character.name
            if target_entity:
                effect_type = effect_data.get("type")
                amount = effect_data.get("amount", 0)
                if effect_type == "damage" and hasattr(target_entity, "health"):
                    skill_damage_roll = roll_dice(1, amount, 0)
                    actual_damage = skill_damage_roll["total"]
                    actual_damage = max(
                        1, actual_damage - getattr(target_entity, "defense", 0)
                    )
                    target_entity.health = max(0, target_entity.health - actual_damage)
                    combat_log_entries.append(
                        f"{target_name} sofreu {actual_damage} de {effect_type} da habilidade!"  # Traduzido
                    )
                    if target_entity.health <= 0:
                        combat_log_entries.append(
                            f"{target_name} foi derrotado(a)!"
                        )  # Traduzido
                elif effect_type == "heal" and effect_data.get("target") == "self":
                    old_hp = character.attributes.get("current_hp", 0)
                    max_hp = character.attributes.get("max_hp", old_hp)
                    heal_amount_from_skill = amount
                    character.attributes["current_hp"] = min(old_hp + amount, max_hp)
                    healed_amount = character.attributes["current_hp"] - old_hp
                    combat_log_entries.append(
                        f"{character.name} curou {healed_amount} HP."  # Traduzido
                    )
                elif effect_type == "status":
                    stat_mods = effect_data.get("stat_modifier", {})
                    duration = effect_data.get("duration", 0)
                    combat_log_entries.append(
                        f"{target_name} é afetado(a) por um status: {stat_mods} por {duration} turnos."  # Traduzido
                    )
        return combat_log_entries


class CraftActionHandler(ActionHandler):
    """Handler for 'craft' action."""

    def __init__(self):
        from utils.item_generator import ItemGenerator

        self.item_generator = ItemGenerator(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        )
        self.skill_manager = SkillManager()

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        if not details:
            available_crafts = []
            for recipe_id, recipe_data in CRAFTING_RECIPES.items():
                skill_req = recipe_data.get("skill_required")
                if skill_req:
                    skill_id_req, skill_level_req = skill_req
                    if skill_id_req not in character.skills:
                        continue
                available_crafts.append(f"{recipe_data['name']} (ID: {recipe_id})")
            if not available_crafts:
                return {
                    "success": True,
                    "message": "Você não conhece nenhuma receita de criação ou não possui as habilidades necessárias para as conhecidas.",  # Traduzido
                }
            return {
                "success": True,
                "message": "Você pode tentar criar: "
                + ", ".join(available_crafts)
                + ". Use 'craft [ID da receita]'.",  # Traduzido
            }
        recipe_id_to_craft = details.strip().lower()
        recipe = CRAFTING_RECIPES.get(recipe_id_to_craft)
        if not recipe:
            return {
                "success": False,
                "message": f"Receita '{recipe_id_to_craft}' não encontrada.",  # Traduzido
            }
        skill_req = recipe.get("skill_required")
        if skill_req:
            skill_id_req, skill_level_req = skill_req
            if skill_id_req not in character.skills:
                skill_obj = self.skill_manager.available_skills.get(skill_id_req)
                skill_display_name = skill_obj.name if skill_obj else skill_id_req
                return {
                    "success": False,
                    "message": f"Você precisa aprender a habilidade '{skill_display_name}' para criar isto.",  # Traduzido
                }
        required_components = recipe.get("components", {})
        inventory_copy = character.inventory[:]
        missing_components = []
        components_to_remove_indices = {}
        for comp_id_ref, quantity_needed in required_components.items():
            found_quantity = 0
            indices_for_this_component = []
            for i, inv_item_obj in enumerate(inventory_copy):
                item_name_in_inv = ""
                if isinstance(inv_item_obj, str):
                    item_name_in_inv = inv_item_obj
                elif isinstance(inv_item_obj, dict) and "name" in inv_item_obj:
                    item_name_in_inv = inv_item_obj["name"]
                if item_name_in_inv.lower() == comp_id_ref.lower():
                    indices_for_this_component.append(i)
                    found_quantity += 1
                    if found_quantity >= quantity_needed:
                        break
            if found_quantity < quantity_needed:
                missing_components.append(
                    f"{comp_id_ref} (precisa de {quantity_needed}, tem {found_quantity})"  # Traduzido
                )
            else:
                components_to_remove_indices[comp_id_ref] = sorted(
                    indices_for_this_component[:quantity_needed], reverse=True
                )
        if missing_components:
            return {
                "success": False,
                "message": "Componentes faltando: "
                + ", ".join(missing_components),  # Traduzido
            }
        for comp_id_ref, indices in components_to_remove_indices.items():
            for index_to_remove in indices:
                character.inventory.pop(index_to_remove)
        output_item_name = recipe["name"]
        output_quantity = recipe.get("output_quantity", 1)
        for _ in range(output_quantity):
            character.inventory.append(output_item_name)
        return {
            "success": True,
            "message": f"Você criou com sucesso {output_quantity}x {output_item_name}!",  # Traduzido
        }


# Action handler factory
def get_action_handler(action: str) -> ActionHandler:
    """
    Get the appropriate action handler for the given action.

    Args:
        action: Action name

    Returns:
        Handler for the action
    """
    action_handlers = {
        "move": MoveActionHandler(),
        "look": LookActionHandler(),
        "talk": TalkActionHandler(),
        "search": SearchActionHandler(),
        "attack": AttackActionHandler(),
        "use_item": UseItemActionHandler(),
        "flee": FleeActionHandler(),
        "rest": RestActionHandler(),
        "custom": CustomActionHandler(),
        "skill": SkillActionHandler(),
        "craft": CraftActionHandler(),
    }
    return action_handlers.get(action, UnknownActionHandler())
