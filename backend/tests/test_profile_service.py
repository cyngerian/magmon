import os
from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch
from werkzeug.datastructures import FileStorage
from io import BytesIO
from flask import Flask

from backend.app import create_app

from backend.app.models import User
from backend.app.api.schemas.profile_schemas import ProfileUpdate
from backend.app.api.services.profile_service import ProfileService

@pytest.fixture
def app():
    """Create a Flask application object."""
    app = create_app('testing')
    return app

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
        avatar_url="/static/uploads/avatars/user_1_avatar.png",
        favorite_color="Blue",
        retirement_plane="Ravnica"
    )
    return user

@pytest.fixture
def mock_file():
    """Create a mock file for avatar upload testing."""
    return FileStorage(
        stream=BytesIO(b"test content"),
        filename="test.png",
        content_type="image/png"
    )

def test_get_profile(mock_db_session, sample_user):
    """Test getting user profile."""
    # Mock User.query
    mock_query = MagicMock()
    mock_query.get.return_value = sample_user
    User.query = mock_query

    # Execute
    response, status_code = ProfileService.get_profile(1)

    # Verify
    assert status_code == 200
    assert response.id == sample_user.id
    assert response.username == sample_user.username
    assert response.email == sample_user.email
    assert response.favorite_color == sample_user.favorite_color
    assert response.retirement_plane == sample_user.retirement_plane

def test_get_profile_not_found(mock_db_session):
    """Test getting profile of non-existent user."""
    # Mock User.query to return None
    mock_query = MagicMock()
    mock_query.get.return_value = None
    User.query = mock_query

    # Execute and verify
    with pytest.raises(ValueError) as exc:
        ProfileService.get_profile(999)
    assert "not found" in str(exc.value)

def test_update_profile(mock_db_session, sample_user):
    """Test updating profile fields."""
    # Setup
    data = ProfileUpdate(
        favorite_color="Red",
        retirement_plane="Innistrad"
    )

    # Mock User.query
    mock_query = MagicMock()
    mock_query.get.return_value = sample_user
    User.query = mock_query

    # Execute
    response, status_code = ProfileService.update_profile(1, data)

    # Verify
    assert status_code == 200
    assert response.favorite_color == data.favorite_color
    assert response.retirement_plane == data.retirement_plane
    assert mock_db_session.add.called
    assert mock_db_session.commit.called

def test_update_profile_validation(mock_db_session, sample_user):
    """Test profile update validation."""
    # Setup - create too long values
    data = ProfileUpdate(
        favorite_color="B" * 51,  # too long
        retirement_plane="R" * 101  # too long
    )

    # Mock User.query
    mock_query = MagicMock()
    mock_query.get.return_value = sample_user
    User.query = mock_query

    # Execute and verify
    with pytest.raises(ValueError) as exc:
        ProfileService.update_profile(1, data)
    assert "color" in str(exc.value)
    assert not mock_db_session.commit.called

def test_upload_avatar(app, mock_db_session, sample_user, mock_file):
    """Test avatar upload."""
    # Mock User.query
    mock_query = MagicMock()
    mock_query.get.return_value = sample_user
    User.query = mock_query

    # Mock file operations within app context
    with app.test_request_context():
        app.config['STATIC_FOLDER'] = '/test/static'
        with patch('os.path.join') as mock_join, \
             patch('werkzeug.utils.secure_filename', return_value='user_1_avatar.png'), \
             patch('flask.url_for', return_value='/static/uploads/avatars/user_1_avatar.png'), \
             patch.object(FileStorage, 'save') as mock_save:
            
            # Configure os.path.join to handle both static folder and URL paths
            def join_side_effect(*args):
                if args[0] == '/test/static':
                    return '/test/static/uploads/avatars/user_1_avatar.png'
                else:
                    return 'uploads/avatars/user_1_avatar.png'
            mock_join.side_effect = join_side_effect
            
            # Execute
            response, status_code = ProfileService.upload_avatar(1, mock_file)

        # Verify
        assert status_code == 200
        assert response.avatar_url == '/static/uploads/avatars/user_1_avatar.png'
        assert mock_save.called
        assert mock_db_session.commit.called

def test_upload_avatar_invalid_file(mock_db_session, sample_user):
    """Test avatar upload with invalid file."""
    # Create invalid file
    invalid_file = FileStorage(
        stream=BytesIO(b"test content"),
        filename="test.txt",  # invalid extension
        content_type="text/plain"
    )

    # Mock User.query
    mock_query = MagicMock()
    mock_query.get.return_value = sample_user
    User.query = mock_query

    # Execute and verify
    with pytest.raises(ValueError) as exc:
        ProfileService.upload_avatar(1, invalid_file)
    assert "not allowed" in str(exc.value)
    assert not mock_db_session.commit.called

def test_upload_avatar_no_file(mock_db_session, sample_user):
    """Test avatar upload with no file."""
    # Execute and verify
    with pytest.raises(ValueError) as exc:
        ProfileService.upload_avatar(1, None)
    assert "No file" in str(exc.value)
    assert not mock_db_session.commit.called

def test_upload_avatar_save_error(app, mock_db_session, sample_user, mock_file):
    """Test avatar upload with save error."""
    # Mock User.query
    mock_query = MagicMock()
    mock_query.get.return_value = sample_user
    User.query = mock_query

    # Mock file operations within app context
    with app.test_request_context():
        app.config['STATIC_FOLDER'] = '/test/static'
        with patch('os.path.join') as mock_join, \
             patch('werkzeug.utils.secure_filename', return_value='user_1_avatar.png'), \
             patch.object(FileStorage, 'save', side_effect=Exception("Save failed")), \
             patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:

            # Configure os.path.join to handle both static folder and URL paths
            def join_side_effect(*args):
                if args[0] == '/test/static':
                    return '/test/static/uploads/avatars/user_1_avatar.png'
                else:
                    return 'uploads/avatars/user_1_avatar.png'
            mock_join.side_effect = join_side_effect
            
            # Execute and verify
            with pytest.raises(ValueError) as exc:
                ProfileService.upload_avatar(1, mock_file)
            assert "failed" in str(exc.value)
            assert mock_db_session.rollback.called
            assert mock_remove.called  # Should try to clean up
        assert mock_db_session.rollback.called