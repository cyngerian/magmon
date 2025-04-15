import pytest
from app.models import MatchPlayer, Match, User, Deck, DeckVersion # Import necessary models

# Note: These tests focus on the model's attributes and methods
# without involving database interactions.

def test_match_player_creation():
    """Test creating a MatchPlayer instance sets attributes correctly."""
    match_id = 1
    user_id = 2
    deck_id = 3
    deck_version_id = 4
    placement = 1

    match_player = MatchPlayer(
        match_id=match_id,
        user_id=user_id,
        deck_id=deck_id,
        deck_version_id=deck_version_id,
        placement=placement
    )

    assert match_player.match_id == match_id
    assert match_player.user_id == user_id
    assert match_player.deck_id == deck_id
    assert match_player.deck_version_id == deck_version_id
    assert match_player.placement == placement

def test_match_player_creation_no_version():
    """Test creating a MatchPlayer without a specific deck version."""
    match_id = 5
    user_id = 6
    deck_id = 7
    placement = None # Placement might be null before results

    match_player = MatchPlayer(
        match_id=match_id,
        user_id=user_id,
        deck_id=deck_id,
        placement=placement
    )

    assert match_player.match_id == match_id
    assert match_player.user_id == user_id
    assert match_player.deck_id == deck_id
    assert match_player.deck_version_id is None
    assert match_player.placement is None

def test_match_player_repr():
    """Test the __repr__ method for the MatchPlayer model."""
    match_player = MatchPlayer(
        match_id=10,
        user_id=20,
        deck_id=30
    )
    # Manually set id for testing repr, though it would normally be None here
    match_player.id = 101
    expected_repr = '<MatchPlayer match_id=10 user_id=20 deck_id=30>'
    assert repr(match_player) == expected_repr