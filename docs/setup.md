# ethopy_control Setup Guide

A Control Manager for lab experiments with real-time monitoring.

### Prerequisites

- **Python 3.11 or higher** (required)
- **MySQL Database** (primary database)
- **pip** or **uv** package manager (uv recommended for faster installs)
- **Git** for version control

### Quick Start

1. **Clone the repository:**
```bash
git clone github.com/ef-lab/ethopy_control
cd ethopy_control
```

2. **Create and activate virtual environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies:**
```bash
# Using pip (standard installation)
pip install .
```

4. **Complete setup and database initialization:**
```bash
# Single command setup - handles environment and database setup
python3 app_setup.py
```

This interactive script will:
- **Create .env file** if it doesn't exist (prompts for database, SSH, and admin credentials)
- **Generate secure SECRET_KEY** automatically
- **Validate your configuration** and test database connectivity
- **Inspect your existing database structure**
- **Create the Users table** if it doesn't exist
- **Verify that required tables** (#control, #task) exist
- **Create an admin user** if no users exist
- **Provide detailed diagnostics** if any issues occur

**What you'll be prompted for:**
- Database credentials (host, username, password)
- SSH configuration (optional, for remote reboot functionality)
- Authentication preferences (local vs LDAP)
- Admin user configuration

**⚠️ Security Notes:**
- Uses auto-generated secure SECRET_KEY
- Never commit .env files to version control
- Store credentials securely (password manager recommended)

5. **Run the development server:**
```bash
python3 main.py
```

The application will be available at `http://localhost:5000`.

## Project Structure
```
ethopy_control/
├── main.py                   # Primary application entry point
├── app.py                    # Flask application definition and routes
├── app_setup.py             # Interactive setup with validation
├── models.py                # Database models (User, ControlTable, Task)
├── pyproject.toml          # Python project configuration and dependencies
│
├── utils/                   # Utility modules
│   ├── __init__.py         # Package initialization
│   ├── init_db.py          # Centralized database initialization
│   ├── config.py           # Configuration management and validation
│   └── setup_env.py        # Environment variable template generation
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html          # Base template with navigation
│   ├── index.html         # Main control table interface
│   ├── login.html         # Authentication page
│   ├── tasks.html         # Task management interface
│   └── activity_monitor.html # Activity monitoring dashboard
│
├── static/                # Static web assets
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript files
│   │   └── table.js      # DataTables implementation
│   └── favicon.ico       # Site favicon
│
├── real_time_plot/        # Real-time data visualization
│   ├── get_activity.py    # Database activity queries
│   └── real_time_events.py # Dash-based real-time plotting
│
├── tests/                 # Test suite
│   ├── conftest.py       # pytest configuration
│   ├── test_api.py       # API endpoint tests
│   └── test_models.py    # Database model tests
│
└── docs/                 # Documentation
    ├── setup.md          # This setup guide
    └── mkdocs.yml        # Documentation configuration
```

## Core Features

### 1. Control Table Management
- **Real-time status monitoring** of lab setups
- **Bulk operations** for updating multiple setups
- **User assignment** and access control
- **Remote reboot capability** via SSH

### 2. Task Management
- **CRUD operations** for experimental tasks
- **Task assignment** to specific setups
- **Task history** and tracking

### 3. Real-time Data Visualization
- **Live event plotting** using Dash and Plotly
- **Lick port and proximity sensor** data visualization
- **Configurable time windows** (30s, 60s, 5min, all)
- **Multi-setup monitoring**

### 4. User Management & Authentication
- **Local authentication**: Database-stored user accounts
- **Role-based access**: Admin and regular users
- **Session management** with Flask sessions

## Authentication Configuration

### Local Authentication

**Admin User Creation:**
- Created automatically during database setup (only if no users exist)
- Username: Set via `ADMIN_USERNAME` environment variable (default: `admin`)
- Password: Set via `ADMIN_PASSWORD` environment variable (auto-generated if not provided)
- The setup script will skip admin creation if users already exist in the database

⚠️ **Important**: Secure admin passwords are automatically generated if not provided. The setup script will display the generated password - save it securely!

**Creating Additional Users:**
1. Login as admin
2. Navigate to "Admin" → "Users"
3. Click "Add User"
4. Set username, password, and admin privileges

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v
```

### Real-time Plotting Development

The real-time plotting feature runs as a separate Dash application:

```bash
cd real_time_plot
python real_time_events.py
```

Access the real-time plots at `http://localhost:8050`.

## Production Deployment

### Using Gunicorn

```bash
# Install gunicorn (included in pyproject.toml)
pip install .

# Run with multiple workers
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Docker Deployment (Optional)

<details>
<summary>Click to expand Docker deployment instructions</summary>

#### Multi-stage Production Dockerfile

Create a `Dockerfile`:
```dockerfile
# Multi-stage build for optimal image size
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements first to leverage Docker layer caching
COPY pyproject.toml ./
RUN pip install --no-cache-dir --user .

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Add local bin to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Run the application
CMD ["python3", "main.py"]
```

#### Development Dockerfile

For development purposes, create a `Dockerfile.dev`:
```dockerfile
FROM python:3.11-slim

# Install development dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    mysql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .[dev]

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Run in development mode
CMD ["python3", "main.py"]
```

#### Docker Compose Setup

Create a `docker-compose.yml` for complete development environment:
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "5000:5000"
    environment:
      - FLASK_CONFIG=development
      - DB_HOST=mysql
      - DB_PORT=3306
      - DB_NAME=lab_experiments
      - DB_USER=sqlcontrol
      - DB_PASSWORD=password
      - SECRET_KEY=dev-secret-key-change-in-production
      - SSH_USERNAME=admin
      - SSH_PASSWORD=admin
      - ADMIN_USERNAME=admin
      - ADMIN_PASSWORD=admin
      - USE_LOCAL_AUTH=true
    depends_on:
      - mysql
    volumes:
      - .:/app
      - /app/.venv  # Exclude venv from volume mount
    command: python3 main.py

  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=rootpassword
      - MYSQL_DATABASE=lab_experiments
      - MYSQL_USER=sqlcontrol
      - MYSQL_PASSWORD=password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    command: --default-authentication-plugin=mysql_native_password

volumes:
  mysql_data:
```

#### Building and Running

```bash
# Build production image
docker build -t sql-control-manager .

# Run production container
docker run -d \
  --name sql-control-manager \
  -p 5000:5000 \
  -e SECRET_KEY="your-production-secret" \
  -e DB_HOST="your-db-host" \
  -e DB_USER="your-db-user" \
  -e DB_PASSWORD="your-db-password" \
  -e SSH_USERNAME="your-ssh-user" \
  -e SSH_PASSWORD="your-ssh-password" \
  -e ADMIN_USERNAME="admin" \
  -e ADMIN_PASSWORD="your-admin-password" \
  -e FLASK_CONFIG="production" \
  sql-control-manager

# Run with Docker Compose (development)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

#### Environment Variables for Docker

Create a `.env.docker` file for container environment variables:
```bash
# Database Configuration
DB_HOST=mysql
DB_PORT=3306
DB_NAME=lab_experiments
DB_USER=sqlcontrol
DB_PASSWORD=secure_password

# Application Configuration
SECRET_KEY=your-super-secret-key-for-production
FLASK_CONFIG=production
USE_LOCAL_AUTH=true

# SSH Configuration
SSH_USERNAME=your-ssh-username
SSH_PASSWORD=your-ssh-password

# Admin Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-admin-password
```

**Security Notes for Docker:**
- Never use default passwords in production
- Use Docker secrets for sensitive data
- Run containers as non-root user
- Regularly update base images
- Use multi-stage builds to reduce image size
- Implement proper logging and monitoring

</details>

### Security Considerations

- **Change default passwords** immediately
- **Use strong SECRET_KEY** in production
- **Enable HTTPS** with reverse proxy (nginx/Apache)
- **Regularly update dependencies**
- **Monitor logs** for security events

## Troubleshooting

### Common Issues

1. **Database Connection Errors:**
      - Verify MySQL server is running
      - Check credentials in `.env` file
      - Ensure database exists and user has proper permissions
      - Run `python3 app_setup.py` for detailed diagnostics

2. **Missing Required Tables:**
      - Ensure `#control` and `#task` tables exist in your database
      - These tables are required for the application to function
      - The setup script will check for their existence and provide guidance

3. **Admin User Creation Issues:**
      - Verify User table was created successfully
      - Check database permissions for user creation
      - Review the detailed error messages from `python3 app_setup.py`

4. **Authentication Issues:**
      - Verify admin credentials in database
      - Ensure session management is working correctly
      - Check that users table has proper structure

5. **Permission Errors:**
      - Ensure proper file permissions
      - Check SSH key access for remote reboot

6. **Real-time Plot Issues:**
      - Verify Dash dependencies installed
      - Check database connectivity
      - Ensure proper animal_id and session data

### Getting Help

- **Check logs:** Application logs provide detailed error information
- **Run diagnostics:** Use `python3 app_setup.py` to validate configuration, test database connection, and inspect database structure
- **Database inspection:** The setup script provides detailed database diagnostics including table existence and row counts
- **Verify dependencies:** `pip list` or `uv pip list`

## Additional Resources

- **Flask Documentation:** https://flask.palletsprojects.com/
- **SQLAlchemy Documentation:** https://docs.sqlalchemy.org/
- **Dash Documentation:** https://dash.plotly.com/
- **Flask-Login Documentation:** https://flask-login.readthedocs.io/
