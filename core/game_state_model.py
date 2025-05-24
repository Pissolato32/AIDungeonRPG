"""
Module for game state data models.
"""

import logging

logger = logging.getLogger(__name__)  # Define the logger

from dataclasses import dataclass, field, asdict  # Import asdict
from typing import (
    Any,
    Dict,
    List,
    Optional,
    TypedDict,
)

# Import NPC here
# If core.npc also imports GameState or related models, this might need further refactoring.
# For now, we assume core.npc is independent or only depends on basic types.
from core.npc import NPC


# TypedDict for chat messages
class MessageDict(TypedDict):
    """Type definition for a single message in a conversation."""

    role: str
    content: str


class LocationCoords(TypedDict):
    """Type definition for location coordinates."""

    x: int
    y: int
    z: int


class LocationData(TypedDict, total=False):
    """Type definition for location data."""

    name: str
    type: str
    description: str
    coordinates: LocationCoords
    visited: bool
    # conexões com outras localizações (id: direção)
    connections: Dict[str, str]
    resources: Optional[Dict[str, int]]
    points_of_interest: Optional[List[str]]  # Novo campo
    danger_level: Optional[int]
    events: List[str]
    welcome: Optional[str]
    npcs: List[str]  # Adicionado para corresponder ao uso em game_engine.py


class SearchResultEntry(TypedDict):
    """Type definition for a single search result entry."""

    query: str
    result: str


class VisitedLocationDetail(TypedDict):
    """Type definition for detailed information about a visited location."""

    name: str
    last_visited: str
    description: str
    npcs_seen: List[str]
    events_seen: List[str]
    search_results: List[SearchResultEntry]


class CombatState(TypedDict, total=False):
    """Type definition for the combat state."""

    enemy: Any  # Idealmente, seria 'Enemy' do core.enemy, mas para evitar import circular, usamos Any
    round: int
    log: List[str]
    # Você pode adicionar mais campos aqui conforme necessário, como:
    # player_turn: bool
    # combat_ended: bool


@dataclass
class GameState:
    """Represents the current state of the game."""

    current_location: str = ""
    scene_description: str = ""
    npcs_present: List[str] = field(
        default_factory=list
    )  # Lista de nomes/IDs de NPCs presentes
    known_npcs: Dict[str, NPC] = field(
        default_factory=dict
    )  # Agora armazena objetos NPC
    messages: List[MessageDict] = field(default_factory=list)  # Changed from List[str]
    coordinates: LocationCoords = field(
        default_factory=lambda: {"x": 0, "y": 0, "z": 0}
    )
    current_action: str = ""
    discovered_locations: Dict[str, LocationData] = field(default_factory=dict)
    npcs_by_location: Dict[str, List[str]] = field(default_factory=dict)
    npc_relationships: Dict[str, int] = field(default_factory=dict)

    location_id: str = ""
    events: List[str] = field(default_factory=list)
    world_map: Dict[str, LocationData] = field(default_factory=dict)
    visited_locations: Dict[str, VisitedLocationDetail] = field(default_factory=dict)
    combat: Optional[CombatState] = field(
        default=None
    )  # Novo atributo para estado de combate
    npc_message_history: Dict[str, List[str]] = field(
        default_factory=dict
    )  # Histórico de mensagens por NPC para evitar repetição
    summary: Optional[str] = None  # Resumo da memória de longo prazo
    long_term_memory: Dict[str, Any] = field(
        default_factory=dict
    )  # Fatos chave da memória de longo prazo

    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to a dictionary."""
        # Manual serialization to handle nested NPC objects correctly
        # and ensure all fields are included as expected.
        return {
            "current_location": self.current_location,
            "scene_description": self.scene_description,
            "npcs_present": self.npcs_present,
            "known_npcs": {
                npc_id: npc.to_dict() for npc_id, npc in self.known_npcs.items()
            },
            "messages": self.messages,
            "coordinates": self.coordinates,
            "current_action": self.current_action,
            "discovered_locations": self.discovered_locations,
            "npcs_by_location": self.npcs_by_location,
            "npc_relationships": self.npc_relationships,
            "location_id": self.location_id,
            "events": self.events,
            "world_map": self.world_map,
            "visited_locations": self.visited_locations,
            "combat": self.combat,
            "npc_message_history": self.npc_message_history,
            "summary": self.summary,
            "long_term_memory": self.long_term_memory,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        """Create GameState from dictionary data."""
        # Explicitly map dictionary keys to dataclass fields
        # This avoids issues with **data if data contains extra keys or misses some with defaults.

        # Deserialize known_npcs from their dict representation
        known_npcs_data = data.get("known_npcs", {})
        loaded_known_npcs = {
            npc_id: (
                NPC.from_dict(npc_data)
                if isinstance(npc_data, dict)
                else npc_data  # Should ideally always be dict if coming from JSON
            )
            for npc_id, npc_data in known_npcs_data.items()
        }

        # Create an instance by explicitly passing arguments
        # This ensures that only fields defined in GameState are passed to its constructor.
        # Fields with default_factory will be initialized if not present in 'data'.
        instance = cls()  # Initialize with defaults
        instance.current_location = data.get(
            "current_location", instance.current_location
        )
        instance.scene_description = data.get(
            "scene_description", instance.scene_description
        )
        instance.npcs_present = data.get("npcs_present", instance.npcs_present)
        instance.known_npcs = loaded_known_npcs  # Use the deserialized NPCs
        instance.messages = data.get("messages", instance.messages)
        instance.coordinates = data.get("coordinates", instance.coordinates)
        instance.current_action = data.get("current_action", instance.current_action)
        instance.discovered_locations = data.get(
            "discovered_locations", instance.discovered_locations
        )
        instance.npcs_by_location = data.get(
            "npcs_by_location", instance.npcs_by_location
        )
        instance.npc_relationships = data.get(
            "npc_relationships", instance.npc_relationships
        )
        instance.location_id = data.get("location_id", instance.location_id)
        instance.events = data.get("events", instance.events)
        instance.world_map = data.get("world_map", instance.world_map)
        instance.visited_locations = data.get(
            "visited_locations", instance.visited_locations
        )
        instance.combat = data.get("combat", instance.combat)
        instance.npc_message_history = data.get(
            "npc_message_history", instance.npc_message_history
        )
        instance.summary = data.get("summary", instance.summary)
        instance.long_term_memory = data.get(
            "long_term_memory", instance.long_term_memory
        )
        return instance

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the game state's conversation history.

        Args:
            role: The role of the message sender (e.g., "user", "assistant").
            content: The content of the message.
        """
        self.messages.append({"role": role, "content": content})
        # Keep the last N messages (e.g., 20 messages for 10 exchanges)
        # Adjust this limit based on context window needs and token limits.
        if len(self.messages) > 20:  # Example limit
            self.messages = self.messages[-20:]

    def discover_location(self, location_id: str, location_data: LocationData) -> None:
        """Add a new discovered location."""
        self.discovered_locations[location_id] = location_data
        # Add a system message for discovering a location
        self.add_message(
            role="system",
            content=f"Você descobriu: {location_data.get('name', 'um novo local desconhecido')}!",
        )

    def add_npc(self, npc_id: str, npc: NPC) -> None:
        """Add or update an NPC object in the game state."""
        if isinstance(npc, NPC):
            self.known_npcs[npc_id] = npc
        elif isinstance(
            npc, dict
        ):  # Fallback if a dict is passed (should ideally be an NPC object)
            logger.warning(
                f"Adding NPC '{npc_id}' from dict to known_npcs. Consider passing an NPC object."
            )
            self.known_npcs[npc_id] = NPC.from_dict(npc)  # type: ignore
        # self.known_npcs[npc_id] = npc_data # Old line

        # Assuming NPC object has a 'location' attribute or a way to get its current location
        # For now, we'll assume the location is managed externally or set when NPC is placed in a scene.
        # If NPC objects store their location, you'd use: location = npc.location
        # This part might need adjustment based on how NPC locations are tracked.
        if hasattr(npc, "current_location_id") and (
            location := getattr(npc, "current_location_id", None)
        ):  # Example if NPC stores its location ID
            if location not in self.npcs_by_location:
                self.npcs_by_location[location] = []
            # Avoid duplicates
            if npc_id not in self.npcs_by_location[location]:
                self.npcs_by_location[location].append(npc_id)

    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Get an NPC by ID."""
        npc_entry = self.known_npcs.get(npc_id)
        if isinstance(npc_entry, NPC):
            return npc_entry
        elif isinstance(
            npc_entry, dict
        ):  # Should not happen if add_npc ensures NPC objects
            # If already an NPC object, return it. If it's still a dict, try to load it.
            logger.warning(
                f"NPC '{npc_id}' in known_npcs was a dict. Attempting to convert."
            )
            return NPC.from_dict(npc_entry)  # type: ignore
        elif npc_entry is not None:
            logger.warning(
                f"Data for NPC ID '{npc_id}' in known_npcs is not an NPC object or dict: {type(npc_entry)}"
            )
        return None

    def get_npcs_in_location(self, location: str) -> List[NPC]:
        """Get all NPCs in a specific location."""
        npc_ids = self.npcs_by_location.get(location, [])
        npcs_found = []
        for npc_id in npc_ids:
            npc_entry = self.known_npcs.get(npc_id)
            if isinstance(npc_entry, NPC):
                npcs_found.append(npc_entry)
            elif isinstance(npc_entry, dict):  # Should not happen
                # If already an NPC object, append it. If it's a dict, try to load it.
                logger.warning(
                    f"NPC '{npc_id}' in known_npcs (for location '{location}') was a dict. Attempting to convert."
                )
                npc_obj = NPC.from_dict(npc_entry)  # type: ignore
                if npc_obj:
                    npcs_found.append(npc_obj)
        return npcs_found

    def update_npc_relationship(
        self, npc_id: str, change: int, max_value: int = 100
    ) -> None:
        """Update relationship with an NPC."""
        current = self.npc_relationships.get(npc_id, 0)
        self.npc_relationships[npc_id] = max(
            -max_value, min(max_value, current + change)
        )
