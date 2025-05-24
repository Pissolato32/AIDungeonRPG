# filepath: c:/Users/rodri/Desktop/REPLIT RPG/ai/schemas.py
"""
Pydantic schemas for AI request and response validation.
"""
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class SuggestedRollPydantic(BaseModel):
    description: str
    attribute: str
    skill: Optional[str] = None
    dc: int
    reasoning: Optional[str] = None


class SuggestedLocationDataPydantic(BaseModel):
    new_location_name: str
    new_location_type: str
    new_location_description: str
    points_of_interest: List[str] = Field(default_factory=list)
    potential_connections: Dict[str, str] = Field(default_factory=dict)
    npcs_suggestions: List[str] = Field(default_factory=list)
    events_suggestions: List[str] = Field(default_factory=list)


class AIResponsePydantic(BaseModel):
    success: bool
    message: str
    current_detailed_location: str
    scene_description_update: str
    details: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    interpreted_action_type: Optional[str] = None
    interpreted_action_details: Optional[Dict[str, Any]] = None
    suggested_roll: Optional[SuggestedRollPydantic] = None
    suggested_location_data: Optional[SuggestedLocationDataPydantic] = None
    interactable_elements: Optional[List[str]] = None
    new_facts: Optional[Dict[str, Any]] = None

    # Adicionar aqui validadores @validator se necessário para campos específicos
