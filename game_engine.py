from __future__ import annotations
import os
import json
import logging
import random
from typing import Dict, List, Union, Optional, Any, TypeVar, cast
from models import Character, Enemy
from translations import TranslationManager
from actions import get_action_handler
from prompt_manager import PromptManager
from utils import save_json_data, load_json_data

logger = logging.getLogger(__name__)
T = TypeVar('T', bound='GameState')

class GameState:
    """
    Represents the current state of the game.
    
    Attributes:
        current_location (str): Name of the current location
        location_id (str): Unique identifier for the location
        coordinates (Dict[str, int]): Map coordinates (x, y, z)
        scene_description (str): Description of the current scene
        npcs_present (List[str]): NPCs present in the location
        events (List[str]): Current events in the location
        messages (List[str]): Game messages/dialogue
        combat (Union[bool, Dict[str, Any]]): Combat state
        quests (List[Dict[str, Any]]): Active quests
        secrets (List[str]): Discovered secrets
        language (str): Current language setting
        visited_locations (Dict[str, Dict[str, Any]]): Record of visited locations
        known_npcs (Dict[str, Dict[str, Any]]): NPCs the player has interacted with
        world_map (Dict[str, Dict[str, Any]]): World map with discovered locations
        summary (str): Incremental summary of relevant interactions
    """
    
    def __init__(self) -> None:
        """Initialize a new game state with default values."""
        self.current_location: str = "Start"
        self.location_id: str = "village_center"
        self.coordinates: Dict[str, int] = {"x": 0, "y": 0, "z": 0}
        self.scene_description: str = "You are in a mysterious place."
        self.npcs_present: List[str] = []
        self.events: List[str] = []
        self.messages: List[str] = []
        self.combat: Union[bool, Dict[str, Any]] = False
        self.quests: List[Dict[str, Any]] = []
        self.secrets: List[str] = []
        self.language: str = TranslationManager.DEFAULT_LANGUAGE
        self.visited_locations: Dict[str, Dict[str, Any]] = {}
        self.known_npcs: Dict[str, Dict[str, Any]] = {}
        self.world_map: Dict[str, Dict[str, Any]] = {}
        self.summary: str = ""

    def add_to_summary(self, interaction_type: str, details: str) -> None:
        """
        Add an interaction to the incremental summary.
        
        Args:
            interaction_type: Type of interaction (quest, dialogue, combat, etc.)
            details: Details of the interaction
        """
        new_interaction = f"[{interaction_type}] {details}"
        if self.summary:
            self.summary += f"\n{new_interaction}"
        else:
            self.summary = new_interaction

    def get_relevant_summary(self, context_type: Optional[str] = None) -> str:
        """
        Get relevant summary based on context.
        
        Args:
            context_type: Type of context to filter (quest, dialogue, etc.)
            
        Returns:
            Filtered summary string
        """
        if not context_type:
            return self.summary
            
        interactions = self.summary.split('\n') if self.summary else []
        relevant = [
            interaction for interaction in interactions 
            if interaction.startswith(f'[{context_type}]')
        ]
        return '\n'.join(relevant)
        
    def update_quest_summary(self, quest_name: str, action: str, progress: int) -> None:
        """
        Update the summary with quest-related interactions.
        
        Args:
            quest_name: Name of the quest
            action: Action taken (started, updated, completed)
            progress: Current progress percentage
        """
        details = f"Quest '{quest_name}' {action} - Progress: {progress}%"
        self.add_to_summary('quest', details)
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameState':
        """
        Create a GameState instance from a dictionary.
        
        Args:
             game state data
            
        Returns:
            GameState instance
        """
        instance = cls()
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        if not hasattr(instance, 'summary'):
            instance.summary = ""
        return instance
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the game state to a dictionary.
        
        Returns:
            Dictionary representation of the game state
        """
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }

class GameEngine:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

    def _get_character_path(self, user_id: str) -> str:
        """Get path to character file"""
        return os.path.join(self.data_dir, f"character_{user_id}.json")

    def _get_game_state_path(self, user_id: str) -> str:
        """Get path to game state file"""
        return os.path.join(self.data_dir, f"game_state_{user_id}.json")

    def save_character(self, user_id: str, character: Union[Character, Dict[str, Any]]) -> bool:
        """
        Save character data to file.

        Args:
            user_id: Unique identifier for the user
            character: Character object or dictionary to save

        Returns:
            Success status of the save operation
        """
        character_path = self._get_character_path(user_id)

        # Convert Character object to dictionary if needed
        if hasattr(character, 'to_dict'):
            character_dict = character.to_dict()
        else:
            character_dict = cast(Dict[str, Any], character)

        return save_json_data(character_dict, character_path)

    def load_character(self, user_id: str) -> Optional[Character]:
        """
        Load character data from file.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Character object if found, None otherwise
        """
        character_path = self._get_character_path(user_id)
        character_data = load_json_data(character_path)

        if character_data:
            # Convert to Character object
            return Character.from_dict(character_data)
        return None

    def create_enemy(self, enemy_data: Dict[str, Any]) -> Enemy:
        """
        Create enemy object from dictionary.

        Args:
            enemy_data: Dictionary with enemy data

        Returns:
            Enemy object
        """
        return Enemy.from_dict(enemy_data)

    def _get_stamina_cost(self, action: str) -> int:
        """
        Get stamina cost for action.

        Args:
            action: Type of action

        Returns:
            Stamina cost as integer
        """
        stamina_costs = {
            "move": 1,
            "look": 0,
            "talk": 0,
            "search": 2,
            "attack": 3,
            "flee": 1,
            "use_item": 0
        }
        return stamina_costs.get(action, 0)  # Default to 0 if action not found

    def delete_character(self, user_id: str) -> bool:
        """
        Delete character data file.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Success status of the delete operation
        """
        character_path = self._get_character_path(user_id)

        if os.path.exists(character_path):
            try:
                os.remove(character_path)
                return True
            except Exception as e:
                logger.error(f"Error deleting character: {str(e)}")
                return False
        return True

    def save_game_state(self, user_id: str, game_state: Union['GameState', Dict[str, Any]]) -> bool:
        """
        Save game state to file.

        Args:
            user_id: Unique identifier for the user
            game_state: GameState object or dictionary to save

        Returns:
            Success status of the save operation
        """
        game_state_path = self._get_game_state_path(user_id)

        # Convert GameState object to dictionary if needed
        if hasattr(game_state, 'to_dict'):
            game_state_dict = game_state.to_dict()
        else:
            game_state_dict = cast(Dict[str, Any], game_state)

        return save_json_data(game_state_dict, game_state_path)

    def load_game_state(self, user_id: str) -> 'GameState':
        """
        Load game state from file.

        Args:
            user_id: Unique identifier for the user

        Returns:
            GameState object (new instance if no saved data found)
        """
        game_state_path = self._get_game_state_path(user_id)
        game_state_data = load_json_data(game_state_path)

        if game_state_data:
            game_state = GameState.from_dict(game_state_data)
            # Ensure messages list exists
            if not hasattr(game_state, 'messages') or game_state.messages is None:
                game_state.messages = []
            return game_state

        # Return a new GameState object if no data found
        return GameState()

    def delete_game_state(self, user_id: str) -> bool:
        """
        Delete game state file.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Success status of the delete operation
        """
        game_state_path = self._get_game_state_path(user_id)

        if os.path.exists(game_state_path):
            try:
                os.remove(game_state_path)
                return True
            except Exception as e:
                logger.error(f"Error deleting game state: {str(e)}")
                return False
        return True

    def get_character_attribute(self, char: Union[Dict[str, Any], Character], attr: str, default: Any = None) -> Any:
        if hasattr(char, attr):
            attr_val = getattr(char, attr)
            if callable(attr_val):
                return attr_val()
            return attr_val
        elif isinstance(char, dict):
            return char.get(attr, default)
        return default

    def set_character_attribute(self, char: Union[Dict[str, Any], Character], attr: str, value: Any) -> None:
        if hasattr(char, attr):
            setattr(char, attr, value)
        elif isinstance(char, dict):
            char[attr] = value

    def create_action_prompt(self, action: str, action_details: str, character: Union[Dict[str, Any], Character], game_state: 'GameState') -> str:
        return PromptManager.create_action_prompt(
            action,
            action_details,
            character,
            game_state,
            self.get_character_attribute
        )

    def process_action(self, action: str, details: str, character: Character, game_state: 'GameState', groq_client: Any) -> Dict[str, Any]:
        try:
            logger.info(f"Processing action '{action}' for character {character.name} at {game_state.current_location}")
            stamina_cost = self._get_stamina_cost(action)
            if not character.validate_action(action, stamina_cost):
                return {
                    "success": False,
                    "message": f"Not enough stamina to {action}. You need {stamina_cost} stamina."
                }
            character.current_stamina -= stamina_cost
            action_handler = get_action_handler(action)
            result = action_handler.handle(details, character, game_state)
            if hasattr(game_state, 'messages'):
                msg = result.get("message", "")
                if msg:
                    game_state.messages.append(msg)
            return result
        except Exception as e:
            logger.error(f"Error processing action '{action}': {str(e)}")
            logger.debug(f"Action details: {details}")
            logger.debug(f"Character: {character.name}, Level: {character.level}")
            logger.debug(f"Location: {game_state.current_location}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "message": f"An error occurred: {str(e)}",
                "error": str(e)
            }
            
    def initialize_game_world(self, game_state: 'GameState', groq_client: Any = None, language: str = 'pt-br') -> Dict[str, Any]:
        """
        Inicializa o mundo do jogo com um cenário procedural.
        
        Args:
            game_state: Estado atual do jogo
            groq_client: Cliente da API Groq para geração de texto
            language: Idioma para geração do texto
            
        Returns:
            Dicionário com informações do cenário inicial
        """
        # Importa o gerador de mundo
        from world_generator import WorldGenerator
        
        # Inicializa o gerador de mundo
        world_generator = WorldGenerator(self.data_dir)
        
        # Carrega ou cria o mapa do mundo
        world_data = world_generator.load_world()
        
        # Verifica se já existe um local inicial
        starting_location = None
        for loc_id, loc_data in world_data.get("locations", {}).items():
            if loc_data.get("coordinates", {}).get("x") == 0 and loc_data.get("coordinates", {}).get("y") == 0:
                starting_location = loc_data
                break
        
        # Se não existir, gera um novo local inicial
        if not starting_location:
            starting_location = world_generator.generate_starting_location()
            
            # Adiciona o local ao mapa do mundo
            if "locations" not in world_data:
                world_data["locations"] = {}
            world_data["locations"][starting_location["id"]] = starting_location
            
            # Salva o mapa do mundo
            world_generator.save_world(world_data)
        
        # Atualiza o estado do jogo
        game_state.current_location = starting_location["name"]
        game_state.location_id = starting_location["id"]
        game_state.scene_description = starting_location["description"]
        game_state.npcs_present = starting_location["npcs"]
        game_state.events = starting_location["events"]
        game_state.coordinates = starting_location["coordinates"]
        
        # Inicializa o mapa do mundo no estado do jogo
        game_state.world_map = world_data
        
        # Adiciona o local aos locais visitados
        if not hasattr(game_state, 'visited_locations'):
            game_state.visited_locations = {}
            
        game_state.visited_locations[game_state.location_id] = {
            "name": starting_location["name"],
            "description": starting_location["description"],
            "coordinates": game_state.coordinates.copy(),
            "npcs_seen": starting_location["npcs"].copy(),
            "events_seen": starting_location["events"].copy()
        }
        
        # Formata a resposta para exibição
        formatted_response = {
            "success": True,
            "location": starting_location["name"],
            "description": starting_location["description"],
            "npcs": ", ".join(starting_location["npcs"]),
            "events": " ".join(starting_location["events"]),
            "message": f"Bem-vindo a {starting_location['name']}! Você pode explorar usando as ações disponíveis."
        }
        
        return formatted_response

    def generate_random_start_prompt(self, groq_client=None, language='pt-br'):
        """
        Gera um prompt inicial randômico e criativo para o início do jogo, usando IA se disponível.
        
        Args:
            groq_client: Cliente da API Groq para geração de texto
            language: Idioma para geração do texto (padrão: pt-br)
            
        Returns:
            Dict com informações do cenário inicial
        """
        # Elementos base para o mundo (fallback)
        locais = [
            "Aldeia de Rivenbrook", "Vilarejo de Eldermoor", "Cidade de Stonehelm", "Aldeia de Willowshade",
            "Vila de Oakenspire", "Povoado de Mistwood", "Aldeia de Silverbrook", "Fortaleza de Ironkeep",
            "Porto de Wavehaven", "Ruínas de Dragonfell", "Cidade Élfica de Silverleaf"
        ]
        tavernas = [
            "O Javali Dourado", "A Raposa Prateada", "O Dragão Sonolento", "O Corvo Negro", "A Lua Minguante",
            "O Caldeirão Fumegante", "A Espada Quebrada", "O Grifo Alado", "A Sereia Encantada"
        ]
        ferrarias = [
            "Martelo Flamejante", "Bigorna Antiga", "O Ferro Rúnico", "O Martelo do Anão",
            "Forja do Dragão", "Aço Élfico", "Metais Encantados", "Armas do Guerreiro"
        ]
        npcs = [
            "Ancião da Aldeia", "Mercador Viajante", "Caçador de Trolls", "Bardo Elfo", "Bruxa do Pântano",
            "Ferreiro Orc", "Fada Curiosa", "Gigante Gentil", "Druida da Floresta", "Aventureiro Misterioso",
            "Cavaleiro Errante", "Alquimista Excêntrico", "Ladino Sombrio", "Sacerdotisa da Lua", "Mago Aprendiz"
        ]
        eventos = [
            "Uma brisa suave sopra pela aldeia.",
            "Um grupo de crianças corre brincando com um cão.",
            "Um trovão distante ecoa nas montanhas.",
            "O sino da igreja toca anunciando o entardecer.",
            "Um dragão é avistado voando ao longe.",
            "Um orc ferido pede ajuda perto da fonte.",
            "Fadas dançam ao redor de uma árvore antiga.",
            "Um mercador grita ofertas especiais na praça.",
            "Cavaleiros retornam de uma missão contra trolls.",
            "Uma caravana de elfos chega com mercadorias exóticas.",
            "Fumaça colorida sai da torre do mago local.",
            "Um grupo de anões discute sobre uma mina recém-descoberta."
        ]
        
        # Tenta usar a API da Groq para gerar um cenário criativo
        if groq_client:
            try:
                # Prompt para a API da Groq
                prompt = f"""
                Crie um cenário inicial para um jogo de RPG medieval fantasia. 
                O cenário deve incluir:
                1. Nome e descrição detalhada de um local (aldeia, cidade, floresta, ruínas, etc.)
                2. Pelo menos dois NPCs presentes com breves descrições
                3. Um evento atual ou situação interessante acontecendo
                4. Uma descrição atmosférica e imersiva do ambiente
                
                Regras:
                - Mantenha-se fiel ao gênero medieval fantasia (dragões, orcs, elfos, magia, etc.)
                - NÃO inclua elementos modernos (armas de fogo, tecnologia, etc.)
                - Seja criativo e detalhado, criando uma atmosfera imersiva
                - Mantenha o tom adequado para uma aventura de RPG
                - Limite a resposta a 3-4 parágrafos no total
                
                Formato da resposta (JSON):
                {{
                    "local": "Nome do local",
                    "descricao": "Descrição detalhada do local e ambiente",
                    "npcs_presentes": ["Nome do NPC 1", "Nome do NPC 2"],
                    "eventos": ["Descrição do evento ou situação atual"]
                }}
                """
                
                # Chamada para a API da Groq
                response = groq_client.chat.completions.create(
                    model="llama3-70b-8192",  # ou outro modelo disponível
                    messages=[
                        {"role": "system", "content": "Você é um mestre de RPG criativo especializado em mundos medievais de fantasia."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=800,
                    response_format={"type": "json_object"}
                )
                
                # Extrai o conteúdo da resposta
                content = response.choices[0].message.content
                scenario = json.loads(content)
                
                # Verifica se o cenário tem todos os campos necessários
                if all(key in scenario for key in ["local", "descricao", "npcs_presentes", "eventos"]):
                    return scenario
                    
            except Exception as e:
                logger.error(f"Erro ao gerar cenário com API Groq: {str(e)}")
                # Continua para o fallback em caso de erro
        
        # Fallback: geração aleatória local
        local = random.choice(locais)
        taverna = random.choice(tavernas)
        ferraria = random.choice(ferrarias)
        
        # Seleciona 2-3 NPCs aleatórios sem repetição
        npcs_presentes = random.sample(npcs, k=min(random.randint(2, 3), len(npcs)))
        
        # Seleciona 1-2 eventos aleatórios sem repetição
        eventos_atuais = random.sample(eventos, k=min(random.randint(1, 2), len(eventos)))
        
        # Gera descrições baseadas nas escolhas
        direcoes = ["norte", "sul", "leste", "oeste"]
        random.shuffle(direcoes)
        
        # Cria uma descrição mais elaborada
        descricoes_locais = [
            f"Você está no centro de {local}. Há uma taverna chamada '{taverna}' ao {direcoes[0]}, uma ferraria chamada '{ferraria}' ao {direcoes[1]}, e o portão da aldeia ao {direcoes[2]}.",
            f"Você se encontra na praça central de {local}. A famosa taverna '{taverna}' fica ao {direcoes[0]}, enquanto a renomada ferraria '{ferraria}' está ao {direcoes[1]}. O caminho para a floresta segue ao {direcoes[2]}.",
            f"As ruas de pedra de {local} se estendem ao seu redor. A taverna '{taverna}' com seu letreiro rangendo ao vento fica ao {direcoes[0]}. A fumaça da fornalha da ferraria '{ferraria}' sobe ao {direcoes[1]}.",
            f"Você acaba de chegar a {local}, um lugar cheio de histórias e mistérios. A taverna local '{taverna}' está ao {direcoes[0]}, com o som de música e risos. A ferraria '{ferraria}' emite o som de metal sendo trabalhado ao {direcoes[1]}."
        ]
        
        descricao = random.choice(descricoes_locais)
        
        # Monta o cenário final
        scenario = {
            "local": local,
            "descricao": descricao,
            "npcs_presentes": npcs_presentes,
            "eventos": eventos_atuais
        }
        
        return scenario
