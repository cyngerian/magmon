"""
Deck-related schemas for request/response validation and serialization.
"""
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class DeckCreate:
    """Schema for creating a new deck."""
    name: str
    commander: str
    colors: str
    decklist_text: Optional[str] = None

@dataclass
class DeckUpdate:
    """Schema for updating a deck."""
    name: Optional[str] = None
    commander: Optional[str] = None
    colors: Optional[str] = None
    decklist_text: Optional[str] = None

@dataclass
class DeckVersionCreate:
    """Schema for creating a new deck version."""
    decklist_text: str
    notes: Optional[str] = None

@dataclass
class DeckVersionResponse:
    """Schema for deck version response."""
    id: int
    version_number: int
    created_at: str  # ISO format datetime
    notes: Optional[str]
    decklist_text: str
    is_current: bool

@dataclass
class DeckResponse:
    """Schema for deck response."""
    id: int
    name: str
    commander: str
    colors: str
    decklist_text: str
    user_id: int
    created_at: str  # ISO format datetime
    last_updated: str  # ISO format datetime
    current_version_id: Optional[int] = None

@dataclass
class DeckListResponse:
    """Schema for deck list response."""
    id: int
    name: str
    commander: str
    colors: str
    last_updated: str  # ISO format datetime

@dataclass
class DeckHistoryEntry:
    """Schema for a deck's game history entry."""
    game_id: int
    game_date: str  # ISO format date
    placement: Optional[int]
    version_number: Optional[int]

@dataclass
class DeckVersionListResponse:
    """Schema for deck version list response."""
    id: int
    version_number: int
    created_at: str  # ISO format datetime
    notes: Optional[str]
    is_current: bool