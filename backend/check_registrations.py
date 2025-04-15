import sys
import os
from datetime import date

# Add the parent directory (backend) to the path to find the 'app' module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from app import db, create_app
    from app.models import GameNight, GameNightRegistration, User, Deck

    print("Creating app context...")
    app = create_app()
    app.app_context().push()
    print("App context pushed.")

    target_date_str = "2025-03-31"
    target_date = date.fromisoformat(target_date_str)
    print(f"Looking for Game Night on {target_date_str}...")

    game_night = GameNight.query.filter_by(game_date=target_date).first()

    if game_night:
        print(f"Found Game Night ID: {game_night.id} (Status: {game_night.status.value})")
        print(f"Querying registrations for Game Night ID: {game_night.id}...")

        # Query registrations joining User and Deck tables
        registrations = db.session.query(GameNightRegistration, User, Deck)\
            .join(User, GameNightRegistration.user_id == User.id)\
            .join(Deck, GameNightRegistration.deck_id == Deck.id)\
            .filter(GameNightRegistration.game_night_id == game_night.id)\
            .all()

        if registrations:
            print("\n--- Registrations Found ---")
            for reg, user, deck in registrations:
                print(f"- User: {user.username} (ID: {user.id}), Deck: {deck.name} (ID: {deck.id}), Commander: {deck.commander}")
            print("---------------------------\n")
        else:
            print("No registrations found for this game night.")

    else:
        print(f"No Game Night found for date {target_date_str}.")

except ImportError as e:
    print(f"ImportError: {e}", file=sys.stderr)
    print("Ensure this script is run from the project root or the app module is findable.", file=sys.stderr)
    exit(1)
except Exception as e:
    print(f"An error occurred: {e}", file=sys.stderr)
    exit(1)

print("Script finished.")
