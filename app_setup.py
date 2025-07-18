#!/usr/bin/env python3
"""
Combined configuration validation and database setup for SQL Control Manager.
This script validates configuration, tests database connectivity, and optionally initializes the database.
"""

import getpass
import os
import secrets
import string
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80)


def get_input(prompt, default=None, password=False):
    """Get user input with a default value option."""
    default_display = f" [{default}]" if default else ""
    prompt = f"{prompt}{default_display}: "

    if password:
        value = getpass.getpass(prompt)
    else:
        value = input(prompt)

    return value.strip() if value.strip() else default


def generate_secret_key():
    """Generate a secure secret key for Flask."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(64))


def get_database_config():
    """Interactively get database configuration from user."""
    print("\n📋 Database Configuration")
    print("Please provide your database connection details:")
    
    db_host = get_input("Database host", "127.0.0.1")
    db_port = get_input("Database port", "3306")
    db_name = get_input("Database name", "lab_experiments")
    db_user = get_input("Database username")
    
    while not db_user:
        print("❌ Database username is required!")
        db_user = get_input("Database username")
    
    db_password = get_input("Database password", password=True)
    
    while not db_password:
        print("❌ Database password is required!")
        db_password = get_input("Database password", password=True)
    
    return db_host, db_port, db_name, db_user, db_password


def get_ssh_config():
    """Interactively get SSH configuration from user."""
    print("\n🔐 SSH Configuration (for remote reboot functionality)")
    use_ssh = get_input("Do you need SSH remote reboot functionality? (y/N)", "n")
    
    if use_ssh.lower() == 'y':
        ssh_user = get_input("SSH username")
        ssh_password = get_input("SSH password", password=True)
        
        while not ssh_user:
            print("❌ SSH username is required!")
            ssh_user = get_input("SSH username")
        
        while not ssh_password:
            print("❌ SSH password is required!")
            ssh_password = get_input("SSH password", password=True)
        
        return ssh_user, ssh_password
    else:
        return "your_ssh_username", "your_ssh_password"


def get_auth_config():
    """Get authentication configuration."""
    print("\n🔒 Authentication Configuration")
    use_ldap = get_input("Do you want to use LDAP authentication? (y/N)", "n")
    
    if use_ldap.lower() == 'y':
        print("LDAP configuration will be set to defaults. Edit .env file for detailed LDAP setup.")
        return "false", "true"
    else:
        return "true", "false"


def get_admin_config():
    """Get admin user configuration."""
    print("\n👤 Admin User Configuration")
    admin_username = get_input("Admin username", "admin")
    admin_password = get_input("Admin password (leave empty for auto-generation)", password=True)
    
    return admin_username, admin_password


def create_env_file():
    """Create .env file with interactive input."""
    env_path = Path(".env")
    
    if env_path.exists():
        print("❌ .env file already exists!")
        response = get_input("Do you want to overwrite it? (y/N)", "n")
        if response.lower() != 'y':
            print("Environment setup cancelled.")
            return False
    
    # Get configuration interactively
    db_host, db_port, db_name, db_user, db_password = get_database_config()
    ssh_user, ssh_password = get_ssh_config()
    use_local_auth, use_ldap_auth = get_auth_config()
    admin_username, admin_password = get_admin_config()
    
    # Generate secure secret key
    secret_key = generate_secret_key()
    
    env_content = f"""# SQL Control Manager Environment Variables
# Generated interactively for user: {os.environ.get('USER', 'system')}

# Flask Configuration
SECRET_KEY={secret_key}
FLASK_CONFIG=development

# Database Configuration
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}

# SSH Configuration (for remote reboot functionality)
SSH_USERNAME={ssh_user}
SSH_PASSWORD={ssh_password}

# Authentication Configuration
USE_LOCAL_AUTH={use_local_auth}
USE_LDAP_AUTH={use_ldap_auth}

# LDAP Configuration (only needed if USE_LDAP_AUTH=true)
LDAP_HOST=ldap.example.org
LDAP_BASE_DN=dc=example,dc=org
LDAP_BIND_USER_DN=cn=admin,dc=example,dc=org
LDAP_BIND_USER_PASSWORD=your_ldap_password
LDAP_USER_DN=ou=users
LDAP_GROUP_DN=ou=groups

# Admin User Configuration
ADMIN_USERNAME={admin_username}
ADMIN_PASSWORD={admin_password}
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print("\n✅ .env file created successfully!")
        
        if use_ldap_auth == "true":
            print("\n⚠️  LDAP Note: Please edit the .env file to configure your LDAP settings.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False


def check_env_file():
    """Check if .env file exists and offer to create it interactively."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found!")
        print("\nWould you like to create the .env file interactively now?")
        print("This will guide you through setting up database, SSH, and admin credentials.")
        
        create_now = get_input("Create .env file now? (Y/n)", "y")
        
        if create_now and create_now.lower() in ['y', 'yes']:
            print("\n🔧 Starting interactive environment setup...")
            return create_env_file()
        else:
            print("\nTo create environment configuration manually:")
            print("1. Run 'python utils/setup_env.py' for interactive setup")
            print("2. Or manually create .env file with required variables")
            print(
                "\nRequired variables: SECRET_KEY, DB_USER, DB_PASSWORD, SSH_USERNAME, SSH_PASSWORD"
            )
            return False
    return True


def validate_configuration():
    """Validate configuration and test database connection."""
    print("\n🔧 Validating configuration...")

    try:
        from utils.config import get_config

        config_obj = get_config()
        print("✅ Configuration loaded successfully!")
        print(f"Environment: {os.environ.get('FLASK_CONFIG', 'default')}")

        # Display configuration summary
        print(
            f"Database: {config_obj.DB_HOST}:{config_obj.DB_PORT}/{config_obj.DB_NAME}"
        )
        print(f"Database User: {config_obj.DB_USER}")

        return config_obj

    except ValueError as e:
        print(f"❌ Configuration validation failed: {e}")
        print(
            "⚠️  Please check your .env file and ensure all required variables are set."
        )
        return None
    except Exception as e:
        print(f"❌ Unexpected configuration error: {e}")
        return None


def test_database_connection(config_obj):
    """Test database connection."""
    print("\nTesting database connection...")

    try:
        from sqlalchemy import create_engine, text

        # Create engine with connection timeout
        engine = create_engine(
            config_obj.SQLALCHEMY_DATABASE_URI, connect_args={"connect_timeout": 10}
        )

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()

        if test_value == 1:
            print("✅ Database connection successful!")
            return True
        else:
            print("❌ Database connection test failed!")
            return False

    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("\nCommon solutions:")
        print("• Check if database server is running")
        print("• Verify database credentials in .env file")
        print("• Ensure database exists and user has access")
        print("• Check network connectivity to database host")
        return False


def inspect_database(app, db):
    """Inspect database to show existing tables and structure."""
    print("\nDatabase Inspection:")

    try:
        with app.app_context():
            from sqlalchemy import text

            with db.engine.connect() as conn:
                # List all tables
                result = conn.execute(text("SHOW TABLES"))
                tables = result.fetchall()

                if tables:
                    print(f"Found {len(tables)} tables:")
                    for table in tables:
                        table_name = table[0]
                        # print(f"  • {table_name}")

                        # Check if it's one of our expected tables
                        if table_name in ["users", "#control", "#task"]:
                            # Get row count
                            count_result = conn.execute(
                                text(f"SELECT COUNT(*) FROM `{table_name}`")
                            )
                            row_count = count_result.scalar()
                            print(f"table: {table_name}  ({row_count} rows)")
                else:
                    print("❌ No tables found in database")

    except Exception as e:
        print(f"❌ Unable to inspect database: {e}")
        print("🔍 This might indicate database connectivity or permission issues")


def run_database_initialization():
    """Run database initialization if user confirms."""
    print("\n🗄️  Database Initialization")
    print("This will:")
    print("• Check if required tables (#control, #task) exist")
    print("• Create the Users table if it doesn't exist")
    print("• Throw an error if required tables are missing")

    initialize_db = get_input(
        "Would you like to initialize the database now? (yes/no)", "yes"
    )

    if initialize_db.lower() != "yes":
        print("Database initialization skipped.")
        return True

    try:
        print("\nInitializing database...")
        from utils.init_db import create_database_tables
        from app import app, db

        # Create Users table and check required tables exist
        if not create_database_tables(app, db):
            print("❌ Database initialization failed!")
            print("\n🔍 Let's inspect the database to understand the issue:")
            inspect_database(app, db)
            print("\n🔍 Common issues:")
            print("• Missing required tables (#control, #task) - these must exist")
            print("• Database permissions problems")
            print("• Database connection issues")
            return False

        # Verify tables are present by inspecting the database
        inspect_database(app, db)

        # Check if users already exist before showing admin creation section
        from models import User
        
        try:
            with app.app_context():
                from sqlalchemy import text

                # Check if users table exists
                with db.engine.connect() as conn:
                    result = conn.execute(text("SHOW TABLES LIKE 'users'"))
                    if not result.fetchone():
                        print("❌ User table does not exist!")
                        print("🔍 This indicates table creation failed. Check the logs above.")
                        return False

                # Now check existing users
                existing_users = User.query.count()
                if existing_users > 0:
                    print(f"\nℹ️  Database already contains {existing_users} user(s)")
                    
                    # Show existing users (usernames only)
                    users = User.query.all()
                    print("Existing users:")
                    for user in users:
                        admin_status = " (admin)" if user.is_admin else ""
                        print(f"  • {user.username}{admin_status}")

                    print("\n✅ Database already has users - no admin user creation needed!")
                    return True

        except Exception as e:
            print(f"❌ Error checking existing users: {e}")
            print("🔍 This might indicate User table creation failed.")
            print("\nLet's inspect the database state:")
            inspect_database(app, db)
            return False

        # Only show admin creation section if no users exist
        print("\n👤 Admin User Creation")
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "")

        if admin_username and admin_password:
            print("Found admin user configuration:")
            print(f"  Username: {admin_username}")
            print(f"  Password: {'*' * len(admin_password)} (from .env)")

            create_admin = get_input(
                "Would you like to create the admin user with these credentials? (yes/no)",
                "yes",
            )
        else:
            print("Admin user credentials not fully configured in .env file.")
            if not admin_username:
                print("  Missing: ADMIN_USERNAME")
            if not admin_password:
                print("  Missing: ADMIN_PASSWORD")

            create_admin = get_input(
                "Would you like to create an admin user anyway? (yes/no)", "yes"
            )

        if create_admin.lower() == "yes":
            print("\nCreating admin user...")
            from utils.init_db import create_admin_user

            success, generated_password = create_admin_user(app, db)

            if success:
                print("✅ Admin user created successfully!")
                if generated_password:
                    print(f"🔑 Generated admin password: {generated_password}")
                    print("⚠️  IMPORTANT: Save this password in a secure location!")
                else:
                    print(f"🔑 Admin user: {admin_username}")
                    print("🔑 Password: (using password from .env file)")
            else:
                print("❌ Failed to create admin user!")
                print("🔍 Possible causes:")
                print("• Database connection issues")
                print("• User table not properly created")
                print("• Invalid admin credentials")
                print("• Database permissions problems")
                print(
                    "\nTry running 'python init_db.py' directly for more detailed error information."
                )
                return False
        else:
            print("Admin user creation skipped.")
            print(
                "⚠️  Note: You'll need to create a user manually to access the application."
            )

        print("\n📋 Next steps:")
        print("• Run 'python main.py' to start the application")
        print("• Access the application in your web browser")
        if create_admin.lower() == "yes":
            print("• Log in with the admin credentials shown above")

        return True

    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        return False


def main():
    """Main setup function."""
    print_header("SQL Control Manager - Configuration Validation & Database Setup")
    print("""
This script will:
1. Validate your configuration settings
2. Test database connectivity
3. Optionally initialize the database and create admin user
    """)

    # Check for .env file
    if not check_env_file():
        return False

    # Validate configuration
    config_obj = validate_configuration()
    if not config_obj:
        return False

    # Test database connection
    if not test_database_connection(config_obj):
        return False

    # Run database initialization
    if not run_database_initialization():
        return False

    print_header("Setup Completed Successfully!")
    print("Your SQL Control Manager is ready to use!")

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Please address the issues above and try again.")
        exit(1)
    else:
        print("\n✅ Setup completed successfully!")
        exit(0)
