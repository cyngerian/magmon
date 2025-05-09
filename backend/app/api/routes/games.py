# This file contains routes related to the game lifecycle,
# including creation, registration, results submission, and approval.

from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import aliased, joinedload
from sqlalchemy import func, select
from datetime import date, datetime # Added datetime

from backend.app import db
from backend.app.models import User, Deck, Match, MatchPlayer, Game, GameStatus, GameRegistration, DeckVersion
from backend.app.api import bp

# Import validation helpers from utils
from ..utils.game_validation import (
    validate_game_exists,
    validate_game_status,
    validate_game_registrations,
    validate_match_status
)

# ================== Game Routes ==================

@bp.route('/games', methods=['POST'])
def create_game():
    """ Manually creates a new Game record. """
    data = request.get_json()
    if not data: return jsonify({"error": "No input data provided"}), 400

    game_date_str = data.get('game_date')
    is_pauper = data.get('is_pauper', False)
    details = data.get('details')

    if not game_date_str:
        return jsonify({"error": "Missing required field: game_date"}), 400

    try:
        game_date = date.fromisoformat(game_date_str)
    except ValueError:
        return jsonify({"error": "Invalid game_date format. Use YYYY-MM-DD."}), 400

    # Check if a game already exists for this date
    if Game.query.filter_by(game_date=game_date).first():
        return jsonify({"error": f"A game for {game_date.strftime('%Y-%m-%d')} already exists."}), 409

    new_game = Game(game_date=game_date, status=GameStatus.UPCOMING, is_pauper=is_pauper, details=details)
    try:
        db.session.add(new_game)
        db.session.commit()
        return jsonify({"message": "Game created successfully", "game": {"id": new_game.id, "game_date": new_game.game_date.isoformat(), "status": new_game.status.value, "is_pauper": new_game.is_pauper, "details": new_game.details}}), 201
    except Exception as e:
        db.session.rollback(); current_app.logger.error(f"Error creating game: {e}"); return jsonify({"error": "Game creation failed"}), 500

@bp.route('/games', methods=['GET'])
def get_games():
    """ Get a list of games, optionally filtered by status. """
    status_filter = request.args.get('status')

    # Subquery for registration count
    reg_count_sq = select(
        GameRegistration.game_id,
        func.count(GameRegistration.id).label('registration_count')
    ).group_by(GameRegistration.game_id).subquery()

    # Alias for joining the subquery
    reg_count_alias = aliased(reg_count_sq)

    # Base query
    query = db.session.query(
        Game,
        reg_count_alias.c.registration_count
    ).outerjoin(
        reg_count_alias, Game.id == reg_count_alias.c.game_id
    )
    # Removed .options(subqueryload(Game.matches)) due to lazy='dynamic' incompatibility

    if status_filter:
        try:
            status_enum = GameStatus(status_filter)
            query = query.filter(Game.status == status_enum)
        except ValueError:
            return jsonify({"error": f"Invalid status filter: {status_filter}. Valid: {[s.value for s in GameStatus]}"}), 400

    try:
        # Execute the optimized query
        results = query.order_by(Game.game_date.desc()).all()
        game_list = []

        for g, reg_count in results: # Unpack game and count
            # Access the first match from the pre-loaded collection
            # Note: g.matches is still a query object due to lazy='dynamic',
            # but the data is loaded, so .first() is efficient here.
            match = g.matches.first()

            game_data = {
                "id": g.id,
                "game_date": g.game_date.isoformat(),
                "status": g.status.value,
                "is_pauper": g.is_pauper,
                "details": g.details,
                "match_id": match.id if match else None,
                "match_status": match.status if match else None,
                "submitted_by_id": match.submitted_by_id if match else None,
                "registration_count": reg_count if reg_count is not None else 0, # Use the count from the query
                "winner_id": None, # Placeholder
                "winner_username": None # Placeholder
            }
            # If game is completed and match approved, find the winner
            if g.status == GameStatus.COMPLETED and match and match.status == 'approved':
                current_app.logger.info(f"Looking for winner for game {g.id} with match {match.id}")
                winner_player = MatchPlayer.query.filter_by(match_id=match.id, placement=1).first()
                if winner_player:
                    current_app.logger.info(f"Found winner player: {winner_player.user_id}")
                    if winner_player.user:
                        current_app.logger.info(f"Found winner user: {winner_player.user.username}")
                        game_data["winner_id"] = winner_player.user_id
                        game_data["winner_username"] = winner_player.user.username
                else:
                    current_app.logger.info(f"No winner player found for match {match.id}")

            game_list.append(game_data)

        # Ensure proper JSON formatting with commas between fields
        return jsonify(game_list), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching games: {e}")
        return jsonify({"error": "Failed to fetch games"}), 500

@bp.route('/games/<int:game_id>', methods=['PATCH'])
def update_game_status(game_id):
    """ Updates the status of a game (e.g., to Cancelled). """
    game = Game.query.get_or_404(game_id)
    data = request.get_json()
    if not data or 'status' not in data: return jsonify({"error": "Missing 'status' in request body"}), 400
    new_status_str = data['status']
    try: new_status = GameStatus(new_status_str)
    except ValueError: return jsonify({"error": f"Invalid status: {new_status_str}. Valid: {[s.value for s in GameStatus]}"}), 400
    if game.status == GameStatus.COMPLETED and new_status != GameStatus.COMPLETED: return jsonify({"error": "Cannot change status of completed game."}), 400
    if game.status == GameStatus.CANCELLED and new_status != GameStatus.CANCELLED: return jsonify({"error": "Cannot change status of cancelled game."}), 400
    game.status = new_status
    try:
        db.session.add(game); db.session.commit()
        return jsonify({"message": "Game status updated", "game": {"id": game.id, "game_date": game.game_date.isoformat(), "status": game.status.value, "is_pauper": game.is_pauper, "details": game.details}}), 200
    except Exception as e:
        db.session.rollback(); current_app.logger.error(f"Error updating game status: {e}"); return jsonify({"error": "Status update failed"}), 500

@bp.route('/games/<int:game_id>/registrations', methods=['POST'])
@jwt_required()
def register_for_game(game_id):
    """ Registers the logged-in user's selected deck for a specific game. """
    current_user_id = get_jwt_identity() # Get user from token
    data = request.get_json()
    deck_id = data.get('deck_id')
    deck_version_id = data.get('deck_version_id')
    
    if not deck_id: return jsonify({"error": "Missing deck_id"}), 400
    
    game = Game.query.get_or_404(game_id)
    if game.status != GameStatus.UPCOMING: return jsonify({"error": "Can only register for upcoming games"}), 400
    
    user = User.query.get(current_user_id)
    deck = Deck.query.get(deck_id)
    if not user or not deck: return jsonify({"error": "User or Deck not found"}), 404
    if deck.user_id != user.id: return jsonify({"error": "Deck does not belong to the user"}), 403
    if GameRegistration.query.filter_by(game_id=game_id, user_id=current_user_id).first(): return jsonify({"error": "User already registered"}), 409
    
    # If no version ID is provided, use the current version
    if not deck_version_id and deck.current_version_id:
        deck_version_id = deck.current_version_id
    
    # Create the registration
    new_registration = GameRegistration(
        game_id=game_id,
        user_id=current_user_id,
        deck_id=deck_id,
        deck_version_id=deck_version_id
    )
    
    try:
        db.session.add(new_registration)
        db.session.commit()
        return jsonify({"message": "Successfully registered for game"}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error registering: {e}")
        return jsonify({"error": "Registration failed"}), 500

@bp.route('/games/<int:game_id>/registrations', methods=['GET'])
def get_game_registrations(game_id):
    """ Gets the list of players and decks registered for a specific game. """
    game = Game.query.get_or_404(game_id)
    registrations = GameRegistration.query.filter_by(game_id=game_id).all()
    
    reg_list = []
    for reg in registrations:
        reg_data = {
            "registration_id": reg.id,
            "user_id": reg.user_id,
            "username": reg.player.username,
            "deck_id": reg.deck_id,
            "deck_name": reg.deck.name,
            "commander": reg.deck.commander,
            "colors": reg.deck.colors,
            "deck_version_id": reg.deck_version_id
        }
        
        # Add version information if available
        if reg.deck_version_id:
            version = DeckVersion.query.get(reg.deck_version_id)
            if version:
                reg_data["version_number"] = version.version_number
                reg_data["version_notes"] = version.notes
        
        reg_list.append(reg_data)
    
    return jsonify(reg_list), 200

@bp.route('/games/<int:game_id>/registrations', methods=['DELETE'])
@jwt_required()
def unregister_from_game(game_id):
    """ Unregisters the logged-in user from a specific upcoming game. """
    current_user_id = get_jwt_identity()
    user_id = int(current_user_id) # Ensure integer comparison

    game = Game.query.get_or_404(game_id)
    if game.status != GameStatus.UPCOMING:
        return jsonify({"error": "Can only unregister from upcoming games"}), 400

    registration = GameRegistration.query.filter_by(game_id=game_id, user_id=user_id).first()

    if not registration:
        return jsonify({"error": "User is not registered for this game"}), 404

    try:
        db.session.delete(registration)
        db.session.commit()
        return jsonify({"message": "Successfully unregistered from game"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error unregistering user {user_id} from game {game_id}: {e}")
        return jsonify({"error": "Unregistration failed"}), 500

# ================== Game Results Routes ==================

@bp.route('/matches', methods=['POST'])
@jwt_required()
def submit_match():
    """Submit results for a completed game.
    
    This represents the completion phase of a game's lifecycle:
    1. Validates game exists and is in UPCOMING status
    2. Validates all registered players have placements
    3. Creates a Match record to store results
    4. Updates game status to COMPLETED (pending approval)
    
    The match will be in 'pending' status until approved by another user,
    at which point the game's COMPLETED status becomes final.
    """
    data = request.get_json()
    if not data: return jsonify({"error": "No input data provided"}), 400
    current_user_id = get_jwt_identity() # Get submitter from token
    required_fields = ['game_id', 'placements'] # submitted_by_id comes from token
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields (game_id, placements)"}), 400

    # Use validation helpers
    game = validate_game_exists(data['game_id'])
    if error := validate_game_status(game, GameStatus.UPCOMING):
        return jsonify(error[0]), error[1]
    if error := validate_game_registrations(game, required_count=2):
        return jsonify(error[0]), error[1]

    placements_data = data.get('placements')
    if not isinstance(placements_data, list) or len(placements_data) < 2: return jsonify({"error": "'placements' must be a list with at least 2 participants"}), 400
    player_count = len(placements_data)

    submitter = User.query.get(current_user_id) # Get submitter from token
    if not submitter: return jsonify({"error": "Submitter user (from token) not found"}), 404 # Should not happen

    registered_players = {reg.user_id: reg.deck_id for reg in GameRegistration.query.filter_by(game_id=game.id).all()}
    player_ids_in_placements = set()
    placements_dict = {}
    for placement_info in placements_data:
        if not isinstance(placement_info, dict) or 'user_id' not in placement_info or 'placement' not in placement_info: return jsonify({"error": "Invalid placement entry format"}), 400
        user_id = placement_info['user_id']; placement = placement_info['placement']
        if not isinstance(placement, int) or placement < 1 or placement > player_count: return jsonify({"error": f"Invalid placement value {placement} for user {user_id}"}), 400
        if user_id in player_ids_in_placements: return jsonify({"error": f"Duplicate user ID {user_id} in placements"}), 400
        if placement in placements_dict.values(): return jsonify({"error": f"Duplicate placement value {placement}"}), 400
        if user_id not in registered_players: return jsonify({"error": f"User ID {user_id} was not registered for this game."}), 400
        player_ids_in_placements.add(user_id); placements_dict[user_id] = placement

    if len(registered_players) != len(player_ids_in_placements): return jsonify({"error": "Placement data does not match registered players."}), 400
    if set(registered_players.keys()) != player_ids_in_placements: return jsonify({"error": "Placement user IDs do not match registered IDs."}), 400

    start_time = None; end_time = None
    try:
        if data.get('start_time'): start_time = datetime.fromisoformat(data['start_time'].replace(" ", "T"))
        if data.get('end_time'): end_time = datetime.fromisoformat(data['end_time'].replace(" ", "T"))
    except ValueError: return jsonify({"error": "Invalid datetime format. Use YYYY-MM-DDTHH:MM or YYYY-MM-DD HH:MM"}), 400

    new_match = Match(
        game_id=game.id, submitted_by_id=current_user_id, # Use submitter from token
        player_count=player_count, start_time=start_time, end_time=end_time, status='pending',
        notes_big_interaction=data.get('notes_big_interaction'), notes_rules_discussion=data.get('notes_rules_discussion'), notes_end_summary=data.get('notes_end_summary')
    )
    try:
        db.session.add(new_match); db.session.flush()
        
        # Get all registrations with deck versions
        registrations = GameRegistration.query.filter_by(game_id=game.id).all()
        reg_dict = {reg.user_id: reg for reg in registrations}
        
        for user_id, placement in placements_dict.items():
            deck_id = registered_players[user_id]
            
            # Get the deck version ID from the registration
            deck_version_id = None
            if user_id in reg_dict and reg_dict[user_id].deck_version_id:
                deck_version_id = reg_dict[user_id].deck_version_id
            
            match_player_entry = MatchPlayer(
                match_id=new_match.id,
                user_id=user_id,
                deck_id=deck_id,
                deck_version_id=deck_version_id,
                placement=placement
            )
            db.session.add(match_player_entry)

        game.status = GameStatus.COMPLETED
        db.session.add(game)

        db.session.commit()
        # Use consistent terminology in response message
        return jsonify({"message": "Game results submitted successfully", "match_id": new_match.id}), 201
    except Exception as e:
        # Use consistent terminology in error message and log
        db.session.rollback(); current_app.logger.error(f"Error submitting game results: {e}"); return jsonify({"error": "Game result submission failed"}), 500

# --- Match Approval Routes ---

@bp.route('/matches', methods=['GET'])
def get_matches():
    """Get a list of completed games with their results.
    
    This endpoint returns games that have had results submitted,
    optionally filtered by approval status:
    - pending: Results submitted but not yet approved
    - approved: Results approved and final
    
    Each result includes:
    - Game details (date, status)
    - Player count
    - Submission details (who, when)
    - Approval details (who, when) if approved
    """
    status_filter = request.args.get('status')
    query = Match.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    try:
        matches = query.order_by(Match.created_at.desc()).all()
        match_list = [{
            "match_id": m.id,
            "game_id": m.game_id,
            "game_date": m.game.game_date.isoformat() if m.game else None,
            "status": m.status,
            "player_count": m.player_count,
            "submitted_by": m.submitter.username,
            "created_at": m.created_at.isoformat(),
            "approved_by": m.approver.username if m.approved_by_id else None, # Include approver username
            "approved_at": m.approved_at.isoformat() if m.approved_at else None
        } for m in matches]
        return jsonify(match_list), 200
    except Exception as e:
        # Use consistent terminology in error message and log
        current_app.logger.error(f"Error fetching game results: {e}")
        return jsonify({"error": "Failed to fetch game results"}), 500


@bp.route('/matches/<int:match_id>/approve', methods=['PATCH'])
@jwt_required()
def approve_match(match_id):
    """Approve game results, finalizing the game's completion.
    
    This represents the final phase of a game's lifecycle:
    1. Validates match exists and is in pending status
    2. Validates approver is not the same as submitter
    3. Updates match status to approved
    4. Game status remains COMPLETED
    
    Once approved, the game results are final and cannot be changed.
    """
    match = Match.query.get_or_404(match_id)
    if error := validate_match_status(match, 'pending'):
        return jsonify(error[0]), error[1]

    approver_id = get_jwt_identity() # Approver is the logged-in user
    data = request.get_json() # Still need data for notes
    approval_notes = data.get('approval_notes') if data else None

    # No need for approver_id in payload anymore
    approver = User.query.get(approver_id)
    if not approver: return jsonify({"error": "Approver user (from token) not found"}), 404 # Should not happen

    # Prevent self-approval
    if match.submitted_by_id == approver_id:
        return jsonify({"error": "Cannot approve your own submitted match"}), 403

    match.status = 'approved'
    match.approved_by_id = approver_id
    match.approved_at = datetime.utcnow()
    match.approval_notes = approval_notes # Save notes

    # TODO: Calculate season number here based on approved matches?

    try:
        db.session.add(match)
        db.session.commit()
        # Use consistent terminology in response message
        return jsonify({"message": "Game results approved successfully", "match_id": match.id, "status": match.status}), 200
    except Exception as e:
        db.session.rollback()
        # Use consistent terminology in error message and log
        current_app.logger.error(f"Error approving game results: {e}")
        return jsonify({"error": "Game result approval failed"}), 500

@bp.route('/matches/<int:match_id>/reject', methods=['PATCH'])
@jwt_required()
def reject_match(match_id):
    """Reject game results, allowing resubmission.
    
    This represents a reset in the game's lifecycle:
    1. Validates match exists and is in pending status
    2. Clears approval-related fields
    3. Updates match status back to pending
    4. Resets game status to UPCOMING
    
    After rejection, new results can be submitted for the game.
    """
    match = Match.query.get_or_404(match_id)
    if error := validate_match_status(match, 'pending'):
        return jsonify(error[0]), error[1]

    rejector_id = get_jwt_identity() # Rejector is the logged-in user
    data = request.get_json() # Still need data for notes
    approval_notes = data.get('approval_notes') if data else None

    # No need for rejected_by_id in payload
    rejector = User.query.get(rejector_id)
    if not rejector: return jsonify({"error": "Rejector user (from token) not found"}), 404 # Should not happen

    # Prevent self-rejection? Usually not necessary but possible.
    # if match.submitted_by_id == rejector_id:
    #     return jsonify({"error": "Cannot reject your own submitted match"}), 403

    # Option 1: Delete the match record entirely upon rejection
    # Option 2: Set status to 'rejected' (requires adding 'rejected' to Match status options)
    # Option 3: Keep status 'pending' but clear placements/add notes, requiring re-submission?
    # Let's go with Option 1 for simplicity now: Delete the match and its players.
    # Alternatively, just update notes and keep pending? Let's update notes and keep pending.

    match.status = 'pending' # Keep as pending
    match.approved_by_id = None # Clear any potential previous approver
    match.approved_at = None
    match.approval_notes = f"Rejected by {rejector.username}: {approval_notes or 'No reason provided.'}" # Use username

    # Also need to potentially reset the Game status if it was set to Completed
    if match.game:
        match.game.status = GameStatus.UPCOMING # Or determine appropriate status
        db.session.add(match.game)

    try:
        db.session.add(match)
        db.session.commit()
        # Use consistent terminology in response message
        return jsonify({"message": "Game result rejection noted. Kept as pending.", "match_id": match.id}), 200
    except Exception as e:
        db.session.rollback()
        # Use consistent terminology in error message and log
        current_app.logger.error(f"Error rejecting game results: {e}")
        return jsonify({"error": "Game result rejection failed"}), 500

@bp.route('/matches/<int:match_id>', methods=['GET'])
def get_match_details(match_id):
    """Get detailed results for a completed game.
    
    Returns comprehensive information about a game's results:
    1. Game metadata (date, status)
    2. Player results (placements, decks used)
    3. Game notes (interactions, rules discussions)
    4. Submission/approval details
    
    Uses eager loading to efficiently fetch all related data
    in a single query.
    """
    # Eager load related objects to prevent N+1 queries
    match = Match.query.options(
        db.joinedload(Match.submitter), # Eager load submitter
        db.joinedload(Match.approver),  # Eager load approver
        db.joinedload(Match.game)       # Eager load game
    ).get_or_404(match_id)

    players = MatchPlayer.query.options(
        db.joinedload(MatchPlayer.user), # Eager load user
        db.joinedload(MatchPlayer.deck)  # Eager load deck
    ).filter_by(match_id=match_id).order_by(MatchPlayer.placement).all()

    # Build player details safely, checking for None relationships
    player_details = []
    for p in players:
        player_info = {
            "user_id": p.user_id,
            "username": p.user.username if p.user else "Unknown User",
            "deck_id": p.deck_id,
            "deck_name": p.deck.name if p.deck else "Unknown Deck",
            "commander": p.deck.commander if p.deck else "Unknown",
            "placement": p.placement,
            "deck_version_id": p.deck_version_id
        }
        
        # Add version information if available
        if p.deck_version_id:
            version = DeckVersion.query.get(p.deck_version_id)
            if version:
                player_info["version_number"] = version.version_number
                player_info["version_notes"] = version.notes
        
        player_details.append(player_info)

    match_data = {
        "match_id": match.id,
        "game_id": match.game_id,
        # Safely access game date
        "game_date": match.game.game_date.isoformat() if match.game and match.game.game_date else None,
        "status": match.status,
        "player_count": match.player_count,
        "submitted_by_id": match.submitted_by_id,
        # Safely access submitter username
        "submitted_by_username": match.submitter.username if match.submitter else None,
        "created_at": match.created_at.isoformat(), # created_at is required
        "approved_by_id": match.approved_by_id,
        # Safely access approver username
        "approved_by_username": match.approver.username if match.approver else None,
        # Safely call isoformat on nullable datetime
        "approved_at": match.approved_at.isoformat() if match.approved_at else None,
        "approval_notes": match.approval_notes,
        # Safely call isoformat on nullable datetime
        "start_time": match.start_time.isoformat() if match.start_time else None,
        # Safely call isoformat on nullable datetime
        "end_time": match.end_time.isoformat() if match.end_time else None,
        "notes_big_interaction": match.notes_big_interaction,
        "notes_rules_discussion": match.notes_rules_discussion,
        "notes_end_summary": match.notes_end_summary,
        "players": player_details
    }
    return jsonify(match_data), 200
