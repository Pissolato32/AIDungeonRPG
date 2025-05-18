# filepath: c:\Users\rodri\Desktop\REPLIT RPG\core\survival_system.py
"""
Módulo de sistema de sobrevivência.

Este módulo fornece funcionalidades para gerenciar mecânicas de sobrevivência
de personagens, como fome, sede, energia e temperatura.
"""

import logging
from typing import Any, Dict, List, TypedDict, cast

from core.models import Character

logger = logging.getLogger(__name__)


class SurvivalStats(TypedDict):
    """Definição de tipo para estatísticas de sobrevivência."""

    # This TypedDict should reflect the structure of character.survival_stats
    current_hunger: int
    current_thirst: int
    current_energy: int
    current_temperature: int


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
        # Max values are now expected to be in character.survival_stats (e.g., max_hunger)
        self._depletion_rates = {
            "current_hunger": 2,
            "current_thirst": 3,
            "current_energy": 1,
        }
        self._critical_thresholds = {
            "current_hunger": 20,
            "current_thirst": 15,
            "current_energy": 10,
            "current_temperature": (35, 65),  # (min, max) intervalo confortável
        }

    def initialize_stats(self, character: Character) -> None:
        """Inicializa estatísticas de sobrevivência do personagem."""
        # Character model should initialize survival_stats with current_hunger, max_hunger, etc.
        # This method can ensure all necessary keys are present if not already.
        default_survival_stats = {
            "current_hunger": 100,
            "max_hunger": 100,
            "current_thirst": 100,
            "max_thirst": 100,
            "current_energy": 100,
            "max_energy": 100,
            "current_temperature": 50,  # Assuming 50 is a neutral/comfortable starting point
        }
        if (
            not getattr(character, "survival_stats", None)
            or not character.survival_stats
        ):
            character.survival_stats = default_survival_stats.copy()
        else:
            for key, value in default_survival_stats.items():
                character.survival_stats.setdefault(key, value)

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
        # Ensure survival_stats is properly initialized.
        # The Character model should ideally do this in its __init__.
        # This call ensures it if somehow missed or if the structure needs verification.
        if not hasattr(character, "survival_stats") or not character.survival_stats:
            self.initialize_stats(character)
            logger.info(
                f"Re-initialized survival stats for character {getattr(character, 'name', 'Unknown')}"
            )

        stats = character.survival_stats  # This is a Dict[str, Any]
        messages: List[str] = []
        effects: List[str] = []

        # Aplicar custos de ação (modifies current_STAT, caps with max_STAT)
        action_costs = self._get_action_costs(action)
        for stat_key, cost in action_costs.items():
            if stat_key in stats:  # stat_key is like "current_hunger"
                current_value = stats.get(stat_key, 0)
                stats[stat_key] = max(0, current_value - cost)

        # Aplicar efeitos ambientais (modifies current_STAT, caps with max_STAT from survival_stats)
        env_effects = self._get_environmental_effects(environment)
        for effect in env_effects:
            effects.append(effect["name"])
            for stat_key, modifier in effect["stats_modifier"].items():
                if stat_key in stats:  # stat_key is like "current_temperature"
                    current_value = stats.get(stat_key, 0)
                    max_value_key = stat_key.replace("current_", "max_")
                    # Temperature might not have a simple max, handle differently or use a wide range.
                    # For hunger/thirst/energy, use their specific max.
                    # For temperature, min/max is more about comfort range, not a hard cap like HP.
                    # Let's assume temperature changes are direct for now, critical_conditions handles effects.
                    if "temperature" in stat_key:
                        stats[stat_key] = current_value + modifier
                    elif max_value_key in stats:
                        stats[stat_key] = max(
                            0, min(stats[max_value_key], current_value + modifier)
                        )
                    else:  # Fallback if no max_STAT, just apply and clamp at 0
                        stats[stat_key] = max(0, current_value + modifier)

        critical_msgs = self._check_critical_conditions(character)  # Pass character
        messages.extend(critical_msgs)

        # Depleção natural (modifies current_STAT)
        for stat_key, rate in self._depletion_rates.items():
            if stat_key in stats:
                current_value = stats.get(stat_key, 0)
                stats[stat_key] = max(0, current_value - rate)

        # Verificar efeitos nas estatísticas vitais (modifies character.attributes['current_hp'])
        self._apply_vital_effects(character, messages)  # Pass character

        # Salvar estatísticas atualizadas
        character.survival_stats = (
            stats  # stats is already a reference to character.survival_stats
        )

        return {"stats": stats, "messages": messages, "effects": effects}

    @staticmethod
    def _get_action_costs(action: str) -> Dict[str, int]:
        """Calcula custos de energia para ações."""
        # Keys should be 'current_hunger', 'current_thirst', 'current_energy'
        costs = {
            "move": {"current_energy": 5, "current_thirst": 3, "current_hunger": 2},
            "fight": {
                "current_energy": 15
            },  # Direct HP cost for actions is unusual, damage is via combat
            "run": {"current_energy": 20, "current_thirst": 8},
            "swim": {
                "current_energy": 10,
                "current_temperature": -5,
            },  # Temperature change
            "climb": {"current_energy": 25, "current_thirst": 5},
            "rest": {
                "current_energy": -30,
                "current_hunger": 5,
            },  # Resting makes you hungrier
            "eat": {"current_hunger": -40},  # Eating reduces hunger
            "drink": {"current_thirst": -50},  # Drinking reduces thirst
            "sleep": {
                "current_energy": -100,
                "current_hunger": 10,
                "current_thirst": 15,
            },
        }
        return costs.get(action, {"current_energy": 1})

    @staticmethod
    def _get_environmental_effects(environment: str) -> List[EnvironmentalEffect]:
        """Obtém efeitos do ambiente atual."""
        effects: Dict[str, List[EnvironmentalEffect]] = {
            "desert": [
                {
                    "name": "Calor Extremo",
                    "description": "O sol escaldante drena sua energia",
                    "stats_modifier": {
                        "current_thirst": -8,
                        "current_temperature": 15,
                        "current_energy": -3,
                    },
                    "duration": 5,
                }
            ],
            "snow": [
                {
                    "name": "Frio Intenso",
                    "description": "O frio congela seus ossos",
                    "stats_modifier": {
                        "current_temperature": -15,
                        "current_energy": -5,
                    },
                    "duration": 5,
                }
            ],
            "forest": [
                {
                    "name": "Umidade",
                    "description": "A umidade da floresta é revigorante",
                    "stats_modifier": {"current_temperature": -2, "current_thirst": -1},
                    "duration": 3,
                }
            ],
            "mountain": [
                {
                    "name": "Altitude",
                    "description": "O ar rarefeito dificulta a respiração",
                    "stats_modifier": {
                        "current_energy": -5,
                        "current_temperature": -10,
                    },
                    "duration": 4,
                }
            ],
        }
        return effects.get(environment, [])

    def _check_critical_conditions(self, character: Character) -> List[str]:
        """Verifica condições críticas de sobrevivência."""
        messages = []
        stats = character.survival_stats  # This is a Dict[str, Any]

        if (
            stats.get("current_hunger", 100)
            <= self._critical_thresholds["current_hunger"]
        ):
            messages.append(
                "Seu estômago está doendo de fome. " "Precisa comer algo logo!"
            )

        if (
            stats.get("current_thirst", 100)
            <= self._critical_thresholds["current_thirst"]
        ):
            messages.append(
                "Sua garganta está seca. " "Precisa encontrar água rapidamente!"
            )

        if (
            stats.get("current_energy", 100)
            <= self._critical_thresholds["current_energy"]
        ):
            messages.append(
                "Você mal consegue manter os olhos abertos. " "Precisa descansar!"
            )

        temp_min, temp_max = self._critical_thresholds["current_temperature"]
        current_temp = stats.get("current_temperature", 50)
        if current_temp < temp_min:
            messages.append("Você está tremendo de frio. " "Precisa se aquecer!")
        elif current_temp > temp_max:
            messages.append("O calor está insuportável. " "Precisa se refrescar!")

        return messages

    @staticmethod
    def _apply_vital_effects(character: Character, messages: List[str]) -> None:
        """Aplica efeitos nas estatísticas vitais."""
        # Health (HP) is in character.attributes
        # Survival stats (hunger, thirst, energy) are in character.survival_stats
        survival_stats = character.survival_stats

        if character.attributes.get("current_hp", 0) <= 0:
            messages.append("Você está gravemente ferido e precisa de cura!")
        if survival_stats.get("current_hunger", 100) <= 0:
            character.attributes["current_hp"] = max(
                0, character.attributes.get("current_hp", 0) - 5
            )
            messages.append("Você está morrendo de fome!")
        if survival_stats.get("current_thirst", 100) <= 0:
            character.attributes["current_hp"] = max(
                0, character.attributes.get("current_hp", 0) - 10
            )
            messages.append("Você está severamente desidratado!")
        if survival_stats.get("current_energy", 100) <= 0:
            character.attributes["current_hp"] = max(
                0, character.attributes.get("current_hp", 0) - 3
            )
            messages.append("Você está exausto e precisa descansar!")
