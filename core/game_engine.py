"""
Game engine module for handling game state and actions."""

import os
import random
from typing import Dict, List, Any, Optional, TypedDict, cast
from dataclasses import dataclass, field
from core.actions import ActionHandler, DefaultActionHandler
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
    connections: Dict[str, str]
    events: List[str]
    welcome: str


@dataclass
class GameState:
    """Represents the current state of the game."""
    current_location: str = ""
    scene_description: str = ""
    npcs_present: List[str] = field(default_factory=list)
    known_npcs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    messages: List[str] = field(default_factory=list)
    coordinates: LocationCoords = field(
        default_factory=lambda: {"x": 0, "y": 0}
    )
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

    def discover_location(
        self, location_id: str, location_data: LocationData
    ) -> None:
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
            self,
            npc_id: str,
            change: int,
            max_value: int = 100) -> None:
        """Update relationship with an NPC."""
        current = self.npc_relationships.get(npc_id, 0)
        self.npc_relationships[npc_id] = max(
            -max_value,
            min(max_value, current + change)
        )


class GameEngine:
    """Main game engine that processes actions and manages game state."""

    def __init__(self) -> None:
        """Initialize the game engine."""
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def process_action(
            self,
            action: str,
            details: str,
            character: Character,
            game_state: GameState,
            action_handler: Optional[ActionHandler] = None,
            ai_client=None) -> Dict[str, Any]:
        """Process a player action."""
        game_state.current_action = action

        # Check survival conditions
        try:
            from core.survival_system import SurvivalSystem
            survival = SurvivalSystem()
            result = survival.update_survival_stats(character, action)
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
                    game_state=game_state
                )
                return cast(Dict[str, Any], ai_result)
            except ImportError:
                pass

        # Use standard handler
        handler = action_handler or DefaultActionHandler()
        result = handler.handle(details, character, game_state)

        # Handle movement
        move_success = result.get("success", False)
        new_location = result.get("new_location")

        if action == "move" and move_success and new_location:
            self._update_location(game_state, new_location)
        else:
            self._generate_location(game_state, result)

        return result

    def _update_location(
            self,
            game_state: GameState,
            new_location: str) -> None:
        """Update the game state for a known location."""
        if loc := game_state.discovered_locations.get(new_location):
            game_state.current_location = new_location
            if coords := loc.get("coordinates"):
                game_state.coordinates = cast(LocationCoords, coords)
            if not loc.get("visited"):
                loc["visited"] = True
            return

        self._generate_location(game_state, {"new_location": new_location})

    def _generate_location(
            self,
            game_state: GameState,
            result: Dict[str, Any]) -> None:
        """Generate a new location when moving to unexplored area."""
        new_coords = self._get_new_coordinates(game_state)
        loc_id = result.get(
            "new_location",
            f"loc_{new_coords['x']}_{new_coords['y']}"
        )

        location_data: LocationData = {
            "name": result.get("location_name", "Nova Área"),
            "coordinates": new_coords,
            "type": self._determine_location_type(loc_id),
            "description": result.get("description", ""),
            "visited": True,
            "connections": {},
        }

        for loc_id, loc in game_state.discovered_locations.items():
            if coords := loc.get("coordinates"):
                if direction := self._get_direction(
                    coords,
                    new_coords,
                ):
                    # Add bidirectional connections
                    location_data["connections"][loc_id] = direction
                    if conns := loc.get("connections"):
                        if isinstance(conns, dict):
                            conns[loc_id] = self._opposite_direction(
                                direction
                            )
                    else:
                        loc["connections"] = {
                            loc_id: self._opposite_direction(direction)
                        }

        game_state.discover_location(loc_id, location_data)
        game_state.current_location = loc_id
        game_state.coordinates = new_coords

    def _get_new_coordinates(
            self,
            game_state: GameState) -> LocationCoords:
        """Generate coordinates for a new location."""
        current = game_state.coordinates
        x, y = current["x"], current["y"]

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            new_x = x + dx
            new_y = y + dy
            if self._is_valid_location(new_x, new_y, game_state):
                return {"x": new_x, "y": new_y}

        diagonals = [(1, 1), (-1, -1), (1, -1), (-1, 1)]
        random.shuffle(diagonals)

        for dx, dy in diagonals:
            new_x = x + dx
            new_y = y + dy
            if self._is_valid_location(new_x, new_y, game_state):
                return {"x": new_x, "y": new_y}

        while True:
            new_x = x + random.randint(-2, 2)
            new_y = y + random.randint(-2, 2)
            if self._is_valid_location(new_x, new_y, game_state):
                return {"x": new_x, "y": new_y}

    def _is_valid_location(
            self,
            x: int,
            y: int,
            game_state: GameState) -> bool:
        """Check if coordinates are valid for a new location."""
        return not any(
            loc.get("coordinates", {}).get("x") == x
            and loc.get("coordinates", {}).get("y") == y
            for loc in game_state.discovered_locations.values()
        )

    def _get_direction(
            self,
            from_coords: LocationCoords,
            to_coords: LocationCoords) -> Optional[str]:
        """Get cardinal direction between two coordinates."""
        dx = to_coords["x"] - from_coords["x"]
        dy = to_coords["y"] - from_coords["y"]

        if abs(dx) > abs(dy):
            return "east" if dx > 0 else "west"
        elif dy != 0:
            return "north" if dy > 0 else "south"
        return None

    def _determine_location_type(self, name: str) -> str:
        """Determine location type from name."""
        name_lower = name.lower()

        types = {
            "village": ["vila", "aldeia", "povoado"],
            "mountain": ["montanha", "pico"],
            "forest": ["floresta", "bosque"],
            "shop": ["loja", "mercado"]
        }

        for loc_type, keywords in types.items():
            if any(word in name_lower for word in keywords):
                return loc_type

        return "wilderness"

    def _opposite_direction(self, direction: str) -> str:
        """Get opposite cardinal direction."""
        opposites = {
            "north": "south",
            "south": "north",
            "east": "west",
            "west": "east"
        }
        return opposites.get(direction, direction)

    def create_game_state(
            self,
            character_id: str,
            language: str = "pt") -> GameState:
        """Create a new game state for a character."""
        initial_location: LocationData = {
            "name": "Centro da Vila",
            "type": "village",
            "description": (
                "Você está no centro da pequena aldeia de Rivenbrook."
            ),
            "coordinates": {"x": 0, "y": 0},
            "visited": True,
            "events": ["Uma brisa suave sopra pela aldeia."],
            "welcome": "Bem-vindo a Rivenbrook!"
        }

        initial_npcs = {
            "guarda": {
                "name": "Guarda da Vila",
                "location": "centro_da_vila",
                "profession": "Guardião"
            },
            "comerciante": {
                "name": "Comerciante",
                "location": "centro_da_vila",
                "profession": "Mercador"
            }
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
