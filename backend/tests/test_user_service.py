from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import func

from backend.app.models import User, MatchPlayer, Deck
from backend.app.api.schemas.user_schemas import UserRegistration
from backend.app.api.services.user_service import UserService

@pytest.fixture
def mock_db_session(mocker):
    """Create a mock database session."""
    session = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    mocker.patch('backend.app.db.session', session)
    return session

@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    now = datetime.utcnow()
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        registered_on=now,
        avatar_url="/static/uploads/avatars/user_1_avatar.png"
    )
    user.set_password("password123")
    return user

def test_register_user(mock_db_session, sample_user):
    """Test user registration."""
    # Setup
    data = UserRegistration(
        username="newuser",
        email="new@example.com",
        password="password123"
    )

    # Mock User.query to simulate no existing user
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    User.query = mock_query

    # Mock db.session.add to set user ID
    def mock_add(obj):
        if isinstance(obj, User):
            obj.id = 1
            obj.registered_on = datetime.utcnow()
    mock_db_session.add.side_effect = mock_add

    # Execute
    response, status_code = UserService.register_user(data)

    # Verify
    assert status_code == 201
    assert response.username == data.username
    assert response.email == data.email
    assert mock_db_session.add.called
    assert mock_db_session.commit.called

def test_register_user_existing(mock_db_session, sample_user):
    """Test registration with existing username/email."""
    data = UserRegistration(
        username="testuser",  # existing username
        email="new@example.com",
        password="password123"
    )

    # Mock User.query to simulate existing user
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = sample_user
    User.query = mock_query

    # Execute and verify
    with pytest.raises(ValueError) as exc:
        UserService.register_user(data)
    assert "exists" in str(exc.value)
    assert not mock_db_session.commit.called

def test_get_users(mock_db_session, sample_user):
    """Test getting list of users."""
    # Mock User.query
    mock_query = MagicMock()
    mock_query.order_by.return_value.all.return_value = [sample_user]
    User.query = mock_query

    # Mock win count query
    mock_count = MagicMock()
    mock_count.scalar.return_value = 5
    mock_db_session.query.return_value.filter.return_value = mock_count

    # Execute
    users = UserService.get_users()

    # Verify
    assert len(users) == 1
    assert users[0].id == sample_user.id
    assert users[0].username == sample_user.username
    assert users[0].stats["total_wins"] == 5

def test_get_user_profile(mock_db_session, sample_user):
    """Test getting user profile."""
    # Mock User.query
    mock_query = MagicMock()
    mock_query.get.return_value = sample_user
    User.query = mock_query

    # Mock win count query
    mock_count = MagicMock()
    mock_count.scalar.return_value = 5
    mock_db_session.query.return_value.filter.return_value = mock_count

    # Execute
    response, status_code = UserService.get_user_profile(1)

    # Verify
    assert status_code == 200
    assert response.id == sample_user.id
    assert response.username == sample_user.username
    assert response.stats["total_wins"] == 5

def test_get_user_profile_not_found(mock_db_session):
    """Test getting profile of non-existent user."""
    # Mock User.query to return None
    mock_query = MagicMock()
    mock_query.get.return_value = None
    User.query = mock_query

    # Execute and verify
    with pytest.raises(ValueError) as exc:
        UserService.get_user_profile(999)
    assert "not found" in str(exc.value)

def test_get_user_decks(mock_db_session, sample_user):
    """Test getting user's decks."""
    # Create a sample deck
    now = datetime.utcnow()
    mock_deck = MagicMock()
    mock_deck.id = 1
    mock_deck.name = "Test Deck"
    mock_deck.commander = "Test Commander"
    mock_deck.colors = "WUB"
    mock_deck.last_updated = now

    # Mock User.query
    mock_query = MagicMock()
    mock_query.get.return_value = sample_user
    User.query = mock_query

    # Mock Deck.query
    mock_deck_query = MagicMock()
    mock_deck_query.filter_by.return_value.order_by.return_value.all.return_value = [mock_deck]
    Deck.query = mock_deck_query

    # Execute
    decks = UserService.get_user_decks(1)

    # Verify
    assert len(decks) == 1
    assert decks[0]["id"] == mock_deck.id
    assert decks[0]["name"] == mock_deck.name
    assert decks[0]["commander"] == mock_deck.commander
    assert decks[0]["last_updated"] == mock_deck.last_updated.isoformat()

def test_get_user_decks_not_found(mock_db_session):
    """Test getting decks of non-existent user."""
    # Mock User.query to return None
    mock_query = MagicMock()
    mock_query.get.return_value = None
    User.query = mock_query

    # Execute and verify
    with pytest.raises(ValueError) as exc:
        UserService.get_user_decks(999)
    assert "not found" in str(exc.value)