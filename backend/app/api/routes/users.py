from flask import jsonify
from sqlalchemy import func
from ... import db
from ...models import User, MatchPlayer
from .. import bp

@bp.route('/users', methods=['GET'])
def get_users():
    """Get a list of all registered users."""
    try:
        users = User.query.order_by(User.username).all()
        user_list = []
        for user in users:
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
                "avatar_url": user.avatar_url,
                "stats": {
                    "total_wins": win_count
                }
            })
        return jsonify(user_list), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching users: {e}")
        return jsonify({"error": "Failed to fetch users"}), 500

@bp.route('/users/<int:user_id>/decks', methods=['GET'])
def get_specific_user_decks(user_id):
    """Get all decks belonging to a specific user."""
    user = User.query.get_or_404(user_id)
    decks = Deck.query.filter_by(user_id=user_id).order_by(Deck.last_updated.desc()).all()
    deck_list = [{
        "id": deck.id,
        "name": deck.name,
        "commander": deck.commander,
        "colors": deck.colors,
        "last_updated": deck.last_updated.isoformat()
    } for deck in decks]
    return jsonify(deck_list), 200

@bp.route('/users/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    """Get public profile details for a specific user."""
    user = User.query.get_or_404(user_id)
    try:
        win_count = db.session.query(func.count(MatchPlayer.id)).filter(
            MatchPlayer.user_id == user_id,
            MatchPlayer.placement == 1
        ).scalar() or 0
    except Exception as e:
        current_app.logger.error(f"Error calculating wins for user {user_id}: {e}")
        win_count = 0

    profile_data = {
        "id": user.id,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "favorite_color": user.favorite_color,
        "retirement_plane": user.retirement_plane,
        "stats": {
            "total_wins": win_count
        }
    }
    return jsonify(profile_data), 200