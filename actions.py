"""
Action handlers for the game engine.

This module contains the action handlers for the game engine, implementing
the Strategy pattern for different action types.
"""

import logging
import random
from typing import Dict, Any, Union, Optional, List
from abc import ABC, abstractmethod
import json
import os
from models import Character, Enemy
from prompt_manager import PromptManager
from groq_client import GroqClient

logger = logging.getLogger(__name__)


class ActionHandler(ABC):
    """Base class for action handlers using the Strategy pattern."""
    
    @abstractmethod
    def handle(self, details: str, character: Character, game_state: Any) -> Dict[str, Any]:
        """
        Handle an action.
        
        Args:
            details: Action details
            character: Character performing the action
            game_state: Current game state
            
        Returns:
            Action result dictionary
        """
        pass
        
    def get_npc_details(self, npc_name: str, character: Character, game_state: Any) -> Dict[str, Any]:
        """
        Generate detailed information about an NPC when interacted with.
        
        Args:
            npc_name: Name of the NPC to get details for
            character: Character interacting with the NPC
            game_state: Current game state
            
        Returns:
            Dictionary with NPC details
        """
        # Este método será chamado apenas quando o jogador interagir com um NPC específico
        # Gera detalhes como raça, classe, nível, história, missões, etc.
        prompt = f"""
        Generate detailed information for NPC named '{npc_name}' in location '{game_state.current_location}'.
        Include: race, class/profession, level (if applicable), personality, background story, 
        possible quests, items they might have, and knowledge they possess.
        
        Return as JSON with fields: race, profession, level, personality, background, quests, items, knowledge.
        """
        
        # Aqui você usaria o cliente GroqClient para gerar os detalhes
        # Por enquanto, retornamos um exemplo
        return {
            "name": npc_name,
            "race": "Human",
            "profession": "Merchant",
            "level": 5,
            "personality": "Friendly but shrewd",
            "background": "Former adventurer who settled down after an injury",
            "quests": ["Find lost shipment", "Deliver message to neighboring town"],
            "items": ["Health Potion", "Map of the region"],
            "knowledge": ["Local rumors", "Trade routes", "Monster sightings"]
        }
    
    def ai_response(self, action: str, details: str, character: Character, game_state: Any) -> Dict[str, Any]:
        # Importa os geradores
        from item_generator import ItemGenerator
        from encounter_generator import EncounterGenerator
        
        # Inicializa os geradores
        item_generator = ItemGenerator(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))
        encounter_generator = EncounterGenerator()
        
        # Verifica se deve gerar um encontro aleatório
        location_type = getattr(game_state, 'current_location', 'forest')
        if random.random() < 0.1:  # 10% de chance de encontro aleatório
            if encounter_generator.should_trigger_random_encounter(location_type):
                encounter = encounter_generator.generate_random_encounter(character.level, location_type)
                
                # Adiciona o encontro ao resultado
                if encounter["type"] == "combat":
                    # Cria um inimigo baseado no encontro
                    from models import Enemy
                    enemy = Enemy(
                        name=encounter["enemy_type"],
                        level=encounter["enemy_level"],
                        max_hp=random.randint(20, 50),
                        current_hp=random.randint(20, 50),
                        attack_damage=(random.randint(3, 8), random.randint(9, 15)),
                        defense=random.randint(3, 10),
                        description=encounter["description"]
                    )
                    
                    # Inicia o combate
                    if not hasattr(game_state, 'combat') or not game_state.combat:
                        game_state.combat = {
                            "enemy": enemy,
                            "round": 1,
                            "log": [f"Encontro aleatório: {encounter['description']}"]
                        }
                        
                        return {
                            "success": True,
                            "message": encounter["description"],
                            "combat": True
                        }
                else:
                    # Para outros tipos de encontro, apenas retorna a descrição
                    return {
                        "success": True,
                        "message": encounter["description"]
                    }
        
        # Verifica se é uma falha crítica (5% de chance)
        if random.random() < 0.05:
            # Determina o tipo de ação
            action_type = "general"
            if action == "attack":
                action_type = "attack"
            elif action in ["look", "search", "move"]:
                action_type = "skill"
            elif action == "custom" and "magia" in details.lower() or "spell" in details.lower():
                action_type = "spell"
            
            # Gera a falha crítica
            failure = encounter_generator.generate_critical_failure(action_type, character.level)
            
            # Aplica os efeitos da falha
            if failure["effect"]["damage"] > 0:
                character.current_hp = max(1, character.current_hp - failure["effect"]["damage"])
            
            return {
                "success": False,
                "message": failure["description"]
            }
        
        # Comportamento normal - gera resposta da IA
        prompt = PromptManager.create_action_prompt(
            action,
            details,
            character,
            game_state,
            lambda c, attr, default=None: getattr(c, attr, default)
        )
        ai = GroqClient()
        ai_result = ai.generate_response(prompt)
        
        # Tenta garantir que o resultado seja um dicionário
        if isinstance(ai_result, dict):
            result = ai_result
        else:
            try:
                # Corrige aspas simples para duplas, se necessário
                if isinstance(ai_result, str):
                    ai_result = ai_result.replace("'", '"')
                result = json.loads(ai_result)
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Erro ao interpretar resposta da IA: {e}\nResposta: {ai_result}"
                }
        
        # Garantir que a mensagem não seja um JSON bruto
        if "message" in result and isinstance(result["message"], str):
            # Verifica se a mensagem parece ser um JSON
            if result["message"].startswith("{") and "}" in result["message"]:
                try:
                    # Tenta encontrar o JSON válido na string
                    json_start = result["message"].find("{")
                    json_end = result["message"].rfind("}") + 1
                    json_str = result["message"][json_start:json_end]
                    
                    message_json = json.loads(json_str)
                    if isinstance(message_json, dict) and "message" in message_json:
                        # Substitui a mensagem pelo campo message do JSON
                        result["message"] = message_json["message"]
                except:
                    # Se falhar ao analisar, mantém a mensagem original
                    pass
        
        # Verificar se a mensagem está incompleta (termina sem pontuação)
        if "message" in result and isinstance(result["message"], str):
            message = result["message"].strip()
            if message and not message[-1] in ['.', '!', '?', '"', "'", ')', ']', '}']:
                # Adiciona um ponto final para completar a frase
                result["message"] = message + "."
        
        # Verifica se há itens para adicionar ao inventário
        if action in ["search", "look"] and result.get("success", False):
            # 30% de chance de encontrar um item
            if random.random() < 0.3:
                # Gera um item aleatório
                item = item_generator.generate_random_item(character.level)
                
                # Adiciona o item ao inventário
                if hasattr(character, 'inventory'):
                    character.inventory.append(item["name"])
                    
                    # Adiciona informação sobre o item encontrado à mensagem
                    result["message"] += f" Você encontrou {item['name']}! {item['description']}"
        
        return result
        
        # Verificar se há informações de quest na resposta
        if action == "talk" and "potential_quest" in result:
            # Inicializa a lista de quests se não existir
            if not hasattr(game_state, 'quests'):
                game_state.quests = []
            
            # Extrai informações da quest
            quest_info = result["potential_quest"]
            
            # Cria um objeto de quest
            new_quest = {
                "name": quest_info.get("titulo", "Nova Missão"),
                "description": quest_info.get("descricao", ""),
                "giver": result.get("npc_name", "NPC"),
                "reward": quest_info.get("recompensa", ""),
                "progress": 0,
                "tasks": []
            }
            
            # Gera tarefas para a quest baseadas na descrição
            if "descricao" in quest_info or "description" in quest_info:
                desc = quest_info.get("descricao", quest_info.get("description", ""))
                # Divide a descrição em possíveis tarefas
                sentences = desc.split(". ")
                for i, sentence in enumerate(sentences[:3]):  # Limita a 3 tarefas
                    if sentence and len(sentence) > 10:  # Ignora frases muito curtas
                        new_quest["tasks"].append({
                            "description": sentence + ("." if not sentence.endswith(".") else ""),
                            "completed": False
                        })
            
            # Adiciona a quest à lista de quests do jogador
            game_state.quests.append(new_quest)
        # Atualiza o game_state com os campos relevantes do resultado da IA
        if 'description' in result:
            game_state.scene_description = result['description']
        if 'npcs' in result:
            # Simplificado: apenas armazena os nomes dos NPCs como strings
            game_state.npcs_present = [str(npc) for npc in result['npcs']]
        if 'events' in result:
            # Simplificado: apenas armazena as descrições dos eventos como strings
            game_state.events = [str(event) for event in result['events']]
        if 'new_location' in result:
            game_state.current_location = result['new_location']
            
            # Gera um ID único para o local se não existir no mapa do mundo
            if hasattr(game_state, 'world_map'):
                location_found = False
                for loc_id, loc_info in game_state.world_map.items():
                    if loc_info.get('name') == result['new_location']:
                        game_state.location_id = loc_id
                        game_state.coordinates = loc_info.get('coordinates', {'x': 0, 'y': 0, 'z': 0})
                        location_found = True
                        break
                
                if not location_found:
                    # Cria um novo ID para o local
                    new_id = result['new_location'].lower().replace(' ', '_')
                    
                    # Gera coordenadas próximas ao local atual
                    current_coords = game_state.coordinates if hasattr(game_state, 'coordinates') else {'x': 0, 'y': 0, 'z': 0}
                    new_coords = {
                        'x': current_coords.get('x', 0) + random.randint(-1, 1),
                        'y': current_coords.get('y', 0) + random.randint(-1, 1),
                        'z': current_coords.get('z', 0)
                    }
                    
                    # Adiciona o novo local ao mapa do mundo
                    game_state.world_map[new_id] = {
                        'name': result['new_location'],
                        'coordinates': new_coords,
                        'connections': {}  # Será preenchido posteriormente
                    }
                    
                    # Atualiza o local atual
                    game_state.location_id = new_id
                    game_state.coordinates = new_coords
        return result


class MoveActionHandler(ActionHandler):
    """Handler for 'move' action."""
    
    def handle(self, details: str, character: Character, game_state: Any) -> Dict[str, Any]:
        # Importa o gerador de mundo
        from world_generator import WorldGenerator
        
        # Inicializa o gerador de mundo
        world_generator = WorldGenerator(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))
        
        # Verifica se o destino está no mapa do mundo
        destination = details.strip().lower()
        current_location_id = game_state.location_id
        
        # Direções padrão
        directions = ["norte", "sul", "leste", "oeste", "north", "south", "east", "west"]
        
        # Mapeia direções em inglês para português
        direction_mapping = {
            "north": "norte",
            "south": "sul",
            "east": "leste",
            "west": "oeste"
        }
        
        # Normaliza a direção
        normalized_direction = None
        for d in directions:
            if d in destination:
                normalized_direction = d
                if d in direction_mapping:
                    normalized_direction = direction_mapping[d]
                break
        
        # Verifica se o local atual tem conexões definidas no mapa do mundo
        if hasattr(game_state, 'world_map') and "locations" in game_state.world_map:
            current_location = game_state.world_map["locations"].get(current_location_id, {})
            connections = current_location.get('connections', {})
            
            # Procura por uma conexão que corresponda à direção ou ao nome do local
            next_location_id = None
            
            # Primeiro, verifica conexões existentes
            for direction, loc_id in connections.items():
                if (direction.lower() == normalized_direction or 
                    (normalized_direction is None and 
                     loc_id in game_state.world_map["locations"] and 
                     game_state.world_map["locations"][loc_id]['name'].lower() in destination)):
                    next_location_id = loc_id
                    break
            
            # Se não encontrou uma conexão existente, mas temos uma direção, gera um novo local
            if next_location_id is None and normalized_direction:
                # Gera um novo local adjacente
                new_location = world_generator.generate_adjacent_location(
                    current_location_id, 
                    normalized_direction, 
                    game_state.world_map
                )
                
                # Adiciona o novo local ao mapa do mundo
                game_state.world_map["locations"][new_location["id"]] = new_location
                
                # Atualiza as conexões do local atual
                if "connections" not in current_location:
                    current_location["connections"] = {}
                current_location["connections"][normalized_direction] = new_location["id"]
                
                # Salva o mapa do mundo atualizado
                world_generator.save_world(game_state.world_map)
                
                next_location_id = new_location["id"]
            
            # Se encontrou ou gerou uma conexão válida
            if next_location_id and next_location_id in game_state.world_map["locations"]:
                # Atualiza a localização atual
                game_state.location_id = next_location_id
                next_location = game_state.world_map["locations"][next_location_id]
                game_state.current_location = next_location['name']
                game_state.coordinates = next_location['coordinates'].copy()
                
                # Verifica se o local já foi visitado antes
                if hasattr(game_state, 'visited_locations') and next_location_id in game_state.visited_locations:
                    # Recupera informações do local já visitado
                    visited_info = game_state.visited_locations[next_location_id]
                    
                    # Atualiza a entrada de local visitado
                    visited_info['last_visited'] = 'revisited'
                    
                    # Usa a descrição e NPCs anteriores, mas permite que a IA adicione novos eventos
                    game_state.scene_description = visited_info['description']
                    game_state.npcs_present = visited_info['npcs_seen']
                    
                    # Gera novos eventos aleatórios ocasionalmente
                    if random.random() < 0.3:  # 30% de chance
                        new_events = world_generator.generate_events(
                            next_location['name'], 
                            next_location.get('type', 'unknown')
                        )
                        game_state.events = new_events
                    else:
                        game_state.events = visited_info.get('events_seen', [])
                    
                    # Registra a visita
                    game_state.visited_locations[next_location_id] = visited_info
                    
                    return {
                        "success": True,
                        "message": f"Você se move para {next_location['name']}. {next_location['description']}",
                        "new_location": next_location['name'],
                        "description": next_location['description'],
                        "npcs": game_state.npcs_present,
                        "events": game_state.events
                    }
                else:
                    # Primeira visita a este local
                    game_state.scene_description = next_location['description']
                    game_state.npcs_present = next_location['npcs']
                    game_state.events = next_location['events']
                    
                    # Marca o local como visitado
                    next_location["visited"] = True
                    
                    # Registra o local como visitado
                    if hasattr(game_state, 'visited_locations'):
                        game_state.visited_locations[next_location_id] = {
                            'name': game_state.current_location,
                            'last_visited': 'first_time',
                            'description': game_state.scene_description,
                            'npcs_seen': game_state.npcs_present.copy(),
                            'events_seen': game_state.events.copy()
                        }
                    
                    return {
                        "success": True,
                        "message": f"Você chega a {next_location['name']}. {next_location['description']}",
                        "new_location": next_location['name'],
                        "description": next_location['description'],
                        "npcs": game_state.npcs_present,
                        "events": game_state.events
                    }
        
        # Se não encontrou no mapa ou não tem mapa, usa o comportamento padrão
        return self.ai_response("move", details, character, game_state)


class LookActionHandler(ActionHandler):
    """Handler for 'look' action."""
    
    def handle(self, details: str, character: Character, game_state: Any) -> Dict[str, Any]:
        # Se o jogador está olhando para um NPC específico
        if details and details.strip():
            # Verifica se o jogador está olhando para um NPC
            target = details.strip().lower()
            
            # Verifica se o alvo é um NPC presente
            if game_state.npcs_present and any(npc.lower() == target for npc in game_state.npcs_present):
                # Gera detalhes do NPC apenas quando o jogador olha para ele
                npc_name = next(npc for npc in game_state.npcs_present if npc.lower() == target)
                npc_details = self.get_npc_details(npc_name, character, game_state)
                
                # Cria uma resposta detalhada sobre o NPC
                return {
                    "success": True,
                    "message": f"Você observa {npc_name} com atenção. {npc_details.get('race', 'Humanóide')} que trabalha como {npc_details.get('profession', 'desconhecido')}. " +
                              f"{npc_name} parece {npc_details.get('personality', 'comum')}. " +
                              f"Pela aparência e postura, você estima que seja de nível {npc_details.get('level', '?')}."
                }
        
        # Comportamento padrão para olhar o ambiente
        return self.ai_response("look", details, character, game_state)


class TalkActionHandler(ActionHandler):
    """Handler for 'talk' action."""
    
    def handle(self, details: str, character: Character, game_state: Any) -> Dict[str, Any]:
        # Se o jogador especificou um NPC para conversar
        if details and details.strip():
            # Verifica se o NPC está presente no local
            npc_name = details.strip()
            if game_state.npcs_present and any(npc.lower() == npc_name.lower() for npc in game_state.npcs_present):
                # Encontra o nome exato do NPC (preservando maiúsculas/minúsculas)
                npc_name = next(npc for npc in game_state.npcs_present if npc.lower() == npc_name.lower())
                
                # Verifica se já conhece este NPC
                if hasattr(game_state, 'known_npcs') and npc_name in game_state.known_npcs:
                    # Recupera informações do NPC já conhecido
                    npc_details = game_state.known_npcs[npc_name]
                    
                    # Atualiza o contador de interações
                    npc_details['interactions'] = npc_details.get('interactions', 0) + 1
                    
                    # Usa os detalhes para enriquecer a resposta da IA
                    result = self.ai_response("talk", details, character, game_state)
                    
                    # Adiciona informações do NPC à resposta com base no nível de familiaridade
                    if "message" in result:
                        if npc_details['interactions'] <= 2:
                            result["message"] += f"\n\nVocê reconhece {npc_name}, um(a) {npc_details['race']} {npc_details['profession']}."
                        else:
                            # Mais detalhes para NPCs com quem o jogador interagiu várias vezes
                            result["message"] += f"\n\n{npc_name} sorri ao ver um rosto familiar. Como {npc_details['profession']} experiente, {npc_name} tem muitas histórias para contar."
                            
                            # Adiciona uma dica sobre missões se o NPC tiver alguma
                            if npc_details.get("quests") and random.random() < 0.7:  # 70% de chance
                                result["message"] += f" {npc_name} menciona que precisa de ajuda com '{random.choice(npc_details['quests'])}'."
                    
                    # Atualiza o registro do NPC
                    game_state.known_npcs[npc_name] = npc_details
                    
                    return result
                else:
                    # Primeira interação com este NPC
                    npc_details = self.get_npc_details(npc_name, character, game_state)
                    
                    # Usa os detalhes para enriquecer a resposta da IA
                    result = self.ai_response("talk", details, character, game_state)
                    
                    # Adiciona informações do NPC à resposta
                    if "message" in result:
                        result["message"] += f"\n\nVocê nota que {npc_name} é um(a) {npc_details['race']} {npc_details['profession']}."
                        
                        # Adiciona uma dica sobre o conhecimento ou missões do NPC
                        if npc_details.get("knowledge"):
                            result["message"] += f" Parece que {npc_name} sabe sobre {', '.join(npc_details['knowledge'][:2])}."
                        
                        if npc_details.get("quests"):
                            result["message"] += f" {npc_name} menciona algo sobre '{npc_details['quests'][0]}'."
                    
                    # Registra o NPC como conhecido
                    if hasattr(game_state, 'known_npcs'):
                        npc_details['interactions'] = 1
                        game_state.known_npcs[npc_name] = npc_details
                    
                    return result
        
        # Comportamento padrão se nenhum NPC específico for mencionado
        return self.ai_response("talk", details, character, game_state)


class SearchActionHandler(ActionHandler):
    """Handler for 'search' action."""
    
    def handle(self, details: str, character: Character, game_state: Any) -> Dict[str, Any]:
        # Verifica se o jogador está procurando por missões
# Verifica se o jogador está procurando por missões
        if "missão" in details.lower() or "missao" in details.lower() or "quest" in details.lower():
            # Verifica se há NPCs presentes que podem oferecer missões
            if not hasattr(game_state, 'npcs_present') or not game_state.npcs_present:
                return {
                    "success": False,
                    "message": "Não há ninguém por perto que possa oferecer missões no momento."
                }
            
            # Inicializa a lista de quests se não existir
            if not hasattr(game_state, 'quests'):
                game_state.quests = []
            
            # Escolhe um NPC aleatório para oferecer uma missão
            quest_giver = random.choice(game_state.npcs_present)
                
            # Gera uma missão aleatória usando o quest_generator
            from utils import generate_quest
            new_quest = generate_quest(
                location=game_state.current_location,
                difficulty=character.level,
                lang=getattr(game_state, 'language', 'pt-br')
            )
                
            # Adiciona informações do NPC à missão
            new_quest['giver'] = quest_giver
            new_quest['location'] = game_state.current_location
                
            # Adiciona a missão à lista de missões do jogador
            game_state.quests.append(new_quest)
                
            # Retorna informações sobre a missão
            return {
                "success": True,
                "message": f"{quest_giver} oferece uma nova missão: {new_quest['name']}. {new_quest['description']} Recompensa: {new_quest['reward_gold']} moedas de ouro."
            }
        
        # Comportamento padrão para outras buscas
        result = self.ai_response("search", details, character, game_state)
        
        # Registra os resultados da busca no local atual
        if hasattr(game_state, 'visited_locations') and game_state.location_id in game_state.visited_locations:
            location_info = game_state.visited_locations[game_state.location_id]
            if 'search_results' not in location_info:
                location_info['search_results'] = []
            
            # Adiciona o resultado da busca ao histórico
            location_info['search_results'].append({
                'query': details,
                'result': result.get('message', '')
            })
        
        return result


class AttackActionHandler(ActionHandler):
    """Handler for 'attack' action."""
    
    def handle(self, details: str, character: Character, game_state: Any) -> Dict[str, Any]:
        # Verifica se o jogador está tentando atacar um NPC específico
        if details and details.strip():
            target = details.strip().lower()
            
            # Verifica se o alvo é um NPC presente
            if game_state.npcs_present and any(npc.lower() == target for npc in game_state.npcs_present):
                # Encontra o nome exato do NPC (preservando maiúsculas/minúsculas)
                npc_name = next(npc for npc in game_state.npcs_present if npc.lower() == target)
                
                # Cria um inimigo baseado no NPC
                enemy = Enemy(
                    name=npc_name,
                    level=random.randint(character.level, character.level + 2),
                    max_hp=random.randint(20, 50),
                    current_hp=random.randint(20, 50),
                    attack_damage=(random.randint(3, 8), random.randint(9, 15)),
                    defense=random.randint(3, 10),
                    description=f"Um {npc_name} hostil que você decidiu atacar."
                )
                
                # Inicia o combate
                if not hasattr(game_state, 'combat') or not game_state.combat:
                    game_state.combat = {
                        "enemy": enemy,
                        "round": 1,
                        "log": [f"Você iniciou combate com {npc_name}!"]
                    }
                    
                    return {
                        "success": True,
                        "message": f"Você atacou {npc_name} e iniciou um combate! Prepare-se para lutar!",
                        "combat": True
                    }
            
            # Se o alvo não for um NPC presente, tenta iniciar combate com um inimigo aleatório
            enemy_types = ["Bandido", "Lobo", "Goblin", "Esqueleto", "Zumbi", "Ladrão", "Mercenário"]
            enemy_name = random.choice(enemy_types)
            
            enemy = Enemy(
                name=enemy_name,
                level=random.randint(character.level, character.level + 2),
                max_hp=random.randint(20, 50),
                current_hp=random.randint(20, 50),
                attack_damage=(random.randint(3, 8), random.randint(9, 15)),
                defense=random.randint(3, 10),
                description=f"Um {enemy_name} hostil que apareceu de repente."
            )
            
            # Inicia o combate
            if not hasattr(game_state, 'combat') or not game_state.combat:
                game_state.combat = {
                    "enemy": enemy,
                    "round": 1,
                    "log": [f"Um {enemy_name} apareceu e você o atacou!"]
                }
                
                return {
                    "success": True,
                    "message": f"Você procurou por inimigos e encontrou um {enemy_name}! Combate iniciado!",
                    "combat": True
                }
        
        # Comportamento padrão se nenhum alvo específico for mencionado
        return self.ai_response("attack", details, character, game_state)


class UseItemActionHandler(ActionHandler):
    """Handler for 'use_item' action."""
    
    def handle(self, details: str, character: Character, game_state: Any) -> Dict[str, Any]:
        # Importa o gerador de itens
        from item_generator import ItemGenerator
        
        # Inicializa o gerador de itens
        item_generator = ItemGenerator(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))
        
        if not details or not hasattr(character, 'inventory') or not character.inventory:
            return {
                "success": False,
                "message": "Você não tem esse item no seu inventário."
            }
        
        # Normaliza o nome do item para comparação
        item_name = details.strip()
        
        # Verifica se o item está no inventário
        item_found = False
        item_index = -1
        item_data = None
        
        # Procura pelo item exato ou por correspondência parcial
        for i, inv_item in enumerate(character.inventory):
            if isinstance(inv_item, str) and (inv_item.lower() == item_name.lower() or inv_item.lower() in item_name.lower()):
                item_found = True
                item_index = i
                item_name = inv_item  # Usa o nome exato do item do inventário
                
                # Verifica se o item existe no banco de dados
                item_data = item_generator.get_item_by_name(item_name)
                break
            elif isinstance(inv_item, dict) and inv_item.get('name', '').lower() == item_name.lower():
                item_found = True
                item_index = i
                item_name = inv_item.get('name')
                item_data = inv_item
                break
        
        if not item_found:
            return {
                "success": False,
                "message": f"Você não tem '{item_name}' no seu inventário."
            }
        
        # Se encontrou o item no banco de dados, usa seus atributos
        if item_data:
            item_type = item_data.get("type", "")
            item_subtype = item_data.get("subtype", "")
            item_description = item_data.get("description", "")
            
            # Lógica para diferentes tipos de itens
            if item_type == "weapon":
                # Equipar arma
                if not hasattr(character, 'equipment') or character.equipment is None:
                    character.equipment = {}
                
                # Guarda o item equipado anteriormente, se houver
                old_item = character.equipment.get("weapon")
                
                # Equipa o novo item
                character.equipment["weapon"] = item_name
                
                # Se havia um item equipado anteriormente, coloca de volta no inventário
                if old_item:
                    character.inventory.append(old_item)
                
                # Remove o item do inventário
                character.inventory.pop(item_index)
                
                # Adiciona bônus de atributos
                damage_info = ""
                if "damage" in item_data:
                    min_damage, max_damage = item_data["damage"]
                    damage_info = f" Dano: {min_damage}-{max_damage}."
                
                return {
                    "success": True,
                    "message": f"Você equipou {item_name}. {damage_info} {item_description} {f'Seu {old_item} foi guardado no inventário.' if old_item else ''}"
                }
                
            elif item_type == "armor":
                # Equipar armadura
                if not hasattr(character, 'equipment') or character.equipment is None:
                    character.equipment = {}
                
                # Determina o slot com base no subtipo
                slot = "armor"
                if item_subtype == "helmet":
                    slot = "helmet"
                elif item_subtype == "shield":
                    slot = "shield"
                elif item_subtype in ["boots", "gauntlets"]:
                    slot = item_subtype
                
                # Guarda o item equipado anteriormente, se houver
                old_item = character.equipment.get(slot)
                
                # Equipa o novo item
                character.equipment[slot] = item_name
                
                # Se havia um item equipado anteriormente, coloca de volta no inventário
                if old_item:
                    character.inventory.append(old_item)
                
                # Remove o item do inventário
                character.inventory.pop(item_index)
                
                # Adiciona bônus de defesa
                defense_info = ""
                if "defense" in item_data:
                    defense_info = f" Defesa: +{item_data['defense']}."
                
                return {
                    "success": True,
                    "message": f"Você equipou {item_name}. {defense_info} {item_description} {f'Seu {old_item} foi guardado no inventário.' if old_item else ''}"
                }
                
            elif item_type == "consumable":
                # Usar item consumível
                effect = item_data.get("effect", {})
                effect_type = effect.get("type", "")
                effect_value = effect.get("value", 0)
                
                if effect_type == "health":
                    # Restaura HP
                    old_hp = character.current_hp
                    character.current_hp = min(character.current_hp + effect_value, character.max_hp)
                    
                    # Remove o item do inventário
                    character.inventory.pop(item_index)
                    
                    return {
                        "success": True,
                        "message": f"Você usou {item_name} e restaurou {character.current_hp - old_hp} pontos de vida. {item_description}"
                    }
                    
                elif effect_type in ["stamina", "hunger", "thirst"]:
                    # Restaura outros atributos
                    attr_name = f"current_{effect_type}"
                    max_attr_name = f"max_{effect_type}"
                    
                    if hasattr(character, attr_name) and hasattr(character, max_attr_name):
                        old_value = getattr(character, attr_name)
                        max_value = getattr(character, max_attr_name)
                        setattr(character, attr_name, min(old_value + effect_value, max_value))
                    
                    # Remove o item do inventário
                    character.inventory.pop(item_index)
                    
                    return {
                        "success": True,
                        "message": f"Você usou {item_name} e se sente revigorado. {item_description}"
                    }
                
                else:
                    # Outros efeitos
                    # Remove o item do inventário
                    character.inventory.pop(item_index)
                    
                    return {
                        "success": True,
                        "message": f"Você usou {item_name}. {item_description}"
                    }
                    
            elif item_type == "quest":
                # Usar item de quest
                if item_subtype in ["document", "map", "letter"] and "content" in item_data:
                    return {
                        "success": True,
                        "message": f"Você examina {item_name}. {item_description}\n\nConteúdo: {item_data['content']}"
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Você examina {item_name}. {item_description}"
                    }
        
        # Lógica para itens sem dados específicos
        
        # Poções de vida
        if any(p in item_name.lower() for p in ["poção", "potion", "vida", "life", "health"]):
            heal_amount = 20  # Ajuste conforme o tipo de poção
            max_hp = getattr(character, "max_hp", 20)
            old_hp = getattr(character, "current_hp", 0)
            character.current_hp = min(old_hp + heal_amount, max_hp)
            
            # Remove o item do inventário
            character.inventory.pop(item_index)
            
            return {
                "success": True,
                "message": f"Você usou {item_name} e restaurou {character.current_hp - old_hp} pontos de vida. Vida atual: {character.current_hp}/{max_hp}."
            }
        
        # Equipamentos (armas, armaduras, etc.)
        elif any(eq in item_name.lower() for eq in ["espada", "sword", "escudo", "shield", "armadura", "armor", "arco", "bow", "machado", "axe", "adaga", "dagger"]):
            # Determina o tipo de equipamento
            equip_type = "weapon"  # Padrão
            if any(w in item_name.lower() for w in ["espada", "sword", "machado", "axe", "adaga", "dagger", "arco", "bow"]):
                equip_type = "weapon"
            elif any(a in item_name.lower() for a in ["escudo", "shield"]):
                equip_type = "shield"
            elif any(a in item_name.lower() for a in ["armadura", "armor", "peitoral", "breastplate"]):
                equip_type = "armor"
            elif any(h in item_name.lower() for h in ["elmo", "helmet", "chapéu", "hat"]):
                equip_type = "helmet"
            
            # Inicializa equipment se não existir
            if not hasattr(character, 'equipment') or character.equipment is None:
                character.equipment = {}
            
            # Guarda o item equipado anteriormente, se houver
            old_item = character.equipment.get(equip_type)
            
            # Equipa o novo item
            character.equipment[equip_type] = item_name
            
            # Se havia um item equipado anteriormente, coloca de volta no inventário
            if old_item:
                character.inventory.append(old_item)
            
            # Remove o item do inventário
            character.inventory.pop(item_index)
            
            return {
                "success": True,
                "message": f"Você equipou {item_name}. {f'Seu {old_item} foi guardado no inventário.' if old_item else ''}"
            }
        
        # Itens consumíveis (comida, bebida)
        elif any(f in item_name.lower() for f in ["comida", "food", "pão", "bread", "fruta", "fruit", "carne", "meat", "água", "water", "bebida", "drink"]):
            # Restaura fome ou sede
            if hasattr(character, 'current_hunger') and hasattr(character, 'max_hunger'):
                hunger_restore = 20
                character.current_hunger = min(character.current_hunger + hunger_restore, character.max_hunger)
            
            if hasattr(character, 'current_thirst') and hasattr(character, 'max_thirst'):
                thirst_restore = 20
                character.current_thirst = min(character.current_thirst + thirst_restore, character.max_thirst)
            
            # Remove o item do inventário
            character.inventory.pop(item_index)
            
            return {
                "success": True,
                "message": f"Você consumiu {item_name} e se sente revigorado."
            }
        
        # Itens arremessáveis
        elif "arremess" in details.lower() or "throw" in details.lower():
            # Extrai o alvo do arremesso
            target = None
            if "em " in details.lower():
                target_part = details.lower().split("em ", 1)[1]
                target = target_part.strip()
            
            # Remove o item do inventário
            character.inventory.pop(item_index)
            
            return {
                "success": True,
                "message": f"Você arremessou {item_name}{f' em {target}' if target else ''}."
            }
        
        # Para outros tipos de itens, usa a resposta da IA
        result = self.ai_response("use_item", details, character, game_state)
        
        # Se a IA indicar sucesso, remove o item do inventário
        if result.get("success", False):
            character.inventory.pop(item_index)
        
        return result


class FleeActionHandler(ActionHandler):
    """Handler for 'flee' action."""
    
    def handle(self, details: str, character: Character, game_state: Any) -> Dict[str, Any]:
        return self.ai_response("flee", details, character, game_state)


class RestActionHandler(ActionHandler):
    """Handler for 'rest' action."""
    
    def handle(self, details: str, character: Character, game_state: Any) -> Dict[str, Any]:
        return self.ai_response("rest", details, character, game_state)


class CustomActionHandler(ActionHandler):
    """Handler for 'custom' (freeform) actions."""
    def handle(self, details: str, character: Character, game_state: Any) -> Dict[str, Any]:
        # Verifica se o jogador está tentando gerenciar o inventário
        inventory_keywords = ["pegar", "coletar", "guardar", "inventário", "inventory", "collect", "pick up", "get", "take"]
        if any(keyword in details.lower() for keyword in inventory_keywords):
            # Procura por itens mencionados
            items_to_add = []
            
            # Verifica se há itens específicos mencionados
            common_items = [
                "espada", "sword", "escudo", "shield", "poção", "potion", 
                "adaga", "dagger", "arco", "bow", "flecha", "arrow",
                "comida", "food", "água", "water", "moeda", "coin", "gold",
                "pergaminho", "scroll", "livro", "book", "mapa", "map",
                "chave", "key", "gema", "gem", "anel", "ring", "amuleto", "amulet",
                "bolsa", "bag", "mochila", "backpack", "corda", "rope",
                "tocha", "torch", "lanterna", "lantern", "óleo", "oil",
                "erva", "herb", "bandagem", "bandage", "antídoto", "antidote",
                "frasco", "flask", "garrafa", "bottle", "punhal", "knife",
                "pão", "bread", "fruta", "fruit", "carne", "meat"
            ]
            
            for item in common_items:
                if item in details.lower():
                    items_to_add.append(item.capitalize())
            
            # Se não encontrou itens específicos, mas parece que o jogador quer pegar algo
            if not items_to_add and any(verb in details.lower() for verb in ["pegar", "coletar", "take", "get", "pick"]):
                # Verifica se há itens no ambiente (mencionados na descrição da cena)
                scene_items = []
                if hasattr(game_state, 'scene_description'):
                    scene_text = game_state.scene_description.lower()
                    for item in common_items:
                        if item in scene_text and item not in scene_items:
                            scene_items.append(item.capitalize())
                
                if scene_items:
                    items_to_add = scene_items
            
            # Adiciona os itens ao inventário
            if items_to_add:
                if not hasattr(character, 'inventory'):
                    character.inventory = []
                
                for item in items_to_add:
                    character.inventory.append(item)
                
                return {
                    "success": True,
                    "message": f"Você adicionou ao seu inventário: {', '.join(items_to_add)}."
                }
        
        # Verifica se o jogador está tentando iniciar um combate
        combat_keywords = ["atacar", "lutar", "combate", "matar", "batalha", "fight", "attack", "kill"]
        if any(keyword in details.lower() for keyword in combat_keywords):
            # Extrai possível alvo do texto
            words = details.lower().split()
            target = None
            
            # Procura por NPCs mencionados no comando
            if game_state.npcs_present:
                for npc in game_state.npcs_present:
                    if npc.lower() in details.lower():
                        target = npc
                        break
            
            # Se encontrou um alvo específico
            if target:
                # Cria um inimigo baseado no NPC
                enemy = Enemy(
                    name=target,
                    level=random.randint(character.level, character.level + 2),
                    max_hp=random.randint(20, 50),
                    current_hp=random.randint(20, 50),
                    attack_damage=(random.randint(3, 8), random.randint(9, 15)),
                    defense=random.randint(3, 10),
                    description=f"Um {target} hostil que você decidiu atacar."
                )
                
                # Inicia o combate
                if not hasattr(game_state, 'combat') or not game_state.combat:
                    game_state.combat = {
                        "enemy": enemy,
                        "round": 1,
                        "log": [f"Você iniciou combate com {target}!"]
                    }
                    
                    return {
                        "success": True,
                        "message": f"Você atacou {target} e iniciou um combate! Prepare-se para lutar!",
                        "combat": True
                    }
            else:
                # Gera um inimigo aleatório se não houver alvo específico
                enemy_types = ["Bandido", "Lobo", "Goblin", "Esqueleto", "Zumbi", "Ladrão", "Mercenário"]
                enemy_name = random.choice(enemy_types)
                
                enemy = Enemy(
                    name=enemy_name,
                    level=random.randint(character.level, character.level + 2),
                    max_hp=random.randint(20, 50),
                    current_hp=random.randint(20, 50),
                    attack_damage=(random.randint(3, 8), random.randint(9, 15)),
                    defense=random.randint(3, 10),
                    description=f"Um {enemy_name} hostil que apareceu de repente."
                )
                
                # Inicia o combate
                if not hasattr(game_state, 'combat') or not game_state.combat:
                    game_state.combat = {
                        "enemy": enemy,
                        "round": 1,
                        "log": [f"Um {enemy_name} apareceu e você o atacou!"]
                    }
                    
                    return {
                        "success": True,
                        "message": f"Você procurou por inimigos e encontrou um {enemy_name}! Combate iniciado!",
                        "combat": True
                    }
        
        # Verifica se o jogador está tentando ver o mapa ou sua localização
        if "mapa" in details.lower() or "onde estou" in details.lower() or "localização" in details.lower():
            # Verifica se o jogador tem um item para mapear
            has_map_item = False
            if hasattr(character, 'inventory'):
                map_items = ["Mapa", "Pergaminho de Mapa", "Bússola", "Mapa da Região"]
                has_map_item = any(item in character.inventory for item in map_items)
            
            if has_map_item:
                # Jogador tem um mapa, mostra a localização atual
                if hasattr(game_state, 'coordinates') and hasattr(game_state, 'world_map'):
                    coords = game_state.coordinates
                    known_locations = []
                    
                    # Lista locais próximos que o jogador já visitou
                    for loc_id, loc_info in game_state.visited_locations.items():
                        if loc_id in game_state.world_map:
                            loc_coords = game_state.world_map[loc_id].get('coordinates', {})
                            distance = ((loc_coords.get('x', 0) - coords.get('x', 0))**2 + 
                                       (loc_coords.get('y', 0) - coords.get('y', 0))**2)**0.5
                            if distance <= 2:  # Locais a até 2 unidades de distância
                                known_locations.append(f"{loc_info['name']} ({loc_coords.get('x', 0)}, {loc_coords.get('y', 0)})")
                    
                    return {
                        "success": True,
                        "message": f"Você consulta seu mapa. Você está em {game_state.current_location}, nas coordenadas ({coords.get('x', 0)}, {coords.get('y', 0)}). " +
                                  f"Locais próximos que você conhece: {', '.join(known_locations) if known_locations else 'nenhum além deste'}."
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Você consulta seu mapa. Você está em {game_state.current_location}."
                    }
            else:
                # Jogador não tem mapa
                return {
                    "success": False,
                    "message": "Você não tem um mapa ou bússola para determinar sua localização exata. Você sabe apenas que está em " + 
                              f"{game_state.current_location}, mas não consegue determinar suas coordenadas."
                }
        
        # Comportamento padrão para outras ações personalizadas
        return self.ai_response("custom", details, character, game_state)


class UnknownActionHandler(ActionHandler):
    """Handler for unknown actions."""
    
    def handle(self, details: str, character: Character, game_state: Any) -> Dict[str, Any]:
        return self.ai_response("unknown", details, character, game_state)


# Action handler factory
def get_action_handler(action: str) -> ActionHandler:
    """
    Get the appropriate action handler for the given action.
    
    Args:
        action: Action name
        
    Returns:
        Handler for the action
    """
    action_handlers = {
        "move": MoveActionHandler(),
        "look": LookActionHandler(),
        "talk": TalkActionHandler(),
        "search": SearchActionHandler(),
        "attack": AttackActionHandler(),
        "use_item": UseItemActionHandler(),
        "flee": FleeActionHandler(),
        "rest": RestActionHandler(),
        "custom": CustomActionHandler()  # Adiciona suporte para ações livres
    }
    
    return action_handlers.get(action, UnknownActionHandler())
