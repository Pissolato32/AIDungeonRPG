"""
Prompt manager for the game engine.

This module handles the creation and management of prompts for the AI.
"""

import logging
from typing import Dict, Any, Union, List

from models import Character
from translations import TranslationManager

logger = logging.getLogger(__name__)


class PromptManager:
    """Manager for creating AI prompts based on game state and actions."""
    
    @staticmethod
    def create_action_prompt(
        action: str,
        action_details: str,
        character: Union[Dict[str, Any], Character],
        game_state: Any,
        get_character_attribute: callable
    ) -> str:
        """
        Create a prompt for the AI based on the action.
        
        Args:
            action: Type of action
            action_details: Additional details for the action
            character: Player character
            game_state: Current game state
            get_character_attribute: Function to safely get character attributes
            
        Returns:
            Formatted prompt string
        """
        # Get character attributes
        char_name = get_character_attribute(character, "name", "Unknown")
        char_class = get_character_attribute(character, "character_class", "Warrior")
        char_level = get_character_attribute(character, "level", 1)
        
        # Format basic prompt - use simple strings for NPCs and events
        npc_names = game_state.npcs_present if game_state.npcs_present else []
        event_descriptions = game_state.events if hasattr(game_state, 'events') and game_state.events else []
        
        # Determine language for the prompt
        lang = game_state.language if hasattr(game_state, 'language') else TranslationManager.DEFAULT_LANGUAGE
        
        # Select prompt based on language
        if lang.startswith("pt"):
            prompt_text = f"""
            Como mestre do jogo, responda à ação do jogador em formato JSON válido. Seja criativo, detalhado e imersivo.
            Faça rolagens de dados quando apropriado para determinar o sucesso das ações.
            
            IMPORTANTE: Se o jogador tentar atacar, lutar ou iniciar combate com alguém, SEMPRE permita que o combate aconteça.
            Quando o jogador tentar atacar, retorne "combat": true no JSON para iniciar o sistema de combate.
            
            Local atual: {game_state.current_location}
            Descrição atual: {game_state.scene_description}
            NPCs presentes: {', '.join(npc_names) if npc_names else 'Nenhum'}
            
            Eventos acontecendo: 
            {chr(10).join(['- ' + event for event in event_descriptions]) if event_descriptions else 'Nenhum'}
            
            Personagem: {char_name}, Nível {char_level} {char_class}
            Atributos relevantes:
            - Força: {get_character_attribute(character, "strength", 10)}
            - Destreza: {get_character_attribute(character, "dexterity", 10)}
            - Constituição: {get_character_attribute(character, "constitution", 10)}
            - Inteligência: {get_character_attribute(character, "intelligence", 10)}
            - Sabedoria: {get_character_attribute(character, "wisdom", 10)}
            - Carisma: {get_character_attribute(character, "charisma", 10)}
            
            Ação: {action}
            Detalhes: {action_details}
            
            Responda com um objeto JSON contendo:
            - success: booleano indicando se a ação foi bem-sucedida
            - roll: objeto com "value" (valor do dado), "difficulty" (dificuldade) e "attribute" (atributo usado)
            - message: texto descritivo do que aconteceu, incluindo o resultado da rolagem
            """
        else:
            # English as default
            prompt_text = f"""
            As a game master, respond to the player's action in valid JSON format. Be creative, detailed and immersive.
            
            IMPORTANT: If the player tries to attack, fight or initiate combat with someone, ALWAYS allow the combat to happen.
            When the player tries to attack, return "combat": true in the JSON to initiate the combat system.
            
            Current location: {game_state.current_location}
            Current description: {game_state.scene_description}
            NPCs present: {', '.join(npc_names) if npc_names else 'None'}
            
            Events happening: 
            {chr(10).join(['- ' + event for event in event_descriptions]) if event_descriptions else 'None'}
            
            Character: {char_name}, Level {char_level} {char_class}
            
            Action: {action}
            Details: {action_details}
            
            Respond with a JSON object containing:
            - success: boolean indicating if the action succeeded
            - message: descriptive text of what happened
            """
        
        # Add explicit instruction for correct JSON formatting
        prompt = prompt_text + """
        
        IMPORTANT: Your response MUST be a valid JSON object. Do not include any text outside the JSON structure.
        Format your JSON properly with correct quotes and commas. Example:
        {
          "success": true,
          "message": "Description of what happened",
          "other_fields": "other values"
        }
        """
        
        # Add action-specific instructions based on language
        prompt += PromptManager._get_action_specific_instructions(action, lang)
        
        return prompt
    
    @staticmethod
    def _get_action_specific_instructions(action: str, lang: str) -> str:
        """
        Get action-specific instructions for the prompt.
        
        Args:
            action: Type of action
            lang: Language code
            
        Returns:
            Action-specific instructions
        """
        if action == "move":
            if lang.startswith("pt"):
                instructions = """
                - new_location: nome do novo local
                - description: descrição detalhada e atmosférica do novo local (pelo menos 3 frases)
                - npcs: array de 2-5 NPCs presentes no local (apenas nomes como strings)
                - events: array de 1-3 eventos dinâmicos acontecendo no local (apenas descrições como strings)
                - interactables: array de objetos com os quais o jogador pode interagir, cada um como um objeto com campos "nome", "tipo" (mobilia, decoracao, item) e "descricao"
                - ambient: objeto com campos "sons", "cheiros", "temperatura" e "iluminacao" descrevendo a experiência sensorial
                """
                
                instructions += """
                Se o local for uma taverna ou estalagem, inclua:
                - Detalhes específicos sobre a atmosfera (música, cheiros, iluminação)
                - Um barman ou estalajadeiro com nome e personalidade
                - Pelo menos um cliente interessante com uma história ou missão
                - Um evento aleatório como um bardo se apresentando, uma discussão acalorada, jogos de azar ou contação de histórias
                - Alguma comida ou bebida notável sendo servida como objetos interativos
                - Mobília como mesas, cadeiras, balcão do bar, lareira com os quais se pode interagir
                
                Se o local for uma loja ou mercado:
                - Inclua um array "items_for_sale" com objetos contendo campos "nome", "descricao", "preco" e "raridade"
                - Dê ao comerciante um traço de personalidade distintivo e uma história de fundo
                - Inclua pelo menos um outro cliente com sua própria história
                - Adicione móveis e decorações específicas da loja como interativos
                
                Se o local for ao ar livre:
                - Inclua detalhes sobre o clima e hora do dia no objeto ambient
                - Descreva os arredores naturais e qualquer vida selvagem como interativos
                - Adicione um elemento ambiental (folhas farfalhando, trovão distante, etc.)
                - Inclua caminhos ou direções potenciais que o jogador pode tomar
                """
            else:
                instructions = """
                - new_location: name of the new location
                - description: detailed and atmospheric description of the new location (at least 3 sentences)
                - npcs: array of 2-5 NPCs present at the new location (just names as strings)
                - events: array of 1-3 dynamic events happening at the new location (just descriptions as strings)
                - interactables: array of objects that the player can interact with, each as an object with "nome", "tipo" (furniture, decoration, item), and "descricao" fields
                - ambient: object with "sons", "cheiros", "temperatura", and "iluminacao" fields describing the sensory experience
                """
                
                instructions += """
                If the location is a tavern or inn, include:
                - Specific details about the atmosphere (music, smells, lighting)
                - A bartender or innkeeper with a name and personality
                - At least one interesting patron with a story or quest
                - A random event like a bard performing, a heated argument, gambling, or storytelling
                - Some notable food or drink being served as interactable objects
                - Furniture like tables, chairs, bar counter, fireplace that can be interacted with
                
                If the location is a shop or market:
                - Include an "items_for_sale" array with objects containing "nome", "descricao", "preco", and "raridade" fields
                - Give the shopkeeper a distinctive personality trait and background story
                - Include at least one other customer with their own story
                - Add shop-specific furniture and decorations as interactables
                
                If the location is outdoors:
                - Include details about the weather and time of day in the ambient object
                - Describe the natural surroundings and any wildlife as interactables
                - Add an environmental element (rustling leaves, distant thunder, etc.)
                - Include potential paths or directions the player can take
                """
            
            return instructions
            
        elif action == "look":
            if lang.startswith("pt"):
                return """
                - description: descrição detalhada do que o personagem vê (pelo menos 3 frases)
                - objects: array de 3-6 objetos notáveis na área, cada um como um objeto com campos "nome", "descricao" e "interativo" (booleano)
                - hidden: quaisquer detalhes ocultos que foram descobertos (portas secretas, itens escondidos, etc.)
                - atmosphere: detalhes sensoriais sobre o ambiente (sons, cheiros, temperatura)
                - people: array de pessoas ou criaturas presentes, cada uma como um objeto com campos "nome", "aparencia" e "acao" (o que estão fazendo)
                - interactions: objeto descrevendo possíveis interações com o ambiente, NPCs e objetos
                """
            else:
                return """
                - description: detailed description of what the character sees (at least 3 sentences)
                - objects: array of 3-6 notable objects in the area, each as an object with "nome", "descricao", and "interativo" (boolean) fields
                - hidden: any hidden details that were discovered (secret doors, concealed items, etc.)
                - atmosphere: sensory details about the environment (sounds, smells, temperature)
                - people: array of people or creatures present, each as an object with "nome", "aparencia", and "acao" (what they're doing) fields
                - interactions: object describing possible interactions with the environment, NPCs, and objects
                """
                
        elif action == "talk":
            if lang.startswith("pt"):
                return """
                - npc_name: nome do NPC com quem está falando
                - appearance: breve descrição da aparência e comportamento do NPC
                - dialogue: o que o NPC diz, refletindo sua personalidade e história
                - reaction: como o NPC reage ao personagem (amigável, desconfiado, etc.)
                - background_hint: uma dica sobre o passado ou motivações do NPC
                - options: array de 3-5 possíveis respostas ou perguntas que o jogador poderia fazer, cada uma como um objeto com campos "texto" e "tema"
                - potential_quest: objeto opcional com campos "titulo", "descricao" e "recompensa" se este NPC puder oferecer uma missão
                - knowledge: array de tópicos que este NPC conhece e que podem ser úteis para o jogador
                - items: array de itens que este NPC pode estar disposto a trocar ou dar ao jogador
                """
            else:
                return """
                - npc_name: name of the NPC being talked to
                - appearance: brief description of the NPC's appearance and demeanor
                - dialogue: what the NPC says, reflecting their personality and background
                - reaction: how the NPC reacts to the character (friendly, suspicious, etc.)
                - background_hint: a hint about the NPC's background or motivations
                - options: array of 3-5 possible responses or questions the player could ask, each as an object with "texto" and "tema" fields
                - potential_quest: optional object with "titulo", "descricao", and "recompensa" fields if this NPC might offer a quest
                - knowledge: array of topics this NPC knows about that might be useful to the player
                - items: array of items this NPC might be willing to trade or give to the player
                """
                
        elif action == "search":
            if lang.startswith("pt"):
                return """
                - findings: descrição detalhada do que o personagem encontra
                - items: array de quaisquer itens descobertos, cada um como um objeto com campos "nome", "descricao" e "valor"
                - secrets: quaisquer segredos ou informações ocultas reveladas
                - clues: quaisquer pistas sobre a história da área ou situação atual
                - hidden_interactions: array de novas interações que se tornam disponíveis após a busca
                - danger: aviso opcional se a busca puder acionar uma armadilha ou atrair atenção indesejada
                """
            else:
                return """
                - findings: detailed description of what the character finds
                - items: array of any items discovered, each as an object with "nome", "descricao", and "valor" fields
                - secrets: any secrets or hidden information revealed
                - clues: any clues about the area's history or current situation
                - hidden_interactions: array of new interactions that become available after searching
                - danger: optional warning if searching might trigger a trap or attract unwanted attention
                """
                
        # Default: return empty string for actions without specific instructions
        return ""