"""
Survival system module.

This module provides functionality for managing character survival mechanics like hunger and thirst.
"""

import logging
import random
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SurvivalSystem:
    """
    Manages character survival mechanics like hunger and thirst.
    
    Features:
    - Hunger and thirst decay over time
    - Effects of hunger and thirst on character stats
    - Consumption of food and water
    """
    
    # Constants for hunger and thirst
    MAX_HUNGER = 100
    MAX_THIRST = 100
    HUNGER_DECAY_RATE = 1  # Per action
    THIRST_DECAY_RATE = 2  # Per action
    
    @staticmethod
    def update_survival_stats(character: Any, action_type: str) -> Dict[str, Any]:
        """
        Update character's hunger and thirst based on action type.
        
        Args:
            character: Character object
            action_type: Type of action performed
            
        Returns:
            Dictionary with updated stats and messages
        """
        result = {
            "hunger_changed": False,
            "thirst_changed": False,
            "messages": []
        }
        
        # Skip for certain actions
        if action_type in ["rest", "use_item"]:
            return result
            
        # Get current values
        current_hunger = getattr(character, "current_hunger", SurvivalSystem.MAX_HUNGER)
        current_thirst = getattr(character, "current_thirst", SurvivalSystem.MAX_THIRST)
        
        # Determine decay rates based on action
        hunger_decay = SurvivalSystem._get_hunger_decay(action_type)
        thirst_decay = SurvivalSystem._get_thirst_decay(action_type)
        
        # Update hunger
        new_hunger = max(0, current_hunger - hunger_decay)
        if new_hunger != current_hunger:
            character.current_hunger = new_hunger
            result["hunger_changed"] = True
            
            # Add hunger messages if reaching thresholds
            if new_hunger <= 0:
                result["messages"].append("Você está faminto! Precisa comer algo imediatamente.")
            elif new_hunger <= 20:
                result["messages"].append("Seu estômago ronca de fome. Você precisa comer logo.")
            elif new_hunger <= 40:
                result["messages"].append("Você começa a sentir fome.")
        
        # Update thirst
        new_thirst = max(0, current_thirst - thirst_decay)
        if new_thirst != current_thirst:
            character.current_thirst = new_thirst
            result["thirst_changed"] = True
            
            # Add thirst messages if reaching thresholds
            if new_thirst <= 0:
                result["messages"].append("Você está desidratado! Precisa beber água imediatamente.")
            elif new_thirst <= 20:
                result["messages"].append("Sua garganta está seca. Você precisa beber algo logo.")
            elif new_thirst <= 40:
                result["messages"].append("Você começa a sentir sede.")
        
        # Apply survival effects
        SurvivalSystem._apply_survival_effects(character)
        
        return result
    
    @staticmethod
    def consume_food(character: Any, food_item: str) -> Dict[str, Any]:
        """
        Character consumes food to restore hunger.
        
        Args:
            character: Character object
            food_item: Name of the food item
            
        Returns:
            Dictionary with results
        """
        # Food values
        food_values = {
            "Pão": 15,
            "Bread": 15,
            "Carne": 25,
            "Meat": 25,
            "Fruta": 10,
            "Fruit": 10,
            "Ração": 20,
            "Ration": 20,
            "Refeição": 40,
            "Meal": 40,
            "Banquete": 100,
            "Feast": 100
        }
        
        # Default value for unknown items
        hunger_restore = food_values.get(food_item, 15)
        
        # Update hunger
        old_hunger = getattr(character, "current_hunger", 0)
        new_hunger = min(SurvivalSystem.MAX_HUNGER, old_hunger + hunger_restore)
        character.current_hunger = new_hunger
        
        return {
            "success": True,
            "hunger_restored": new_hunger - old_hunger,
            "message": f"Você consome {food_item} e recupera {new_hunger - old_hunger} pontos de fome."
        }
    
    @staticmethod
    def consume_water(character: Any, water_item: str) -> Dict[str, Any]:
        """
        Character consumes water to restore thirst.
        
        Args:
            character: Character object
            water_item: Name of the water item
            
        Returns:
            Dictionary with results
        """
        # Water values
        water_values = {
            "Água": 20,
            "Water": 20,
            "Poção": 15,
            "Potion": 15,
            "Vinho": 10,
            "Wine": 10,
            "Cerveja": 15,
            "Beer": 15,
            "Hidromel": 25,
            "Mead": 25
        }
        
        # Default value for unknown items
        thirst_restore = water_values.get(water_item, 20)
        
        # Update thirst
        old_thirst = getattr(character, "current_thirst", 0)
        new_thirst = min(SurvivalSystem.MAX_THIRST, old_thirst + thirst_restore)
        character.current_thirst = new_thirst
        
        return {
            "success": True,
            "thirst_restored": new_thirst - old_thirst,
            "message": f"Você bebe {water_item} e recupera {new_thirst - old_thirst} pontos de sede."
        }
    
    @staticmethod
    def _get_hunger_decay(action_type: str) -> int:
        """Get hunger decay rate based on action type."""
        decay_rates = {
            "move": 2,
            "attack": 3,
            "flee": 4,
            "search": 1,
            "talk": 0.5,
            "look": 0.5
        }
        
        # Add randomness
        base_rate = decay_rates.get(action_type, SurvivalSystem.HUNGER_DECAY_RATE)
        return random.uniform(base_rate * 0.8, base_rate * 1.2)
    
    @staticmethod
    def _get_thirst_decay(action_type: str) -> int:
        """Get thirst decay rate based on action type."""
        decay_rates = {
            "move": 3,
            "attack": 4,
            "flee": 5,
            "search": 1,
            "talk": 1,
            "look": 0.5
        }
        
        # Add randomness
        base_rate = decay_rates.get(action_type, SurvivalSystem.THIRST_DECAY_RATE)
        return random.uniform(base_rate * 0.8, base_rate * 1.2)
    
    @staticmethod
    def _apply_survival_effects(character: Any) -> None:
        """Apply effects of hunger and thirst on character stats."""
        hunger = getattr(character, "current_hunger", SurvivalSystem.MAX_HUNGER)
        thirst = getattr(character, "current_thirst", SurvivalSystem.MAX_THIRST)
        
        # Reset temporary effects
        if hasattr(character, "temp_stat_penalties"):
            character.temp_stat_penalties = {}
        else:
            character.temp_stat_penalties = {}
        
        # Apply hunger penalties
        if hunger <= 0:
            # Severe hunger: -3 to strength and dexterity
            character.temp_stat_penalties["strength"] = -3
            character.temp_stat_penalties["dexterity"] = -3
        elif hunger <= 20:
            # Moderate hunger: -2 to strength
            character.temp_stat_penalties["strength"] = -2
        elif hunger <= 40:
            # Mild hunger: -1 to strength
            character.temp_stat_penalties["strength"] = -1
        
        # Apply thirst penalties
        if thirst <= 0:
            # Severe thirst: -3 to constitution and wisdom
            character.temp_stat_penalties["constitution"] = -3
            character.temp_stat_penalties["wisdom"] = -3
        elif thirst <= 20:
            # Moderate thirst: -2 to constitution
            character.temp_stat_penalties["constitution"] = -2
        elif thirst <= 40:
            # Mild thirst: -1 to constitution
            character.temp_stat_penalties["constitution"] = -1