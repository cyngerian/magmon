import pytest
from datetime import datetime
from app.models import Deck, User # Import Deck and User

# Note: These tests focus on the model's attributes and methods
# without involving database interactions.

def test_deck_creation():
    """Test creating a Deck instance sets attributes correctly."""
    # A User instance might be needed if the model expects it,
    # but for basic attribute checks, we might just need the ID.
    # Let's assume user_id is sufficient for this basic test.
    user_id = 1
    deck_name = "My Test Deck"
    commander = "Test Commander"
    colors = "WUBRG"
    decklist = "1 Sol Ring\n99 Island"

    deck = Deck(
        user_id=user_id,
        name=deck_name,
        commander=commander,
        colors=colors,
        decklist_text=decklist
        # created_at and last_updated have defaults
    )

    assert deck.user_id == user_id
    assert deck.name == deck_name
    assert deck.commander == commander
    assert deck.colors == colors
    assert deck.decklist_text == decklist
    # Note: created_at and last_updated have database defaults,
    # which are not applied during simple Python object instantiation.
    # We assert their initial state is None here. Testing DB defaults
    # requires integration tests.
    assert deck.created_at is None
    assert deck.last_updated is None
    # Check default relationships/foreign keys are initially None
    assert deck.current_version_id is None
    assert deck.current_version is None

def test_deck_repr():
    """Test the __repr__ method for the Deck model."""
    deck = Deck(
        user_id=5,
        name="Another Deck",
        commander="Another Commander",
        colors="BG",
        decklist_text="Some cards"
    )
    expected_repr = '<Deck Another Deck (Another Commander) by User 5>'
    assert repr(deck) == expected_repr