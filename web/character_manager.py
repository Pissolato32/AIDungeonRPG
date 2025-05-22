import logging
from typing import Any, Dict, List, Union  # Added List, Union

# Import Character model and CombatStats
from core.models import Character, CombatStats

logger = logging.getLogger(__name__)


class CharacterManager:
    # ATTRIBUTE_DEFAULTS for "int" (core stats) is no longer needed here.
    # Defaults for core stats like strength, dexterity, etc., are handled by:
    # 1. The HTML form inputs in character.html (which default to "8").
    # 2. The Character model in models.py (which defaults to 10 if not provided).
    ATTRIBUTE_DEFAULTS = {
        "str": {  # Default name if not provided
            "name": "Survivor",
        },
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

        # 2. Initialize data for CombatStats
        combat_stats_data: Dict[str, Any] = {}

        core_stat_names = [
            "strength",
            "dexterity",
            "constitution",
            "intelligence",
            "wisdom",
            "charisma",
        ]
        for stat_name in core_stat_names:
            form_value_str = character_data.get(stat_name)
            if (
                form_value_str is not None and form_value_str.strip()
            ):  # Check if not None and not empty string
                try:
                    combat_stats_data[stat_name] = int(form_value_str)
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid value for {stat_name} from form: '{form_value_str}'. "
                        f"CombatStats default will be used."
                    )
            # If form_value_str is None or invalid, CombatStats.from_dict will use its defaults.

        # 3. Calculate derived attributes (HP, Stamina) for CombatStats
        constitution_for_hp_calc = combat_stats_data.get(
            "constitution", 10
        )  # Use value from form or default 10
        max_hp_val = cls.calculate_max_hp_survivor(constitution_for_hp_calc, level_val)
        combat_stats_data["max_hp"] = max_hp_val
        combat_stats_data["current_hp"] = max_hp_val

        dexterity_for_stamina_calc = combat_stats_data.get("dexterity", 10)
        constitution_for_stamina_calc = combat_stats_data.get("constitution", 10)
        stamina_base = 10
        dex_mod_stamina = (dexterity_for_stamina_calc - 10) // 2
        con_mod_stamina = (constitution_for_stamina_calc - 10) // 2
        max_stamina_val = max(
            1,
            stamina_base
            + (dex_mod_stamina * level_val)
            + (con_mod_stamina * level_val),
        )
        combat_stats_data["max_stamina"] = max_stamina_val
        combat_stats_data["current_stamina"] = max_stamina_val

        # Create CombatStats instance
        combat_stats_obj = CombatStats.from_dict(combat_stats_data)

        # Other direct fields
        # These will be passed directly to the Character constructor
        description_val = description_val
        experience_val = 0
        gold_val = calculate_initial_gold()

        # 4. Generate initial inventory
        strength_for_inv_calc = combat_stats_data.get("strength", 10)
        dexterity_for_inv_calc = combat_stats_data.get("dexterity", 10)
        intelligence_for_inv_calc = combat_stats_data.get("intelligence", 10)
        generated_inventory_items = generate_initial_inventory(
            strength_for_inv_calc,
            dexterity_for_inv_calc,
            intelligence_for_inv_calc,
            description_val,
        )
        inventory_val: List[Union[str, Dict[str, Any]]] = list(
            generated_inventory_items
        )

        # 5. Create the Character object
        return Character(
            name=name_val,
            level=level_val,
            owner_session_id=owner_session_id,  # Use the owner_session_id passed as an argument
            description=description_val,
            experience=experience_val,
            gold=gold_val,
            inventory=inventory_val,
            stats=combat_stats_obj,
            # survival_stats will use default_factory from Character model
            # attributes (dict) will use default_factory
            # skills will use default_factory
            # equipment will use default_factory
        )
