# filepath: c:\Users\rodri\Desktop\REPLIT RPG\core\actions.py
import logging
import os
import random
import re  # Importar re para regex
from typing import Any, Dict, List, Optional, Tuple, cast  # Added Tuple

from core.enemy import Enemy  # Import Enemy class
from core.models import Character
from utils.dice import calculate_attribute_modifier, calculate_damage, roll_dice
from utils.quest_generator import generate_quest  # Import generate_quest

from .recipes import CRAFTING_RECIPES  # For CraftActionHandler
from .skills import SkillManager  # For SkillActionHandler
from .world_generator import WorldGenerator

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ActionHandler:
    """
    Base class for action handlers.
    Subclasses must implement the 'handle' method.
    """

    # Base class for action handlers. Subclasses must implement 'handle'.
    def handle(
        self, details: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement this method")


class MoveActionHandler(ActionHandler):
    """Handler for the 'move' action."""

    def handle(
        self, details: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        logger.info(
            f"MoveActionHandler: Recebido details='{details}', location_id='{game_state.location_id}'"
        )
        # Init world generator
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        world_generator = WorldGenerator(data_dir)

        destination = details.strip().lower() if isinstance(details, str) else ""
        current_location_id = game_state.location_id
        directions = ["norte", "sul", "leste", "oeste"]  # Traduzido

        logger.debug(
            f"MoveActionHandler: Current location ID: {current_location_id}, Destination input: '{destination}'"
        )
        # Normalize input
        normalized_direction: Optional[str] = next(
            (d for d in directions if d in destination), None
        )
        if (
            not hasattr(game_state, "world_map")
            or not game_state.world_map  # Checa se o world_map em si está vazio ou é None
        ):
            logger.warning(
                "MoveActionHandler: game_state.world_map não está configurado corretamente ou não contém 'locations'. "
                f"world_map atual: {getattr(game_state, 'world_map', 'Não definido')}"
            )
            logger.warning("MoveActionHandler: World map error condition met.")
            # Se o mapa não está pronto, a IA deve narrar a falha ou a tentativa.
            # Retornamos sucesso=True para que o GameEngine chame a IA com action="move"
            return {
                "success": True,
                "message": f"Você tenta se mover para {details}, mas o mapa não está claro.",
                "action_performed": "move_failed_map_error",  # Indica para a IA que a mecânica falhou
            }

        # Acessar localizações diretamente do world_map
        current_location_data = game_state.world_map.get(current_location_id, {})
        connections = current_location_data.get("connections", {})
        logger.debug(
            f"MoveActionHandler: Connections for '{current_location_id}': {connections}. Normalized direction: '{normalized_direction}'"
        )

        next_location_id: Optional[str] = None

        # Try existing connections
        for dir_key, loc_id in connections.items():
            if (
                normalized_direction is None
                and loc_id in game_state.world_map
                and game_state.world_map.get(loc_id, {}).get("name", "").lower()
                in destination
            ):
                next_location_id = loc_id
                break
            elif (
                dir_key.lower() == normalized_direction
            ):  # Checar direção normalizada depois
                next_location_id = loc_id
                break

        logger.debug(
            f"MoveActionHandler: Found next_location_id by connection: '{next_location_id}'"
        )

        # If not found, generate adjacent location
        if next_location_id is None and normalized_direction:
            logger.info(
                f"MoveActionHandler: No existing connection found for direction '{normalized_direction}'. Attempting to generate new location."
            )
            new_location = world_generator.generate_adjacent_location(
                current_location_id, normalized_direction, game_state.world_map
            )

            # Ensure new locations are properly added (incorporating user suggestion)
            # Add the new location to the world_map only if its ID isn't already present.
            # This adds robustness in case the generator could theoretically return an existing ID.
            if new_location["id"] not in game_state.world_map:
                game_state.world_map[new_location["id"]] = new_location

            # Update the connections of the original current_location (defined earlier in the method).
            # The user's suggestion included re-fetching current_location_data here,
            # which is generally not needed as the original reference is still valid.
            current_location_data.setdefault("connections", {})[
                normalized_direction
            ] = new_location["id"]
            logger.info(
                f"MoveActionHandler: Generated new location '{new_location['id']}' and updated connections for '{current_location_id}'."
            )
            next_location_id = new_location["id"]

        # Garantir que visited_locations exista no game_state
        if not hasattr(game_state, "visited_locations"):
            game_state.visited_locations = {}

        # If found or generated
        if next_location_id and next_location_id in game_state.world_map:
            logger.info(
                f"MoveActionHandler: Moving to location_id '{next_location_id}'."
            )
            next_location = game_state.world_map[next_location_id]
            game_state.location_id = next_location_id
            game_state.current_location = next_location["name"]
            game_state.coordinates = next_location["coordinates"].copy()

            # Agora é seguro acessar game_state.visited_locations diretamente
            visited_info = game_state.visited_locations.get(next_location_id)

            if visited_info and next_location.get(
                "visited"
            ):  # Checar se o local já foi visitado antes
                visited_info["last_visited"] = "revisited"
                game_state.scene_description = visited_info["description"]
                game_state.npcs_present = visited_info["npcs_seen"]
                # Marcar como visitado no world_map também, se não estiver
                if not game_state.world_map[next_location_id].get("visited"):
                    game_state.world_map[next_location_id]["visited"] = True
                # Optional: add new events
                if random.random() < 0.3:
                    game_state.events = world_generator.generate_events(
                        next_location["name"], next_location.get("type", "unknown")
                    )
                else:
                    game_state.events = visited_info.get("events_seen", [])

                game_state.visited_locations[next_location_id] = visited_info

                return {
                    "success": True,
                    "message": f"Você se move para {next_location['name']}.",  # Mensagem para IA narrar a chegada
                    "action_performed": "move",
                    "current_detailed_location": next_location["name"],  # Novo local
                    "scene_description_update": next_location["description"],
                    "npcs_present": game_state.npcs_present,  # NPCs do novo local
                    "events": game_state.events,  # Eventos do novo local
                }
            # First visit
            game_state.scene_description = next_location["description"]
            game_state.npcs_present = next_location["npcs"]
            game_state.events = next_location.get(
                "events", []
            )  # Adicionar get com fallback
            game_state.world_map[next_location_id][
                "visited"
            ] = True  # Marcar como visitado

            # game_state.visited_locations é garantido existir aqui
            game_state.visited_locations[next_location_id] = {
                # Usar o nome do next_location, pois game_state.current_location já foi atualizado
                "name": next_location["name"],
                "last_visited": "first_time",
                "description": game_state.scene_description,
                "npcs_seen": game_state.npcs_present.copy(),
                "events_seen": game_state.events.copy(),
                "search_results": [],  # Initialize search_results
            }

            return {
                "success": True,
                "message": f"Você chega em {next_location['name']}. {next_location['description']}",
                "action_performed": "move",  # Para a IA saber que foi um movimento
                "current_detailed_location": next_location["name"],  # Novo local
                "scene_description_update": next_location[
                    "description"
                ],  # Nova descrição
                "npcs": game_state.npcs_present,
                "events": game_state.events,
                # Campos antigos 'new_location' e 'description' podem ser removidos se o frontend usar os novos
            }

        # Se o movimento falhou (direção inválida, etc.)
        # Retornamos sucesso=True para que o GameEngine chame a IA com action="move"
        return {
            "success": True,
            "action_performed": "move_failed_no_path",
            "message": f"Você tenta se mover para '{details}', mas não encontra um caminho claro ou a direção é inválida.",
            # Manter current_detailed_location e scene_description_update com os valores atuais do game_state
        }


class LookActionHandler(ActionHandler):
    """Handler for the 'look' action."""

    def handle(
        self, details: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        """Handle the 'look' action, either observing an NPC or the environment."""

        # This handler signals to GameEngine to let the AI describe what the player sees.
        # The 'details' (what the player wants to look at) will be passed to the AI.
        return {
            "success": True,  # The action of "looking" is always mechanically possible
            "action_performed": "look_attempt",
            "message": f"Você olha ao redor de '{details if details else game_state.current_location}'.",  # Mensagem para a IA
            # No 'message' here, GameEngine will use original 'details' for AI prompt
        }


class TalkActionHandler(ActionHandler):
    """Handler for 'talk' action."""

    def handle(
        self, details: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        # A lógica mecânica do 'talk' é mínima. A IA fará a maior parte da interação.
        # Retornamos sucesso=True para que o GameEngine chame a IA com action="talk"
        # O 'details' (com quem o jogador quer falar) será passado para a IA.
        if details and details.strip():
            npc_query_name = details.strip()
            npc_query_name_lower = npc_query_name.lower()

            # Verificar se o NPC está presente
            if game_state.npcs_present and any(
                npc.lower() == npc_query_name_lower for npc in game_state.npcs_present
            ):
                # Se o NPC está presente, a IA cuidará da interação.
                # Podemos adicionar mecânicas aqui no futuro, como verificações de carisma,
                # ou se o NPC está disposto a falar.
                return {
                    "success": True,
                    "action_performed": "talk_attempt_npc_present",
                    "message": f"Você tenta falar com {npc_query_name}.",  # Mensagem para a IA
                    "npc_name": npc_query_name,  # Passa o nome do NPC para uso interno e da IA
                }
            else:
                # NPC não encontrado ou não especificado claramente
                return {
                    "success": True,  # A ação de tentar falar foi processada
                    "action_performed": "talk_attempt_npc_not_found",
                    "message": f"Você tenta falar com '{npc_query_name}', mas não parece haver ninguém com esse nome por perto.",
                }

        # Se 'details' estiver vazio (ex: jogador digitou apenas "falar")
        return {
            "success": True,
            "action_performed": "talk_attempt_generic",
            "message": "Você olha ao redor, procurando alguém para conversar, mas não especifica quem.",
        }

    # O método get_npc_details e a lógica de interação com known_npcs
    # foram removidos daqui. Essa lógica, se necessária,
    # deve ser gerenciada pelo GameEngine ou pela IA com base no
    # 'action_performed' e nos dados do game_state.
    # A IA pode, por exemplo, acessar game_state.known_npcs para enriquecer a narrativa.

    # def get_npc_details(...) e a lógica de interação anterior foram removidas
    # para simplificar e delegar mais à IA e ao GameEngine.

    def get_npc_details(
        self, npc_name: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        return game_state.known_npcs.get(
            npc_name,
            {
                "race": "Humano",
                "profession": "Sobrevivente",
                "personality": "Cauteloso",
                "level": character.level,
                "knowledge": [],
                "quests": [],
            },
        )


class SearchActionHandler(ActionHandler):
    """Handler for 'search' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        # A lógica mecânica do 'search' é mínima. A IA fará a maior parte da descrição do que é encontrado.
        details_lower = details.lower() if isinstance(details, str) else ""
        if "missão" in details_lower or "tarefa" in details_lower:  # Traduzido "quest"
            # Add null check and validation
            if (
                not getattr(game_state, "npcs_present", None)
                or len(game_state.npcs_present) == 0
            ):
                return {
                    "success": False,
                    "message": "Não há ninguém por perto que possa oferecer missões no momento.",
                }

            # Filter valid NPC names and check again
            valid_npcs = [
                npc
                for npc in game_state.npcs_present
                if isinstance(npc, str) and npc.strip()
            ]
            if not valid_npcs:
                return {
                    "success": False,
                    "message": "Não há NPCs válidos disponíveis para oferecer missões no momento.",
                }

            if not hasattr(game_state, "quests"):
                game_state.quests = []

            quest_giver = random.choice(valid_npcs)
            new_quest = generate_quest(
                location=game_state.current_location,
                difficulty=character.level,
            )
            new_quest["giver"] = quest_giver
            new_quest["location"] = game_state.current_location
            game_state.quests.append(new_quest)
            return {
                "success": True,
                "message": f"{quest_giver} oferece uma nova missão: {new_quest['name']}. {new_quest['description']} Recompensa: {new_quest['reward_gold']} moedas de ouro.",
            }

        # Retornamos sucesso=True para que o GameEngine chame a IA com action="search"
        return {
            "success": True,
            "action_performed": "search_attempt",  # Indica para a IA que a mecânica foi processada
            "message": f"Você começa a procurar por '{details if details else 'algo interessante'}'.",  # Mensagem para a IA
        }


class AttackActionHandler(ActionHandler):
    """Handler for 'attack' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        # A lógica de combate é complexa e pode ser resolvida mecanicamente AQUI.
        # A IA será chamada DEPOIS para narrar o resultado mecânico.

        # Verificar se já está em combate
        if (
            game_state.combat
            and game_state.combat.get("active")
            # A verificação de game_state.combat.get("enemy") será feita abaixo com isinstance
        ):
            enemy_data = game_state.combat.get("enemy")

            # Garantir que enemy_data é uma instância de Enemy
            if not isinstance(enemy_data, Enemy):
                logger.error(
                    f"AttackActionHandler: game_state.combat['enemy'] não é uma instância de Enemy. "
                    f"Tipo encontrado: {type(enemy_data)}. Valor: {enemy_data}"
                )
                return {
                    "success": False,
                    "message": "Erro crítico no estado de combate: dados do inimigo inválidos.",
                    "action_performed": "attack_failed_enemy_data_error",
                }

            enemy: Enemy = (
                enemy_data  # Agora temos certeza do tipo e podemos usar type hinting
            )

            # Lógica de ataque contra o inimigo atual
            # Corrigido: Acessar stats aninhados
            str_modifier = calculate_attribute_modifier(character.stats.strength)

            # Acesso direto aos atributos do inimigo
            to_hit_dc = 10 + enemy.level

            # Rolagem de ataque (d20 + modificador)
            attack_roll_result = roll_dice(1, 20, str_modifier)
            attack_roll = attack_roll_result["total"]
            attack_roll_string = attack_roll_result["result_string"]

            mechanical_outcome_message = ""
            damage_dealt = 0
            combat_log_entry = ""
            action_performed_type = "attack_resolved"  # Default resolved type

            if attack_roll >= to_hit_dc:
                # Acertou! Calcular dano.
                # Lógica de dano da arma equipada ou dano base
                weapon_damage_dice_num = 1
                weapon_damage_dice_sides = 6  # Dano base de uma arma simples (d6)
                equipped_weapon_name = character.equipment.get("weapon")
                weapon_data = None
                if equipped_weapon_name:
                    # Precisamos de uma forma de obter dados de itens aqui
                    # Importar ItemGenerator ou ter um cache de itens
                    try:
                        from utils.item_generator import ItemGenerator

                        # Padronizar caminho para o diretório de dados
                        data_dir_path = os.path.join(
                            os.path.dirname(os.path.abspath(__file__)), "..", "data"
                        )
                        item_gen = ItemGenerator(data_dir_path)
                        weapon_data = item_gen.get_item_by_name(equipped_weapon_name)
                    except ImportError:
                        logger.error("ItemGenerator not found for AttackActionHandler.")
                    except Exception as e:
                        logger.error(f"Error loading weapon data: {e}")

                if weapon_data and weapon_data.get("type") == "weapon":
                    # Usar dados de dano da arma
                    dmg_min = weapon_data.get("damage_min", 1)
                    dmg_max = weapon_data.get(
                        "damage_max", 4
                    )  # Exemplo de dano de arma leve
                    # Rola um dado com faces igual à diferença + 1, e adiciona o mínimo e o modificador
                    damage_roll_result = roll_dice(
                        1, (dmg_max - dmg_min + 1), dmg_min - 1 + str_modifier
                    )
                else:
                    # Dano base (ex: soco, arma genérica)
                    damage_roll_result = roll_dice(
                        1, 4, str_modifier
                    )  # Exemplo: 1d4 + modificador de Força

                damage_dealt = max(
                    1,  # Dano mínimo de 1
                    damage_roll_result["total"] - enemy.defense,  # Acesso direto
                )

                # Aplicar dano ao inimigo
                enemy.current_hp = max(0, enemy.current_hp - damage_dealt)

                combat_log_entry = f"Você atacou {enemy.name} e causou {damage_dealt} de dano! ({attack_roll_string} vs DC {to_hit_dc})"
                mechanical_outcome_message = (
                    f"Você acertou {enemy.name} causando {damage_dealt} de dano."
                )

                if enemy.current_hp <= 0:
                    # Inimigo derrotado
                    combat_log_entry += f" {enemy.name} foi derrotado!"
                    mechanical_outcome_message += f" {enemy.name} foi derrotado."
                    game_state.combat["active"] = False  # Fim do combate
                    game_state.combat["enemy"] = None  # Remover inimigo
                    action_performed_type = "attack_kill"

            else:
                # Errou!
                damage_dealt = 0
                combat_log_entry = f"Você tentou atacar {enemy.name}, mas errou! ({attack_roll_string} vs DC {to_hit_dc})"
                mechanical_outcome_message = f"Você errou o ataque contra {enemy.name}."
                action_performed_type = "attack_miss"

            # Adicionar entrada ao log de combate
            if "log" not in game_state.combat or not isinstance(
                game_state.combat["log"], list
            ):
                game_state.combat["log"] = []  # Garantir que o log existe e é uma lista
            game_state.combat["log"].append(combat_log_entry)

            # Retornar resultado mecânico para a IA narrar
            return {
                "success": True,  # A ação mecânica foi processada
                "action_performed": action_performed_type,  # Tipo de resultado mecânico
                "combat_ongoing": (
                    game_state.combat.get("active", False)
                    if game_state.combat
                    else False
                ),
                "enemy_hp": enemy.current_hp,
                "enemy_max_hp": enemy.max_hp,
                "combat_log_update": combat_log_entry,  # Enviar a última entrada do log para o frontend
            }

        # Se não está em combate, mas a ação é "attack" com um alvo específico
        if details and details.strip():
            target_name_query = details.strip()
            target_name_lower = target_name_query.lower()

            # Verificar se o alvo é um NPC presente
            npc_to_attack: Optional[str] = None
            if game_state.npcs_present:
                try:
                    npc_to_attack = next(
                        npc
                        for npc in game_state.npcs_present
                        if npc.lower() == target_name_lower
                    )
                except StopIteration:
                    pass  # Alvo não é um NPC presente

            if npc_to_attack:
                # Iniciar combate com o NPC
                # Você precisará de uma forma de obter ou gerar stats para NPCs que viram inimigos
                # Gerar stats para o inimigo
                max_hp_val = random.randint(
                    character.level * 10 + 10, character.level * 15 + 30
                )  # Ex: entre 20-60 para nível 1
                current_hp_val = random.randint(
                    int(max_hp_val * 0.7), max_hp_val
                )  # Começa com 70-100% HP
                enemy_attack_stat = random.randint(
                    character.level + 2, character.level + 7
                )  # Ex: 3-8 para nível 1
                enemy_defense_stat = random.randint(
                    character.level + 1, character.level + 5
                )  # Ex: 2-6 para nível 1

                enemy = Enemy(
                    # Campos de CharacterStats (herdado por Enemy)
                    current_hp=current_hp_val,
                    max_hp=max_hp_val,
                    attack=enemy_attack_stat,
                    defense=enemy_defense_stat,
                    # aim_skill pode usar o default de CharacterStats (0) ou ser definido aqui
                    # Campos específicos de Enemy
                    name=npc_to_attack,
                    level=random.randint(character.level, character.level + 2),
                    attack_damage_min=random.randint(3, 8),
                    attack_damage_max=random.randint(9, 15),
                    description=f"Um(a) hostil {npc_to_attack} que você decidiu atacar.",
                    # xp_reward, gold_reward, etc., usarão os defaults de Enemy se não especificados
                )
                game_state.combat = {
                    "active": True,  # Combate ativo
                    "enemy": enemy,
                    "round": 1,
                    "log": [f"Você iniciou combate com {npc_to_attack}!"],
                }
                # Remover NPC da lista de npcs_present se ele virou inimigo? Depende da sua lógica.
                # if npc_to_attack in game_state.npcs_present:
                #     game_state.npcs_present.remove(npc_to_attack)

                return {
                    "success": True,  # Mecanicamente, o combate foi iniciado
                    "message": f"Você atacou {npc_to_attack} e iniciou um combate!",  # Mensagem para a IA narrar o início
                    "action_performed": "combat_start_npc",
                    "combat_ongoing": True,
                    "enemy_name": enemy.name,  # type: ignore
                    "enemy_hp": enemy.current_hp,
                    "enemy_max_hp": enemy.max_hp,
                    "combat_log_update": game_state.combat["log"][-1],
                }

            # Se o alvo não é um NPC presente, talvez seja um inimigo genérico ou algo no ambiente
            # A IA pode interpretar isso.
            # Retornamos sucesso=True para que o GameEngine chame a IA com action="attack"
            return {
                "success": True,
                "action_performed": "attack_attempt_target",
                "message": f"Você se prepara para atacar '{details.strip()}'.",  # Mensagem para a IA
            }

        # Se a ação é "attack" sem detalhes (ex: "attack" ou "atacar")
        # A IA pode interpretar como procurar por inimigos ou se preparar para combate.
        # Retornamos sucesso=True para que o GameEngine chame a IA com action="attack"
        return {
            "success": True,
            "action_performed": "attack_attempt_generic",
            "message": "Você se prepara para o combate, procurando por um alvo.",  # Mensagem para a IA
        }


class UseItemActionHandler(ActionHandler):
    """Handler for 'use_item' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        # A lógica mecânica de usar item acontece AQUI.
        # A IA será chamada DEPOIS para narrar o resultado mecânico.

        from utils.item_generator import ItemGenerator

        # Precisamos do caminho para o diretório de dados para ItemGenerator
        data_dir_path = os.path.join(  # Padronizado
            os.path.dirname(os.path.abspath(__file__)), "..", "data"
        )
        item_generator = ItemGenerator(data_dir_path)

        item_name_query = (
            details.strip().lower() if isinstance(details, str) else ""
        )  # Normalize query

        if (
            not item_name_query
            or not hasattr(character, "inventory")
            or not character.inventory
        ):
            return {
                "success": False,
                "message": "Você não especificou qual item usar ou seu inventário está vazio.",
            }

        item_index = -1
        item_data: Optional[Dict[str, Any]] = None
        actual_item_name: Optional[str] = None

        # Procurar o item no inventário
        for i, inv_item in enumerate(character.inventory):
            # Tenta encontrar pelo nome, seja string ou dict['name']
            inv_item_name = ""
            if isinstance(inv_item, str):
                inv_item_name = inv_item
            elif isinstance(inv_item, dict) and "name" in inv_item:
                inv_item_name = inv_item["name"]

            if (
                inv_item_name and inv_item_name.strip().lower() == item_name_query
            ):  # Compare with normalized query
                item_index = i
                actual_item_name = inv_item_name
                # Se o item no inventário já é um dict, use-o.
                if isinstance(inv_item, dict):
                    item_data = inv_item
                else:
                    # Senão, carregue os dados.
                    # actual_item_name é garantidamente str aqui devido ao 'if inv_item_name:'
                    if actual_item_name is None:
                        raise ValueError("actual_item_name should not be None here.")
                    name_for_lookup: str = actual_item_name
                    item_data = item_generator.get_item_by_name(name_for_lookup)
                break  # Item encontrado
        logger.info(f"Tentando usar: '{item_name_query}'")
        logger.info(f"Inventário atual: {character.inventory}")
        if item_index == -1 or actual_item_name is None or item_data is None:
            # actual_item_name é None aqui ou item não foi encontrado, ou item_data não pôde ser carregado.
            return {
                "success": False,
                "message": f"Você não tem '{item_name_query}' no seu inventário.",
            }

        # Item encontrado, processar uso
        # Se chegamos aqui, actual_item_name NÃO é None, e item_data NÃO é None.
        if actual_item_name is None:
            raise RuntimeError("actual_item_name should not be None here.")
        guaranteed_actual_item_name = actual_item_name

        item_type = item_data.get("type", "unknown")
        item_subtype = item_data.get("subtype", "unknown")
        item_description = item_data.get("description", "")
        item_effects = item_data.get("effects", [])
        item_equip_slot = item_data.get("equip_slot")

        mechanical_outcome_message = ""
        action_performed_type = "use_item_resolved"
        inventory_changed = False
        character_stats_updated = False
        equipment_changed = False

        if item_type == "consumable":
            effects_applied_messages = []
            for effect in item_effects:
                effect_type = effect.get("type", "")
                effect_value = effect.get("value", 0)
                effect_target = effect.get("target", "self")  # Default target is self

                if effect_target == "self":
                    if effect_type == "heal_hp":
                        old_hp = character.stats.current_hp
                        max_hp = character.stats.max_hp
                        character.stats.current_hp = min(old_hp + effect_value, max_hp)
                        healed_amount = character.stats.current_hp - old_hp
                        if healed_amount > 0:
                            effects_applied_messages.append(
                                f"restaurou {healed_amount} pontos de vida"
                            )
                            character_stats_updated = True
                    elif effect_type == "restore_hunger":
                        old_value = character.survival_stats.hunger
                        max_value = 100  # Assumindo 100 como máximo de SurvivalStats
                        character.survival_stats.hunger = min(
                            old_value + effect_value, max_value
                        )
                        restored_amount = character.survival_stats.hunger - old_value
                        if restored_amount > 0:
                            effects_applied_messages.append(
                                f"reduziu a fome em {restored_amount}"
                            )
                            character_stats_updated = True
                    elif effect_type == "restore_thirst":
                        old_value = character.survival_stats.thirst
                        max_value = 100  # Assumindo 100 como máximo de SurvivalStats
                        character.survival_stats.thirst = min(
                            old_value + effect_value, max_value
                        )
                        restored_amount = character.survival_stats.thirst - old_value
                        if restored_amount > 0:
                            effects_applied_messages.append(
                                f"reduziu a sede em {restored_amount}"
                            )
                            character_stats_updated = True
                    # Adicionar outros tipos de efeito de consumo aqui (ex: buff, remove_debuff)
                # Adicionar lógica para efeitos em outros alvos (ex: "target": "other_npc", "target": "enemy") se aplicável

            # Remover item consumido
            character.inventory.pop(item_index)
            inventory_changed = True

            mechanical_outcome_message = f"Você usou {guaranteed_actual_item_name}."
            if effects_applied_messages:
                mechanical_outcome_message += (
                    " Ele " + ", e ".join(effects_applied_messages) + "."
                )
            mechanical_outcome_message += f" {item_description}"  # Incluir descrição do item na mensagem para a IA
            action_performed_type = "use_item_consumable"

        elif item_type in ["weapon", "protection"]:
            # Lógica de equipar
            if not hasattr(character, "equipment") or character.equipment is None:
                character.equipment = {}  # Ensure equipment dict exists

            slot = item_equip_slot  # Use the defined equip_slot
            if not slot:  # Fallback if equip_slot is missing
                slot = (
                    "weapon" if item_type == "weapon" else "body_armor"
                )  # Default slot based on type
                if (
                    item_subtype and "capacete" in item_subtype.lower()
                ):  # Heurística para capacetes
                    slot = "helmet"
                logger.warning(
                    f"Item '{guaranteed_actual_item_name}' missing 'equip_slot'. Using fallback slot: {slot}"
                )

            old_item_name = character.equipment.get(slot)

            # Equipar o novo item (arma ou proteção)
            character.equipment[slot] = (
                guaranteed_actual_item_name  # Store just the name in equipment
            )
            equipment_changed = True

            # Remover o item do inventário
            character.inventory.pop(item_index)
            inventory_changed = True

            # Adicionar o item antigo de volta ao inventário, se houver
            if old_item_name:
                # Precisamos dos dados do item antigo para adicioná-lo de volta como dict ou string
                # Para simplificar, vamos adicionar de volta como string por enquanto.
                # Uma implementação mais robusta adicionaria o objeto/dict completo do item antigo.
                character.inventory.append(old_item_name)
                inventory_changed = True  # Inventário mudou novamente

            mechanical_outcome_message = (
                f"Você equipou {guaranteed_actual_item_name} no slot '{slot}'."
            )
            if old_item_name:
                mechanical_outcome_message += (
                    f" Seu {old_item_name} foi guardado no inventário."
                )
            mechanical_outcome_message += f" {item_description}"  # Incluir descrição do item na mensagem para a IA
            action_performed_type = "use_item_equip"

        elif item_type == "quest":
            # Lógica para itens de quest (ex: ler documento, usar chave em porta)
            # A IA fará a maior parte da narrativa aqui, mas podemos fornecer um resultado mecânico básico.
            mechanical_outcome_message = (
                f"Você examina {guaranteed_actual_item_name}. {item_description}"
            )
            if (
                item_subtype in ["documento", "mapa", "carta"]
                and "content" in item_data
            ):
                mechanical_outcome_message += f"\n\nConteúdo: {item_data['content']}"
            # Itens de quest geralmente não são removidos do inventário automaticamente ao "usar"
            # a menos que a ação seja específica (ex: "entregar chave para NPC X").
            # Por enquanto, não removemos do inventário.
            action_performed_type = "use_item_quest"
            inventory_changed = False  # Inventário não muda por padrão

        elif item_type == "tool":
            # Lógica para usar ferramentas (ex: pé de cabra em porta, kit de arrombamento em cadeado)
            # Isso geralmente envolveria um teste de habilidade/atributo.
            # A IA pode sugerir a rolagem, ou o handler pode resolvê-la.
            # Por enquanto, vamos apenas narrar que você está tentando usar a ferramenta.
            mechanical_outcome_message = (
                f"Você se prepara para usar {guaranteed_actual_item_name}."
            )
            # A IA precisará interpretar o que o jogador está tentando fazer COM a ferramenta (ex: "usar pé de cabra na porta")
            # O GameEngine já passa os 'details' originais para a IA.
            action_performed_type = "use_item_tool"
            inventory_changed = False  # Ferramentas geralmente não são consumidas

        else:
            # Tipo de item desconhecido ou sem handler específico
            mechanical_outcome_message = f"Você tenta usar {guaranteed_actual_item_name}, mas não tem certeza de como ou o que fazer com ele. {item_description}"
            action_performed_type = "use_item_unknown"
            inventory_changed = (
                False  # Não consome item de tipo desconhecido por padrão
            )

        # Retornar resultado mecânico para a IA narrar
        result = {
            "success": True,  # A ação mecânica foi processada (tentativa ou sucesso)
            "message": mechanical_outcome_message,  # Adicionar a mensagem mecânica ao resultado
            "action_performed": action_performed_type,  # Tipo de resultado mecânico
            "inventory_changed": inventory_changed,  # Indica se o inventário precisa ser atualizado no frontend
            "character_stats_updated": character_stats_updated,  # Indica se HP/Stamina/Survival mudaram
            "equipment_changed": equipment_changed,  # Indica se equipamento mudou
            # Incluir dados atualizados do personagem se stats mudaram
            "character_stats": (
                character.to_dict()
                if character_stats_updated or equipment_changed
                else None
            ),
            "inventory": character.inventory if inventory_changed else None,
            "equipment": character.equipment if equipment_changed else None,
        }

        # Se a IA sugerir uma rolagem após a tentativa de usar a ferramenta, o GameEngine lidará com isso.

        return result


class FleeActionHandler(ActionHandler):
    """Handler for 'flee' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        # Lógica mecânica de fuga AQUI. IA narra o resultado.
        if (
            not hasattr(game_state, "combat")
            or not game_state.combat
            or not game_state.combat.get("active")
            or not game_state.combat.get("enemy")
        ):
            # Não está em combate, a IA pode narrar que não há perigo para fugir.
            return {
                "success": True,  # Mecanicamente, a tentativa de fuga foi processada (mas não havia combate)
                "message": "Você tenta fugir, mas não há perigo imediato por perto.",
            }

        enemy_name = game_state.combat["enemy"].name  # Assumindo que enemy tem nome
        dex_modifier = calculate_attribute_modifier(
            character.stats.dexterity
        )  # Corrigido

        # Chance de fuga baseada em Destreza (exemplo simples)
        flee_chance = 0.5 + (dex_modifier * 0.05)  # +5% chance por ponto de modificador
        flee_chance = max(0.1, min(0.9, flee_chance))  # Limitar chance entre 10% e 90%

        roll_result = random.random()  # Rola um número entre 0 e 1

        mechanical_outcome_message = ""
        action_performed_type = "flee_resolved"
        combat_ended = False

        if roll_result < flee_chance:
            # Fuga bem-sucedida
            mechanical_outcome_message = f"Você conseguiu escapar de {enemy_name}!"
            action_performed_type = "flee_success"
            combat_ended = True
            game_state.combat["active"] = False  # Fim do combate
            game_state.combat["enemy"] = None  # Remover inimigo
            # TODO: Mover o personagem para uma localização adjacente segura?
            # Isso exigiria lógica de movimento aqui ou um sinal para o GameEngine.
            # Por enquanto, apenas termina o combate.
        else:
            # Fuga falhou
            mechanical_outcome_message = (
                f"Você tentou fugir, mas {enemy_name} bloqueou seu caminho!"
            )
            action_performed_type = "flee_fail"
            combat_ended = False  # Combate continua
            # TODO: O inimigo pode ter um ataque de oportunidade?

        # Retornar resultado mecânico para a IA narrar
        return {
            "success": True,  # A ação mecânica foi processada
            "action_performed": action_performed_type,  # Tipo de resultado mecânico
            "combat_ended": combat_ended,  # Indica se o combate terminou
            "combat_ongoing": not combat_ended,  # Indica se o combate continua
            # Se o combate terminou, o frontend precisará atualizar a UI.
        }


class RestActionHandler(ActionHandler):
    """Handler for 'rest' action."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        # Lógica mecânica de descanso AQUI. IA narra o resultado.
        if (
            hasattr(game_state, "combat")
            and game_state.combat
            and game_state.combat.get("active")
            and game_state.combat.get("enemy")
        ):
            # Não pode descansar em combate
            return {
                "success": False,  # Mecanicamente, a ação falhou
                "message": "Você não pode descansar durante o combate!",
            }

        # Verificar segurança do local (exemplo simples: 20% chance de interrupção)
        interruption_chance = 0.2
        if random.random() < interruption_chance:
            # Descanso interrompido
            mechanical_outcome_message = "Você tenta encontrar um lugar para descansar, mas os barulhos ao redor e a tensão no ar tornam impossível relaxar."
            action_performed_type = "rest_fail_interrupted"
            rested_successfully = False  # Define rested_successfully
        else:
            # Descanso bem-sucedido
            # Restaurar HP e Vigor (exemplo: 10% do máximo de HP, 20% do máximo de Vigor)
            hp_to_restore = max(1, int(character.stats.max_hp * 0.1))
            stamina_to_restore = max(1, int(character.stats.max_stamina * 0.2))

            old_hp = character.stats.current_hp
            old_stamina = character.stats.current_stamina

            character.stats.current_hp = min(
                character.stats.max_hp, character.stats.current_hp + hp_to_restore
            )
            character.stats.current_stamina = min(
                character.stats.max_stamina,
                character.stats.current_stamina + stamina_to_restore,
            )

            hp_restored_amount = character.stats.current_hp - old_hp
            stamina_restored_amount = character.stats.current_stamina - old_stamina

            mechanical_outcome_message = f"Você encontra um momento de relativa calma para descansar. Você recupera {hp_restored_amount} HP e {stamina_restored_amount} de Vigor."
            action_performed_type = "rest_success"
            rested_successfully = True  # Define rested_successfully

            # TODO: Reduzir fome/sede durante o descanso?

        # Retornar resultado mecânico para a IA narrar
        return {
            "success": True,  # A ação mecânica foi processada (tentativa ou sucesso)
            "message": mechanical_outcome_message,  # Mensagem para a IA narrar
            "action_performed": action_performed_type,  # Tipo de resultado mecânico
            "character_stats_updated": rested_successfully,  # Indica se HP/Stamina mudaram
            "character_stats": (
                character.to_dict() if rested_successfully else None
            ),  # Incluir stats atualizados se houve recuperação
        }


class CustomActionHandler(ActionHandler):
    """
    Handler genérico para ações 'custom' ou 'interpret'.
    Este handler NÃO tenta interpretar a ação mecanicamente.
    Ele apenas retorna os detalhes brutos para que o GameEngine
    os passe para a IA para interpretação e narração (via 'interpret_needed').
    """

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        """
        Retorna os detalhes brutos para que a IA os interprete.
        """
        # Sempre retorna sucesso=True para indicar que a ação foi recebida
        # e deve ser passada para a IA para interpretação.
        return {
            "success": True,
            "action_performed": "interpret_needed",  # Sinaliza para o GameEngine que a IA precisa interpretar
        }


class UnknownActionHandler(ActionHandler):
    """Handler for unknown actions."""

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        # Ação desconhecida. Passa para a IA para ver se ela consegue fazer algo.
        return {
            "success": True,  # Indica que a ação foi recebida
            "action_performed": "unknown_action",  # Sinaliza para a IA que a ação foi desconhecida
        }


class SkillActionHandler(ActionHandler):
    """Handler for 'skill' action."""

    def __init__(self) -> None:
        """Initialize the skill handler."""
        self.skill_manager = SkillManager()

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        """Processa o uso de habilidades do personagem e retorna os resultados mecânicos."""

        # Listar habilidades disponíveis se nenhum detalhe for fornecido
        if not details:
            return self._handle_skill_listing(character)

        return self._handle_skill_usage(details, character, game_state)

    def _handle_skill_listing(self, character: Character) -> Dict[str, Any]:
        """Retorna a lista de habilidades disponíveis do personagem."""
        available_skills = self.skill_manager.get_available_skills(character)
        skill_names = [skill.name for skill in available_skills]
        skill_list = ", ".join(skill_names) if skill_names else "Nenhuma"
        return {
            "success": True,
            "message": f"Habilidades disponíveis: {skill_list}",
        }

    def _handle_skill_usage(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        """Processa o uso de uma habilidade específica."""
        skill_id = details.strip().lower().replace(" ", "_")
        target = self._get_skill_target(game_state)

        result = self.skill_manager.use_skill(character, skill_id, target)

        if not result["success"]:
            return self._build_failure_response(result, details)

        return self._build_success_response(result, character, game_state, target)

    def _get_skill_target(self, game_state: Any) -> Optional[Any]:
        """Determina o alvo padrão para a habilidade baseado no estado do jogo."""
        if not (game_state.combat and game_state.combat.get("active")):
            return None

        return game_state.combat.get("enemy")

    def _build_failure_response(
        self, result: Dict[str, Any], details: str
    ) -> Dict[str, Any]:
        """Constrói resposta para casos de falha no uso de habilidade."""
        return {
            "success": False,
            "message": result.get(
                "message", f"Você tentou usar {details}, mas falhou."
            ),
        }

    def _build_success_response(
        self, result: Dict[str, Any], character: Character, game_state: Any, target: Any
    ) -> Dict[str, Any]:
        """Constrói resposta detalhada para uso bem-sucedido de habilidade."""
        log_entries = self._apply_combat_effects(result, game_state, character)
        self._update_combat_log(game_state, log_entries)

        combat_status = self._get_combat_status(game_state)
        enemy_hp, enemy_max_hp = self._get_enemy_health_info(game_state, target)

        return {
            "success": True,
            "action_performed": result.get("action_performed", "skill_resolved"),
            "combat_log_update": "\n".join(log_entries) if log_entries else None,
            "character_stats_updated": True,
            "character_stats": character.to_dict(),
            "combat_ongoing": combat_status,
            "enemy_hp": enemy_hp,
            "enemy_max_hp": enemy_max_hp,
        }

    def _update_combat_log(self, game_state: Any, log_entries: List[str]):
        """Atualiza o registro de combate se aplicável."""
        if game_state.combat and "log" in game_state.combat:
            game_state.combat["log"].extend(log_entries)

    def _get_combat_status(self, game_state: Any) -> bool:
        """Retorna o status atual do combate."""
        return bool(game_state.combat and game_state.combat.get("active", False))

    def _get_enemy_health_info(
        self, game_state: Any, target: Any
    ) -> Tuple[Optional[int], Optional[int]]:
        """Extrai informações de saúde do inimigo de forma segura."""
        if not (target and self._get_combat_status(game_state)):
            return None, None

        return (
            getattr(target, "current_hp", 0),
            getattr(target, "max_hp", 0),
        )

    @staticmethod
    def _apply_combat_effects(
        result: Dict[str, Any], game_state: Any, character: Character
    ) -> List[str]:
        combat_log_entries = []
        # Verificar se o combate está ativo e se há um inimigo
        if (
            not game_state.combat
            or not game_state.combat.get("active")
            or not game_state.combat.get("enemy")
        ):
            # Se a habilidade teve efeitos que não dependem de combate (ex: buff em si mesmo),
            # a lógica precisaria ser adaptada para aplicar esses efeitos fora do contexto de combate.
            # Por enquanto, esta função foca em efeitos de combate.
            return combat_log_entries

        enemy = game_state.combat["enemy"]  # O inimigo atual

        raw_effects = result.get("raw_effects", [])
        for effect_data in raw_effects:
            target_entity: Optional[Any] = None
            target_name: str = "Desconhecido"  # Traduzido
            effect_target_type = effect_data.get("target")

            if effect_target_type == "enemy":
                target_entity = enemy
                target_name = enemy.name
            elif effect_target_type == "self":
                target_entity = character
                target_name = character.name
            # TODO: Adicionar outros alvos como "other_npc", "area", etc.

            if target_entity:
                effect_type = effect_data.get("type")
                amount = effect_data.get("amount", 0)
                attribute = effect_data.get(
                    "attribute"
                )  # Para efeitos de modificação de atributo
                duration = effect_data.get(
                    "duration"
                )  # Para efeitos de status/buff/debuff

                if effect_type == "damage":
                    # Calcular dano da habilidade (exemplo: rola um dado de 'amount' faces)
                    skill_damage_roll = roll_dice(1, amount, 0)  # Ex: amount=6 para 1d6
                    actual_damage = skill_damage_roll["total"]

                    # Aplicar defesa do alvo
                    target_defense = 0
                    if isinstance(target_entity, Character):
                        target_defense = target_entity.stats.defense
                    elif isinstance(
                        target_entity, Enemy
                    ):  # Assuming Enemy has a defense attribute
                        target_defense = target_entity.defense

                    actual_damage = max(1, actual_damage - target_defense)

                    # Aplicar defesa do alvo
                    if isinstance(target_entity, Character):
                        target_entity.stats.current_hp = max(
                            0, target_entity.stats.current_hp - actual_damage
                        )
                    elif isinstance(target_entity, Enemy):
                        target_entity.current_hp = max(
                            0, target_entity.current_hp - actual_damage
                        )

                    # Atualizar o objeto inimigo no game_state se o alvo for o inimigo
                    if effect_target_type == "enemy":
                        game_state.combat["enemy"] = target_entity

                    combat_log_entries.append(
                        f"{target_name} sofreu {actual_damage} de dano da habilidade!"  # Traduzido
                    )  # Alterado de health para current_hp

                    current_hp_after_damage = (
                        target_entity.stats.current_hp
                        if isinstance(target_entity, Character)
                        else target_entity.current_hp
                    )
                    if effect_target_type == "enemy" and current_hp_after_damage <= 0:
                        combat_log_entries.append(
                            f"{target_name} foi derrotado(a)!"  # Alterado de health para current_hp
                        )  # Traduzido
                        game_state.combat["active"] = False  # Fim do combate
                        game_state.combat["enemy"] = None  # Remover inimigo

                elif effect_type == "heal" and effect_target_type == "self":
                    old_hp = character.stats.current_hp
                    max_hp = character.stats.max_hp
                    heal_amount_from_skill = amount
                    character.stats.current_hp = min(
                        max_hp, old_hp + heal_amount_from_skill
                    )
                    healed_amount = character.stats.current_hp - old_hp
                    if healed_amount > 0:
                        combat_log_entries.append(
                            f"{character.name} curou {healed_amount} HP com a habilidade."  # Traduzido
                        )
                elif effect_type == "restore_stamina" and effect_target_type == "self":
                    old_stamina = character.stats.current_stamina
                    max_stamina = character.stats.max_stamina
                    stamina_restored_amount = amount
                    character.stats.current_stamina = min(
                        max_stamina, old_stamina + stamina_restored_amount
                    )
                    restored_amount = character.stats.current_stamina - old_stamina
                    if restored_amount > 0:
                        combat_log_entries.append(
                            f"{character.name} recuperou {restored_amount} Vigor com a habilidade."  # Traduzido
                        )
                elif effect_type == "status":
                    # Lógica para aplicar status (buffs/debuffs)
                    # Isso exigiria um sistema de status no Character/Enemy
                    combat_log_entries.append(
                        f"{target_name} é afetado(a) por um status da habilidade (Tipo: {effect_data.get('status_type')}, Duração: {duration})."  # Traduzido
                    )
                # TODO: Adicionar outros tipos de efeito (ex: restore_hunger, restore_thirst, modify_attribute)

        return combat_log_entries


class CraftActionHandler(ActionHandler):
    """Handler for 'craft' action."""

    def __init__(self):
        from utils.item_generator import ItemGenerator

        # Padronizar caminho para o diretório de dados
        data_dir_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "data"
        )
        self.item_generator = ItemGenerator(data_dir_path)
        self.skill_manager = SkillManager()  # Para verificar requisitos de habilidade

    def handle(
        self, details: str, character: Character, game_state: Any
    ) -> Dict[str, Any]:
        # Lógica mecânica de criação AQUI. IA narra o resultado.
        recipe_id_query = details.strip().lower() if isinstance(details, str) else ""

        if not recipe_id_query:
            # Se nenhum detalhe foi fornecido, listar receitas conhecidas
            available_crafts = []
            # Precisamos de uma forma de saber quais receitas o personagem conhece.
            # Por enquanto, listamos todas as receitas que o personagem tem habilidade para tentar.
            for recipe_id, recipe_data in CRAFTING_RECIPES.items():
                skill_req = recipe_data.get("skill_required")
                has_skill = True
                if skill_req:
                    skill_id_req, skill_level_req = (
                        skill_req  # Assumindo formato (id, level)
                    )
                    # Verificar se o personagem tem a habilidade necessária
                    # O sistema de habilidades precisaria rastrear habilidades aprendidas pelo personagem.
                    # Por enquanto, vamos verificar se a habilidade ID está na lista character.skills
                    if skill_id_req not in character.skills:
                        has_skill = False
                    # TODO: Verificar o nível da habilidade se necessário

                if has_skill:
                    available_crafts.append(
                        f"{recipe_data.get('name', recipe_id)} (ID: {recipe_id})"
                    )

            if not available_crafts:
                return {
                    "success": True,  # Mecanicamente, você conseguiu verificar, mas não há receitas
                    "message": "Você não conhece nenhuma receita de criação ou não possui as habilidades necessárias para as conhecidas.",  # Traduzido
                }
            return {
                "success": True,  # Mecanicamente, você conseguiu listar
                "message": "Você pode tentar criar: "
                + ", ".join(available_crafts)
                + ". Use 'craft [ID da receita]'.",  # Traduzido
                "action_performed": "craft_list",
            }

        # Tentar criar uma receita específica
        recipe = CRAFTING_RECIPES.get(recipe_id_query)

        if not recipe:
            return {
                "message": f"Receita com ID '{recipe_id_query}' não encontrada.",  # Adicionada mensagem para clareza
                "success": False,  # Mecanicamente, a receita não existe
                "action_performed": "craft_failed_recipe_not_found",
            }

        # Verificar requisito de habilidade
        skill_req = recipe.get("skill_required")
        if skill_req:
            skill_id_req, skill_level_req = skill_req
            if skill_id_req not in character.skills:
                # Tentar obter o nome da habilidade para a mensagem
                skill_obj = self.skill_manager.available_skills.get(skill_id_req)
                skill_display_name = skill_obj.name if skill_obj else skill_id_req
                recipe_name = recipe.get("name", recipe_id_query)
                return {
                    "success": False,  # Mecanicamente, falta habilidade
                    "message": f"Você não tem a habilidade '{skill_display_name}' (nível {skill_level_req}) necessária para criar '{recipe_name}'.",  # Adicionada mensagem de erro
                    "action_performed": "craft_failed_skill_missing",
                }
            # TODO: Adicionar verificação de nível de habilidade e talvez um teste de habilidade aqui

        # Verificar componentes necessários no inventário
        required_components = recipe.get("components", {})
        inventory_copy = character.inventory[
            :
        ]  # Trabalhar em uma cópia para não modificar antes de confirmar
        missing_components = []
        components_to_remove_indices: Dict[str, List[int]] = (
            {}
        )  # {component_name: [indices_no_inventario]}

        for comp_id_ref, quantity_needed in required_components.items():
            found_quantity = 0
            indices_for_this_component = []
            # Procurar o componente no inventário
            # Unified item name extraction
            for i, inv_item_obj in enumerate(inventory_copy):
                item_name = ""
                if isinstance(inv_item_obj, str):
                    item_name = inv_item_obj.lower()
                elif isinstance(inv_item_obj, dict) and "name" in inv_item_obj:
                    item_name = inv_item_obj.get("name", "").lower()

                # Comparar pelo ID de referência do componente (lowercase)
                if (
                    item_name == comp_id_ref.lower()
                ):  # comp_id_ref já é o nome/ID do item da receita
                    indices_for_this_component.append(i)
                    found_quantity += 1
                    if found_quantity >= quantity_needed:
                        break  # Já encontramos o suficiente deste componente

            if found_quantity < quantity_needed:
                missing_components.append(
                    f"{comp_id_ref} (precisa de {quantity_needed}, tem {found_quantity})"  # Traduzido
                )
            else:
                # Guardar os índices dos itens que serão removidos para este componente
                # Ordenar reversamente para remover sem bagunçar os índices restantes
                components_to_remove_indices[comp_id_ref] = sorted(
                    indices_for_this_component[:quantity_needed], reverse=True
                )

        if missing_components:
            return {
                "success": False,  # Mecanicamente, faltam componentes
                "message": "Componentes faltando: "
                + ", ".join(missing_components),  # Mensagem para a IA narrar a falha
            }

        # Se chegou aqui, tem todos os componentes. Remover do inventário.
        # Remover os itens do inventário original (character.inventory)
        # É importante remover os índices maiores primeiro para não invalidar os menores.
        all_indices_to_remove = sorted(
            [
                idx
                for indices in components_to_remove_indices.values()
                for idx in indices
            ],
            reverse=True,
        )
        for index_to_remove in all_indices_to_remove:
            if 0 <= index_to_remove < len(character.inventory):
                character.inventory.pop(index_to_remove)
            else:
                logger.error(
                    f"Erro ao remover item do inventário para criação. Índice inválido: {index_to_remove}"
                )

        # Adicionar o item criado ao inventário
        output_item_name = recipe.get(
            "name", recipe_id_query
        )  # Usar nome da receita como fallback
        output_quantity = recipe.get("output_quantity", 1)

        for _ in range(output_quantity):
            # Modified item creation with error handling (integrating user suggestion)
            try:
                crafted_item_data = self.item_generator.get_item_by_name(
                    output_item_name
                )
                if not crafted_item_data:
                    # Se o item_generator não encontrar o item, consideramos uma falha crítica para esta receita.
                    # A mensagem de log aqui é mais específica para depuração.
                    logger.error(
                        f"ItemGenerator não conseguiu encontrar/gerar dados para o item '{output_item_name}' durante a criação."
                    )
                    raise ValueError(
                        f"Definição do item '{output_item_name}' não encontrada pelo gerador."
                    )

                # Add structured data to inventory
                character.inventory.append(crafted_item_data)
            except Exception as e:
                # Captura o ValueError acima ou qualquer outra exceção durante get_item_by_name ou append.
                logger.error(
                    f"Erro crítico durante a criação ou adição do item '{output_item_name}': {str(e)}",
                    exc_info=True,
                )
                return {  # Retorna falha para toda a ação de craft
                    "success": False,
                    "message": "A criação falhou devido a um erro inesperado no sistema de itens.",
                    "inventory_changed": True,  # Componentes já foram removidos
                    "inventory": character.inventory,
                }

        # Se o loop completar, todos os itens foram adicionados com sucesso.
        return {
            "success": True,  # Mecanicamente, a criação foi bem-sucedida
            "action_performed": "craft_success",
            "inventory_changed": True,  # Inventário mudou
            "inventory": character.inventory,  # Enviar inventário atualizado
        }


class InterpretActionHandler(ActionHandler):
    """
    A simple handler for 'interpret' actions.
    Its main purpose is to pass the raw details to the AI for interpretation.
    """

    def handle(
        self, details: str, character: "Character", game_state: Any
    ) -> Dict[str, Any]:
        """Passa os detalhes para a IA interpretar."""
        # Sempre retorna sucesso=True para indicar que a ação foi recebida
        # Sempre retorna sucesso=True para indicar que a ação foi recebida
        # e deve ser passada para a IA para interpretação.
        return {
            "success": True,
            "action_performed": "interpret_needed",  # Sinaliza para o GameEngine que a IA precisa interpretar
            # A 'message' para a IA será os 'details' originais passados pelo jogador.
            "skip_ai_narration": False,  # Queremos a narração da IA
        }


# Cache para instâncias de handlers
_action_handler_instances: Dict[str, ActionHandler] = {}


# Action handler factory
def get_action_handler(action: str) -> ActionHandler:
    """
    Get the appropriate action handler for the given action.

    Args:
        action: Action name

    Returns:
        Handler for the action
    """
    global _action_handler_instances

    if action in _action_handler_instances:
        return _action_handler_instances[action]

    handler: ActionHandler
    if action == "move":
        handler = MoveActionHandler()
    elif action == "look":
        handler = LookActionHandler()
    elif action == "talk":
        handler = TalkActionHandler()
    elif action == "search":
        handler = SearchActionHandler()
    elif action == "attack":
        handler = AttackActionHandler()
    elif action == "use_item":
        handler = UseItemActionHandler()
    elif action == "flee":
        handler = FleeActionHandler()
    elif action == "rest":
        handler = RestActionHandler()
    elif action == "skill":
        handler = SkillActionHandler()
    elif action == "craft":
        handler = CraftActionHandler()
    elif action == "interpret":
        handler = InterpretActionHandler()
    else:  # Fallback para CustomActionHandler para ações desconhecidas ou 'custom'
        handler = (
            CustomActionHandler()
        )  # Explicitly use CustomActionHandler for unknown/custom

    _action_handler_instances[action] = handler
    return handler
