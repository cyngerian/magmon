# API Route Refactoring Status - 2025-04-15

## Overall Goal

Refactor the monolithic `backend/app/api/routes.py` file to improve organization and maintainability, following both `GAME_MATCH_MERGE_PLAN.md` for game lifecycle logic and `ROUTES_REFACTORING_PLAN.md` for other routes.

## Accomplished Today

*   **Started Game/Match Consolidation:**
    *   Created `GAME_MATCH_MERGE_PLAN.md` to guide the consolidation
    *   Identified game lifecycle stages and related endpoints
    *   Documented the unified game/match concept
*   **Infrastructure Setup:**
    *   Created new directory structure: `routes/`, `services/`, `schemas/`, `utils/`
    *   Created initial utility modules: `utils/error_handlers.py` and `utils/auth.py`
    *   Moved `admin_required` decorator and `generate_temp_password` to `utils/auth.py`
    *   Registered common error handlers in `api/__init__.py`
*   **Deck Module:**
    *   Moved Deck routes to `routes/decks.py`
    *   Removed Deck routes section from `routes.py`
    *   Updated imports in `__init__.py`

## Current Task

*   **Game/Match Consolidation:**
    *   Reorder functions in `routes.py` to group game lifecycle logic
    *   Update terminology to prefer "game results" over "match"
    *   Add lifecycle documentation to functions
    *   Move shared validation code into helper functions

## Next Steps (Immediate)

1.  Follow `GAME_MATCH_MERGE_PLAN.md` steps:
    - Group related game/match functions
    - Consolidate common validation logic
    - Update terminology and documentation
2.  Run tests to verify changes
3.  Commit consolidated game lifecycle changes

## Next Steps (Overall Plan)

*   Complete game/match consolidation
*   Move User routes to `routes/users.py`
*   Move Profile routes to `routes/profile.py`
*   Update `api/__init__.py` imports accordingly
*   Add/update integration tests