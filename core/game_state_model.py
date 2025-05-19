"""
Module for game state data models.
"""

from dataclasses import dataclass, field
from typing import (  # Added Set for visited_locations previous type
    Any,
    Dict,
    List,
    Optional,
    TypedDict,
)

# Import NPC here if it's a clean dependency (i.e., npc.py doesn't import GameState)
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
    npcs_present: List[str] = field(default_factory=list)
    known_npcs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to a dictionary."""
        return {
            "current_location": self.current_location,
            "scene_description": self.scene_description,
            "npcs_present": self.npcs_present,
            "known_npcs": self.known_npcs,
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
            coordinates=data.get("coordinates", {"x": 0, "y": 0, "z": 0}),
            current_action=data.get("current_action", ""),
            discovered_locations=data.get("discovered_locations", {}),
            npcs_by_location=data.get("npcs_by_location", {}),
            npc_relationships=data.get("npc_relationships", {}),
            location_id=data.get("location_id", ""),
            events=data.get("events", []),
            world_map=data.get("world_map", {}),
            visited_locations=data.get("visited_locations", {}),
            combat=data.get("combat", None),
        )

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

    def add_npc(
        self, npc_id: str, npc_data: Dict[str, Any]
    ) -> None:  # Changed 'npc' to 'npc_data'
        """Add or update an NPC in the game state."""
        self.known_npcs[npc_id] = npc_data

        if location := npc_data.get("location"):
            if location not in self.npcs_by_location:
                self.npcs_by_location[location] = []
            # Avoid duplicates
            if npc_id not in self.npcs_by_location[location]:
                self.npcs_by_location[location].append(npc_id)

    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Get an NPC by ID."""
        if npc_data := self.known_npcs.get(npc_id):
            return NPC(
                **npc_data
            )  # Assumes NPC can be instantiated from its dict representation
        return None

    def get_npcs_in_location(self, location: str) -> List[NPC]:
        """Get all NPCs in a specific location."""
        npc_ids = self.npcs_by_location.get(location, [])
        npcs_found = []
        for npc_id in npc_ids:
            if npc_data := self.known_npcs.get(npc_id):
                npcs_found.append(NPC(**npc_data))
        return npcs_found

    def update_npc_relationship(
        self, npc_id: str, change: int, max_value: int = 100
    ) -> None:
        """Update relationship with an NPC."""
        current = self.npc_relationships.get(npc_id, 0)
        self.npc_relationships[npc_id] = max(
            -max_value, min(max_value, current + change)
        )
