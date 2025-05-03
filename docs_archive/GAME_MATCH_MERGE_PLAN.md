# Game/Match Merge Plan

## Current State
- `Game` model tracks scheduled events and registrations
- `Match` model tracks results and approval workflow
- Frontend treats them as one concept already
- Routes are split between game and match endpoints

## Immediate Goals
1. Consolidate game/match logic in routes.py
2. Keep existing API endpoints working
3. Minimize changes to maintain stability

## Step 1: Consolidate Route Logic
1. Move match-related functions next to corresponding game functions:
   ```python
   # Group related endpoints
   @bp.route('/games', methods=['POST'])
   def create_game(): ...
   
   @bp.route('/games/<int:game_id>', methods=['PATCH'])
   def update_game_status(): ...
   
   # Move match submission next to game endpoints
   @bp.route('/matches', methods=['POST'])
   def submit_match(): ...
   ```

2. Add comments showing the relationship:
   ```python
   # Game Lifecycle:
   # 1. Create game (/games POST)
   # 2. Handle registrations (/games/<id>/registrations)
   # 3. Submit results (/matches POST)
   # 4. Approve results (/matches/<id>/approve)
   ```

## Step 2: Consolidate Common Logic
1. Move shared validation code into helper functions:
   ```python
   def validate_game_exists(game_id):
       game = Game.query.get_or_404(game_id)
       return game

   def validate_game_status(game, expected_status):
       if game.status != expected_status:
           return jsonify({"error": f"Game must be {expected_status}"}), 400
   ```

2. Use these helpers in both game and match routes:
   ```python
   @bp.route('/matches', methods=['POST'])
   def submit_match():
       game = validate_game_exists(data['game_id'])
       if err := validate_game_status(game, GameStatus.UPCOMING):
           return err
       # ... rest of function
   ```

## Step 3: Document Unified Concept
1. Update docstrings to reflect game lifecycle:
   ```python
   def submit_match():
       """Submit results for a game.
       
       This represents the completion phase of a game's lifecycle,
       moving it from UPCOMING to COMPLETED status (pending approval).
       """
   ```

2. Add lifecycle documentation in models.py:
   ```python
   class Game:
       """A game event.
       
       Lifecycle:
       1. Created with UPCOMING status
       2. Players register
       3. Results submitted (creates associated Match)
       4. Results approved -> COMPLETED
       (or) Game cancelled -> CANCELLED
       """
   ```

## Step 4: Clean Up Terminology
1. Update variable names to prefer "game" over "match":
   ```python
   # Before
   match_status = 'pending'
   match_details = get_match(match_id)
   
   # After
   result_status = 'pending'
   game_details = get_game_with_results(game_id)
   ```

2. Update error messages:
   ```python
   # Before
   "Match submission failed"
   
   # After
   "Game result submission failed"
   ```

## Success Criteria
1. All existing endpoints continue working
2. Code is more logically organized
3. Documentation reflects unified concept
4. No changes required to frontend
5. All tests still pass

## Future Considerations
- Consider merging Match model into Game
- Rename match-specific endpoints
- Consolidate database schema

But these can wait until the immediate organization is complete.