"""
Encounter generator module.

This module provides functionality for generating random encounters.
"""

import random
import logging
from typing import Dict, Any, List, Optional, Union

from ai.groq_client import GroqClient
from core.enemy import Enemy

logger = logging.getLogger(__name__)

def get_random_encounter(character_level: int, location: str = None) -> Dict[str, Any]:
    """
    Generate a random encounter based on character level and location.
    
    Args:
        character_level: The character's level
        location: Optional location name for themed encounters
        
    Returns:
        Dictionary with encounter details
    """
    # Determine encounter type
    encounter_type = _determine_encounter_type(location)
    
    if encounter_type == "combat":
        return _generate_combat_encounter(character_level, location)
    elif encounter_type == "npc":
        return _generate_npc_encounter(character_level, location)
    else:
        return _generate_environmental_encounter(character_level, location)

def _determine_encounter_type(location: Optional[str] = None) -> str:
    """
    Determine the type of encounter based on location.
    
    Args:
        location: Optional location name
        
    Returns:
        Encounter type: "combat", "npc", or "environmental"
    """
    # Base probabilities
    combat_chance = 0.5  # 50% chance of combat
    npc_chance = 0.3     # 30% chance of NPC encounter
    
    # Adjust based on location
    if location:
        location_lower = location.lower()
        
        if "floresta" in location_lower or "caverna" in location_lower:
            combat_chance = 0.7  # More combat in dangerous areas
            npc_chance = 0.2
        elif "cidade" in location_lower or "aldeia" in location_lower:
            combat_chance = 0.3  # Less combat in civilized areas
            npc_chance = 0.5
    
    # Roll for encounter type
    roll = random.random()
    
    if roll < combat_chance:
        return "combat"
    elif roll < combat_chance + npc_chance:
        return "npc"
    else:
        return "environmental"

def _generate_combat_encounter(character_level: int, location: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a combat encounter.
    
    Args:
        character_level: The character's level
        location: Optional location name
        
    Returns:
        Dictionary with combat encounter details
    """
    # Determine enemy type based on location and level
    enemy_type = _select_enemy_type(character_level, location)
    
    # Create enemy instance
    enemy = _create_enemy(enemy_type, character_level)
    
    # Create encounter result
    return {
        "type": "combat",
        "enemy": enemy.to_dict(),
        "message": f"Um {enemy.name} aparece!",
        "combat": True
    }

def _select_enemy_type(character_level: int, location: Optional[str] = None) -> str:
    """
    Select an appropriate enemy type based on level and location.
    
    Args:
        character_level: The character's level
        location: Optional location name
        
    Returns:
        Enemy type name
    """
    # Basic enemies for low levels
    tier1_enemies = ["Lobo Selvagem", "Bandido", "Goblin", "Aranha Gigante"]
    
    # Medium difficulty enemies
    tier2_enemies = ["Guerreiro Orc", "Esqueleto", "Zumbi", "Ladrão"]
    
    # Harder enemies
    tier3_enemies = ["Troll", "Ogro", "Elemental", "Cultista"]
    
    # Boss-level enemies
    tier4_enemies = ["Dragão Jovem", "Lich", "Demônio Menor", "Gigante"]
    
    # Select tier based on level
    if character_level <= 3:
        enemy_pool = tier1_enemies
    elif character_level <= 6:
        enemy_pool = tier1_enemies + tier2_enemies
    elif character_level <= 10:
        enemy_pool = tier2_enemies + tier3_enemies
    else:
        enemy_pool = tier3_enemies + tier4_enemies
    
    # Adjust based on location if provided
    if location:
        location_lower = location.lower()
        
        if "floresta" in location_lower:
            forest_enemies = ["Lobo Selvagem", "Urso", "Aranha Gigante", "Druida Corrompido"]
            enemy_pool = [e for e in enemy_pool if e in forest_enemies] or enemy_pool
        elif "caverna" in location_lower:
            cave_enemies = ["Goblin", "Troll", "Morcego Gigante", "Slime"]
            enemy_pool = [e for e in enemy_pool if e in cave_enemies] or enemy_pool
    
    # Select random enemy from pool
    return random.choice(enemy_pool)

def _create_enemy(enemy_type: str, character_level: int) -> Enemy:
    """
    Create an enemy instance based on type and level.
    
    Args:
        enemy_type: The type of enemy
        character_level: The character's level
        
    Returns:
        Enemy instance
    """
    # Base stats
    base_hp = 10
    base_damage = (1, 4)
    
    # Adjust level based on character level
    enemy_level = max(1, character_level - 1 + random.randint(-1, 1))
    
    # Scale stats based on level
    hp = base_hp + (enemy_level * 5)
    min_damage, max_damage = base_damage
    damage = (min_damage + enemy_level // 2, max_damage + enemy_level)
    
    # Create enemy
    enemy = Enemy(
        name=enemy_type,
        description=f"Um {enemy_type} hostil.",
        level=enemy_level,
        max_hp=hp,
        current_hp=hp,
        attack_damage=damage,
        defense=enemy_level // 2,
        xp_reward=10 * enemy_level,
        gold_reward=(5 * enemy_level, 15 * enemy_level)
    )
    
    return enemy

def _generate_npc_encounter(character_level: int, location: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate an NPC encounter.
    
    Args:
        character_level: The character's level
        location: Optional location name
        
    Returns:
        Dictionary with NPC encounter details
    """
    # NPC types
    npc_types = [
        "Mercador Viajante", "Aventureiro Ferido", "Peregrino", 
        "Caçador", "Refugiado", "Bardo", "Eremita"
    ]
    
    # Select NPC type
    npc_type = random.choice(npc_types)
    
    # Generate message
    messages = [
        f"Você encontra um {npc_type} no caminho.",
        f"Um {npc_type} acena para você à distância.",
        f"Um {npc_type} se aproxima cautelosamente."
    ]
    
    return {
        "type": "npc",
        "npc": npc_type,
        "message": random.choice(messages),
        "combat": False
    }

def _generate_environmental_encounter(character_level: int, location: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate an environmental encounter.
    
    Args:
        character_level: The character's level
        location: Optional location name
        
    Returns:
        Dictionary with environmental encounter details
    """
    # Environmental events
    events = [
        "Você encontra pegadas estranhas no chão.",
        "Uma brisa fria sopra, trazendo um cheiro peculiar.",
        "Você ouve sons distantes que não consegue identificar.",
        "O céu escurece repentinamente, mas logo volta ao normal.",
        "Você encontra os restos de um acampamento abandonado."
    ]
    
    # Adjust based on location
    if location:
        location_lower = location.lower()
        
        if "floresta" in location_lower:
            forest_events = [
                "Os pássaros silenciam repentinamente.",
                "Você nota marcas de garras em uma árvore próxima.",
                "Uma névoa estranha começa a se formar entre as árvores."
            ]
            events.extend(forest_events)
        elif "caverna" in location_lower:
            cave_events = [
                "Você ouve o som de água pingando nas profundezas.",
                "Cristais estranhos brilham nas paredes.",
                "Um vento inexplicável apaga momentaneamente sua tocha."
            ]
            events.extend(cave_events)
    
    return {
        "type": "environmental",
        "message": random.choice(events),
        "combat": False
    }