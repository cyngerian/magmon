import enum
from datetime import datetime, date, timedelta
from sqlalchemy import Enum, JSON
from . import db, bcrypt

# Enum for admin action types
class AdminActionType(enum.Enum):
    GAME_DELETE = 'GAME_DELETE'
    GAME_RESTORE = 'GAME_RESTORE'
    MATCH_UNAPPROVE = 'MATCH_UNAPPROVE'
    MATCH_UNSUBMIT = 'MATCH_UNSUBMIT'

# Admin audit log model
class AdminAuditLog(db.Model):
    __tablename__ = 'admin_audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action_type = db.Column(Enum(AdminActionType), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    previous_state = db.Column(JSON, nullable=True)
    new_state = db.Column(JSON, nullable=True)
    reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to admin user
    admin = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'))

    def __repr__(self):
        return f'<AdminAuditLog id={self.id} action={self.action_type.value} target={self.target_type}:{self.target_id}>'

# Enum for Game status
class GameStatus(enum.Enum):
    UPCOMING = 'Upcoming'
    COMPLETED = 'Completed'
    CANCELLED = 'Cancelled'

# Association table for Match players
class MatchPlayer(db.Model):
    __tablename__ = 'match_players'
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('matches.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=False)
    deck_version_id = db.Column(db.Integer, db.ForeignKey('deck_versions.id'), nullable=True)
    placement = db.Column(db.Integer, nullable=True) # Nullable until result submitted

    user = db.relationship('User', backref=db.backref('match_participations', lazy='select'))
    match = db.relationship('Match', backref=db.backref('player_details', lazy='select', cascade="all, delete-orphan"))
    deck = db.relationship('Deck', backref=db.backref('match_uses', lazy='select'))
    deck_version = db.relationship('DeckVersion', backref=db.backref('match_uses', lazy='dynamic'))

    def __repr__(self):
        return f'<MatchPlayer match_id={self.match_id} user_id={self.user_id} deck_id={self.deck_id}>'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # Admin and password reset fields
    is_admin = db.Column(db.Boolean, nullable=False, default=False, index=True)
    temp_password_hash = db.Column(db.String(128), nullable=True)
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)
    temp_password_expires_at = db.Column(db.DateTime, nullable=True)

    # Profile fields
    favorite_color = db.Column(db.String(50), nullable=True)
    retirement_plane = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True) # URL to avatar image

    # Relationships
    decks = db.relationship('Deck', backref='owner', lazy=True, cascade="all, delete-orphan")
    submitted_matches = db.relationship('Match', foreign_keys='Match.submitted_by_id', backref='submitter', lazy=True)
    # Relationship to GameRegistrations (renamed)
    game_registrations = db.relationship('GameRegistration', backref='player', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        # Clear temporary password fields when setting a new password
        self.temp_password_hash = None
        self.temp_password_expires_at = None
        self.must_change_password = False

    def check_password(self, password):
        # First check temporary password if it exists and hasn't expired
        if self.temp_password_hash and self.temp_password_expires_at:
            if datetime.utcnow() <= self.temp_password_expires_at:
                if bcrypt.check_password_hash(self.temp_password_hash, password):
                    return True
        # Then check regular password
        return bcrypt.check_password_hash(self.password_hash, password)

    def set_temp_password(self, password, expires_in_hours=24):
        self.temp_password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.temp_password_expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        self.must_change_password = True

    def clear_temp_password(self):
        self.temp_password_hash = None
        self.temp_password_expires_at = None
        self.must_change_password = False

    def update_last_login(self):
        self.last_login = datetime.utcnow()

    def __repr__(self):
        return f'<User {self.username}>'

class DeckVersion(db.Model):
    __tablename__ = 'deck_versions'
    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id', ondelete='CASCADE'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)  # Auto-incremented for each deck
    decklist_text = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)  # Notes specific to this version
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship back to the parent Deck
    deck = db.relationship('Deck', foreign_keys=[deck_id], backref=db.backref('versions', lazy='dynamic', order_by='DeckVersion.version_number.desc()'))

    # Unique constraint to ensure version numbers are unique per deck
    __table_args__ = (db.UniqueConstraint('deck_id', 'version_number', name='_deck_version_uc'),)
    
    def __repr__(self):
        return f'<DeckVersion deck_id={self.deck_id} version={self.version_number}>'

class Deck(db.Model):
    __tablename__ = 'decks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    commander = db.Column(db.String(100), nullable=False)
    colors = db.Column(db.String(5), nullable=False)
    decklist_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    current_version_id = db.Column(db.Integer, db.ForeignKey('deck_versions.id'), nullable=True)

    # Relationship to the current version
    current_version = db.relationship('DeckVersion', foreign_keys=[current_version_id], post_update=True)
    # Relationship to all versions is defined in DeckVersion model
    
    # Relationship to GameRegistrations (renamed)
    game_registrations = db.relationship('GameRegistration', backref='deck', lazy='dynamic', cascade="all, delete-orphan")
    def __repr__(self): return f'<Deck {self.name} ({self.commander}) by User {self.user_id}>'

class Game(db.Model):
    """A game event that represents a Magic: The Gathering multiplayer session.
    
    Lifecycle:
    1. Created with UPCOMING status
    2. Players register their decks (and optionally specific versions)
    3. Game is played
    4. Results submitted - creates associated Match record, status remains UPCOMING
    5. Results approved -> status changes to COMPLETED
       or
       Game cancelled -> status changes to CANCELLED
    
    The Match model represents the results and approval phase of a game's lifecycle.
    While conceptually part of the same entity, it's currently kept separate for
    data organization. Future refactoring may merge these models.
    """
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    game_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    status = db.Column(Enum(GameStatus), nullable=False, default=GameStatus.UPCOMING, index=True)
    is_pauper = db.Column(db.Boolean, nullable=False, default=False) # Added Pauper flag
    details = db.Column(db.Text, nullable=True) # Added details text field
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Soft delete and admin action tracking
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    last_admin_action = db.Column(db.String(50), nullable=True)
    last_admin_action_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship to admin who deleted
    deleted_by = db.relationship('User', foreign_keys=[deleted_by_id])

    registrations = db.relationship('GameRegistration', backref='game', lazy='dynamic', cascade="all, delete-orphan") # Renamed relationship
    matches = db.relationship('Match', backref='game', lazy='dynamic') # Renamed backref

    def __repr__(self): return f'<Game id={self.id} date={self.game_date.strftime("%Y-%m-%d")} status={self.status.value}>'

    @staticmethod
    def get_next_monday():
        today = date.today(); days_ahead = 0 - today.weekday()
        if days_ahead <= 0: days_ahead += 7
        return today + timedelta(days=days_ahead)

# Renamed GameNightRegistration to GameRegistration
class GameRegistration(db.Model):
    __tablename__ = 'game_registrations' # Renamed table
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), nullable=False) # Renamed foreign key column and target table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=False)
    deck_version_id = db.Column(db.Integer, db.ForeignKey('deck_versions.id'), nullable=True)
    registered_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to the specific version
    deck_version = db.relationship('DeckVersion', backref=db.backref('game_registrations', lazy='dynamic'))

    __table_args__ = (db.UniqueConstraint('game_id', 'user_id', name='_game_user_uc'),) # Renamed constraint

    def __repr__(self): return f'<GameRegistration user={self.user_id} deck={self.deck_id} game={self.game_id}>'

class Match(db.Model):
    """Represents the results and approval phase of a game.
    
    This model captures:
    1. Player placements and deck choices
    2. Game timing (start/end)
    3. Game notes (interactions, rules discussions, summary)
    4. Approval workflow
    
    While conceptually part of a Game's lifecycle, this data is currently
    stored separately. A Match is created when game results are submitted,
    and its status ('pending'/'approved') influences the parent Game's status.
    """
    __tablename__ = 'matches'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='SET NULL'), nullable=True, index=True) # Renamed foreign key column and target table
    player_count = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    season_number = db.Column(db.Integer, nullable=True, index=True)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes_big_interaction = db.Column(db.Text, nullable=True)
    notes_rules_discussion = db.Column(db.Text, nullable=True)
    notes_end_summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    approval_notes = db.Column(db.Text, nullable=True) # Notes added during approval/rejection

    # Define relationships for submitter and approver
    # submitter = db.relationship('User', foreign_keys=[submitted_by_id], backref='submitted_matches') # backref already defined on User
    approver = db.relationship('User', foreign_keys=[approved_by_id], backref='approved_matches')

    def __repr__(self): return f'<Match id={self.id} game_id={self.game_id} status={self.status}>'
