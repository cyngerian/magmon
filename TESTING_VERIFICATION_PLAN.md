# Testing Verification Plan

This document outlines the existing test suites in the MagMon project as of May 1st, 2025, and provides instructions on how to run them locally to verify system functionality before starting new feature development or merging changes.

## Testing Overview

The project utilizes several types of automated tests:

*   **Backend Unit Tests:**
    *   **Location:** `backend/tests/` (e.g., `test_deck_model.py`, `test_deck_service.py`, etc., excluding `integration/`)
    *   **Purpose:** Verify individual backend code units (functions, classes) in isolation, mocking dependencies like the database.
*   **Backend Integration Tests:**
    *   **Location:** `backend/tests/integration/` (currently `test_user_auth_flow.py`, `test_deck_flow.py`)
    *   **Purpose:** Verify the interaction between backend components, specifically API endpoints (User Auth, Deck Management) and service logic interacting with a real test database via Docker Compose. Marked with `@pytest.mark.integration`.
*   **Frontend Unit/Component Tests:**
    *   **Location:** `frontend/src/**/__tests__/` (currently `ChangePasswordModal.test.tsx`, `DeckManagementPage.test.tsx`)
    *   **Purpose:** Verify individual React components (Change Password Modal, Deck Management Page) and potentially hooks/utils in isolation, mocking API calls. Uses Vitest and React Testing Library.

## Running Tests Locally

Use the following commands from the project root directory:

*   **Backend Unit Tests:**
    ```bash
    # Ensure Docker Compose services (at least backend) are running if needed for context
    docker-compose exec backend pytest backend/tests -m "not integration"
    ```
*   **Backend Integration Tests:**
    ```bash
    # Start required services (database and backend) in detached mode
    docker-compose -f docker-compose.yml -f docker-compose.test.yml up -d db backend && \
    # Wait a few seconds for services to initialize (adjust time if needed)
    echo "Waiting for services to start..." && sleep 10 && \
    # Run tests in a temporary container against the running services
    echo "Running integration tests..." && \
    docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm backend pytest backend/tests/integration -m "integration" && \
    # Stop and remove containers after tests complete
    echo "Stopping services..." && \
    docker-compose -f docker-compose.yml -f docker-compose.test.yml down
    ```
    *Note: Requires Docker and Docker Compose. This multi-step process is necessary because the integration tests require the `db` and `backend` services to be running before the tests are executed. The `up -d` command starts these services, the `sleep` provides a brief pause for initialization, the `run` command executes the tests against the running services, and the `down` command cleans up the services afterwards.*
*   **Frontend Unit/Component Tests:**
    ```bash
    cd frontend && npm test -- --run
    ```
    *Note: Navigates into the frontend directory first.*

## System Verification Workflow

Before starting significant new feature work or merging branches, run tests locally in this sequence:

1.  **Run Backend Unit Tests:** Quick check for isolated backend logic issues.
2.  **Run Frontend Unit/Component Tests:** Quick check for isolated frontend component issues.
3.  **Run Backend Integration Tests:** Verify core API flows and database interactions.

**Rationale:** This order runs faster, isolated tests first. Passing all three provides good confidence in the current system state.

## CI Pipeline Reminder

The CI pipeline (`.github/workflows/ci-cd.yml`) automates running these tests on pushes/pull requests to main branches.