import pytest
from datetime import datetime
from app.models import Match, Game, User # Import Match and related models

# Note: These tests focus on the model's attributes and methods
# without involving database interactions.

def test_match_creation_defaults():
    """Test creating a Match instance uses defaults correctly."""
    # Assume related objects exist (we only need IDs for FKs)
    game_id = 1
    submitter_id = 2

    match = Match(
        game_id=game_id,
        player_count=4, # player_count is required
        submitted_by_id=submitter_id
    )

    assert match.game_id == game_id
    assert match.player_count == 4
    assert match.submitted_by_id == submitter_id
    assert match.status is None # Default value is handled by DB
    # Database defaults/FKs are not set on instantiation
    assert match.created_at is None
    assert match.approved_at is None
    assert match.approved_by_id is None
    # Nullable fields should be None initially
    assert match.season_number is None
    assert match.start_time is None
    assert match.end_time is None
    assert match.notes_big_interaction is None
    assert match.notes_rules_discussion is None
    assert match.notes_end_summary is None
    assert match.approval_notes is None

def test_match_creation_specific_values():
    """Test creating a Match instance with specific values."""
    game_id = 5
    submitter_id = 10
    approver_id = 11
    start = datetime(2024, 1, 1, 19, 0, 0)
    end = datetime(2024, 1, 1, 20, 30, 0)

    match = Match(
        game_id=game_id,
        player_count=3,
        status='approved',
        season_number=1,
        start_time=start,
        end_time=end,
        submitted_by_id=submitter_id,
        approved_by_id=approver_id,
        notes_big_interaction="Big play happened",
        notes_rules_discussion="Rule discussed",
        notes_end_summary="Good game",
        approval_notes="Looks good"
        # created_at and approved_at have DB defaults or are set later
    )

    assert match.game_id == game_id
    assert match.player_count == 3
    assert match.status == 'approved'
    assert match.season_number == 1
    assert match.start_time == start
    assert match.end_time == end
    assert match.submitted_by_id == submitter_id
    assert match.approved_by_id == approver_id
    assert match.notes_big_interaction == "Big play happened"
    assert match.notes_rules_discussion == "Rule discussed"
    assert match.notes_end_summary == "Good game"
    assert match.approval_notes == "Looks good"
    assert match.created_at is None # DB default
    assert match.approved_at is None # Set during approval logic

def test_match_repr():
    """Test the __repr__ method for the Match model."""
    match = Match(id=123, game_id=45, status='pending', player_count=4, submitted_by_id=1)
    # Manually set id for repr testing, though it would normally be None here
    match.id = 123
    expected_repr = '<Match id=123 game_id=45 status=pending>'
    assert repr(match) == expected_repr