#!/usr/bin/env python3
"""
Database initialization module for SQL Control Manager.
Handles database table creation and admin user setup.
"""

import logging
import os
import secrets
import string

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_users_table_only(app, db):
    """Create only the Users table."""
    try:
        with app.app_context():
            # Safety check: prevent accidental production database operations during testing
            if os.environ.get("FLASK_CONFIG") == "testing":
                db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
                if "mysql" in db_uri and "memory" not in db_uri:
                    raise ValueError(
                        "Testing mode cannot use production MySQL database"
                    )

            # Import User model to ensure it's registered with SQLAlchemy
            from models import User

            # Create only the users table
            User.__table__.create(db.engine, checkfirst=True)

            # Verify User table was created
            from sqlalchemy import text

            with db.engine.connect() as conn:
                result = conn.execute(text("SHOW TABLES LIKE 'users'"))
                if not result.fetchone():
                    raise Exception("User table was not created")

            return True

    except Exception as e:
        logger.error(f"❌ Error creating User table: {e}")
        logger.error("This might be due to:")
        logger.error("  • Database connection issues")
        logger.error("  • Insufficient database permissions")
        logger.error("  • Invalid table schema")
        logger.error("  • Database server not running")
        return False


def check_required_tables(app, db):
    """Check if Control and Task tables exist, throw error if missing."""
    try:
        with app.app_context():
            from sqlalchemy import text

            missing_tables = []

            with db.engine.connect() as conn:
                # Check for ControlTable
                result = conn.execute(text("SHOW TABLES LIKE '#control'"))
                if not result.fetchone():
                    missing_tables.append("#control")

                # Check for Task table
                result = conn.execute(text("SHOW TABLES LIKE '#task'"))
                if not result.fetchone():
                    missing_tables.append("#task")

            if missing_tables:
                error_msg = (
                    f"❌ Required tables are missing: {', '.join(missing_tables)}"
                )
                logger.error(error_msg)
                logger.error(
                    "These tables are required for the application to function properly."
                )
                logger.error(
                    "Please ensure these tables exist in your database before proceeding."
                )
                raise Exception(f"Missing required tables: {', '.join(missing_tables)}")

            logger.info("✅ All required tables (#control, #task) are present!")
            return True

    except Exception as e:
        logger.error(f"❌ Error checking required tables: {e}")
        raise


def create_database_tables(app, db):
    """Create Users table and verify other required tables exist."""
    try:
        # First check if required tables exist
        check_required_tables(app, db)

        # Create only the Users table
        return create_users_table_only(app, db)

    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False


def create_admin_user(app, db):
    """Create admin user if no users exist."""
    try:
        with app.app_context():
            from models import User
            from sqlalchemy import text

            # First, verify the User table exists
            try:
                with db.engine.connect() as conn:
                    result = conn.execute(text("SHOW TABLES LIKE 'users'"))
                    if not result.fetchone():
                        logger.error(
                            "❌ User table does not exist! Run table creation first."
                        )
                        return False, None
            except Exception as e:
                logger.error(f"❌ Unable to check if User table exists: {e}")
                return False, None

            # Check if any users exist
            try:
                user_count = User.query.count()
                logger.info(f"Found {user_count} existing users in database")
            except Exception as e:
                logger.error(f"❌ Unable to query User table: {e}")
                logger.error("This suggests the User table structure may be invalid")
                return False, None

            if user_count == 0:
                admin_username = os.environ.get("ADMIN_USERNAME", "admin")
                admin_password = os.environ.get("ADMIN_PASSWORD")

                if not admin_password:
                    # Generate a random password if none provided
                    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                    admin_password = "".join(
                        secrets.choice(alphabet) for _ in range(12)
                    )
                    logger.warning(f"Generated admin password: {admin_password}")
                    logger.warning(
                        "⚠️  IMPORTANT: Save this password in a secure location!"
                    )

                admin_user = User(username=admin_username, is_admin=True)
                admin_user.set_password(admin_password)
                db.session.add(admin_user)
                db.session.commit()

                logger.info(f"Created admin user: {admin_username}")
                logger.info("✅ Admin user created successfully!")
                return True, admin_password
            else:
                logger.info("Admin user already exists, skipping creation")
                return True, None

    except Exception as e:
        logger.error(f"❌ Error creating admin user: {e}")
        logger.error("Common causes:")
        logger.error("  • User table doesn't exist")
        logger.error("  • Database connection issues")
        logger.error("  • Invalid admin credentials")
        logger.error("  • Database permissions problems")
        return False, None


def validate_database_connection(app):
    """Validate database connection."""
    try:
        with app.app_context():
            from sqlalchemy import text
            from app import db

            # Safety check: prevent accidental production database operations during testing
            if os.environ.get("FLASK_CONFIG") == "testing":
                db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
                if "mysql" in db_uri and "memory" not in db_uri:
                    raise ValueError(
                        "Testing mode cannot use production MySQL database"
                    )
                logger.info("Database connection validation: Using test database")

            # Test database connection
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection: ✅ Success")
            return True
    except Exception as e:
        logger.error(f"Database connection: ❌ Failed ({str(e)})")
        return False


def initialize_database(app=None, db=None):
    """
    Complete database initialization process.

    Args:
        app: Flask application instance (optional, will import if not provided)
        db: SQLAlchemy database instance (optional, will import if not provided)

    Returns:
        tuple: (success: bool, admin_password: str or None)
    """
    logger.info(" Starting database initialization...")

    # Import app and db if not provided
    if app is None or db is None:
        from app import app, db

    # Validate database connection
    if not validate_database_connection(app):
        logger.error("❌ Database connection failed. Check your configuration.")
        return False, None

    # Create database tables
    if not create_database_tables(app, db):
        logger.error("❌ Failed to create database tables.")
        return False, None

    # Create admin user
    success, admin_password = create_admin_user(app, db)
    if not success:
        logger.error("❌ Failed to create admin user.")
        return False, None

    logger.info("Database initialization completed successfully!")
    return True, admin_password


def main():
    """Main function for standalone execution."""
    try:
        # Import here to avoid circular imports
        from app import app, db

        logger.info("=" * 60)
        logger.info("SQL Control Manager - Database Initialization")
        logger.info("=" * 60)

        # Validate configuration first
        logger.info("Validating configuration...")
        try:
            from config import get_config

            config_obj = get_config()
            logger.info(f"Environment: {os.environ.get('FLASK_CONFIG', 'default')}")

            # Production environment protection
            if config_obj.__class__.__name__ == "ProductionConfig":
                logger.warning("⚠️  PRODUCTION ENVIRONMENT DETECTED!")
                logger.warning(
                    "⚠️  This will create/modify database tables and users in production."
                )
                logger.warning(
                    "⚠️  Please ensure you have a database backup before proceeding."
                )

                # Require explicit confirmation for production
                try:
                    response = input(
                        "\nAre you sure you want to initialize the production database? (type 'yes' to confirm): "
                    )
                    if response.lower() != "yes":
                        logger.info("Database initialization cancelled.")
                        return False
                except KeyboardInterrupt:
                    logger.info("\nDatabase initialization cancelled.")
                    return False

        except Exception as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            return False

        # Initialize database
        success, admin_password = initialize_database(app, db)

        if success:
            logger.info("=" * 60)
            logger.info("✅ Database initialization completed successfully!")
            if admin_password:
                logger.warning("⚠️  IMPORTANT: Save the admin password shown above!")
            logger.info("You can now start the application with 'python main.py'.")
            logger.info("=" * 60)
            return True
        else:
            logger.error("❌ Database initialization failed.")
            return False

    except Exception as e:
        logger.error(f"❌ Unexpected error during initialization: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
