from typing import List, Tuple, Dict, Optional
from datetime import datetime
from sqlalchemy import func

from ... import db
from ...models import User, MatchPlayer, Deck
from ..schemas.user_schemas import (
    UserRegistration, UserResponse, UserListResponse, UserProfileResponse
)

class UserService:
    """Service class for user-related operations."""

    @staticmethod
    def register_user(data: UserRegistration) -> Tuple[UserResponse, int]:
        """Register a new user.
        
        Args:
            data: User registration data
            
        Returns:
            Tuple[UserResponse, int]: User response and status code
            
        Raises:
            ValueError: If validation fails
        """
        # Validate input
        if error := data.validate():
            raise ValueError(error)

        # Check if username or email already exists
        if User.query.filter(
            (User.username == data.username) | (User.email == data.email)
        ).first():
            raise ValueError("Username or email already exists")

        try:
            # Create new user
            new_user = User(
                username=data.username,
                email=data.email
            )
            new_user.set_password(data.password)

            db.session.add(new_user)
            db.session.commit()

            # Create response
            response = UserResponse(
                id=new_user.id,
                username=new_user.username,
                email=new_user.email,
                registered_on=new_user.registered_on.isoformat(),
                avatar_url=new_user.avatar_url
            )
            return response, 201

        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Registration failed: {str(e)}")

    @staticmethod
    def get_users() -> List[UserListResponse]:
        """Get list of all users with their stats.
        
        Returns:
            List[UserListResponse]: List of users with basic info and stats
        """
        users = User.query.order_by(User.username).all()
        user_list = []

        for user in users:
            # Calculate wins for each user
            try:
                win_count = db.session.query(func.count(MatchPlayer.id)).filter(
                    MatchPlayer.user_id == user.id,
                    MatchPlayer.placement == 1
                ).scalar() or 0
            except Exception as e:
                win_count = 0

            user_list.append(UserListResponse(
                id=user.id,
                username=user.username,
                avatar_url=user.avatar_url,
                stats={"total_wins": win_count}
            ))

        return user_list

    @staticmethod
    def get_user_profile(user_id: int) -> Tuple[UserProfileResponse, int]:
        """Get public profile for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Tuple[UserProfileResponse, int]: User profile and status code
            
        Raises:
            ValueError: If user not found
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        try:
            # Calculate wins
            win_count = db.session.query(func.count(MatchPlayer.id)).filter(
                MatchPlayer.user_id == user_id,
                MatchPlayer.placement == 1
            ).scalar() or 0
        except Exception as e:
            win_count = 0

        response = UserProfileResponse(
            id=user.id,
            username=user.username,
            avatar_url=user.avatar_url,
            favorite_color=user.favorite_color,
            retirement_plane=user.retirement_plane,
            stats={"total_wins": win_count}
        )
        return response, 200

    @staticmethod
    def get_user_decks(user_id: int) -> List[Dict]:
        """Get decks for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List[Dict]: List of user's decks
            
        Raises:
            ValueError: If user not found
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        # Query decks through the model to get proper query interface
        decks = Deck.query.filter_by(user_id=user_id).order_by(Deck.last_updated.desc()).all()
        return [{
            "id": deck.id,
            "name": deck.name,
            "commander": deck.commander,
            "colors": deck.colors,
            "last_updated": deck.last_updated.isoformat()
        } for deck in decks]