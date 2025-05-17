import logging
from typing import Any, Dict, List, Union  # Added List, Union

from core.models import Character

logger = logging.getLogger(__name__)


class CharacterManager:
    ATTRIBUTE_DEFAULTS = {
        "int": {
            "strength": 10,
            "dexterity": 10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10,
            "max_hp": 20,
            "current_hp": 20,
            "max_stamina": 10,
            "current_stamina": 10,
            "gold": 50,
            "experience": 0,
            "level": 1,
        },
        "str": {
            "name": "",
            "character_class": "Warrior",
            "race": "Human",
        },
        "list": {
            "inventory": [
                "Canivete Enferrujado",
                "Bandagem Suja",
                "Lata de Comida Amassada",
            ]
        },
    }

    CLASS_HIT_DICE = {
        "Barbarian": 12,
        "Fighter": 10,
        "Paladin": 10,
        "Ranger": 10,
        "Bard": 8,
        "Cleric": 8,
        "Druid": 8,
        "Monk": 8,
        "Rogue": 8,
        "Warlock": 8,
        "Sorcerer": 6,
        "Wizard": 6,
        "Warrior": 10,  # Placeholder for a more generic combatant
        "Survivor": 8,  # Example for a zombie apocalypse class
        "Medic": 6,  # Example
        "Scavenger": 8,  # Example
    }

    @staticmethod
    def calculate_max_hp_dnd5e(
        character_class: str, constitution: int, level: int
    ) -> int:
        level = max(1, level)
        hit_die = CharacterManager.CLASS_HIT_DICE.get(
            character_class, 8
        )  # Default to 8 for survivor-types
        mod_const = (constitution - 10) // 2
        max_hp = hit_die + mod_const
        for lvl in range(2, level + 1):
            avg = (hit_die // 2) + 1
            max_hp += avg + mod_const
        return max(1, max_hp)

    @classmethod
    def create_character_from_form(cls, character_data: Dict[str, Any]) -> "Character":
        from utils.character_utils import (
            calculate_initial_gold,
            generate_initial_inventory,
        )

        # This dictionary will hold all attributes parsed from the form and defaults.
        # Some will be passed directly to Character init, others will go into Character.attributes.
        parsed_attributes_from_form = cls.get_character_attributes(character_data)

        # Extract values for direct Character __init__ parameters
        name_val = parsed_attributes_from_form.pop("name", "Unknown")
        character_class_val = parsed_attributes_from_form.pop(
            "character_class", "Survivor"
        )
        race_val = parsed_attributes_from_form.pop("race", "Human")
        level_val = parsed_attributes_from_form.pop("level", 1)
        experience_val = parsed_attributes_from_form.pop("experience", 0)

        # Description comes directly from character_data, not processed by get_character_attributes
        description_val = character_data.get("description", "")

        # Inventory from form is popped but we'll generate a new one for a new character.
        # Popping it ensures it's not in the final 'attributes' dict for Character.
        parsed_attributes_from_form.pop("inventory", [])

        # The remaining items in parsed_attributes_from_form are candidates for Character.attributes
        # This includes: strength, dexterity, constitution, intelligence, wisdom, charisma,
        # current_hp, max_hp, current_stamina, max_stamina, gold.
        # We will update hp, stamina, and gold in this dictionary.
        final_character_attributes_dict: Dict[str, int] = parsed_attributes_from_form  # type: ignore

        # Calculate and update HP in the attributes dictionary
        constitution_for_hp_calc = final_character_attributes_dict.get(
            "constitution", 10
        )
        max_hp_val = cls.calculate_max_hp_dnd5e(
            character_class_val, constitution_for_hp_calc, level_val
        )
        final_character_attributes_dict["max_hp"] = max_hp_val
        final_character_attributes_dict["current_hp"] = max_hp_val

        # Calculate and update Stamina in the attributes dictionary
        dexterity_for_stamina_calc = final_character_attributes_dict.get(
            "dexterity", 10
        )
        constitution_for_stamina_calc = final_character_attributes_dict.get(
            "constitution", 10
        )
        stamina_base = 10  # Valor base inicial de Stamina
        dex_mod_stamina = (dexterity_for_stamina_calc - 10) // 2
        con_mod_stamina = (constitution_for_stamina_calc - 10) // 2
        max_stamina_val = (
            stamina_base + (dex_mod_stamina * level_val) + (con_mod_stamina * level_val)
        )
        max_stamina_val = max(1, max_stamina_val)  # Ensure stamina is at least 1
        final_character_attributes_dict["max_stamina"] = max_stamina_val
        final_character_attributes_dict["current_stamina"] = max_stamina_val

        # Calculate and update Gold in the attributes dictionary
        final_character_attributes_dict["gold"] = calculate_initial_gold(
            character_class_val, race_val
        )

        # Generate initial inventory (this is a direct Character field)
        # Use stats from the final_character_attributes_dict for generation if needed
        strength_for_inv_calc = final_character_attributes_dict.get("strength", 10)
        dexterity_for_inv_calc = final_character_attributes_dict.get("dexterity", 10)
        intelligence_for_inv_calc = final_character_attributes_dict.get(
            "intelligence", 10
        )
        # Assuming generate_initial_inventory returns List[str] or a list of items
        # compatible with Union[str, Dict[str, Any]]
        generated_inventory_items = generate_initial_inventory(
            character_class_val,
            race_val,
            strength_for_inv_calc,
            dexterity_for_inv_calc,
            intelligence_for_inv_calc,
            description_val,
        )
        initial_inventory_list: List[Union[str, Dict[str, Any]]] = list(
            generated_inventory_items
        )
<<<<<<< Updated upstream
=======

        # Ensure all items are strings or dicts as per the type hint
        processed_inventory: List[Union[str, Dict[str, Any]]] = []
>>>>>>> Stashed changes

        return Character(
            name=name_val,
            character_class=character_class_val,
            race=race_val,
            level=level_val,
            experience=experience_val,
            description=description_val,
            inventory=initial_inventory_list,
            attributes=final_character_attributes_dict,
            equipment={},  # Default for new character
            skills=[],  # Default for new character
            survival_stats={},  # Default for new character
            status_effects=[],  # Default for new character
        )

    @classmethod
    def get_character_attributes(cls, character_data: Dict[str, Any]) -> Dict[str, Any]:
        attributes = {}

        for attr, default in cls.ATTRIBUTE_DEFAULTS["int"].items():
            try:
                value = character_data.get(attr, default)
                attributes[attr] = int(value)
            except (ValueError, TypeError):
                attributes[attr] = default
                logger.warning("Invalid value for %s, using default: %s", attr, default)

        for attr, default in cls.ATTRIBUTE_DEFAULTS["str"].items():
            form_key = "class" if attr == "character_class" else attr
            attributes[attr] = character_data.get(form_key, default)

        for attr, default in cls.ATTRIBUTE_DEFAULTS["list"].items():
            if attr == "inventory":
                inventory = character_data.get("inventory", "")
                if isinstance(inventory, str):
                    attributes[attr] = (
                        [item.strip() for item in inventory.split(",") if item.strip()]
                        if inventory
                        else default
                    )
                elif isinstance(inventory, list):  # If it's already a list
                    attributes[attr] = inventory
                else:
                    attributes[attr] = default

        return attributes
