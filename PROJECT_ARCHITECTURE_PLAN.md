# Project Architecture Plan

## 1. Introduction

*   Purpose: Define the reviewed and refined architecture for the MagMon development pipeline, covering environments, containerization, testing, CI/CD, migrations, and deployment.
*   Goals: Ensure clear boundaries, effective containerization, robust testing, a reliable CI/CD flow, and secure deployment based on best practices.
*   Supersedes: This document supersedes relevant architectural sections in `DEV_PROCESS_IMPROVEMENT_PLAN.md`.

## 2. Environment Strategy

*   **Overview:** Three distinct environments managed via Docker Compose: Development, Testing (Integration), and Production.
*   **Development (`docker-compose.yml`):**
    *   Focus: Local development ease, hot-reloading.
    *   Services: `db`, `backend`, `frontend`.
    *   Configuration: Uses `.env` file, `FLASK_DEBUG=1`, source code volume mounts, automatic DB migration on backend start (`flask db upgrade`).
    *   Network: `magmon_network`.
*   **Testing (`docker-compose.test.yml` override):**
    *   Focus: Running backend integration tests in CI and locally.
    *   Services: Overrides `db` and `backend` from `docker-compose.yml`.
    *   Configuration: Uses separate `magmon_test` database, `FLASK_DEBUG=0`. Relies on `docker-compose run` for test execution.
    *   Migration Strategy: Confirm reliance on the default backend command (`flask db upgrade` run via `docker-compose up -d backend` in CI) for schema setup before tests. Alternatively, recommend explicit migration step or test fixture management.
*   **Production (`docker-compose.prod.yml`):**
    *   Focus: Running pre-built, optimized images.
    *   Services: `db`, `backend`, `frontend`.
    *   Configuration: Uses production images tagged with immutable identifiers (e.g., Git SHA), no source code mounts, `FLASK_DEBUG=0`, separate `postgres_data_prod` volume.
    *   Network: `magmon_network`.
*   **Configuration & Secret Management:**
    *   **Development:** `.env` file (in `.gitignore`) is acceptable.
    *   **Testing (CI):** Use GitHub Actions secrets injected as environment variables during `docker-compose up` or via temporary `.env` files created in the workflow.
    *   **Production:** **Strictly forbid** committing secrets or including them in images. Use environment variables injected by the deployment mechanism (e.g., SSH environment, systemd unit, orchestrator secrets) or Docker secrets.

## 3. Containerization

*   **Backend (`backend/Dockerfile`):**
    *   Base: `python:3.11-slim`.
    *   Structure: Single-stage, optimized layer caching.
    *   Runtime: Gunicorn (`CMD ["gunicorn", ...]`). Consider tuning worker count/type for production via environment variables if needed.
    *   `.dockerignore`: Critical for minimizing image size and excluding unnecessary files (tests, `.git`, `.env`, etc.). Must be maintained.
*   **Frontend (`frontend/Dockerfile`):**
    *   Base: `node:20-alpine` (builder), `nginx:stable-alpine` (runner).
    *   Structure: Multi-stage build. Stage 1 builds static assets (`npm run build`). Stage 2 serves assets via Nginx.
    *   `nginx.conf`: Critical for SPA routing (redirect to `index.html`) and API proxying (`/api` to `http://backend:5004`). Must be maintained.
    *   `.dockerignore`: Critical for minimizing build context in Stage 1. Must be maintained.
*   **Database (`db` service):**
    *   Base: `postgres:15`. Standard image. Data persistence via named volumes (`postgres_data`, `postgres_data_prod`).

## 4. Testing Integration

*   **Backend Unit Tests (`backend/tests/`, `not integration`):** Run via `pytest` directly (in CI) or `docker-compose exec backend pytest ...` (local). Mock dependencies.
*   **Frontend Unit/Component Tests (`frontend/src/**/__tests__/`):** Run via `npm test -- --run` (Vitest/RTL). Mock API calls.
*   **Backend Integration Tests (`backend/tests/integration/`, `integration`):**
    *   Run via `docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm backend pytest ...` against running `db` and `backend` services using the test database.
    *   Requires reliable service startup in CI (see CI/CD section).
*   **E2E Tests (Optional):** If implemented (e.g., Playwright/Cypress), run against a full `docker-compose` stack (`db`, `backend`, `frontend`) using the test database configuration.

## 5. CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

*   **Triggers:** Push/PR to `main`/`develop`, `workflow_dispatch`.
*   **Jobs:**
    *   `lint-and-format`: Checks backend (flake8, black) and frontend (eslint).
    *   `backend-unit-tests`: Runs `pytest -m "not integration"`.
    *   `frontend-unit-tests`: Runs `npm test -- --run`.
    *   `backend-integration-tests`:
        *   **Setup:** Needs secure handling of environment variables/secrets for `docker-compose`.
        *   **Service Startup:** `docker-compose ... up -d db backend`.
        *   **Health Checks:** **Replace `sleep`** with robust checks (e.g., `docker inspect` health status, `pg_isready`, backend health endpoint check script).
        *   **Execution:** `docker-compose ... run --rm backend pytest -m "integration"`.
        *   **Teardown:** `docker-compose ... down`.
    *   `(Optional) frontend-e2e-tests`: Similar setup but includes `frontend` service.
    *   `build-images`:
        *   Builds production backend and frontend images using `docker/build-push-action`.
        *   **Tagging:** Tags images with Git SHA (`${{ github.sha }}`).
        *   **Pushing:** (Currently disabled) Add steps to log in to a container registry (using secrets) and push the tagged images. This should likely only run on merges/pushes to specific branches (e.g., `main`).
*   **Deployment (Manual Trigger Job - `deploy`):**
    *   Trigger: `workflow_dispatch`.
    *   Environment: Consider using GitHub Environments for protection rules.
    *   Steps:
        1.  **Connect:** Establish connection to the deployment target (e.g., SSH using secrets).
        2.  **Set Environment:** Ensure necessary production environment variables (DB credentials, `SECRET_KEY`, etc.) are available to Docker Compose on the target machine (method depends on hosting).
        3.  **Pull Images:** `docker pull <registry>/magmon-backend:${{ github.sha }}` and `docker pull <registry>/magmon-frontend:${{ github.sha }}` (or relevant tag).
        4.  **Run Migrations:** `docker-compose -f docker-compose.prod.yml run --rm backend flask db upgrade`.
        5.  **Update Services:** `docker-compose -f docker-compose.prod.yml up -d --force-recreate backend frontend` (or specific services being updated).
        6.  **(Optional) Prune old images/containers.**

## 6. Database Migrations (Alembic / `flask db`)

*   **Development:** Automatic execution via `command` in `docker-compose.yml` is acceptable. Developers can also run `docker-compose exec backend flask db migrate/upgrade` manually.
*   **Testing (CI):** Currently handled by the automatic run in the backend container started by `docker-compose up -d`. Confirm this is the desired approach. Ensure tests handle schema state appropriately (e.g., transaction rollback, specific setup/teardown).
*   **Production:** **Manual, explicit step** during deployment, executed *before* restarting the application containers using the new code. Use `docker-compose -f docker-compose.prod.yml run --rm backend flask db upgrade`.

## 7. Deployment Strategy

*   **Method:** Manual trigger via GitHub Actions `workflow_dispatch`.
*   **Process:** As outlined in the CI/CD section (Connect -> Set Env -> Pull -> Migrate -> Update).
*   **Target:** Assumed to be a single server/VM running Docker Compose. Adaptations needed for other targets (e.g., Kubernetes, cloud container services).
*   **Rollback:** Basic rollback involves re-triggering deployment with a previous Git SHA tag. More sophisticated strategies (blue/green) are out of scope for now.

## 8. Future Considerations

*   E2E Test Implementation.
*   Container Registry Setup (e.g., Docker Hub, GHCR, AWS ECR).
*   More sophisticated deployment strategies (automated triggers, blue/green).
*   Centralized logging/monitoring.
*   Security scanning of Docker images.
*   Optimizing Gunicorn settings.

## 9. Implementation Plan

This section outlines the steps required to transition from the current state (as described in `PROGRESS_UPDATE_2025-05-02.md`) to the refined architecture defined in this document. These steps are designed to be actionable and can be broken down into subtasks for execution.

**Phase 1: CI/CD Refinements**

*   **Subtask 1.1: Implement CI Health Checks:**
    *   Action: Modify `.github/workflows/ci-cd.yml`. Replace `sleep` commands in the `backend-integration-tests` job with robust health checks for the `db` and `backend` services.
    *   Reference: Section 5 (CI/CD Pipeline - Health Checks).
*   **Subtask 1.2: Secure CI Environment Variables:**
    *   Action: Define required secrets in GitHub Actions secrets. Update `.github/workflows/ci-cd.yml` to securely inject these secrets as environment variables into the `docker-compose` environment for the `backend-integration-tests` job.
    *   Reference: Section 2 (Environment Strategy - Testing (CI)), Section 5 (CI/CD Pipeline - Setup).
*   **Subtask 1.3: Configure Image Tagging & Pushing:**
    *   Action: Update the `build-images` job in `.github/workflows/ci-cd.yml`. Define a container registry target. Add steps to log in using secrets. Enable pushing and ensure images are tagged with Git SHA. Configure to run on specific branches (e.g., `main`).
    *   Reference: Section 5 (CI/CD Pipeline - build-images), Section 3 (Containerization - Image Tagging).

**Phase 2: Production Configuration Hardening**

*   **Subtask 2.1: Secure Production Secret Management:**
    *   Action: Remove `env_file` loading for secrets from `docker-compose.prod.yml`. Define and document the strategy for injecting secrets in the target production environment (e.g., via deployment system environment variables, Docker secrets).
    *   Reference: Section 2 (Environment Strategy - Production), Section 2 (Configuration & Secret Management - Production).
*   **Subtask 2.2: Update Production Compose for Tagged Images:**
    *   Action: Modify deployment scripts/process (in `ci-cd.yml` `deploy` job) to substitute placeholder image names in `docker-compose.prod.yml` with correctly tagged images (using Git SHA) during deployment.
    *   Reference: Section 2 (Environment Strategy - Production), Section 5 (CI/CD Pipeline - Deployment).

**Phase 3: Migration Strategy Confirmation & Documentation**

*   **Subtask 3.1: Confirm Test Migration Strategy:**
    *   Action: Decide and document whether the current implicit migration run for integration tests is acceptable OR if explicit pre-test migration steps/fixture management is preferred. Update Section 6 accordingly.
    *   Reference: Section 6 (Database Migrations - Testing (CI)).
*   **Subtask 3.2: Document Production Migration Step:**
    *   Action: Ensure the deployment steps in `.github/workflows/ci-cd.yml` explicitly include the `flask db upgrade` command *before* the service update step.
    *   Reference: Section 6 (Database Migrations - Production), Section 5 (CI/CD Pipeline - Deployment).

**Phase 4: Verification & Finalization**

*   **Subtask 4.1: Full Test Suite Verification:**
    *   Action: After implementing CI refinements (Phase 1), trigger the CI pipeline and ensure all jobs pass. Run tests locally as a final check.
    *   Reference: `PROGRESS_UPDATE_2025-05-02.md`, `TESTING_VERIFICATION_PLAN.md`.
*   **Subtask 4.2: Documentation Review & Cleanup:**
    *   Action: Review all related documentation for consistency. Archive or update superseded sections in older documents.