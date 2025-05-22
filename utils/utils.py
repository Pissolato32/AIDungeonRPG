"""
Utility functions for the RPG game.

This module re-exports selected utility functions from other modules within the
utils package. This can be useful for creating a simplified access point to
commonly used utilities or for maintaining backward compatibility if functions
are moved around.
"""

# Re-export all functions from the utils package
from utils.dice import calculate_attribute_modifier, roll_dice

# Export all functions for backward compatibility
# Only list functions that are actually intended to be exported from this top-level utils.py
__all__ = [
    "roll_dice",
    "calculate_attribute_modifier",
]
