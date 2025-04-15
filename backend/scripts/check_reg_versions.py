import os
import sys

# Add project root to the Python path to allow importing 'app'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from app import create_app, db
from app.models import GameRegistration, DeckVersion # Import DeckVersion

TARGET_DECK_ID = 2 # Assuming 'gorges' is deck ID 2

def check_versions():
    """Queries and prints game_id and deck_version_id for a specific deck."""
    flask_app = create_app()
    with flask_app.app_context():
        session = Session(db.engine)
        print(f"Checking registrations for Deck ID: {TARGET_DECK_ID}")
        try:
            # Find the ID of version 1 for the target deck
            initial_version = session.query(DeckVersion).filter_by(deck_id=TARGET_DECK_ID, version_number=1).first()
            if not initial_version:
                print(f"Error: Could not find Version 1 for Deck ID {TARGET_DECK_ID}.")
                return

            print(f"\nFound Initial Version (Version 1) - ID: {initial_version.id}")

            registrations = session.query(GameRegistration).filter_by(deck_id=TARGET_DECK_ID).order_by(GameRegistration.game_id).all()
            if not registrations:
                print("No registrations found for this deck.")
                # Still print suggested command even if no current registrations exist, in case data is inconsistent
            else:
                print("\nCurrent Registrations:")
                print("Game ID | Deck Version ID")
                print("--------|----------------")
                for reg in registrations:
                    print(f"{reg.game_id:<7} | {reg.deck_version_id}")
                print("--------|----------------")

            # Suggest update command (don't execute automatically)
            print("\nTo fix incorrect historical versions, consider running SQL like:")
            print(f"UPDATE game_registrations SET deck_version_id = {initial_version.id} WHERE deck_id = {TARGET_DECK_ID} AND deck_version_id != {initial_version.id};")
            # Also consider match_players table if needed:
            # print(f"UPDATE match_players SET deck_version_id = {initial_version.id} WHERE deck_id = {TARGET_DECK_ID} AND deck_version_id != {initial_version.id};")

        except Exception as e:
            print(f"\nAn error occurred: {e}")
        finally:
            print("\nClosing database session.")
            session.close()

if __name__ == "__main__":
    check_versions()