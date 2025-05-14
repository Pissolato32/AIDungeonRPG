"""
World Generator for the RPG game.

This module handles procedural generation of the game world.
"""

import random
import json
import os
import logging
from typing import Dict, List, Any, Tuple, Optional
from groq_client import GroqClient

logger = logging.getLogger(__name__)

class WorldGenerator:
    """Handles procedural generation of the game world."""
    
    # Tipos de biomas para diversidade
    BIOMES = [
        "floresta", "montanha", "planície", "deserto", "pântano", 
        "tundra", "costa", "caverna", "ruínas", "selva"
    ]
    
    # Tipos de assentamentos
    SETTLEMENT_TYPES = [
        "aldeia", "vila", "cidade", "fortaleza", "acampamento", 
        "posto avançado", "porto", "refúgio", "santuário", "colônia"
    ]
    
    # Prefixos e sufixos para nomes de locais
    NAME_PREFIXES = [
        "Riven", "Elder", "Stone", "Oak", "Silver", "Dawn", "Dusk", 
        "Frost", "Shadow", "Ember", "Crystal", "Iron", "Golden", "Mist"
    ]
    
    NAME_SUFFIXES = [
        "brook", "vale", "keep", "haven", "ford", "cross", "wood", 
        "peak", "fall", "ridge", "hollow", "field", "shore", "gate"
    ]
    
    def __init__(self, data_dir: str):
        """
        Initialize the world generator.
        
        Args:
            data_dir: Directory to store world data
        """
        self.data_dir = data_dir
        self.world_file = os.path.join(data_dir, "world_map.json")
        self.ai_client = GroqClient()
    
    def load_world(self) -> Dict[str, Any]:
        """
        Load the world map from file.
        
        Returns:
            World map dictionary
        """
        if os.path.exists(self.world_file):
            try:
                with open(self.world_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading world map: {e}")
        
        # Return empty world if file doesn't exist or has errors
        return {
            "locations": {},
            "connections": {},
            "metadata": {
                "version": "1.0",
                "created": "procedural"
            }
        }
    
    def save_world(self, world_data: Dict[str, Any]) -> bool:
        """
        Save the world map to file.
        
        Args:
            world_data: World map dictionary
            
        Returns:
            Success status
        """
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.world_file, 'w', encoding='utf-8') as f:
                json.dump(world_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving world map: {e}")
            return False
    
    def generate_location_name(self, location_type: str = None) -> str:
        """
        Generate a random location name.
        
        Args:
            location_type: Optional type of location
            
        Returns:
            Generated name
        """
        if random.random() < 0.7:  # 70% chance of compound name
            prefix = random.choice(self.NAME_PREFIXES)
            suffix = random.choice(self.NAME_SUFFIXES)
            return f"{prefix}{suffix}"
        else:  # 30% chance of type-based name
            if not location_type:
                location_type = random.choice(self.SETTLEMENT_TYPES)
            
            adjectives = ["Antiga", "Nova", "Grande", "Pequena", "Alta", "Baixa", "Velha"]
            elements = ["do Norte", "do Sul", "do Leste", "do Oeste", "da Montanha", "do Rio", "da Floresta"]
            
            if random.random() < 0.5:
                return f"{random.choice(adjectives)} {location_type.capitalize()}"
            else:
                return f"{location_type.capitalize()} {random.choice(elements)}"
    
    def generate_starting_location(self) -> Dict[str, Any]:
        """
        Generate a starting location for a new game.
        
        Returns:
            Location data dictionary
        """
        # Choose a settlement type for starting location
        settlement_type = random.choice(self.SETTLEMENT_TYPES[:3])  # Limit to aldeia, vila, cidade
        location_name = self.generate_location_name(settlement_type)
        
        # Generate a unique ID for the location
        location_id = location_name.lower().replace(" ", "_")
        
        # Generate description using AI
        description = self.generate_location_description(location_name, settlement_type)
        
        # Generate NPCs
        npcs = self.generate_npcs(location_name, settlement_type)
        
        # Generate events
        events = self.generate_events(location_name, settlement_type)
        
        # Create location data
        location_data = {
            "id": location_id,
            "name": location_name,
            "type": settlement_type,
            "description": description,
            "npcs": npcs,
            "events": events,
            "coordinates": {"x": 0, "y": 0, "z": 0},  # Starting point is origin
            "connections": {},  # Will be filled as player explores
            "discovered": True,
            "visited": True
        }
        
        return location_data
    
    def generate_location_description(self, location_name: str, location_type: str) -> str:
        """
        Generate a description for a location using AI.
        
        Args:
            location_name: Name of the location
            location_type: Type of location
            
        Returns:
            Generated description
        """
        prompt = f"""
        Gere uma descrição detalhada e atmosférica para um local chamado '{location_name}', 
        que é um(a) {location_type} em um mundo de fantasia medieval.
        
        A descrição deve ter 2-3 parágrafos e incluir:
        - Aparência visual e arquitetura
        - Atmosfera e sensações (sons, cheiros, etc.)
        - Elementos culturais ou históricos interessantes
        - Alguma característica única que torne o local memorável
        
        Mantenha a descrição imersiva e evite mencionar elementos modernos.
        """
        
        try:
            response = self.ai_client.generate_response(prompt)
            if isinstance(response, str) and response.strip():
                return response.strip()
        except Exception as e:
            logger.error(f"Error generating location description: {e}")
        
        # Fallback description if AI fails
        return f"Um(a) {location_type} chamado(a) {location_name}. O local parece tranquilo e acolhedor."
    
    def generate_npcs(self, location_name: str, location_type: str) -> List[str]:
        """
        Generate NPCs for a location.
        
        Args:
            location_name: Name of the location
            location_type: Type of location
            
        Returns:
            List of NPC names
        """
        # Base NPCs by location type
        base_npcs = {
            "aldeia": ["Ancião da Aldeia", "Ferreiro", "Comerciante", "Fazendeiro", "Caçador"],
            "vila": ["Prefeito", "Guarda", "Mercador", "Estalajadeiro", "Artesão"],
            "cidade": ["Nobre", "Capitão da Guarda", "Mercador Rico", "Sacerdote", "Mago da Corte"],
            "fortaleza": ["Comandante", "Soldado", "Armeiro", "Sentinela", "Prisioneiro"],
            "acampamento": ["Líder do Acampamento", "Batedor", "Cozinheiro", "Guerreiro", "Xamã"],
            "porto": ["Capitão do Porto", "Marinheiro", "Pescador", "Contrabandista", "Viajante"]
        }
        
        # Get base NPCs for this location type
        npc_pool = base_npcs.get(location_type.lower(), ["Viajante", "Morador", "Guarda"])
        
        # Select 2-4 NPCs
        num_npcs = random.randint(2, 4)
        npcs = random.sample(npc_pool, min(num_npcs, len(npc_pool)))
        
        # Try to generate a unique NPC using AI
        try:
            prompt = f"""
            Gere o nome e ocupação de um personagem NPC único e interessante que vive em {location_name}.
            O personagem deve se encaixar em um mundo de fantasia medieval e ter alguma característica memorável.
            Responda apenas com o nome e ocupação, sem explicações adicionais.
            Exemplo: "Thorne, o Ferreiro de Espadas Mágicas" ou "Elara, Sacerdotisa das Chamas Antigas"
            """
            
            response = self.ai_client.generate_response(prompt)
            if isinstance(response, str) and response.strip():
                unique_npc = response.strip().split('\n')[0]  # Get first line only
                npcs.append(unique_npc)
        except Exception as e:
            logger.error(f"Error generating unique NPC: {e}")
        
        return npcs
    
    def generate_events(self, location_name: str, location_type: str) -> List[str]:
        """
        Generate events for a location.
        
        Args:
            location_name: Name of the location
            location_type: Type of location
            
        Returns:
            List of event descriptions
        """
        # Base events by location type
        base_events = {
            "aldeia": [
                "Uma brisa suave sopra pela aldeia.",
                "Crianças brincam na praça central.",
                "O sino da pequena capela toca ao longe."
            ],
            "vila": [
                "Mercadores organizam suas barracas na praça do mercado.",
                "Guardas patrulham as ruas principais.",
                "Um bardo toca música na taverna local."
            ],
            "cidade": [
                "Nobres passeiam em suas carruagens pelas ruas.",
                "Pregadores anunciam decretos reais na praça central.",
                "Mercadores de terras distantes vendem itens exóticos."
            ]
        }
        
        # Get base events for this location type
        event_pool = base_events.get(location_type.lower(), ["Viajantes passam pelo local.", "O vento sopra suavemente."])
        
        # Select 1-2 events
        num_events = random.randint(1, 2)
        events = random.sample(event_pool, min(num_events, len(event_pool)))
        
        # Try to generate a unique event using AI
        try:
            prompt = f"""
            Gere uma breve descrição de um evento ou situação interessante acontecendo em {location_name}.
            O evento deve ser adequado para um mundo de fantasia medieval e criar uma atmosfera imersiva.
            Responda com apenas uma frase descritiva, sem explicações adicionais.
            """
            
            response = self.ai_client.generate_response(prompt)
            if isinstance(response, str) and response.strip():
                unique_event = response.strip().split('\n')[0]  # Get first line only
                events.append(unique_event)
        except Exception as e:
            logger.error(f"Error generating unique event: {e}")
        
        return events
    
    def generate_adjacent_location(self, current_location_id: str, direction: str, world_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a new location adjacent to the current one.
        
        Args:
            current_location_id: ID of the current location
            direction: Direction of travel (north, south, east, west)
            world_data: Current world data
            
        Returns:
            New location data
        """
        # Get current location data
        current_location = world_data["locations"].get(current_location_id, {})
        current_coords = current_location.get("coordinates", {"x": 0, "y": 0, "z": 0})
        
        # Determine new coordinates based on direction
        new_coords = current_coords.copy()
        if direction == "north":
            new_coords["y"] += 1
        elif direction == "south":
            new_coords["y"] -= 1
        elif direction == "east":
            new_coords["x"] += 1
        elif direction == "west":
            new_coords["x"] -= 1
        
        # Check if there's already a location at these coordinates
        for loc_id, loc_data in world_data["locations"].items():
            loc_coords = loc_data.get("coordinates", {})
            if (loc_coords.get("x") == new_coords["x"] and 
                loc_coords.get("y") == new_coords["y"] and
                loc_coords.get("z") == new_coords["z"]):
                # Return existing location
                return loc_data
        
        # Determine location type based on distance from origin
        distance_from_origin = abs(new_coords["x"]) + abs(new_coords["y"])
        
        if distance_from_origin <= 1:
            # Close to origin - civilized areas
            location_types = self.SETTLEMENT_TYPES[:4]  # aldeia, vila, cidade, fortaleza
        elif distance_from_origin <= 3:
            # Medium distance - mix of settlements and wilderness
            location_types = self.SETTLEMENT_TYPES + [f"{biome}" for biome in self.BIOMES[:5]]
        else:
            # Far from origin - mostly wilderness with occasional settlements
            location_types = [f"{biome}" for biome in self.BIOMES] + self.SETTLEMENT_TYPES[4:]
        
        location_type = random.choice(location_types)
        
        # Generate name based on type
        is_settlement = location_type in self.SETTLEMENT_TYPES
        if is_settlement:
            location_name = self.generate_location_name(location_type)
        else:
            location_name = f"{location_type.capitalize()} de {random.choice(self.NAME_PREFIXES)}{random.choice(self.NAME_SUFFIXES)}"
        
        # Generate a unique ID for the location
        location_id = f"{location_name.lower().replace(' ', '_')}_{new_coords['x']}_{new_coords['y']}"
        
        # Generate description using AI
        description = self.generate_location_description(location_name, location_type)
        
        # Generate NPCs (only for settlements)
        npcs = self.generate_npcs(location_name, location_type) if is_settlement else []
        
        # Generate events
        events = self.generate_events(location_name, location_type)
        
        # Create location data
        location_data = {
            "id": location_id,
            "name": location_name,
            "type": location_type,
            "description": description,
            "npcs": npcs,
            "events": events,
            "coordinates": new_coords,
            "connections": {
                self._get_opposite_direction(direction): current_location_id
            },
            "discovered": True,
            "visited": False
        }
        
        # Update connections in current location
        if "connections" not in current_location:
            current_location["connections"] = {}
        current_location["connections"][direction] = location_id
        
        return location_data
    
    def _get_opposite_direction(self, direction: str) -> str:
        """Get the opposite of a direction."""
        opposites = {
            "north": "south",
            "south": "north",
            "east": "west",
            "west": "east",
            "up": "down",
            "down": "up"
        }
        return opposites.get(direction, "unknown")
    
    def get_available_directions(self, location_id: str, world_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Get available directions from a location.
        
        Args:
            location_id: ID of the location
            world_data: World data
            
        Returns:
            Dictionary of directions and their destination IDs
        """
        location = world_data["locations"].get(location_id, {})
        return location.get("connections", {})
    
    def get_location_by_coordinates(self, coords: Dict[str, int], world_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a location by its coordinates.
        
        Args:
            coords: Coordinates dictionary with x, y, z
            world_data: World data
            
        Returns:
            Location data or None if not found
        """
        for loc_id, loc_data in world_data["locations"].items():
            loc_coords = loc_data.get("coordinates", {})
            if (loc_coords.get("x") == coords["x"] and 
                loc_coords.get("y") == coords["y"] and
                loc_coords.get("z") == coords["z"]):
                return loc_data
        return None