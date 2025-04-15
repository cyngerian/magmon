from datetime import datetime, timedelta
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
# Removed functools, secrets, string imports as they are now in utils.auth
from .. import db
from ..models import User, Game, AdminAuditLog, AdminActionType
from . import bp
from .utils.auth import admin_required, generate_temp_password # Import from utils

# Removed original definitions of admin_required and generate_temp_password
@bp.route('/admin/check', methods=['GET'])
@jwt_required()
def check_admin():
    """Check if current user is an admin"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify({'is_admin': bool(user and user.is_admin)})

@bp.route('/admin/users', methods=['GET'])
@jwt_required()
@admin_required
def list_users():
    """List all users with their status"""
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'avatar_url': user.avatar_url,
        'must_change_password': user.must_change_password,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'is_admin': user.is_admin
    } for user in users])

@bp.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@jwt_required()
@admin_required
def reset_user_password(user_id):
    """Reset a user's password and generate a temporary one"""
    user = User.query.get_or_404(user_id)
    
    # Don't allow resetting other admin passwords
    if user.is_admin and user.id != get_jwt_identity():
        return jsonify({'error': 'Cannot reset another admin\'s password'}), 403

    # Generate and set temporary password
    temp_password = generate_temp_password()
    user.set_temp_password(temp_password)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Password reset successful',
            'temp_password': temp_password,
            'expires_at': user.temp_password_expires_at.isoformat()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to reset password: {str(e)}'}), 500

@bp.route('/admin/users/<int:user_id>/make-admin', methods=['POST'])
@jwt_required()
@admin_required
def toggle_admin(user_id):
    """Toggle admin status for a user"""
    current_user_id = get_jwt_identity()
    if current_user_id == user_id:
        return jsonify({'error': 'Cannot modify your own admin status'}), 403

    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin

    try:
        db.session.commit()
        return jsonify({
            'message': f'Admin status {"granted to" if user.is_admin else "revoked from"} {user.username}',
            'is_admin': user.is_admin
        })
    except Exception as e:
        db.session.rollback()
@bp.route('/admin/games/deleted', methods=['GET'])
@jwt_required()
@admin_required
def list_deleted_games():
    """Get a list of all soft-deleted games"""
    deleted_games = Game.query.filter(Game.deleted_at.isnot(None)).all()
    
    return jsonify([{
        'id': game.id,
        'game_date': game.game_date.isoformat(),
        'deleted_at': game.deleted_at.isoformat(),
        'deleted_by': {
            'id': game.deleted_by_id,
            'username': game.deleted_by.username if game.deleted_by else None
        },
        'last_admin_action': game.last_admin_action,
        'last_admin_action_at': game.last_admin_action_at.isoformat() if game.last_admin_action_at else None
    } for game in deleted_games])

@bp.route('/admin/games/<int:game_id>/audit-log', methods=['GET'])
@jwt_required()
@admin_required
def get_game_audit_log(game_id):
    """Get the audit log history for a specific game"""
    # Verify game exists
    game = Game.query.get_or_404(game_id)
    
    # Get all audit log entries for this game
    audit_logs = AdminAuditLog.query.filter_by(
        target_type='game',
        target_id=game_id
    ).order_by(AdminAuditLog.created_at.desc()).all()
    
    return jsonify([{
        'id': log.id,
        'admin': {
            'id': log.admin_id,
            'username': log.admin.username
        },
        'action_type': log.action_type.value,
        'previous_state': log.previous_state,
        'new_state': log.new_state,
        'reason': log.reason,
        'created_at': log.created_at.isoformat()
    } for log in audit_logs])
@bp.route('/admin/games/<int:game_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_game(game_id):
    """Soft delete a game"""
    admin_id = get_jwt_identity()
    game = Game.query.get_or_404(game_id)
    reason = request.json.get('reason')

    if not reason:
        return jsonify({'error': 'Reason is required for deletion'}), 400

    if game.deleted_at:
        return jsonify({'error': 'Game is already deleted'}), 400

    # Store previous state for audit log
    previous_state = {
        'deleted_at': None,
        'deleted_by_id': None,
        'last_admin_action': game.last_admin_action,
        'last_admin_action_at': game.last_admin_action_at.isoformat() if game.last_admin_action_at else None
    }

    # Update game state
    game.deleted_at = datetime.utcnow()
    game.deleted_by_id = admin_id
    game.last_admin_action = AdminActionType.GAME_DELETE.value
    game.last_admin_action_at = datetime.utcnow()

    # Create audit log entry
    new_state = {
        'deleted_at': game.deleted_at.isoformat(),
        'deleted_by_id': game.deleted_by_id,
        'last_admin_action': game.last_admin_action,
        'last_admin_action_at': game.last_admin_action_at.isoformat()
    }

    audit_log = AdminAuditLog(
        admin_id=admin_id,
        action_type=AdminActionType.GAME_DELETE,
        target_type='game',
        target_id=game_id,
        previous_state=previous_state,
        new_state=new_state,
        reason=reason
    )

    try:
        db.session.add(game)
        db.session.add(audit_log)
        db.session.commit()
        return jsonify({
            'message': 'Game deleted successfully',
            'game_id': game_id,
            'deleted_at': game.deleted_at.isoformat(),
            'deleted_by': game.deleted_by_id
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting game: {str(e)}")  # Debug log
        import traceback
        traceback.print_exc()  # Print full stack trace
        return jsonify({'error': f'Failed to delete game: {str(e)}'}), 500

@bp.route('/admin/games/<int:game_id>/restore', methods=['POST'])
@jwt_required()
@admin_required
def restore_game(game_id):
    """Restore a soft-deleted game"""
    admin_id = get_jwt_identity()
    game = Game.query.get_or_404(game_id)
    reason = request.json.get('reason')

    if not reason:
        return jsonify({'error': 'Reason is required for restoration'}), 400

    if not game.deleted_at:
        return jsonify({'error': 'Game is not deleted'}), 400

    # Store previous state for audit log
    previous_state = {
        'deleted_at': game.deleted_at.isoformat(),
        'deleted_by_id': game.deleted_by_id,
        'last_admin_action': game.last_admin_action,
        'last_admin_action_at': game.last_admin_action_at.isoformat() if game.last_admin_action_at else None
    }

    # Update game state
    game.deleted_at = None
    game.deleted_by_id = None
    game.last_admin_action = AdminActionType.GAME_RESTORE.value
    game.last_admin_action_at = datetime.utcnow()

    # Create audit log entry
    new_state = {
        'deleted_at': None,
        'deleted_by_id': None,
        'last_admin_action': game.last_admin_action,
        'last_admin_action_at': game.last_admin_action_at.isoformat()
    }

    audit_log = AdminAuditLog(
        admin_id=admin_id,
        action_type=AdminActionType.GAME_RESTORE,
        target_type='game',
        target_id=game_id,
        previous_state=previous_state,
        new_state=new_state,
        reason=reason
    )

    try:
        db.session.add(game)
        db.session.add(audit_log)
        db.session.commit()
        return jsonify({
            'message': 'Game restored successfully',
            'game_id': game_id,
            'restored_at': game.last_admin_action_at.isoformat(),
            'restored_by': admin_id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to restore game: {str(e)}'}), 500