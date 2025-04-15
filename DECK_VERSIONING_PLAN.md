# Deck Versioning Implementation Plan

## Overview
This document outlines the implementation plan for adding deck versioning to the Magic the Gathering Commander game tracker app. This feature will allow users to save snapshots of their decks while maintaining a working version.

## Phase 1: Database Schema Changes

### Step 1: Create the DeckVersion Model
Add the following model to `backend/app/models.py`:

```python
class DeckVersion(db.Model):
    __tablename__ = 'deck_versions'
    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id', ondelete='CASCADE'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)  # Auto-incremented for each deck
    decklist_text = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)  # Notes specific to this version
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationship back to the parent deck
    deck = db.relationship('Deck', backref=db.backref('versions', lazy='dynamic', cascade="all, delete-orphan"))
    
    # Unique constraint to ensure version numbers are unique per deck
    __table_args__ = (db.UniqueConstraint('deck_id', 'version_number', name='_deck_version_uc'),)
    
    def __repr__(self):
        return f'<DeckVersion deck_id={self.deck_id} version={self.version_number}>'
```

### Step 2: Modify Existing Models

#### Update the Deck Model
```python
class Deck(db.Model):
    # Existing fields...
    current_version_id = db.Column(db.Integer, db.ForeignKey('deck_versions.id'), nullable=True)
    current_version = db.relationship('DeckVersion', foreign_keys=[current_version_id], post_update=True)
```

#### Update the GameRegistration Model
```python
class GameRegistration(db.Model):
    # Existing fields...
    deck_version_id = db.Column(db.Integer, db.ForeignKey('deck_versions.id'), nullable=True)
    # Relationship to the specific version
    deck_version = db.relationship('DeckVersion', backref=db.backref('game_registrations', lazy='dynamic'))
```

#### Update the MatchPlayer Model
```python
class MatchPlayer(db.Model):
    # Existing fields...
    deck_version_id = db.Column(db.Integer, db.ForeignKey('deck_versions.id'), nullable=True)
    # Relationship to the specific version
    deck_version = db.relationship('DeckVersion', backref=db.backref('match_uses', lazy='dynamic'))
```

### Step 3: Create Database Migration
Generate a new migration file using Flask-Migrate:
```bash
flask db migrate -m "Add deck versioning"
```

Modify the migration file to:
1. Create the deck_versions table
2. Add the current_version_id column to the decks table
3. Add the deck_version_id column to the game_registrations and match_players tables
4. Create initial versions for all existing decks
5. Update existing game registrations and match players to point to these initial versions

## Phase 2: Backend API Changes

### Step 4: Update Deck Creation/Editing Endpoints

#### Modify the Create Deck Endpoint
Update the `/decks` POST endpoint to create an initial version when a new deck is created:
```python
@api_bp.route('/decks', methods=['POST'])
@jwt_required()
def create_deck():
    # Existing code...
    
    # Create the deck
    new_deck = Deck(name=data['name'], commander=data['commander'], colors=data['colors'], user_id=current_user_id)
    db.session.add(new_deck)
    db.session.flush()  # Get the deck ID
    
    # Create the initial version
    initial_version = DeckVersion(
        deck_id=new_deck.id,
        version_number=1,
        decklist_text=data.get('decklist_text', ''),
        notes="Initial version"
    )
    db.session.add(initial_version)
    db.session.flush()  # Get the version ID
    
    # Set the current version
    new_deck.current_version_id = initial_version.id
    db.session.add(new_deck)
    db.session.commit()
    
    # Return response...
```

#### Create a New Version Endpoint
Add a new endpoint to create a new version of a deck:
```python
@api_bp.route('/decks/<int:deck_id>/versions', methods=['POST'])
@jwt_required()
def create_deck_version(deck_id):
    current_user_id = get_jwt_identity()
    
    # Get the deck
    deck = Deck.query.get_or_404(deck_id)
    
    # Check ownership
    if deck.user_id != int(current_user_id):
        return jsonify({"error": "You don't own this deck"}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    # Get the latest version number
    latest_version = DeckVersion.query.filter_by(deck_id=deck_id).order_by(DeckVersion.version_number.desc()).first()
    new_version_number = 1 if not latest_version else latest_version.version_number + 1
    
    # Create the new version
    new_version = DeckVersion(
        deck_id=deck_id,
        version_number=new_version_number,
        decklist_text=data.get('decklist_text', ''),
        notes=data.get('notes', '')
    )
    db.session.add(new_version)
    db.session.flush()  # Get the version ID
    
    # Update the current version
    deck.current_version_id = new_version.id
    db.session.add(deck)
    db.session.commit()
    
    return jsonify({
        "message": "New version created successfully",
        "version": {
            "id": new_version.id,
            "version_number": new_version.version_number,
            "created_at": new_version.created_at.isoformat(),
            "notes": new_version.notes
        }
    }), 201
```

### Step 5: Add Version Retrieval Endpoints

#### Get All Versions of a Deck
```python
@api_bp.route('/decks/<int:deck_id>/versions', methods=['GET'])
@jwt_required()
def get_deck_versions(deck_id):
    # Get the deck
    deck = Deck.query.get_or_404(deck_id)
    
    # Get all versions
    versions = DeckVersion.query.filter_by(deck_id=deck_id).order_by(DeckVersion.version_number.desc()).all()
    
    versions_list = [{
        "id": version.id,
        "version_number": version.version_number,
        "created_at": version.created_at.isoformat(),
        "notes": version.notes,
        "is_current": version.id == deck.current_version_id
    } for version in versions]
    
    return jsonify(versions_list), 200
```

#### Get a Specific Version
```python
@api_bp.route('/decks/<int:deck_id>/versions/<int:version_id>', methods=['GET'])
@jwt_required()
def get_deck_version(deck_id, version_id):
    # Get the version
    version = DeckVersion.query.filter_by(deck_id=deck_id, id=version_id).first_or_404()
    
    version_data = {
        "id": version.id,
        "version_number": version.version_number,
        "created_at": version.created_at.isoformat(),
        "notes": version.notes,
        "decklist_text": version.decklist_text,
        "is_current": version.id == version.deck.current_version_id
    }
    
    return jsonify(version_data), 200
```

### Step 6: Update Game Registration Endpoint
Modify the game registration endpoint to accept an optional deck_version_id:
```python
@api_bp.route('/games/<int:game_id>/registrations', methods=['POST'])
@jwt_required()
def register_for_game(game_id):
    # Existing code...
    
    data = request.get_json()
    deck_id = data.get('deck_id')
    deck_version_id = data.get('deck_version_id')
    
    # If no version ID is provided, use the current version
    if not deck_version_id:
        deck = Deck.query.get_or_404(deck_id)
        deck_version_id = deck.current_version_id
    
    # Create the registration
    new_registration = GameRegistration(
        game_id=game_id,
        user_id=current_user_id,
        deck_id=deck_id,
        deck_version_id=deck_version_id
    )
    
    # Rest of the code...
```

### Step 7: Update Match Submission Logic
Ensure the correct deck version is recorded when submitting match results:
```python
@api_bp.route('/matches', methods=['POST'])
@jwt_required()
def submit_match():
    # Existing code...
    
    # When creating MatchPlayer entries, include the deck_version_id from the registration
    for user_id, placement in placements_dict.items():
        registration = GameRegistration.query.filter_by(game_id=game.id, user_id=user_id).first()
        deck_id = registration.deck_id
        deck_version_id = registration.deck_version_id
        
        match_player_entry = MatchPlayer(
            match_id=new_match.id,
            user_id=user_id,
            deck_id=deck_id,
            deck_version_id=deck_version_id,
            placement=placement
        )
        db.session.add(match_player_entry)
    
    # Rest of the code...
```

## Phase 3: Frontend Implementation

### Step 8: Update Deck Management Page
Modify `frontend/src/pages/DeckManagementPage.tsx` to:
1. Add a "Save Version" button to each deck in the list
2. Create a modal for entering version notes and saving a new version
3. Show version history in the deck details view

### Step 9: Update Deck Detail Page
Modify `frontend/src/pages/DeckDetailPage.tsx` to:
1. Display version history
2. Allow switching between versions
3. Show creation dates and notes for each version

### Step 10: Update Game Registration UI
Modify `frontend/src/pages/GamesPage.tsx` to:
1. Add version selection when registering a deck
2. Show version information in the selection dropdown
3. Default to the latest version

### Step 11: Update Game Details View
Modify the game details view to show which version of each deck was used.

## Phase 4: Testing and Deployment

### Step 12: Write Tests
1. Test database migrations
2. Test API endpoints for version management
3. Test UI components for version selection

### Step 13: Manual Testing
1. Test creating a new deck and its initial version
2. Test creating new versions of a deck
3. Test registering a specific version for a game
4. Test viewing version history
5. Test that match results correctly record the deck version used

### Step 14: Deployment
1. Deploy database migrations
2. Deploy updated backend and frontend code
