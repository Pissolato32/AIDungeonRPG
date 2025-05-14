import random
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Tuple, TypeVar, Protocol
from dataclasses import dataclass, field, asdict
from abc import ABC
from utils import calculate_attribute_modifier

logger = logging.getLogger(__name__)

# Type variables for generics
T = TypeVar('T')

class GameEntity(Protocol):
    """Protocol defining common methods for game entities."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> T:
        """Create an object from a dictionary."""
        ...


@dataclass
class BaseEntity(ABC):
    """Base class for all game entities with common functionality."""

    name: str
    description: str = ""

    # Metadata
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> T:
        """
        Create an entity from a dictionary.

        This is a basic implementation that should be overridden by subclasses
        if they need special handling.
        """
        # Filter out keys that aren't in the class annotations
        filtered_data = {k: v for k, v in data.items() if k in cls.__annotations__}
        return cls(**filtered_data)


@dataclass
class CombatEntity(BaseEntity):
    """Base class for entities that can engage in combat."""

    # Health and combat stats
    level: int = 1
    max_hp: int = 10
    current_hp: int = 10
    defense: int = 0
    attack_damage: Tuple[int, int] = (1, 4)

    def is_alive(self) -> bool:
        """Check if the entity is alive."""
        return self.current_hp > 0

    def take_damage(self, amount: int) -> Tuple[int, int]:
        """
        Apply damage to the entity considering its defense.

        Args:
            amount: Amount of damage to apply

        Returns:
            Tuple with current HP and effective damage
        """
        damage_after_defense = max(1, amount - self.defense)
        self.current_hp = max(0, self.current_hp - damage_after_defense)
        return self.current_hp, damage_after_defense

    def heal(self, amount: int) -> int:
        """
        Heal the entity.

        Args:
            amount: Amount of healing to apply

        Returns:
            New current HP
        """
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp


@dataclass
class Character(CombatEntity):
    """
    Represents a player character in the RPG game.

    Attributes cover basic stats, inventory, progression, and survival mechanics.
    """
    # Required attributes (must be provided at creation)
    character_class: str = "Warrior"
    race: str = "Human"

    # Base attributes
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    # Attribute modifiers (calculated automatically)
    strength_mod: int = field(init=False, default=0)
    dexterity_mod: int = field(init=False, default=0)
    constitution_mod: int = field(init=False, default=0)
    intelligence_mod: int = field(init=False, default=0)
    wisdom_mod: int = field(init=False, default=0)
    charisma_mod: int = field(init=False, default=0)

    # Resource stats
    max_stamina: int = 10
    current_stamina: int = 10

    # Survival stats
    max_hunger: int = 100
    current_hunger: int = 100
    max_thirst: int = 100
    current_thirst: int = 100

    # Inventory and equipment
    inventory: List[str] = field(default_factory=lambda: ["Basic Sword", "Health Potion"])
    equipment: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "weapon": None, "armor": None, "helmet": None,
        "gloves": None, "boots": None, "accessory": None
    })

    # Progression and resources
    gold: int = 50
    experience: int = 0

    # Status effects
    status_effects: List[Dict[str, Any]] = field(default_factory=list)

    # User identification
    user_id: str = ""

    def __post_init__(self):
        """Post-initialization setup."""
        # Calculate attribute modifiers
        self._calculate_attribute_modifiers()

        # Set combat stats based on attributes
        self._update_combat_stats()

        # Log character creation
        logger.info(f"Character created: {self.name} (Level {self.level})")

    def _calculate_attribute_modifiers(self) -> None:
        """Calculate all attribute modifiers."""
        self.strength_mod = calculate_attribute_modifier(self.strength)
        self.dexterity_mod = calculate_attribute_modifier(self.dexterity)
        self.constitution_mod = calculate_attribute_modifier(self.constitution)
        self.intelligence_mod = calculate_attribute_modifier(self.intelligence)
        self.wisdom_mod = calculate_attribute_modifier(self.wisdom)
        self.charisma_mod = calculate_attribute_modifier(self.charisma)

    def _update_combat_stats(self) -> None:
        """Update combat stats based on attributes."""
        # Attack damage based on strength
        self.attack_damage = (1 + self.strength_mod, 4 + self.strength_mod * 2)

        # Defense based on dexterity
        self.defense = self.dexterity_mod

        # Max HP based on constitution
        constitution_bonus = self.constitution_mod * 2
        self.max_hp = 20 + constitution_bonus

        # Max stamina based on constitution
        stamina_bonus = max(0, self.constitution_mod)
        self.max_stamina = 10 + stamina_bonus

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """Create a character from a dictionary or return if already Character."""
        if isinstance(data, cls):
            return data  # Já é um Character, retorna direto
        # Remove calculated fields that shouldn't be passed to the constructor
        calculated_fields = [
            'attack_damage', 'defense', 
            'strength_mod', 'dexterity_mod', 'constitution_mod', 
            'intelligence_mod', 'wisdom_mod', 'charisma_mod'
        ]

        filtered_data = {k: v for k, v in data.items() if k not in calculated_fields}

        # Handle class field name difference
        if 'class' in filtered_data and 'character_class' not in filtered_data:
            filtered_data['character_class'] = filtered_data.pop('class')

        return cls(**filtered_data)

    def validate_action(self, action: str, cost: int) -> bool:
        """
        Validate if the character can perform an action based on stamina cost.

        Args:
            action: Action name
            cost: Stamina cost

        Returns:
            Boolean indicating if the action is possible
        """
        if self.current_stamina < cost:
            from translations import get_text
            logger.warning(get_text("character.not_enough_stamina", None, self.name, action))
            return False
        return True

    def gain_experience(self, amount: int) -> bool:
        """
        Add experience to the character and check for level up.

        Args:
            amount: Amount of experience to add

        Returns:
            Boolean indicating if the character leveled up
        """
        self.experience += amount

        # Check for level up
        level_before = self.level
        self._update_level()

        # Return whether the character leveled up
        return self.level > level_before

    def _update_level(self) -> None:
        """Update character level based on experience."""
        # Simple level formula: level * 100 experience needed for next level
        while self.experience >= self.level * 100:
            self.level += 1
            self._on_level_up()

    def _on_level_up(self) -> None:
        """Apply level up bonuses."""
        # Increase max HP and stamina
        self.max_hp += 5
        self.max_stamina += 2

        # Restore to full
        self.current_hp = self.max_hp
        self.current_stamina = self.max_stamina

        # Update combat stats
        self._update_combat_stats()

        logger.info(f"Character {self.name} leveled up to {self.level}")

    def rest(self) -> Dict[str, int]:
        """
        Rest to recover HP and stamina.

        Returns:
            Dictionary with recovered amounts
        """
        hp_recovery = max(1, self.max_hp // 4)
        stamina_recovery = max(1, self.max_stamina // 2)

        old_hp = self.current_hp
        old_stamina = self.current_stamina

        self.current_hp = min(self.max_hp, self.current_hp + hp_recovery)
        self.current_stamina = min(self.max_stamina, self.current_stamina + stamina_recovery)

        return {
            "hp_recovered": self.current_hp - old_hp,
            "stamina_recovered": self.current_stamina - old_stamina
        }

    def attack(self, target: CombatEntity) -> Tuple[int, bool]:
        """
        Attack a target.

        Args:
            target: The entity to attack

        Returns:
            Tuple with damage dealt and hit success
        """
        # Roll for damage
        min_damage, max_damage = self.attack_damage
        damage = random.randint(min_damage, max_damage)

        # Apply damage to target
        current_hp, effective_damage = target.take_damage(damage)

        return effective_damage, True

    @property
    def class_(self) -> str:
        """Return the character class (for compatibility)."""
        return self.character_class


@dataclass
class Enemy(CombatEntity):
    """
    Represents an enemy in the RPG game.

    Attributes describe enemy characteristics for combat and progression.
    """
    # Combat rewards
    experience_reward: int = 25
    gold_reward: Tuple[int, int] = (5, 15)

    # Loot and abilities
    loot_table: List[str] = field(default_factory=list)
    abilities: List[str] = field(default_factory=list)

    def take_damage(self, amount: int) -> Tuple[int, int]:
        """
        Apply damage to the enemy considering its defense.

        Args:
            amount: Amount of damage to apply

        Returns:
            Tuple with current HP and effective damage
        """
        damage_after_defense = max(1, amount - self.defense)
        self.current_hp = max(0, self.current_hp - damage_after_defense)
        logger.info("Enemy took damage", extra={"enemy_name": self.name, "damage": damage_after_defense})
        return self.current_hp, damage_after_defense

    def attack(self, target: CombatEntity) -> Tuple[int, bool]:
        """
        Attack a target.

        Args:
            target: The entity to attack

        Returns:
            Tuple with damage dealt and hit success
        """
        # Roll for damage
        min_damage, max_damage = self.attack_damage
        damage = random.randint(min_damage, max_damage)

        # Apply damage to target
        current_hp, effective_damage = target.take_damage(damage)

        return effective_damage, True

    def get_gold_reward(self) -> int:
        """
        Get the gold reward for defeating this enemy.

        Returns:
            Amount of gold
        """
        min_gold, max_gold = self.gold_reward
        return random.randint(min_gold, max_gold)


@dataclass
class Quest(BaseEntity):
    """
    Represents a quest in the RPG game.

    Attributes describe objectives, rewards, and quest progress.
    """
    difficulty: int = 1
    reward_gold: int = 50
    reward_xp: int = 100
    reward_items: List[str] = field(default_factory=list)
    status: str = "active"
    progress: int = 0

    def update_progress(self, amount: int) -> int:
        """
        Update quest progress.

        Args:
            amount: Amount of progress to add

        Returns:
            Current progress
        """
        self.progress = min(100, self.progress + amount)
        if self.progress >= 100:
            self.complete()
        return self.progress

    def complete(self) -> None:
        """Mark the quest as completed."""
        self.status = "completed"
        self.progress = 100
        logger.info(f"Quest completed: {self.name}")

    def fail(self) -> None:
        """Mark the quest as failed."""
        self.status = "failed"
        logger.warning(f"Quest failed: {self.name}")

    def is_completed(self) -> bool:
        """Check if the quest is completed."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if the quest is failed."""
        return self.status == "failed"

    def is_active(self) -> bool:
        """Check if the quest is active."""
        return self.status == "active"