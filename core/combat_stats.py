"""
Base combat statistics system.

This module provides the base class for combat statistics that can be used by both
characters and enemies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class CombatStats:
    """Base class for combat statistics."""

    # Basic stats
    health: int = 100
    max_health: int = 100
    stamina: int = 100
    max_stamina: int = 100

    # Combat stats
    strength: int = 10
    agility: int = 10
    defense: int = 0

    # Combat modifiers
    damage_bonus: int = 0
    defense_bonus: int = 0
    critical_chance: float = 0.1
    dodge_chance: float = 0.1

    # Status effects and resistances
    resistances: Dict[str, float] = field(default_factory=dict)
    status_effects: List[Dict[str, Any]] = field(default_factory=list)

    def modify_health(self, amount: int) -> int:
        """
        Modify health by given amount.

        Args:
            amount: Amount to modify health by (positive for healing, negative for damage)

        Returns:
            Actual amount modified
        """
        old_health = self.health
        self.health = max(0, min(self.max_health, self.health + amount))
        return self.health - old_health

    def modify_stamina(self, amount: int) -> int:
        """
        Modify stamina by given amount.

        Args:
            amount: Amount to modify stamina by

        Returns:
            Actual amount modified
        """
        old_stamina = self.stamina
        self.stamina = max(0, min(self.max_stamina, self.stamina + amount))
        return self.stamina - old_stamina

    def add_status_effect(
        self,
        effect_type: str,
        duration: int,
        strength: int = 1,
        data: Optional[Dict] = None,
    ) -> None:
        """
        Add a status effect.

        Args:
            effect_type: Type of effect
            duration: Number of turns the effect lasts
            strength: Strength of the effect
            data: Additional effect data
        """
        self.status_effects.append(
            {
                "type": effect_type,
                "duration": duration,
                "strength": strength,
                "data": data or {},
            }
        )

    def remove_status_effect(self, effect_type: str) -> None:
        """
        Remove all status effects of given type.

        Args:
            effect_type: Type of effect to remove
        """
        self.status_effects = [
            effect for effect in self.status_effects if effect["type"] != effect_type
        ]

    def update_status_effects(self) -> List[Dict]:
        """
        Update status effects durations and return expired effects.

        Returns:
            List of expired effects that were removed
        """
        expired = []
        remaining = []

        for effect in self.status_effects:
            effect["duration"] -= 1
            if effect["duration"] <= 0:
                expired.append(effect)
            else:
                remaining.append(effect)

        self.status_effects = remaining
        return expired

    def get_combat_stats(self) -> Dict[str, Any]:
        """Get current combat statistics."""
        return {
            "health": self.health,
            "max_health": self.max_health,
            "stamina": self.stamina,
            "max_stamina": self.max_stamina,
            "strength": self.strength,
            "agility": self.agility,
            "defense": self.defense + self.defense_bonus,
            "critical_chance": self.critical_chance,
            "dodge_chance": self.dodge_chance,
            "status_effects": self.status_effects.copy(),
            "resistances": self.resistances.copy(),
        }

    def get_resource_percentage(self, resource: str) -> float:
        """
        Get percentage of a resource.

        Args:
            resource: Resource to check ("health" or "stamina")

        Returns:
            Percentage of resource remaining
        """
        if resource == "health":
            return (self.health / self.max_health) * 100
        if resource == "stamina":
            return (self.stamina / self.max_stamina) * 100
        return 0.0
