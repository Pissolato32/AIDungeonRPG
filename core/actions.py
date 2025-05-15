"""
Action handlers for the game engine.
"""

import logging
import random
import re
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class ActionHandler(ABC):
    """Base class for all action handlers."""
    
    @abstractmethod
    def handle(self, details: str, character: Any, game_state: Any) -> Dict[str, Any]:
        """Handle an action."""
        pass
    
    def ai_response(self, action: str, details: str, character: Any, game_state: Any) -> Dict[str, Any]:
        """Generate a response using AI, with didactic context and fallback."""
        try:
            from ai.game_ai_client import GameAIClient
            from ai.groq_client import GroqClient
            # Sempre instancia o GameAIClient com GroqClient (ou outro client real futuramente)
            ai_client = GameAIClient(GroqClient())
            # Adiciona contexto didático ao prompt
            details_with_context = (
                f"{details}\n\n"
                "(IMPORTANTE: Analise a plausibilidade e dificuldade da ação, mas nunca bloqueie a criatividade do jogador. "
                "Se a ação for improvável, explique de forma didática o porquê e sugira consequências, mas sempre narre o resultado de forma criativa e aberta.)"
            )
            result = ai_client.process_player_action(action, details_with_context, character, game_state)
            # Se a IA retornar mensagem de indisponibilidade, mostra fallback amigável
            if (isinstance(result, dict) and not result.get("success", True)) or (
                isinstance(result, dict) and "indisponível" in str(result.get("message", "")).lower()
            ):
                return {
                    "success": False,
                    "message": "A inteligência artificial está temporariamente indisponível. Você pode continuar jogando, mas respostas criativas automáticas estão desativadas."
                }
            return result
        except Exception as e:
            # Fallback amigável
            return {
                "success": False,
                "message": f"A IA está indisponível no momento. Motivo: {e}. Você pode continuar jogando, mas respostas automáticas estão desativadas."
            }

    def _generate_default_response(self, action: str, details: str, character: Any, game_state: Any) -> str:
        """Generate a default response based on action type and context."""
        if action == "move":
            return self._generate_move_response(details, game_state)
        elif action == "look":
            return self._generate_look_response(details, game_state)
        elif action == "talk":
            return self._generate_talk_response(details, game_state)
        elif action == "search":
            return self._generate_search_response(details, game_state)
        else:
            return f"Você tenta {action}: {details}. Aguarde enquanto o mundo reage à sua ação."
    
    def _generate_move_response(self, details: str, game_state: Any) -> str:
        """Generate a response for movement actions."""
        location = game_state.current_location
        
        # Extrair direção ou destino da ação
        details_lower = details.lower()
        
        # Verificar se é movimento para um navio
        if "navio" in details_lower or "barco" in details_lower:
            return (
                f"Você se aproxima do navio atracado no porto. É um grande navio mercante chamado 'Estrela do Mar'. "
                f"A tripulação está ocupada carregando e descarregando mercadorias. O capitão, um homem robusto com "
                f"barba grisalha, observa os trabalhos do convés. Ele nota sua presença e acena para você subir a bordo "
                f"se desejar conversar."
            )
        
        # Verificar se é movimento para uma direção específica
        directions = {
            "norte": "ao norte",
            "sul": "ao sul",
            "leste": "a leste",
            "oeste": "a oeste",
            "direita": "à direita",
            "esquerda": "à esquerda",
            "frente": "à frente",
            "trás": "atrás"
        }
        
        for direction, text in directions.items():
            if direction in details_lower:
                return f"Você se move {text} de {location} e explora a área. O caminho leva a uma pequena praça com algumas bancas de mercadores."
        
        # Resposta genérica para outros movimentos
        return f"Você explora {location}, movendo-se conforme indicado. A área é movimentada com pessoas indo e vindo em seus afazeres diários."

    def _generate_look_response(self, details: str, game_state: Any) -> str:
        """Generate a response for look actions."""
        details_lower = details.lower()
        
        # Olhar para NPCs presentes
        for npc in game_state.npcs_present:
            if npc.lower() in details_lower:
                return f"Você observa {npc} atentamente. Parece ser uma pessoa importante neste local, pela forma como os outros o tratam."
        
        # Olhar para o ambiente
        if "céu" in details_lower or "sky" in details_lower:
            return "Você olha para o céu. Está parcialmente nublado, com o sol ocasionalmente aparecendo entre as nuvens."
        
        if "chão" in details_lower or "ground" in details_lower or "floor" in details_lower:
            return "O chão é feito de pedras bem colocadas, típicas de uma área urbana bem mantida."
        
        # Resposta genérica
        return f"Você examina {details} cuidadosamente. Nada de incomum chama sua atenção, mas a observação cuidadosa sempre é útil."

    def _generate_talk_response(self, details: str, game_state: Any) -> str:
        """Generate a response for talk actions."""
        # Verificar se está falando com um NPC presente
        for npc in game_state.npcs_present:
            if npc.lower() in details.lower():
                return f"{npc} responde: 'Olá, viajante! O que traz você a estas paragens? Posso ajudar com informações sobre a região.'"
        
        # Resposta genérica
        return f"Você tenta falar com {details}, mas não recebe resposta clara. Talvez você precise se aproximar mais ou ser mais específico."

    def _generate_search_response(self, details: str, game_state: Any) -> str:
        """Generate a response for search actions."""
        # Chance de encontrar algo interessante
        if random.random() < 0.3:
            items = ["uma pequena moeda", "um pedaço de pergaminho", "uma pedra interessante", "um pequeno amuleto"]
            found = random.choice(items)
            return f"Procurando em {details}, você encontra {found}. Pode não parecer muito, mas quem sabe sua utilidade no futuro."
        
        # Resposta genérica
        return f"Você procura cuidadosamente em {details}, mais não encontra nada de especial desta vez."

class UnknownActionHandler(ActionHandler):
    """Handler for unknown actions."""
    
    def handle(self, details: str, character: Any, game_state: Any) -> Dict[str, Any]:
        return {
            "success": False,
            "message": "Ação desconhecida. Tente move, look, talk ou search."
        }

class MoveActionHandler(ActionHandler):
    """Handler for 'move' action."""
    
    def handle(self, details: str, character: Any, game_state: Any) -> Dict[str, Any]:
        return self.ai_response("move", details, character, game_state)

class LookActionHandler(ActionHandler):
    """Handler for 'look' action."""
    
    def handle(self, details: str, character: Any, game_state: Any) -> Dict[str, Any]:
        return self.ai_response("look", details, character, game_state)

class TalkActionHandler(ActionHandler):
    """Handler for 'talk' action."""
    
    def handle(self, details: str, character: Any, game_state: Any) -> Dict[str, Any]:
        return self.ai_response("talk", details, character, game_state)

class SearchActionHandler(ActionHandler):
    """Handler for 'search' action."""
    
    def handle(self, details: str, character: Any, game_state: Any) -> Dict[str, Any]:
        return self.ai_response("search", details, character, game_state)

class AttackActionHandler(ActionHandler):
    """Handler for 'attack' action."""
    
    def handle(self, details: str, character: Any, game_state: Any) -> Dict[str, Any]:
        return {
            "success": True,
            "message": f"Você se prepara para atacar {details}. Tem certeza que deseja iniciar um combate? Use 'attack: confirmar' para confirmar."
        }

class FleeActionHandler(ActionHandler):
    """Handler for 'flee' action."""
    
    def handle(self, details: str, character: Any, game_state: Any) -> Dict[str, Any]:
        return {
            "success": True,
            "message": "Você decide recuar estrategicamente da situação. Melhor viver para lutar outro dia."
        }

class UseItemActionHandler(ActionHandler):
    """Handler for 'use_item' action."""
    
    def handle(self, details: str, character: Any, game_state: Any) -> Dict[str, Any]:
        # Verificar se o item está no inventário
        inventory = character.inventory if hasattr(character, 'inventory') else []
        
        for item in inventory:
            item_name = item if isinstance(item, str) else item.get('name', '')
            if item_name.lower() in details.lower():
                return {
                    "success": True,
                    "message": f"Você usa {item_name}. Sente-se revigorado e pronto para continuar sua aventura."
                }
        
        return {
            "success": False,
            "message": f"Você não possui {details} em seu inventário."
        }

class RestActionHandler(ActionHandler):
    """Handler for 'rest' action."""
    
    def handle(self, details: str, character: Any, game_state: Any) -> Dict[str, Any]:
        # Recuperar HP e stamina
        if hasattr(character, 'rest'):
            recovery = character.rest()
            return {
                "success": True,
                "message": f"Você descansa por um tempo. Recuperou {recovery.get('hp_recovered', 0)} pontos de vida e {recovery.get('stamina_recovered', 0)} pontos de stamina."
            }
        
        return {
            "success": True,
            "message": "Você descansa por um tempo e se sente revigorado."
        }

class CustomActionHandler(ActionHandler):
    """Handler for custom/free-form actions."""
    
    def handle(self, details: str, character: Any, game_state: Any) -> Dict[str, Any]:
        # Nova lógica: sempre delega à IA, mas com contexto de dificuldade e plausibilidade
        # Analisa o pedido do jogador
        action_text = details.strip().lower()
        # Exemplos de limites: tarefas "impossíveis" ou absurdas
        impossiveis = [
            "atacar uma vila inteira", "destruir uma cidade sozinho", "matar todos instantaneamente", "voar sem magia", "ficar invisível sem magia"
        ]
        for impossivel in impossiveis:
            if impossivel in action_text:
                return self.ai_response(
                    "custom",
                    f"{details}\n\nNota do sistema: Esta ação é extremamente improvável para um personagem sozinho. Considere as limitações físicas, sociais e mágicas do seu personagem. O mestre pode impor penalidades severas, exigir rolagens de dados muito difíceis ou simplesmente narrar uma consequência negativa realista.",
                    character,
                    game_state
                )
        # Para qualquer outra ação, delega à IA, mas adiciona contexto de dificuldade baseado em atributos
        # Exemplo: se a ação envolve força, furtividade, magia, etc, pode-se sugerir rolagem de dados
        contexto = ""
        if any(palavra in action_text for palavra in ["força", "levantar", "empurrar", "arrombar", "quebrar"]):
            contexto = "Esta ação depende da sua força. O mestre pode pedir uma rolagem de força."
        elif any(palavra in action_text for palavra in ["furtivo", "esconder", "roubar", "invadir", "infiltrar"]):
            contexto = "Esta ação depende da sua destreza. O mestre pode pedir uma rolagem de destreza."
        elif any(palavra in action_text for palavra in ["magia", "encantar", "lançar feitiço", "conjurar"]):
            contexto = "Esta ação depende da sua inteligência ou sabedoria. O mestre pode pedir uma rolagem de magia."
        elif any(palavra in action_text for palavra in ["convencer", "intimidar", "persuadir", "mentir"]):
            contexto = "Esta ação depende do seu carisma. O mestre pode pedir uma rolagem de carisma."
        # Adiciona contexto didático para a IA
        if contexto:
            details = f"{details}\n\nNota do sistema: {contexto} Se a tarefa for muito difícil, o mestre pode impor penalidades ou consequências realistas."
        else:
            details = f"{details}\n\nNota do sistema: O mestre deve avaliar a plausibilidade da ação, considerando atributos, contexto, e pode exigir rolagens de dados apropriadas."
        return self.ai_response("custom", details, character, game_state)

def get_action_handler(action: str) -> ActionHandler:
    """Get the appropriate action handler for an action."""
    # Map of action types to handlers
    action_handlers = {
        "move": MoveActionHandler(),
        "look": LookActionHandler(),
        "talk": TalkActionHandler(),
        "search": SearchActionHandler(),
        "attack": AttackActionHandler(),
        "use_item": UseItemActionHandler(),
        "flee": FleeActionHandler(),
        "rest": RestActionHandler(),
        "custom": CustomActionHandler()
    }
    
    return action_handlers.get(action, UnknownActionHandler())