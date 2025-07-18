#!/usr/bin/env python3
"""
Interactive environment setup script for SQL Control Manager.
Creates .env file with user-provided configuration.
"""

import getpass
import os
import secrets
import string
from pathlib import Path


def generate_secret_key():
    """Generate a secure secret key for Flask."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(64))


def get_input(prompt, default=None, password=False):
    """Get user input with optional default value."""
    if default:
        display_prompt = f"{prompt} [{default}]: "
    else:
        display_prompt = f"{prompt}: "
    
    if password:
        value = getpass.getpass(display_prompt)
    else:
        value = input(display_prompt)
    
    return value.strip() if value.strip() else default


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
        response = input("Do you want to overwrite it? (y/N): ")
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
        print("\n📋 Next steps:")
        print("1. Run 'python config.py' to validate your configuration")
        print("2. Run 'python init_db.py' to initialize the database")
        print("3. Run 'python main.py' to start the application")
        
        if use_ldap_auth == "true":
            print("\n⚠️  LDAP Note: Please edit the .env file to configure your LDAP settings.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False


def main():
    """Main function."""
    print("=" * 60)
    print("SQL Control Manager - Interactive Environment Setup")
    print("=" * 60)
    print("\nThis script will guide you through creating a .env file")
    print("with your specific configuration settings.\n")
    
    if create_env_file():
        print("\n" + "=" * 60)
        print("Environment setup completed successfully!")
        print("=" * 60)
    else:
        print("\n❌ Environment setup failed!")


if __name__ == "__main__":
    main()