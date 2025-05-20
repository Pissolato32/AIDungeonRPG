# filepath: c:\Users\rodri\Desktop\REPLIT RPG\core\npc.py
"""NPC module for managing non-player characters in the game world."""

import random
from dataclasses import dataclass, field, asdict
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    TypedDict,  # Ensure TypedDict is imported
    cast,
)  # Ensure these are imported
import uuid  # Ensure uuid is imported if generating IDs

from .models import NPCBase

# Type definitions
DispositionType = Literal["hostile", "neutral", "friendly"]
ActionType = Literal["greet", "trade", "quest", "ask_about", "small_talk"]


class DialogueOption(TypedDict):
    """Type definition for dialogue options."""

    text: str
    action: ActionType
    topic: Optional[str]


class QuestData(TypedDict):
    """Type definition for quest data."""

    id: str
    name: str
    description: str
    reward: Dict[str, Any]
    status: Literal["available", "active", "completed", "failed"]


class DailySchedule(TypedDict):
    """Type definition for NPC daily schedule."""

    time: str
    activity: str
    location: str


class InteractionResult(TypedDict):
    """Type definition for interaction results."""

    success: bool
    message: str
    options: List[DialogueOption]


DialogueDict = Dict[str, List[DialogueOption]]


@dataclass
class NPC:
    """Represents an NPC in the game world.

    Attributes:
        race: The NPC's species or racial background
        profession: The NPC's occupation or role
        personality: Core personality traits and tendencies
        current_state: Current mood and physical condition
        faction: Group affiliation or allegiance
        knowledge: Topics and information known to the NPC
        skills: Abilities and proficiencies
        available_quests: Quests that can be offered
        interaction_count: Number of player interactions
        last_interaction: Type of most recent interaction
        relationship_level: Disposition toward player (-100 to 100)
        daily_schedule: Time-based location and activities
        dialogue_options: Available conversation choices
    """

    # Non-default fields (required) must come first
    name: str  # Inherited from NPCBase, likely required
    level: int  # This was the problematic field, now correctly positioned

    # Fields with default values (optional)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    race: Optional[str] = field(default="Human")  # Assuming default for race
    profession: Optional[str] = field(
        default="Commoner"
    )  # Changed from profession to role for consistency  # Assuming default for profession
    personality: Optional[str] = field(
        default="Neutral"
    )  # Assuming default for personality
    current_mood: Optional[str] = field(
        default="Normal"
    )  # Renamed from current_state for consistency with NPCBase
    disposition: Optional[str] = field(
        default="neutral"
    )  # e.g., "friendly", "neutral", "hostile"

    # Other fields that might have defaults or be initialized as empty
    faction: Optional[str] = field(default="Neutral")  # Assuming default for faction
    knowledge: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    available_quests: List[QuestData] = field(default_factory=list)
    interaction_count: int = field(default=0)
    last_interaction: ActionType = field(default="greet")
    relationship_level: int = field(default=0)
    daily_schedule: List[DailySchedule] = field(default_factory=list)
    dialogue_options: DialogueDict = field(default_factory=dict)
    # Attributes for NPCs, similar to Characters
    attributes: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPC":
        """Creates an NPC object from a dictionary."""
        # Ensure all fields expected by the dataclass constructor are present
        # or have defaults.
        # The 'level' field was identified as potentially problematic if not handled.
        # If 'level' is not in data, it will use the default from the dataclass if defined,
        # or raise an error if it's a required field without a default.
        # Based on the current dataclass definition, 'level' is required.

        # Map NPCBase fields to NPC dataclass fields if names differ or need defaults
        npc_id = data.get("id", str(uuid.uuid4()))  # Generate ID if not present
        name = data.get("name", "Unknown NPC")
        level = data.get("level", 1)  # Default level to 1 if not provided
        race = data.get("race", "Human")
        profession = data.get("profession", "Commoner")
        personality = data.get("personality", "Neutral")
        current_mood = data.get("current_mood", "Normal")
        disposition = data.get("disposition", "neutral")
        faction = data.get("faction", "Neutral")
        knowledge = data.get("knowledge", [])
        skills = data.get("skills", [])
        available_quests = data.get("available_quests", [])
        interaction_count = data.get("interaction_count", 0)
        last_interaction = data.get("last_interaction", "greet")
        relationship_level = data.get("relationship_level", 0)
        daily_schedule = data.get("daily_schedule", [])
        dialogue_options = data.get("dialogue_options", {})
        attributes = data.get("attributes", {})

        return cls(
            id=npc_id,
            name=name,
            level=level,
            race=race,
            profession=profession,
            personality=personality,
            current_mood=current_mood,
            disposition=disposition,
            faction=faction,
            knowledge=knowledge,
            skills=skills,
            available_quests=available_quests,
            interaction_count=interaction_count,
            last_interaction=last_interaction,  # type: ignore
            relationship_level=relationship_level,
            daily_schedule=daily_schedule,
            dialogue_options=dialogue_options,
            attributes=attributes,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Converts the NPC object to a dictionary."""
        # Use asdict to convert the dataclass instance to a dictionary
        return asdict(self)

    def get_greeting(self) -> str:
        """Generate a contextual greeting based on NPC's disposition.

        The greeting considers the relationship level with the player and
        the NPC's current state to select an appropriate response.

        Returns:
            str: A contextually appropriate greeting message
        """
        greetings: Dict[DispositionType, List[str]] = {
            "hostile": [
                "O que você quer?",
                "*olha com desconfiança*",
                "Não tenho nada para falar com você.",
            ],
            "neutral": ["Olá viajante.", "Bem-vindo.", "Como posso ajudar?"],
            "friendly": [
                "Ah, que bom ver você novamente!",
                "Que os deuses abençoem seu caminho!",
                "Estava esperando sua visita!",
            ],
        }

        disposition: DispositionType = cast(
            DispositionType,
            (
                "hostile"
                if self.relationship_level < -30
                else "friendly" if self.relationship_level > 30 else "neutral"
            ),
        )

        return random.choice(greetings[disposition])

    def get_dialogue_options(self, context: Dict[str, Any]) -> List[DialogueOption]:
        """Generate relevant dialogue options based on context.

        The options are determined by the NPC's profession, knowledge,
        and relationship level with the player.

        Args:
            context: Current game state and interaction details

        Returns:
            List[DialogueOption]: Available conversation options
        """
        options: List[DialogueOption] = []

        # Add profession-specific options
        if self.profession == "Merchant":
            options.append(
                {
                    "text": "Gostaria de ver seus produtos",
                    "action": "trade",
                    "topic": None,
                }
            )
        elif self.profession == "Quest Giver":
            options.append(
                {
                    "text": "Tem alguma tarefa para mim?",
                    "action": "quest",
                    "topic": None,
                }
            )

        # Add knowledge-based options
        for topic in self.knowledge:
            options.append(
                {
                    "text": f"Perguntar sobre {topic}",
                    "action": "ask_about",
                    "topic": topic,
                }
            )

        # Add relationship-based options
        if self.relationship_level > 0:
            options.append(
                {
                    "text": "Como você tem passado?",
                    "action": "small_talk",
                    "topic": None,
                }
            )

        return options

    def interact(
        self, action: ActionType, context: Dict[str, Any]
    ) -> InteractionResult:
        """Process an interaction with the NPC.

        Updates interaction history and generates appropriate responses
        based on the type of interaction and current context.

        Args:
            action: The type of interaction being performed
            context: Current game state and interaction details

        Returns:
            InteractionResult containing response message and options
        """
        self.interaction_count += 1
        self.last_interaction = action

        response: InteractionResult = {"success": True, "message": "", "options": []}

        if action == "greet":
            response["message"] = self.get_greeting()
            response["options"] = self.get_dialogue_options(context)

        return response
