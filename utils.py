"""
Utility functions for the RPG game.

This module re-exports all utility functions from the utils package
to maintain backward compatibility with existing code.
"""

# Re-export all functions from the utils package
from utils.dice import roll_dice, calculate_attribute_modifier, calculate_damage
from utils.data_io import save_json_data, load_json_data
from utils.datetime_utils import format_datetime
from utils.encounter_generator import get_random_encounter, generate_loot_table
from utils.quest_generator import generate_quest

# Export all functions for backward compatibility
__all__ = [
    'roll_dice',
    'calculate_attribute_modifier',
    'calculate_damage',
    'save_json_data',
    'load_json_data',
    'format_datetime',
    'get_random_encounter',
    'generate_loot_table',
    'generate_quest'
]