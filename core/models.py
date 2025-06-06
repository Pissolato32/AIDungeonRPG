# filepath: c:\Users\rodri\Desktop\REPLIT RPG\core\models.py
"""
Central module for core game data models and type definitions.
"""
from typing import (
    Dict,
    Any,
    TypedDict,
    Optional,
    List,
    Union,
)  # Ensure List and Union are imported
import uuid  # Importar uuid para gerar IDs
from dataclasses import dataclass, field, asdict, fields  # Import fields


@dataclass
class CombatStats:
    """Stores and manages combat-related attributes of a character."""

    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    max_hp: int = 10
    current_hp: int = 10
    max_stamina: int = 10
    current_stamina: int = 10
    attack: int = 1  # Default base attack
    defense: int = 0  # Default base defense
    aim_skill: int = 0  # Habilidade de mira, influencia headshots

    def to_dict(self) -> Dict[str, Any]:
        """Converts the CombatStats object to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CombatStats":
        """Creates a CombatStats object from a dictionary, using defaults for missing keys."""
        field_names = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)


@dataclass
class SurvivalStats:
    """Stores and manages survival attributes of a character."""

    hunger: int = 100  # Default to max
    thirst: int = 100  # Default to max
    # stamina: int = 100 # Consider if this is needed or if CombatStats.current_stamina is sufficient
    infection_risk: int = 0  # Default to no risk

    def to_dict(self) -> Dict[str, Any]:
        """Converts the SurvivalStats object to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SurvivalStats":
        """Creates a SurvivalStats object from a dictionary, using defaults for missing keys."""
        field_names = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)


@dataclass
class Character:
    """Represents a player character."""

    # Fields without default values (must be provided during initialization)
    name: str
    level: int
    owner_session_id: str

    # Fields with default values
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    attributes: Dict[str, Any] = field(
        default_factory=dict
    )  # For other/dynamic attributes
    description: str = ""
    experience: int = 0
    gold: int = 0
    inventory: List[Union[str, Dict[str, Any]]] = field(default_factory=list)
    equipment: Dict[str, Any] = field(
        default_factory=dict
    )  # e.g., {"weapon": "Sword", "armor": "Leather"}
    skills: List[str] = field(default_factory=list)  # e.g., ["Lockpicking", "Stealth"]

    # Structured stats
    stats: CombatStats = field(default_factory=CombatStats)
    survival_stats: SurvivalStats = field(default_factory=SurvivalStats)

    @property
    def is_zombie(self) -> bool:
        """Player characters are not zombies."""
        return False

    @property
    def is_infected(self) -> bool:
        """Player's infection status based on survival_stats."""
        return (
            self.survival_stats.infection_risk > 50
        )  # Example threshold, adjust as needed

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Character object to a dictionary."""
        return asdict(self)  # type: ignore[arg-type]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Character":
        """Creates a Character object from a dictionary.
        Assumes 'data' may contain 'stats' and 'survival_stats' as sub-dictionaries.
        """
        stats_data = data.get("stats", {})
        survival_stats_data = data.get("survival_stats", {})

        # Required fields for Character constructor
        name = data.get("name", "Unknown Character")
        level = data.get("level", 1)
        owner_session_id = data.get("owner_session_id", "unknown_owner")

        # Other direct fields of Character (will use dataclass defaults if not in data)
        # These are fields like id, attributes, description, experience, etc.

        character_field_names = {f.name for f in fields(cls)}

        kwargs_for_direct_fields = {}
        for field_name in character_field_names:
            if field_name not in [
                "name",
                "level",
                "owner_session_id",
                "stats",
                "survival_stats",
            ]:
                if field_name in data:
                    kwargs_for_direct_fields[field_name] = data[field_name]

        return cls(
            name=name,
            level=level,
            owner_session_id=owner_session_id,
            stats=CombatStats.from_dict(stats_data),
            survival_stats=SurvivalStats.from_dict(survival_stats_data),
            **kwargs_for_direct_fields,
        )


class NPCBase(TypedDict, total=False):
    """Base structure for NPC data.
    `total=False` allows for additional, non-defined fields."""

    name: str
    race: Optional[str]
    profession: Optional[str]
    personality: Optional[str]
    level: Optional[int]
    knowledge: Optional[List[str]]
    quests: Optional[List[str]]
    current_mood: Optional[str]
    disposition: Optional[str]  # e.g., "friendly", "neutral", "hostile"
