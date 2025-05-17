"""
Prompt manager for the game engine.

This module handles the creation and management of prompts for the AI model
interactions, ensuring consistent and contextual responses.
"""

import logging
from typing import Dict, Any, List, TypedDict, Literal
from dataclasses import dataclass
from core.models import Character
from typing_extensions import NotRequired

logger = logging.getLogger(__name__)


class NPCDetails(TypedDict, total=False):
    """Type definition for NPC details."""

    race: str
    profession: str
    personality: str
    knowledge: List[str]
    current_state: str
    interactions: int
    quests: NotRequired[List[str]]
    attitude: str


class QuestDetails(TypedDict):
    """Type definition for quest information."""

    name: str
    description: str
    reward: Dict[str, Any]
    difficulty: str
    requirements: List[str]


class CombatEnemy(TypedDict):
    """Type definition for enemy in combat."""

    name: str
    level: int
    current_hp: int
    max_hp: int


InteractionType = Literal["talk", "trade", "quest"]


@dataclass
class GameState:
    """Represents the current state of the game world.

    Attributes:
        current_location: Name of the current location
        scene_description: Description of the current scene
        npcs_present: List of NPCs in the current location
        known_npcs: Dictionary of known NPCs and their details
    """

    current_location: str
    scene_description: str
    npcs_present: List[str]
    known_npcs: Dict[str, NPCDetails]


class PromptManager:
    """Manages prompts for AI interactions in the game.

    This class provides methods to generate contextual prompts for various
    game interactions, ensuring consistent and engaging AI responses.
    """

    @staticmethod
    def get_action_prompt(
        action: str, details: str, character: Character, game_state: GameState
    ) -> str:
        """Generate a prompt for player actions.

        Args:
            action: The type of action being performed
            details: Additional details about the action
            character: The player's character information
            game_state: Current state of the game world

        Returns:
            str: A formatted prompt for the AI model
        """
        base_prompt = PromptManager._get_base_prompt(character, game_state)

        if action == "talk":
            npc_name = details.strip()
            npc_details = game_state.known_npcs.get(npc_name, {})
            base_prompt += PromptManager._get_talk_prompt()

            if npc_details:
                base_prompt += PromptManager._format_npc_details(npc_name, npc_details)

            base_prompt += PromptManager._get_talk_conclusion(details)

        return base_prompt

    @staticmethod
    def _get_base_prompt(character: Character, game_state: GameState) -> str:
        """Generate the base prompt with game state and character info.

        Args:
            character: The player's character information
            game_state: Current state of the game world

        Returns:
            str: Base prompt with context information
        """
        npcs = ", ".join(game_state.npcs_present or []) or "Nenhum"
        return (
            "Você é o Mestre de um jogo de RPG medieval fantastico. "
            "Como narrador, sua missão é criar uma experiência imersiva "
            "e envolvente para o jogador.\n\n"
            f"Local atual: {game_state.current_location}\n"
            f"Descrição: {game_state.scene_description}\n"
            f"NPCs presentes: {npcs}\n\n"
            f"Personagem do jogador:\n"
            f"- Nome: {character.name}\n"
            f"- Raça: {character.race}\n"
            f"- Classe: {character.character_class}\n"
            f"- Nível: {character.level}\n"
            f"- HP: {character.current_hp}/{character.max_hp}\n"
        )

    @staticmethod
    def _get_talk_prompt() -> str:
        """Generate the standard NPC interaction prompt section.

        Returns:
            str: Guidelines for NPC interaction dialogue
        """
        return (
            "\nVocê está controlando um NPC em uma conversa. "
            "Crie uma interação envolvente que:\n"
            "1. Reflita a personalidade e atitude do NPC\n"
            "2. Use informações prévias se o jogador já conhece o NPC\n"
            "3. Revele detalhes do mundo e possíveis missões\n"
            "4. Mantenha consistência com interações anteriores\n"
            "5. Permita que o jogador faça escolhas significativas\n\n"
        )

    @staticmethod
    def _format_npc_details(npc_name: str, details: NPCDetails) -> str:
        """Format NPC details for prompt inclusion.

        Args:
            npc_name: Name of the NPC
            details: Dictionary containing NPC information

        Returns:
            str: Formatted NPC details for the prompt
        """
        knowledge = ", ".join(details.get("knowledge", []))
        npc_info = [
            f"Detalhes do NPC ({npc_name}):",
            f"- Raça: {details.get('race', 'desconhecida')}",
            f"- Profissão: {details.get('profession', 'desconhecida')}",
            f"- Personalidade: {details.get('personality', 'variada')}",
            f"- Conhecimento: {knowledge}",
            f"- Estado atual: {details.get('current_state', 'normal')}",
            f"- Interações: {details.get('interactions', 0)}",
        ]

        quests = details.get("quests", [])
        if quests:
            quest_names = ", ".join(quests[:2])
            npc_info.append(f"- Quests: {quest_names}")

        return "\n".join(npc_info) + "\n"

    @staticmethod
    def _get_talk_conclusion(npc_name: str) -> str:
        """Generate the conclusion of a talk prompt.

        Args:
            npc_name: Name of the NPC being talked to

        Returns:
            str: Concluding prompt instructions
        """
        return (
            f"\nO jogador está tentando conversar com '{npc_name}'. "
            "Crie um diálogo realista e interessante que desenvolva "
            "a narrativa e o mundo do jogo.\n"
        )

    @staticmethod
    def get_combat_prompt(character: Character, enemy: CombatEnemy, action: str) -> str:
        """Generate a prompt for combat.

        Args:
            character: The player character's information
            enemy: The enemy's combat stats
            action: The combat action being performed

        Returns:
            str: A formatted combat prompt
        """
        return (
            "You are the Game Master for a medieval fantasy RPG.\n"
            f"The player is in combat with {enemy['name']}.\n\n"
            f"Character information:\n"
            f"- Name: {character.name}\n"
            f"- Race: {character.race}\n"
            f"- Class: {character.character_class}\n"
            f"- Level: {character.level}\n"
            f"- HP: {character.current_hp}/{character.max_hp}\n\n"
            f"Enemy information:\n"
            f"- Name: {enemy['name']}\n"
            f"- Level: {enemy['level']}\n"
            f"- HP: {enemy['current_hp']}/{enemy['max_hp']}\n\n"
            f"The player is performing the combat action '{action}'.\n\n"
            "Response format:\n"
            "{\n"
            '    "success": true/false,\n'
            '    "message": "Combat narration",\n'
            '    "damage_dealt": 0,\n'
            '    "damage_taken": 0,\n'
            '    "combat_ended": true/false\n'
            "}\n\n"
            "Be brief but vivid in your combat descriptions.\n"
        )
