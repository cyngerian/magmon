import sys
import os

# Add the parent directory (backend) to the path to find the 'app' module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from app import db, create_app
    from app.models import Match, MatchPlayer  # Import MatchPlayer

    print("Creating app context...")
    app = create_app()
    app.app_context().push()
    print("App context pushed.")

    print("Querying match players...")
    num_players_deleted = MatchPlayer.query.delete()
    print(f"Deleted {num_players_deleted} match player record(s).")

    print("Querying matches...")
    num_matches_deleted = Match.query.delete()
    print(f"Deleted {num_matches_deleted} match record(s).")

    print("Committing changes...")
    db.session.commit()
    print("Changes committed.")

except ImportError as e:
    print(f"ImportError: {e}", file=sys.stderr)
    print(
        "Ensure this script is run from the 'backend' directory or the app"
        " module is findable.",
        file=sys.stderr,
    )
    exit(1)
except Exception as e:
    print(f"An error occurred: {e}", file=sys.stderr)
    db.session.rollback()
    print("Rolled back database session.", file=sys.stderr)
    exit(1)

print("Script finished successfully.")
