import random
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

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
