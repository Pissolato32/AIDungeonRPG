"""
Game engine module for handling game state and actions."""

import json
import os
import random
from typing import Any, Dict, List, Optional, cast

# Assume GameAIClient is in ai.game_ai_client, adjust if necessary
from ai.game_ai_client import GameAIClient

# Assume ActionHandler is in core.actions, adjust if necessary
from core.actions import ActionHandler
from core.models import Character

from .game_state_model import GameState, LocationCoords, LocationData


class GameEngine:
    """Main game engine that processes actions and manages game state."""

    def __init__(self) -> None:
        """Initialize the game engine."""
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self._location_cache: Dict[str, Dict[str, Any]] = {}
        # Updated location types for zombie apocalypse
        self._location_types: Dict[str, List[str]] = {
            "abrigo": ["abrigo subterrâneo", "bunker", "refúgio seguro"],
            "ruina_urbana": [
                "ruas devastadas",
                "prédio abandonado",
                "zona comercial saqueada",
            ],
            "posto_avancado": ["posto de controle", "acampamento de sobreviventes"],
            "zona_perigosa": [
                "ninho de zumbis",
                "área contaminada",
                "hospital infestado",
            ],
            "natureza_selvagem": [
                "floresta silenciosa",
                "estrada abandonada",
                "fazenda isolada",
            ],
        }

    def _get_save_path(self, user_id: str, data_type: str) -> str:
        """Helper to get the save file path."""
        return os.path.join(self.data_dir, f"{user_id}_{data_type}.json")

    def save_character(self, user_id: str, character: Character) -> None:
        """Save character data to a file."""
        path = self._get_save_path(user_id, "character")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(character.to_dict(), f, indent=2)
        except IOError as e:
            # Log error
            print(
                f"Error saving character for {user_id}: {e}"
            )  # Replace with proper logging

    def load_character(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load character data from a file."""
        path = self._get_save_path(user_id, "character")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                # Log error
                print(
                    f"Error loading character for {user_id}: {e}"
                )  # Replace with proper logging
        return None

    def delete_character(self, user_id: str) -> None:
        """Delete character data file."""
        path = self._get_save_path(user_id, "character")
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError as e:
                # Log error
                print(
                    f"Error deleting character file for {user_id}: {e}"
                )  # Replace with proper logging

    def save_game_state(self, user_id: str, game_state: GameState) -> None:
        """Save game state data to a file."""
        path = self._get_save_path(user_id, "gamestate")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(game_state.to_dict(), f, indent=2)
        except IOError as e:
            # Log error
            print(
                f"Error saving game state for {user_id}: {e}"
            )  # Replace with proper logging

    def load_game_state(self, user_id: str) -> Optional[GameState]:
        """Load game state data from a file."""
        path = self._get_save_path(user_id, "gamestate")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return GameState.from_dict(data)
            except (IOError, json.JSONDecodeError) as e:
                # Log error
                print(
                    f"Error loading game state for {user_id}: {e}"
                )  # Replace with proper logging
        return None

    def delete_game_state(self, user_id: str) -> None:
        """Delete game state data file."""
        path = self._get_save_path(user_id, "gamestate")
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError as e:
                # Log error
                print(
                    f"Error deleting game state file for {user_id}: {e}"
                )  # Replace with proper logging

    def process_action(
        self,
        action: str,
        details: str,
        character: Character,
        game_state: GameState,
        action_handler: Optional[
            ActionHandler
        ] = None,  # ActionHandler should be imported
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
                # GameAIClient should be imported at the top level

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
            if coords := loc.get("coordinates"):  # Ensure coordinates exist
                game_state.coordinates = cast(LocationCoords, coords)
            if not loc.get("visited"):
                loc["visited"] = True
            return

        self._generate_location(game_state, {"new_location": new_location})

    def _get_new_coordinates(self, game_state: GameState) -> LocationCoords:
        """Generate coordinates for a new location."""
        current = game_state.coordinates
        x, y, z = (
            current.get("x", 0),
            current.get("y", 0),
            current.get("z", 0),
        )  # Handle missing z

        # Try adjacent positions first
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            new_x = x + dx
            new_y = y + dy
            if self._is_valid_location(new_x, new_y, z, game_state):  # Pass z
                return {"x": new_x, "y": new_y, "z": z}

        # Try diagonal positions next
        diagonals = [(1, 1), (-1, -1), (1, -1), (-1, 1)]
        random.shuffle(diagonals)

        for dx, dy in diagonals:
            new_x = x + dx
            new_y = y + dy
            if self._is_valid_location(new_x, new_y, z, game_state):  # Pass z
                return {"x": new_x, "y": new_y, "z": z}

        # If no adjacent positions are available, try random positions
        max_attempts = 10
        for _ in range(max_attempts):
            new_x = x + random.randint(-2, 2)
            new_y = y + random.randint(-2, 2)
            if self._is_valid_location(new_x, new_y, z, game_state):  # Pass z
                return {"x": new_x, "y": new_y, "z": z}

        # Fallback to a guaranteed new position
        while True:
            new_x = x + random.randint(-5, 5)
            new_y = y + random.randint(-5, 5)
            if self._is_valid_location(new_x, new_y, z, game_state):  # Pass z
                return {"x": new_x, "y": new_y, "z": z}

    def _is_valid_location(self, x: int, y: int, z: int, game_state: GameState) -> bool:
        """Check if coordinates are valid for a new location."""
        # Check if location already exists
        for loc in game_state.discovered_locations.values():
            coords = loc.get("coordinates", {})
            if coords.get("x") == x and coords.get("y") == y and coords.get("z") == z:
                return False
        # Add additional validation as needed
        # Example: Check map boundaries, terrain restrictions, etc.
        return True

    def _get_direction(
        self, from_coords: LocationCoords, to_coords: LocationCoords
    ) -> Optional[str]:
        """Get cardinal direction between two coordinates."""
        dx = to_coords.get("x", 0) - from_coords.get("x", 0)
        dy = to_coords.get("y", 0) - from_coords.get("y", 0)

        if abs(dx) > abs(dy):
            return "east" if dx > 0 else "west"
        if dy != 0:
            return "north" if dy > 0 else "south"
        return None

    def _opposite_direction(self, direction: str) -> str:
        """Get opposite cardinal direction."""
        opposites = {"north": "south", "south": "north", "east": "west", "west": "east"}
        return opposites.get(direction, direction)

    def _generate_location(self, game_state: GameState, result: Dict[str, Any]) -> None:
        """Generate a new location when moving to unexplored area."""
        coords = game_state.coordinates  # This should now include 'z'
        cache_key = f"{coords['x']},{coords['y']}"

        if cache_key in self._location_cache:
            cached = self._location_cache[cache_key]
            game_state.discover_location(cached["id"], cached["data"])
            game_state.current_location = cached["id"]
            return

        new_coords = self._get_new_coordinates(game_state)
        loc_id = result.get(
            "new_location",
            f"loc_{
                new_coords['x']}_{
                new_coords['y']}",
        )

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
        # Prioritize location_type from the action result (AI or ActionHandler)
        location_type = result.get("location_type")
        if not location_type or location_type not in self._location_types:
            # Fallback to a random type if not provided or invalid
            location_type = random.choice(list(self._location_types.keys()))

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
                direction = self._get_direction(
                    cast(LocationCoords, coords), new_coords
                )
                if direction:
                    location_data["connections"][existing_id] = direction
                    loc["connections"] = loc.get("connections", {})
                    opp_dir = self._opposite_direction(direction)
                    loc["connections"][loc_id] = opp_dir

    def _generate_location_name(self, location_type: str) -> str:
        """Generate a thematic name for the location."""
        prefixes = {
            "abrigo": ["Abrigo", "Bunker", "Refúgio"],
            "ruina_urbana": ["Ruínas de", "Distrito de", "Setor"],
            "posto_avancado": ["Posto Avançado", "Acampamento", "Barricada"],
            "zona_perigosa": ["Zona Infestada de", "Ninho de", "Covil de"],
            "natureza_selvagem": ["Estrada para", "Floresta de", "Campos de"],
        }
        suffixes = [
            "Perdida",
            "Esquecida",
            "Devastada",
            "Silenciosa",
            "da Esperança",
            "do Desespero",
        ]

        prefix = random.choice(prefixes.get(location_type, ["Local"]))
        suffix = random.choice(suffixes)
        return (
            f"{prefix} {suffix}"
            if random.random() > 0.3
            else f"{prefix} {random.choice(['Alfa', 'Beta', 'Gama', 'Delta'])}"
        )

    def _generate_location_description(self, location_type: str) -> str:
        """Generate a detailed description for the location."""
        descriptions = {
            "abrigo": "Um refúgio improvisado, mas relativamente seguro. As paredes são frias e úmidas, e o ar é pesado.",
            "ruina_urbana": "Prédios em ruínas se erguem como esqueletos contra o céu cinzento. Carros abandonados e destroços bloqueiam as ruas.",
            "posto_avancado": "Uma barricada feita às pressas com arame farpado e sucata. Sentinelas observam nervosamente os arredores.",
            "zona_perigosa": "Um silêncio opressor paira aqui, quebrado apenas por sons guturais distantes. O cheiro de morte é forte.",
            "natureza_selvagem": "A natureza tenta retomar o que era seu, mas mesmo aqui, a ameaça dos infectados e da escassez é constante.",
        }
        return descriptions.get(
            location_type,
            "Um local desolado e perigoso. Você sente um arrepio na espinha.",
        )

    def _generate_location_resources(
        self, location_type: str
    ) -> Optional[Dict[str, int]]:  # Changed to Dict
        """Generate available resources for the location."""
        resources = {
            "abrigo": {
                "Comida Enlatada": random.randint(1, 3),
                "Água Purificada": random.randint(1, 2),
            },
            "ruina_urbana": {
                "Sucata de Metal": random.randint(2, 5),
                "Tecido Rasgado": random.randint(1, 4),
            },
            "posto_avancado": {
                "Munição (variada)": random.randint(3, 10),
                "Bandagens": random.randint(0, 2),
            },
            "zona_perigosa": {
                "Componentes Eletrônicos": random.randint(0, 1),
                "Químicos Estranhos": random.randint(0, 1),
            },  # Less resources, more danger
            "natureza_selvagem": {
                "Madeira": random.randint(1, 5),
                "Ervas Medicinais (não identificadas)": random.randint(0, 3),
            },
        }
        return (
            resources.get(location_type, {"Sucata Variada": random.randint(1, 2)})
            if random.random() < 0.6
            else None
        )  # 60% chance of resources

    def _generate_location_events(self, location_type: str) -> List[str]:
        """Generate random events for the location."""
        events = {
            "abrigo": [
                "O gerador falha por um instante.",
                "Alguém está cantando baixinho uma canção triste.",
                "Uma discussão sobre racionamento de comida.",
            ],
            "ruina_urbana": [
                "Um bando de corvos sobrevoa.",
                "O vento assobia por janelas quebradas.",
                "Um barulho de algo caindo em um prédio próximo.",
            ],
            "posto_avancado": [
                "Um sobrevivente está limpando sua arma.",
                "Troca de guarda na barricada.",
                "Alguém conta uma história sobre o mundo antigo.",
            ],
            "zona_perigosa": [
                "Um gemido distante ecoa.",
                "O cheiro de podridão se intensifica.",
                "Você vê sombras se movendo no limite da sua visão.",
            ],
            "natureza_selvagem": [
                "Um animal selvagem (não infectado) cruza seu caminho.",
                "O silêncio é quase total, apenas o som do vento.",
                "Você encontra rastros recentes... não humanos.",
            ],
        }
        available = events.get(location_type, ["O silêncio é perturbador."])
        return random.sample(available, k=random.randint(1, min(2, len(available))))
