"""
Sistema de combate refatorado.

Este módulo gerencia as mecânicas de combate simplificadas.
Adaptado para um cenário de apocalipse zumbi.
"""

import random  # Importa o módulo random
from typing import Optional, Union  # Importa Optional e Union para type hinting

# Import Character from core.models
from .models import Character
from .enemy import Enemy  # Import Enemy class
from utils.combat_log import CombatLog  # Opcional, para registrar o combate


class CombatSystem:
    """Sistema de gerenciamento de combate refatorado."""

    def __init__(self, player: Character, enemy: Enemy):  # Enemy type hint for enemy
        self.player = player
        self.enemy = enemy
        self.combat_log: Optional[CombatLog] = None  # Log de combate opcional
        self.current_attacker_is_player: bool = True  # Player usually starts

    def set_combat_log(self, combat_log: CombatLog) -> None:
        """Define uma instância de CombatLog para ser usada pelo sistema."""
        self.combat_log = combat_log
        if self.combat_log:
            self.combat_log.start_new_round()  # Inicia o primeiro round no log

    def _get_combatant_stats(self, combatant: Union[Character, Enemy]):
        """Helper to get relevant combat stats based on type."""
        if isinstance(combatant, Character):  # Player
            return (
                combatant.stats.attack,
                combatant.stats.defense,
                combatant.stats.current_hp,
                combatant.stats.aim_skill,
            )
        elif isinstance(combatant, Enemy):  # Enemy
            return (
                combatant.attack,
                combatant.defense,
                combatant.current_hp,
                combatant.aim_skill,
            )
        raise TypeError("Unsupported combatant type")

    def _set_combatant_hp(self, combatant: Union[Character, Enemy], new_hp: int):
        """Helper to set HP based on type."""
        if isinstance(combatant, Character):
            combatant.stats.current_hp = new_hp
        elif isinstance(combatant, Enemy):
            combatant.current_hp = new_hp
        else:
            raise TypeError("Unsupported combatant type for setting HP")

    def calculate_damage(
        self, attacker: Union[Character, Enemy], defender: Union[Character, Enemy]
    ) -> int:
        """Calcula dano com base nos stats dos personagens."""
        attacker_attack, _, _, _ = self._get_combatant_stats(attacker)
        _, defender_defense, _, _ = self._get_combatant_stats(defender)
        return max(attacker_attack - defender_defense, 1)

    def _attempt_headshot(
        self, attacker: Union[Character, Enemy], target: Union[Character, Enemy]
    ) -> bool:
        """Tenta um tiro na cabeça se o atacante for sobrevivente e o alvo um zumbi."""
        _, _, _, attacker_aim_skill = self._get_combatant_stats(attacker)
        if not attacker.is_zombie and target.is_zombie:
            # Chance base de headshot + bônus pela habilidade de mira
            # Ex: 10% base + 2% por ponto em aim_skill
            headshot_chance = 0.10 + (attacker_aim_skill * 0.02)
            return random.random() < headshot_chance
        return False

    def _attempt_infection(
        self, attacker: Union[Character, Enemy], target: Union[Character, Enemy]
    ) -> bool:
        """Tenta infectar o alvo se o atacante for zumbi e o alvo um sobrevivente não infectado."""
        # Infection logic:
        # - Attacker must be an Enemy and a zombie.
        # - Target must be a Character (player) and not already infected.
        if (
            isinstance(attacker, Enemy)
            and attacker.is_zombie
            and isinstance(target, Character)
            and not target.is_infected  # Check the property
        ):
            infection_chance = 0.25  # 25% chance of infection by zombie attack
            return random.random() < infection_chance
        return False

    def attack(
        self, attacker: Union[Character, Enemy], target: Union[Character, Enemy]
    ) -> str:
        """Executa um ataque e retorna mensagem de resultado."""
        # 'is_alive' is not a direct attribute on Enemy or Character.
        # We check HP instead.
        _, _, target_hp, _ = self._get_combatant_stats(target)
        if target_hp <= 0:
            return f"{target.name} já foi derrotado(a)!"

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
            # If target is a Character, modify survival_stats.infection_risk
            if isinstance(target, Character):
                target.survival_stats.infection_risk = (
                    100  # Set to a value that makes is_infected true
                )
            # If target is an Enemy, its is_infected is usually set at creation or by other means
            message += f" ☣️ {target.name} foi INFECTADO pelo ataque de {attacker.name}!"
            action_effects.append("infectado")

        new_target_hp = max(target_hp - damage, 0)
        self._set_combatant_hp(target, new_target_hp)

        message += f" {target.name} sofre {damage} de dano ({target.name} HP: {new_target_hp})."

        if new_target_hp <= 0:
            # target.is_alive = False # is_alive is not a direct attribute to set. HP check is sufficient.
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

        _, _, player_hp, _ = self._get_combatant_stats(self.player)
        _, _, enemy_hp, _ = self._get_combatant_stats(self.enemy)

        # Ataque do jogador
        if player_hp > 0:
            log = self.attack(self.player, self.enemy)
            if log:
                battle_log_messages.append(log)
            # Re-check enemy HP after player's attack
            _, _, enemy_hp, _ = self._get_combatant_stats(self.enemy)

        # Ataque do inimigo (se ainda vivo)
        if enemy_hp > 0:
            log = self.attack(self.enemy, self.player)
            battle_log_messages.append(log)

        return "\n".join(battle_log_messages)
