"""
Validation helpers for game lifecycle operations.
"""
from typing import Optional, Tuple, Dict
from ...models import Game, Match, GameRegistration, GameStatus

def validate_game_exists(game_id: int) -> Game:
    """Get a game by ID or raise 404.
    
    This is a common validation used across game and match endpoints
    since matches are part of a game's lifecycle.
    """
    game = Game.query.get_or_404(game_id)
    return game

def validate_game_status(game: Game, expected_status: GameStatus) -> Optional[Tuple[Dict, int]]:
    """Validate game has expected status or return error response.
    
    Returns None if valid, otherwise returns (error_response, status_code).
    Used by both game and match endpoints to ensure proper lifecycle state.
    """
    if game.status != expected_status:
        return {"error": f"Game must be {expected_status.value}"}, 400
    return None

def validate_game_registrations(game: Game, required_count: int = 2) -> Optional[Tuple[Dict, int]]:
    """Validate game has minimum required registrations.
    
    Returns None if valid, otherwise returns (error_response, status_code).
    Used by match submission to ensure enough players are registered.
    """
    reg_count = GameRegistration.query.filter_by(game_id=game.id).count()
    if reg_count < required_count:
        return {"error": f"Game must have at least {required_count} registered players"}, 400
    return None

def validate_match_status(match: Match, expected_status: str = 'pending') -> Optional[Tuple[Dict, int]]:
    """Validate match has expected status or return error response.
    
    Returns None if valid, otherwise returns (error_response, status_code).
    Used by match approval/rejection endpoints.
    """
    if match.status != expected_status:
        return {"error": f"Match must be {expected_status}"}, 400
    return None