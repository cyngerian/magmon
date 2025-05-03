import os
from flask import request, jsonify, current_app, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from ... import db
from ...models import User
from .. import bp
from ..services.profile_service import ProfileService

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_my_profile():
    """Get the profile details for the currently logged-in user."""
    current_user_id = get_jwt_identity()
    try:
        response, status_code = ProfileService.get_profile(current_user_id)
        return jsonify(response), status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        current_app.logger.error(f"Error fetching profile for user {current_user_id}: {e}")
        return jsonify({"error": "Failed to fetch profile"}), 500

@bp.route('/profile', methods=['PATCH'])
@jwt_required()
def update_my_profile():
    """Update the profile details for the currently logged-in user."""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    try:
        response, status_code = ProfileService.update_profile(current_user_id, data)
        return jsonify({"message": "Profile updated successfully", "profile": response}), status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating profile for user {current_user_id}: {e}")
        return jsonify({"error": "Profile update failed"}), 500

@bp.route('/profile/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """Upload an avatar image for the logged-in user."""
    current_user_id = get_jwt_identity()

    if 'avatar' not in request.files:
        return jsonify({"error": "No avatar file part in the request"}), 400
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        response, status_code = ProfileService.upload_avatar(current_user_id, file)
        return jsonify({"message": "Avatar uploaded successfully", "avatar_url": response.avatar_url}), status_code
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error uploading avatar for user {current_user_id}: {e}")
        return jsonify({"error": "Avatar upload failed"}), 500