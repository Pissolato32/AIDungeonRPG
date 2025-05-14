"""
Character management module.

This module provides functionality for managing character creation and attributes.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from models import Character

logger = logging.getLogger(__name__)


class CharacterManager:
    """
    Manages character creation and attribute processing.

    Features:
    - Character attribute processing
    - Form data conversion
    - Default attribute management
    """

    # Default attribute values by type
    ATTRIBUTE_DEFAULTS = {
        # Integer attributes
        'int': {
            # Base stats
            'strength': 10,
            'dexterity': 10,
            'constitution': 10,
            'intelligence': 10,
            'wisdom': 10,
            'charisma': 10,

            # Resource stats
            'max_hp': 20,
            'current_hp': 20,
            'max_stamina': 10,
            'current_stamina': 10,

            # Progression stats
            'gold': 50,
            'experience': 0,
            'level': 1
        },

        # String attributes
        'str': {
            'name': '',  # Campo vazio por padrão
            'character_class': 'Warrior',
            'race': 'Human'
        },

        # List attributes
        'list': {
            'inventory': ["Basic Sword", "Health Potion"]
        }
    }

    @classmethod
    def create_character_from_form(cls, character_data: Dict[str, Any]) -> 'Character':
        """
        Create a character object from form data.

        Args:
            character_data: Dictionary containing character form data

        Returns:
            Character: A newly created character object
        """
        # Import here to avoid circular imports
        from models import Character

        # Process attributes
        attributes = cls.get_character_attributes(character_data)

        # Create character with processed attributes
        return Character(
            name=attributes.get('name', 'Unknown'),
            character_class=attributes.get('character_class', 'Warrior'),
            race=attributes.get('race', 'Human'),
            **attributes
        )

    @classmethod
    def get_character_attributes(cls, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and convert character attributes from form data.

        Args:
            character_data: Dictionary containing character form data

        Returns:
            Dictionary with properly typed character attributes
        """
        # Initialize attributes dictionary
        attributes = {}

        # Process integer attributes
        for attr, default in cls.ATTRIBUTE_DEFAULTS['int'].items():
            try:
                value = character_data.get(attr, default)
                attributes[attr] = int(value)
            except (ValueError, TypeError):
                attributes[attr] = default
                logger.warning(f"Invalid value for {attr}, using default: {default}")

        # Process string attributes
        for attr, default in cls.ATTRIBUTE_DEFAULTS['str'].items():
            # Special case for 'character_class' which is stored as 'class' in form data
            form_key = 'class' if attr == 'character_class' else attr
            attributes[attr] = character_data.get(form_key, default)

        # Process list attributes with special handling
        for attr, default in cls.ATTRIBUTE_DEFAULTS['list'].items():
            if attr == 'inventory':
                inventory = character_data.get('inventory', '')
                attributes[attr] = inventory.split(',') if inventory else default

        return attributes
