import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity # Import JWTManager and decorators/functions
from flask import jsonify # Import jsonify for error responses

from config import config_by_name

# Moved User import into user_lookup_callback to avoid circular import

# Initialize extensions without app context
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
cors = CORS()
jwt = JWTManager() # Initialize JWTManager

def create_app(config_name=None):
    """Application Factory Function"""
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions with app context
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    # Allow requests from the frontend origin (adjust in production)
    # Explicitly allow the Vite dev server origin with necessary headers
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "send_wildcard": False
        }
    })
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 900  # 15 minutes
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 2592000  # 30 days
    jwt.init_app(app) # Initialize JWT with app context

    # Ensure JWT_SECRET_KEY is set (should come from config.py)
    if not app.config.get('JWT_SECRET_KEY'):
        app.logger.warning("JWT_SECRET_KEY is not set! Authentication will not work securely.")
        # You might want to raise an error here in production
        # raise ValueError("JWT_SECRET_KEY must be set in configuration")

    # Ensure upload directory exists
    try:
        # Define relative path within static folder
        upload_folder_rel = 'uploads/avatars'
        # Construct absolute path using app's static folder
        absolute_upload_folder = os.path.join(app.static_folder, upload_folder_rel)
        if not os.path.exists(absolute_upload_folder):
            os.makedirs(absolute_upload_folder)
            app.logger.info(f"Created upload directory: {absolute_upload_folder}")
    except Exception as e:
        app.logger.error(f"Failed to create upload directory: {e}")


    # Register Blueprints
    # Register Blueprints (before registering error handlers that might use the blueprint)
    from .api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Add a simple route for testing
    @app.route('/ping')
    def ping():
        return 'Pong!'

    # Shell context for flask cli
    @app.shell_context_processor
    def ctx():
        return {"app": app, "db": db}

    # Register JWT Error Handlers for Debugging
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        app.logger.error(f"JWT Invalid Token Error: {error_string}")
        return jsonify({"message": "Invalid token", "error": error_string}), 422

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        app.logger.error(f"JWT Expired Token Error. Header: {jwt_header}, Payload: {jwt_payload}")
        return jsonify({"message": "Token has expired"}), 401 # Expired is typically 401

    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        app.logger.error(f"JWT Unauthorized/Missing Token Error: {error_string}")
        return jsonify({"message": "Authorization required", "error": error_string}), 401

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        app.logger.error(f"JWT Needs Fresh Token Error. Header: {jwt_header}, Payload: {jwt_payload}")
        return jsonify({"message": "Fresh token required"}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        app.logger.error(f"JWT Revoked Token Error. Header: {jwt_header}, Payload: {jwt_payload}")
        return jsonify({"message": "Token has been revoked"}), 401

    # Register User Lookup Loader
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        from .models import User # Import User model here
        """
        Register a callback function that loads a user from your database.
        This function will be called whenever @jwt_required() is used and the
        identity is available in the JWT payload.
        """
        identity = jwt_data["sub"] # "sub" is the standard claim for subject/identity
        try:
            # Assuming identity is the user ID stored as a string
            user_id = int(identity)
            return User.query.get(user_id)
        except (ValueError, TypeError):
             # Handle cases where identity might not be a valid integer string
             app.logger.error(f"Invalid identity in JWT: {identity}")
             return None

    # JWT Error Handlers already registered above

    return app
