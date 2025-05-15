"""
Prompt manager for the game engine.

This module handles the creation and management of prompts for the AI.
"""

import logging
from typing import Dict, Any, Union, List

from core.models import Character

logger = logging.getLogger(__name__)

class PromptManager:
    """
    Manages prompts for AI interactions.
    
    This class provides methods for generating prompts for different
    game actions and scenarios.
    """
    
    @staticmethod
    def get_action_prompt(action: str, details: str, character: Character, game_state: Any) -> str:
        """
        Generate a prompt for an action.
        
        Args:
            action: The action being performed
            details: Additional details for the action
            character: The player character
            game_state: The current game state
            
        Returns:
            A prompt string for the AI
        """
        # Base prompt with game state context
        base_prompt = f"""
        You are the Game Master for a medieval fantasy RPG. The player is performing the action '{action}' with details '{details}'.
        
        Current location: {game_state.current_location}
        Scene description: {game_state.scene_description}
        NPCs present: {', '.join(game_state.npcs_present) if game_state.npcs_present else 'None'}
        Events: {', '.join(game_state.events) if game_state.events else 'None'}
        
        Character information:
        - Name: {character.name}
        - Race: {character.race}
        - Class: {character.character_class}
        - Level: {character.level}
        - HP: {character.current_hp}/{character.max_hp}
        
        Respond in JSON format with the following structure:
        {{
            "success": true/false,
            "message": "Your detailed response as the Game Master",
            "description": "Optional updated scene description",
            "npcs_present": ["Optional", "updated", "NPC", "list"],
            "events": ["Optional", "updated", "events", "list"],
            "combat": true/false,
            "enemy": {{Optional enemy details if combat is initiated}}
        }}
        
        Keep your response in character as a Game Master. Be descriptive and immersive, but concise.
        """
        
        # Add action-specific context
        if action == "move":
            base_prompt += f"\nThe player is trying to move to '{details}'. Describe what they see and experience."
        elif action == "look":
            base_prompt += f"\nThe player is looking at '{details or 'the surroundings'}'. Provide a detailed description."
        elif action == "talk":
            base_prompt += f"\nThe player is talking to '{details}'. Create a realistic dialogue response."
        elif action == "search":
            base_prompt += f"\nThe player is searching '{details or 'the area'}'. Describe what they find."
        elif action == "custom":
            base_prompt += f"\nThe player is attempting a custom action: '{details}'. Determine the outcome based on the context."
        
        return base_prompt
    
    @staticmethod
    def get_combat_prompt(character: Character, enemy: Any, action: str) -> str:
        """
        Generate a prompt for combat.
        
        Args:
            character: The player character
            enemy: The enemy
            action: The combat action
            
        Returns:
            A prompt string for the AI
        """
        return f"""
        You are the Game Master for a medieval fantasy RPG. The player is in combat with {enemy.name}.
        
        Character information:
        - Name: {character.name}
        - Race: {character.race}
        - Class: {character.character_class}
        - Level: {character.level}
        - HP: {character.current_hp}/{character.max_hp}
        
        Enemy information:
        - Name: {enemy.name}
        - Level: {enemy.level}
        - HP: {enemy.current_hp}/{enemy.max_hp}
        
        The player is performing the combat action '{action}'.
        
        Respond in JSON format with the following structure:
        {{
            "success": true/false,
            "message": "Your detailed combat narration",
            "damage_dealt": 0,
            "damage_taken": 0,
            "combat_ended": true/false
        }}
        
        Be descriptive and exciting in your combat narration, but concise.
        """
    
    @staticmethod
    def get_npc_interaction_prompt(character: Character, npc_name: str, npc_details: Dict[str, Any], interaction_type: str) -> str:
        """
        Generate a prompt for NPC interaction.
        
        Args:
            character: The player character
            npc_name: The name of the NPC
            npc_details: Details about the NPC
            interaction_type: The type of interaction
            
        Returns:
            A prompt string for the AI
        """
        return f"""
        You are the Game Master for a medieval fantasy RPG. The player is interacting with {npc_name}, a {npc_details.get('race', 'humanoid')} {npc_details.get('profession', '')}.
        
        NPC details:
        - Personality: {npc_details.get('personality', 'neutral')}
        - Attitude toward player: {npc_details.get('attitude', 'neutral')}
        - Knowledge: {npc_details.get('knowledge', 'general information about the area')}
        
        Character information:
        - Name: {character.name}
        - Race: {character.race}
        - Class: {character.character_class}
        
        The interaction type is '{interaction_type}'.
        
        Respond in JSON format with the following structure:
        {{
            "success": true/false,
            "message": "The NPC's response or interaction result",
            "attitude_change": 0,
            "quest_offered": false,
            "quest_details": {{}} if offered
        }}
        
        Write the NPC's dialogue in a way that reflects their personality and attitude.
        """