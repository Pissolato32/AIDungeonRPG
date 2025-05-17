import logging
import os
import random
from typing import Any, Dict, List, Optional  # Added List

from core.enemy import Enemy  # Import Enemy class
from core.models import Character
# Direct import for generate_quest
from utils.quest_generator import generate_quest

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
            "message": f"The action '{
                details if details else 'unknown'}' is not recognized or not implemented.",
        }

    def ai_response(self,
                    action: str,
                    details: str,
                    character: "Character",
                    game_state: Any) -> Dict[str,
                                             Any]:
        """Fallback AI response if a specific handler doesn't fully process."""
        return {
            "success": False,
            "message": f"The action '{details}' is not recognized or not implemented.",
        }

    def log_action(self, action: str, character: "Character") -> None:
        """Log the action performed by the character."""
        logger.info(f"{character.name} performed action: {action}")

    def validate_action(self, action: str) -> bool:
        """Validate the action before processing."""
        return action in self.VALID_ACTIONS

    def handle_action(self,
                      action: str,
                      details: str,
                      character: "Character",
                      game_state: Any) -> Dict[str,
                                               Any]:
        """Handle the action based on its type."""
        if not self.validate_action(action):
            logger.warning(f"Invalid action attempted: {action}")
            return {"success": False, "message": f"Invalid action '{action}'."}

        self.log_action(action, character)
        return self.handle(details, character, game_state)


class MoveActionHandler(ActionHandler):
    """Handler for the 'move' action."""

    def handle(
        self, details: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        # Init world generator
        data_dir = os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)),
            "data")
        world_generator = WorldGenerator(data_dir)

        destination = details.strip().lower() if isinstance(details, str) else ""
        current_location_id = game_state.location_id
        directions = ["north", "south", "east", "west"]

        # Normalize input
        normalized_direction: Optional[str] = next(
            (d for d in directions if d in destination), None
        )

        # Process world map
        if (
            not hasattr(game_state, "world_map")
            or "locations" not in game_state.world_map
        ):
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
            elif (
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
            game_state.world_map["locations"][new_location["id"]
                                              ] = new_location
            current_location.setdefault(
                "connections",
                {})[normalized_direction] = (
                new_location["id"])
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
                    "message": f"You move to {
                        next_location['name']}. {
                        next_location['description']}",
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
                "message": f"You arrive at {
                    next_location['name']}. {
                    next_location['description']}",
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
        if target and hasattr(game_state,
                              "npcs_present") and game_state.npcs_present:
            # Verifica se o alvo está entre os NPCs presentes
            npc_name = next(
                (npc for npc in game_state.npcs_present if npc.lower() == target), None)

            if npc_name:
                npc_details = self.get_npc_details(
                    npc_name, character, game_state)

                return {
                    "success": True,
                    "message": (
                        f"You observe {npc_name} closely. " f"{
                            npc_details.get(
                                'race',
                                'A humanoid')} who works as a {
                            npc_details.get(
                                'profession',
                                'unknown')}. " f"{npc_name} seems {
                            npc_details.get(
                                'personality',
                                'ordinary')}. " f"By their appearance and posture, you estimate they are about level {
                                    npc_details.get(
                                        'level',
                                        '?')}."),
                }

        # Caso contrário, executa a resposta padrão do cenário
        return self.ai_response("look", details, character, game_state)

    def get_npc_details(
        self, npc_name: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        """
        Placeholder para obter os detalhes de um NPC.
        Essa função deve ser implementada de acordo com seu sistema de NPCs.
        """
        return {
            "race": "Human",
            "profession": "merchant",
            "personality": "friendly",
            "level": 3,
        }


class TalkActionHandler(ActionHandler):
    """Handler for 'talk' action."""

    def handle(
        self, details: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        # If the player specified an NPC to talk to
        if details and details.strip():
            # Check if the NPC is present in the location
            npc_name = details.strip()
            if game_state.npcs_present and any(
                    npc.lower() == npc_name.lower() for npc in game_state.npcs_present):
                # Find the exact name of the NPC (preserving case)
                npc_name = next(
                    npc
                    for npc in game_state.npcs_present
                    if npc.lower() == npc_name.lower()
                )

                # Check if this NPC is already known
                if (
                    hasattr(game_state, "known_npcs")
                    and npc_name in game_state.known_npcs
                ):
                    # Retrieve information about the already known NPC
                    npc_details = game_state.known_npcs[npc_name]

                    # Update the interaction count
                    npc_details["interactions"] = npc_details.get(
                        "interactions", 0) + 1

                    # Use the details to enrich the AI response
                    result = self.ai_response(
                        "talk", details, character, game_state)

                    # Add NPC information to the response based on the
                    # familiarity level
                    if "message" in result:
                        if npc_details["interactions"] <= 2:
                            result["message"] += f"\n\nYou recognize {npc_name}, a {
                                npc_details['race']} {
                                npc_details['profession']}."
                        else:
                            # More details for NPCs the player has interacted
                            # with multiple times
                            result["message"] += f"\n\n{npc_name} smiles at a familiar face. As an experienced {
                                npc_details['profession']}, {npc_name} has many stories to tell."

                            # Add a hint about quests if the NPC has any
                            if (npc_details.get("quests")
                                    and random.random() < 0.7):  # 70% chance
                                result["message"] += f" {npc_name} mentions needing help with '{
                                    random.choice(
                                        npc_details['quests'])}'."

                    # Update the NPC record
                    game_state.known_npcs[npc_name] = npc_details

                    return result
                # First interaction with this NPC
                npc_details = self.get_npc_details(
                    npc_name, character, game_state)

                # Use the details to enrich the AI response
                result = self.ai_response(
                    "talk", details, character, game_state)

                # Add NPC information to the response
                if "message" in result:
                    result["message"] += f"\n\nYou notice that {npc_name} is a {
                        npc_details['race']} {
                        npc_details['profession']}."

                    # Add a hint about the NPC's knowledge or quests
                    if npc_details.get("knowledge"):
                        result[
                            "message"
                        ] += f" It seems that {npc_name} knows about {', '.join(npc_details['knowledge'][:2])}."

                    if npc_details.get("quests"):
                        result["message"] += f" {npc_name} mentions something about '{
                            npc_details['quests'][0]}'."

                # Record the NPC as known
                if hasattr(game_state, "known_npcs"):
                    npc_details["interactions"] = 1
                    game_state.known_npcs[npc_name] = npc_details

                return result

        # Default behavior if no specific NPC is mentioned
        return self.ai_response("talk", details, character, game_state)

    def get_npc_details(
        self, npc_name: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        """
        Placeholder para obter os detalhes de um NPC.
        Essa função deve ser implementada de acordo com seu sistema de NPCs.
        """
        # Example: fetch from game_state.known_npcs or generate dynamically
        return game_state.known_npcs.get(
            npc_name,
            {
                "race": "Unknown Race",
                "profession": "Unknown Profession",
                "personality": "Mysterious",
                "level": character.level,  # Or some other logic
                "knowledge": [],
                "quests": [],
            },
        )


class SearchActionHandler(ActionHandler):
    """Handler for 'search' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        # Check if the player is looking for quests
        details_lower = details.lower() if isinstance(details, str) else ""
        if "quest" in details_lower:
            # Check if there are NPCs present who can offer quests
            if not hasattr(
                    game_state,
                    "npcs_present") or not game_state.npcs_present:
                return {
                    "success": False,
                    "message": "There is no one around who can offer quests at the moment.",
                }

            # Initialize the list of quests if it doesn't exist
            if not hasattr(game_state, "quests"):
                game_state.quests = []

            # Randomly choose an NPC to offer a quest
            quest_giver = random.choice(game_state.npcs_present)

            new_quest = generate_quest(
                location=game_state.current_location,
                difficulty=character.level,
            )

            # Add NPC information to the quest
            new_quest["giver"] = quest_giver
            new_quest["location"] = game_state.current_location

            # Add the quest to the player's list of quests
            game_state.quests.append(new_quest)

            # Return information about the quest
            return {
                "success": True,
                "message": f"{quest_giver} offers a new quest: {
                    new_quest['name']}. {
                    new_quest['description']} Reward: {
                    new_quest['reward_gold']} gold coins.",
            }

        # Default behavior for other searches
        result = self.ai_response("search", details, character, game_state)

        # Record the search results in the current location
        if (
            hasattr(game_state, "visited_locations")
            and game_state.location_id in game_state.visited_locations
        ):
            location_info = game_state.visited_locations[game_state.location_id]
            if "search_results" not in location_info:
                location_info["search_results"] = []

            # Add the search result to the history
            location_info["search_results"].append(
                {"query": details, "result": result.get("message", "")}
            )

        return result


class AttackActionHandler(ActionHandler):
    """Handler for 'attack' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        # Check if the player is trying to attack a specific NPC
        if details and details.strip():
            target = details.strip().lower() if isinstance(details, str) else ""

            # Check if the target is an NPC present
            if game_state.npcs_present and any(
                npc.lower() == target for npc in game_state.npcs_present
            ):
                # Find the exact name of the NPC (preserving case)
                npc_name = next(
                    npc for npc in game_state.npcs_present if npc.lower() == target)

                # Create an enemy based on the NPC
                enemy = Enemy(
                    name=npc_name,
                    level=random.randint(character.level, character.level + 2),
                    max_health=random.randint(
                        20, 50
                    ),  # Use max_health from CombatStats
                    # Use health from CombatStats
                    health=random.randint(20, 50),
                    attack_damage_min=random.randint(3, 8),
                    attack_damage_max=random.randint(9, 15),
                    defense=random.randint(3, 10),
                    description=f"A hostile {npc_name} that you decided to attack.",
                )

                # Start the combat
                if not hasattr(game_state, "combat") or not game_state.combat:
                    game_state.combat = {
                        "enemy": enemy,
                        "round": 1,
                        "log": [f"You initiated combat with {npc_name}!"],
                    }

                    return {
                        "success": True,
                        "message": f"You attacked {npc_name} and started a combat! Get ready to fight!",
                        "combat": True,
                    }

            # If the target is not an NPC present, try to start combat with a
            # random enemy
            enemy_types = [
                "Bandit",
                "Wolf",
                "Goblin",
                "Skeleton",
                "Zombie",
                "Thief",
                "Mercenary",
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
                description=f"A hostile {enemy_name} that appeared suddenly.",
            )

            # Start the combat
            if not hasattr(game_state, "combat") or not game_state.combat:
                game_state.combat = {
                    "enemy": enemy,
                    "round": 1,
                    "log": [f"A {enemy_name} appeared and you attacked it!"],
                }

                return {
                    "success": True,
                    "message": f"You looked for enemies and found a {enemy_name}! Combat initiated!",
                    "combat": True,
                }

        # Default behavior if no specific target is mentioned
        return self.ai_response("attack", details, character, game_state)


class UseItemActionHandler(ActionHandler):
    """Handler for 'use_item' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        # Import the item generator
        from utils.item_generator import ItemGenerator

        # Initialize the item generator
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
                "message": "You don't have that item in your inventory.",
            }

        # Normalize the item name for comparison
        item_name_query = details.strip() if isinstance(details, str) else ""

        # Check if the item is in the inventory
        item_found = False
        item_index = -1
        item_data = None

        # Look for the exact item or partial match
        for i, inv_item in enumerate(character.inventory):
            if isinstance(
                inv_item, str) and (
                inv_item.lower() == item_name_query.lower() or (
                    item_name_query and inv_item.lower() in item_name_query.lower())):
                item_found = True
                item_index = i
                actual_item_name = (
                    inv_item  # Use the exact item name from the inventory
                )

                # Check if the item exists in the database
                item_data = item_generator.get_item_by_name(actual_item_name)
                break
            elif (
                isinstance(inv_item, dict)
                and inv_item.get("name", "").lower() == item_name_query.lower()
            ):
                item_found = True
                item_index = i
                actual_item_name = inv_item.get("name")
                item_data = inv_item
                break

        if not item_found:
            return {
                "success": False,
                "message": f"You don't have '{item_name_query}' in your inventory.",
            }

        # If the item was found in the database, use its attributes
        if item_data:
            item_type = item_data.get("type", "")
            item_subtype = item_data.get("subtype", "")
            item_description = item_data.get("description", "")

            # Logic for different item types
            if item_type == "weapon":
                # Equip weapon
                if not hasattr(character,
                               "equipment") or character.equipment is None:
                    character.equipment = {}

                # Store the previously equipped item, if any
                old_item = character.equipment.get("weapon")

                # Equip the new item
                character.equipment["weapon"] = actual_item_name

                # If there was a previously equipped item, put it back in the
                # inventory
                if old_item:
                    character.inventory.append(old_item)

                # Remove the item from the inventory
                character.inventory.pop(item_index)

                # Add attribute bonuses
                damage_info = ""
                if "damage" in item_data:
                    min_damage, max_damage = item_data["damage"]
                    damage_info = f" Damage: {min_damage}-{max_damage}."

                return {
                    "success": True,
                    "message": f"You equipped {actual_item_name}. {damage_info} {item_description} {
                        f'Your {old_item} was stored in the inventory.' if old_item else ''}",
                }

            if item_type == "armor":
                # Equip armor
                if not hasattr(character,
                               "equipment") or character.equipment is None:
                    character.equipment = {}

                # Determine the slot based on the subtype
                slot = "armor"
                if item_subtype == "helmet":
                    slot = "helmet"
                elif item_subtype == "shield":
                    slot = "shield"
                elif item_subtype in ["boots", "gauntlets"]:
                    slot = item_subtype

                # Store the previously equipped item, if any
                old_item = character.equipment.get(slot)

                # Equip the new item
                character.equipment[slot] = actual_item_name

                # If there was a previously equipped item, put it back in the
                # inventory
                if old_item:
                    character.inventory.append(old_item)

                # Remove the item from the inventory
                character.inventory.pop(item_index)

                # Add defense bonus
                defense_info = ""
                if "defense" in item_data:
                    defense_info = f" Defense: +{item_data['defense']}."

                return {
                    "success": True,
                    "message": f"You equipped {actual_item_name}. {defense_info} {item_description} {
                        f'Your {old_item} was stored in the inventory.' if old_item else ''}",
                }

            if item_type == "consumable":
                # Use consumable item
                effect = item_data.get("effect", {})
                effect_type = effect.get("type", "")
                effect_value = effect.get("value", 0)

                if effect_type == "health":
                    # Restore HP
                    old_hp = character.health
                    character.health = min(
                        character.health + effect_value, character.max_hp
                    )

                    # Remove the item from the inventory
                    character.inventory.pop(item_index)

                    return {
                        "success": True,
                        "message": f"You used {actual_item_name} and restored {
                            character.health -
                            old_hp} health points. {item_description}",
                    }

                if (
                    effect_type == "stamina"
                ):  # Hunger and thirst are handled by survival_stats
                    # Restore other attributes
                    attr_name = f"current_{effect_type}"
                    max_attr_name = f"max_{effect_type}"

                    if hasattr(character, attr_name) and hasattr(
                        character, max_attr_name
                    ):
                        # For stamina, assuming it's in attributes like hp
                        if effect_type == "stamina":
                            old_value = character.attributes.get(attr_name, 0)
                            max_value = character.attributes.get(
                                max_attr_name, 0)
                            character.attributes[attr_name] = min(
                                old_value + effect_value, max_value
                            )

                    # Remove the item from the inventory
                    character.inventory.pop(item_index)

                    return {
                        "success": True,
                        "message": f"You used {actual_item_name} and feel refreshed. {item_description}",
                    }
                if effect_type in ["hunger", "thirst"]:
                    stat_key = f"current_{effect_type}"
                    max_stat_key = f"max_{effect_type}"
                    old_value = character.survival_stats.get(stat_key, 0)
                    max_value = character.survival_stats.get(
                        max_stat_key, 100
                    )  # Default max if not set
                    character.survival_stats[stat_key] = min(
                        old_value + effect_value, max_value
                    )

                    character.inventory.pop(item_index)
                    return {
                        "success": True,
                        "message": f"You used {actual_item_name} and feel less {effect_type}. {item_description}",
                    }
                # Other effects
                # Remove the item from the inventory
                character.inventory.pop(item_index)

                return {
                    "success": True,
                    "message": f"You used {actual_item_name}. {item_description}",
                }

            if item_type == "quest":
                # Use quest item
                if (
                    item_subtype in ["document", "map", "letter"]
                    and "content" in item_data
                ):
                    return {
                        "success": True,
                        "message": f"You examine {actual_item_name}. {item_description}\n\nContent: {
                            item_data['content']}",
                    }
                return {
                    "success": True,
                    "message": f"You examine {actual_item_name}. {item_description}",
                }

        # Logic for items without specific data
        item_name_lower = actual_item_name.lower() if actual_item_name else ""

        # Health potions
        if any(p in item_name_lower for p in ["potion", "life", "health"]):
            heal_amount = 20  # Adjust based on potion type
            max_hp = character.max_hp
            old_hp = character.health
            character.health = min(old_hp + heal_amount, max_hp)

            # Remove the item from the inventory
            character.inventory.pop(item_index)

            return {
                "success": True,
                "message": f"You used {actual_item_name} and restored {
                    character.health - old_hp} health points. Current HP: {
                    character.health}/{max_hp}.",
            }

        # Equipment (weapons, armor, etc.)
        if isinstance(actual_item_name, str) and any(  # Ensure actual_item_name is str
            eq in actual_item_name.lower()
            for eq in [
                "sword",
                "shield",
                "armor",
                "bow",
                "axe",
                "dagger",
            ]
        ):
            # Determine the equipment type
            equip_type = "weapon"  # Default
            if any(  # Ensure actual_item_name is str
                w in actual_item_name.lower()
                for w in [
                    "sword",
                    "axe",
                    "dagger",
                    "bow",
                ]
            ) and isinstance(actual_item_name, str):
                equip_type = "weapon"
            elif isinstance(actual_item_name, str) and any(
                a in actual_item_name.lower() for a in ["shield"]
            ):
                equip_type = "shield"
            elif isinstance(actual_item_name, str) and any(
                a in actual_item_name.lower() for a in ["armor", "breastplate"]
            ):
                equip_type = "armor"
            elif isinstance(actual_item_name, str) and any(
                h in actual_item_name.lower() for h in ["helmet", "hat"]
            ):
                equip_type = "helmet"

            # Initialize equipment if it doesn't exist
            if not hasattr(
                    character,
                    "equipment") or character.equipment is None:
                character.equipment = {}

            # Store the previously equipped item, if any
            old_item = character.equipment.get(equip_type)

            # Equip the new item
            character.equipment[equip_type] = actual_item_name

            # If there was a previously equipped item, put it back in the
            # inventory
            if old_item:
                character.inventory.append(old_item)

            # Remove the item from the inventory
            character.inventory.pop(item_index)

            return {
                "success": True,
                "message": f"You equipped {actual_item_name}. {
                    f'Your {old_item} was stored in the inventory.' if old_item else ''}",
            }

        # Consumable items (food, drink)
        if isinstance(actual_item_name, str) and any(  # Ensure actual_item_name is str
            f in actual_item_name.lower()
            for f in [
                "food",
                "bread",
                "fruit",
                "meat",
                "water",
                "drink",
            ]
        ):
            # Restore hunger or thirst
            if (
                "current_hunger" in character.survival_stats
                and "max_hunger" in character.survival_stats
            ):
                hunger_restore = 20
                character.survival_stats["current_hunger"] = min(
                    character.survival_stats["current_hunger"] +
                    hunger_restore,
                    character.survival_stats["max_hunger"],
                )

            if (
                "current_thirst" in character.survival_stats
                and "max_thirst" in character.survival_stats
            ):
                thirst_restore = 20
                character.survival_stats["current_thirst"] = min(
                    character.survival_stats["current_thirst"] +
                    thirst_restore,
                    character.survival_stats["max_thirst"],
                )

            # Remove the item from the inventory
            character.inventory.pop(item_index)

            return {
                "success": True,
                "message": f"You consumed {actual_item_name} and feel refreshed.",
            }

        # Throwable items
        details_lower = details.lower() if isinstance(details, str) else ""
        if "throw" in details_lower:
            # Extract the target of the throw
            target = None
            if "at" in details_lower:
                target_part = details_lower.split("at ", 1)[1]
                target = target_part.strip()

            # Remove the item from the inventory
            character.inventory.pop(item_index)

            return {
                "success": True,
                "message": f"You threw {actual_item_name}{
                    f' at {target}' if target else ''}.",
            }

        # For other item types, use the AI response
        result = self.ai_response("use_item", details, character, game_state)

        # If the AI indicates success, remove the item from the inventory
        if result.get("success", False):
            character.inventory.pop(item_index)

        return result


class FleeActionHandler(ActionHandler):
    """Handler for 'flee' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        return self.ai_response("flee", details, character, game_state)


class RestActionHandler(ActionHandler):
    """Handler for 'rest' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        return self.ai_response("rest", details, character, game_state)


class CustomActionHandler(ActionHandler):
    """Handler for 'custom' (freeform) actions."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        details_lower = details.lower() if isinstance(details, str) else ""
        # Check if the player is trying to manage the inventory
        inventory_keywords = [
            "get",
            "collect",
            "store",
            "inventory",
            "pick up",
        ]
        if any(keyword in details_lower for keyword in inventory_keywords):
            # Look for mentioned items
            items_to_add = []

            # Check if specific items are mentioned
            common_items = [
                "sword",
                "shield",
                "potion",
                "dagger",
                "bow",
                "arrow",
                "food",
                "water",
                "coin",
                "scroll",
                "book",
                "map",
                "key",
                "gem",
                "ring",
                "amulet",
                "bag",
                "backpack",
                "rope",
                "torch",
                "lantern",
                "oil",
                "herb",
                "bandage",
                "antidote",
                "flask",
                "bottle",
                "knife",
                "bread",
                "fruit",
                "meat",
            ]

            for item in common_items:
                if item in details_lower:
                    items_to_add.append(item.capitalize())

            # If no specific items were found, but the player seems to want to
            # pick something up
            if not items_to_add and any(
                verb in details.lower() for verb in ["get", "collect", "take"]
            ):
                # Check if there are items in the environment (mentioned in the
                # scene description)
                scene_items: List[str] = []
                if hasattr(game_state, "scene_description"):
                    scene_text = game_state.scene_description.lower()
                    for item in common_items:
                        if item in scene_text and item not in scene_items:
                            scene_items.append(item.capitalize())

                if scene_items:
                    items_to_add = scene_items

            # Add the items to the inventory
            if items_to_add:
                if not hasattr(character, "inventory"):
                    character.inventory = []

                for item in items_to_add:
                    character.inventory.append(item)

                return {
                    "success": True,
                    "message": f"You added the following items to your inventory: {
                        ', '.join(items_to_add)}.",
                }

        # Check if the player is trying to initiate combat
        combat_keywords = [
            "attack",
            "fight",
            "combat",
            "kill",
            "battle",
        ]
        if any(keyword in details_lower for keyword in combat_keywords):
            # Extract possible target from the text
            words = details_lower.split()
            target = None

            # Look for NPCs mentioned in the command
            if game_state.npcs_present:
                for npc in game_state.npcs_present:
                    if npc.lower() in details_lower:
                        target = npc
                        break

            # If a specific target was found
            if target:
                # Create an enemy based on the NPC
                enemy = Enemy(
                    name=target,
                    level=random.randint(character.level, character.level + 2),
                    max_health=random.randint(20, 50),
                    health=random.randint(20, 50),
                    attack_damage_min=random.randint(3, 8),
                    attack_damage_max=random.randint(9, 15),
                    defense=random.randint(3, 10),
                    description=f"A hostile {target} that you decided to attack.",
                )

                # Start the combat
                if not hasattr(game_state, "combat") or not game_state.combat:
                    game_state.combat = {
                        "enemy": enemy,
                        "round": 1,
                        "log": [f"You initiated combat with {target}!"],
                    }

                    return {
                        "success": True,
                        "message": f"You attacked {target} and started a combat! Get ready to fight!",
                        "combat": True,
                    }
            else:
                # Generate a random enemy if no specific target is mentioned
                enemy_types = [
                    "Bandit",
                    "Wolf",
                    "Goblin",
                    "Skeleton",
                    "Zombie",
                    "Thief",
                    "Mercenary",
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
                    description=f"A hostile {enemy_name} that appeared suddenly.",
                )

                # Start the combat
                if not hasattr(game_state, "combat") or not game_state.combat:
                    game_state.combat = {
                        "enemy": enemy, "round": 1, "log": [
                            f"A {enemy_name} appeared and you attacked it!"], }

                    return {
                        "success": True,
                        "message": f"You looked for enemies and found a {enemy_name}! Combat initiated!",
                        "combat": True,
                    }

        # Check if the player is trying to see the map or their location
        details_lower = details.lower() if isinstance(details, str) else ""
        if (
            "map" in details_lower
            or "where am i" in details_lower
            or "location" in details_lower
        ):
            # Check if the player has an item to map with
            has_map_item = False
            if hasattr(character, "inventory"):
                map_items = ["Map", "Map Scroll", "Compass", "Regional Map"]
                has_map_item = any(
                    item in character.inventory for item in map_items)

            if has_map_item:
                # Player has a map, show the current location
                if hasattr(game_state, "coordinates") and hasattr(
                    game_state, "world_map"
                ):
                    coords = game_state.coordinates
                    known_locations = []

                    # List nearby locations the player has already visited
                    for loc_id, loc_info in game_state.visited_locations.items():
                        if loc_id in game_state.world_map:
                            loc_coords = game_state.world_map[loc_id].get(
                                "coordinates", {}
                            )
                            distance = ((loc_coords.get("x", 0) -
                                         coords.get("x", 0)) ** 2 +
                                        (loc_coords.get("y", 0) -
                                         coords.get("y", 0)) ** 2) ** 0.5
                            if distance <= 2:  # Locations up to 2 units away
                                known_locations.append(
                                    f"{loc_info['name']} ({loc_coords.get('x', 0)}, {loc_coords.get('y', 0)})"
                                )

                    return {
                        "success": True,
                        "message": f"You consult your map. You are in {
                            game_state.current_location}, at the coordinates ({
                            coords.get(
                                'x',
                                0)}, {
                            coords.get(
                                'y',
                                0)}). " +
                        f"Nearby locations you know: {
                            ', '.join(known_locations) if known_locations else 'none besides this one'}.",
                    }
                return {
                    "success": True,
                    "message": f"You consult your map. You are in {
                        game_state.current_location}.",
                }
            # Player doesn't have a map
            return {
                "success": False,
                "message": "You don't have a map or compass to determine your exact location. You know you are in "
                + f"{game_state.current_location}, but can't pinpoint your coordinates.",
            }

        # Default behavior for other custom actions
        return self.ai_response("custom", details, character, game_state)


class UnknownActionHandler(ActionHandler):
    """Handler for unknown actions."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        return self.ai_response("unknown", details, character, game_state)


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
        "custom": CustomActionHandler(),  # Add support for freeform actions
    }

    return action_handlers.get(action, UnknownActionHandler())
