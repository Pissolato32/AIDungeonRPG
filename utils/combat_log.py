"""
Módulo de registro de combate.

Gerencia o histórico de combates e fornece estatísticas de batalha.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CombatAction:
    """Representa uma ação durante o combate."""

    actor: str
    target: str
    action_type: str
    damage: Optional[int] = None
    healing: Optional[int] = None
    effects: List[str] = field(default_factory=list)
    is_headshot: Optional[bool] = False
    infection_attempted: Optional[bool] = False
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
            "total_damage_taken_by_survivors": 0,  # Mais específico
            "total_healing": 0,
            "golpes_criticos": 0,
            "esquivas_sortudas": 0,
            "zumbis_eliminados": 0,
            "sobreviventes_caidos": 0,
            "headshots_efetuados": 0,
            "tentativas_de_infeccao": 0,
            "infeccoes_bem_sucedidas": 0,
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
        is_headshot: Optional[bool] = False,
        infection_attempted: Optional[bool] = False,
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
            is_headshot: Se a ação foi um tiro na cabeça
            infection_attempted: Se houve uma tentativa de infecção
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
            is_headshot=is_headshot,
            infection_attempted=infection_attempted,
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
                        "is_headshot": action.is_headshot,
                        "infection_attempted": action.infection_attempted,
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
            "golpes_criticos_desferidos": 0,
            "actions_taken": 0,
            "headshots_feitos": 0,
            "infeccoes_causadas": 0,
        }

        for round_data in self.rounds:
            for action in round_data.actions:
                if action.actor == actor:
                    stats["actions_taken"] += 1
                    if action.damage:
                        stats["damage_dealt"] += action.damage
                    if action.healing:
                        stats["healing_done"] += action.healing
                    if "golpe_critico" in action.effects:
                        stats["golpes_criticos_desferidos"] += 1
                    if action.is_headshot:
                        stats["headshots_feitos"] += 1
                    if "infectado" in action.effects and action.infection_attempted:
                        stats["infeccoes_causadas"] += 1
                elif action.target == actor and action.damage:
                    stats["damage_taken"] += action.damage
                    # Poderia adicionar lógica para saber se o 'actor' é um sobrevivente
                    # para popular self.combat_stats["total_damage_taken_by_survivors"] aqui também.

        return stats

    def _update_stats(self, action: CombatAction) -> None:
        """Atualiza as estatísticas gerais do combate."""
        if action.damage:
            self.combat_stats["total_damage_dealt"] += action.damage
            # Assumindo que o log pode diferenciar se o alvo é sobrevivente
            # if target_is_survivor(action.target):
            # self.combat_stats["total_damage_taken_by_survivors"] += action.damage

        if action.healing:
            self.combat_stats["total_healing"] += action.healing

        if "golpe_critico" in action.effects:
            self.combat_stats["golpes_criticos"] += 1

        if action.is_headshot:
            self.combat_stats["headshots_efetuados"] += 1

        if "esquiva_sortuda" in action.effects:
            self.combat_stats["esquivas_sortudas"] += 1

        if "eliminacao_zumbi" in action.effects:
            self.combat_stats["zumbis_eliminados"] += 1
        elif "sobrevivente_caido" in action.effects:
            self.combat_stats["sobreviventes_caidos"] += 1

        if action.infection_attempted:
            self.combat_stats["tentativas_de_infeccao"] += 1
            if (
                "infectado" in action.effects
            ):  # Se o efeito "infectado" foi aplicado com sucesso
                self.combat_stats["infeccoes_bem_sucedidas"] += 1

    def get_highlight_moments(self) -> List[Dict[str, Any]]:
        """Retorna os momentos mais destacados do combate."""
        highlights = []

        for round_data in self.rounds:
            for action in round_data.actions:
                # Golpes críticos
                if "golpe_critico" in action.effects:
                    highlights.append(
                        {
                            "type": "golpe_critico",
                            "round": round_data.round_number,
                            "description": (
                                f"{action.actor} desferiu um GOLPE CRÍTICO em "
                                f"{action.target} causando {action.damage} de dano!"
                            ),
                        }
                    )

                # Grandes curas
                if action.healing and action.healing > 20:
                    highlights.append(
                        {
                            "type": "grande_cura",
                            "round": round_data.round_number,
                            "description": (
                                f"{action.actor} curou {action.target} por "
                                f"{action.healing} pontos de vida!"
                            ),
                        }
                    )

                # Esquivas impressionantes
                if "esquiva_sortuda" in action.effects:
                    highlights.append(
                        {
                            "type": "esquiva_sortuda",
                            "round": round_data.round_number,
                            "description": (
                                f"{action.target} esquivou-se habilmente do "
                                f"ataque de {action.actor}!"
                            ),
                        }
                    )

                # Eliminações de Zumbis
                if "eliminacao_zumbi" in action.effects:
                    highlights.append(
                        {
                            "type": "eliminacao_zumbi",
                            "round": round_data.round_number,
                            "description": (
                                f"{action.actor} eliminou o zumbi {action.target}!"
                            ),
                        }
                    )
                # Sobreviventes Caídos
                elif "sobrevivente_caido" in action.effects:
                    highlights.append(
                        {
                            "type": "sobrevivente_caido",
                            "round": round_data.round_number,
                            "description": (
                                f"O sobrevivente {action.target} foi derrubado por {action.actor}!"
                            ),
                        }
                    )
                # Tiros na cabeça
                if action.is_headshot:
                    highlights.append(
                        {
                            "type": "headshot",
                            "round": round_data.round_number,
                            "description": (
                                f"{action.actor} acertou um TIRO NA CABEÇA em {action.target}, causando {action.damage} de dano!"
                            ),
                        }
                    )
                # Infecções
                if "infectado" in action.effects and action.infection_attempted:
                    highlights.append(
                        {
                            "type": "infeccao",
                            "round": round_data.round_number,
                            "description": (
                                f"{action.target} foi INFECTADO pelo ataque de {action.actor}!"
                            ),
                        }
                    )

        return sorted(
            highlights,
            key=lambda x: (
                x["type"] == "sobrevivente_caido",
                x["type"] == "infeccao",
                x["type"] == "headshot",
                x["type"] == "golpe_critico",
                x["round"],
            ),
            reverse=True,
        )[
            :5
        ]  # Retorna os 5 momentos mais interessantes, priorizando os mais impactantes
