from datetime import datetime
from backend.app.api.schemas.user_schemas import (
    UserRegistration, UserResponse, UserListResponse, UserProfileResponse
)
from backend.app.api.schemas.profile_schemas import (
    ProfileUpdate, ProfileResponse, AvatarUpdate
)

def test_user_registration_validation():
    """Test UserRegistration schema validation."""
    # Test valid data
    data = UserRegistration(
        username="testuser",
        email="test@example.com",
        password="password123"
    )
    assert data.validate() is None

    # Test invalid username
    data = UserRegistration(
        username="ab",  # too short
        email="test@example.com",
        password="password123"
    )
    assert data.validate() is not None
    assert "Username" in data.validate()

    # Test invalid email
    data = UserRegistration(
        username="testuser",
        email="invalid-email",  # missing @
        password="password123"
    )
    assert data.validate() is not None
    assert "email" in data.validate()

    # Test invalid password
    data = UserRegistration(
        username="testuser",
        email="test@example.com",
        password="short"  # too short
    )
    assert data.validate() is not None
    assert "Password" in data.validate()

def test_profile_update_validation():
    """Test ProfileUpdate schema validation."""
    # Test valid data
    data = ProfileUpdate(
        favorite_color="Blue",
        retirement_plane="Ravnica"
    )
    assert data.validate() is None

    # Test optional fields
    data = ProfileUpdate()  # all fields optional
    assert data.validate() is None

    # Test field length validation
    data = ProfileUpdate(
        favorite_color="B" * 51,  # too long
        retirement_plane="R" * 101  # too long
    )
    assert data.validate() is not None
    assert "color" in data.validate()

    data = ProfileUpdate(
        favorite_color="Blue",
        retirement_plane="R" * 101  # too long
    )
    assert data.validate() is not None
    assert "plane" in data.validate()

def test_response_schemas():
    """Test response schema creation."""
    now = datetime.utcnow().isoformat()

    # Test UserResponse
    user_response = UserResponse(
        id=1,
        username="testuser",
        email="test@example.com",
        registered_on=now,
        avatar_url="/static/uploads/avatars/user_1_avatar.png"
    )
    assert user_response.id == 1
    assert user_response.username == "testuser"
    assert user_response.avatar_url is not None

    # Test UserListResponse
    user_list = UserListResponse(
        id=1,
        username="testuser",
        avatar_url="/static/uploads/avatars/user_1_avatar.png",
        stats={"total_wins": 5}
    )
    assert user_list.id == 1
    assert user_list.stats["total_wins"] == 5

    # Test UserProfileResponse
    profile = UserProfileResponse(
        id=1,
        username="testuser",
        avatar_url="/static/uploads/avatars/user_1_avatar.png",
        favorite_color="Blue",
        retirement_plane="Ravnica",
        stats={"total_wins": 5}
    )
    assert profile.id == 1
    assert profile.favorite_color == "Blue"
    assert profile.stats["total_wins"] == 5

    # Test ProfileResponse
    profile_response = ProfileResponse(
        id=1,
        username="testuser",
        email="test@example.com",
        avatar_url="/static/uploads/avatars/user_1_avatar.png",
        favorite_color="Blue",
        retirement_plane="Ravnica",
        registered_on=now
    )
    assert profile_response.id == 1
    assert profile_response.favorite_color == "Blue"
    assert profile_response.registered_on == now

def test_avatar_update():
    """Test AvatarUpdate schema."""
    url = "/static/uploads/avatars/user_1_avatar.png"
    
    # Test direct creation
    avatar = AvatarUpdate(avatar_url=url)
    assert avatar.avatar_url == url

    # Test factory method
    avatar = AvatarUpdate.from_url(url)
    assert avatar.avatar_url == url