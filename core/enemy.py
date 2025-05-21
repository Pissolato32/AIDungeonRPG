"""
Enemy module for the RPG game.
"""

import random  # Movido para o topo do arquivo
from dataclasses import dataclass, field
from typing import List, Tuple

from .combat_stats import (  # Corrigido para CharacterStats e usando import relativo
    CharacterStats,
)


@dataclass
class Enemy(CharacterStats):  # Corrigido para herdar de CharacterStats
    """
    Represents an enemy in the RPG game.
    """

    # Basic enemy identifiers and descriptors
    name: str = "Unnamed Enemy"
    level: int = 1
    description: str = ""

    # Combat stats are inherited from CombatStats (e.g., health, max_health,
    # strength, agility, defense)
    # Nota: CharacterStats atualmente fornece health, attack, defense, aim_skill.

    # Specific damage range for this enemy type, to align with
    # AttackActionHandler
    attack_damage_min: int = 3
    attack_damage_max: int = 8

    # Combat stats
    xp_reward: int = 10
    gold_reward: Tuple[int, int] = field(default_factory=lambda: (5, 15))

    # Loot table
    possible_loot: List[str] = field(default_factory=list)
    loot_chance: float = 0.5

    def get_xp_reward(self) -> int:
        """Get the XP reward for defeating this enemy."""
        return self.xp_reward * self.level

    def get_gold_reward(self) -> int:
        """Get a random gold reward within the range."""

        min_gold, max_gold = self.gold_reward
        return random.randint(min_gold, max_gold)
