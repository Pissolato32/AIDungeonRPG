"""
Random encounter generator.

This module provides functions for generating random encounters and loot.
"""

import random
import logging
from typing import Dict, List, Any

from translations import get_text

logger = logging.getLogger(__name__)


# Enemy types by location
LOCATION_ENEMIES = {
    "wilderness": [
        "wild_wolf", "bear", "bandit", "goblin", "wild_boar", 
        "giant_spider", "dire_wolf", "ogre", "troll"
    ],
    "dungeon": [
        "skeleton", "zombie", "goblin", "orc", "kobold", 
        "ghoul", "minotaur", "troll", "gelatinous_cube"
    ],
    "village": [
        "thief", "bandit", "drunk_brawler", "guard", "cultist"
    ]
}

# Loot tables
COMMON_LOOT = ["health_potion", "gold_coin", "stamina_potion"]
ENEMY_LOOT = {
    "wild_wolf": ["wolf_pelt", "sharp_tooth", "wolf_meat"],
    "bear": ["bear_pelt", "bear_claw", "bear_meat"],
    "goblin": ["rusty_dagger", "stolen_coin_purse", "goblin_ear"],
    "skeleton": ["bone_fragment", "rusty_weapon", "tattered_cloth"],
    "zombie": ["rotting_flesh", "tattered_clothing", "broken_jewelry"],
    "giant_spider": ["spider_silk", "venom_sac", "spider_eye"],
    "bandit": ["stolen_goods", "leather_pouch", "cheap_jewelry"],
    "orc": ["crude_weapon", "orc_tooth", "tribal_symbol"],
    "troll": ["troll_hide", "large_tooth", "crude_club"]
}


def get_random_encounter(
    character_level: int,
    location_type: str = "wilderness",
    lang: str = None
) -> Dict[str, Any]:
    """
    Generate a random encounter based on character level and location.

    Args:
        character_level: Character level
        location_type: Location type (wilderness, dungeon, village)
        lang: Language for translation
        
    Returns:
        Dictionary with enemy data
    """
    # Validate location type
    enemies = LOCATION_ENEMIES.get(location_type, LOCATION_ENEMIES["wilderness"])
    
    try:
        # Select random enemy
        enemy_key = random.choice(enemies)
        enemy_type = get_text(f"enemies.{enemy_key}", lang)

        # Scale enemy level
        enemy_level = _scale_enemy_level(character_level)

        # Calculate enemy stats
        enemy_stats = _calculate_enemy_stats(enemy_level)
        
        # Generate enemy description
        description = _generate_enemy_description(enemy_type, lang)
            
        # Create enemy data
        enemy = {
            "name": enemy_type,
            "description": description,
            "level": enemy_level,
            "max_hp": enemy_stats["max_hp"],
            "current_hp": enemy_stats["max_hp"],
            "attack_damage": enemy_stats["attack_damage"],
            "defense": enemy_stats["defense"],
            "experience_reward": enemy_stats["experience_reward"],
            "gold_reward": enemy_stats["gold_reward"],
            "loot_table": generate_loot_table(enemy_key, enemy_level, lang)
        }

        logger.info(f"Encounter generated: {enemy['name']} (Level {enemy_level})")
        return enemy

    except Exception as e:
        logger.error(f"Error generating encounter: {e}")
        # Return default enemy in case of error
        return _get_default_enemy()


def generate_loot_table(
    enemy_key: str,
    enemy_level: int,
    lang: str = None
) -> List[str]:
    """
    Generate a list of loot items for an enemy.
    
    Args:
        enemy_key: Enemy type identifier
        enemy_level: Enemy level
        lang: Language for translation
        
    Returns:
        List of loot items
    """
    try:
        # Get specific or generic loot
        specific_loot = ENEMY_LOOT.get(enemy_key, ["unknown_item"])
        
        # Add better items for higher level enemies
        enhanced_loot = _enhance_loot_by_level(specific_loot, enemy_level)

        # Select 2-4 random items
        loot_count = random.randint(2, 4)
        combined_loot = COMMON_LOOT + enhanced_loot
        loot_keys = random.sample(combined_loot, min(loot_count, len(combined_loot)))

        # Translate items
        loot_table = [get_text(f"items.{item}", lang) for item in loot_keys]

        logger.debug(f"Loot generated for {enemy_key}: {loot_table}")
        return loot_table
    except Exception as e:
        logger.error(f"Error generating loot: {e}")
        return []


def _scale_enemy_level(character_level: int) -> int:
    """
    Scale enemy level based on character level.
    
    Args:
        character_level: Character level
        
    Returns:
        Scaled enemy level
    """
    # Enemy level is character level +/- 2, minimum 1, maximum 10
    return max(1, min(character_level + random.randint(-2, 2), 10))


def _calculate_enemy_stats(enemy_level: int) -> Dict[str, Any]:
    """
    Calculate enemy statistics based on level.
    
    Args:
        enemy_level: Enemy level
        
    Returns:
        Dictionary with enemy statistics
    """
    # Calculate HP
    hp_base = 8 + (enemy_level * 2)
    hp_variance = random.randint(-3, 3)
    max_hp = hp_base + hp_variance
    
    return {
        "max_hp": max_hp,
        "attack_damage": [1 + (enemy_level // 3), 4 + enemy_level],
        "defense": enemy_level // 2,
        "experience_reward": 20 + (enemy_level * 10),
        "gold_reward": [enemy_level, 5 + (enemy_level * 3)]
    }


def _generate_enemy_description(enemy_type: str, lang: str) -> str:
    """
    Generate a description for an enemy.
    
    Args:
        enemy_type: Enemy type
        lang: Language for translation
        
    Returns:
        Enemy description
    """
    try:
        return f"{get_text('enemies.description_prefix', lang)} {enemy_type.lower()} {get_text('enemies.description_suffix', lang)}"
    except Exception:
        return f"A hostile {enemy_type.lower()}"


def _enhance_loot_by_level(specific_loot: List[str], enemy_level: int) -> List[str]:
    """
    Enhance loot based on enemy level.
    
    Args:
        specific_loot: Base loot list
        enemy_level: Enemy level
        
    Returns:
        Enhanced loot list
    """
    enhanced_loot = specific_loot.copy()
    
    # Add medium items for level 5+
    if enemy_level >= 5:
        enhanced_loot.extend(["medium_health_potion", "medium_stamina_potion"])

    # Add high-quality items for level 8+
    if enemy_level >= 8:
        enhanced_loot.extend(["large_health_potion", "enchanted_item"])
        
    return enhanced_loot


def _get_default_enemy() -> Dict[str, Any]:
    """
    Get a default enemy for fallback.
    
    Returns:
        Default enemy data
    """
    return {
        "name": "Goblin",
        "description": "A small, malicious goblin",
        "level": 1,
        "max_hp": 10,
        "current_hp": 10,
        "attack_damage": [1, 4],
        "defense": 0,
        "experience_reward": 20,
        "gold_reward": [1, 5],
        "loot_table": []
    }