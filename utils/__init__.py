"""
Utility functions for the RPG game.

This package contains various utility functions used throughout the game.
"""

from .dice import roll_dice, calculate_attribute_modifier, calculate_damage
from .data_io import save_json_data, load_json_data
from .datetime_utils import format_datetime
from .encounter_generator import get_random_encounter, generate_loot_table
from .quest_generator import generate_quest

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
