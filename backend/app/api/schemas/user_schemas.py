from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime

@dataclass
class UserRegistration:
    """Schema for user registration request data."""
    username: str
    email: str
    password: str

    def validate(self) -> Optional[str]:
        """Validate registration data.
        
        Returns:
            Optional[str]: Error message if validation fails, None if valid
        """
        if not self.username or len(self.username) < 3:
            return "Username must be at least 3 characters long"
        if not self.email or '@' not in self.email:
            return "Invalid email address"
        if not self.password or len(self.password) < 8:
            return "Password must be at least 8 characters long"
        return None

@dataclass
class UserResponse:
    """Schema for user response data."""
    id: int
    username: str
    email: str
    registered_on: str
    avatar_url: Optional[str] = None

@dataclass
class UserListResponse:
    """Schema for user list response data."""
    id: int
    username: str
    avatar_url: Optional[str]
    stats: Dict[str, int]  # total_wins, etc.

@dataclass
class UserProfileResponse:
    """Schema for public user profile response data."""
    id: int
    username: str
    avatar_url: Optional[str]
    favorite_color: Optional[str]
    retirement_plane: Optional[str]
    stats: Dict[str, int]  # total_wins, etc.