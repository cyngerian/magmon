from datetime import datetime, timedelta
from flask import jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from .. import db
from ..models import User
from . import bp

@bp.route('/login', methods=['POST'])
def login():
    """Handle user login with support for temporary passwords"""
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    # Update last login time
    user.update_last_login()
    
    # Generate tokens with string identity
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            'is_admin': user.is_admin,
            'must_change_password': user.must_change_password
        }
    )
    refresh_token = create_refresh_token(identity=str(user.id))

    try:
        db.session.commit()
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'must_change_password': user.must_change_password,
                'avatar_url': user.avatar_url
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password, handling both normal and forced changes"""
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    current_password = request.json.get('current_password', None)
    new_password = request.json.get('new_password', None)

    if not current_password or not new_password:
        return jsonify({"error": "Missing current or new password"}), 400

    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Verify current password
    if not user.check_password(current_password):
        return jsonify({"error": "Current password is incorrect"}), 401

    # Set new password (this also clears temporary password fields)
    user.set_password(new_password)

    try:
        db.session.commit()
        
        # Generate new tokens with updated claims
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'is_admin': user.is_admin,
                'must_change_password': False
            }
        )
        refresh_token = create_refresh_token(identity=str(user.id))

        return jsonify({
            'message': 'Password changed successfully',
            'access_token': access_token,
            'refresh_token': refresh_token
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to change password: {str(e)}'}), 500

@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    access_token = create_access_token(
        identity=str(current_user_id),
        additional_claims={
            'is_admin': user.is_admin,
            'must_change_password': user.must_change_password
        }
    )
    return jsonify({'access_token': access_token})

@bp.route('/check-auth', methods=['GET'])
@jwt_required()
def check_auth():
    """Check if current auth token is valid and return user info"""
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'must_change_password': user.must_change_password,
            'avatar_url': user.avatar_url
        }
    })