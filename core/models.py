# filepath: c:\Users\rodri\Desktop\REPLIT RPG\core\models.py
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


@dataclass
class NPCBase:
    """Base class for Non-Player Characters."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Mysterious Figure"
    description: str = "An enigmatic presence."
    # Add any other common attributes you want all NPCs to have by default
    # For example, a general disposition or a default set of dialogue.
    disposition: Literal["hostile", "neutral", "friendly"] = "neutral"


class Character:
    """Represents a player character in the game."""

    def __init__(
        self,
        name: str,
        strength: int = 8,
        dexterity: int = 8,
        constitution: int = 8,
        intelligence: int = 8,
        wisdom: int = 8,
        charisma: int = 8,
        description: str = "",
        level: int = 1,
        experience: int = 0,
        gold: int = 50,
        inventory: Optional[List[Any]] = None,
        equipment: Optional[Dict[str, Any]] = None,
        skills: Optional[List[str]] = None,
        max_hp: int = 10,  # Will be calculated by JS/CharacterManager
        current_hp: int = 10,  # Will be calculated by JS/CharacterManager
        max_stamina: int = 10,  # Will be calculated by JS/CharacterManager
        current_stamina: int = 10,  # Will be calculated by JS/CharacterManager
        id: Optional[str] = None,
        owner_session_id: Optional[str] = None,
    ):
        self.id: str = id if id else str(uuid.uuid4())
        self.owner_session_id: Optional[str] = owner_session_id
        self.name: str = name
        self.strength: int = strength
        self.dexterity: int = dexterity
        self.constitution: int = constitution
        self.intelligence: int = intelligence
        self.wisdom: int = wisdom
        self.charisma: int = charisma
        self.description: str = description
        self.level: int = level
        self.experience: int = experience
        self.gold: int = gold
        self.inventory: List[Any] = inventory if inventory is not None else []
        self.equipment: Dict[str, Any] = equipment if equipment is not None else {}
        self.skills: List[str] = skills if skills is not None else []

        # These are often derived or set by CharacterManager/JS initially
        self.max_hp: int = max_hp
        self.current_hp: int = current_hp
        self.max_stamina: int = max_stamina
        self.current_stamina: int = current_stamina

        # For compatibility with existing action handlers that expect these structures
        self.attributes: Dict[str, Any] = {
            "strength": self.strength,
            "dexterity": self.dexterity,
            "constitution": self.constitution,
            "intelligence": self.intelligence,
            "wisdom": self.wisdom,
            "charisma": self.charisma,
            "current_hp": self.current_hp,
            "max_hp": self.max_hp,
            "current_stamina": self.current_stamina,
            "max_stamina": self.max_stamina,
        }
        self.survival_stats: Dict[str, Any] = {  # Example defaults
            "current_hunger": 100,
            "max_hunger": 100,
            "current_thirst": 100,
            "max_thirst": 100,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize character data to a dictionary."""
        return {
            "id": self.id,
            "owner_session_id": self.owner_session_id,
            "name": self.name,
            "strength": self.strength,
            "dexterity": self.dexterity,
            "constitution": self.constitution,
            "intelligence": self.intelligence,
            "wisdom": self.wisdom,
            "charisma": self.charisma,
            "description": self.description,
            "level": self.level,
            "experience": self.experience,
            "gold": self.gold,
            "inventory": self.inventory,
            "equipment": self.equipment,
            "skills": self.skills,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "max_stamina": self.max_stamina,
            "current_stamina": self.current_stamina,
            "attributes": self.attributes,  # Save for consistency
            "survival_stats": self.survival_stats,  # Save for consistency
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Character":
        """Deserialize character data from a dictionary."""
        character = cls(
            **{
                k: v
                for k, v in data.items()
                # Exclude old fields that are no longer in __init__
                # and also special handling fields.
                if k
                not in [
                    "attributes",
                    "survival_stats",
                    "character_class",
                    "race",
                    "status_effects",  # Adicionado 'status_effects' à lista de exclusão
                ]
            }
        )
        if "attributes" in data:  # Restore attributes dict if present
            character.attributes.update(data["attributes"])
        if "survival_stats" in data:  # Restore survival_stats dict if present
            character.survival_stats.update(data["survival_stats"])
        return character
