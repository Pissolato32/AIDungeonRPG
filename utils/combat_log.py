"""
Módulo de registro de combate.

Gerencia o histórico de combates e fornece estatísticas de batalha.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CombatAction:
    """Representa uma ação durante o combate."""

    actor: str
    target: str
    action_type: str
    damage: Optional[int] = None
    healing: Optional[int] = None
    effects: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CombatRound:
    """Representa uma rodada de combate."""

    round_number: int
    actions: List[CombatAction] = field(default_factory=list)
    status_effects: Dict[str, List[str]] = field(default_factory=dict)


class CombatLog:
    """Gerenciador de registro de combate."""

    def __init__(self) -> None:
        """Inicializa um novo registro de combate."""
        self.rounds: List[CombatRound] = []
        self.current_round: int = 0
        self.combat_stats: Dict[str, Any] = {
            "total_damage_dealt": 0,
            "total_damage_taken": 0,
            "total_healing": 0,
            "critical_hits": 0,
            "dodges": 0,
            "kills": 0,
        }

    def start_new_round(self) -> None:
        """Inicia uma nova rodada de combate."""
        self.current_round += 1
        self.rounds.append(CombatRound(self.current_round))

    def add_action(
        self,
        actor: str,
        target: str,
        action_type: str,
        damage: Optional[int] = None,
        healing: Optional[int] = None,
        effects: Optional[List[str]] = None,
    ) -> None:
        """
        Adiciona uma ação ao registro da rodada atual.

        Args:
            actor: Quem realizou a ação
            target: Alvo da ação
            action_type: Tipo de ação (ataque, cura, etc)
            damage: Dano causado (se houver)
            healing: Cura realizada (se houver)
            effects: Efeitos adicionais da ação
        """
        if not self.rounds:
            self.start_new_round()

        action = CombatAction(
            actor=actor,
            target=target,
            action_type=action_type,
            damage=damage,
            healing=healing,
            effects=effects or [],
        )

        self.rounds[-1].actions.append(action)
        self._update_stats(action)

    def add_status_effect(self, target: str, effect: str) -> None:
        """Adiciona um efeito de status a um alvo."""
        if not self.rounds:
            self.start_new_round()

        if target not in self.rounds[-1].status_effects:
            self.rounds[-1].status_effects[target] = []

        self.rounds[-1].status_effects[target].append(effect)

    def get_round_summary(self, round_number: int) -> Dict[str, Any]:
        """Retorna um resumo de uma rodada específica."""
        if 0 < round_number <= len(self.rounds):
            round_data = self.rounds[round_number - 1]
            return {
                "round": round_number,
                "actions": [
                    {
                        "actor": action.actor,
                        "target": action.target,
                        "type": action.action_type,
                        "damage": action.damage,
                        "healing": action.healing,
                        "effects": action.effects,
                    }
                    for action in round_data.actions
                ],
                "status_effects": round_data.status_effects,
            }
        return {}

    def get_combat_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas gerais do combate."""
        return self.combat_stats

    def get_actor_statistics(self, actor: str) -> Dict[str, Any]:
        """Retorna estatísticas específicas de um participante."""
        stats = {
            "damage_dealt": 0,
            "damage_taken": 0,
            "healing_done": 0,
            "critical_hits": 0,
            "actions_taken": 0,
        }

        for round_data in self.rounds:
            for action in round_data.actions:
                if action.actor == actor:
                    stats["actions_taken"] += 1
                    if action.damage:
                        stats["damage_dealt"] += action.damage
                    if action.healing:
                        stats["healing_done"] += action.healing
                    if "crítico" in action.effects:
                        stats["critical_hits"] += 1
                elif action.target == actor and action.damage:
                    stats["damage_taken"] += action.damage

        return stats

    def _update_stats(self, action: CombatAction) -> None:
        """Atualiza as estatísticas gerais do combate."""
        if action.damage:
            self.combat_stats["total_damage_dealt"] += action.damage

        if action.healing:
            self.combat_stats["total_healing"] += action.healing

        if "crítico" in action.effects:
            self.combat_stats["critical_hits"] += 1

        if "esquiva" in action.effects:
            self.combat_stats["dodges"] += 1

        if "morte" in action.effects:
            self.combat_stats["kills"] += 1

    def get_highlight_moments(self) -> List[Dict[str, Any]]:
        """Retorna os momentos mais destacados do combate."""
        highlights = []

        for round_data in self.rounds:
            for action in round_data.actions:
                # Golpes críticos
                if "crítico" in action.effects:
                    highlights.append(
                        {
                            "type": "critical",
                            "round": round_data.round_number,
                            "description": (
                                f"{action.actor} causou um golpe crítico em "
                                f"{action.target} causando {action.damage} de dano!"
                            ),
                        }
                    )

                # Grandes curas
                if action.healing and action.healing > 20:
                    highlights.append(
                        {
                            "type": "healing",
                            "round": round_data.round_number,
                            "description": (
                                f"{action.actor} curou {action.target} por "
                                f"{action.healing} pontos de vida!"
                            ),
                        }
                    )

                # Esquivas impressionantes
                if "esquiva" in action.effects:
                    highlights.append(
                        {
                            "type": "dodge",
                            "round": round_data.round_number,
                            "description": (
                                f"{action.target} esquivou-se habilmente do "
                                f"ataque de {action.actor}!"
                            ),
                        }
                    )

                # Abates
                if "morte" in action.effects:
                    highlights.append(
                        {
                            "type": "kill",
                            "round": round_data.round_number,
                            "description": (
                                f"{action.actor} derrotou {action.target}!"
                            ),
                        }
                    )

        return sorted(
            highlights,
            key=lambda x: (x["type"] == "kill", x["type"] == "critical", x["round"]),
            reverse=True,
        )[
            :5
        ]  # Retorna os 5 momentos mais interessantes
