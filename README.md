# SQL Control Manager

A Flask-based application for managing laboratory experiments and device control.

## Quick Start

### 1. Generate Environment Configuration

```bash
# Generate secure environment variables
python3 setup_env.py
```

### 2. Set Up Environment Variables

Create a `.env` file with the generated template and your actual credentials:

```bash
# REQUIRED: Use generated SECRET_KEY (secure & random)
SECRET_KEY=generated_key_from_script

# REQUIRED: Your existing database credentials
DB_USER=your_actual_db_username  
DB_PASSWORD=your_actual_db_password

# REQUIRED: Your existing SSH credentials
SSH_USERNAME=your_actual_ssh_username
SSH_PASSWORD=your_actual_ssh_password

# REQUIRED: Admin user credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_admin_password
```

### 3. Install and Run

Choose one of the following installation methods:

#### Option A: Standard Installation
```bash
# Install the application
pip install .

# Validate configuration
python3 config.py

# Initialize database (if needed)
python3 setup.py

# Start the application
python3 main.py
```

#### Option B: Development Installation (Recommended for developers)
```bash
# Install in development mode with all development tools
pip install -e .[dev]

# Validate configuration
validate-config

# Initialize database (if needed)
python3 setup.py

# Start the application
python3 main.py
```

## 📋 Configuration

**Environment Variables**: See **[Environment Variables Documentation](docs/environment-variables.md)** for complete details.

**Required variables:**
- `SECRET_KEY` - Flask session encryption (generate new)
- `DB_USER`, `DB_PASSWORD` - Your existing database credentials  
- `SSH_USERNAME`, `SSH_PASSWORD` - Your existing SSH credentials

**Optional variables:**
- `FLASK_CONFIG` - Environment (development/production/testing)
- `USE_LOCAL_AUTH`, `USE_LDAP_AUTH` - Authentication methods
- `DB_HOST`, `DB_PORT`, `DB_NAME` - Database connection settings

## Production Deployment

**Important:** Never use `.env` files in production. Set environment variables directly:

```bash
export SECRET_KEY="your-production-secret"
export DB_PASSWORD="your-production-password"
export FLASK_CONFIG="production"
python3 main.py
```

## Features

- **Control table monitoring** with real-time status updates
- **Bulk status updates** for multiple setups
- **Remote reboot capability** via SSH
- **Dual authentication** (Local database + LDAP)
- **Role-based access control** (Admin/User permissions)
- **Real-time data visualization** with Dash/Plotly
- **Task management** and assignment system

## Development

### Prerequisites

- **Python 3.11+** (required)
- **MySQL/MariaDB** database
- **Git** for version control

### Development Setup

1. **Clone and set up virtual environment:**
   ```bash
   git clone <repository-url>
   cd ethopy_control
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install in development mode:**
   ```bash
   # Install with all development dependencies
   pip install -e .[dev]
   
   # Or install minimal dependencies
   pip install -e .
   ```

3. **Generate development configuration:**
   ```bash
   python3 setup_env.py
   # Edit .env with your actual database credentials
   ```

4. **Initialize database:**
   ```bash
   python3 setup.py  # Interactive setup with validation
   # Or standalone initialization
   python3 init_db.py
   ```

5. **Run development server:**
   ```bash
   python3 main.py
   ```

#### Documentation
```bash
# Build documentation
mkdocs build

# Serve documentation locally
mkdocs serve
```

### Package Management

This project uses modern Python packaging with `pyproject.toml`:

- **For users**: Use `pip install .`
- **For developers**: Use `pip install -e .[dev]`
- **For documentation**: Use `pip install -e .[docs]`
- **For testing only**: Use `pip install -e .[test]`

### Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make your changes** following the code style guidelines
4. **Submit a pull request**

#### Code Style Guidelines

- Use **Ruff** for code formatting (line length: 88)
- Follow **PEP 8** naming conventions
- Add **type hints** for function parameters and return values
- Write **docstrings** for public functions and classes
- Keep **imports** organized (standard library, third-party, local)
- Use **pytest** for testing with descriptive test names

## 📚 Documentation

- **[Environment Variables](docs/environment-variables.md)** - Configuration guide
- **[Setup Guide](docs/setup.md)** - Installation instructions
- **[User Management](docs/user_management.md)** - Authentication setup

## Package Installation

### For End Users

```bash
# Clone the repository
git clone <repository-url>
cd ethopy_control

# Install using modern packaging
pip install .
```

### For Developers

```bash
# Clone the repository
git clone https://github.com/ef-lab/ethopy_control
cd ethopy_control

# Install in development mode with all tools
pip install -e .[dev]

# Or install with specific dependency groups
pip install -e .[test]     # Testing dependencies only
pip install -e .[docs]     # Documentation dependencies only
```

### Available Console Scripts

After installation with `pip install -e .`, you can use these commands:

```bash
setup-env        # Generate secure environment configuration
validate-config  # Validate current configuration
init-db          # Initialize database and create admin user
```

**Note:** The refactored architecture provides these direct commands:
- `python3 main.py` - Start the application (primary entry point)
- `python3 setup.py` - Interactive database setup with validation
- `python3 init_db.py` - Standalone database initialization
- `python3 config.py` - Configuration validation and testing
- `python3 setup_env.py` - Environment variable template generation

## Getting Help

1. **Configuration issues:** Run `validate-config` or `python3 config.py`
2. **Missing environment variables:** Run `setup-env` or `python3 setup_env.py`
3. **Database problems:** Verify connection settings in your `.env`
4. **Development setup:** Follow the detailed development setup guide above
5. **Installation issues:** Ensure you're using `pip install .` instead of requirements.txt

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.