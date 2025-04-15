import os
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_default_secret_key_for_dev') # For Flask session, CSRF etc.
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'a_default_jwt_secret_key_for_dev') # For Flask-JWT-Extended
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Removed explicit JWT header configs, relying on defaults
    # Add other default configurations here

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # Use environment variable for database URI, fallback to a default SQLite for simplicity if not set
    # IMPORTANT: Replace the fallback with your actual PostgreSQL connection string in .env
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost:5432/magmon_dev' # Example, replace in .env!

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'test.db') # Use SQLite for tests unless specified
    WTF_CSRF_ENABLED = False # Disable CSRF forms protection in tests

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Ensure DATABASE_URL is set in the production environment
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # Add other production-specific settings like logging, security headers etc.

# Dictionary to access config classes by name
config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
    default=DevelopmentConfig
)

# Function to get the secret key
def get_secret_key():
    key = os.environ.get('SECRET_KEY')
    if not key:
        # Generate a default key for development if not set
        # In production, this MUST be set via environment variable
        print("WARNING: SECRET_KEY not set in environment. Using default for development.")
        key = 'fallback-secret-key-change-me'
        # You could also generate a random key here if needed:
        # import secrets
        # key = secrets.token_hex(16)
    return key

secret_key = get_secret_key()
