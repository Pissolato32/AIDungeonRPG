"""
Models for game entities.
"""

from dataclasses import dataclass, field  # type: ignore
from typing import Any, Dict, List, Optional, Union  # Added Union


@dataclass
class Character:
    """Represents a player character in the game."""

    name: str
    character_class: str
    race: str
    description: str = ""
    level: int = 1
    experience: int = 0
    attributes: Dict[str, int] = field(default_factory=dict)
    inventory: List[Union[str, Dict[str, Any]]] = field(default_factory=list)
    equipment: Dict[str, Any] = field(default_factory=dict)
    skills: List[str] = field(default_factory=list)
    survival_stats: Dict[str, int] = field(default_factory=dict)
    status_effects: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def current_hp(self) -> int:
        return self.attributes.get("current_hp", 0)

    @property
    def max_hp(self) -> int:
        return self.attributes.get("max_hp", 0)

    @property
    def current_stamina(self) -> int:
        return self.attributes.get("current_stamina", 0)

    @property
    def max_stamina(self) -> int:
        return self.attributes.get("max_stamina", 0)

    @property
    def current_hunger(self) -> int:
        return self.survival_stats.get("current_hunger", 0)

    @property
    def max_hunger(self) -> int:
        return max(self.survival_stats.get("max_hunger", 1), 1)  # nunca menor que 1

    @property
    def current_thirst(self) -> int:
        return max(self.survival_stats.get("current_thirst", 1), 1)  # nunca menor que 1

    @property
    def max_thirst(self) -> int:
        return max(self.survival_stats.get("max_thirst", 1), 1)  # nunca menor que 1

    @property
    def agility(self) -> int:
        """Gets the agility attribute from the attributes dictionary."""
        return self.attributes.get("agility", 0)

    @property
    def strength(self) -> int:
        """Gets the strength attribute from the attributes dictionary."""
        return self.attributes.get("strength", 0)

    @property
    def health(self) -> int:
        """Gets the current health points (current_hp) from the attributes dictionary."""
        return self.attributes.get("current_hp", 0)

    @health.setter
    def health(self, value: int) -> None:
        """Sets the current health points (current_hp), clamping between 0 and max_hp."""
        # Uses the existing max_hp property to get the maximum health value
        self.attributes["current_hp"] = max(0, min(value, self.max_hp))

    # Você pode adicionar mais properties conforme a necessidade, ex:
    # @property
    # def mana(self) -> int:
    #     return self.attributes.get("mana", 0)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Character":
        """Create a character from a dictionary."""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert character to a dictionary."""
        return {
            "name": self.name,
            "character_class": self.character_class,
            "race": self.race,
            "description": self.description,
            "level": self.level,
            "experience": self.experience,
            "attributes": self.attributes,
            "inventory": self.inventory,
            "equipment": self.equipment,
            "skills": self.skills,
            "survival_stats": self.survival_stats,
            "status_effects": self.status_effects,
        }


@dataclass
class NPCBase:
    """Base class for all NPCs."""

    id: Optional[int] = field(default=None)
    name: str = field(default="")
    description: str = field(default="")

    quests: List[str] = field(default_factory=list)
    dialogue: Dict[str, str] = field(default_factory=dict)

    # Novos campos
    race: str = field(default="Human")  # Raça do NPC
    profession: str = field(default="Unknown")  # Profissão ou papel
    personality: str = field(default="Neutral")  # Traço de personalidade
    level: int = field(default=1)  # Nível de dificuldade ou poder do NPC

    is_hostile: bool = field(default=False)  # Se o NPC é hostil ou amigável
    location_id: Optional[str] = field(default=None)  # Onde o NPC se encontra no mundo

    def speak(self, topic: str) -> str:
        """Retorna a fala do NPC sobre um tópico, ou frase padrão."""
        return self.dialogue.get(topic, "They have nothing to say about that.")

    def add_quest(self, quest_name: str) -> None:
        """Adiciona uma quest à lista do NPC."""
        if quest_name not in self.quests:
            self.quests.append(quest_name)

    def describe(self) -> str:
        """Descrição detalhada do NPC."""
        return (
            f"{self.name} is a level {self.level} {self.race} {self.profession} "
            f"who seems {self.personality}. {self.description}"
        )
