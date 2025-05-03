import os
from typing import Dict, Tuple, Optional
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask import current_app, url_for

from ... import db
from ...models import User
from ..schemas.profile_schemas import ProfileUpdate, ProfileResponse, AvatarUpdate

# Avatar configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER_REL = 'uploads/avatars'

class ProfileService:
    """Service class for profile-related operations."""

    @staticmethod
    def get_profile(user_id: int) -> Tuple[ProfileResponse, int]:
        """Get full profile for current user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Tuple[ProfileResponse, int]: Profile response and status code
            
        Raises:
            ValueError: If user not found
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        response = ProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            avatar_url=user.avatar_url,
            favorite_color=user.favorite_color,
            retirement_plane=user.retirement_plane,
            registered_on=user.registered_on.isoformat()
        )
        return response, 200

    @staticmethod
    def update_profile(user_id: int, data: ProfileUpdate) -> Tuple[ProfileResponse, int]:
        """Update profile fields.
        
        Args:
            user_id: ID of the user
            data: Profile update data
            
        Returns:
            Tuple[ProfileResponse, int]: Updated profile and status code
            
        Raises:
            ValueError: If validation fails or user not found
        """
        # Validate input
        if error := data.validate():
            raise ValueError(error)

        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        try:
            # Update fields if provided
            if data.favorite_color is not None:
                user.favorite_color = data.favorite_color
            if data.retirement_plane is not None:
                user.retirement_plane = data.retirement_plane

            db.session.add(user)
            db.session.commit()

            # Create response
            response = ProfileResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                avatar_url=user.avatar_url,
                favorite_color=user.favorite_color,
                retirement_plane=user.retirement_plane,
                registered_on=user.registered_on.isoformat()
            )
            return response, 200

        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Profile update failed: {str(e)}")

    @staticmethod
    def upload_avatar(user_id: int, file: FileStorage) -> Tuple[AvatarUpdate, int]:
        """Handle avatar upload and update.
        
        Args:
            user_id: ID of the user
            file: Uploaded file
            
        Returns:
            Tuple[AvatarUpdate, int]: Avatar update response and status code
            
        Raises:
            ValueError: If file invalid or upload fails
        """
        if not file or file.filename == '':
            raise ValueError("No file provided")

        if not ProfileService._allowed_file(file.filename):
            raise ValueError("File type not allowed")

        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        try:
            # Create secure filename
            filename = secure_filename(f"user_{user_id}_avatar.{file.filename.rsplit('.', 1)[1].lower()}")
            
            # Get upload path
            upload_folder = os.path.join(current_app.static_folder, UPLOAD_FOLDER_REL)
            filepath = os.path.join(upload_folder, filename)

            # Save file
            file.save(filepath)

            # Update user's avatar URL
            url_path = os.path.join(UPLOAD_FOLDER_REL, filename)
            avatar_url = url_for('static', filename=url_path, _external=False)
            
            user.avatar_url = avatar_url
            db.session.add(user)
            db.session.commit()

            return AvatarUpdate.from_url(avatar_url), 200

        except Exception as e:
            db.session.rollback()
            # Clean up file if it was saved
            if 'filepath' in locals() and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass  # Already logged in routes
            raise ValueError(f"Avatar upload failed: {str(e)}")

    @staticmethod
    def _allowed_file(filename: str) -> bool:
        """Check if file extension is allowed.
        
        Args:
            filename: Name of the file
            
        Returns:
            bool: True if extension is allowed, False otherwise
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS