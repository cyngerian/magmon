#!/bin/bash
echo "--- Activating Virtual Environment ---"
SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/venv/bin/activate"

echo "--- Installing Python Packages ---"
pip install Flask SQLAlchemy psycopg2-binary python-dotenv Flask-SQLAlchemy Flask-Migrate Flask-Bcrypt Flask-Cors

echo "--- Freezing Requirements ---"
pip freeze > requirements.txt

echo "--- Deactivating Virtual Environment ---"
deactivate

echo "--- Setup Script Finished ---"
