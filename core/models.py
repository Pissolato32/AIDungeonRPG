# filepath: c:\Users\rodri\Desktop\REPLIT RPG\core\models.py
"""
Central module for core game data models and type definitions.
"""

import uuid  # Importar uuid para gerar IDs
from dataclasses import asdict, dataclass, field  # Import asdict
from typing import (  # Ensure List and Union are imported
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    TypedDict,
    Union,
)


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

    # Core combat/status attributes as direct fields
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

    # Survival stats - assuming these are also direct attributes
    # If they are complex, they could be a nested dataclass
    # For simplicity, let's assume they are direct for now, or part of 'attributes'
    # If they are direct:
    # current_hunger: int = 100
    # max_hunger: int = 100
    # current_thirst: int = 100
    # max_thirst: int = 100
    # current_fatigue: int = 0 # Example
    # max_fatigue: int = 100 # Example

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Character object to a dictionary."""
        # Use asdict to convert the dataclass instance to a dictionary
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Character":
        """Creates a Character object from a dictionary."""
        char_id = data.get("id")
        # Ensure attributes dict is loaded if present, otherwise default to empty
        attributes_data = data.get("attributes", {})

        init_args = {
            "name": data.get("name", "Unknown Character"),
            "level": data.get("level", 1),
            "owner_session_id": data.get("owner_session_id", "unknown_owner"),
            "attributes": attributes_data,  # Pass the loaded attributes dict
            "description": data.get("description", ""),
            "experience": data.get("experience", 0),
            "gold": data.get("gold", 0),
            "inventory": data.get("inventory", []),
            "equipment": data.get("equipment", {}),
            "skills": data.get("skills", []),
            "strength": data.get(
                "strength", attributes_data.get("strength", 10)
            ),  # Load from root or attributes
            "dexterity": data.get("dexterity", attributes_data.get("dexterity", 10)),
            "constitution": data.get(
                "constitution", attributes_data.get("constitution", 10)
            ),
            "intelligence": data.get(
                "intelligence", attributes_data.get("intelligence", 10)
            ),
            "wisdom": data.get("wisdom", attributes_data.get("wisdom", 10)),
            "charisma": data.get("charisma", attributes_data.get("charisma", 10)),
            "max_hp": data.get("max_hp", attributes_data.get("max_hp", 10)),
            "current_hp": data.get("current_hp", attributes_data.get("current_hp", 10)),
            "max_stamina": data.get(
                "max_stamina", attributes_data.get("max_stamina", 10)
            ),
            "current_stamina": data.get(
                "current_stamina", attributes_data.get("current_stamina", 10)
            ),
        }
        if char_id is not None:
            init_args["id"] = char_id

        return cls(**init_args)  # type: ignore[arg-type]


class CharacterType(Protocol):
    """Protocol for character objects passed to modules that don't need the full Character implementation."""

    name: str
    level: int
    attributes: Dict[str, Any]
    owner_session_id: str
    description: str
    experience: int
    gold: int
    inventory: List[Union[str, Dict[str, Any]]]
    equipment: Dict[str, Any]
    skills: List[str]
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    max_hp: int
    current_hp: int
    max_stamina: int
    current_stamina: int


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
