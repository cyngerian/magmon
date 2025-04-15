> **Note:** This plan is obsolete as of 2025-04-06. The project proceeded with the existing `Game` model instead of the "Game Night" refactor described below.

# MagMon - Project Plan (Game Night Workflow)

## Goal
Refactor the application around a "Game Night" concept for tracking regular Monday night Commander games.

## Phases

### Phase 1: Database & Model Updates
- **Tasks:**
    - Add `GameNight` table (`id`, `game_date`, `status` ['Upcoming', 'Completed', 'Cancelled']).
    - Add `GameNightRegistration` table (`id`, `user_id`, `deck_id`, `game_night_id`).
    - Modify `Match` table: Add `game_night_id` foreign key. Remove `date_played`.
    - Update `backend/app/models.py` with new/modified models and relationships.
    - Generate and apply database migrations using Flask-Migrate.
- **Status:** Not Started

### Phase 2: Game Night Management (Backend & Frontend)
- **Tasks:**
    - Backend: Add API endpoints:
        - `POST /api/game-nights` (Manual creation, sets date to next Monday initially?).
        - `GET /api/game-nights` (List upcoming/past nights, perhaps with status filter).
    - Frontend: Create a new page/route (`/game-nights`).
        - Display list of Game Nights.
        - Add a "Create Next Game Night" button (visible to admin/all users?).
- **Status:** Not Started

### Phase 3: Deck Registration for Game Night (Backend & Frontend)
- **Tasks:**
    - Backend: Add API endpoint `POST /api/game-nights/<game_night_id>/registrations` (Registers logged-in user's chosen deck for the night). Needs logic to prevent multiple registrations per user per night.
    - Frontend: On the `/game-nights` page (or a detail view for a specific night):
        - Allow users to select an "Upcoming" night.
        - Provide a dropdown of the logged-in user's decks.
        - Add a "Register Deck" button.
        - Display players/decks already registered for the selected night.
- **Status:** Not Started

### Phase 4: Match Submission Overhaul (Backend & Frontend)
- **Tasks:**
    - Backend: Modify `POST /api/matches` endpoint:
        - Expect `game_night_id` instead of `date_played`.
        - Validate that players/decks submitted were actually registered for that `game_night_id`.
        - Update `GameNight` status to 'Completed' (or similar) upon successful match submission?
    - Frontend: Modify `/submit-match` page:
        - Step 1: Select an "Upcoming" or "In Progress" Game Night.
        - Step 2: Populate player/deck dropdowns based ONLY on players/decks registered for *that specific night*.
        - Step 3: User confirms actual participants for the pod (maybe checkboxes?).
        - Step 4: Select winner/loser from confirmed participants.
        - Step 5: Add notes.
        - Step 6: Submit.
- **Status:** Not Started

### Phase 5: View Deck Details (Backend & Frontend)
- **Tasks:**
    - Backend: Add `GET /api/decks/<deck_id>` endpoint to return full deck details including `decklist_text`. Add authorization check (is owner?).
    - Frontend: Update the "View" button functionality on the `/decks` page to fetch and display the full details (e.g., in the existing modal/section).
- **Status:** Not Started

### Phase 6: UI Compaction (Frontend)
- **Tasks:**
    - Apply CSS overrides (e.g., in `custom.css`) to reduce padding/margins.
    - Consider using `<table>` for data-dense lists (Game Nights, Deck List).
    - Adjust font sizes if necessary.
- **Status:** Not Started

### Future Enhancements
- Automatic Game Night creation (scheduler/cron).
- Match Approval Workflow.
- Statistics Pages (Player stats, Deck stats, Season stats).
- User Profiles.
- JWT Authentication.
- Admin panel/features.
- AWS Deployment preparation (Docker refinement, environment variables).
