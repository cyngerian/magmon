from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class ProfileUpdate:
    """Schema for profile update request data."""
    favorite_color: Optional[str] = None
    retirement_plane: Optional[str] = None

    def validate(self) -> Optional[str]:
        """Validate profile update data.
        
        Returns:
            Optional[str]: Error message if validation fails, None if valid
        """
        if self.favorite_color is not None and len(self.favorite_color) > 50:
            return "Favorite color must be less than 50 characters"
        if self.retirement_plane is not None and len(self.retirement_plane) > 100:
            return "Retirement plane must be less than 100 characters"
        return None

@dataclass
class ProfileResponse:
    """Schema for profile response data."""
    id: int
    username: str
    email: str
    avatar_url: Optional[str]
    favorite_color: Optional[str]
    retirement_plane: Optional[str]
    registered_on: str

@dataclass
class AvatarUpdate:
    """Schema for avatar update response."""
    avatar_url: str

    @staticmethod
    def from_url(url: str) -> 'AvatarUpdate':
        """Create AvatarUpdate instance from URL.
        
        Args:
            url: The URL of the uploaded avatar
            
        Returns:
            AvatarUpdate: New instance with the given URL
        """
        return AvatarUpdate(avatar_url=url)