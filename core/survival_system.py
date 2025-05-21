# filepath: c:\Users\rodri\Desktop\REPLIT RPG\core\survival_system.py
"""
Módulo de sistema de sobrevivência.
"""
# Código Refatorado do Sistema de Sobrevivência

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from core.models import Character


@dataclass
class SurvivalConfig:
    """Configurações para o sistema de sobrevivência."""

    STAT_MIN: int = 0
    STAT_MAX: int = 100
    INFECTION_RISK_THRESHOLD: int = 50
    HP_DAMAGE_FROM_INFECTION: int = 10
    DEFAULT_ACTION_COST: Dict[str, int] = {"hunger": 5, "thirst": 10}


class SurvivalManager:
    """Gerencia as mecânicas de sobrevivência de um personagem."""

    def __init__(self, config: Optional[SurvivalConfig] = None):
        self.config = config or SurvivalConfig()
        self.ACTION_COST = {
            action: self.config.DEFAULT_ACTION_COST.copy()
            for action in ["move", "attack", "flee", "craft"]
        }

    def _update_stat(self, character: Character, stat_name: str, amount: int) -> bool:
        """Atualiza uma estatística do personagem com limites configuráveis."""
        # Verifica se character.survival_stats.stat_name existe
        if not self._has_required_attributes(character, ["survival_stats", stat_name]):
            return False
        # Garante que survival_stats não é None antes de acessar stat_name
        current = getattr(character.survival_stats, stat_name)

        new_value = max(
            self.config.STAT_MIN, min(current + amount, self.config.STAT_MAX)
        )
        if new_value != current:
            setattr(character.survival_stats, stat_name, new_value)
            return True
        return False

    def _check_infection(self, character: Character) -> List[str]:
        """Verifica e aplica dano por infecção se necessário."""
        messages = []
        # Verifica se character.survival_stats.infection_risk existe
        if not self._has_required_attributes(
            character, ["survival_stats", "infection_risk"]
        ):
            return messages
        # Garante que survival_stats não é None
        infection_risk = character.survival_stats.infection_risk

        if infection_risk > self.config.INFECTION_RISK_THRESHOLD:
            # Verifica se character.stats.current_hp existe
            if self._has_required_attributes(character, ["stats", "current_hp"]):
                # Garante que stats não é None
                old_hp = character.stats.current_hp
                new_hp = max(0, old_hp - self.config.HP_DAMAGE_FROM_INFECTION)
                if new_hp < old_hp:
                    character.stats.current_hp = new_hp
                    messages.append(
                        f"{character.name} perdeu {self.config.HP_DAMAGE_FROM_INFECTION} HP por infecção."
                    )
        return messages

    def update_stats(
        self, character: Character, action: str
    ) -> Dict[str, Union[List[str], str]]:
        """Atualiza as estatísticas do personagem baseado na ação realizada."""
        messages = []
        if action in self.ACTION_COST:
            cost = self.ACTION_COST[action]
            for stat, amount in cost.items():
                if self._update_stat(character, stat, amount):
                    messages.append(f"Ação '{action}' aumentou {stat} em {amount}.")
        messages.extend(self._check_infection(character))
        return {"messages": messages, "status": "ok"}

    def _has_required_attributes(self, obj: Any, attribute_path: List[str]) -> bool:
        """
        Verifica se um objeto possui um caminho de atributos aninhados.
        Por exemplo, para verificar obj.attr1.attr2, attribute_path seria ["attr1", "attr2"].
        """
        current_obj = obj
        for i, attr_name in enumerate(attribute_path):
            if not hasattr(current_obj, attr_name):
                return False
            current_obj = getattr(current_obj, attr_name)
            # Se um atributo no meio do caminho for None, o caminho completo não pode ser acessado,
            # a menos que seja o último atributo do caminho (que pode ser None).
            if current_obj is None and i < len(attribute_path) - 1:
                return False
        return True
