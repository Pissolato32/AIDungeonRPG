import logging
from typing import Any, Dict

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

        full_data = cls.get_character_attributes(character_data)

        name = full_data.pop("name", "Unknown")
        # Default class more fitting for zombie apocalypse
        character_class = full_data.get("character_class", "Survivor")
        race = full_data.get("race", "Human")
        description = character_data.get("description", "")
        level = full_data.get("level", 1)
        constitution = full_data.get("constitution", 10)
        strength = full_data.get("strength", 10)
        dexterity = full_data.get("dexterity", 10)
        intelligence = full_data.get(
            "intelligence", 10
        )  # Ensure intelligence is fetched

        # Cálculo do HP
        # Using the D&D 5e calculation method for consistency, or adjust as needed
        max_hp = cls.calculate_max_hp_dnd5e(character_class, constitution, level)
        full_data["max_hp"] = max_hp
        full_data["current_hp"] = max_hp

        # Cálculo da Stamina (anteriormente Resistência)
        stamina_base = 10  # Valor base inicial de Stamina
        # Example: Stamina could be based on constitution and dexterity
        dex_mod_stamina = (full_data.get("dexterity", 10) - 10) // 2
        con_mod_stamina = (constitution - 10) // 2
        max_stamina_val = (
            stamina_base + (dex_mod_stamina * level) + (con_mod_stamina * level)
        )
        max_stamina_val = max(1, max_stamina_val)  # Ensure stamina is at least 1

        full_data["max_stamina"] = max_stamina_val
        full_data["current_stamina"] = max_stamina_val

        full_data["description"] = description
        full_data["gold"] = calculate_initial_gold(character_class, race)
        full_data["inventory"] = generate_initial_inventory(
            character_class, race, strength, dexterity, intelligence, description
        )
        # Attributes like strength, dexterity, etc., are already in full_data
        # from get_character_attributes, no need to re-assign unless they were modified above.
        return Character(
            name=name, character_class=character_class, race=race, attributes=full_data
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
