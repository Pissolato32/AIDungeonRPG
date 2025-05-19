import logging
from typing import Any, Dict, List, Union  # Added List, Union

from core.models import Character

logger = logging.getLogger(__name__)


class CharacterManager:
    ATTRIBUTE_DEFAULTS = {
        "int": {  # Core stats that can be set from form for a new character
            "strength": 10,
            "dexterity": 10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10,
            # HP, Stamina, Gold, Level, Experience for new characters are handled directly
            # in create_character_from_form or by Character model defaults.
        },
        "str": {  # Default name if not provided
            "name": "Survivor",
        },
        # Default inventory is now solely handled by generate_initial_inventory
        # from character_utils.py, making this section redundant here.
    }

    # CLASS_HIT_DICE REMOVIDO
    DEFAULT_HIT_DIE = 8  # Todos os sobreviventes começam com um "dado de vida" base

    @staticmethod
    def calculate_max_hp_survivor(  # Nome alterado para refletir a mudança
        constitution: int, level: int
    ) -> int:
        level = max(1, level)
        # hit_die = CharacterManager.CLASS_HIT_DICE.get(
        #     character_class, 8
        # ) # REMOVIDO
        hit_die = CharacterManager.DEFAULT_HIT_DIE
        mod_const = (constitution - 10) // 2
        max_hp = hit_die + mod_const
        for _ in range(2, level + 1):
            avg = (hit_die // 2) + 1
            max_hp += avg + mod_const
        return max(1, max_hp)

    @classmethod
    def create_character_from_form(
        cls, character_data: Dict[str, Any], owner_session_id: str
    ) -> "Character":
        from utils.character_utils import (
            calculate_initial_gold,
            generate_initial_inventory,
        )

        # 1. Get direct Character fields or set defaults for a new character
        name_val = character_data.get("name", cls.ATTRIBUTE_DEFAULTS["str"]["name"])
        description_val = character_data.get(
            "description", ""
        )  # Define description_val here
        level_val = 1  # New characters always start at level 1
        # 2. Initialize core attributes dictionary (strength, dexterity, etc.)
        # These will now be passed as direct arguments to Character constructor.
        # The 'attributes' dict on Character can be used for other, more dynamic stats.
        character_direct_attrs: Dict[str, Any] = {
            "attributes": {}
        }  # Initialize attributes dict

        core_stat_names = [
            "strength",
            "dexterity",
            "constitution",
            "intelligence",
            "wisdom",
            "charisma",
        ]
        for stat_name in core_stat_names:
            try:
                # Use default from ATTRIBUTE_DEFAULTS["int"] if not in character_data
                value = character_data.get(
                    stat_name, cls.ATTRIBUTE_DEFAULTS["int"].get(stat_name, 10)
                )
                character_direct_attrs[stat_name] = int(value)
            except (ValueError, TypeError):
                default_stat_val = cls.ATTRIBUTE_DEFAULTS["int"].get(stat_name, 10)
                character_direct_attrs[stat_name] = default_stat_val
                logger.warning(
                    f"Invalid value for {stat_name}, using default: {default_stat_val}"
                )

        # 3. Calculate derived attributes (HP, Stamina, Gold) and add them
        constitution_for_hp_calc = character_direct_attrs.get("constitution", 10)
        max_hp_val = cls.calculate_max_hp_survivor(constitution_for_hp_calc, level_val)
        character_direct_attrs["max_hp"] = max_hp_val
        character_direct_attrs["current_hp"] = max_hp_val

        dexterity_for_stamina_calc = character_direct_attrs.get("dexterity", 10)
        constitution_for_stamina_calc = character_direct_attrs.get("constitution", 10)
        stamina_base = 10
        dex_mod_stamina = (dexterity_for_stamina_calc - 10) // 2
        con_mod_stamina = (constitution_for_stamina_calc - 10) // 2
        max_stamina_val = max(
            1,
            stamina_base
            + (dex_mod_stamina * level_val)
            + (con_mod_stamina * level_val),
        )
        character_direct_attrs["max_stamina"] = max_stamina_val
        character_direct_attrs["current_stamina"] = max_stamina_val

        # Other direct fields
        character_direct_attrs["description"] = (
            description_val  # Ensure description from form is included
        )
        character_direct_attrs["experience"] = (
            0  # New characters start with 0 experience
        )
        character_direct_attrs["gold"] = calculate_initial_gold()

        # 4. Generate initial inventory
        strength_for_inv_calc = character_direct_attrs.get("strength", 10)
        dexterity_for_inv_calc = character_direct_attrs.get("dexterity", 10)
        intelligence_for_inv_calc = character_direct_attrs.get("intelligence", 10)
        generated_inventory_items = generate_initial_inventory(
            strength_for_inv_calc,
            dexterity_for_inv_calc,
            intelligence_for_inv_calc,
            description_val,
        )
        character_direct_attrs["inventory"] = list(generated_inventory_items)
        # equipment and skills default to empty lists/dicts in Character model

        # 5. Create the Character object, passing the collected attributes dictionary
        return Character(
            name=name_val,
            level=level_val,
            owner_session_id=owner_session_id,  # Use the owner_session_id passed as an argument
            **character_direct_attrs,  # Pass all other collected attributes
        )

    # The get_character_attributes method is no longer needed with the streamlined
    # create_character_from_form method and can be removed.
