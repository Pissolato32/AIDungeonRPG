"""
Enemy module for the RPG game.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple
from core.models import CombatEntity

@dataclass
class Enemy(CombatEntity):
    """
    Represents an enemy in the RPG game.
    """
    # Combat stats
    xp_reward: int = 10
    gold_reward: Tuple[int, int] = (5, 15)
    
    # Loot table
    possible_loot: List[str] = field(default_factory=list)
    loot_chance: float = 0.5
    
    def get_xp_reward(self) -> int:
        """Get the XP reward for defeating this enemy."""
        return self.xp_reward * self.level
    
    def get_gold_reward(self) -> int:
        """Get a random gold reward within the range."""
        import random
        min_gold, max_gold = self.gold_reward
        return random.randint(min_gold, max_gold)