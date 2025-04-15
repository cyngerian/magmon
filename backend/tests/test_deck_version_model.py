import pytest
from datetime import datetime
from app.models import DeckVersion, Deck # Import DeckVersion and Deck

# Note: These tests focus on the model's attributes and methods
# without involving database interactions.

def test_deck_version_creation():
    """Test creating a DeckVersion instance sets attributes correctly."""
    # Assume a parent deck exists (we only need its ID for the FK)
    deck_id = 10
    version_num = 1
    decklist = "1 Card A\n1 Card B"
    notes = "Initial version"

    deck_version = DeckVersion(
        deck_id=deck_id,
        version_number=version_num,
        decklist_text=decklist,
        notes=notes
        # created_at has a database default
    )

    assert deck_version.deck_id == deck_id
    assert deck_version.version_number == version_num
    assert deck_version.decklist_text == decklist
    assert deck_version.notes == notes
    # Database default is not set on instantiation
    assert deck_version.created_at is None

def test_deck_version_repr():
    """Test the __repr__ method for the DeckVersion model."""
    deck_version = DeckVersion(
        deck_id=25,
        version_number=3
    )
    expected_repr = '<DeckVersion deck_id=25 version=3>'
    assert repr(deck_version) == expected_repr