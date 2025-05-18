"""
Skill system module for the RPG game.

This module provides the core skill system functionality including:
- Skill data models
- Skill usage and cooldown management
- Skill progression and unlocking
- Class skill trees
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union  # Added Union

from .models import Character

SkillType = Literal["active", "passive", "combat", "crafting", "survival"]
ResourceType = Literal["stamina", "mana", "focus", "rage"]
StatType = Literal[
    "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"
]


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
    resource_cost: Optional[Dict[ResourceType, int]] = None  # E.g. {"stamina": 10}
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
            # Assume resources like 'stamina', 'mana' are in character.attributes
            # as 'current_stamina', 'current_mana'
            attribute_key = f"current_{resource.lower()}"
            current = character.attributes.get(attribute_key, 0)
            if current < cost:
                return False
        return True

    def apply_cost(self, character: Character) -> None:
        """Apply resource costs when skill is used."""
        if not self.resource_cost:
            return

        for resource, cost in self.resource_cost.items():
            # Assume resources like 'stamina', 'mana' are in character.attributes
            attribute_key = f"current_{resource.lower()}"
            current = character.attributes.get(attribute_key, 0)
            character.attributes[attribute_key] = max(0, current - cost)


class SkillManager:
    """
    Manages skill learning, usage and progression.
    """

    def __init__(self) -> None:
        self.available_skills: Dict[str, Skill] = {}
        self._initialize_skills()

    def _initialize_skills(self) -> None:
        """Initialize all available skills with their data."""
        # Survivor Skills
        self.available_skills["first_aid_basics"] = Skill(
            id="first_aid_basics",
            name="First Aid Basics",
            description="Use scavenged supplies to patch up minor wounds.",
            skill_type="survival",
            resource_cost={"stamina": 10},  # Example cost
            cooldown=2,  # Example cooldown
            effects=[
                SkillEffect(
                    type="heal",
                    target="self",
                    amount=15,
                    duration=None,
                    stat_modifier={},
                )
            ],
        )
        self.available_skills["quick_fix"] = Skill(
            id="quick_fix",
            name="Quick Fix",
            description="Improvises a quick repair on a piece of equipment, restoring some durability.",
            skill_type="crafting",  # Could also be 'survival'
            resource_cost={"stamina": 15},
            cooldown=5,
            level_requirement=2,
            effects=[
                SkillEffect(
                    type="buff", target="self", amount=0, duration=0, stat_modifier={}
                )  # Placeholder, effect handled by action
            ],
            prerequisites=[
                "first_aid_basics"
            ],  # Example: learn basic mending before advanced repair
        )
        self.available_skills["scrounge"] = Skill(
            id="scrounge",
            name="Scrounge",
            description="Higher chance to find extra basic supplies when searching.",
            skill_type="passive",  # Passive skills might not have costs/cooldowns or direct "use" effects
            level_requirement=2,
            prerequisites=[],
            # Passive effects might be handled differently, e.g., by checking if a character has the skill
            # during a search action.
        )

        # Brawler Skills
        self.available_skills["power_strike"] = Skill(
            id="power_strike",
            name="Power Strike",
            description="A forceful melee attack that deals extra damage.",
            skill_type="combat",
            resource_cost={"stamina": 15},
            cooldown=3,
            effects=[
                SkillEffect(
                    type="damage",
                    target="enemy",
                    amount=12,
                    duration=None,
                    stat_modifier={},
                )
            ],
        )
        self.available_skills["improvised_weapon_mastery"] = Skill(
            id="improvised_weapon_mastery",
            name="Improvised Weapon Mastery",
            description="Increases damage and effectiveness with makeshift melee weapons.",
            skill_type="passive",
            level_requirement=3,
            prerequisites=["power_strike"],
        )
        self.available_skills["intimidate_shout"] = Skill(
            id="intimidate_shout",
            name="Intimidate Shout",
            description="Lets out a fearsome yell that might briefly stun weaker enemies or make them hesitate.",
            skill_type="combat",
            resource_cost={"stamina": 20, "rage": 5},  # Example of multi-resource
            cooldown=4,
            level_requirement=4,
            effects=[
                SkillEffect(
                    type="debuff",
                    target="enemy",
                    amount=0,
                    duration=1,
                    stat_modifier={"dexterity": -2},
                )  # Example: stun/slow
            ],
            prerequisites=["power_strike"],
        )

        # Sharpshooter Skills
        self.available_skills["steady_aim"] = Skill(
            id="steady_aim",
            name="Steady Aim",
            description="Take a moment to aim, increasing accuracy and damage for the next ranged attack.",
            skill_type="combat",
            resource_cost={"focus": 10},  # Assuming 'focus' is a resource
            cooldown=1,
            effects=[
                SkillEffect(
                    type="buff",
                    target="self",
                    amount=0,
                    duration=1,  # Lasts for 1 turn/next attack
                    stat_modifier={"dexterity": 2},
                )  # Example: +2 dexterity for accuracy/damage calc
            ],
            prerequisites=[],
        )
        self.available_skills["headshot_focus"] = Skill(
            id="headshot_focus",
            name="Headshot Focus",
            description="Passively increases critical hit chance with ranged weapons against humanoid targets.",
            skill_type="passive",
            level_requirement=3,
            prerequisites=["steady_aim"],
        )
        self.available_skills["ammo_crafter"] = Skill(
            id="ammo_crafter",
            name="Ammo Crafter",
            description="Allows crafting of basic ammunition from scavenged components.",
            skill_type="crafting",
            level_requirement=2,
            resource_cost={"focus": 5},  # Small focus cost to represent concentration
            effects=[],  # Crafting outcome handled by crafting system
            prerequisites=[],
        )

        # Medic Skills (Example)
        self.available_skills["advanced_first_aid"] = Skill(
            id="advanced_first_aid",
            name="Advanced First Aid",
            description="Heals more significant wounds and can remove minor infections.",
            skill_type="survival",
            resource_cost={"stamina": 15, "focus": 5},
            cooldown=3,
            level_requirement=3,
            effects=[
                SkillEffect(
                    type="heal",
                    target="self",
                    amount=30,
                    duration=None,
                    stat_modifier={},
                ),
                SkillEffect(
                    type="status", target="self", amount=0, duration=0, stat_modifier={}
                ),  # Represents 'cure_infection_low'
            ],
            prerequisites=["first_aid_basics"],
        )

        # Scavenger Skills (Example)
        self.available_skills["lockpicking"] = Skill(
            id="lockpicking",
            name="Lockpicking",
            description="Attempt to pick simple locks on doors and containers.",
            skill_type="survival",  # Or utility
            resource_cost={"focus": 10},
            cooldown=1,  # Cooldown might represent time taken or tool wear
            level_requirement=2,
            effects=[],  # Success/failure handled by action
            prerequisites=["scrounge"],
        )

        # Engineer Skills (Example)
        self.available_skills["barricade_expert"] = Skill(
            id="barricade_expert",
            name="Barricade Expert",
            description="Quickly construct a makeshift barricade to slow down enemies or provide cover.",
            skill_type="crafting",  # Or tactical
            resource_cost={"stamina": 20},
            cooldown=5,  # Represents time and effort
            level_requirement=3,
            effects=[],  # Barricade creation handled by action
            prerequisites=["quick_fix"],
        )

    def get_available_skills(
        self, character: Character, skill_type: Optional[SkillType] = None
    ) -> List[Skill]:
        """Get all skills available to a character based on class and level."""
        # class_skills = self.class_skill_trees.get(character.character_class, []) # REMOVIDO
        available = []

        # Agora iteramos por todas as habilidades e verificamos os requisitos
        for skill_id, skill in self.available_skills.items():
            if character.level >= skill.level_requirement:
                # Verifica se o personagem já possui os pré-requisitos
                has_prerequisites = True
                for prereq_id in skill.prerequisites:
                    if prereq_id not in character.skills:
                        has_prerequisites = False
                        break
                if has_prerequisites:
                    if skill_type is None or skill.skill_type == skill_type:
                        available.append(skill)

        return available

    def use_skill(
        self, character: Character, skill_id: str, target: Any
    ) -> Dict[str, Any]:
        """Use a skill and apply its effects."""
        if skill_id not in character.skills:
            return {"success": False, "message": "You haven't learned this skill yet"}

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
        applied_effects_summary = []  # For the main message
        for effect_data in skill.effects:
            # Implement effect application based on type
            # This is where we'd integrate with combat/status systems
            # For now, just build a summary for the message
            applied_effects_summary.append(
                f"{effect_data.get('type','unknown')} on {effect_data.get('target','unknown')} "
                f"(amount: {effect_data.get('amount',0)})"
            )

        return {
            "success": True,
            "message": f"Used {skill.name}. Effects: {', '.join(applied_effects_summary)}",
            "raw_effects": skill.effects,  # Pass the original list of SkillEffect dicts
        }

    def learn_skill(self, character: Character, skill_id: str) -> Dict[str, Any]:
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
