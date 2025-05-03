# Development Process Improvement Plan

## 1. Introduction

This document outlines the plan to enhance the development process for the MagMon project by implementing full containerization, a comprehensive testing strategy, and a CI/CD pipeline. The goal is to create more consistent development and production environments, improve code quality through automated testing, and streamline the build and deployment process.

## 2. Full Containerization

**Goal:** Achieve consistent, reproducible environments for development and production, simplifying setup and deployment.

**Services:**
*   **`db`:** PostgreSQL database (already defined).
*   **`backend`:** Flask/Python application (already defined).
*   **`frontend`:** React/Vite application (already defined).
*   **(Future Consideration):** Services like Redis could be added later if caching or background task requirements arise.

**`docker-compose.yml` Refinements:**
*   **Separate Files:** Create `docker-compose.yml` (for development) and `docker-compose.prod.yml` (for production builds/testing).
*   **Development (`docker-compose.yml`):**
    *   **Backend Volume:** Ensure the backend code volume mount is active for hot-reloading: `volumes: - ./backend:/app/backend`.
    *   **Frontend Volume:** Confirm existing frontend volume mount: `volumes: - ./frontend:/app - /app/node_modules`.
    *   **Environment:** Use development-specific environment variables (e.g., `FLASK_DEBUG=1` for backend, `NODE_ENV=development` for frontend).
    *   **Database:** Use the existing `db` service definition.
*   **Production (`docker-compose.prod.yml`):**
    *   Define services using pre-built production images (see Dockerfile refinements below).
    *   Do *not* mount source code volumes for backend/frontend.
    *   Use production environment variables (`FLASK_DEBUG=0`, `NODE_ENV=production`).
    *   Include database service definition, potentially using a different volume for production data if needed, or relying on external managed databases per the deployment plan.

**`backend/Dockerfile` Refinements:**
*   **Development:** The current Dockerfile can serve as a base. Development-specific settings (like `FLASK_DEBUG=1`) should be controlled via `docker-compose.yml` environment variables rather than hardcoded in the Dockerfile. Ensure any dev-specific Python dependencies are included in `requirements.txt` (or a separate `requirements-dev.txt`).
*   **Production:**
    *   The current Dockerfile is a good starting point.
    *   Ensure `FLASK_DEBUG=0`.
    *   Review Gunicorn configuration (`CMD` line) for optimal worker count/type based on expected production load and server resources.
    *   Consider a multi-stage build if there are build-specific dependencies that aren't needed at runtime, although for Python this is often less critical than for compiled languages or Node.js frontend builds.
    *   Ensure `.dockerignore` is comprehensive to minimize build context and image size.

**`frontend/Dockerfile` Refinements:**
*   **Development:** The current Dockerfile (`CMD ["npm", "run", "dev", "--", "--host"]`) is suitable for development with hot-reloading via the volume mount in `docker-compose.yml`.
*   **Production:**
    *   Implement a **multi-stage build**:
        *   **Stage 1 (Builder):** Use a `node:20` image, copy `package.json`, `package-lock.json`, install dependencies (`npm ci --only=production` recommended), copy source code, and run the production build (`npm run build`).
        *   **Stage 2 (Runner):** Use a lightweight web server image (e.g., `nginx:stable-alpine`). Copy the built static assets (typically from a `/dist` folder) from the *Builder* stage into the Nginx HTML directory (`/usr/share/nginx/html`).
        *   **Nginx Configuration:** Add a custom `nginx.conf` to serve the React application correctly (handle routing by redirecting non-file requests to `index.html`) and proxy API requests starting with `/api` to the backend service (e.g., `proxy_pass http://backend:5004;`).

**Database Migrations (Alembic):**
*   **Strategy:** Use `flask db upgrade` (which utilizes Alembic).
*   **Execution Options:**
    1.  **(Recommended for Dev Simplicity):** Modify the `backend` service's `command` in `docker-compose.yml` to run migrations before starting the server: `command: bash -c "flask db upgrade && gunicorn --bind 0.0.0.0:5004 --timeout 120 wsgi:app"`
    2.  **Manual Execution:** Document the command `docker-compose exec backend flask db upgrade` for developers/CI.
    3.  **Separate Migration Service:** Define a short-lived service in `docker-compose.yml` that depends on `db` and runs only the `flask db upgrade` command. This is cleaner but adds complexity.
*   **Production:** Migrations should be run as a distinct step during the deployment process, *before* the new application code is started.

## 3. Comprehensive Testing Strategy

**Goal:** Ensure code correctness, prevent regressions, and increase confidence in deployments.

**Backend (Python/Flask):**
*   **Integration Tests:**
    *   **Tool:** `pytest`.
    *   **Setup:**
        *   Define a separate test database configuration (e.g., using environment variables overridden in a `docker-compose.test.yml` or similar).
        *   Use `pytest` fixtures to manage database connections and transaction rollbacks (or database setup/teardown) for test isolation. A common pattern is to create a fresh test database for each test run or module.
    *   **Scope:**
        *   API Endpoints: Test CRUD operations, authentication/authorization, specific game logic endpoints. Simulate requests and assert responses/database state changes.
        *   Service Logic: Test functions/methods involving multiple database models, complex queries, or transactions.
    *   **Execution:** Integrate into the CI pipeline. Run using a command like `docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm backend pytest tests/`.
*   **Unit Tests:**
    *   Continue using `pytest` for existing unit tests.
    *   Focus on testing individual functions, classes, and modules in isolation, mocking external dependencies (like database or external APIs).
    *   Maintain high coverage for critical logic (e.g., utility functions, complex algorithms).

**Frontend (React/Vite):**
*   **Unit/Component Tests:**
    *   **Tools:** Vitest (already configured via `vitest.config.ts`), React Testing Library (RTL) (needs setup if not already present - check `setupTests.ts`).
    *   **Scope:**
        *   Components: Test rendering, user interactions (clicks, form input), conditional rendering based on props/state for key components (e.g., `ChangePasswordModal`, `DeckManagementPage` components, forms).
        *   Custom Hooks: Test logic within custom hooks.
        *   Utility Functions: Test data transformations, API client helpers (`apiClient.ts`).
        *   State Management: If using Zustand, Redux, etc., test reducers/actions/selectors.
    *   **Goals:** Aim for a meaningful coverage target (e.g., 75%+) for new and refactored code. Focus on testing behavior rather than implementation details.
    *   **Execution:** Run via `npm test` (or `vitest run`). Integrate into the CI pipeline.
*   **End-to-End (E2E) Tests (Optional but Recommended):**
    *   **Tools:** Consider Playwright or Cypress.
    *   **Strategy:**
        *   Define 3-5 critical user flows (e.g., User Login -> View Profile -> Edit Profile; Create Deck -> Add Cards -> View Deck; View Games -> Join Game).
        *   Run these tests against a fully containerized environment (backend, frontend, db) spun up by `docker-compose`.
        *   Focus on verifying the integration between frontend and backend from a user's perspective.
    *   **Consideration:** E2E tests provide the highest level of confidence but are slower and can be more brittle. Start small and expand as needed. Integrate into a later stage of the CI pipeline.

## 4. CI/CD Pipeline (GitHub Actions)

**Goal:** Automate the process of testing, building artifacts, and preparing for deployment upon code changes.

**Platform:** GitHub Actions.

**Workflow File:** `.github/workflows/ci-cd.yml`

**Triggers:**
*   `on: push: branches: [ main, develop ]` # Or relevant branches
*   `on: pull_request: branches: [ main, develop ]`

**Stages/Jobs:**
1.  **Lint & Format Check:**
    *   Run backend linters (e.g., `flake8`, `black --check`).
    *   Run frontend linters (e.g., `npm run lint` using ESLint).
2.  **Backend Unit Tests:**
    *   Set up Python environment.
    *   Install dependencies (`pip install -r backend/requirements.txt`).
    *   Run unit tests (`pytest backend/tests/ -m "not integration"` - assuming marking integration tests).
3.  **Frontend Unit/Component Tests:**
    *   Set up Node.js environment.
    *   Install dependencies (`npm ci` in `frontend` directory).
    *   Run tests (`npm test -- --run` in `frontend` directory).
4.  **Setup Test Environment (Docker):**
    *   Use `docker-compose` (potentially with overrides for CI, e.g., `docker-compose -f docker-compose.yml -f docker-compose.ci.yml up -d db backend`).
    *   Wait for services (especially DB) to be healthy.
5.  **Backend Integration Tests:**
    *   Execute integration tests against the running services: `docker-compose exec backend pytest tests/ -m "integration"`.
6.  **(Optional) Frontend E2E Tests:**
    *   Requires a running frontend service as well.
    *   Execute E2E tests (e.g., `docker-compose exec frontend npx playwright test`).
7.  **Build Docker Images:**
    *   Build production-ready backend image (`docker build -t <registry>/magmon-backend:${{ github.sha }} -f backend/Dockerfile . --target production` if using multi-stage, otherwise standard build).
    *   Build production-ready frontend image (`docker build -t <registry>/magmon-frontend:${{ github.sha }} -f frontend/Dockerfile . --target production` - requires multi-stage setup).
8.  **Push Docker Images:**
    *   Log in to container registry (Docker Hub, GHCR, etc.) using secrets.
    *   Push the tagged images.
9.  **Deployment (Manual Trigger):**
    *   Define a separate workflow or a job within the same workflow triggered by `workflow_dispatch`.
    *   This job would typically:
        *   Connect to the deployment environment (e.g., SSH into a server, use cloud provider CLI).
        *   Pull the specific Docker image versions built in the CI pipeline.
        *   Run database migrations (`docker-compose -f docker-compose.prod.yml run --rm backend flask db upgrade`).
        *   Stop the old containers and start the new ones (`docker-compose -f docker-compose.prod.yml up -d --force-recreate`).
    *   Refer to `docs_archive/DEPLOYMENT_PLAN.md` for specific deployment environment details.

**Secrets Management:**
*   Use GitHub Actions Encrypted Secrets to store sensitive information:
    *   `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` (or equivalent for other registries)
    *   `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (for CI test database if needed, and potentially for deployment connection)
    *   `SECRET_KEY` (Flask secret key for backend)
    *   Any other API keys or sensitive credentials needed during build or deployment.

## 5. Next Steps

1.  Review this plan for completeness and accuracy.
2.  Approve the plan or suggest modifications.
3.  Once approved, proceed with the implementation tasks, potentially breaking them down into smaller, manageable units.