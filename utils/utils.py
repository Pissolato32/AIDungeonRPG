"""
Utility functions for the RPG game.

This module re-exports all utility functions from the utils package
to maintain backward compatibility with existing code.
"""

# Re-export all functions from the utils package
from utils.dice import calculate_attribute_modifier, roll_dice

# Export all functions for backward compatibility
__all__ = [
    "roll_dice",
    "calculate_attribute_modifier",
    # "calculate_damage", # Removed
    # "save_data", # Removed
    # "load_data", # Removed
    # "format_datetime", # Removed
    # "generate_quest", # Removed
]
