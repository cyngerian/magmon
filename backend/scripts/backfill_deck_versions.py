import os
import sys
from datetime import datetime

# Add the project root to the Python path to allow importing 'app'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from app import create_app, db  # Import create_app and db from the Flask app factory
from app.models import Deck, DeckVersion, GameRegistration, MatchPlayer

def backfill_initial_versions():
    """
    Creates initial DeckVersion records for existing decks that don't have one
    and updates related GameRegistration and MatchPlayer records.
    """
    flask_app = create_app()  # Create a Flask app instance to work within its context
    with flask_app.app_context():
        session = Session(db.engine)  # Create a session using the app's engine
        print("Starting backfill process for initial deck versions...")

        try:
            # Get all existing decks
            decks = session.query(Deck).all()
            print(f"Found {len(decks)} decks to process.")

            updated_decks = 0
            updated_registrations = 0
            updated_match_players = 0

            for i, deck in enumerate(decks):
                print(f"Processing deck {i+1}/{len(decks)}: ID={deck.id}, Name='{deck.name}'")

                # Check if an initial version already exists (e.g., if script is re-run)
                existing_initial_version = session.query(DeckVersion).filter_by(deck_id=deck.id, version_number=1).first()

                if existing_initial_version:
                    print(f"  - Initial version (ID={existing_initial_version.id}) already exists. Skipping version creation.")
                    initial_version = existing_initial_version
                elif deck.decklist_text: # Only create if there's a decklist to version
                     print(f"  - Creating initial version...")
                     initial_version = DeckVersion(
                         deck_id=deck.id,
                         version_number=1,
                         decklist_text=deck.decklist_text,
                         notes="Initial version created during backfill script",
                         created_at=datetime.utcnow()
                     )
                     session.add(initial_version)
                     session.flush()  # Get the version ID before assigning it
                     print(f"  - Created initial version ID={initial_version.id}")
                else:
                    print(f"  - Deck has no decklist_text. Skipping initial version creation.")
                    initial_version = None # Cannot proceed without a version

                # Update the deck's current_version_id if it's not set and we created/found an initial version
                if initial_version and deck.current_version_id is None:
                    deck.current_version_id = initial_version.id
                    session.add(deck)
                    updated_decks += 1
                    print(f"  - Set deck's current_version_id to {initial_version.id}")

                # Update related records if we have an initial version
                if initial_version:
                    # Update game registrations that don't have a version set
                    registrations_to_update = session.query(GameRegistration).filter_by(deck_id=deck.id, deck_version_id=None).all()
                    if registrations_to_update:
                        print(f"  - Updating {len(registrations_to_update)} game registrations...")
                        for reg in registrations_to_update:
                            reg.deck_version_id = initial_version.id
                            session.add(reg)
                            updated_registrations += 1

                    # Update match players that don't have a version set
                    match_players_to_update = session.query(MatchPlayer).filter_by(deck_id=deck.id, deck_version_id=None).all()
                    if match_players_to_update:
                        print(f"  - Updating {len(match_players_to_update)} match player records...")
                        for mp in match_players_to_update:
                            mp.deck_version_id = initial_version.id
                            session.add(mp)
                            updated_match_players += 1

            # Commit all changes made in the loop
            print("\nCommitting changes to the database...")
            session.commit()
            print("Changes committed.")
            print("\nBackfill Summary:")
            print(f"- Decks updated (current_version_id set): {updated_decks}")
            print(f"- Game Registrations updated: {updated_registrations}")
            print(f"- Match Players updated: {updated_match_players}")

        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Rolling back changes...")
            session.rollback()
        finally:
            print("Closing database session.")
            session.close()
            print("Backfill process finished.")

if __name__ == "__main__":
    backfill_initial_versions()