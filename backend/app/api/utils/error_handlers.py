from flask import jsonify
from werkzeug.exceptions import NotFound, MethodNotAllowed, BadRequest

def handle_not_found(error: NotFound):
    """Handles 404 Not Found errors."""
    return jsonify({"error": "Resource not found", "message": str(error)}), 404

def handle_method_not_allowed(error: MethodNotAllowed):
    """Handles 405 Method Not Allowed errors."""
    return jsonify({"error": "Method not allowed", "message": str(error)}), 405

def handle_bad_request(error: BadRequest):
    """Handles 400 Bad Request errors."""
    # Often BadRequest includes useful info in error.description
    message = error.description if error.description else str(error)
    return jsonify({"error": "Bad request", "message": message}), 400

# Add more specific error handlers as needed, e.g., for validation errors
# from marshmallow import ValidationError
# def handle_validation_error(error: ValidationError):
#     return jsonify({"error": "Validation failed", "messages": error.messages}), 400

def register_error_handlers(bp):
    """Registers error handlers with the blueprint."""
    bp.register_error_handler(NotFound, handle_not_found)
    bp.register_error_handler(MethodNotAllowed, handle_method_not_allowed)
    bp.register_error_handler(BadRequest, handle_bad_request)
    # bp.register_error_handler(ValidationError, handle_validation_error)