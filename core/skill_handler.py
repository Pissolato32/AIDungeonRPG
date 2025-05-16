"""
Skill action handler for using skills in combat and other scenarios.
"""

from typing import Dict, Any
from .actions import ActionHandler
from .models import Character
from .skills import SkillManager


class SkillActionHandler(ActionHandler):
    """Handler for 'skill' action."""

    def __init__(self) -> None:
        """Initialize the skill handler."""
        self.skill_manager = SkillManager()

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        """
        Handle skill usage. Details should contain the skill ID to use.
        """
        if not details:
            available_skills = self.skill_manager.get_available_skills(character)
            skill_names = [skill.name for skill in available_skills]
            return {
                "success": True,
                "message": f"Available skills: {', '.join(skill_names)}",
            }

        # Extract skill ID
        skill_id = details.lower().replace(" ", "_")

        # Get target - for now we assume enemy in combat
        target = None
        if hasattr(game_state, "combat") and game_state.combat:
            target = game_state.combat.get("enemy")

        # Use the skill
        result = self.skill_manager.use_skill(character, skill_id, target)

        # If successful and in combat, apply combat effects
        if result["success"] and target:
            self._apply_combat_effects(result, game_state)

            # Add effects to combat log
            if "combat" in game_state.__dict__ and "log" in game_state.combat:
                for effect in result.get("effects", []):
                    game_state.combat["log"].append(effect)

        return result

    def _apply_combat_effects(self, result: Dict[str, Any], game_state: Any) -> None:
        """Apply skill effects in combat."""
        if not game_state.combat or not game_state.combat.get("enemy"):
            return

        combat = game_state.combat
        enemy = combat["enemy"]

        # For now we just apply damage
        # This should be expanded to handle different effect types
        for effect in result.get("effects", []):
            if "damage" in effect:
                enemy.current_hp = max(0, enemy.current_hp - effect["damage"])
