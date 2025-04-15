import pytest
from datetime import datetime, timedelta
from app.models import User # Import relative to the /app directory inside the container

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

# TODO: Add tests for temporary password logic (requires mocking datetime)
# TODO: Add tests for update_last_login (requires mocking datetime)