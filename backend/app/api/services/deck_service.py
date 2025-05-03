"""
Service layer for deck management operations.
"""
from typing import List, Optional, Tuple, Dict
from datetime import datetime
from flask import current_app
from sqlalchemy.orm import joinedload

from backend.app import db
from backend.app.models import Deck, DeckVersion, Game, GameRegistration, Match, MatchPlayer
from ..schemas.deck_schemas import (
    DeckCreate, DeckUpdate, DeckVersionCreate,
    DeckResponse, DeckListResponse, DeckVersionResponse,
    DeckHistoryEntry, DeckVersionListResponse
)

class DeckService:
    @staticmethod
    def create_deck(user_id: int, data: DeckCreate) -> Tuple[DeckResponse, int]:
        """Create a new deck with initial version."""
        try:
            new_deck = Deck(
                name=data.name,
                commander=data.commander,
                colors=data.colors,
                decklist_text=data.decklist_text or '',
                user_id=user_id
            )
            db.session.add(new_deck)
            db.session.flush()  # Get the deck ID
            
            # Create the initial version
            initial_version = DeckVersion(
                deck_id=new_deck.id,
                version_number=1,
                decklist_text=data.decklist_text or '',
                notes="Initial version"
            )
            db.session.add(initial_version)
            db.session.flush()  # Get the version ID
            
            # Set the current version
            new_deck.current_version_id = initial_version.id
            db.session.add(new_deck)
            db.session.commit()
            
            response = DeckResponse(
                id=new_deck.id,
                name=new_deck.name,
                commander=new_deck.commander,
                colors=new_deck.colors,
                decklist_text=new_deck.decklist_text,
                user_id=new_deck.user_id,
                created_at=new_deck.created_at.isoformat(),
                last_updated=new_deck.last_updated.isoformat(),
                current_version_id=new_deck.current_version_id
            )
            return response, 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating deck: {e}")
            raise

    @staticmethod
    def get_user_decks(user_id: int) -> List[DeckListResponse]:
        """Get all decks belonging to a user."""
        decks = Deck.query.filter_by(user_id=user_id).order_by(Deck.last_updated.desc()).all()
        return [
            DeckListResponse(
                id=deck.id,
                name=deck.name,
                commander=deck.commander,
                colors=deck.colors,
                last_updated=deck.last_updated.isoformat()
            ) for deck in decks
        ]

    @staticmethod
    def get_deck_details(deck_id: int) -> Tuple[DeckResponse, int]:
        """Get full details for a specific deck."""
        deck = Deck.query.get_or_404(deck_id)
        
        # Get the current version if it exists
        current_version = None
        if deck.current_version_id:
            current_version = DeckVersion.query.get(deck.current_version_id)
        
        # Use the decklist from the current version if available
        decklist_text = current_version.decklist_text if current_version else deck.decklist_text
        
        response = DeckResponse(
            id=deck.id,
            name=deck.name,
            commander=deck.commander,
            colors=deck.colors,
            decklist_text=decklist_text,
            user_id=deck.user_id,
            created_at=deck.created_at.isoformat(),
            last_updated=deck.last_updated.isoformat(),
            current_version_id=deck.current_version_id
        )
        return response, 200

    @staticmethod
    def create_deck_version(deck_id: int, user_id: int, data: DeckVersionCreate) -> Tuple[DeckVersionResponse, int]:
        """Create a new version of a deck."""
        deck = Deck.query.get_or_404(deck_id)
        
        # Check ownership
        if deck.user_id != user_id:
            raise PermissionError("You don't own this deck")
        
        # Get the latest version number
        latest_version = DeckVersion.query.filter_by(deck_id=deck_id).order_by(DeckVersion.version_number.desc()).first()
        new_version_number = 1 if not latest_version else latest_version.version_number + 1
        
        try:
            # Create the new version
            new_version = DeckVersion(
                deck_id=deck_id,
                version_number=new_version_number,
                decklist_text=data.decklist_text,
                notes=data.notes or ''
            )
            db.session.add(new_version)
            db.session.flush()  # Get the version ID
            
            # Update the current version
            deck.current_version_id = new_version.id
            db.session.add(deck)
            db.session.commit()
            
            response = DeckVersionResponse(
                id=new_version.id,
                version_number=new_version.version_number,
                created_at=new_version.created_at.isoformat(),
                notes=new_version.notes,
                decklist_text=new_version.decklist_text,
                is_current=True
            )
            return response, 201
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating deck version: {e}")
            raise

    @staticmethod
    def get_deck_versions(deck_id: int) -> List[DeckVersionListResponse]:
        """Get all versions of a specific deck."""
        deck = Deck.query.get_or_404(deck_id)
        versions = DeckVersion.query.filter_by(deck_id=deck_id).order_by(DeckVersion.version_number.desc()).all()
        
        return [
            DeckVersionListResponse(
                id=version.id,
                version_number=version.version_number,
                created_at=version.created_at.isoformat(),
                notes=version.notes,
                is_current=version.id == deck.current_version_id
            ) for version in versions
        ]

    @staticmethod
    def get_deck_version(deck_id: int, version_id: int) -> Tuple[DeckVersionResponse, int]:
        """Get a specific version of a deck."""
        version = DeckVersion.query.filter_by(deck_id=deck_id, id=version_id).first_or_404()
        
        response = DeckVersionResponse(
            id=version.id,
            version_number=version.version_number,
            created_at=version.created_at.isoformat(),
            notes=version.notes,
            decklist_text=version.decklist_text,
            is_current=version.id == version.deck.current_version_id
        )
        return response, 200

    @staticmethod
    def get_deck_history(deck_id: int) -> List[DeckHistoryEntry]:
        """Get the game history for a specific deck."""
        deck = Deck.query.options(joinedload(Deck.owner)).get_or_404(deck_id)
        owner_id = deck.user_id

        try:
            results = db.session.query(
                Game.id.label('game_id'),
                Game.game_date,
                DeckVersion.version_number,
                MatchPlayer.placement
            ).select_from(Game).join(
                GameRegistration, Game.id == GameRegistration.game_id
            ).outerjoin(
                DeckVersion, GameRegistration.deck_version_id == DeckVersion.id
            ).outerjoin(
                Match, Match.game_id == Game.id
            ).outerjoin(
                MatchPlayer,
                (MatchPlayer.match_id == Match.id) & (MatchPlayer.user_id == owner_id)
            ).filter(
                GameRegistration.deck_id == deck_id
            ).order_by(
                Game.game_date.desc()
            ).all()

            return [
                DeckHistoryEntry(
                    game_id=r.game_id,
                    game_date=r.game_date.isoformat(),
                    placement=r.placement,
                    version_number=r.version_number
                ) for r in results
            ]
        except Exception as e:
            current_app.logger.error(f"Error fetching deck history for deck {deck_id}: {e}")
            raise