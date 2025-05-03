"""
Tests for deck service layer.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from sqlalchemy.orm.session import Session
from flask import Flask

from backend.app import create_app
from backend.app.api.services.deck_service import DeckService
from backend.app.api.schemas.deck_schemas import DeckCreate, DeckVersionCreate
from backend.app.models import Deck, DeckVersion, Game, GameRegistration, Match, MatchPlayer

@pytest.fixture
def app():
    """Create a Flask application for testing."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app

@pytest.fixture
def mock_db_session(mocker, app):
    """Create a mock database session."""
    with app.app_context():
        session = MagicMock(spec=Session)
        session.remove = MagicMock()  # Add remove method
        session.add = MagicMock()
        session.commit = MagicMock()
        session.flush = MagicMock()
        
        # Mock query methods
        query_mock = MagicMock()
        query_mock.get_or_404.return_value = None
        query_mock.filter_by.return_value.order_by.return_value.all.return_value = []
        query_mock.filter_by.return_value.first_or_404.return_value = None
        session.query = MagicMock(return_value=query_mock)
        
        mocker.patch('backend.app.db.session', session)
        mocker.patch('backend.app.models.Deck.query', query_mock)
        mocker.patch('backend.app.models.DeckVersion.query', query_mock)
        yield session

@pytest.fixture
def sample_deck(mock_db_session):
    """Create a sample deck for testing."""
    now = datetime.utcnow()
    deck = Deck(
        id=1,
        name="Test Deck",
        commander="Test Commander",
        colors="WUB",
        decklist_text="1 Test Card",
        user_id=1,
        created_at=now,
        last_updated=now
    )
    
    # Mock the deck creation
    def mock_add(obj):
        if isinstance(obj, Deck):
            obj.id = 1
            obj.created_at = now
            obj.last_updated = now
        elif isinstance(obj, DeckVersion):
            obj.id = 1
            obj.created_at = now
    mock_db_session.add = MagicMock(side_effect=mock_add)
    
    # Update mock query methods to return this deck
    query_mock = mock_db_session.query.return_value
    query_mock.get_or_404.return_value = deck
    query_mock.filter_by.return_value.order_by.return_value.all.return_value = [deck]
    return deck

@pytest.fixture
def sample_version(mock_db_session, sample_deck):
    """Create a sample deck version for testing."""
    now = datetime.utcnow()
    version = DeckVersion(
        id=1,
        deck_id=sample_deck.id,
        version_number=1,
        decklist_text="1 Test Card",
        notes="Initial version",
        created_at=now
    )
    version.deck = sample_deck
    
    # Mock the version creation
    def mock_add(obj):
        if isinstance(obj, DeckVersion):
            obj.id = 1
            obj.created_at = now
    mock_db_session.add = MagicMock(side_effect=mock_add)
    
    # Update mock query methods to return this version
    query_mock = mock_db_session.query.return_value
    query_mock.get.return_value = version
    query_mock.filter_by.return_value.first_or_404.return_value = version
    query_mock.filter_by.return_value.order_by.return_value.all.return_value = [version]
    return version

def test_create_deck(mock_db_session, sample_deck, sample_version, app):
    """Test creating a new deck."""
    # Setup
    mock_db_session.flush = MagicMock()
    mock_db_session.commit = MagicMock()
    
    # Create test data
    deck_data = DeckCreate(
        name="Test Deck",
        commander="Test Commander",
        colors="WUB",
        decklist_text="1 Test Card"
    )
    
    # Mock Deck and DeckVersion instantiation to add timestamps
    now = datetime.utcnow()
    # Create a real Deck instance
    new_deck = Deck(
        name=deck_data.name,
        commander=deck_data.commander,
        colors=deck_data.colors,
        decklist_text=deck_data.decklist_text,
        user_id=1
    )
    new_deck.id = 1
    new_deck.created_at = now
    new_deck.last_updated = now

    # Create a real DeckVersion instance
    new_version = DeckVersion(
        deck_id=1,
        version_number=1,
        decklist_text=deck_data.decklist_text,
        notes="Initial version"
    )
    new_version.id = 1
    new_version.created_at = now

    # Mock db.session behavior
    def mock_add(obj):
        if isinstance(obj, Deck):
            obj.id = new_deck.id
            obj.created_at = new_deck.created_at
            obj.last_updated = new_deck.last_updated
        elif isinstance(obj, DeckVersion):
            obj.id = new_version.id
            obj.created_at = new_version.created_at

    mock_db_session.add.side_effect = mock_add

    # Execute
    response, status_code = DeckService.create_deck(1, deck_data)

    # Verify the response
    assert status_code == 201
    assert response.id == new_deck.id
    assert response.name == new_deck.name
    assert response.commander == new_deck.commander
    assert response.created_at == new_deck.created_at.isoformat()
    
    # Verify
    assert status_code == 201
    assert response.name == deck_data.name
    assert response.commander == deck_data.commander
    assert mock_db_session.add.call_count == 3  # Deck + Version + Deck update
    assert mock_db_session.commit.call_count == 1

def test_get_user_decks(mock_db_session, sample_deck, app):
    """Test getting all decks for a user."""
    # Setup
    mock_db_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [sample_deck]
    
    # Execute
    decks = DeckService.get_user_decks(1)
    
    # Verify
    assert len(decks) == 1
    assert decks[0].id == sample_deck.id
    assert decks[0].name == sample_deck.name

def test_get_deck_details(mock_db_session, sample_deck, sample_version, app):
    """Test getting deck details."""
    # Setup
    mock_db_session.query.return_value.get_or_404.return_value = sample_deck
    sample_deck.current_version_id = sample_version.id
    
    # Execute
    response, status_code = DeckService.get_deck_details(1)
    
    # Verify
    assert status_code == 200
    assert response.id == sample_deck.id
    assert response.name == sample_deck.name
    assert response.decklist_text == sample_version.decklist_text

def test_create_deck_version(mock_db_session, sample_deck, sample_version, app):
    """Test creating a new deck version."""
    # Setup
    mock_db_session.query.return_value.get_or_404.return_value = sample_deck
    mock_db_session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = sample_version
    
    version_data = DeckVersionCreate(
        decklist_text="2 New Card",
        notes="Updated version"
    )
    
    # Mock new version
    new_version = DeckVersion(
        id=2,
        deck_id=sample_deck.id,
        version_number=2,
        decklist_text=version_data.decklist_text,
        notes=version_data.notes,
        created_at=datetime.utcnow()
    )
    
    # Set user_id to match test case
    sample_deck.user_id = 1
    # Execute
    response, status_code = DeckService.create_deck_version(1, 1, version_data)
    
    # Verify
    assert status_code == 201
    assert response.version_number == 2
    assert response.decklist_text == version_data.decklist_text
    assert response.notes == version_data.notes
    assert response.is_current is True

def test_create_deck_version_permission_error(mock_db_session, sample_deck, app):
    """Test creating a version for someone else's deck."""
    # Setup
    mock_db_session.query.return_value.get_or_404.return_value = sample_deck
    
    version_data = DeckVersionCreate(
        decklist_text="2 New Card",
        notes="Updated version"
    )
    
    # Execute and verify
    with pytest.raises(PermissionError):
        DeckService.create_deck_version(1, sample_deck.user_id + 1, version_data)

def test_get_deck_versions(mock_db_session, sample_deck, sample_version, app):
    """Test getting all versions of a deck."""
    # Setup
    mock_db_session.query.return_value.get_or_404.return_value = sample_deck
    mock_db_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [sample_version]
    sample_deck.current_version_id = sample_version.id
    
    # Execute
    versions = DeckService.get_deck_versions(1)
    
    # Verify
    assert len(versions) == 1
    assert versions[0].id == sample_version.id
    assert versions[0].version_number == sample_version.version_number
    assert versions[0].is_current is True

def test_get_deck_version(mock_db_session, sample_deck, sample_version, app):
    """Test getting a specific version of a deck."""
    # Setup
    mock_db_session.query.return_value.filter_by.return_value.first_or_404.return_value = sample_version
    sample_deck.current_version_id = sample_version.id
    sample_version.deck = sample_deck
    
    # Execute
    response, status_code = DeckService.get_deck_version(1, 1)
    
    # Verify
    assert status_code == 200
    assert response.id == sample_version.id
    assert response.version_number == sample_version.version_number
    assert response.is_current is True

def test_get_deck_history(mock_db_session, sample_deck, app):
    """Test getting deck game history."""
    # Setup
    mock_db_session.query.return_value.options.return_value.get_or_404.return_value = sample_deck
    
    # Mock query results
    mock_result = MagicMock()
    mock_result.game_id = 1
    mock_result.game_date = datetime.utcnow().date()
    mock_result.version_number = 1
    mock_result.placement = 1
    
    mock_db_session.query.return_value.select_from.return_value.join.return_value\
        .outerjoin.return_value.outerjoin.return_value.outerjoin.return_value\
        .filter.return_value.order_by.return_value.all.return_value = [mock_result]
    
    # Execute
    history = DeckService.get_deck_history(1)
    
    # Verify
    assert len(history) == 1
    assert history[0].game_id == mock_result.game_id
    assert history[0].placement == mock_result.placement
    assert history[0].version_number == mock_result.version_number