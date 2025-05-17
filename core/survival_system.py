"""
Módulo de sistema de sobrevivência.

Este módulo fornece funcionalidades para gerenciar mecânicas de sobrevivência
de personagens, como fome, sede, energia e temperatura.
"""

import logging
from typing import Dict, Any, List, TypedDict, cast
from core.models import Character

logger = logging.getLogger(__name__)


class SurvivalStats(TypedDict):
    """Definição de tipo para estatísticas de sobrevivência."""

    health: int
    hunger: int
    thirst: int
    energy: int
    temperature: int


class EnvironmentalEffect(TypedDict):
    """Definição de tipo para efeitos ambientais."""

    name: str
    description: str
    stats_modifier: Dict[str, int]
    duration: int


class SurvivalSystem:
    """
    Gerencia as mecânicas de sobrevivência do personagem.

    Recursos:
    - Decaimento de fome, sede e energia ao longo do tempo
    - Efeitos de fome, sede e temperatura nas estatísticas
    - Consumo de comida e água
    - Efeitos ambientais dinâmicos
    - Sistema de temperatura corporal
    - Condições climáticas variáveis
    """

    def __init__(self) -> None:
        """Inicializa o sistema de sobrevivência com valores base."""
        self._max_stats = {
            "health": 100,
            "hunger": 100,
            "thirst": 100,
            "energy": 100,
            "temperature": 100,
        }
        self._depletion_rates = {"hunger": 2, "thirst": 3, "energy": 1}
        self._critical_thresholds = {
            "hunger": 20,
            "thirst": 15,
            "energy": 10,
            "temperature": (35, 65),  # (min, max) intervalo confortável
        }

    def initialize_stats(self, character: Character) -> None:
        """Inicializa estatísticas de sobrevivência do personagem."""
        stats = {}
        for stat in ["health", "hunger", "thirst", "energy"]:
            stats[stat] = self._max_stats[stat]
        stats["temperature"] = self._max_stats["temperature"] // 2
        character.survival_stats = stats

    def update_stats(
        self, character: Character, action: str, environment: str = "normal"
    ) -> Dict[str, Any]:
        """
        Atualiza as estatísticas do personagem.

        Args:
            character: O personagem a ser atualizado
            action: A ação sendo realizada
            environment: O tipo de ambiente atual

        Returns:
            Dict com estatísticas atualizadas e mensagens
        """
        # Ensure survival_stats is properly initialized if it doesn't exist,
        # is None, or is an empty dictionary.
        if not getattr(character, "survival_stats", None):
            self.initialize_stats(character)
            logger.info(
                f"Initialized survival stats for character {getattr(character, 'name', 'Unknown')}"
            )

        stats = character.survival_stats
        messages: List[str] = []
        effects: List[str] = []

        # Aplicar custos de ação
        action_costs = self._get_action_costs(action)
        for stat, cost in action_costs.items():
            if stat in stats:
                stats[stat] = max(0, stats[stat] - cost)

        # Aplicar efeitos ambientais
        env_effects = self._get_environmental_effects(environment)
        for effect in env_effects:
            effects.append(effect["name"])
            for stat, modifier in effect["stats_modifier"].items():
                if stat in stats:
                    new_val = stats[stat] + modifier
                    stats[stat] = max(
                        0, min(self._max_stats[stat], new_val)
                    )  # Verificar condições críticas
        typed_stats = cast(SurvivalStats, stats)
        critical_msgs = self._check_critical_conditions(typed_stats)
        messages.extend(critical_msgs)

        # Depleção natural
        for stat, rate in self._depletion_rates.items():
            if stat in stats:
                stats[stat] = max(0, stats[stat] - rate)

        # Verificar efeitos nas estatísticas vitais
        self._apply_vital_effects(typed_stats, messages)

        # Salvar estatísticas atualizadas
        character.survival_stats = stats

        return {"stats": stats, "messages": messages, "effects": effects}

    def _get_action_costs(self, action: str) -> Dict[str, int]:
        """Calcula custos de energia para ações."""
        costs = {
            "move": {"energy": 5, "thirst": 3, "hunger": 2},
            "fight": {"energy": 15, "health": 10},
            "run": {"energy": 20, "thirst": 8},
            "swim": {"energy": 10, "temperature": -5},
            "climb": {"energy": 25, "thirst": 5},
            "rest": {"energy": -30, "hunger": 5},
            "eat": {"hunger": -40},
            "drink": {"thirst": -50},
            "sleep": {"energy": -100, "hunger": 10, "thirst": 15},
        }
        return costs.get(action, {"energy": 1})

    def _get_environmental_effects(self, environment: str) -> List[EnvironmentalEffect]:
        """Obtém efeitos do ambiente atual."""
        effects: Dict[str, List[EnvironmentalEffect]] = {
            "desert": [
                {
                    "name": "Calor Extremo",
                    "description": "O sol escaldante drena sua energia",
                    "stats_modifier": {"thirst": -8, "temperature": 15, "energy": -3},
                    "duration": 5,
                }
            ],
            "snow": [
                {
                    "name": "Frio Intenso",
                    "description": "O frio congela seus ossos",
                    "stats_modifier": {"temperature": -15, "energy": -5},
                    "duration": 5,
                }
            ],
            "forest": [
                {
                    "name": "Umidade",
                    "description": "A umidade da floresta é revigorante",
                    "stats_modifier": {"temperature": -2, "thirst": -1},
                    "duration": 3,
                }
            ],
            "mountain": [
                {
                    "name": "Altitude",
                    "description": "O ar rarefeito dificulta a respiração",
                    "stats_modifier": {"energy": -5, "temperature": -10},
                    "duration": 4,
                }
            ],
        }
        return effects.get(environment, [])

    def _check_critical_conditions(self, stats: SurvivalStats) -> List[str]:
        """Verifica condições críticas de sobrevivência."""
        messages = []

        if stats["hunger"] <= self._critical_thresholds["hunger"]:
            messages.append(
                "Seu estômago está doendo de fome. " "Precisa comer algo logo!"
            )

        if stats["thirst"] <= self._critical_thresholds["thirst"]:
            messages.append(
                "Sua garganta está seca. " "Precisa encontrar água rapidamente!"
            )

        if stats["energy"] <= self._critical_thresholds["energy"]:
            messages.append(
                "Você mal consegue manter os olhos abertos. " "Precisa descansar!"
            )

        temp_min, temp_max = self._critical_thresholds["temperature"]
        if stats["temperature"] < temp_min:
            messages.append("Você está tremendo de frio. " "Precisa se aquecer!")
        elif stats["temperature"] > temp_max:
            messages.append("O calor está insuportável. " "Precisa se refrescar!")

        return messages

    def _apply_vital_effects(self, stats: SurvivalStats, messages: List[str]) -> None:
        """Aplica efeitos nas estatísticas vitais."""
        if stats["health"] <= 0:
            messages.append("Você está gravemente ferido e precisa de cura!")
        if stats["hunger"] <= 0:
            stats["health"] = max(0, stats["health"] - 5)
            messages.append("Você está morrendo de fome!")
        if stats["thirst"] <= 0:
            stats["health"] = max(0, stats["health"] - 10)
            messages.append("Você está severamente desidratado!")
        if stats["energy"] <= 0:
            stats["health"] = max(0, stats["health"] - 3)
            messages.append("Você está exausto e precisa descansar!")
