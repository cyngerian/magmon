# MagMon - Technical Overview

This document provides a technical overview of the MagMon Commander Tracker application.

## Technology Stack

*   **Backend:**
    *   Language: Python 3
    *   Framework: Flask
    *   Database: PostgreSQL
    *   ORM: SQLAlchemy (with Flask-SQLAlchemy & Flask-Migrate)
    *   Password Hashing: Flask-Bcrypt
    *   CORS Handling: Flask-Cors
*   **Frontend:**
    *   Framework: React (with TypeScript)
    *   Build Tool: Vite
    *   Routing: React Router DOM v6
    *   HTTP Client: Axios
    *   CSS: Pico.css (base) + `custom.css` (overrides)
*   **Development Database:** Docker (via Docker Compose) running `postgres:15` image.

## Project Structure

```
/magmon
├── backend/
│   ├── app/                    # Flask application package
│   │   ├── __init__.py         # App factory (create_app)
│   │   ├── models.py           # SQLAlchemy DB models
│   │   └── api/                # API Blueprint
│   │       ├── __init__.py     # Blueprint definition
│   │       └── routes.py       # API endpoint definitions
│   ├── migrations/             # Flask-Migrate migration scripts
│   ├── venv/                   # Python virtual environment (ignored by git)
│   ├── .env                    # Backend environment variables (DB URL, SECRET_KEY)
│   ├── .gitignore
│   ├── config.py               # Flask configuration classes
│   ├── requirements.txt        # Python dependencies
│   └── wsgi.py                 # WSGI entry point (for Flask runner/deployment)
├── frontend/
│   ├── public/                 # Static assets
│   ├── src/
│   │   ├── assets/             # Frontend assets (images, etc.)
│   │   ├── pages/              # Page-level components (Games, Decks, Submit, etc.)
│   │   ├── App.css             # Main app styles
│   │   ├── App.tsx             # Root component with routing setup
│   │   ├── custom.css          # Custom style overrides
│   │   ├── index.css           # Base styles (Vite default, modified)
│   │   └── main.tsx            # Entry point, renders App into DOM
│   ├── .gitignore
│   ├── index.html              # Main HTML template
│   ├── package.json            # Node dependencies & scripts
│   ├── package-lock.json
│   ├── tsconfig.json           # TypeScript config
│   ├── tsconfig.node.json      # TypeScript config for Node env (Vite)
│   └── vite.config.ts          # Vite configuration
├── .env                        # Docker Compose environment variables (DB credentials)
├── docker-compose.yml          # Docker Compose definition for PostgreSQL DB
├── PLAN.md                     # Project plan and phases
└── TECHNICAL_README.md         # This file
```

## Setup & Running Locally

1.  **Prerequisites:** Docker, Docker Compose, Python 3, Node.js, npm.
2.  **Clone Repository:** `git clone ...` (Assuming version control is used)
3.  **Backend Setup:**
    *   `cd backend`
    *   `python3 -m venv venv`
    *   `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
    *   `pip install -r requirements.txt`
    *   Create `backend/.env` file with `DATABASE_URL` (e.g., `postgresql://magmon_user:magmon_password@localhost:5432/magmon_dev`) and a strong `SECRET_KEY`.
    *   `deactivate` (optional)
    *   `cd ..`
4.  **Frontend Setup:**
    *   `npm install --prefix frontend`
5.  **Database Setup:**
    *   Create root `.env` file with `POSTGRES_USER=magmon_user`, `POSTGRES_PASSWORD=magmon_password`, `POSTGRES_DB=magmon_dev`.
    *   Start DB: `docker-compose up -d`
    *   Apply Migrations: `backend/venv/bin/flask --app backend/wsgi.py db upgrade --directory backend/migrations`
6.  **Run Servers:**
    *   Backend (Terminal 1): `backend/venv/bin/flask --app backend/wsgi.py run --port 5004` (or chosen port)
    *   Frontend (Terminal 2): `npm run --prefix frontend dev`
7.  **Access:** Open browser to the URL provided by the frontend server (e.g., `http://localhost:5174`).

## Core Workflow Implemented

1.  **User Auth:** Register, Login (basic, using localStorage persistence).
2.  **Deck Management:** Create, List (own), View Details (including decklist).
3.  **Game Management:** Create (manual, optional date/pauper/details), List, Cancel.
4.  **Game Registration:** Users register one of their decks for an upcoming game.
5.  **Match Submission:** Select Game -> View Registered Players -> Assign Placements -> Add Times/Notes -> Submit (marks Game as Completed).

## Key TODOs / Next Steps (See PLAN.md)

*   Implement Match Approval workflow.
*   Implement Match History display.
*   Implement robust Authentication (e.g., JWT).
*   Refine UI/UX (mana symbols, compaction, etc.).
*   Add backend endpoint for fetching specific Game details (if needed beyond list view).
*   Add authorization checks to backend endpoints (e.g., only owner can modify/delete deck).
*   Add registration count display to Games list.
*   Consider automatic Game creation.
*   Address persistent TypeScript error in `GamesPage.tsx`.
*   Deployment Strategy (AWS).
