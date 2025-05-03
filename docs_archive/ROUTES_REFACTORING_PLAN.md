# Routes Refactoring Plan

## Goals
1. Improve code organization and maintainability
2. Preserve existing UI flow and functionality
3. Reduce code duplication
4. Make testing easier

## Phase 1: Setup & Infrastructure (1-2 days)
1. Create new directory structure:
   ```
   backend/app/api/
   ├── routes/
   │   ├── __init__.py
   │   ├── decks.py      # Deck management endpoints
   │   ├── users.py      # User management endpoints
   │   └── profile.py    # Profile management endpoints
   ├── services/
   │   ├── __init__.py
   │   ├── deck_service.py    # Deck management logic
   │   ├── user_service.py    # User management logic
   │   └── profile_service.py # Profile management logic
   ├── schemas/
   │   ├── __init__.py
   │   ├── deck_schemas.py    # Deck-related schemas
   │   ├── user_schemas.py    # User-related schemas
   │   └── profile_schemas.py # Profile-related schemas
   └── utils/
       ├── __init__.py
       ├── auth.py
       ├── validation.py
       └── error_handlers.py
   ```

2. Set up common utilities:
   - Error handling decorators
   - Request validation helpers
   - Authentication utilities
   - Response formatting

3. Create base test infrastructure:
   - API test fixtures
   - Mock service helpers
   - Test database setup

## Phase 2: Game/Match Consolidation (2-3 days)
Follow GAME_MATCH_MERGE_PLAN.md to:

1. Consolidate route logic:
   - Group related game/match functions
   - Document game lifecycle flow
   - Keep existing endpoints working

2. Consolidate common logic:
   - Move shared validation code into helpers
   - Update terminology to prefer "game" over "match"
   - Improve error messages and documentation

3. Write tests:
   - Unit tests for validation helpers
   - Integration tests for game lifecycle
   - API compatibility tests

## Phase 3: Deck Module (2-3 days)
1. Create schemas:
   - Deck schemas
   - Version schemas
   - History response schemas

2. Extract deck service:
   - Deck management logic
   - Version control logic
   - History tracking

3. Create deck routes:
   - Move and refactor existing endpoints
   - Add validation
   - Use deck service

4. Write tests:
   - Unit tests for deck service
   - Integration tests for endpoints
   - Version control tests

## Phase 5: User & Profile Module (2-3 days)
1. Create schemas:
   ```python
   class UserRegistration:
       username: str
       email: str
       password: str

   class ProfileUpdate:
       favorite_color: Optional[str]
       retirement_plane: Optional[str]
   ```

2. Extract services:
   ```python
   class UserService:
       def register_user(...)
       def get_user_profile(...)

   class ProfileService:
       def update_profile(...)
       def upload_avatar(...)
   ```

3. Create route modules:
   a. User Routes:
      - Create `backend/app/api/routes/users.py`
      - Move registration and user listing endpoints
      - Update imports and `__init__.py`
   
   b. Profile Routes:
      - Create `backend/app/api/routes/profile.py`
      - Move profile management and avatar endpoints
      - Move helper functions (allowed_file, etc.)
      - Update imports and `__init__.py`

4. Write tests:
   - Unit tests for user and profile services
   - Integration tests for endpoints
   - Authentication tests
   - File upload tests

## Phase 6: Clean Up & Documentation (1-2 days)
1. Remove old routes.py file
2. Update API documentation
3. Add service layer documentation
4. Update technical README
5. Performance testing
6. Security review

## Implementation Strategy

### For Each Module:
1. Create new files without removing old code
2. Write tests for new implementation
3. Gradually migrate endpoints one at a time
4. Verify functionality with integration tests
5. Remove old code once verified

### Testing Approach:
1. Write tests before refactoring each endpoint
2. Use pytest fixtures for common setup
3. Mock service layer in route tests
4. Integration tests for full workflow
5. Compare responses between old and new implementations

### Risk Mitigation:
1. Small, incremental changes
2. Comprehensive testing at each step
3. Maintain API compatibility
4. Ability to quickly rollback changes
5. Keep old routes until new ones are verified

## Success Criteria
1. All tests passing
2. No changes to API responses
3. Improved code organization
4. Better test coverage
5. Clearer documentation
6. No performance regression
7. Frontend continues to work without changes

## Time Estimate
- Total: 8-12 days
- Can be parallelized if multiple developers
- Additional time for review and QA

## Dependencies
1. Phase 1 must complete first
2. Game/Match consolidation should be done before other modules
3. Clean up phase must be last

## Current Status
- ✓ Phase 1: Setup & Infrastructure completed
- ⚡ Phase 2: Game/Match Consolidation in progress
- Phase 3: Deck Module pending
- Phase 4: User & Profile Module pending
- Phase 5: Clean Up & Documentation pending