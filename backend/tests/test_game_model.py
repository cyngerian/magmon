import pytest
from datetime import date, datetime
from unittest.mock import patch
from app.models import Game, GameStatus, User # Import Game and GameStatus

# Note: These tests focus on the model's attributes and methods
# without involving database interactions.

def test_game_creation_defaults():
    """Test creating a Game instance uses defaults correctly."""
    # today = date.today() # Default is handled by DB
    game = Game() # Use defaults

    # Database defaults are not applied during simple Python object instantiation.
    assert game.game_date is None
    assert game.status is None # Default is handled by DB
    assert game.is_pauper is None # Default is handled by DB
    assert game.details is None
    # Database defaults/FKs are not set on instantiation
    assert game.created_at is None
    assert game.deleted_at is None
    assert game.deleted_by_id is None
    assert game.last_admin_action is None
    assert game.last_admin_action_at is None

def test_game_creation_specific_values():
    """Test creating a Game instance with specific values."""
    specific_date = date(2024, 1, 15)
    details_text = "Special event details"
    game = Game(
        game_date=specific_date,
        status=GameStatus.COMPLETED,
        is_pauper=True,
        details=details_text
    )

    assert game.game_date == specific_date
    assert game.status == GameStatus.COMPLETED
    assert game.is_pauper is True
    assert game.details == details_text
    # Database defaults/FKs are not set on instantiation
    assert game.created_at is None
    assert game.deleted_at is None
    assert game.deleted_by_id is None
    assert game.last_admin_action is None
    assert game.last_admin_action_at is None


def test_game_repr():
    """Test the __repr__ method for the Game model."""
    test_date = date(2024, 5, 20)
    game = Game(game_date=test_date, status=GameStatus.CANCELLED)
    expected_repr = '<Game id=None date=2024-05-20 status=Cancelled>'
    # Note: id will be None as it's not added to a session/db
    assert repr(game) == expected_repr

@pytest.mark.parametrize("current_date,expected_date", [
    # If today is Monday (weekday 0), next Monday is in 7 days
    (date(2024, 1, 1), date(2024, 1, 8)),  # Monday Jan 1 -> Monday Jan 8
    # If today is Tuesday (weekday 1), next Monday is in 6 days
    (date(2024, 1, 2), date(2024, 1, 8)),  # Tuesday Jan 2 -> Monday Jan 8
    # If today is Saturday (weekday 5), next Monday is in 2 days
    (date(2024, 1, 6), date(2024, 1, 8)),  # Saturday Jan 6 -> Monday Jan 8
    # If today is Sunday (weekday 6), next Monday is in 1 day
    (date(2024, 1, 7), date(2024, 1, 8)),  # Sunday Jan 7 -> Monday Jan 8
])
def test_get_next_monday(current_date, expected_date):
    """Test getting the next Monday from various starting dates."""
    with patch('app.models.date') as mock_date:
        mock_date.today.return_value = current_date
        assert Game.get_next_monday() == expected_date