"""
Sistema de combate.

Este módulo gerencia as mecânicas de combate entre personagens e inimigos.
"""

import random
from typing import Dict, List, Any, Tuple, Optional
from core.models import Character
from utils.combat_log import CombatLog
from utils.dice import roll_dice


class CombatSystem:
    """Sistema de gerenciamento de combate."""

    def __init__(self) -> None:
        """Inicializa o sistema de combate."""
        self.combat_log = CombatLog()
        self._status_effects: Dict[str, List[Dict[str, Any]]] = {}

    def initiate_combat(
        self, character: Character, enemies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Inicia um novo combate.

        Args:
            character: Personagem do jogador
            enemies: Lista de inimigos no encontro

        Returns:
            Informações iniciais do combate
        """
        self.combat_log = CombatLog()
        self._status_effects.clear()

        # Determinar ordem de iniciativa
        initiative_order = self._determine_initiative(character, enemies)

        # Registrar início do combate
        self.combat_log.start_new_round()

        return {
            "message": self._generate_combat_start_message(enemies),
            "initiative_order": initiative_order,
            "combat_id": id(self.combat_log),
        }

    def process_combat_round(
        self,
        character: Character,
        enemies: List[Dict[str, Any]],
        character_action: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Processa uma rodada de combate.

        Args:
            character: Personagem do jogador
            enemies: Lista de inimigos ativos
            character_action: Ação escolhida pelo jogador

        Returns:
            Resultado da rodada de combate
        """
        self.combat_log.start_new_round()

        # Processar ação do jogador
        action_result = self._process_character_action(
            character, character_action, enemies
        )

        # Processar ações dos inimigos
        enemy_results = []
        for enemy in enemies:
            if enemy.get("health", 0) > 0:  # Apenas inimigos vivos agem
                enemy_action = self._generate_enemy_action(enemy, character)
                result = self._process_enemy_action(enemy, enemy_action, character)
                enemy_results.append(result)

        # Processar efeitos de status
        self._process_status_effects(character, enemies)

        # Verificar condições de fim de combate
        combat_status = self._check_combat_status(character, enemies)

        return {
            "character_result": action_result,
            "enemy_results": enemy_results,
            "status_effects": self._status_effects,
            "combat_status": combat_status,
            "highlights": self.combat_log.get_highlight_moments(),
        }

    def _determine_initiative(
        self, character: Character, enemies: List[Dict[str, Any]]
    ) -> List[str]:
        """Determina a ordem de iniciativa no combate."""
        initiatives = []

        # Iniciativa do personagem
        char_init = roll_dice(1, 20)["total"] + character.agility
        initiatives.append(("character", char_init))

        # Iniciativa dos inimigos
        for i, enemy in enumerate(enemies):
            enemy_init = roll_dice(1, 20)["total"] + enemy.get("agility", 0)
            initiatives.append((f"enemy_{i}", enemy_init))

        # Ordenar por iniciativa
        initiatives.sort(key=lambda x: x[1], reverse=True)
        return [init[0] for init in initiatives]

    def _process_character_action(
        self,
        character: Character,
        action: Dict[str, Any],
        enemies: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Processa a ação do personagem."""
        action_type = action.get("type", "attack")
        target_id = action.get("target")

        if action_type == "attack":
            if not target_id:
                return {
                    "success": False,
                    "message": "Alvo não especificado para o ataque.",
                }
            defender_enemy = self._find_enemy(enemies, target_id)
            if not defender_enemy:
                return {
                    "success": False,
                    "message": f"Inimigo alvo com ID '{target_id}' não encontrado.",
                }
            return self._process_attack(
                attacker=character,
                defender=defender_enemy,
                is_character=True,
            )
        if action_type == "skill":
            skill_id_val = action.get("skill_id")
            if not isinstance(skill_id_val, str):
                return {
                    "success": False,
                    "message": "Ação de habilidade requer um 'skill_id' (string).",
                }

            target_enemy_for_skill = self._find_enemy(enemies, target_id)
            # If a target_id was provided, but the enemy was not found, it's an error.
            if target_id and not target_enemy_for_skill:
                return {
                    "success": False,
                    "message": f"Alvo com ID '{target_id}' não encontrado para a habilidade.",
                }

            return self._process_skill(
                character=character,
                skill_id=skill_id_val,
                target=target_enemy_for_skill,
            )
        if action_type == "item":
            item_id_val = action.get("item_id")
            if not isinstance(item_id_val, str):
                return {
                    "success": False,
                    "message": "Ação de item requer um 'item_id' (string).",
                }

            target_enemy_for_item = self._find_enemy(enemies, target_id)
            # If a target_id was provided, but the enemy was not found, it's an error.
            if target_id and not target_enemy_for_item:
                return {
                    "success": False,
                    "message": f"Alvo com ID '{target_id}' não encontrado para o item.",
                }

            return self._process_item_use(
                character=character,
                item_id=item_id_val,
                target=target_enemy_for_item,
            )
        return {"success": False, "message": "Ação inválida"}

    def _process_attack(
        self,
        attacker: Any,
        defender: Any,
        is_character: bool = False,  # defender will be Character or Dict
    ) -> Dict[str, Any]:
        """Processa um ataque básico."""
        # Calcular chance de acerto
        # hit_roll_result = roll_dice(1, 20) # This variable was defined but not used for the hit check below.
        accuracy = attacker.agility if is_character else attacker.get("agility", 0)
        defense = defender.agility if not is_character else defender.get("agility", 0)

        if roll_dice(1, 20)["total"] + accuracy <= defense:
            self.combat_log.add_action(
                actor=attacker.name if is_character else attacker["name"],
                target=defender["name"] if is_character else defender.name,
                action_type="attack",
                effects=["esquiva"],
            )
            return {
                "success": False,
                "message": f"{defender['name']} esquivou-se do ataque!",
            }

        # Calcular dano
        damage_value = roll_dice(1, 6)["total"]
        damage_bonus = attacker.strength if is_character else attacker.get("damage", 0)

        # Verificar crítico
        is_critical = roll_dice(1, 20)["total"] == 20
        if is_critical:
            damage_value *= 2

        total_damage = damage_value + damage_bonus

        # Aplicar dano
        if is_character:
            defender["health"] = defender.get("health", 0) - total_damage
        else:
            defender.health -= total_damage

        effects = []
        if is_critical:
            effects.append("crítico")
        if (is_character and defender["health"] <= 0) or (
            not is_character and defender.health <= 0
        ):
            effects.append("morte")

        self.combat_log.add_action(
            actor=attacker.name if is_character else attacker["name"],
            target=defender["name"] if is_character else defender.name,
            action_type="attack",
            damage=total_damage,
            effects=effects,
        )

        return {
            "success": True,
            "damage": total_damage,
            "critical": is_critical,
            "message": self._generate_attack_message(
                attacker.name if is_character else attacker["name"],
                total_damage,
                is_critical,
            ),
        }

    def _process_skill(
        self, character: Character, skill_id: str, target: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Processa o uso de uma habilidade."""
        # Implementar lógica de habilidades aqui
        # Por enquanto retorna um erro
        return {
            "success": False,
            "message": "Sistema de habilidades em desenvolvimento",
        }

    def _process_item_use(
        self, character: Character, item_id: str, target: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Processa o uso de um item."""
        # Implementar lógica de uso de itens aqui
        # Por enquanto retorna um erro
        return {"success": False, "message": "Sistema de itens em desenvolvimento"}

    def _generate_enemy_action(
        self, enemy: Dict[str, Any], character: Character
    ) -> Dict[str, Any]:
        """Gera uma ação para um inimigo."""
        # Por enquanto, inimigos apenas atacam
        return {"type": "attack", "target": "character"}

    def _process_enemy_action(
        self, enemy: Dict[str, Any], action: Dict[str, Any], character: Character
    ) -> Dict[str, Any]:
        """Processa a ação de um inimigo."""
        if action["type"] == "attack":
            return self._process_attack(
                attacker=enemy, defender=character, is_character=False
            )
        return {"success": False, "message": "Ação inválida"}

    def _process_status_effects(
        self, character: Character, enemies: List[Dict[str, Any]]
    ) -> None:
        """Processa efeitos de status ativos."""
        # Processar efeitos no personagem
        char_effects = self._status_effects.get(character.name, [])
        for effect in char_effects[:]:
            effect["duration"] -= 1
            if effect["duration"] <= 0:
                char_effects.remove(effect)
            else:
                self._apply_status_effect(character, effect, True)

        # Processar efeitos nos inimigos
        for enemy in enemies:
            enemy_effects = self._status_effects.get(enemy["name"], [])
            for effect in enemy_effects[:]:
                effect["duration"] -= 1
                if effect["duration"] <= 0:
                    enemy_effects.remove(effect)
                else:
                    self._apply_status_effect(enemy, effect, False)

    def _apply_status_effect(
        self, target: Any, effect: Dict[str, Any], is_character: bool
    ) -> None:
        """Aplica um efeito de status."""
        effect_type = effect.get("type")
        if effect_type == "poison":
            damage = effect.get("damage", 2)
            if is_character:
                target.health -= damage
            else:
                target["health"] -= damage

            self.combat_log.add_action(
                actor="Veneno",
                target=target.name if is_character else target["name"],
                action_type="status_effect",
                damage=damage,
                effects=["poison"],
            )

    def _check_combat_status(
        self, character: Character, enemies: List[Dict[str, Any]]
    ) -> str:
        """Verifica o estado atual do combate."""
        if character.health <= 0:
            return "defeat"

        if all(enemy["health"] <= 0 for enemy in enemies):
            return "victory"

        return "ongoing"

    def _find_enemy(
        self, enemies: List[Dict[str, Any]], target_id: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Encontra um inimigo específico na lista."""
        if not target_id:
            return None

        for enemy in enemies:
            if enemy.get("id") == target_id:
                return enemy
        return None

    def _generate_combat_start_message(self, enemies: List[Dict[str, Any]]) -> str:
        """Gera mensagem de início de combate."""
        if len(enemies) == 1:
            return f"Um {enemies[0]['name']} aparece!"
        enemy_names = [e["name"] for e in enemies]
        return (
            f"Um grupo de {len(enemies)} inimigos aparece: "
            f"{', '.join(enemy_names)}!"
        )

    def _generate_attack_message(
        self, attacker: str, damage: int, critical: bool
    ) -> str:
        """Gera mensagem descritiva de ataque."""
        if critical:
            return f"{attacker} acerta um golpe crítico " f"causando {damage} de dano!"
        return f"{attacker} ataca causando {damage} de dano!"
