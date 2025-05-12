import os
import logging
import json
import random
import requests
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")

# Configure server-side session
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 hours
Session(app)

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

#------------------------------------------------------
# MODEL CLASSES
#------------------------------------------------------

class Character:
    """Character model representing player character attributes and methods"""
    
    def __init__(self, name, character_class, race, 
                strength=10, dexterity=10, constitution=10, 
                intelligence=10, wisdom=10, charisma=10,
                max_hp=20, current_hp=20, max_stamina=10, current_stamina=10,
                inventory=None, gold=50, experience=0, level=1):
        
        self.name = name
        self.character_class = character_class
        self.race = race
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma
        self.max_hp = max_hp
        self.current_hp = current_hp
        self.max_stamina = max_stamina
        self.current_stamina = current_stamina
        self.inventory = inventory or ["Basic Sword", "Health Potion"]
        self.gold = gold
        self.experience = experience
        self.level = level
        self.last_updated = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert character to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "class": self.character_class,
            "race": self.race,
            "strength": self.strength,
            "dexterity": self.dexterity,
            "constitution": self.constitution,
            "intelligence": self.intelligence,
            "wisdom": self.wisdom,
            "charisma": self.charisma,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "max_stamina": self.max_stamina,
            "current_stamina": self.current_stamina,
            "inventory": self.inventory,
            "gold": self.gold,
            "experience": self.experience,
            "level": self.level,
            "last_updated": self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create character from dictionary"""
        if not data:
            return None
            
        character = cls(
            name=data.get("name", "Unknown"),
            character_class=data.get("class", "Fighter"),
            race=data.get("race", "Human"),
            strength=data.get("strength", 10),
            dexterity=data.get("dexterity", 10),
            constitution=data.get("constitution", 10),
            intelligence=data.get("intelligence", 10),
            wisdom=data.get("wisdom", 10),
            charisma=data.get("charisma", 10),
            max_hp=data.get("max_hp", 20),
            current_hp=data.get("current_hp", 20),
            max_stamina=data.get("max_stamina", 10),
            current_stamina=data.get("current_stamina", 10),
            inventory=data.get("inventory", ["Basic Sword", "Health Potion"]),
            gold=data.get("gold", 50),
            experience=data.get("experience", 0),
            level=data.get("level", 1)
        )
        
        character.last_updated = data.get("last_updated", datetime.now().isoformat())
        return character
    
    def take_damage(self, amount):
        """Apply damage to character"""
        self.current_hp = max(0, self.current_hp - amount)
        self.last_updated = datetime.now().isoformat()
        return self.current_hp
    
    def heal(self, amount):
        """Heal character"""
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        self.last_updated = datetime.now().isoformat()
        return self.current_hp
    
    def use_stamina(self, amount):
        """Use stamina for actions"""
        if self.current_stamina < amount:
            return False
        
        self.current_stamina -= amount
        self.last_updated = datetime.now().isoformat()
        return True
    
    def recover_stamina(self, amount):
        """Recover stamina"""
        self.current_stamina = min(self.max_stamina, self.current_stamina + amount)
        self.last_updated = datetime.now().isoformat()
        return self.current_stamina
    
    def add_to_inventory(self, item):
        """Add item to inventory"""
        self.inventory.append(item)
        self.last_updated = datetime.now().isoformat()
    
    def remove_from_inventory(self, item):
        """Remove item from inventory"""
        if item in self.inventory:
            self.inventory.remove(item)
            self.last_updated = datetime.now().isoformat()
            return True
        return False
    
    def add_experience(self, amount):
        """Add experience points and handle level up"""
        self.experience += amount
        
        # Simple leveling logic: 100 * current level = XP needed for next level
        xp_for_next_level = 100 * self.level
        
        if self.experience >= xp_for_next_level:
            self.level_up()
        
        self.last_updated = datetime.now().isoformat()
    
    def level_up(self):
        """Level up character, increasing stats"""
        self.level += 1
        
        # Increase HP and stamina
        hp_increase = 5 + (self.constitution // 3)
        stamina_increase = 2 + (self.constitution // 5)
        
        self.max_hp += hp_increase
        self.current_hp = self.max_hp
        self.max_stamina += stamina_increase
        self.current_stamina = self.max_stamina
        
        self.last_updated = datetime.now().isoformat()
        return {
            "new_level": self.level,
            "hp_increase": hp_increase,
            "stamina_increase": stamina_increase
        }

class Enemy:
    """Enemy model representing NPCs and monsters in combat"""
    
    def __init__(self, name, description, level=1, max_hp=10, current_hp=10, 
                 attack_damage=(1, 6), defense=0, experience_reward=25, 
                 gold_reward=(5, 15), loot_table=None):
        
        self.name = name
        self.description = description
        self.level = level
        self.max_hp = max_hp
        self.current_hp = current_hp
        self.attack_damage = attack_damage  # Tuple of (min_damage, max_damage)
        self.defense = defense
        self.experience_reward = experience_reward
        self.gold_reward = gold_reward  # Tuple of (min_gold, max_gold)
        self.loot_table = loot_table or []
    
    def to_dict(self):
        """Convert enemy to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "level": self.level,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "attack_damage": self.attack_damage,
            "defense": self.defense,
            "experience_reward": self.experience_reward,
            "gold_reward": self.gold_reward,
            "loot_table": self.loot_table
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create enemy from dictionary"""
        if not data:
            return None
            
        return cls(
            name=data.get("name", "Unknown Enemy"),
            description=data.get("description", "A mysterious creature"),
            level=data.get("level", 1),
            max_hp=data.get("max_hp", 10),
            current_hp=data.get("current_hp", 10),
            attack_damage=data.get("attack_damage", (1, 6)),
            defense=data.get("defense", 0),
            experience_reward=data.get("experience_reward", 25),
            gold_reward=data.get("gold_reward", (5, 15)),
            loot_table=data.get("loot_table", [])
        )
    
    def take_damage(self, amount):
        """Apply damage to enemy"""
        damage_after_defense = max(1, amount - self.defense)
        self.current_hp = max(0, self.current_hp - damage_after_defense)
        return self.current_hp, damage_after_defense
    
    def is_defeated(self):
        """Check if enemy is defeated"""
        return self.current_hp <= 0

#------------------------------------------------------
# UTILITY FUNCTIONS
#------------------------------------------------------

def roll_dice(num_dice, sides, modifier=0):
    """Roll dice in the format NdS+M (N dice with S sides plus modifier M)"""
    result = sum(random.randint(1, sides) for _ in range(num_dice)) + modifier
    return result

def calculate_attribute_modifier(attribute_score):
    """Calculate the modifier for an attribute score (DnD style)"""
    return (attribute_score - 10) // 2

def get_random_encounter(character_level, location_type="wilderness"):
    """Generate a random encounter based on character level and location"""
    # Define enemy types by location
    location_enemies = {
        "wilderness": [
            "Wolf", "Bear", "Bandit", "Goblin", "Wild Boar", 
            "Giant Spider", "Dire Wolf", "Ogre", "Troll"
        ],
        "dungeon": [
            "Skeleton", "Zombie", "Goblin", "Orc", "Kobold", 
            "Ghoul", "Minotaur", "Troll", "Gelatinous Cube"
        ],
        "village": [
            "Thief", "Bandit", "Drunk Fighter", "Guard", "Cultist"
        ]
    }
    
    # Get enemies appropriate for the location
    enemies = location_enemies.get(location_type, location_enemies["wilderness"])
    
    # Select a random enemy type
    enemy_type = random.choice(enemies)
    
    # Scale enemy level based on character level
    enemy_level = max(1, min(character_level + random.randint(-2, 2), 10))
    
    # Calculate enemy stats based on level
    hp_base = 8 + (enemy_level * 2)
    hp_variance = random.randint(-3, 3)
    max_hp = hp_base + hp_variance
    
    # Generate enemy data
    enemy = {
        "name": enemy_type,
        "description": f"A level {enemy_level} {enemy_type.lower()} ready for battle.",
        "level": enemy_level,
        "max_hp": max_hp,
        "current_hp": max_hp,
        "attack_damage": [1 + (enemy_level // 3), 4 + enemy_level],
        "defense": enemy_level // 2,
        "experience_reward": 20 + (enemy_level * 10),
        "gold_reward": [enemy_level, 5 + (enemy_level * 3)],
        "loot_table": generate_loot_table(enemy_type, enemy_level)
    }
    
    return enemy

def generate_loot_table(enemy_type, enemy_level):
    """Generate possible loot for an enemy"""
    # Common loot that many enemies might drop
    common_loot = ["Small Health Potion", "Gold Coin", "Minor Stamina Potion"]
    
    # Enemy-specific loot
    enemy_loot = {
        "Wolf": ["Wolf Pelt", "Sharp Tooth", "Wolf Meat"],
        "Bear": ["Bear Pelt", "Bear Claw", "Bear Meat"],
        "Bandit": ["Rusty Dagger", "Leather Scraps", "Coin Purse"],
        "Goblin": ["Goblin Ear", "Crude Knife", "Shiny Trinket"],
        "Wild Boar": ["Boar Tusk", "Boar Hide", "Boar Meat"],
        "Giant Spider": ["Spider Silk", "Venom Sac", "Spider Leg"],
        "Dire Wolf": ["Thick Fur", "Large Fang", "Wolf Heart"],
        "Ogre": ["Ogre Tooth", "Heavy Club", "Gold Pouch"],
        "Troll": ["Troll Hide", "Regenerating Flesh", "Troll Bone"],
        "Skeleton": ["Bone Fragment", "Rusty Sword", "Ancient Coin"],
        "Zombie": ["Rotting Flesh", "Tattered Clothes", "Zombie Tooth"],
        "Orc": ["Orc Tusk", "Crude Armor Piece", "War Banner Fragment"],
        "Kobold": ["Kobold Scale", "Mining Pick", "Shiny Rock"],
        "Ghoul": ["Ghoul Fingernail", "Putrid Flesh", "Burial Trinket"],
        "Minotaur": ["Bull Horn", "Hoof", "Maze Map Fragment"],
        "Gelatinous Cube": ["Gelatinous Sample", "Dissolved Item", "Strange Coin"],
        "Thief": ["Lockpick", "Stolen Goods", "Hidden Blade"],
        "Drunk Fighter": ["Empty Bottle", "Tavern Token", "Brass Knuckle"],
        "Guard": ["Guard Badge", "Chainmail Scraps", "Patrol Schedule"],
        "Cultist": ["Cult Symbol", "Ritual Component", "Mysterious Scroll"]
    }
    
    # Get enemy-specific loot or use generic if not found
    specific_loot = enemy_loot.get(enemy_type, ["Unknown Item"])
    
    # Higher level enemies might drop better items
    if enemy_level >= 5:
        specific_loot.append("Medium Health Potion")
        specific_loot.append("Medium Stamina Potion")
    
    if enemy_level >= 8:
        specific_loot.append("Large Health Potion")
        specific_loot.append("Enchanted Item")
    
    # Create loot table with 2-4 possible drops
    loot_count = random.randint(2, 4)
    loot_table = random.sample(common_loot + specific_loot, min(loot_count, len(common_loot) + len(specific_loot)))
    
    return loot_table

def generate_quest(location, difficulty=1):
    """Generate a random quest"""
    quest_types = [
        "Kill", "Collect", "Deliver", "Escort", "Investigate"
    ]
    
    quest_type = random.choice(quest_types)
    
    if quest_type == "Kill":
        target = random.choice(["Bandits", "Wolves", "Goblins", "Cultists", "Monster"])
        name = f"Eliminate the {target}"
        description = f"Clear out the {target.lower()} causing trouble near {location}."
    elif quest_type == "Collect":
        item = random.choice(["Herbs", "Gems", "Artifacts", "Materials", "Lost Items"])
        name = f"Gather {item}"
        description = f"Collect valuable {item.lower()} from the area around {location}."
    elif quest_type == "Deliver":
        item = random.choice(["Message", "Package", "Supplies", "Medicine", "Weapon"])
        destination = random.choice(["Village", "Camp", "Outpost", "Castle", "Tower"])
        name = f"Deliver {item}"
        description = f"Deliver an important {item.lower()} to the {destination.lower()} from {location}."
    elif quest_type == "Escort":
        npc = random.choice(["Merchant", "Noble", "Scholar", "Child", "Prisoner"])
        destination = random.choice(["Village", "Camp", "Outpost", "Castle", "Tower"])
        name = f"Escort the {npc}"
        description = f"Safely escort the {npc.lower()} from {location} to the {destination.lower()}."
    else:  # Investigate
        subject = random.choice(["Disappearances", "Strange Noises", "Mysterious Lights", "Abandoned Ruin", "Curse"])
        name = f"Investigate the {subject}"
        description = f"Discover the source of the {subject.lower()} near {location}."
    
    return {
        "name": name,
        "description": description,
        "difficulty": difficulty,
        "reward_gold": 50 * difficulty,
        "reward_xp": 100 * difficulty,
        "reward_items": ["Health Potion"] if difficulty > 1 else [],
        "status": "active",
        "progress": 0
    }

def save_json_data(data, filename):
    """Save data to a JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving data to {filename}: {str(e)}")
        return False

def load_json_data(filename):
    """Load data from a JSON file"""
    if not os.path.exists(filename):
        return None
        
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error loading data from {filename}: {str(e)}")
        return None

#------------------------------------------------------
# GROQ CLIENT
#------------------------------------------------------

class GroqClient:
    """Client for interacting with the Groq API"""
    
    def __init__(self):
        """Initialize the Groq client with API key from environment"""
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama2-70b-4096"  # Default model
        self.conversation_history = {}  # Store conversation history per character
    
    def generate_response(self, prompt, character_id="default"):
        """Generate a response using the Groq API"""
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set. Using fallback response.")
            return self._generate_fallback_response(prompt)
        
        # Initialize history for this character if not exists
        if character_id not in self.conversation_history:
            self.conversation_history[character_id] = []
        
        # Add prompt to history
        self.conversation_history[character_id].append({
            "role": "user",
            "content": prompt
        })
        
        # Keep history limited to last 10 messages
        if len(self.conversation_history[character_id]) > 10:
            self.conversation_history[character_id] = self.conversation_history[character_id][-10:]
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": self.conversation_history[character_id],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                result = response_data["choices"][0]["message"]["content"]
                
                # Add response to history
                self.conversation_history[character_id].append({
                    "role": "assistant",
                    "content": result
                })
                
                return result
            else:
                logger.error(f"Unexpected response format: {response_data}")
                return self._generate_fallback_response(prompt)
                
        except Exception as e:
            logger.error(f"Error generating response from Groq API: {str(e)}")
            return self._generate_fallback_response(prompt)
    
    def _generate_fallback_response(self, prompt):
        """Generate a fallback response when API is unavailable"""
        # Check if prompt is asking for JSON
        if "JSON" in prompt and "format" in prompt:
            # Simple JSON fallback for common scenarios
            if "move" in prompt.lower():
                return json.dumps({
                    "success": True,
                    "new_location": "Forest Path",
                    "description": "You walk along a winding path through a dense forest. Tall trees tower above you, and sunlight filters through the leaves.",
                    "npcs": ["Wandering Merchant"],
                    "events": ["A gentle breeze rustles the leaves."],
                    "message": "You move along the forest path.",
                    "combat": False
                })
            elif "look" in prompt.lower():
                return json.dumps({
                    "success": True,
                    "description": "You examine your surroundings carefully.",
                    "observations": ["The area seems peaceful."],
                    "message": "You look around and take in the details of your surroundings."
                })
            elif "talk" in prompt.lower():
                return json.dumps({
                    "success": True,
                    "dialogue": "Greetings, traveler! What brings you to these parts?",
                    "information": ["The village to the east has been having trouble with bandits."],
                    "quests": [{
                        "name": "Clear the Bandit Camp",
                        "description": "Defeat the bandits that have been troubling the village."
                    }],
                    "message": "The NPC greets you warmly and shares some information."
                })
            elif "search" in prompt.lower():
                return json.dumps({
                    "success": True,
                    "items": ["Small Health Potion"],
                    "gold": 5,
                    "secrets": ["There seems to be a hidden path to the north."],
                    "message": "You search the area and find a small health potion and 5 gold coins.",
                    "combat": False
                })
            elif "enemy" in prompt.lower():
                return json.dumps({
                    "enemy": {
                        "name": "Forest Wolf",
                        "description": "A large wolf with grey fur and sharp teeth.",
                        "level": 1,
                        "max_hp": 15,
                        "current_hp": 15,
                        "attack_damage": [2, 5],
                        "defense": 1,
                        "experience_reward": 30,
                        "gold_reward": [3, 8],
                        "loot_table": ["Wolf Pelt", "Sharp Tooth"]
                    },
                    "message": "A forest wolf approaches, growling menacingly!"
                })
            else:
                return json.dumps({
                    "success": True,
                    "description": "The action seems to work.",
                    "effects": {
                        "hp_change": 0,
                        "stamina_change": 0,
                        "gold_change": 0,
                        "items_gained": [],
                        "items_lost": []
                    },
                    "message": "You perform the action successfully."
                })
        else:
            # Generic text response
            return "The system processes your request and provides a response."

#------------------------------------------------------
# GAME ENGINE
#------------------------------------------------------

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

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/character", methods=["GET", "POST"])
def character():
    if request.method == "POST":
        # Create or update character
        character_data = {
            "name": request.form.get("name"),
            "class": request.form.get("class"),
            "race": request.form.get("race"),
            "strength": int(request.form.get("strength", 10)),
            "dexterity": int(request.form.get("dexterity", 10)),
            "constitution": int(request.form.get("constitution", 10)),
            "intelligence": int(request.form.get("intelligence", 10)),
            "wisdom": int(request.form.get("wisdom", 10)),
            "charisma": int(request.form.get("charisma", 10)),
            "max_hp": int(request.form.get("max_hp", 20)),
            "current_hp": int(request.form.get("current_hp", 20)),
            "max_stamina": int(request.form.get("max_stamina", 10)),
            "current_stamina": int(request.form.get("current_stamina", 10)),
            "inventory": request.form.get("inventory", "").split(",") if request.form.get("inventory") else ["Basic Sword", "Health Potion"],
            "gold": int(request.form.get("gold", 50)),
            "experience": int(request.form.get("experience", 0)),
            "level": int(request.form.get("level", 1)),
        }
        
        # Set character data in session
        session["character"] = character_data
        
        # Save character data to file for persistence
        user_id = session.get("user_id", "default_user")
        game_engine.save_character(user_id, character_data)
        
        flash("Character saved successfully!", "success")
        return redirect(url_for("game"))
    
    # Check if character exists in session
    character_data = session.get("character")
    
    # If not in session, try to load from file
    if character_data is None:
        user_id = session.get("user_id", "default_user")
        character_data = game_engine.load_character(user_id)
    
    return render_template("character.html", character=character_data)

@app.route("/game")
def game():
    # Check if character exists in session
    character = session.get("character")
    
    # If no character, redirect to character creation
    if not character:
        flash("Please create a character first!", "warning")
        return redirect(url_for("character"))
    
    # Load game state if exists
    user_id = session.get("user_id", "default_user")
    game_state = game_engine.load_game_state(user_id)
    
    # If no game state, create a new one
    if not game_state:
        game_state = {
            "current_location": "Village Square",
            "scene_description": "You stand in the center of a small village. There's a tavern to the north, a blacksmith to the east, and the village gate to the south.",
            "npcs_present": ["Village Elder", "Merchant"],
            "events": ["A festival is being prepared in the village square."],
            "messages": ["Welcome to the village of Eldermist! Your adventure begins now."],
            "combat": None
        }
        game_engine.save_game_state(user_id, game_state)
    
    return render_template("game.html", character=character, game_state=game_state)

@app.route("/api/action", methods=["POST"])
def perform_action():
    data = request.json
    action = data.get("action")
    action_details = data.get("details", "")
    
    # Get character and game state
    character = session.get("character")
    user_id = session.get("user_id", "default_user")
    game_state = game_engine.load_game_state(user_id)
    
    if not character or not game_state:
        return jsonify({"error": "Character or game state not found"}), 400
    
    try:
        # Process the action using the game engine and AI
        result = game_engine.process_action(action, action_details, character, game_state, groq_client)
        
        # Update character in session
        session["character"] = character
        
        # Save updated character and game state
        game_engine.save_character(user_id, character)
        game_engine.save_game_state(user_id, game_state)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing action: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/combat/attack", methods=["POST"])
def combat_attack():
    data = request.json
    attack_type = data.get("attack_type", "basic")
    
    # Get character and game state
    character = session.get("character")
    user_id = session.get("user_id", "default_user")
    game_state = game_engine.load_game_state(user_id)
    
    if not character or not game_state or not game_state.get("combat"):
        return jsonify({"error": "Character, game state, or combat not found"}), 400
    
    try:
        # Process combat attack
        result = game_engine.process_combat_attack(attack_type, character, game_state)
        
        # Update character in session
        session["character"] = character
        
        # Save updated character and game state
        game_engine.save_character(user_id, character)
        game_engine.save_game_state(user_id, game_state)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing combat attack: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/use-item", methods=["POST"])
def use_item():
    data = request.json
    item_name = data.get("item")
    
    # Get character and game state
    character = session.get("character")
    user_id = session.get("user_id", "default_user")
    game_state = game_engine.load_game_state(user_id)
    
    if not character or not game_state:
        return jsonify({"error": "Character or game state not found"}), 400
    
    try:
        # Use the item via game engine
        result = game_engine.use_item(item_name, character, game_state)
        
        # Update character in session
        session["character"] = character
        
        # Save updated character and game state
        game_engine.save_character(user_id, character)
        game_engine.save_game_state(user_id, game_state)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error using item: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/rest", methods=["POST"])
def rest():
    # Get character and game state
    character = session.get("character")
    user_id = session.get("user_id", "default_user")
    game_state = game_engine.load_game_state(user_id)
    
    if not character or not game_state:
        return jsonify({"error": "Character or game state not found"}), 400
    
    try:
        # Process resting action
        result = game_engine.process_rest(character, game_state)
        
        # Update character in session
        session["character"] = character
        
        # Save updated character and game state
        game_engine.save_character(user_id, character)
        game_engine.save_game_state(user_id, game_state)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing rest: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/reset-game", methods=["POST"])
def reset_game():
    # Clear character and game state
    user_id = session.get("user_id", "default_user")
    session.pop("character", None)
    
    try:
        # Reset game state
        game_engine.delete_game_state(user_id)
        game_engine.delete_character(user_id)
        
        return jsonify({"success": True, "message": "Game reset successfully"})
    except Exception as e:
        logger.error(f"Error resetting game: {str(e)}")
        return jsonify({"error": str(e)}), 500
