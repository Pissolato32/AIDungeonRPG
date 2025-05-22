"""
Módulo para definir as estatísticas base de combate para entidades.
"""

from dataclasses import dataclass, field


@dataclass
class CharacterStats:
    """Armazena os atributos de combate de um personagem."""

    # health foi renomeado para current_hp e max_hp foi adicionado para consistência
    current_hp: int
    max_hp: int
    attack: int
    defense: int
    aim_skill: int = 0  # Habilidade de mira, influencia headshots
