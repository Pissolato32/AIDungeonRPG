"""
Dice rolling and combat calculation utilities.

This module provides functions for dice rolling and combat-related calculations.
"""

import random
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


def roll_dice(num_dice: int, sides: int, modifier: int = 0) -> Dict[str, any]:
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


def calculate_damage(
    attacker_stats: Dict[str, int],
    defender_stats: Dict[str, int],
    attack_type: str = "basic",
) -> Tuple[int, bool]:
    """
    Calculate attack damage considering attacker and defender statistics.

    Args:
        attacker_stats: Attacker statistics
        defender_stats: Defender statistics
        attack_type: Attack type (basic, light, heavy)

    Returns:
        Tuple with damage dealt and hit indicator
    """
    try:
        # Get attack parameters based on attack type
        attack_params = _get_attack_parameters(attack_type, attacker_stats)
        min_damage, max_damage, hit_chance = attack_params

        # Determine if the attack hits
        if random.random() > hit_chance:
            logger.info(f"{attack_type.capitalize()} attack missed")
            return 0, False

        # Calculate damage
        damage = random.randint(min_damage, max_damage)

        # Apply defense
        defense = defender_stats.get("defense", 0)
        final_damage = max(1, damage - defense)

        logger.debug(f"{attack_type.capitalize()} attack: {final_damage} damage")
        return final_damage, True

    except Exception as e:
        logger.error(f"Error in damage calculation: {e}")
        return 1, True  # Minimum damage in case of error


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
