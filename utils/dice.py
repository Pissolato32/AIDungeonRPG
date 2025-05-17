"""
Dice rolling and combat calculation utilities.

This module provides functions for dice rolling and combat-related calculations.
"""

import logging
import random
from typing import (  # Added Union for potential future use, Any is the key fix
    Any,
    Dict,
    Optional,
    Tuple,
    Union,
)

logger = logging.getLogger(__name__)


def roll_dice(num_dice: int, sides: int, modifier: int = 0) -> Dict[str, Any]:
    """
    Roll dice in NdS+M format (N dice with S sides plus modifier M).

    Args:
        num_dice: Number of dice to roll
        sides: Number of sides on each die
        modifier: Modifier to add to the result

    Returns:
        Dictionary with roll results including individual dice, total, and formatted string
    """
    try:
        num_dice = max(1, num_dice)  # Ensure at least one die is rolled
        individual_rolls = [random.randint(1, sides) for _ in range(num_dice)]
        total = sum(individual_rolls) + modifier

        # Create formatted string representation
        roll_str = f"{num_dice}d{sides}"
        if modifier > 0:
            roll_str += f"+{modifier}"
        elif modifier < 0:
            roll_str += f"{modifier}"

        result_str = f"{roll_str} = {total} ({'+'.join(map(str, individual_rolls))}"
        if modifier != 0:
            result_str += f"{'+' if modifier > 0 else ''}{modifier}"
        result_str += ")"

        result = {
            "dice": individual_rolls,
            "total": total,
            "modifier": modifier,
            "formula": roll_str,
            "result_string": result_str,
            "success": True,
        }

        logger.debug(f"Dice roll: {result_str}")
        return result
    except Exception as e:
        logger.error(f"Error in dice roll: {e}")
        return {
            "dice": [],
            "total": modifier,
            "modifier": modifier,
            "formula": f"0d{sides}+{modifier}",
            "result_string": f"Erro na rolagem: {str(e)}",
            "success": False,
        }


def calculate_attribute_modifier(attribute_score: int) -> int:
    """
    Calculate the modifier for an attribute score (DnD style).

    Args:
        attribute_score: Attribute score

    Returns:
        Calculated modifier
    """
    return (attribute_score - 10) // 2


import logging
import random
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def calculate_damage(
    attacker_stats: Dict[str, int],
    defender_stats: Dict[str, Any],  # resistência pode ser dict dentro do dict
    attack_type: str = "basic",
    weapon_stats: Optional[Dict[str, Any]] = None,
    skill_stats: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Calculate attack damage considering all combat factors.

    Args:
        attacker_stats: Attacker statistics
        defender_stats: Defender statistics
        attack_type: Attack type (basic, light, heavy)
        weapon_stats: Optional weapon statistics
        skill_stats: Optional skill statistics

    Returns:
        Dict containing damage info, hit status, critical hit, and effects
    """
    try:
        # Get base attack parameters (implementação separada)
        attack_params = _get_attack_parameters(attack_type, attacker_stats)
        min_damage, max_damage, hit_chance = attack_params

        # Apply weapon modifiers if present
        if weapon_stats:
            min_damage += weapon_stats.get("min_damage", 0)
            max_damage += weapon_stats.get("max_damage", 0)
            hit_chance += weapon_stats.get("accuracy", 0)

        # Apply skill modifiers if present
        if skill_stats:
            min_damage += skill_stats.get("damage_bonus", 0)
            max_damage += skill_stats.get("damage_bonus", 0)
            hit_chance += skill_stats.get("accuracy_bonus", 0)

        # Clamp hit_chance between 0 and 1
        hit_chance = max(0.0, min(hit_chance, 1.0))

        # Roll to hit
        hit_roll = random.random()
        if hit_roll > hit_chance:
            return {
                "damage": 0,
                "hit": False,
                "critical": False,
                "effects": [],
                "roll_info": {"hit_roll": hit_roll, "hit_chance": hit_chance},
            }

        # Calculate base damage (garantir min_damage <= max_damage)
        # Ensure min_damage is not greater than max_damage
        actual_min_damage = min(min_damage, max_damage)
        actual_max_damage = max(min_damage, max_damage)
        base_damage = random.randint(actual_min_damage, actual_max_damage)

        # Check for critical hit (10% chance)
        critical = random.random() < 0.1
        if critical:
            base_damage *= 2

        # Apply defense and resistances
        defense = defender_stats.get("defense", 0)
        resistance = 0.0
        resist_dict = defender_stats.get("resistance", {})
        if isinstance(resist_dict, dict):
            resistance = resist_dict.get(attack_type, 0.0)
        else:
            logger.warning(
                f"defender_stats['resistance'] is not dict but {type(resist_dict)}"
            )

        # Clamp resistance entre 0 e 1
        resistance = max(0.0, min(resistance, 1.0))

        final_damage = max(1, base_damage - defense)
        final_damage = max(1, int(final_damage * (1 - resistance)))

        # Calculate any additional effects
        effects = []
        if critical:
            effects.append("critical")

        if weapon_stats and weapon_stats.get("effects"):
            effects.extend(weapon_stats["effects"])

        if skill_stats and skill_stats.get("effects"):
            effects.extend(skill_stats["effects"])

        result = {
            "damage": final_damage,
            "hit": True,
            "critical": critical,
            "effects": effects,
            "roll_info": {
                "base_damage": base_damage,
                "defense": defense,
                "resistance": resistance,
                "hit_roll": hit_roll,
                "hit_chance": hit_chance,
            },
        }

        logger.debug(f"Attack calculation: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in damage calculation: {e}", exc_info=True)
        return {
            "damage": 1,
            "hit": True,
            "critical": False,
            "effects": ["error"],
            "roll_info": {"error": str(e)},
        }


def _get_attack_parameters(
    attack_type: str, attacker_stats: Dict[str, int]
) -> Tuple[int, int, float]:
    """
    Get attack parameters based on attack type.

    Args:
        attack_type: Attack type (basic, light, heavy)
        attacker_stats: Attacker statistics

    Returns:
        Tuple with min damage, max damage, and hit chance
    """
    strength = attacker_stats.get("strength", 10)

    if attack_type == "light":
        min_damage = max(1, strength // 4)
        max_damage = max(3, strength // 2)
        hit_chance = 0.9
    elif attack_type == "heavy":
        min_damage = max(2, strength // 2)
        max_damage = max(6, strength)
        hit_chance = 0.7
    else:  # basic
        min_damage = max(1, strength // 3)
        max_damage = max(4, strength // 2 + 2)
        hit_chance = 0.8

    return min_damage, max_damage, hit_chance
