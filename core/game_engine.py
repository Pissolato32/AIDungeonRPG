"""
Game engine module.
"""

import os
import json
import logging
import random
from typing import Dict, Any, Optional, List

from core.actions import get_action_handler

logger = logging.getLogger(__name__)

class GameState:
    """Represents the current state of the game."""
    
    def __init__(self):
        """Initialize a new game state."""
        self.current_location = ""
        self.location_id = ""
        self.coordinates = {"x": 0, "y": 0, "z": 0}
        self.scene_description = ""
        self.npcs_present = []
        self.events = []
        self.messages = []
        self.combat = False
        self.language = "pt-br"
        self.world_map = {
            "locations": {},
            "discovered": {}
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the game state to a dictionary."""
        return {
            "current_location": self.current_location,
            "location_id": self.location_id,
            "coordinates": self.coordinates,
            "scene_description": self.scene_description,
            "npcs_present": self.npcs_present,
            "events": self.events,
            "messages": self.messages,
            "combat": self.combat,
            "language": self.language,
            "world_map": self.world_map
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameState':
        """Create a game state from a dictionary."""
        state = cls()
        
        # Copy all attributes from the dictionary
        for key, value in data.items():
            if hasattr(state, key):
                setattr(state, key, value)
        
        return state
    
    def add_message(self, message: str) -> None:
        """Add a message to the game state."""
        self.messages.append(message)
        
        # Keep only the last 50 messages
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]
            
    def discover_location(self, location_id: str, location_data: Dict[str, Any]) -> None:
        """
        Discover a new location and add it to the world map.
        
        Args:
            location_id: Unique identifier for the location
            location_data: Location data including coordinates, name, type, etc.
        """
        # Add to locations dictionary
        self.world_map["locations"][location_id] = location_data
        
        # Mark as discovered in the coordinates map
        coords = location_data.get("coordinates", {})
        coord_key = f"{coords.get('x', 0)},{coords.get('y', 0)}"
        self.world_map["discovered"][coord_key] = location_id
        
        # Add a message about discovering the location
        self.add_message(f"Você descobriu {location_data.get('name', 'um novo local')}!")

class GameEngine:
    """Main game engine that processes actions and manages game state."""
    
    def __init__(self):
        """Initialize the game engine."""
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def process_action(self, action: str, details: str, character: Any, 
                      game_state: GameState, ai_client=None) -> Dict[str, Any]:
        """Process a player action."""
        # Atualizar estatísticas de sobrevivência (fome e sede)
        try:
            from core.survival_system import SurvivalSystem
            survival_result = SurvivalSystem.update_survival_stats(character, action)
            
            # Adicionar mensagens de fome/sede se houver
            if survival_result["messages"]:
                for msg in survival_result["messages"]:
                    game_state.add_message(msg)
        except ImportError:
            # Se o sistema de sobrevivência não estiver disponível, continua sem ele
            logger.info("Survival system not available")
        
        # Tentar usar a IA para processar a ação se disponível
        try:
            from ai.game_ai_client import GameAIClient
            game_ai = GameAIClient(ai_client)
            result = game_ai.process_player_action(action, details, character, game_state)
            if result:
                return result
        except ImportError:
            # Se o módulo não estiver disponível, continua com o processamento padrão
            logger.info("AI module not available, using standard action handlers")
            
        # Processamento padrão usando handlers
        action_handler = get_action_handler(action)
        result = action_handler.handle(details, character, game_state)
        
        # Verificar se a ação resultou em descoberta de novo local
        if action == "move" and result.get("success") and result.get("new_location"):
            self._handle_location_discovery(game_state, result)
        
        return result
    
    def _handle_location_discovery(self, game_state: GameState, result: Dict[str, Any]) -> None:
        """
        Handle the discovery of a new location after movement.
        
        Args:
            game_state: Current game state
            result: Action result containing new location info
        """
        new_location = result.get("new_location", "")
        if not new_location:
            return
            
        # Check if this is a new location or an existing one
        location_id = self._get_location_id(new_location)
        
        # If location exists, just update player position
        if location_id in game_state.world_map["locations"]:
            location = game_state.world_map["locations"][location_id]
            game_state.coordinates = location.get("coordinates", game_state.coordinates)
            game_state.current_location = new_location
            game_state.location_id = location_id
            
            # Mark as visited
            location["visited"] = True
            return
            
        # This is a new location, generate it
        new_coords = self._get_new_coordinates(game_state)
        
        # Create location data
        location_data = {
            "id": location_id,
            "name": new_location,
            "type": self._determine_location_type(new_location),
            "coordinates": new_coords,
            "description": result.get("description", ""),
            "visited": True,
            "discovered": True,
            "connections": {}
        }
        
        # Add connection from previous location if applicable
        if game_state.location_id:
            # Determine direction based on coordinates
            direction = self._determine_direction(game_state.coordinates, new_coords)
            
            # Add bidirectional connections
            if game_state.location_id in game_state.world_map["locations"]:
                game_state.world_map["locations"][game_state.location_id]["connections"][direction] = location_id
                location_data["connections"][self._opposite_direction(direction)] = game_state.location_id
        
        # Update game state
        game_state.discover_location(location_id, location_data)
        game_state.coordinates = new_coords
        game_state.current_location = new_location
        game_state.location_id = location_id
    
    def _get_location_id(self, location_name: str) -> str:
        """Generate a location ID from a name."""
        return location_name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
    
    def _get_new_coordinates(self, game_state: GameState) -> Dict[str, int]:
        """
        Generate coordinates for a new location based on current position.
        
        Args:
            game_state: Current game state
            
        Returns:
            Dictionary with x, y coordinates
        """
        # Start with current coordinates
        current_coords = game_state.coordinates
        
        # Try to find an unoccupied adjacent position
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(directions)
        
        for dx, dy in directions:
            new_x = current_coords.get("x", 0) + dx
            new_y = current_coords.get("y", 0) + dy
            
            # Check if this position is already occupied
            coord_key = f"{new_x},{new_y}"
            if coord_key not in game_state.world_map["discovered"]:
                return {"x": new_x, "y": new_y, "z": current_coords.get("z", 0)}
        
        # If all adjacent positions are occupied, try diagonal positions
        diagonals = [(1, 1), (-1, -1), (1, -1), (-1, 1)]
        random.shuffle(diagonals)
        
        for dx, dy in diagonals:
            new_x = current_coords.get("x", 0) + dx
            new_y = current_coords.get("y", 0) + dy
            
            coord_key = f"{new_x},{new_y}"
            if coord_key not in game_state.world_map["discovered"]:
                return {"x": new_x, "y": new_y, "z": current_coords.get("z", 0)}
        
        # If all positions are occupied, just pick a random position further away
        new_x = current_coords.get("x", 0) + random.randint(-2, 2)
        new_y = current_coords.get("y", 0) + random.randint(-2, 2)
        return {"x": new_x, "y": new_y, "z": current_coords.get("z", 0)}
    
    def _determine_location_type(self, location_name: str) -> str:
        """
        Determine the type of location based on its name.
        
        Args:
            location_name: Name of the location
            
        Returns:
            Location type string
        """
        name_lower = location_name.lower()
        
        if any(word in name_lower for word in ["cidade", "city"]):
            return "city"
        elif any(word in name_lower for word in ["aldeia", "vila", "village"]):
            return "village"
        elif any(word in name_lower for word in ["floresta", "bosque", "forest", "woods"]):
            return "forest"
        elif any(word in name_lower for word in ["montanha", "mountain", "pico", "peak"]):
            return "mountain"
        elif any(word in name_lower for word in ["caverna", "cave", "gruta"]):
            return "cave"
        elif any(word in name_lower for word in ["ruína", "ruinas", "ruins"]):
            return "ruins"
        elif any(word in name_lower for word in ["templo", "temple", "santuário", "sanctuary"]):
            return "temple"
        elif any(word in name_lower for word in ["castelo", "castle", "fortaleza", "fortress"]):
            return "castle"
        elif any(word in name_lower for word in ["taverna", "tavern", "inn", "estalagem"]):
            return "tavern"
        elif any(word in name_lower for word in ["loja", "shop", "mercado", "market"]):
            return "shop"
        else:
            return "unknown"
    
    def _determine_direction(self, from_coords: Dict[str, int], to_coords: Dict[str, int]) -> str:
        """
        Determine the direction from one set of coordinates to another.
        
        Args:
            from_coords: Starting coordinates
            to_coords: Ending coordinates
            
        Returns:
            Direction string (north, south, east, west)
        """
        dx = to_coords.get("x", 0) - from_coords.get("x", 0)
        dy = to_coords.get("y", 0) - from_coords.get("y", 0)
        
        if abs(dx) > abs(dy):
            # East-west movement is dominant
            return "east" if dx > 0 else "west"
        else:
            # North-south movement is dominant
            return "north" if dy > 0 else "south"
    
    def _opposite_direction(self, direction: str) -> str:
        """Get the opposite of a direction."""
        opposites = {
            "north": "south",
            "south": "north",
            "east": "west",
            "west": "east"
        }
        return opposites.get(direction, "unknown")
        
    def create_game_state(self, character: Any) -> GameState:
        """Create a new game state for a character."""
        return self.generate_random_start()
        
    def load_game_state(self, data: Dict[str, Any]) -> GameState:
        """Load a game state from data."""
        return GameState.from_dict(data)
    
    def generate_random_start(self, language: str = 'pt-br') -> GameState:
        """Generate a random starting game state."""
        # Create a new game state
        game_state = GameState()
        game_state.language = language
        
        # Lista de possíveis cenários iniciais
        starting_scenarios = [
            {
                "location": "Aldeia de Rivenbrook",
                "location_id": "village_center",
                "description": "Você está no centro de uma pequena aldeia chamada Rivenbrook. Há uma taverna ao norte chamada 'O Javali Dourado', uma ferraria a leste, e o portão da aldeia ao sul.",
                "npcs": ["Ancião da Aldeia", "Mercador Viajante"],
                "events": ["Uma brisa suave sopra pela aldeia."],
                "welcome": "Bem-vindo a Rivenbrook! Você pode explorar usando as ações abaixo.",
                "type": "village"
            },
            {
                "location": "Floresta Sombria",
                "location_id": "dark_forest_entrance",
                "description": "Você se encontra na entrada de uma densa floresta. Os galhos das árvores formam um dossel que bloqueia grande parte da luz solar. Um caminho estreito serpenteia entre as árvores, e sons misteriosos ecoam ao seu redor.",
                "npcs": ["Caçador Solitário"],
                "events": ["Um corvo observa você de um galho próximo.", "Folhas secas farfalham com o vento."],
                "welcome": "A Floresta Sombria guarda muitos segredos. Tenha cuidado por onde anda.",
                "type": "forest"
            },
            {
                "location": "Ruínas de Eldrath",
                "location_id": "ancient_ruins",
                "description": "Você está entre as ruínas de uma antiga civilização. Colunas de pedra quebradas e estátuas parcialmente destruídas se erguem ao seu redor. O ar parece pesado com história e magia residual.",
                "npcs": ["Arqueólogo Estudioso", "Espírito Inquieto"],
                "events": ["Poeira mágica brilha no ar.", "Um sussurro incompreensível ecoa entre as pedras."],
                "welcome": "As ruínas de Eldrath são um local de grande poder e perigo. Que segredos você descobrirá aqui?",
                "type": "ruins"
            },
            {
                "location": "Porto de Maré Alta",
                "location_id": "harbor_docks",
                "description": "O cheiro de sal e peixe preenche o ar no movimentado porto. Navios de vários tamanhos estão ancorados nos cais, e marinheiros trabalham carregando e descarregando mercadorias. Tavernas e lojas de suprimentos alinham-se ao longo do calçadão.",
                "npcs": ["Capitão do Porto", "Marinheiro Bêbado", "Mercadora de Especiarias"],
                "events": ["Gaivotas sobrevoam o porto em busca de restos de comida.", "Um navio acaba de atracar."],
                "welcome": "O Porto de Maré Alta conecta este reino a terras distantes. Quem sabe que oportunidades você encontrará aqui?",
                "type": "city"
            },
            {
                "location": "Montanhas Geladas",
                "location_id": "frozen_peaks",
                "description": "O ar rarefeito e gelado das montanhas corta como facas. Você está em um platô rochoso com vista para vales cobertos de neve. Picos imponentes se erguem ao seu redor, e o vento uiva incessantemente.",
                "npcs": ["Guia Montanhês", "Eremita das Neves"],
                "events": ["Uma avalanche distante ecoa pelo vale.", "Pegadas misteriosas marcam a neve ao seu redor."],
                "welcome": "Poucos aventureiros se atrevem a explorar as Montanhas Geladas. Prepare-se para desafios mortais e descobertas incríveis.",
                "type": "mountain"
            }
        ]
        
        # Escolhe um cenário aleatório
        scenario = random.choice(starting_scenarios)
        
        # Configura o estado do jogo com base no cenário escolhido
        game_state.current_location = scenario["location"]
        game_state.location_id = scenario["location_id"]
        game_state.scene_description = scenario["description"]
        game_state.npcs_present = scenario["npcs"]
        game_state.events = scenario["events"]
        game_state.add_message(scenario["welcome"])
        
        # Inicializa o mapa do mundo com a localização inicial
        location_data = {
            "id": scenario["location_id"],
            "name": scenario["location"],
            "type": scenario["type"],
            "coordinates": {"x": 0, "y": 0, "z": 0},
            "description": scenario["description"],
            "visited": True,
            "discovered": True,
            "connections": {}
        }
        
        game_state.world_map["locations"][scenario["location_id"]] = location_data
        game_state.world_map["discovered"]["0,0"] = scenario["location_id"]
        
        return game_state