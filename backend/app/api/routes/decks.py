"""
Routes for deck management, including CRUD operations, versioning, and history.
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from dataclasses import asdict

from .. import bp
from ..services.deck_service import DeckService
from ..schemas.deck_schemas import (
    DeckCreate, DeckVersionCreate, DeckResponse,
    DeckListResponse, DeckVersionResponse, DeckHistoryEntry
)

# ================== Deck Routes ==================

@bp.route('/decks', methods=['POST'])
@jwt_required()
def create_deck():
    """Create a new deck for the logged-in user."""
    current_user_id = get_jwt_identity()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        deck_data = DeckCreate(**data)
        response, status_code = DeckService.create_deck(current_user_id, deck_data)
        return jsonify({"message": "Deck created successfully", "deck": asdict(response)}), status_code
    except (ValueError, TypeError, KeyError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Deck creation failed"}), 500

@bp.route('/decks', methods=['GET'])
@jwt_required()
def get_user_decks():
    """Get all decks belonging to the logged-in user."""
    current_user_id = get_jwt_identity()
    
    try:
        decks = DeckService.get_user_decks(current_user_id)
        return jsonify([asdict(deck) for deck in decks]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch decks"}), 500

@bp.route('/decks/<int:deck_id>', methods=['GET'])
@jwt_required()
def get_deck_details(deck_id):
    """Get full details for a specific deck, including decklist."""
    try:
        response, status_code = DeckService.get_deck_details(deck_id)
        return jsonify(asdict(response)), status_code
    except Exception as e:
        return jsonify({"error": "Failed to fetch deck details"}), 500

@bp.route('/decks/<int:deck_id>/versions', methods=['GET'])
@jwt_required()
def get_deck_versions(deck_id):
    """Get all versions of a specific deck."""
    try:
        versions = DeckService.get_deck_versions(deck_id)
        return jsonify([asdict(version) for version in versions]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch deck versions"}), 500

@bp.route('/decks/<int:deck_id>/versions/<int:version_id>', methods=['GET'])
@jwt_required()
def get_deck_version(deck_id, version_id):
    """Get a specific version of a deck."""
    try:
        response, status_code = DeckService.get_deck_version(deck_id, version_id)
        return jsonify(asdict(response)), status_code
    except Exception as e:
        return jsonify({"error": "Failed to fetch deck version"}), 500

@bp.route('/decks/<int:deck_id>/versions', methods=['POST'])
@jwt_required()
def create_deck_version(deck_id):
    """Create a new version of a deck."""
    current_user_id = get_jwt_identity()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400
        
        version_data = DeckVersionCreate(**data)
        response, status_code = DeckService.create_deck_version(deck_id, current_user_id, version_data)
        return jsonify({"message": "New version created successfully", "version": asdict(response)}), status_code
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except (ValueError, TypeError, KeyError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Version creation failed"}), 500

@bp.route('/decks/<int:deck_id>/history', methods=['GET'])
@jwt_required()
def get_deck_game_history(deck_id):
    """Get the game history for a specific deck, including placement."""
    try:
        history = DeckService.get_deck_history(deck_id)
        return jsonify([asdict(entry) for entry in history]), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch deck history"}), 500