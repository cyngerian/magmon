# User & Profile Module Refactoring Plan

## Overview

Refactor user and profile-related functionality from `routes.py` into separate modules following the established pattern of schemas, services, and routes.

## Components

### 1. Schemas

#### User Schemas (`schemas/user_schemas.py`)
```python
@dataclass
class UserRegistration:
    username: str
    email: str
    password: str

@dataclass
class UserResponse:
    id: int
    username: str
    email: str
    registered_on: str
    avatar_url: Optional[str]

@dataclass
class UserListResponse:
    id: int
    username: str
    avatar_url: Optional[str]
    stats: Dict[str, int]  # total_wins, etc.
```

#### Profile Schemas (`schemas/profile_schemas.py`)
```python
@dataclass
class ProfileUpdate:
    favorite_color: Optional[str]
    retirement_plane: Optional[str]

@dataclass
class ProfileResponse:
    id: int
    username: str
    email: str
    avatar_url: Optional[str]
    favorite_color: Optional[str]
    retirement_plane: Optional[str]
    registered_on: str
```

### 2. Services

#### User Service (`services/user_service.py`)
```python
class UserService:
    @staticmethod
    def register_user(data: UserRegistration) -> Tuple[UserResponse, int]:
        """Register a new user"""

    @staticmethod
    def get_users() -> List[UserListResponse]:
        """Get list of all users with stats"""

    @staticmethod
    def get_user_profile(user_id: int) -> Tuple[UserResponse, int]:
        """Get public profile for specific user"""

    @staticmethod
    def get_user_decks(user_id: int) -> List[DeckListResponse]:
        """Get decks for specific user"""
```

#### Profile Service (`services/profile_service.py`)
```python
class ProfileService:
    @staticmethod
    def get_profile(user_id: int) -> Tuple[ProfileResponse, int]:
        """Get full profile for current user"""

    @staticmethod
    def update_profile(user_id: int, data: ProfileUpdate) -> Tuple[ProfileResponse, int]:
        """Update profile fields"""

    @staticmethod
    def upload_avatar(user_id: int, file: FileStorage) -> Tuple[Dict[str, str], int]:
        """Handle avatar upload and update"""
```

### 3. Routes

#### User Routes (`routes/users.py`)
```python
@bp.route('/register', methods=['POST'])
def register_user():
    """Register new user endpoint"""

@bp.route('/users', methods=['GET'])
def get_users():
    """List all users endpoint"""

@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile endpoint"""

@bp.route('/users/<int:user_id>/decks', methods=['GET'])
def get_user_decks(user_id):
    """Get user's decks endpoint"""
```

#### Profile Routes (`routes/profile.py`)
```python
@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_my_profile():
    """Get own profile endpoint"""

@bp.route('/profile', methods=['PATCH'])
@jwt_required()
def update_my_profile():
    """Update profile endpoint"""

@bp.route('/profile/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """Upload avatar endpoint"""
```

### 4. Utils

Move avatar-related utilities to a new module:

#### Avatar Utils (`utils/avatar.py`)
```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER_REL = 'uploads/avatars'

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""

def save_avatar(file: FileStorage, user_id: int) -> str:
    """Save avatar file and return URL"""
```

## Implementation Steps

1. Create Schema Files
   - Create user_schemas.py and profile_schemas.py
   - Define all dataclasses with proper types
   - Add validation where needed

2. Create Service Layer
   - Implement UserService with user management logic
   - Implement ProfileService with profile management logic
   - Move business logic from routes into services
   - Add proper error handling and logging

3. Create Route Modules
   - Create users.py and profile.py route modules
   - Move endpoints from routes.py
   - Update to use new services and schemas
   - Maintain existing URL structure and responses

4. Create Utils
   - Move avatar handling code to utils/avatar.py
   - Refactor for reusability
   - Add proper error handling

5. Write Tests
   - Schema validation tests
   - Service layer unit tests
   - Route integration tests
   - Avatar upload tests

6. Update Documentation
   - Add docstrings to all new modules
   - Update API documentation
   - Update technical README

## Testing Strategy

1. Schema Tests
   - Test validation of registration data
   - Test validation of profile updates
   - Test response serialization

2. Service Tests
   - Test user registration flow
   - Test profile updates
   - Test avatar uploads
   - Test error cases

3. Route Tests
   - Test all endpoints with valid data
   - Test authentication requirements
   - Test error responses
   - Test file uploads

4. Integration Tests
   - Test full user registration flow
   - Test profile update with avatar
   - Test user listing with stats

## Migration Strategy

1. Create new files without removing old code
2. Write tests for new implementation
3. Gradually migrate endpoints one at a time
4. Verify functionality with integration tests
5. Remove old code once verified

## Success Criteria

1. All tests passing
2. No changes to API responses
3. Improved code organization
4. Better test coverage
5. Clearer documentation
6. No performance regression
7. Frontend continues to work without changes

Would you like to proceed with implementing this plan in Code mode?