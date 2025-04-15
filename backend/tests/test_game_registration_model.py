import pytest
from datetime import datetime
from app.models import GameRegistration, Game, User, Deck, DeckVersion # Import necessary models

# Note: These tests focus on the model's attributes and methods
# without involving database interactions.

def test_game_registration_creation():
    """Test creating a GameRegistration instance sets attributes correctly."""
    game_id = 1
    user_id = 2
    deck_id = 3
    deck_version_id = 4

    registration = GameRegistration(
        game_id=game_id,
        user_id=user_id,
        deck_id=deck_id,
        deck_version_id=deck_version_id
        # registered_at has a database default
    )

    assert registration.game_id == game_id
    assert registration.user_id == user_id
    assert registration.deck_id == deck_id
    assert registration.deck_version_id == deck_version_id
    # Database default is not set on instantiation
    assert registration.registered_at is None

def test_game_registration_creation_no_version():
    """Test creating a GameRegistration without a specific deck version."""
    game_id = 5
    user_id = 6
    deck_id = 7

    registration = GameRegistration(
        game_id=game_id,
        user_id=user_id,
        deck_id=deck_id
    )

    assert registration.game_id == game_id
    assert registration.user_id == user_id
    assert registration.deck_id == deck_id
    assert registration.deck_version_id is None
    assert registration.registered_at is None

def test_game_registration_repr():
    """Test the __repr__ method for the GameRegistration model."""
    registration = GameRegistration(
        game_id=10,
        user_id=20,
        deck_id=30
    )
    # Manually set id for testing repr, though it would normally be None here
    registration.id = 101
    expected_repr = '<GameRegistration user=20 deck=30 game=10>'
    assert repr(registration) == expected_repr