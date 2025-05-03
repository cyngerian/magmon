# Route Migration Plan

## Phase 1: Match Routes Migration

### Steps
1. Create `backend/app/api/routes/matches.py`
2. Move match-related validation helpers:
   - `validate_match_status`
3. Move all match endpoints (lines 286-603)
4. Update imports in matches.py:
   ```python
   from flask import request, jsonify, current_app
   from flask_jwt_extended import jwt_required, get_jwt_identity
   from datetime import datetime
   from .. import bp
   from ...models import Match, MatchPlayer, User, Game, GameStatus, DeckVersion
   ```
5. Update `__init__.py` to import matches module

### Endpoints to Move
- `/matches POST` - submit_match
- `/matches GET` - get_matches
- `/matches/:id GET` - get_match_details
- `/matches/:id/approve PATCH`
- `/matches/:id/reject PATCH`

## Phase 2: User Routes Migration

### Steps
1. Create `backend/app/api/routes/users.py`
2. Move user endpoints (lines 55-149)
3. Update imports in users.py:
   ```python
   from flask import request, jsonify, current_app
   from flask_jwt_extended import create_access_token, create_refresh_token
   from .. import bp
   from ...models import User, Deck, MatchPlayer
   from sqlalchemy import func
   ```
4. Update `__init__.py` to import users module

### Endpoints to Move
- `/register POST`
- `/users GET`
- `/users/:id GET`
- `/users/:id/decks GET`

## Phase 3: Profile Routes Migration

### Steps
1. Create `backend/app/api/routes/profile.py`
2. Move helper functions:
   - `allowed_file`
   - File upload constants
3. Move profile endpoints (lines 155-284)
4. Update imports in profile.py:
   ```python
   from flask import request, jsonify, current_app, url_for
   from flask_jwt_extended import jwt_required, get_jwt_identity
   from werkzeug.utils import secure_filename
   import os
   from .. import bp
   from ...models import User
   ```
4. Update `__init__.py` to import profile module

### Endpoints to Move
- `/profile GET`
- `/profile PATCH`
- `/profile/avatar POST`

## Phase 4: Service Layer Setup

### Service Classes
```python
# services/match_service.py
class MatchService:
    def submit_match(...)
    def approve_match(...)
    def reject_match(...)

# services/user_service.py
class UserService:
    def register_user(...)
    def get_user_profile(...)

# services/profile_service.py
class ProfileService:
    def update_profile(...)
    def upload_avatar(...)
```

### Steps
1. Create service classes
2. Move business logic from routes to services
3. Update route handlers to use services

## Phase 5: Schema Implementation

### Schema Classes
```python
# schemas/match_schemas.py
class MatchSubmission:
    game_id: int
    placements: List[PlayerPlacement]

# schemas/user_schemas.py
class UserRegistration:
    username: str
    email: str
    password: str

# schemas/profile_schemas.py
class ProfileUpdate:
    favorite_color: Optional[str]
    retirement_plane: Optional[str]
```

### Steps
1. Create schema classes
2. Add request/response validation
3. Update routes to use schemas

## Testing Strategy

### Unit Tests
- Test each service method
- Test schema validation
- Mock database interactions

### Integration Tests
- Test complete workflows
- Verify API responses
- Test error handling

### API Compatibility Tests
- Ensure response formats match existing API
- Verify all existing frontend functionality