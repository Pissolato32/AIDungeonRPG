"""
Game engine module for handling game state and actions."""

import os
import random
from typing import Dict, List, Any, Optional, TypedDict, cast
from dataclasses import dataclass, field
from core.actions import ActionHandler
from core.models import Character
from core.npc import NPC


class LocationCoords(TypedDict):
    """Type definition for location coordinates."""

    x: int
    y: int


class LocationData(TypedDict, total=False):
    """Type definition for location data."""

    name: str
    type: str
    description: str
    coordinates: LocationCoords
    visited: bool
    connections: Dict[str, str]  # conexões com outras localizações (id: direção)
    resources: Optional[Dict[str, int]]
    danger_level: Optional[int]
    events: List[str]
    welcome: Optional[str]


@dataclass
class GameState:
    """Represents the current state of the game."""

    current_location: str = ""
    scene_description: str = ""
    npcs_present: List[str] = field(default_factory=list)
    known_npcs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    messages: List[str] = field(default_factory=list)
    coordinates: LocationCoords = field(default_factory=lambda: {"x": 0, "y": 0})
    language: str = "pt"
    current_action: str = ""
    discovered_locations: Dict[str, LocationData] = field(default_factory=dict)
    npcs_by_location: Dict[str, List[str]] = field(default_factory=dict)
    npc_relationships: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to a dictionary."""
        return {
            "current_location": self.current_location,
            "scene_description": self.scene_description,
            "npcs_present": self.npcs_present,
            "known_npcs": self.known_npcs,
            "messages": self.messages,
            "coordinates": self.coordinates,
            "language": self.language,
            "current_action": self.current_action,
            "discovered_locations": self.discovered_locations,
            "npcs_by_location": self.npcs_by_location,
            "npc_relationships": self.npc_relationships,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        """Create GameState from dictionary data."""
        return cls(
            current_location=data.get("current_location", ""),
            scene_description=data.get("scene_description", ""),
            npcs_present=data.get("npcs_present", []),
            known_npcs=data.get("known_npcs", {}),
            messages=data.get("messages", []),
            coordinates=data.get("coordinates", {"x": 0, "y": 0}),
            language=data.get("language", "pt"),
            current_action=data.get("current_action", ""),
            discovered_locations=data.get("discovered_locations", {}),
            npcs_by_location=data.get("npcs_by_location", {}),
            npc_relationships=data.get("npc_relationships", {}),
        )

    def add_message(self, message: str) -> None:
        """Add a message to game state history."""
        self.messages.append(message)
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]

    def discover_location(self, location_id: str, location_data: LocationData) -> None:
        """Add a new discovered location."""
        self.discovered_locations[location_id] = location_data
        self.add_message(
            f"Você descobriu {location_data.get('name', 'um novo local')}!"
        )

    def add_npc(self, npc_id: str, npc: Dict[str, Any]) -> None:
        """Add or update an NPC in the game state."""
        self.known_npcs[npc_id] = npc

        if location := npc.get("location"):
            if location not in self.npcs_by_location:
                self.npcs_by_location[location] = []
            self.npcs_by_location[location].append(npc_id)

    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Get an NPC by ID."""
        if npc_data := self.known_npcs.get(npc_id):
            return NPC(**npc_data)
        return None

    def get_npcs_in_location(self, location: str) -> List[NPC]:
        """Get all NPCs in a specific location."""
        npc_ids = self.npcs_by_location.get(location, [])
        return [
            NPC(**self.known_npcs[npc_id])
            for npc_id in npc_ids
            if npc_id in self.known_npcs
        ]

    def update_npc_relationship(
        self, npc_id: str, change: int, max_value: int = 100
    ) -> None:
        """Update relationship with an NPC."""
        current = self.npc_relationships.get(npc_id, 0)
        self.npc_relationships[npc_id] = max(
            -max_value, min(max_value, current + change)
        )


class GameEngine:
    """Main game engine that processes actions and manages game state."""

    def __init__(self) -> None:
        """Initialize the game engine."""
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self._location_cache: Dict[str, Dict[str, Any]] = {}
        self._location_types: Dict[str, List[str]] = {
            "village": ["vila", "aldeia", "povoado"],
            "mountain": ["montanha", "pico", "cordilheira"],
            "forest": ["floresta", "bosque", "mata"],
            "shop": ["loja", "mercado", "feira"],
            "dungeon": ["dungeon", "caverna", "ruína"],
            "camp": ["acampamento", "posto avançado"],
            "temple": ["templo", "santuário", "igreja"],
        }

    def process_action(
        self,
        action: str,
        details: str,
        character: Character,
        game_state: GameState,
        action_handler: Optional[ActionHandler] = None,
        ai_client=None,
    ) -> Dict[str, Any]:
        """Process a player action."""
        game_state.current_action = action

        # Check survival conditions
        try:
            from core.survival_system import SurvivalSystem

            survival = SurvivalSystem()
            result = survival.update_stats(character, action)
            if messages := result.get("messages", []):
                for msg in messages:
                    game_state.add_message(msg)
        except (ImportError, AttributeError):
            pass

        # Process through AI if available
        if ai_client is not None:
            try:
                from ai.game_ai_client import GameAIClient

                game_ai = GameAIClient(ai_client)
                ai_result = game_ai.process_action(
                    action=action,
                    details=details,
                    character=character,
                    game_state=game_state,
                )
                return cast(Dict[str, Any], ai_result)
            except ImportError:
                pass

        # Use standard handler
        handler = action_handler or ActionHandler()
        result = handler.handle(details, character, game_state)

        # Handle movement
        move_success = result.get("success", False)
        new_location = result.get("new_location")

        if action == "move" and move_success and new_location:
            self._update_location(game_state, new_location)
        else:
            self._generate_location(game_state, result)

        return result

    def _update_location(self, game_state: GameState, new_location: str) -> None:
        """Update the game state for a known location."""
        if loc := game_state.discovered_locations.get(new_location):
            game_state.current_location = new_location
            if coords := loc.get("coordinates"):
                game_state.coordinates = cast(LocationCoords, coords)
            if not loc.get("visited"):
                loc["visited"] = True
            return

        self._generate_location(game_state, {"new_location": new_location})

    def _get_new_coordinates(self, game_state: GameState) -> LocationCoords:
        """Generate coordinates for a new location."""
        current = game_state.coordinates
        x, y = current["x"], current["y"]

        # Try adjacent positions first
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            new_x = x + dx
            new_y = y + dy
            if self._is_valid_location(new_x, new_y, game_state):
                return {"x": new_x, "y": new_y}

        # Try diagonal positions next
        diagonals = [(1, 1), (-1, -1), (1, -1), (-1, 1)]
        random.shuffle(diagonals)

        for dx, dy in diagonals:
            new_x = x + dx
            new_y = y + dy
            if self._is_valid_location(new_x, new_y, game_state):
                return {"x": new_x, "y": new_y}

        # If no adjacent positions are available, try random positions
        max_attempts = 10
        for _ in range(max_attempts):
            new_x = x + random.randint(-2, 2)
            new_y = y + random.randint(-2, 2)
            if self._is_valid_location(new_x, new_y, game_state):
                return {"x": new_x, "y": new_y}

        # Fallback to a guaranteed new position
        while True:
            new_x = x + random.randint(-5, 5)
            new_y = y + random.randint(-5, 5)
            if self._is_valid_location(new_x, new_y, game_state):
                return {"x": new_x, "y": new_y}

    def _is_valid_location(self, x: int, y: int, game_state: GameState) -> bool:
        """Check if coordinates are valid for a new location."""
        # Check if location already exists
        for loc in game_state.discovered_locations.values():
            coords = loc.get("coordinates", {})
            if coords.get("x") == x and coords.get("y") == y:
                return False

        # Add additional validation as needed
        # Example: Check map boundaries, terrain restrictions, etc.
        return True

    def _determine_location_type(self, name: str) -> str:
        """Determine location type from name."""
        name_lower = name.lower()

        # Check for each location type
        for loc_type, keywords in self._location_types.items():
            if any(word in name_lower for word in keywords):
                return loc_type

        # Default to random type if no matches
        return random.choice(list(self._location_types.keys()))

    def _get_direction(
        self, from_coords: LocationCoords, to_coords: LocationCoords
    ) -> Optional[str]:
        """Get cardinal direction between two coordinates."""
        dx = to_coords["x"] - from_coords["x"]
        dy = to_coords["y"] - from_coords["y"]

        if abs(dx) > abs(dy):
            return "east" if dx > 0 else "west"
        elif dy != 0:
            return "north" if dy > 0 else "south"
        return None

    def _opposite_direction(self, direction: str) -> str:
        """Get opposite cardinal direction."""
        opposites = {"north": "south", "south": "north", "east": "west", "west": "east"}
        return opposites.get(direction, direction)

    def _generate_location(self, game_state: GameState, result: Dict[str, Any]) -> None:
        """Generate a new location when moving to unexplored area."""
        coords = game_state.coordinates
        cache_key = f"{coords['x']},{coords['y']}"

        if cache_key in self._location_cache:
            cached = self._location_cache[cache_key]
            game_state.discover_location(cached["id"], cached["data"])
            game_state.current_location = cached["id"]
            return

        new_coords = self._get_new_coordinates(game_state)
        loc_id = result.get("new_location", f"loc_{new_coords['x']}_{new_coords['y']}")

        location_data = self._create_location_data(result, new_coords, loc_id)
        self._handle_connections(game_state, location_data, new_coords, loc_id)

        # Cache the location
        self._location_cache[cache_key] = {"id": loc_id, "data": location_data}

        game_state.discover_location(loc_id, location_data)
        game_state.current_location = loc_id
        game_state.coordinates = new_coords

    def _create_location_data(
        self, result: Dict[str, Any], new_coords: LocationCoords, loc_id: str
    ) -> LocationData:
        """Create location data from the result and new coordinates."""
        location_type = self._determine_location_type(loc_id)
        return {
            "name": result.get(
                "location_name", self._generate_location_name(location_type)
            ),
            "coordinates": new_coords,
            "type": location_type,
            "description": result.get(
                "description", self._generate_location_description(location_type)
            ),
            "visited": True,
            "connections": {},
            "resources": self._generate_location_resources(location_type),
            "danger_level": random.randint(1, 5),
            "events": self._generate_location_events(location_type),
        }

    def _handle_connections(
        self,
        game_state: GameState,
        location_data: LocationData,
        new_coords: LocationCoords,
        loc_id: str,
    ) -> None:
        """Establish connections between the new location and existing locations."""
        if "connections" not in location_data:
            location_data["connections"] = {}

        for existing_id, loc in game_state.discovered_locations.items():
            if coords := loc.get("coordinates"):
                direction = self._get_direction(coords, new_coords)
                if direction:
                    location_data["connections"][existing_id] = direction
                    loc["connections"] = loc.get("connections", {})
                    opp_dir = self._opposite_direction(direction)
                    loc["connections"][loc_id] = opp_dir

    def _generate_location_name(self, location_type: str) -> str:
        """Generate a thematic name for the location."""
        prefixes = {
            "village": ["Vila", "Aldeia", "Povoado"],
            "mountain": ["Pico", "Monte", "Serra"],
            "forest": ["Floresta", "Bosque", "Mata"],
            "shop": ["Mercado", "Empório", "Feira"],
            "dungeon": ["Caverna", "Ruína", "Cripta"],
            "camp": ["Acampamento", "Posto", "Refúgio"],
            "temple": ["Templo", "Santuário", "Capela"],
        }
        suffixes = [
            "do Norte",
            "do Sul",
            "do Leste",
            "do Oeste",
            "Antiga",
            "Nova",
            "Perdida",
            "Esquecida",
        ]

        prefix = random.choice(prefixes.get(location_type, ["Local"]))
        suffix = random.choice(suffixes)
        return f"{prefix} {suffix}"

    def _generate_location_description(self, location_type: str) -> str:
        """Generate a detailed description for the location."""
        descriptions = {
            "village": (
                "Uma pequena vila com casas rústicas e " "moradores acolhedores."
            ),
            "mountain": "Uma imponente montanha que se ergue até as nuvens.",
            "forest": "Uma densa floresta com árvores antigas e misteriosas.",
            "shop": ("Um movimentado local de comércio com " "mercadorias diversas."),
            "dungeon": "Uma antiga construção que guarda segredos do passado.",
            "camp": "Um posto avançado usado por viajantes e exploradores.",
            "temple": "Um local sagrado de adoração e contemplação.",
        }
        return descriptions.get(location_type, "Um local misterioso e inexplorado.")

    def _generate_location_resources(self, location_type: str) -> List[str]:
        """Generate available resources for the location."""
        resources = {
            "village": ["água", "comida", "ferramentas"],
            "mountain": ["minérios", "cristais", "ervas raras"],
            "forest": ["madeira", "frutas", "ervas medicinais"],
            "shop": ["equipamentos", "poções", "itens mágicos"],
            "dungeon": ["tesouros", "artefatos", "relíquias"],
            "camp": ["suprimentos", "mapas", "informações"],
            "temple": ["bênçãos", "curas", "conhecimento"],
        }
        available = resources.get(location_type, ["recursos desconhecidos"])
        return random.sample(available, k=random.randint(1, min(3, len(available))))

    def _generate_location_events(self, location_type: str) -> List[str]:
        """Generate random events for the location."""
        events = {
            "village": [
                "Festival local em andamento",
                "Mercadores visitantes chegaram",
                "Reunião do conselho",
            ],
            "mountain": [
                "Avalanche recente",
                "Dragão avistado",
                "Expedição de mineração",
            ],
            "forest": [
                "Criaturas místicas próximas",
                "Chuva de flores mágicas",
                "Caçadores acampados",
            ],
            "shop": [
                "Promoção especial",
                "Itens raros disponíveis",
                "Negociações tensas",
            ],
            "dungeon": ["Sons misteriosos", "Luzes estranhas", "Portas seladas"],
            "camp": [
                "Viajantes descansando",
                "Histórias sendo compartilhadas",
                "Preparativos para jornada",
            ],
            "temple": [
                "Ritual em andamento",
                "Peregrinos chegando",
                "Meditação coletiva",
            ],
        }
        available = events.get(location_type, ["Nada de notável acontecendo"])
        return random.sample(available, k=random.randint(1, min(2, len(available))))

    def create_game_state(self, character_id: str, language: str = "pt") -> GameState:
        """Create a new game state for a character."""
        initial_location: LocationData = {
            "name": "Centro da Vila",
            "type": "village",
            "description": ("Você está no centro da pequena aldeia de Rivenbrook."),
            "coordinates": {"x": 0, "y": 0},
            "visited": True,
            "events": ["Uma brisa suave sopra pela aldeia."],
            "welcome": "Bem-vindo a Rivenbrook!",
        }

        initial_npcs = {
            "guarda": {
                "name": "Guarda da Vila",
                "location": "centro_da_vila",
                "profession": "Guardião",
            },
            "comerciante": {
                "name": "Comerciante",
                "location": "centro_da_vila",
                "profession": "Mercador",
            },
        }

        state = GameState()
        state.language = language
        state.current_location = "centro_da_vila"
        state.discovered_locations["centro_da_vila"] = initial_location

        for npc_id, npc_data in initial_npcs.items():
            state.add_npc(npc_id, npc_data)
        return state

    def load_game_state(self, data: Dict[str, Any]) -> GameState:
        """Load a game state from saved data."""
        return GameState.from_dict(data)
