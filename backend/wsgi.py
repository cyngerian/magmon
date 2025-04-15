import os
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file, searching from the directory of this file upwards
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    print(f"Loading environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print("Warning: .env file not found.")

from app import create_app, db
# Import models here if needed for migrations later, e.g.:
# from app.models import User, Deck, Match, MatchPlayer

# Determine the configuration name (e.g., 'development', 'production')
config_name = os.getenv('FLASK_CONFIG', 'default')
app = create_app(config_name)

# Optional: Set up Flask-Migrate commands
# You might run these from the command line using 'flask db init', 'flask db migrate', 'flask db upgrade'
# Ensure FLASK_APP=wsgi.py is set in your environment for the flask command to work.

if __name__ == "__main__":
    # Note: Use 'flask run' command for development instead of app.run() directly
    # Set FLASK_APP=wsgi.py and FLASK_DEBUG=1 in your environment
    # Example: export FLASK_APP=wsgi.py; export FLASK_DEBUG=1; flask run
    # The 'flask run' command uses a better development server than app.run()
    print("To run the development server:")
    print("1. Activate the virtual environment: source venv/bin/activate")
    print("2. Set environment variables: export FLASK_APP=wsgi.py; export FLASK_DEBUG=1")
    print("3. Run the server: flask run")
    # app.run() # Avoid using this directly for development
