from flask import Blueprint

# Create a Blueprint instance for API routes
bp = Blueprint('api', __name__)

# Import routes after blueprint creation to avoid circular imports
# Import specific route modules AFTER blueprint creation
# Keep importing routes for now as it still contains user/deck/profile routes
from . import routes, auth, admin
from .routes import games # Import the new games routes module
from .utils import error_handlers # Import the error handlers module

# Register common error handlers for this blueprint
error_handlers.register_error_handlers(bp)

# Note: Routes are registered via @bp decorators within each module
