"""
Sistema de combate refatorado.

Este módulo gerencia as mecânicas de combate simplificadas.
Adaptado para um cenário de apocalipse zumbi.
"""

import random  # Importa o módulo random
from typing import Optional  # Importa Optional para type hinting

# Ajuste no import para refletir a nova estrutura de combat_stats.py

from .combat_stats import Character  # Alterado para import relativo
from utils.combat_log import CombatLog  # Opcional, para registrar o combate


class CombatSystem:
    """Sistema de gerenciamento de combate refatorado."""

    def __init__(self, player: Character, enemy: Character):
        self.player = player
        self.enemy = enemy
        self.combat_log: Optional[CombatLog] = None  # Log de combate opcional

    def set_combat_log(self, combat_log: CombatLog) -> None:
        """Define uma instância de CombatLog para ser usada pelo sistema."""
        self.combat_log = combat_log
        if self.combat_log:
            self.combat_log.start_new_round()  # Inicia o primeiro round no log

    def calculate_damage(self, attacker: Character, defender: Character) -> int:
        """Calcula dano com base nos stats dos personagens."""
        return max(attacker.stats.attack - defender.stats.defense, 1)

    def _attempt_headshot(self, attacker: Character, target: Character) -> bool:
        """Tenta um tiro na cabeça se o atacante for sobrevivente e o alvo um zumbi."""
        if not attacker.is_zombie and target.is_zombie:
            # Chance base de headshot + bônus pela habilidade de mira
            # Ex: 10% base + 2% por ponto em aim_skill
            headshot_chance = 0.10 + (attacker.stats.aim_skill * 0.02)
            return random.random() < headshot_chance
        return False

    def _attempt_infection(self, attacker: Character, target: Character) -> bool:
        """Tenta infectar o alvo se o atacante for zumbi e o alvo um sobrevivente não infectado."""
        if attacker.is_zombie and not target.is_zombie and not target.is_infected:
            infection_chance = 0.25  # Chance de 25% de infecção por ataque de zumbi
            return random.random() < infection_chance
        return False

    def attack(self, attacker: Character, target: Character) -> str:
        """Executa um ataque e retorna mensagem de resultado."""
        if not target.is_alive:
            return f"{target.name} já foi derrotado!"

        action_effects = []
        is_headshot_attempt = False
        infection_attempted_flag = False

        damage = self.calculate_damage(attacker, target)
        message = ""
        if self._attempt_headshot(attacker, target):
            is_headshot_attempt = True
            damage = int(damage * 3.5)  # Headshots causam dano massivo
            message += (
                f"💥 TIRO NA CABEÇA! {attacker.name} acerta em cheio {target.name}!"
            )
            action_effects.append("headshot_damage")
        else:
            message += f"{attacker.name} ataca {target.name}."

        # Tentativa de infecção
        if self._attempt_infection(attacker, target):
            infection_attempted_flag = True
            target.is_infected = True
            message += f" ☣️ {target.name} foi INFECTADO pelo ataque de {attacker.name}!"
            action_effects.append("infectado")

        target.stats.current_hp = max(
            target.stats.current_hp - damage, 0
        )  # Alterado de health para current_hp

        message += f" {target.name} sofre {damage} de dano."

        if target.stats.current_hp <= 0:  # Alterado de health para current_hp
            target.is_alive = False
            if target.is_zombie:
                message += f"\n💀 O zumbi {target.name} foi neutralizado!"
                action_effects.append("eliminacao_zumbi")
            else:
                message += f"\n✝️ {target.name} sucumbiu aos ferimentos!"
                action_effects.append("sobrevivente_caido")

        if self.combat_log:
            self.combat_log.add_action(
                actor=attacker.name,
                target=target.name,
                action_type=(
                    "ataque_zumbi" if attacker.is_zombie else "ataque_sobrevivente"
                ),
                damage=damage,
                effects=action_effects,
                is_headshot=is_headshot_attempt,
                infection_attempted=infection_attempted_flag,
            )

        return message

    def start_combat_round(self) -> str:
        """Controla um round completo de combate."""
        battle_log_messages = []

        if (
            self.combat_log and self.combat_log.current_round > 0
        ):  # Se já houve um round, inicia um novo
            # (a primeira rodada é iniciada quando o log é definido)
            # Ou podemos simplesmente chamar start_new_round sempre aqui,
            # e o log lida com a primeira inicialização.
            # Para simplificar, vamos assumir que o log já foi iniciado se existir.
            # Se não, o usuário deve chamar set_combat_log que inicia o primeiro round.
            pass  # A lógica de round do log é mais complexa, esta função foca nas mensagens de turno.

        # Ataque do jogador
        if self.player.is_alive:
            log = self.attack(self.player, self.enemy)
            if log:
                battle_log_messages.append(log)

        # Ataque do inimigo (se ainda vivo)
        if self.enemy.is_alive:
            log = self.attack(self.enemy, self.player)
        battle_log_messages.append(log)

        return "\n".join(battle_log_messages)
