"""
Tests for deck routes.
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_jwt_extended import create_access_token, JWTManager, get_jwt_identity

from backend.app import create_app
from backend.app.api.routes.decks import bp
from backend.app.api.services.deck_service import DeckService
from backend.app.api.schemas.deck_schemas import (
    DeckResponse, DeckListResponse, DeckVersionResponse,
    DeckHistoryEntry, DeckVersionListResponse
)

@pytest.fixture
def app():
    """Create a Flask application for testing."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'JWT_SECRET_KEY': 'test-secret',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    JWTManager(app)
    app.config.update({
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'JWT_SECRET_KEY': 'test-secret',
        'JWT_ACCESS_TOKEN_EXPIRES': False,  # Disable token expiration for testing
        'JWT_ERROR_MESSAGE_KEY': 'message',
        'TESTING': True,
        'DEBUG': True
    })
    JWTManager(app)
    app.register_blueprint(bp, url_prefix='/api', name='test_api')
    return app

@pytest.fixture
def jwt_mock():
    """Mock JWT verification."""
    jwt_data = {'sub': 1}
    jwt_header = {'alg': 'HS256'}
    jwt_location = 'headers'
    with patch('flask_jwt_extended.view_decorators._decode_jwt_from_request',
              return_value=(jwt_data, jwt_header, jwt_location)):
        yield

@pytest.fixture
def test_client(app, jwt_mock):
    """Create a test client with app context."""
    with app.test_client() as client:
        with app.app_context():
            with patch('flask_jwt_extended.utils.get_jwt_identity', return_value=1):
                yield client
    return app

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def auth_headers():
    """Create authentication headers."""
    return {'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'}

@pytest.fixture
def sample_deck_response():
    """Create a sample deck response."""
    return DeckResponse(
        id=1,
        name="Test Deck",
        commander="Test Commander",
        colors="WUB",
        decklist_text="1 Test Card",
        user_id=1,
        created_at=datetime.utcnow().isoformat(),
        last_updated=datetime.utcnow().isoformat(),
        current_version_id=1
    )

def test_create_deck(test_client, auth_headers, sample_deck_response):
    """Test POST /api/decks endpoint."""
    # Setup
    deck_data = {
        "name": "Test Deck",
        "commander": "Test Commander",
        "colors": "WUB",
        "decklist_text": "1 Test Card"
    }
    
    with patch.object(DeckService, 'create_deck', return_value=(sample_deck_response, 201)):
        # Execute
        response = test_client.post('/api/decks', json=deck_data, headers=auth_headers)
    
    # Verify
    assert response.status_code == 201
    assert response.json['deck']['name'] == deck_data['name']
    assert response.json['deck']['commander'] == deck_data['commander']

def test_create_deck_invalid_data(test_client, auth_headers):
    """Test POST /api/decks with invalid data."""
    # Missing required fields
    response = test_client.post('/api/decks', json={}, headers=auth_headers)
    assert response.status_code == 400
    
    # Missing commander
    response = test_client.post('/api/decks', json={"name": "Test"}, headers=auth_headers)
    assert response.status_code == 400

def test_get_user_decks(test_client, auth_headers):
    """Test GET /api/decks endpoint."""
    # Setup
    deck_list = [
        DeckListResponse(
            id=1,
            name="Test Deck 1",
            commander="Commander 1",
            colors="WUB",
            last_updated=datetime.utcnow().isoformat()
        ),
        DeckListResponse(
            id=2,
            name="Test Deck 2",
            commander="Commander 2",
            colors="RG",
            last_updated=datetime.utcnow().isoformat()
        )
    ]
    
    with patch.object(DeckService, 'get_user_decks', return_value=deck_list):
        # Execute
        response = test_client.get('/api/decks', headers=auth_headers)
    
    # Verify
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]['name'] == deck_list[0].name
    assert response.json[1]['name'] == deck_list[1].name

def test_get_deck_details(test_client, auth_headers, sample_deck_response):
    """Test GET /api/decks/<deck_id> endpoint."""
    with patch.object(DeckService, 'get_deck_details', return_value=(sample_deck_response, 200)):
        # Execute
        response = test_client.get('/api/decks/1', headers=auth_headers)
    
    # Verify
    assert response.status_code == 200
    assert response.json['name'] == sample_deck_response.name
    assert response.json['commander'] == sample_deck_response.commander

def test_create_deck_version(test_client, auth_headers):
    """Test POST /api/decks/<deck_id>/versions endpoint."""
    # Setup
    version_data = {
        "decklist_text": "2 New Card",
        "notes": "Updated version"
    }
    
    version_response = DeckVersionResponse(
        id=2,
        version_number=2,
        created_at=datetime.utcnow().isoformat(),
        notes=version_data['notes'],
        decklist_text=version_data['decklist_text'],
        is_current=True
    )
    
    with patch.object(DeckService, 'create_deck_version', return_value=(version_response, 201)):
        # Execute
        response = test_client.post('/api/decks/1/versions', json=version_data, headers=auth_headers)
    
    # Verify
    assert response.status_code == 201
    assert response.json['version']['version_number'] == version_response.version_number
    assert response.json['version']['notes'] == version_response.notes

def test_create_deck_version_unauthorized(test_client, auth_headers):
    """Test POST /api/decks/<deck_id>/versions with unauthorized user."""
    version_data = {
        "decklist_text": "2 New Card",
        "notes": "Updated version"
    }
    
    with patch.object(DeckService, 'create_deck_version', side_effect=PermissionError("You don't own this deck")):
        # Execute
        response = test_client.post('/api/decks/1/versions', json=version_data, headers=auth_headers)
    
    # Verify
    assert response.status_code == 403
    assert "don't own this deck" in response.json['error']

def test_get_deck_versions(test_client, auth_headers):
    """Test GET /api/decks/<deck_id>/versions endpoint."""
    # Setup
    versions = [
        DeckVersionListResponse(
            id=1,
            version_number=1,
            created_at=datetime.utcnow().isoformat(),
            notes="Initial version",
            is_current=False
        ),
        DeckVersionListResponse(
            id=2,
            version_number=2,
            created_at=datetime.utcnow().isoformat(),
            notes="Updated version",
            is_current=True
        )
    ]
    
    with patch.object(DeckService, 'get_deck_versions', return_value=versions):
        # Execute
        response = test_client.get('/api/decks/1/versions', headers=auth_headers)
    
    # Verify
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]['version_number'] == versions[0].version_number
    assert response.json[1]['is_current'] == versions[1].is_current

def test_get_deck_version(test_client, auth_headers):
    """Test GET /api/decks/<deck_id>/versions/<version_id> endpoint."""
    # Setup
    version = DeckVersionResponse(
        id=1,
        version_number=1,
        created_at=datetime.utcnow().isoformat(),
        notes="Initial version",
        decklist_text="1 Test Card",
        is_current=True
    )
    
    with patch.object(DeckService, 'get_deck_version', return_value=(version, 200)):
        # Execute
        response = test_client.get('/api/decks/1/versions/1', headers=auth_headers)
    
    # Verify
    assert response.status_code == 200
    assert response.json['version_number'] == version.version_number
    assert response.json['decklist_text'] == version.decklist_text

def test_get_deck_history(test_client, auth_headers):
    """Test GET /api/decks/<deck_id>/history endpoint."""
    # Setup
    history = [
        DeckHistoryEntry(
            game_id=1,
            game_date=datetime.utcnow().date().isoformat(),
            placement=1,
            version_number=1
        ),
        DeckHistoryEntry(
            game_id=2,
            game_date=datetime.utcnow().date().isoformat(),
            placement=2,
            version_number=2
        )
    ]
    
    with patch.object(DeckService, 'get_deck_history', return_value=history):
        # Execute
        response = test_client.get('/api/decks/1/history', headers=auth_headers)
    
    # Verify
    assert response.status_code == 200
    assert len(response.json) == 2
    assert response.json[0]['game_id'] == history[0].game_id
    assert response.json[1]['placement'] == history[1].placement