from flask import Blueprint

# Create a Blueprint instance for API routes
bp = Blueprint('api', __name__)

# Import routes after blueprint creation to avoid circular imports
from . import routes, auth, admin

# Note: The routes are automatically registered with the blueprint
# when they are imported, thanks to the @bp.route decorators
