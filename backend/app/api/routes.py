import os # Needed for path operations
from flask import request, jsonify, current_app, url_for, send_from_directory
from werkzeug.utils import secure_filename # For secure file handling
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity # Import JWT functions
from datetime import datetime, date # Import date
from . import bp # Import the blueprint instance
from sqlalchemy.orm import subqueryload, aliased, joinedload # Added joinedload
from sqlalchemy import func, select
from .. import db, create_app # Import create_app to access app context outside request
# Import all necessary models (with updated names: Game, GameStatus, GameRegistration)
from ..models import User, Deck, Match, MatchPlayer, Game, GameStatus, GameRegistration, DeckVersion

@bp.route('/register', methods=['POST'])
def register_user():
    """ User registration endpoint. """
    data = request.get_json()
    if not data: return jsonify({"error": "No input data provided"}), 400
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if not username or not email or not password: return jsonify({"error": "Missing username, email, or password"}), 400
    if User.query.filter((User.username == username) | (User.email == email)).first(): return jsonify({"error": "Username or email already exists"}), 409
    new_user = User(username=username, email=email)
    new_user.set_password(password)
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully", "user": {"id": new_user.id, "username": new_user.username, "email": new_user.email}}), 201
    except Exception as e:
        db.session.rollback(); current_app.logger.error(f"Error registering user: {e}"); return jsonify({"error": "Registration failed due to server error"}), 500

# Login endpoint moved to auth.py

# ================== Deck Routes ==================

@bp.route('/decks', methods=['POST'])
@jwt_required()
def create_deck():
    """ Create a new deck for the logged-in user. """
    current_user_id = get_jwt_identity() # Get user from JWT identity

    data = request.get_json()
    if not data: return jsonify({"error": "No input data provided"}), 400
    required_fields = ['name', 'commander', 'colors'] # user_id no longer needed in payload
    if not all(field in data for field in required_fields): return jsonify({"error": "Missing required fields (name, commander, colors)"}), 400

    # TODO: Validate colors string
    new_deck = Deck(name=data['name'], commander=data['commander'], colors=data['colors'], decklist_text=data.get('decklist_text', ''), user_id=current_user_id) # Use ID from token
    try:
        db.session.add(new_deck)
        db.session.flush()  # Get the deck ID
        
        # Create the initial version
        initial_version = DeckVersion(
            deck_id=new_deck.id,
            version_number=1,
            decklist_text=data.get('decklist_text', ''),
            notes="Initial version"
        )
        db.session.add(initial_version)
        db.session.flush()  # Get the version ID
        
        # Set the current version
        new_deck.current_version_id = initial_version.id
        db.session.add(new_deck)
        db.session.commit()
        
        return jsonify({"message": "Deck created successfully", "deck": {"id": new_deck.id, "name": new_deck.name, "commander": new_deck.commander, "colors": new_deck.colors, "user_id": new_deck.user_id}}), 201
    except Exception as e:
        db.session.rollback(); current_app.logger.error(f"Error creating deck: {e}"); return jsonify({"error": "Deck creation failed"}), 500

@bp.route('/decks', methods=['GET'])
@jwt_required()
def get_user_decks():
    """ Get all decks belonging to the logged-in user. """
    current_user_id = get_jwt_identity() # Get user from JWT identity
    user_id = current_user_id # Use ID from token

    decks = Deck.query.filter_by(user_id=user_id).order_by(Deck.last_updated.desc()).all()
    deck_list = [{"id": deck.id, "name": deck.name, "commander": deck.commander, "colors": deck.colors, "last_updated": deck.last_updated.isoformat()} for deck in decks]
    return jsonify(deck_list), 200

@bp.route('/decks/<int:deck_id>', methods=['GET'])
@jwt_required()
def get_deck_details(deck_id):
    """ Get full details for a specific deck, including decklist. """
    deck = Deck.query.get_or_404(deck_id)
    # Removed ownership check - any logged-in user can view details
    # TODO: Add admin check later if needed
    
    # Get the current version if it exists
    current_version = None
    if deck.current_version_id:
        current_version = DeckVersion.query.get(deck.current_version_id)
    
    # Use the decklist from the current version if available
    decklist_text = current_version.decklist_text if current_version else deck.decklist_text
    
    return jsonify({
        "id": deck.id, 
        "name": deck.name, 
        "commander": deck.commander, 
        "colors": deck.colors, 
        "decklist_text": decklist_text, 
        "user_id": deck.user_id, 
        "created_at": deck.created_at.isoformat(), 
        "last_updated": deck.last_updated.isoformat(),
        "current_version_id": deck.current_version_id
    }), 200

@bp.route('/decks/<int:deck_id>/versions', methods=['GET'])
@jwt_required()
def get_deck_versions(deck_id):
    """ Get all versions of a specific deck. """
    deck = Deck.query.get_or_404(deck_id)
    
    # Get all versions
    versions = DeckVersion.query.filter_by(deck_id=deck_id).order_by(DeckVersion.version_number.desc()).all()
    
    versions_list = [{
        "id": version.id,
        "version_number": version.version_number,
        "created_at": version.created_at.isoformat(),
        "notes": version.notes,
        "is_current": version.id == deck.current_version_id
    } for version in versions]
    
    return jsonify(versions_list), 200

@bp.route('/decks/<int:deck_id>/versions/<int:version_id>', methods=['GET'])
@jwt_required()
def get_deck_version(deck_id, version_id):
    """ Get a specific version of a deck. """
    # Get the version
    version = DeckVersion.query.filter_by(deck_id=deck_id, id=version_id).first_or_404()
    
    version_data = {
        "id": version.id,
        "version_number": version.version_number,
        "created_at": version.created_at.isoformat(),
        "notes": version.notes,
        "decklist_text": version.decklist_text,
        "is_current": version.id == version.deck.current_version_id
    }
    
    return jsonify(version_data), 200

@bp.route('/decks/<int:deck_id>/versions', methods=['POST'])
@jwt_required()
def create_deck_version(deck_id):
    """ Create a new version of a deck. """
    current_user_id = get_jwt_identity()
    
    # Get the deck
    deck = Deck.query.get_or_404(deck_id)
    
    # Check ownership
    if deck.user_id != int(current_user_id):
        return jsonify({"error": "You don't own this deck"}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    # Get the latest version number
    latest_version = DeckVersion.query.filter_by(deck_id=deck_id).order_by(DeckVersion.version_number.desc()).first()
    new_version_number = 1 if not latest_version else latest_version.version_number + 1
    
    # Create the new version
    new_version = DeckVersion(
        deck_id=deck_id,
        version_number=new_version_number,
        decklist_text=data.get('decklist_text', ''),
        notes=data.get('notes', '')
    )
    
    try:
        db.session.add(new_version)
        db.session.flush()  # Get the version ID
        
        # Update the current version
        deck.current_version_id = new_version.id
        db.session.add(deck)
        db.session.commit()
        
        return jsonify({
            "message": "New version created successfully",
            "version": {
                "id": new_version.id,
                "version_number": new_version.version_number,
                "created_at": new_version.created_at.isoformat(),
                "notes": new_version.notes
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating deck version: {e}")
        return jsonify({"error": "Version creation failed"}), 500

@bp.route('/decks/<int:deck_id>/history', methods=['GET'])
@jwt_required()
def get_deck_game_history(deck_id):
    """ Get the game history for a specific deck, including placement. """
    deck = Deck.query.options(joinedload(Deck.owner)).get_or_404(deck_id) # Eager load owner
    # Removed ownership check - any logged-in user can view history
    owner_id = deck.user_id # Use owner_id for the query below

    try:
        # Query joining GameRegistration, Game, Match, and MatchPlayer
        # Revised Query: Start from Game, join Registration, outer join Match/Player
        results = db.session.query(
            Game.id.label('game_id'),
            Game.game_date,
            DeckVersion.version_number, # Select version_number instead of ID
            MatchPlayer.placement # Get placement via outer joins
        ).select_from(Game).join( # Start from Game
            GameRegistration, Game.id == GameRegistration.game_id
        ).outerjoin( # Use outerjoin in case a registration exists but the version was somehow deleted
            DeckVersion, GameRegistration.deck_version_id == DeckVersion.id
        ).outerjoin(
            Match, Match.game_id == Game.id
        ).outerjoin(
            MatchPlayer,
            (MatchPlayer.match_id == Match.id) & (MatchPlayer.user_id == owner_id) # Join placement for the deck owner
        ).filter(
            GameRegistration.deck_id == deck_id # Filter by deck registration
        ).order_by(
            Game.game_date.desc()
        ).all()

        history_list = [
            {
                "game_id": r.game_id,
                "game_date": r.game_date.isoformat(),
                "placement": r.placement, # Will be None if no match or no placement recorded
                "version_number": r.version_number # Return version_number
            } for r in results
        ]

        return jsonify(history_list), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching deck history for deck {deck_id}: {e}")
        return jsonify({"error": "Failed to fetch deck history"}), 500


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

# ================== User Routes ==================

@bp.route('/users', methods=['GET'])
def get_users():
    """ Get a list of all registered users. """
    try:
        users = User.query.order_by(User.username).all()
        # Include profile fields in the response
        user_list = []
        for user in users:
            # Calculate wins for each user (potential N+1 issue)
            try:
                win_count = db.session.query(func.count(MatchPlayer.id)).filter(
                    MatchPlayer.user_id == user.id,
                    MatchPlayer.placement == 1
                ).scalar() or 0
            except Exception as e:
                 current_app.logger.error(f"Error calculating wins for user {user.id} in user list: {e}")
                 win_count = 0

            user_list.append({
                "id": user.id,
                "username": user.username,
                # "email": user.email, # Probably don't need email in the list view
                "avatar_url": user.avatar_url,
                # "favorite_color": user.favorite_color, # Not needed for list view
                # "retirement_plane": user.retirement_plane, # Not needed for list view
                "stats": {
                    "total_wins": win_count
                }
            })
        return jsonify(user_list), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching users: {e}"); return jsonify({"error": "Failed to fetch users"}), 500

@bp.route('/users/<int:user_id>/decks', methods=['GET'])
def get_specific_user_decks(user_id):
    """ Get all decks belonging to a specific user identified by user_id in the URL. """
    user = User.query.get_or_404(user_id)
    decks = Deck.query.filter_by(user_id=user_id).order_by(Deck.last_updated.desc()).all()
    deck_list = [{"id": deck.id, "name": deck.name, "commander": deck.commander, "colors": deck.colors, "last_updated": deck.last_updated.isoformat()} for deck in decks]
    return jsonify(deck_list), 200
# New route to get public profile for a specific user
@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    """ Get public profile details for a specific user. """
    user = User.query.get_or_404(user_id)
    # Calculate total wins
    try:
        win_count = db.session.query(func.count(MatchPlayer.id)).filter(
            MatchPlayer.user_id == user_id,
            MatchPlayer.placement == 1
        ).scalar() or 0 # Use scalar() and default to 0 if None
    except Exception as e:
        current_app.logger.error(f"Error calculating wins for user {user_id}: {e}")
        win_count = 0 # Default to 0 on error

    profile_data = {
        "id": user.id,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "favorite_color": user.favorite_color,
        "retirement_plane": user.retirement_plane,
        "stats": {
            "total_wins": win_count
            # Add 'current_form' here later if needed
        }
    }
    return jsonify(profile_data), 200

# ================== Profile Routes ================== # Renamed section

# TODO: Add authentication requirement to these routes (e.g., @jwt_required())

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_my_profile():
    """ Get the profile details for the currently logged-in user. """
    current_user_id = get_jwt_identity() # Get user ID from JWT
    # === End Placeholder === # Removed redundant placeholder comments

    user = User.query.get(current_user_id)
    if not user:
        # This case should ideally not happen if auth is working
        return jsonify({"error": "User not found"}), 404

    profile_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email, # Own email is fine
        "avatar_url": user.avatar_url,
        "favorite_color": user.favorite_color,
        "retirement_plane": user.retirement_plane,
        "registered_on": user.registered_on.isoformat()
    }
    return jsonify(profile_data), 200

@bp.route('/profile', methods=['PATCH'])
@jwt_required()
def update_my_profile():
    """ Update the profile details for the currently logged-in user. """
    current_user_id = get_jwt_identity() # Get user ID from JWT
    # === End Placeholder === # Removed redundant placeholder comments

    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404 # Should be handled by auth

    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    updated = False
    if 'favorite_color' in data:
        user.favorite_color = data['favorite_color']
        updated = True
    if 'retirement_plane' in data:
        user.retirement_plane = data['retirement_plane']
        updated = True
    # Note: avatar_url update will be handled by a separate file upload endpoint

    if not updated:
        return jsonify({"message": "No profile fields provided to update"}), 400

    try:
        db.session.add(user)
        db.session.commit()
        # Return updated profile data
        profile_data = {
            "id": user.id, "username": user.username, "email": user.email,
            "avatar_url": user.avatar_url, "favorite_color": user.favorite_color,
            "retirement_plane": user.retirement_plane, "registered_on": user.registered_on.isoformat()
        }
        return jsonify({"message": "Profile updated successfully", "profile": profile_data}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating profile for user {current_user_id}: {e}")
        return jsonify({"error": "Profile update failed"}), 500

# Define allowed extensions and upload folder path relative to static folder
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER_REL = 'uploads/avatars'

# Directory creation moved to create_app in __init__.py

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/profile/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """ Uploads an avatar image for the logged-in user. """
    current_user_id = get_jwt_identity() # Get user ID from JWT
    # === End Placeholder === # Removed redundant placeholder comments

    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404 # Should be handled by auth

    if 'avatar' not in request.files:
        return jsonify({"error": "No avatar file part in the request"}), 400
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        # Create a secure filename (e.g., user_1_avatar.jpg)
        filename = secure_filename(f"user_{current_user_id}_avatar.{file.filename.rsplit('.', 1)[1].lower()}")
        # Use absolute path for saving based on app's static folder (get path within route)
        absolute_upload_folder = os.path.join(current_app.static_folder, UPLOAD_FOLDER_REL)
        absolute_filepath = os.path.join(absolute_upload_folder, filename)

        try:
            # TODO: Add resizing logic here if needed
            file.save(absolute_filepath)
            current_app.logger.info(f"Avatar saved to: {absolute_filepath}")

            # Construct the URL path relative to the static folder for URL generation
            url_path_relative_to_static = os.path.join(UPLOAD_FOLDER_REL, filename)

            # Update user's avatar_url using url_for('static', ...)
            # This assumes the 'static' endpoint serves files from app.static_folder
            user.avatar_url = url_for('static', filename=url_path_relative_to_static, _external=False) # Use relative URL

            db.session.add(user)
            db.session.commit()

            return jsonify({"message": "Avatar uploaded successfully", "avatar_url": user.avatar_url}), 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error uploading avatar for user {current_user_id}: {e}")
            # Attempt to remove partially saved file if error occurred during DB commit
            if os.path.exists(absolute_filepath):
                 try: os.remove(absolute_filepath)
                 except OSError as remove_error:
                     current_app.logger.error(f"Error removing partially uploaded file {absolute_filepath}: {remove_error}")
            return jsonify({"error": "Avatar upload failed"}), 500
    else:
        return jsonify({"error": "File type not allowed"}), 400

# Note: Serving static files like avatars is typically handled by Flask's built-in
# static file serving (if app.static_folder is set correctly, usually './static')
# or by a web server like Nginx in production. No separate route needed here usually.


# ================== Match Routes ==================

@bp.route('/matches', methods=['POST'])
@jwt_required()
def submit_match():
    """ Submit match results (placements, times, notes) for a specific Game. """
    data = request.get_json()
    if not data: return jsonify({"error": "No input data provided"}), 400
    current_user_id = get_jwt_identity() # Get submitter from token
    required_fields = ['game_id', 'placements'] # submitted_by_id comes from token
    if not all(field in data for field in required_fields): return jsonify({"error": "Missing required fields (game_id, placements)"}), 400

    game = Game.query.get(data['game_id'])
    if not game: return jsonify({"error": "Game not found"}), 404

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
        return jsonify({"message": "Match submitted successfully", "match_id": new_match.id}), 201 # Updated message
    except Exception as e:
        db.session.rollback(); current_app.logger.error(f"Error submitting match: {e}"); return jsonify({"error": "Match submission failed"}), 500

# --- Match Approval Routes ---

@bp.route('/matches', methods=['GET'])
def get_matches():
    """ Gets a list of matches, optionally filtered by status. """
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
        current_app.logger.error(f"Error fetching matches: {e}")
        return jsonify({"error": "Failed to fetch matches"}), 500


@bp.route('/matches/<int:match_id>/approve', methods=['PATCH'])
@jwt_required()
def approve_match(match_id):
    """ Approves a pending match result. """
    match = Match.query.get_or_404(match_id)
    if match.status != 'pending':
        return jsonify({"error": "Match is not pending approval"}), 400

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
        return jsonify({"message": "Match approved successfully", "match_id": match.id, "status": match.status}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving match: {e}")
        return jsonify({"error": "Match approval failed"}), 500

# Add route for rejecting a match
@bp.route('/matches/<int:match_id>/reject', methods=['PATCH'])
@jwt_required()
def reject_match(match_id):
    """ Rejects a pending match result, setting status back to allow re-submission or deletion. """
    match = Match.query.get_or_404(match_id)
    if match.status != 'pending':
        return jsonify({"error": "Match is not pending approval"}), 400

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
        return jsonify({"message": "Match rejection noted. Kept as pending.", "match_id": match.id}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting match: {e}")
        return jsonify({"error": "Match rejection failed"}), 500

@bp.route('/matches/<int:match_id>', methods=['GET'])
def get_match_details(match_id):
    """ Gets the full details for a specific match, including players and placements. """
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

# Add other API routes here later
