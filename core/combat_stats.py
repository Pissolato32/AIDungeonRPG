"""
Módulo para definir as estatísticas e a estrutura base de personagens.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

# Para evitar importação circular em tempo de execução, mas permitir type checking
if TYPE_CHECKING:
    from .survival_system import SurvivalStats


@dataclass
class CharacterStats:
    """Armazena os atributos de combate de um personagem."""

    health: int
    attack: int
    defense: int
    aim_skill: int = 0  # Habilidade de mira, influencia headshots


class Character:
    """Representa um personagem no jogo."""

    def __init__(
        self,
        name: str,
        stats: CharacterStats,
        survival_stats: "SurvivalStats",
        is_zombie: bool = False,  # Para identificar se o personagem é um zumbi
    ):
        """Inicializa um personagem."""
        self.name = name
        self.stats: CharacterStats = stats  # Atributo obrigatório
        self.survival_stats: "SurvivalStats" = (
            survival_stats  # Atributo de sobrevivência
        )
        self.is_alive: bool = True
        self.is_zombie: bool = is_zombie
        self.is_infected: bool = (
            False  # Estado de infecção do personagem (se não for zumbi de início)
        )
        if is_zombie:  # Zumbis já começam infectados e "mortos-vivos"
            self.is_infected = True
