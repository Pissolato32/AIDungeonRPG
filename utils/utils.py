"""
Utility functions for the RPG game.

This module re-exports all utility functions from the utils package
to maintain backward compatibility with existing code.
"""

from utils.data_io import load_data, save_data  # Corrected names
from utils.datetime_utils import format_datetime

# Re-export all functions from the utils package
from utils.dice import calculate_attribute_modifier, calculate_damage, roll_dice
from utils.encounter_generator import generate_loot_table, get_random_encounter
from utils.quest_generator import generate_quest

# Export all functions for backward compatibility
__all__ = [
    "roll_dice",
    "calculate_attribute_modifier",
    "calculate_damage",
    "save_data",  # Corrected name
    "load_data",  # Corrected name
    "format_datetime",
    "get_random_encounter",
    "generate_loot_table",
    "generate_quest",
]
