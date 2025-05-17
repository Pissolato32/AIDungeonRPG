"""NPC module for managing non-player characters in the game world."""

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, TypedDict, cast

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
class NPC(NPCBase):
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

    race: str = field(default="Human")
    profession: str = field(default="Commoner")
    personality: str = field(default="Neutral")
    current_state: str = field(default="Normal")
    faction: str = field(default="Neutral")

    knowledge: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    available_quests: List[QuestData] = field(default_factory=list)

    interaction_count: int = field(default=0)
    last_interaction: ActionType = field(default="greet")
    relationship_level: int = field(default=0)

    daily_schedule: List[DailySchedule] = field(default_factory=list)
    dialogue_options: DialogueDict = field(default_factory=dict)

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
