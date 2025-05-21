# filepath: c:\Users\rodri\Desktop\REPLIT RPG\core\survival_system.py
"""
Módulo de sistema de sobrevivência.
"""

# Altera o import para usar a classe Character definida em combat_stats.py
from .combat_stats import Character


class SurvivalStats:
    """Armazena e gerencia os atributos de sobrevivência de um personagem."""

    def __init__(self, hunger: int, thirst: int, stamina: int, infection_risk: int):
        """
        Inicializa os atributos de sobrevivência.

        Args:
            hunger: Nível de fome do personagem.
            thirst: Nível de sede do personagem.
            stamina: Nível de estamina/energia do personagem.
            infection_risk: Risco de infecção do personagem.
        """
        self.hunger = hunger
        self.thirst = thirst
        self.stamina = stamina
        self.infection_risk = infection_risk


class SurvivalSystem:
    """Gerencia as mecânicas de sobrevivência de um personagem."""

    def __init__(self, character: Character):
        """
        Inicializa o sistema de sobrevivência para um personagem específico.

        Args:
            character: O personagem cujas estatísticas de sobrevivência serão gerenciadas.
                       Espera-se que character.survival_stats seja uma instância de SurvivalStats
                       e que character tenha um atributo 'health'.
        """
        self.character = character

    def update_hunger(self, amount: int) -> None:
        """Atualiza o nível de fome do personagem."""
        self.character.survival_stats.hunger += (
            amount  # Agora deve encontrar survival_stats
        )
        # Adicionar lógica para garantir que a fome não ultrapasse limites (e.g., 0 a 100) se necessário.

    def update_thirst(self, amount: int) -> None:
        """Atualiza o nível de sede do personagem."""
        self.character.survival_stats.thirst += (
            amount  # Agora deve encontrar survival_stats
        )
        # Adicionar lógica para garantir que a sede não ultrapasse limites se necessário.

    def check_infection(self) -> None:
        """Verifica o risco de infecção e aplica penalidades se necessário."""
        if (
            self.character.survival_stats.infection_risk > 50
        ):  # Agora deve encontrar survival_stats
            # Acessa a saúde através de character.stats.health
            self.character.stats.health -= 10
            # Adicionar lógica para garantir que a saúde não fique abaixo de 0, se necessário.
            # Pode ser útil logar ou retornar uma mensagem sobre a perda de saúde.
