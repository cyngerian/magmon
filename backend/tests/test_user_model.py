import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
from app.models import User # Import relative to the /app directory inside the container

@pytest.fixture
def mock_datetime():
    """Fixture to mock datetime.utcnow() for consistent testing."""
    with patch('app.models.datetime') as mock_dt:
        # Set a fixed "current" time for testing
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_dt.utcnow.return_value = mock_now
        yield mock_dt

@pytest.fixture
def mock_bcrypt():
    """Fixture to mock bcrypt for password hashing/checking."""
    with patch('app.models.bcrypt') as mock_bc:
        # Make generate_password_hash return a predictable value
        mock_bc.generate_password_hash.return_value = b'mocked_hash'
        # Make check_password_hash return True only for specific values
        def check_mock(stored_hash, password):
            return stored_hash == b'mocked_hash' and password == 'correct_password'
        mock_bc.check_password_hash.side_effect = check_mock
        yield mock_bc

# Note: For these tests to run without a database connection,
# they only test the logic within the model methods themselves.
# Testing database interactions would require setting up a test database
# and potentially using fixtures (e.g., with pytest-flask).

def test_password_setting():
    """Test setting a password hashes it correctly."""
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    assert user.password_hash is not None
    assert isinstance(user.password_hash, str)
    # Basic check: hash should not be the plain password
    assert user.password_hash != 'password123'
    # Check that temp password fields are cleared
    assert user.temp_password_hash is None
    assert user.temp_password_expires_at is None
    assert user.must_change_password is False

def test_password_checking():
    """Test checking a correct and incorrect password."""
    user = User(username='testuser2', email='test2@example.com')
    user.set_password('correct_password')

    # Check correct password
    assert user.check_password('correct_password') is True

    # Check incorrect password
    assert user.check_password('wrong_password') is False

def test_repr():
    """Test the __repr__ method."""
    user = User(username='repruser', email='repr@example.com')
    assert repr(user) == '<User repruser>'

def test_set_temp_password(mock_datetime, mock_bcrypt):
    """Test setting a temporary password."""
    user = User(username='tempuser', email='temp@example.com')
    
    # Set a temporary password with 24h expiry
    user.set_temp_password('temp123')
    
    # Check that temp password was set
    assert user.temp_password_hash == 'mocked_hash'
    assert user.must_change_password is True
    # Expiry should be 24 hours from mock time
    expected_expiry = datetime(2024, 1, 2, 12, 0, 0)  # mock_now + 24h
    assert user.temp_password_expires_at == expected_expiry

def test_check_password_with_temp(mock_datetime, mock_bcrypt):
    """Test password checking with temporary password."""
    user = User(username='tempuser', email='temp@example.com')
    
    # Set up regular password
    mock_bcrypt.generate_password_hash.return_value = b'regular_hash'
    user.set_password('regular_password')  # This will decode to string
    
    # Set up temp password
    mock_bcrypt.generate_password_hash.return_value = b'temp_hash'
    user.set_temp_password('temp_password')  # This will decode to string
    
    # Verify our understanding of the stored hashes
    assert user.password_hash == 'regular_hash'  # Stored as string
    assert user.temp_password_hash == 'temp_hash'  # Stored as string
    
    # Configure bcrypt mock to validate passwords
    def check_mock(stored_hash, password):
        # stored_hash will be encoded back to bytes by the model
        if stored_hash.encode('utf-8') == b'temp_hash' and password == 'temp_password':
            return True
        if stored_hash.encode('utf-8') == b'regular_hash' and password == 'regular_password':
            return True
        return False
    mock_bcrypt.check_password_hash.side_effect = check_mock

    # Test before expiry (1 hour after set)
    mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 13, 0, 0)
    assert user.check_password('temp_password') is True  # Temp password works
    assert user.check_password('regular_password') is True  # Regular password still works
    assert user.check_password('wrong_password') is False  # Wrong password fails

    # Test after expiry (48 hours after set)
    mock_datetime.utcnow.return_value = datetime(2024, 1, 3, 12, 0, 0)
    assert user.check_password('temp_password') is False  # Temp password expired
    assert user.check_password('regular_password') is True  # Regular password still works
    assert user.check_password('wrong_password') is False  # Wrong password still fails

def test_clear_temp_password():
    """Test clearing temporary password."""
    user = User(username='tempuser', email='temp@example.com')
    
    # Set up temp password state
    user.temp_password_hash = 'some_hash'
    user.temp_password_expires_at = datetime.utcnow() + timedelta(hours=24)
    user.must_change_password = True
    
    # Clear temp password
    user.clear_temp_password()
    
    # Verify all temp password fields are cleared
    assert user.temp_password_hash is None
    assert user.temp_password_expires_at is None
    assert user.must_change_password is False

def test_update_last_login(mock_datetime):
    """Test updating last login timestamp."""
    user = User(username='loginuser', email='login@example.com')
    
    # Update last login
    user.update_last_login()
    
    # Should be set to current time (from mock)
    assert user.last_login == datetime(2024, 1, 1, 12, 0, 0)