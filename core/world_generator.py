"""
World Generator for the RPG game.

This module handles procedural generation of the game world.
"""

import json
import logging
import os
import random
from typing import Any, Dict, List, Optional, Tuple

from ai.groq_client import GroqClient

logger = logging.getLogger(__name__)


class WorldGenerator:
    """Handles procedural generation of the game world."""

    # Tipos de Zonas/Biomas Pós-Apocalípticos
    BIOMES = [
        "ruas devastadas da cidade",
        "zona de quarentena abandonada",
        "esgotos infestados",
        "rodovia destruída",
        "floresta sombria e silenciosa",
        "pântano contaminado",
        "shopping center saqueado",
        "hospital abandonado",
        "complexo industrial em ruínas",
        "área rural desolada",
    ]

    # Tipos de Locais/Assentamentos de Sobreviventes (ou perigosos)
    SETTLEMENT_TYPES = [
        "abrigo subterrâneo",
        "posto avançado de sobreviventes",
        "acampamento de saqueadores",
        "ninho de zumbis",
        "edifício barricado",
        "ponto de controle militar abandonado",
        "fazenda isolada",
        "estação de metrô colapsada",
        "laboratório secreto",
        "zona de evacuação falha",
    ]

    # Prefixos e sufixos para nomes de locais
    NAME_PREFIXES = [
        "Cinza",
        "Eco",
        "Sombra",
        "Ferrugem",
        "Osso",
        "Silêncio",
        "Ruína",
        "Esperança",  # Ocasional
        "Último",
        "Novo",  # Irônico
        "Refúgio",
        "Posto",
        "Zona",
        "Marco",
    ]

    NAME_SUFFIXES = [
        "Zero",
        "Final",
        "Perdido",
        "Esquecido",
        "Morto",
        "Caído",
        "Quebrado",
        "Seguro",  # Ocasional
        "Norte",
        "Sul",
        "Leste",
        "Oeste",  # Funcional
        "Alfa",
        "Beta",
        "Gama",  # Militar
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
                with open(self.world_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading world map: {e}")

        # Return empty world if file doesn't exist or has errors
        return {
            "locations": {},
            "connections": {},
            "metadata": {"version": "1.0", "created": "procedural"},
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
            with open(self.world_file, "w", encoding="utf-8") as f:
                json.dump(world_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving world map: {e}")
            return False

    def generate_location_name(self, location_type: Optional[str] = None) -> str:
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

            adjectives = [  # Adjetivos mais temáticos
                "Abandonada",
                "Devastada",
                "Contaminada",
                "Fortificada",
                "Isolada",
                "Saqueada",
                "Assombrada",
            ]
            elements = [
                "do Norte",
                "do Sul",
                "do Leste",
                "do Oeste",
                "da Montanha",
                "do Esgoto",
                "da Zona Morta",
            ]

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
        possible_starts = [
            "abrigo subterrâneo",
            "edifício barricado",
            "posto avançado de sobreviventes",
        ]
        settlement_type = random.choice(possible_starts)
        location_name = self.generate_location_name(settlement_type)

        # Generate a unique ID for the location
        base_location_id = (
            location_name.lower()
            .replace(" ", "_")
            .replace("ç", "c")
            .replace("ã", "a")
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
        )
        location_id = f"{base_location_id}_0_0"  # Assume starting at 0,0

        # Generate description using AI - ADAPTED PROMPT
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
            "visited": True,
        }

        return location_data

    def generate_location_description(
        self, location_name: str, location_type: str
    ) -> str:
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
        que é um(a) {location_type} em um mundo pós-apocalíptico infestado por zumbis.
        
        A descrição deve ter 2-3 parágrafos e incluir:
        - Aparência visual (destruição, abandono, sinais de luta, pichações de sobreviventes).
        - Atmosfera e sensações (cheiro de podridão, silêncio opressor, sons distantes de zumbis ou tiros).
        - Pistas sobre o que aconteceu ali (sinais de evacuação apressada, barricadas falhas, restos de suprimentos).
        - Alguma característica única que torne o local memorável (um grafite específico, um veículo abandonado de forma peculiar, um perigo óbvio ou uma oportunidade).
        
        Mantenha a descrição imersiva e focada no tema de sobrevivência e perigo.
        """

        try:
            response = self.ai_client.generate_response(prompt)
            if isinstance(response, str) and response.strip():
                return response.strip()
        except Exception as e:
            logger.error(f"Error generating location description: {e}")

        # Fallback description if AI fails
        return f"Um(a) {location_type} chamado(a) {location_name}. O ar é pesado e o silêncio é perturbador. Há sinais de destruição por toda parte."

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
        base_npcs = {  # ADAPTED FOR ZOMBIE APOCALYPSE
            "abrigo subterrâneo": [
                "Líder do Abrigo Tenso",
                "Engenheiro Cansado",
                "Guarda Paranoico",
                "Criança Assustada",
            ],
            "posto avançado de sobreviventes": [
                "Vigia Solitário",
                "Caçador Habilidoso",
                "Negociante Oportunista",
                "Curandeiro Improvisado",
            ],
            "acampamento de saqueadores": [
                "Líder Saqueador Brutal",
                "Capanga Violento",
                "Informante Covarde",
            ],
            "edifício barricado": [
                "Sobrevivente Desconfiado",
                "Família Escondida",
                "Vigia Nervoso",
            ],
            "hospital abandonado": [
                "Médico Enlouquecido",
                "Enfermeira Fantasma (delírio?)",
                "Paciente Infectado (prestes a virar)",
            ],
            "shopping center saqueado": [
                "Saqueador Solitário",
                "Grupo de Sobreviventes Desesperados",
            ],
            "zona de quarentena abandonada": [
                "Soldado Traumatizado",
                "Cientista Arrependido",
            ],
        }

        # Get base NPCs for this location type
        npc_pool = base_npcs.get(
            location_type.lower(), ["Sobrevivente Solitário", "Viajante Desesperado"]
        )

        # Select 1-3 NPCs
        num_npcs = random.randint(1, 3)
        npcs = random.sample(npc_pool, min(num_npcs, len(npc_pool)))

        # Try to generate a unique NPC using AI - ADAPTED PROMPT
        try:
            prompt = f"""
            Gere o nome e uma breve descrição (1 frase) de um personagem NPC único e interessante que poderia ser encontrado em '{location_name}', um(a) {location_type} durante um apocalipse zumbi.
            O personagem deve ter alguma característica ou história implícita que o torne memorável.
            Responda apenas com o nome e a descrição.
            Exemplo: "Corvo, um ex-militar que perdeu seu esquadrão e agora só confia em seu rifle." ou "Lily, uma garotinha que carrega um ursinho de pelúcia manchado de sangue e não fala."
            """

            response = self.ai_client.generate_response(prompt)
            if isinstance(response, str) and response.strip():
                unique_npc = response.strip().split("\n")[0]  # Get first line only
                if unique_npc not in npcs:  # Avoid duplicates if AI gives a base one
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
        # Base events by location type - ADAPTED FOR ZOMBIE APOCALYPSE
        base_events = {
            "abrigo subterrâneo": [
                "O gerador falha por um momento, mergulhando tudo na escuridão antes de voltar.",
                "Alguém chora baixinho em um canto escuro.",
                "Uma discussão tensa sobre os suprimentos restantes pode ser ouvida.",
            ],
            "ruas devastadas da cidade": [
                "Um grupo de corvos bica algo no meio da rua.",
                "O vento uiva através das janelas quebradas dos edifícios.",
                "Um zumbi solitário cambaleia ao longe.",
            ],
            "shopping center saqueado": [
                "Prateleiras vazias e vidros quebrados cobrem o chão.",
                "Um carrinho de compras abandonado bloqueia um corredor.",
                "Um alarme de incêndio defeituoso dispara intermitentemente.",
            ],
            "hospital abandonado": [
                "O cheiro de antisséptico e podridão paira no ar.",
                "Macas viradas e equipamentos médicos espalhados pelo chão.",
                "Um prontuário médico ensanguentado está aberto em uma mesa.",
            ],
        }

        # Get base events for this location type
        event_pool = base_events.get(
            location_type.lower(),
            [
                "O silêncio é quebrado por um som não identificado à distância.",
                "Um rato corre por entre os escombros.",
            ],
        )

        # Select 1-2 events
        num_events = random.randint(1, 2)
        events = random.sample(event_pool, min(num_events, len(event_pool)))

        # Try to generate a unique event using AI - ADAPTED PROMPT
        try:
            prompt = f"""
            Gere uma breve descrição de um evento ou situação interessante e tensa acontecendo em '{location_name}', um(a) {location_type} durante um apocalipse zumbi.
            O evento deve aumentar a sensação de perigo ou desolação.
            Responda com apenas uma frase descritiva, sem explicações adicionais.
            """

            response = self.ai_client.generate_response(prompt)
            if isinstance(response, str) and response.strip():
                unique_event = response.strip().split("\n")[0]  # Get first line only
                if unique_event not in events:
                    events.append(unique_event)
        except Exception as e:
            logger.error(f"Error generating unique event: {e}")

        return events

    def generate_adjacent_location(
        self, current_location_id: str, direction: str, world_data: Dict[str, Any]
    ) -> Dict[str, Any]:
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
            if (
                loc_coords.get("x") == new_coords["x"]
                and loc_coords.get("y") == new_coords["y"]
                and loc_coords.get("z") == new_coords["z"]
            ):
                # Return existing location
                return loc_data

        # Determine location type based on distance from origin
        distance_from_origin = abs(new_coords["x"]) + abs(new_coords["y"])

        if distance_from_origin <= 2:  # Mais próximo do início
            # Áreas urbanas em ruínas, talvez alguns postos avançados
            possible_types = [
                self.BIOMES[0],
                self.BIOMES[1],
                self.SETTLEMENT_TYPES[1],
                self.SETTLEMENT_TYPES[4],
            ]
        elif distance_from_origin <= 5:  # Distância média
            # Mistura de ruínas, áreas industriais, talvez zonas de quarentena
            possible_types = self.BIOMES[:4] + [
                self.SETTLEMENT_TYPES[2],
                self.SETTLEMENT_TYPES[5],
                self.SETTLEMENT_TYPES[8],
            ]
        else:
            # Longe, áreas mais selvagens ou perigosas
            possible_types = self.BIOMES[3:] + [
                self.SETTLEMENT_TYPES[3],
                self.SETTLEMENT_TYPES[9],
            ]

        location_type = random.choice(possible_types)

        # Refine location_type para não ser apenas o nome do bioma se for um bioma
        # Ex: "ruas devastadas da cidade" pode ser apenas "ruas devastadas"
        # Ou "shopping center saqueado" (que é um bioma e um tipo de local)
        if location_type in self.BIOMES and location_type not in self.SETTLEMENT_TYPES:
            # Para biomas puros, o nome do local pode ser mais genérico
            pass  # A geração de nome abaixo cuidará disso

        # Generate name based on type
        is_settlement = location_type in self.SETTLEMENT_TYPES
        if is_settlement:
            location_name = self.generate_location_name(location_type)
        else:
            location_name = f"{random.choice(self.NAME_PREFIXES)} {location_type.capitalize().split(' ')[-1]} {random.choice(self.NAME_SUFFIXES)}"

        # Generate a unique ID for the location
        base_location_id = f"{location_name.lower().replace(' ', '_').replace('ç', 'c').replace('ã', 'a').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')}_{new_coords['x']}_{new_coords['y']}"
        location_id = base_location_id
        counter = 0
        # Ensure ID is unique within world_data, though coordinates should make it mostly unique
        while location_id in world_data["locations"]:
            counter += 1
            location_id = f"{base_location_id}_{counter}"

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
            "visited": False,
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
            "down": "up",
        }
        return opposites.get(direction, "unknown")

    def get_available_directions(
        self, location_id: str, world_data: Dict[str, Any]
    ) -> Dict[str, str]:
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

    def get_location_by_coordinates(
        self, coords: Dict[str, int], world_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
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
            if (
                loc_coords.get("x") == coords["x"]
                and loc_coords.get("y") == coords["y"]
                and loc_coords.get("z") == coords["z"]
            ):
                return loc_data
        return None
