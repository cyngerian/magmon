# Player Profile & Deck History Features - Implementation Plan

**Overall Goal:** Enhance the MagMon application with player profiles, a player browsing section, and detailed deck game history.

**Proposed Implementation Phases:**

**Phase 1: Backend - Player Profile Data & API**

*   **Database Model (`User` in `models.py`):**
    *   Add new nullable fields: `favorite_color` (String), `retirement_plane` (String), `avatar_url` (String).
*   **Database Migration:**
    *   Generate migration script (`flask db migrate`).
    *   Review and apply migration (`flask db upgrade`).
*   **API Endpoints (`routes.py`):**
    *   `GET /api/users`: Modify to optionally include new profile fields in the response.
    *   `GET /api/users/<user_id>`: Create a new endpoint to fetch detailed public profile information for a specific user (username, profile fields, stats - stats added later).
    *   `GET /api/profile`: Create a new endpoint for the *logged-in* user to get their *own* profile data (requires authentication).
    *   `PATCH /api/profile`: Create a new endpoint for the *logged-in* user to update their own profile fields (color, plane). Avatar URL update will be handled separately. Requires authentication.

**Phase 2: Backend - Deck Game History API**

*   **Database Model (`Deck` in `models.py`):**
    *   Ensure necessary relationships exist to link a `Deck` to its `GameRegistration`s and associated `MatchPlayer` entries (to get placement). It looks like we can traverse `Deck -> GameRegistration -> Game -> Match -> MatchPlayer` or potentially optimize.
*   **API Endpoint (`routes.py`):**
    *   `GET /api/decks/<deck_id>/history`: Create a new endpoint. It should return a list of games the deck was registered in, including `game_id`, `game_date`, and the `placement` achieved by the user with that deck in the corresponding match (requires joining `GameRegistration`, `Game`, `Match`, `MatchPlayer`).

**Phase 3: Frontend - Profile Editing Page**

*   **Routing (`App.tsx`):** Add a new route, e.g., `/profile`.
*   **Navigation (`DashboardLayout`):** Add a "Profile" link near the "Welcome, user" area.
*   **New Page (`ProfilePage.tsx`):**
    *   Fetch logged-in user's data using `GET /api/profile`.
    *   Display current profile fields (color, plane) in an editable form.
    *   Handle form submission using `PATCH /api/profile`.
    *   (Avatar upload UI will be added in a later phase).

**Phase 4: Frontend - Players List Page**

*   **Routing (`App.tsx`):** Add a new route, e.g., `/players`.
*   **Navigation (`DashboardLayout`):** Add a "Players" link to the main navigation bar.
*   **New Page (`PlayersPage.tsx`):**
    *   Fetch the list of all users using `GET /api/users`.
    *   Display the list of usernames.
    *   Make each username a link to the player detail page (`/players/<user_id>`).

**Phase 5: Frontend - Player Detail Page (Layout & Basic Info)**

*   **Routing (`App.tsx`):** Add a new route, e.g., `/players/:userId`.
*   **New Page (`PlayerDetailPage.tsx`):**
    *   Fetch detailed data for the specific user using `GET /api/users/<user_id>`.
    *   Implement the multi-pane layout (e.g., using CSS Grid):
        *   Top-wide pane: Player Details.
        *   Bottom-left pane: Deck List.
        *   Bottom-right pane: Deck Details.
    *   Display the fetched profile information (username, color, plane, avatar placeholder) in the top pane.

**Phase 6: Frontend - Player Detail Page (Deck Integration)**

*   **PlayerDetailPage.tsx:**
    *   Fetch the selected player's decks using the existing `GET /api/users/<user_id>/decks` endpoint.
    *   Display the list of decks in the bottom-left pane.
    *   When a deck is clicked:
        *   Fetch its details (using existing `GET /api/decks/<deck_id>`).
        *   Fetch its game history (using the new `GET /api/decks/<deck_id>/history`).
        *   Display the deck details and the new game history list in the bottom-right pane.

**Phase 7: Frontend - Integrate Deck History Elsewhere**

*   **DeckManagementPage.tsx:** Modify the deck detail view (modal) to also fetch and display the game history list from `GET /api/decks/<deck_id>/history`.
*   **DeckDetailPage.tsx:** Enhance this standalone page to also fetch and display the game history list.

**Phase 8: Frontend - Player Name Links**

*   **Modify Components:** Update components where player names appear (e.g., `GamesPage` registration list, match details) to wrap the username in `<Link to={`/players/${user_id}`}>`.

**Phase 9: Backend & Frontend - Player Stats**

*   **Backend:**
    *   Define logic for calculating "# wins" (e.g., count `MatchPlayer` where `placement == 1`).
    *   Define logic for "current form" (this needs more specific requirements - e.g., win rate in last 5 games?).
    *   Modify `GET /api/users/<user_id>` to compute and return these stats.
*   **Frontend (`PlayerDetailPage.tsx`):** Display the stats in the player details pane.

**Phase 10: Backend & Frontend - Avatar Upload**

*   **Backend:** Implement `POST /api/profile/avatar` endpoint for file upload, storage, and updating `User.avatar_url`.
*   **Frontend (`ProfilePage.tsx`):** Add file input and form handling for upload.
*   **Frontend (`PlayerDetailPage.tsx`):** Display the avatar image using the `avatar_url`.

**Diagram (High-Level Frontend Flow):**

```mermaid
graph TD
    subgraph Navigation
        Nav[DashboardLayout]
        Nav -- Link --> P_Games[GamesPage]
        Nav -- Link --> P_DecksMgmt[DeckManagementPage]
        Nav -- Link --> P_Players[PlayersPage]
        Nav -- Link --> P_Profile[ProfilePage]
    end

    subgraph Player Section
        P_Players -- Select Player --> P_PlayerDetail[PlayerDetailPage]
        P_PlayerDetail --> PD_Info[Player Info Pane (Stats, Profile)]
        P_PlayerDetail --> PD_DeckList[Deck List Pane]
        P_PlayerDetail --> PD_DeckDetail[Deck Detail Pane]
        PD_DeckList -- Select Deck --> PD_DeckDetail
        PD_DeckDetail --> DH_History1[Deck History List]
    end

    subgraph Deck Section
        P_DecksMgmt -- View Deck --> DM_DeckDetail[Deck Detail Modal/View]
        DM_DeckDetail --> DH_History2[Deck History List]
        P_DecksMgmt -- Link --> P_DeckDetailStandalone[DeckDetailPage]
        P_DeckDetailStandalone --> DH_History3[Deck History List]
    end

    subgraph Profile Section
        P_Profile --> ProfileForm[Profile Edit Form]
    end

    subgraph Linking
        P_Games -- Player Link --> P_PlayerDetail
    end

    style P_Players fill:#f9f,stroke:#333,stroke-width:2px
    style P_PlayerDetail fill:#f9f,stroke:#333,stroke-width:2px
    style P_Profile fill:#f9f,stroke:#333,stroke-width:2px
    style DH_History1 fill:#9cf,stroke:#333,stroke-width:1px
    style DH_History2 fill:#9cf,stroke:#333,stroke-width:1px
    style DH_History3 fill:#9cf,stroke:#333,stroke-width:1px