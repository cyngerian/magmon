from flask import Blueprint

# Create a Blueprint instance for API routes
bp = Blueprint('api', __name__)

# Import route modules after blueprint creation to avoid circular imports
from . import auth, admin
from .routes import games, decks, users, profile
from .utils import error_handlers # Import the error handlers module

# Register common error handlers for this blueprint
error_handlers.register_error_handlers(bp)

# Note: Routes are registered via @bp decorators within each module
