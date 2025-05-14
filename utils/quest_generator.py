"""
Quest generator module.

This module provides functions for generating random quests.
"""

import random
import logging
from typing import Dict, Any, List

from translations import get_text

logger = logging.getLogger(__name__)


# Quest types and targets
QUEST_TYPES = ["kill", "collect", "deliver", "escort", "investigate"]
QUEST_TARGETS = {
    "kill": ["bandits", "wolves", "goblins", "cultists", "monster"],
    "collect": ["herbs", "minerals", "artifacts", "supplies", "ingredients"],
    "deliver": ["message", "package", "supplies", "medicine", "weapon"],
    "escort": ["merchant", "noble", "child", "scholar", "pilgrim"],
    "investigate": ["ruins", "disappearance", "strange_events", "creature", "crime"]
}


def generate_quest(
    location: str,
    difficulty: int = 1,
    lang: str = None
) -> Dict[str, Any]:
    """
    Generate a random quest.

    Args:
        location: Quest location
        difficulty: Quest difficulty
        lang: Language for translation

    Returns:
        Dictionary with quest details
    """
    try:
        # Select random quest type
        quest_type = random.choice(QUEST_TYPES)

        # Generate quest details based on type
        quest_details = _generate_quest_details(quest_type, location, lang)

        # Create quest data
        quest = {
            "name": quest_details["name"],
            "description": quest_details["description"],
            "difficulty": difficulty,
            "reward_gold": 50 * difficulty,
            "reward_xp": 100 * difficulty,
            "reward_items": _generate_quest_rewards(difficulty, lang),
            "status": "active",
            "progress": 0
        }

        logger.info(f"Quest generated: {quest['name']}")
        return quest

    except Exception as e:
        logger.error(f"Error generating quest: {e}")
        # Return fallback quest
        return _get_default_quest(location)


def _generate_quest_details(quest_type: str, location: str, lang: str) -> Dict[str, str]:
    """
    Generate quest name and description based on type.

    Args:
        quest_type: Quest type
        location: Quest location
        lang: Language for translation

    Returns:
        Dictionary with quest name and description
    """
    if quest_type == "kill":
        return _generate_kill_quest(location, lang)
    elif quest_type == "collect":
        return _generate_collect_quest(location, lang)
    elif quest_type == "deliver":
        return _generate_deliver_quest(location, lang)
    elif quest_type == "escort":
        return _generate_escort_quest(location, lang)
    elif quest_type == "investigate":
        return _generate_investigate_quest(location, lang)
    else:
        # Default quest
        return {
            "name": get_text("quest_names.default", lang),
            "description": get_text("quest_descriptions.default", lang, location)
        }


def _generate_kill_quest(location: str, lang: str) -> Dict[str, str]:
    """
    Generate a kill quest.

    Args:
        location: Quest location
        lang: Language for translation

    Returns:
        Dictionary with quest name and description
    """
    target_key = random.choice(QUEST_TARGETS["kill"])
    target = get_text(f"quest_targets.{target_key}", lang)

    return {
        "name": get_text("quest_names.kill", lang, target),
        "description": get_text("quest_descriptions.kill", lang, target.lower(), location)
    }


def _generate_collect_quest(location: str, lang: str) -> Dict[str, str]:
    """
    Generate a collection quest.

    Args:
        location: Quest location
        lang: Language for translation

    Returns:
        Dictionary with quest name and description
    """
    target_key = random.choice(QUEST_TARGETS["collect"])
    target = get_text(f"quest_targets.{target_key}", lang)

    return {
        "name": get_text("quest_names.collect", lang, target),
        "description": get_text("quest_descriptions.collect", lang, target.lower(), location)
    }


def _generate_deliver_quest(location: str, lang: str) -> Dict[str, str]:
    """
    Generate a delivery quest.

    Args:
        location: Quest location
        lang: Language for translation

    Returns:
        Dictionary with quest name and description
    """
    target_key = random.choice(QUEST_TARGETS["deliver"])
    target = get_text(f"quest_targets.{target_key}", lang)

    return {
        "name": get_text("quest_names.deliver", lang, target),
        "description": get_text("quest_descriptions.deliver", lang, target.lower(), location)
    }


def _generate_escort_quest(location: str, lang: str) -> Dict[str, str]:
    """
    Generate an escort quest.

    Args:
        location: Quest location
        lang: Language for translation

    Returns:
        Dictionary with quest name and description
    """
    target_key = random.choice(QUEST_TARGETS["escort"])
    target = get_text(f"quest_targets.{target_key}", lang)

    return {
        "name": get_text("quest_names.escort", lang, target),
        "description": get_text("quest_descriptions.escort", lang, target.lower(), location)
    }


def _generate_investigate_quest(location: str, lang: str) -> Dict[str, str]:
    """
    Generate an investigation quest.

    Args:
        location: Quest location
        lang: Language for translation

    Returns:
        Dictionary with quest name and description
    """
    target_key = random.choice(QUEST_TARGETS["investigate"])
    target = get_text(f"quest_targets.{target_key}", lang)

    return {
        "name": get_text("quest_names.investigate", lang, target),
        "description": get_text("quest_descriptions.investigate", lang, target.lower(), location)
    }


def _generate_quest_rewards(difficulty: int, lang: str) -> List[str]:
    """
    Generate quest rewards based on difficulty.

    Args:
        difficulty: Quest difficulty
        lang: Language for translation

    Returns:
        List of reward items
    """
    rewards = []

    # Add basic rewards for difficulty > 1
    if difficulty > 1:
        rewards.append(get_text("items.health_potion", lang))

    # Add better rewards for higher difficulties
    if difficulty > 2:
        rewards.append(get_text("items.stamina_potion", lang))

    if difficulty > 3:
        rewards.append(get_text("items.rare_item", lang))

    return rewards


def _get_default_quest(location: str) -> Dict[str, Any]:
    """
    Get a default quest for fallback.

    Args:
        location: Quest location

    Returns:
        Default quest data
    """
    return {
        "name": "Simple Task",
        "description": f"Help around {location}",
        "difficulty": 1,
        "reward_gold": 10,
        "reward_xp": 25,
        "reward_items": [],
        "status": "active",
        "progress": 0
    }
