import os
import json
import random
import logging
from datetime import datetime
from models import Character, Enemy

logger = logging.getLogger(__name__)

class GameEngine:
    """Game engine for handling game mechanics and state management"""
    
    def __init__(self):
        """Initialize game engine"""
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def save_character(self, user_id, character_data):
        """Save character data to file"""
        if isinstance(character_data, Character):
            character_data = character_data.to_dict()
            
        character_path = os.path.join(self.data_dir, f"character_{user_id}.json")
        
        try:
            with open(character_path, 'w') as f:
                json.dump(character_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving character: {str(e)}")
            return False
    
    def load_character(self, user_id):
        """Load character data from file"""
        character_path = os.path.join(self.data_dir, f"character_{user_id}.json")
        
        if not os.path.exists(character_path):
            return None
            
        try:
            with open(character_path, 'r') as f:
                character_data = json.load(f)
            return character_data
        except Exception as e:
            logger.error(f"Error loading character: {str(e)}")
            return None
    
    def delete_character(self, user_id):
        """Delete character data file"""
        character_path = os.path.join(self.data_dir, f"character_{user_id}.json")
        
        if os.path.exists(character_path):
            try:
                os.remove(character_path)
                return True
            except Exception as e:
                logger.error(f"Error deleting character: {str(e)}")
                return False
        return True
    
    def save_game_state(self, user_id, game_state):
        """Save game state to file"""
        game_state_path = os.path.join(self.data_dir, f"game_state_{user_id}.json")
        
        try:
            with open(game_state_path, 'w') as f:
                json.dump(game_state, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving game state: {str(e)}")
            return False
    
    def load_game_state(self, user_id):
        """Load game state from file"""
        game_state_path = os.path.join(self.data_dir, f"game_state_{user_id}.json")
        
        if not os.path.exists(game_state_path):
            return None
            
        try:
            with open(game_state_path, 'r') as f:
                game_state = json.load(f)
            return game_state
        except Exception as e:
            logger.error(f"Error loading game state: {str(e)}")
            return None
    
    def delete_game_state(self, user_id):
        """Delete game state file"""
        game_state_path = os.path.join(self.data_dir, f"game_state_{user_id}.json")
        
        if os.path.exists(game_state_path):
            try:
                os.remove(game_state_path)
                return True
            except Exception as e:
                logger.error(f"Error deleting game state: {str(e)}")
                return False
        return True
    
    def process_action(self, action, action_details, character, game_state, groq_client):
        """Process player action and update game state"""
        # Ensure messages list exists
        if "messages" not in game_state:
            game_state["messages"] = []
        
        # Check if in combat
        if game_state.get("combat"):
            # Can't perform non-combat actions in combat
            if action not in ["attack", "use_item", "flee"]:
                return {
                    "success": False,
                    "message": "You are in combat! You must attack, use an item, or flee."
                }
        
        # Check stamina for actions that require it
        stamina_cost = self._get_stamina_cost(action)
        if stamina_cost > 0:
            if character["current_stamina"] < stamina_cost:
                return {
                    "success": False,
                    "message": f"Not enough stamina to {action}. You need {stamina_cost} stamina."
                }
            # Deduct stamina
            character["current_stamina"] -= stamina_cost
        
        # Process specific actions
        if action == "move":
            return self._process_move(action_details, character, game_state, groq_client)
        elif action == "look":
            return self._process_look(action_details, character, game_state, groq_client)
        elif action == "talk":
            return self._process_talk(action_details, character, game_state, groq_client)
        elif action == "search":
            return self._process_search(character, game_state, groq_client)
        elif action == "attack":
            return self._process_attack(action_details, character, game_state, groq_client)
        elif action == "flee":
            return self._process_flee(character, game_state)
        elif action == "use_item":
            return self._process_use_item(action_details, character, game_state)
        else:
            # For custom actions, use Groq API to determine outcome
            return self._process_custom_action(action, action_details, character, game_state, groq_client)
    
    def _get_stamina_cost(self, action):
        """Get stamina cost for an action"""
        stamina_costs = {
            "move": 1,
            "search": 2,
            "attack": 3,
            "flee": 2
        }
        return stamina_costs.get(action, 0)
    
    def _process_move(self, direction, character, game_state, groq_client):
        """Process move action"""
        # Get current location
        current_location = game_state.get("current_location", "Unknown")
        
        # Get possible directions from Groq
        prompt = f"""
        The player is currently at: {current_location}
        Game state: {json.dumps(game_state)}
        
        The player wants to move {direction}.
        
        Generate a JSON response with:
        1. Whether the move is possible (success: true/false)
        2. A new location name if successful
        3. A detailed description of what the player sees
        4. Any NPCs present in the new location
        5. Any events happening in the new location
        6. A message to display to the player
        7. Whether this should trigger a combat encounter (random chance, more likely in dangerous areas)
        
        JSON format:
        {{
            "success": true/false,
            "new_location": "Location Name",
            "description": "Detailed description of the new location",
            "npcs": ["NPC1", "NPC2"],
            "events": ["Event1", "Event2"],
            "message": "Message to player",
            "combat": true/false
        }}
        
        If the move is not possible, only include:
        {{
            "success": false,
            "message": "Reason why move is not possible"
        }}
        """
        
        # Get response from Groq
        response = groq_client.generate_response(prompt, character["name"])
        
        try:
            result = json.loads(response)
            
            if result.get("success"):
                # Update game state with new location info
                game_state["current_location"] = result.get("new_location")
                game_state["scene_description"] = result.get("description")
                game_state["npcs_present"] = result.get("npcs", [])
                game_state["events"] = result.get("events", [])
                
                # Add message to history
                game_state["messages"].append(result.get("message"))
                
                # Check if combat should be triggered
                if result.get("combat"):
                    combat_result = self._initiate_combat(character, game_state, groq_client)
                    if combat_result.get("success"):
                        result["message"] += " " + combat_result.get("message")
                
                # Recover some stamina after successful move
                character["current_stamina"] = min(character["max_stamina"], 
                                                  character["current_stamina"] + 1)
            
            return result
        except Exception as e:
            logger.error(f"Error processing move: {str(e)}")
            return {
                "success": False,
                "message": "Sorry, there was an error processing your movement."
            }
    
    def _process_look(self, target, character, game_state, groq_client):
        """Process look action to examine something"""
        current_location = game_state.get("current_location", "Unknown")
        scene_description = game_state.get("scene_description", "")
        npcs = game_state.get("npcs_present", [])
        
        prompt = f"""
        The player is currently at: {current_location}
        Scene description: {scene_description}
        NPCs present: {', '.join(npcs)}
        
        The player wants to look at: {target}
        
        Generate a JSON response with:
        1. Whether the target is found (success: true/false)
        2. A detailed description of what the player sees when looking at the target
        3. Any special observations or clues the player might notice
        4. A message to display to the player
        
        JSON format:
        {{
            "success": true/false,
            "description": "Detailed description of what the player sees",
            "observations": ["Observation1", "Observation2"],
            "message": "Message to player"
        }}
        
        If the target is not found, only include:
        {{
            "success": false,
            "message": "You don't see that here."
        }}
        """
        
        # Get response from Groq
        response = groq_client.generate_response(prompt, character["name"])
        
        try:
            result = json.loads(response)
            
            if result.get("success"):
                # Add message to history
                game_state["messages"].append(result.get("message"))
            
            return result
        except Exception as e:
            logger.error(f"Error processing look: {str(e)}")
            return {
                "success": False,
                "message": "Sorry, there was an error processing your action."
            }
    
    def _process_talk(self, npc_name, character, game_state, groq_client):
        """Process talking to an NPC"""
        current_location = game_state.get("current_location", "Unknown")
        npcs = game_state.get("npcs_present", [])
        
        # Check if NPC is present
        npc_present = any(npc.lower() == npc_name.lower() for npc in npcs)
        if not npc_present:
            return {
                "success": False,
                "message": f"There is no {npc_name} here to talk to."
            }
        
        prompt = f"""
        The player is currently at: {current_location}
        The player character is: {character["name"]}, a level {character["level"]} {character["race"]} {character["class"]}
        
        The player wants to talk to: {npc_name}
        
        Generate a JSON response with:
        1. Success true
        2. The NPC's response as dialogue
        3. Any information or quests the NPC might offer
        4. Any changes to the game state (new quests, information learned)
        5. A message to display to the player
        
        JSON format:
        {{
            "success": true,
            "dialogue": "NPC's dialogue response",
            "information": ["Info1", "Info2"],
            "quests": [{{
                "name": "Quest Name",
                "description": "Quest Description"
            }}],
            "message": "Message to player"
        }}
        """
        
        # Get response from Groq
        response = groq_client.generate_response(prompt, character["name"])
        
        try:
            result = json.loads(response)
            
            if result.get("success"):
                # Add message to history
                game_state["messages"].append(result.get("message"))
                
                # Add quests if provided
                if "quests" in result and isinstance(result["quests"], list):
                    if "quests" not in game_state:
                        game_state["quests"] = []
                    
                    for quest in result["quests"]:
                        if isinstance(quest, dict) and "name" in quest and "description" in quest:
                            # Check if quest already exists
                            existing = any(q.get("name") == quest["name"] for q in game_state.get("quests", []))
                            if not existing:
                                quest["status"] = "active"
                                quest["progress"] = 0
                                game_state["quests"].append(quest)
            
            return result
        except Exception as e:
            logger.error(f"Error processing talk: {str(e)}")
            return {
                "success": False,
                "message": "Sorry, there was an error processing your conversation."
            }
    
    def _process_search(self, character, game_state, groq_client):
        """Process searching the current location"""
        current_location = game_state.get("current_location", "Unknown")
        scene_description = game_state.get("scene_description", "")
        
        prompt = f"""
        The player is currently at: {current_location}
        Scene description: {scene_description}
        
        The player is searching the area thoroughly.
        
        Generate a JSON response with:
        1. Whether the player finds anything (success: true/false)
        2. A list of items found if successful
        3. Any gold found
        4. Any hidden passages or secrets discovered
        5. A message to display to the player
        6. Whether this should trigger a combat encounter (small random chance)
        
        JSON format:
        {{
            "success": true/false,
            "items": ["Item1", "Item2"],
            "gold": 0-25,
            "secrets": ["Secret1", "Secret2"],
            "message": "Message to player",
            "combat": true/false
        }}
        
        If nothing is found, set success to false and provide an appropriate message.
        """
        
        # Get response from Groq
        response = groq_client.generate_response(prompt, character["name"])
        
        try:
            result = json.loads(response)
            
            if result.get("success"):
                # Add found items to inventory
                if "items" in result and isinstance(result["items"], list):
                    for item in result["items"]:
                        character["inventory"].append(item)
                
                # Add gold
                if "gold" in result and isinstance(result["gold"], (int, float)):
                    character["gold"] += result["gold"]
                
                # Add any secrets to game state
                if "secrets" in result and isinstance(result["secrets"], list):
                    if "secrets" not in game_state:
                        game_state["secrets"] = []
                    
                    for secret in result["secrets"]:
                        if secret not in game_state["secrets"]:
                            game_state["secrets"].append(secret)
                
                # Add message to history
                game_state["messages"].append(result.get("message"))
                
                # Check if combat should be triggered
                if result.get("combat"):
                    combat_result = self._initiate_combat(character, game_state, groq_client)
                    if combat_result.get("success"):
                        result["message"] += " " + combat_result.get("message")
            else:
                # Add message to history even if nothing found
                game_state["messages"].append(result.get("message"))
            
            return result
        except Exception as e:
            logger.error(f"Error processing search: {str(e)}")
            return {
                "success": False,
                "message": "Sorry, there was an error processing your search."
            }
    
    def _initiate_combat(self, character, game_state, groq_client):
        """Initiate a combat encounter"""
        current_location = game_state.get("current_location", "Unknown")
        
        prompt = f"""
        The player is currently at: {current_location}
        The player character is: {character["name"]}, a level {character["level"]} {character["race"]} {character["class"]}
        
        Generate a random enemy appropriate for this location and the player's level.
        
        Generate a JSON response with:
        1. The enemy's name
        2. A description of the enemy
        3. The enemy's stats (HP, attack damage, etc.)
        4. A message describing the encounter
        
        JSON format:
        {{
            "enemy": {{
                "name": "Enemy Name",
                "description": "Enemy Description",
                "level": 1-{character["level"]+2},
                "max_hp": 10-50,
                "current_hp": same as max_hp,
                "attack_damage": [min, max],
                "defense": 0-5,
                "experience_reward": 20-100,
                "gold_reward": [min, max],
                "loot_table": ["Item1", "Item2"]
            }},
            "message": "Message describing the encounter"
        }}
        """
        
        # Get response from Groq
        response = groq_client.generate_response(prompt, character["name"])
        
        try:
            result = json.loads(response)
            
            if "enemy" in result and isinstance(result["enemy"], dict):
                # Create combat state
                game_state["combat"] = {
                    "enemy": result["enemy"],
                    "round": 1,
                    "player_turn": True,
                    "log": [result.get("message")]
                }
                
                return {
                    "success": True,
                    "message": result.get("message"),
                    "combat_started": True,
                    "enemy": result["enemy"]
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to initialize combat encounter."
                }
        except Exception as e:
            logger.error(f"Error initiating combat: {str(e)}")
            return {
                "success": False,
                "message": "Sorry, there was an error initiating combat."
            }
    
    def _process_attack(self, attack_type, character, game_state, groq_client):
        """Process a combat attack"""
        # Check if in combat
        if not game_state.get("combat"):
            return {
                "success": False,
                "message": "You are not in combat!"
            }
        
        # Check if it's player's turn
        if not game_state["combat"].get("player_turn", True):
            return {
                "success": False,
                "message": "It's not your turn to attack!"
            }
        
        # Process player attack
        enemy = game_state["combat"]["enemy"]
        
        # Calculate damage based on character stats and attack type
        base_damage = 0
        stamina_cost = 0
        
        if attack_type == "light":
            base_damage = 3 + (character["dexterity"] // 3)
            stamina_cost = 1
        elif attack_type == "heavy":
            base_damage = 6 + (character["strength"] // 2)
            stamina_cost = 3
        else:  # Basic attack
            base_damage = 4 + (character["strength"] // 3)
            stamina_cost = 2
        
        # Check if enough stamina
        if character["current_stamina"] < stamina_cost:
            return {
                "success": False,
                "message": f"Not enough stamina for a {attack_type} attack! You need {stamina_cost} stamina."
            }
        
        # Deduct stamina
        character["current_stamina"] -= stamina_cost
        
        # Add randomness to damage (±20%)
        damage_variance = random.uniform(0.8, 1.2)
        damage = round(base_damage * damage_variance)
        
        # Apply damage to enemy
        enemy_hp_before = enemy["current_hp"]
        enemy["current_hp"] = max(0, enemy["current_hp"] - damage)
        
        # Create attack message
        attack_message = f"You perform a {attack_type} attack on the {enemy['name']} for {damage} damage!"
        
        # Add to combat log
        game_state["combat"]["log"].append(attack_message)
        
        # Check if enemy defeated
        if enemy["current_hp"] <= 0:
            # Combat won
            victory_result = self._process_combat_victory(character, game_state, enemy)
            
            return {
                "success": True,
                "damage_dealt": damage,
                "enemy_hp_before": enemy_hp_before,
                "enemy_hp_after": 0,
                "message": attack_message + " " + victory_result.get("message", ""),
                "combat_over": True,
                "victory": True,
                "rewards": victory_result.get("rewards", {})
            }
        
        # Enemy turn
        enemy_attack_result = self._process_enemy_attack(character, game_state)
        
        # Increment round
        game_state["combat"]["round"] += 1
        
        return {
            "success": True,
            "damage_dealt": damage,
            "enemy_hp_before": enemy_hp_before,
            "enemy_hp_after": enemy["current_hp"],
            "message": attack_message,
            "enemy_attack": enemy_attack_result.get("message", ""),
            "player_hp": character["current_hp"],
            "combat_over": enemy_attack_result.get("combat_over", False),
            "victory": False
        }
    
    def _process_enemy_attack(self, character, game_state):
        """Process enemy's attack on player"""
        enemy = game_state["combat"]["enemy"]
        
        # Calculate enemy damage
        min_damage, max_damage = enemy["attack_damage"]
        enemy_damage = random.randint(min_damage, max_damage)
        
        # Apply damage to character
        hp_before = character["current_hp"]
        character["current_hp"] = max(0, character["current_hp"] - enemy_damage)
        
        # Create attack message
        attack_message = f"The {enemy['name']} attacks you for {enemy_damage} damage!"
        
        # Add to combat log
        game_state["combat"]["log"].append(attack_message)
        
        # Check if player defeated
        if character["current_hp"] <= 0:
            # Combat lost
            defeat_message = f"You have been defeated by the {enemy['name']}!"
            game_state["combat"]["log"].append(defeat_message)
            
            # End combat
            game_state["combat"] = None
            
            # Restore some HP and stamina
            character["current_hp"] = max(1, character["max_hp"] // 4)
            character["current_stamina"] = max(2, character["max_stamina"] // 2)
            
            return {
                "success": True,
                "message": attack_message + " " + defeat_message,
                "combat_over": True,
                "victory": False
            }
        
        # Switch turn back to player
        game_state["combat"]["player_turn"] = True
        
        return {
            "success": True,
            "message": attack_message,
            "damage_taken": enemy_damage,
            "hp_before": hp_before,
            "hp_after": character["current_hp"]
        }
    
    def _process_combat_victory(self, character, game_state, enemy):
        """Process player victory in combat"""
        # Calculate rewards
        experience_reward = enemy.get("experience_reward", 25)
        min_gold, max_gold = enemy.get("gold_reward", (5, 15))
        gold_reward = random.randint(min_gold, max_gold)
        
        # Add experience and gold
        character["experience"] += experience_reward
        character["gold"] += gold_reward
        
        # Check for level up
        level_before = character["level"]
        xp_for_next_level = 100 * character["level"]
        
        if character["experience"] >= xp_for_next_level:
            character["level"] += 1
            hp_increase = 5 + (character["constitution"] // 3)
            stamina_increase = 2 + (character["constitution"] // 5)
            
            character["max_hp"] += hp_increase
            character["current_hp"] = character["max_hp"]
            character["max_stamina"] += stamina_increase
            character["current_stamina"] = character["max_stamina"]
            
            level_up_message = f" You leveled up to level {character['level']}!"
        else:
            level_up_message = ""
        
        # Determine loot
        loot = []
        
        if "loot_table" in enemy and isinstance(enemy["loot_table"], list) and enemy["loot_table"]:
            # Chance to get an item based on enemy level
            loot_chance = min(0.3 + (enemy["level"] * 0.1), 0.8)
            
            if random.random() < loot_chance:
                # Select a random item from loot table
                loot_item = random.choice(enemy["loot_table"])
                character["inventory"].append(loot_item)
                loot.append(loot_item)
        
        # Create victory message
        victory_message = f"You defeated the {enemy['name']}! You gained {experience_reward} experience and {gold_reward} gold."
        
        if loot:
            victory_message += f" You found: {', '.join(loot)}."
        
        victory_message += level_up_message
        
        # Add to combat log
        game_state["combat"]["log"].append(victory_message)
        
        # Add to game messages
        game_state["messages"].append(victory_message)
        
        # End combat
        game_state["combat"] = None
        
        # Restore some stamina
        character["current_stamina"] = min(character["max_stamina"], 
                                         character["current_stamina"] + 3)
        
        return {
            "success": True,
            "message": victory_message,
            "rewards": {
                "experience": experience_reward,
                "gold": gold_reward,
                "loot": loot,
                "level_up": character["level"] > level_before
            }
        }
    
    def _process_flee(self, character, game_state):
        """Process attempt to flee from combat"""
        # Check if in combat
        if not game_state.get("combat"):
            return {
                "success": False,
                "message": "You are not in combat!"
            }
        
        # Deduct stamina
        stamina_cost = 2
        
        if character["current_stamina"] < stamina_cost:
            return {
                "success": False,
                "message": f"Not enough stamina to flee! You need {stamina_cost} stamina."
            }
        
        character["current_stamina"] -= stamina_cost
        
        # Calculate flee chance based on character dexterity and enemy level
        enemy = game_state["combat"]["enemy"]
        flee_chance = 0.4 + (character["dexterity"] * 0.02) - (enemy["level"] * 0.05)
        flee_chance = max(0.1, min(0.9, flee_chance))  # Clamp between 10% and 90%
        
        if random.random() < flee_chance:
            # Successful flee
            flee_message = f"You successfully fled from the {enemy['name']}!"
            game_state["combat"] = None
            game_state["messages"].append(flee_message)
            
            return {
                "success": True,
                "message": flee_message,
                "combat_over": True
            }
        else:
            # Failed flee, enemy gets free attack
            flee_message = f"You failed to flee from the {enemy['name']}!"
            game_state["combat"]["log"].append(flee_message)
            
            # Enemy attacks
            enemy_attack_result = self._process_enemy_attack(character, game_state)
            
            return {
                "success": False,
                "message": flee_message + " " + enemy_attack_result.get("message", ""),
                "enemy_attack": enemy_attack_result.get("message", ""),
                "damage_taken": enemy_attack_result.get("damage_taken", 0),
                "player_hp": character["current_hp"],
                "combat_over": enemy_attack_result.get("combat_over", False)
            }
    
    def _process_use_item(self, item_name, character, game_state):
        """Process using an item from inventory"""
        # Check if item is in inventory
        if item_name not in character["inventory"]:
            return {
                "success": False,
                "message": f"You don't have a {item_name} in your inventory."
            }
        
        # Process different item types
        if "health potion" in item_name.lower() or "healing potion" in item_name.lower():
            # Healing potion
            heal_amount = 10 + (character["level"] * 2)
            hp_before = character["current_hp"]
            character["current_hp"] = min(character["max_hp"], character["current_hp"] + heal_amount)
            hp_after = character["current_hp"]
            
            # Remove item from inventory
            character["inventory"].remove(item_name)
            
            use_message = f"You used a {item_name} and restored {hp_after - hp_before} health!"
            
            # Add to messages/combat log
            game_state["messages"].append(use_message)
            if game_state.get("combat"):
                game_state["combat"]["log"].append(use_message)
                # In combat, using an item doesn't end the player's turn
            
            return {
                "success": True,
                "message": use_message,
                "hp_before": hp_before,
                "hp_after": hp_after,
                "hp_restored": hp_after - hp_before
            }
        
        elif "stamina potion" in item_name.lower() or "energy potion" in item_name.lower():
            # Stamina potion
            stamina_amount = 5 + (character["level"] * 1)
            stamina_before = character["current_stamina"]
            character["current_stamina"] = min(character["max_stamina"], character["current_stamina"] + stamina_amount)
            stamina_after = character["current_stamina"]
            
            # Remove item from inventory
            character["inventory"].remove(item_name)
            
            use_message = f"You used a {item_name} and restored {stamina_after - stamina_before} stamina!"
            
            # Add to messages/combat log
            game_state["messages"].append(use_message)
            if game_state.get("combat"):
                game_state["combat"]["log"].append(use_message)
            
            return {
                "success": True,
                "message": use_message,
                "stamina_before": stamina_before,
                "stamina_after": stamina_after,
                "stamina_restored": stamina_after - stamina_before
            }
        
        else:
            # For unknown items, use a generic response
            # Could be extended with a more detailed item system
            use_message = f"You used the {item_name}."
            
            # Remove item from inventory
            character["inventory"].remove(item_name)
            
            # Add to messages/combat log
            game_state["messages"].append(use_message)
            if game_state.get("combat"):
                game_state["combat"]["log"].append(use_message)
            
            return {
                "success": True,
                "message": use_message,
                "item_used": item_name
            }
    
    def process_combat_attack(self, attack_type, character, game_state):
        """Process combat attack from API endpoint"""
        return self._process_attack(attack_type, character, game_state, None)
    
    def process_rest(self, character, game_state):
        """Process resting to recover HP and stamina"""
        # Check if in combat
        if game_state.get("combat"):
            return {
                "success": False,
                "message": "You cannot rest while in combat!"
            }
        
        # Calculate recovery amounts
        hp_recovery = 5 + (character["constitution"] // 3)
        stamina_recovery = 3 + (character["constitution"] // 4)
        
        # Record before values
        hp_before = character["current_hp"]
        stamina_before = character["current_stamina"]
        
        # Apply recovery
        character["current_hp"] = min(character["max_hp"], character["current_hp"] + hp_recovery)
        character["current_stamina"] = min(character["max_stamina"], character["current_stamina"] + stamina_recovery)
        
        # Calculate amounts restored
        hp_restored = character["current_hp"] - hp_before
        stamina_restored = character["current_stamina"] - stamina_before
        
        rest_message = f"You take some time to rest. You recovered {hp_restored} HP and {stamina_restored} stamina."
        
        # Add to game messages
        game_state["messages"].append(rest_message)
        
        # Small chance of random encounter while resting
        encounter_chance = 0.15  # 15% chance
        
        if random.random() < encounter_chance:
            # This would call _initiate_combat, but that requires a groq_client
            # For this endpoint, we'll just return the rest result
            rest_message += " But your rest was interrupted!"
        
        return {
            "success": True,
            "message": rest_message,
            "hp_before": hp_before,
            "hp_after": character["current_hp"],
            "hp_restored": hp_restored,
            "stamina_before": stamina_before,
            "stamina_after": character["current_stamina"],
            "stamina_restored": stamina_restored
        }
    
    def use_item(self, item_name, character, game_state):
        """Use item from API endpoint"""
        return self._process_use_item(item_name, character, game_state)
    
    def _process_custom_action(self, action, action_details, character, game_state, groq_client):
        """Process a custom action using Groq API to determine outcome"""
        current_location = game_state.get("current_location", "Unknown")
        
        prompt = f"""
        The player is currently at: {current_location}
        The player character is: {character["name"]}, a level {character["level"]} {character["race"]} {character["class"]}
        Game state: {json.dumps(game_state)}
        
        The player wants to perform this action: "{action} {action_details}"
        
        Determine the outcome of this action and generate a JSON response with:
        1. Whether the action succeeds (success: true/false)
        2. A detailed description of what happens
        3. Any stat changes, items found, or other effects
        4. A message to display to the player
        
        JSON format:
        {{
            "success": true/false,
            "description": "Detailed description of the outcome",
            "effects": {{
                "hp_change": 0,
                "stamina_change": 0,
                "gold_change": 0,
                "items_gained": [],
                "items_lost": []
            }},
            "message": "Message to player"
        }}
        """
        
        # Get response from Groq
        response = groq_client.generate_response(prompt, character["name"])
        
        try:
            result = json.loads(response)
            
            if result.get("success") and "effects" in result:
                effects = result.get("effects", {})
                
                # Apply HP change
                hp_change = effects.get("hp_change", 0)
                if hp_change < 0:
                    character["current_hp"] = max(0, character["current_hp"] + hp_change)
                else:
                    character["current_hp"] = min(character["max_hp"], character["current_hp"] + hp_change)
                
                # Apply stamina change
                stamina_change = effects.get("stamina_change", 0)
                if stamina_change < 0:
                    character["current_stamina"] = max(0, character["current_stamina"] + stamina_change)
                else:
                    character["current_stamina"] = min(character["max_stamina"], 
                                                     character["current_stamina"] + stamina_change)
                
                # Apply gold change
                gold_change = effects.get("gold_change", 0)
                character["gold"] = max(0, character["gold"] + gold_change)
                
                # Add items gained
                for item in effects.get("items_gained", []):
                    character["inventory"].append(item)
                
                # Remove items lost
                for item in effects.get("items_lost", []):
                    if item in character["inventory"]:
                        character["inventory"].remove(item)
            
            # Add message to history
            game_state["messages"].append(result.get("message"))
            
            return result
        except Exception as e:
            logger.error(f"Error processing custom action: {str(e)}")
            return {
                "success": False,
                "message": "Sorry, there was an error processing your action."
            }
