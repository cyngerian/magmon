import secrets
import string
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from ...models import User # Use relative import from utils directory

def admin_required(f):
    """Decorator to ensure the user is an admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        # Pass the admin user object to the decorated function? Optional.
        # kwargs['admin_user'] = user 
        return f(*args, **kwargs)
    return decorated_function

def generate_temp_password(length=12):
    """Generate a secure temporary password."""
    alphabet = string.ascii_letters + string.digits
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        # Ensure password contains at least one number and one letter
        if any(c.isdigit() for c in password) and any(c.isalpha() for c in password):
            return password