"""
Tests for deck-related schemas.
"""
import pytest
from datetime import datetime
from backend.app.api.schemas.deck_schemas import (
    DeckCreate, DeckUpdate, DeckVersionCreate,
    DeckResponse, DeckListResponse, DeckVersionResponse,
    DeckHistoryEntry, DeckVersionListResponse
)

def test_deck_create_schema():
    """Test DeckCreate schema validation."""
    # Test valid data
    valid_data = {
        "name": "Test Deck",
        "commander": "Test Commander",
        "colors": "WUB",
        "decklist_text": "1 Test Card\n2 Another Card"
    }
    deck = DeckCreate(**valid_data)
    assert deck.name == valid_data["name"]
    assert deck.commander == valid_data["commander"]
    assert deck.colors == valid_data["colors"]
    assert deck.decklist_text == valid_data["decklist_text"]

    # Test optional decklist_text
    minimal_data = {
        "name": "Test Deck",
        "commander": "Test Commander",
        "colors": "WUB"
    }
    deck = DeckCreate(**minimal_data)
    assert deck.decklist_text is None

    # Test invalid data
    with pytest.raises(TypeError):
        DeckCreate()  # Missing required fields

    with pytest.raises(TypeError):
        DeckCreate(name="Test")  # Missing required fields

def test_deck_update_schema():
    """Test DeckUpdate schema validation."""
    # Test with all fields
    valid_data = {
        "name": "Updated Deck",
        "commander": "New Commander",
        "colors": "WUB",
        "decklist_text": "Updated decklist"
    }
    deck = DeckUpdate(**valid_data)
    assert deck.name == valid_data["name"]
    assert deck.commander == valid_data["commander"]
    assert deck.colors == valid_data["colors"]
    assert deck.decklist_text == valid_data["decklist_text"]

    # Test with partial update
    partial_data = {
        "name": "Updated Deck"
    }
    deck = DeckUpdate(**partial_data)
    assert deck.name == partial_data["name"]
    assert deck.commander is None
    assert deck.colors is None
    assert deck.decklist_text is None

def test_deck_version_create_schema():
    """Test DeckVersionCreate schema validation."""
    # Test with all fields
    valid_data = {
        "decklist_text": "1 Test Card\n2 Another Card",
        "notes": "Updated mana base"
    }
    version = DeckVersionCreate(**valid_data)
    assert version.decklist_text == valid_data["decklist_text"]
    assert version.notes == valid_data["notes"]

    # Test without optional notes
    minimal_data = {
        "decklist_text": "1 Test Card"
    }
    version = DeckVersionCreate(**minimal_data)
    assert version.decklist_text == minimal_data["decklist_text"]
    assert version.notes is None

    # Test invalid data
    with pytest.raises(TypeError):
        DeckVersionCreate()  # Missing required decklist_text

def test_deck_response_schemas():
    """Test response schemas."""
    # Test DeckResponse
    deck_data = {
        "id": 1,
        "name": "Test Deck",
        "commander": "Test Commander",
        "colors": "WUB",
        "decklist_text": "1 Test Card",
        "user_id": 1,
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "current_version_id": 1
    }
    deck = DeckResponse(**deck_data)
    assert deck.id == deck_data["id"]
    assert deck.name == deck_data["name"]
    assert deck.current_version_id == deck_data["current_version_id"]

    # Test DeckListResponse
    list_data = {
        "id": 1,
        "name": "Test Deck",
        "commander": "Test Commander",
        "colors": "WUB",
        "last_updated": datetime.now().isoformat()
    }
    deck_list = DeckListResponse(**list_data)
    assert deck_list.id == list_data["id"]
    assert deck_list.name == list_data["name"]
    assert deck_list.last_updated == list_data["last_updated"]

    # Test DeckVersionResponse
    version_data = {
        "id": 1,
        "version_number": 1,
        "created_at": datetime.now().isoformat(),
        "notes": "Test notes",
        "decklist_text": "1 Test Card",
        "is_current": True
    }
    version = DeckVersionResponse(**version_data)
    assert version.id == version_data["id"]
    assert version.version_number == version_data["version_number"]
    assert version.is_current == version_data["is_current"]

def test_deck_history_schemas():
    """Test history-related schemas."""
    # Test DeckHistoryEntry
    history_data = {
        "game_id": 1,
        "game_date": datetime.now().date().isoformat(),
        "placement": 1,
        "version_number": 1
    }
    history = DeckHistoryEntry(**history_data)
    assert history.game_id == history_data["game_id"]
    assert history.game_date == history_data["game_date"]
    assert history.placement == history_data["placement"]
    assert history.version_number == history_data["version_number"]

    # Test with optional fields as None
    minimal_history = {
        "game_id": 1,
        "game_date": datetime.now().date().isoformat(),
        "placement": None,
        "version_number": None
    }
    history = DeckHistoryEntry(**minimal_history)
    assert history.placement is None
    assert history.version_number is None

def test_deck_version_list_schema():
    """Test DeckVersionListResponse schema."""
    version_data = {
        "id": 1,
        "version_number": 1,
        "created_at": datetime.now().isoformat(),
        "notes": "Test notes",
        "is_current": True
    }
    version = DeckVersionListResponse(**version_data)
    assert version.id == version_data["id"]
    assert version.version_number == version_data["version_number"]
    assert version.notes == version_data["notes"]
    assert version.is_current == version_data["is_current"]

    # Test with optional notes as None
    minimal_data = {
        "id": 1,
        "version_number": 1,
        "created_at": datetime.now().isoformat(),
        "notes": None,
        "is_current": False
    }
    version = DeckVersionListResponse(**minimal_data)
    assert version.notes is None