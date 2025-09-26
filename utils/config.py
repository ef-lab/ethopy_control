import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


class Config:
    """Base configuration class."""

    # Required environment variables
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required")

    DB_USER = os.environ.get("DB_USER")
    if not DB_USER:
        raise ValueError("DB_USER environment variable is required")

    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    if not DB_PASSWORD:
        raise ValueError("DB_PASSWORD environment variable is required")

    SSH_USERNAME = os.environ.get("SSH_USERNAME")
    if not SSH_USERNAME:
        raise ValueError("SSH_USERNAME environment variable is required")

    SSH_PASSWORD = os.environ.get("SSH_PASSWORD")
    if not SSH_PASSWORD:
        raise ValueError("SSH_PASSWORD environment variable is required")

    # Optional settings with defaults
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "lab_experiments")

    # Database URI
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Authentication
    USE_LOCAL_AUTH = os.environ.get("USE_LOCAL_AUTH", "true").lower() == "true"
    USE_LDAP_AUTH = os.environ.get("USE_LDAP_AUTH", "false").lower() == "true"

    # LDAP settings (only required if LDAP is enabled)
    if USE_LDAP_AUTH:
        LDAP_HOST = os.environ.get("LDAP_HOST")
        if not LDAP_HOST:
            raise ValueError("LDAP_HOST is required when USE_LDAP_AUTH=true")
        LDAP_BASE_DN = os.environ.get("LDAP_BASE_DN")
        if not LDAP_BASE_DN:
            raise ValueError("LDAP_BASE_DN is required when USE_LDAP_AUTH=true")
    else:
        LDAP_HOST = os.environ.get("LDAP_HOST", "ldap.example.org")
        LDAP_BASE_DN = os.environ.get("LDAP_BASE_DN", "dc=example,dc=org")

    # LDAP connection settings - with environment variable support
    LDAP_PORT = int(os.environ.get("LDAP_PORT", "389"))
    LDAP_USE_SSL = os.environ.get("LDAP_USE_SSL", "false").lower() == "true"

    # LDAP bind credentials - optional for anonymous binding
    LDAP_BIND_USER_DN = os.environ.get("LDAP_BIND_USER_DN", "").strip()
    LDAP_BIND_USER_PASSWORD = os.environ.get("LDAP_BIND_USER_PASSWORD", "").strip()

    # Convert "None" strings to empty strings (common mistake in .env files)
    if LDAP_BIND_USER_DN.lower() == "none":
        LDAP_BIND_USER_DN = ""
    if LDAP_BIND_USER_PASSWORD.lower() == "none":
        LDAP_BIND_USER_PASSWORD = ""

    # Directory structure settings
    LDAP_USER_DN = os.environ.get("LDAP_USER_DN", "ou=users")
    LDAP_GROUP_DN = os.environ.get("LDAP_GROUP_DN", "ou=groups")
    LDAP_USER_RDN_ATTR = os.environ.get("LDAP_USER_RDN_ATTR", "uid")
    LDAP_USER_LOGIN_ATTR = os.environ.get("LDAP_USER_LOGIN_ATTR", "uid")

    # Flask-LDAP3-Login specific settings
    LDAP_SEARCH_FOR_GROUPS = os.environ.get("LDAP_SEARCH_FOR_GROUPS", "false").lower() == "true"
    LDAP_GROUP_SEARCH_SCOPE = "SUBTREE"
    LDAP_USER_SEARCH_SCOPE = "SUBTREE"

    # Additional Flask-LDAP3-Login settings to handle Synology DS properly
    LDAP_GROUP_OBJECT_FILTER = "(&(objectclass=posixGroup)(memberUid=%s))"
    LDAP_USER_OBJECT_FILTER = "(&(objectclass=person)(uid=%s))"


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False

    def __init__(self):
        super().__init__()
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-key"
    DB_USER = "test"
    DB_PASSWORD = "test"
    SSH_USERNAME = "test"
    SSH_PASSWORD = "test"
    
    def __init__(self):
        # Skip parent __init__ to avoid environment variable validation for testing
        pass


# Configuration mapping
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config():
    """Get configuration based on FLASK_CONFIG environment variable."""
    config_name = os.environ.get("FLASK_CONFIG", "default")
    return config[config_name]


def main():
    """Validate configuration and display status."""
    try:
        config_obj = get_config()
        print("Configuration validation successful!")
        print(f"Configuration: {config_obj.__class__.__name__}")
        print(f"Environment: {os.environ.get('FLASK_CONFIG', 'default')}")
        print(
            f"Database: {config_obj.SQLALCHEMY_DATABASE_URI.split('@')[1] if '@' in config_obj.SQLALCHEMY_DATABASE_URI else 'Not configured'}"
        )
        print(
            f"Authentication: Local={'✅' if config_obj.USE_LOCAL_AUTH else '❌'}"
        )

        # Test database connection
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(config_obj.SQLALCHEMY_DATABASE_URI)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database connection: ✅ Success")
        except Exception as e:
            print(f"Database connection: ❌ Failed ({str(e)})")

    except Exception as e:
        print(f"❌ Configuration validation failed: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
