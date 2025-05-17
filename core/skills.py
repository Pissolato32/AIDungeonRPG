"""
Skill system module for the RPG game.

This module provides the core skill system functionality including:
- Skill data models
- Skill usage and cooldown management
- Skill progression and unlocking
- Class skill trees
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, TypedDict

from .models import Character

SkillType = Literal["active", "passive", "combat", "crafting", "survival"]
ResourceType = Literal["stamina", "mana", "focus", "rage"]
StatType = Literal["strength", "dexterity",
                   "constitution", "intelligence", "wisdom", "charisma"]


class SkillEffect(TypedDict):
    """
    Type definition for skill effects that can be applied during skill use.
    """

    type: Literal["damage", "heal", "buff", "debuff", "resource", "status"]
    target: Literal["self", "enemy", "ally", "area"]
    amount: int
    duration: Optional[int]  # Number of turns for temporary effects
    stat_modifier: Dict[StatType, int]  # Stat modifications for buffs/debuffs


@dataclass
class Skill:
    """
    Represents a skill that can be learned and used by characters.
    """

    id: str  # Unique identifier
    name: str
    description: str
    skill_type: SkillType
    level_requirement: int = 1
    resource_cost: Optional[Dict[ResourceType, int]
                            ] = None  # E.g. {"stamina": 10}
    cooldown: int = 0  # Turns until skill can be used again
    effects: List[SkillEffect] = field(default_factory=list)
    prerequisites: List[str] = field(
        default_factory=list
    )  # Skill IDs required before learning

    def can_use(self, character: Character) -> bool:
        """Check if character has required resources/conditions to use skill."""
        if not self.resource_cost:
            return True

        for resource, cost in self.resource_cost.items():
            current = character.survival_stats.get(resource.lower(), 0)
            if current < cost:
                return False
        return True

    def apply_cost(self, character: Character) -> None:
        """Apply resource costs when skill is used."""
        if not self.resource_cost:
            return

        for resource, cost in self.resource_cost.items():
            current = character.survival_stats.get(resource.lower(), 0)
            character.survival_stats[resource.lower()] = max(0, current - cost)


class SkillManager:
    """
    Manages skill learning, usage and progression.
    """

    def __init__(self) -> None:
        self.class_skill_trees: Dict[str, List[str]] = {
            "Warrior": ["bash", "cleave", "taunt", "second_wind", "shield_wall"],
            "Mage": ["fireball", "ice_bolt", "mana_shield", "teleport", "arcane_burst"],
            "Rogue": ["backstab", "stealth", "poison_strike", "evasion", "shadow_step"],
            "Cleric": ["heal", "smite", "bless", "turn_undead", "divine_shield"],
            "Ranger": ["aimed_shot", "track", "animal_companion", "snare", "volley"],
        }
        self.available_skills: Dict[str, Skill] = {}
        self._initialize_skills()

    def _initialize_skills(self) -> None:
        """Initialize all available skills with their data."""
        # Warrior skills
        self.available_skills["bash"] = Skill(
            id="bash",
            name="Bash",
            description="A powerful melee strike that can stun enemies",
            skill_type="combat",
            resource_cost={"stamina": 15},
            cooldown=3,
            effects=[
                {
                    "type": "damage",
                    "target": "enemy",
                    "amount": 10,
                    "duration": None,
                    "stat_modifier": {},
                },
                {
                    "type": "status",
                    "target": "enemy",
                    "amount": 0,
                    "duration": 1,
                    "stat_modifier": {"dexterity": -2},
                },
            ],
        )

        # Mage skills
        self.available_skills["fireball"] = Skill(
            id="fireball",
            name="Fireball",
            description="Launches a ball of fire at enemies",
            skill_type="combat",
            resource_cost={"mana": 20},
            cooldown=2,
            effects=[
                {
                    "type": "damage",
                    "target": "enemy",
                    "amount": 15,
                    "duration": None,
                    "stat_modifier": {},
                }
            ],
        )

        # Add more skills here...

    def get_available_skills(
        self, character: Character, skill_type: Optional[SkillType] = None
    ) -> List[Skill]:
        """Get all skills available to a character based on class and level."""
        class_skills = self.class_skill_trees.get(
            character.character_class, [])
        available = []

        for skill_id in class_skills:
            skill = self.available_skills.get(skill_id)
            if not skill:
                continue

            if character.level >= skill.level_requirement:
                if skill_type is None or skill.skill_type == skill_type:
                    available.append(skill)

        return available

    def use_skill(
        self, character: Character, skill_id: str, target: Any
    ) -> Dict[str, Any]:
        """Use a skill and apply its effects."""
        if skill_id not in character.skills:
            return {
                "success": False,
                "message": "You haven't learned this skill yet"}

        skill = self.available_skills.get(skill_id)
        if not skill:
            return {"success": False, "message": "Invalid skill"}

        if not skill.can_use(character):
            return {
                "success": False,
                "message": f"Not enough resources to use {skill.name}",
            }

        # Apply resource costs
        skill.apply_cost(character)

        # Apply effects
        results = []
        for effect in skill.effects:
            # Implement effect application based on type
            # This is where we'd integrate with combat/status systems
            results.append(
                f"{effect['type']} effect applied to {effect['target']}")

        return {
            "success": True,
            "message": f"Used {
                skill.name}",
            "effects": results}

    def learn_skill(self, character: Character,
                    skill_id: str) -> Dict[str, Any]:
        """Attempt to learn a new skill."""
        if skill_id in character.skills:
            return {"success": False, "message": "You already know this skill"}

        skill = self.available_skills.get(skill_id)
        if not skill:
            return {"success": False, "message": "Invalid skill"}

        # Check prerequisites
        for prereq in skill.prerequisites:
            if prereq not in character.skills:
                prereq_name = self.available_skills[prereq].name
                return {
                    "success": False,
                    "message": f"You need to learn {prereq_name} first",
                }

        if character.level < skill.level_requirement:
            return {
                "success": False,
                "message": f"Requires level {skill.level_requirement}",
            }

        character.skills.append(skill_id)
        return {"success": True, "message": f"Learned {skill.name}"}
