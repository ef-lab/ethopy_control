# Project Structure

This document provides an overview of the SQL Control Manager project structure to help you understand how the codebase is organized.

## Directory Overview


```
ethopy_control/
├── app.py                     # Main Flask application
├── main.py                   # Application entry point
├── utils/                    # Utility modules
│   ├── __init__.py          # Package initialization
│   ├── init_db.py           # Database initialization
│   ├── config.py            # Configuration management
│   └── setup_env.py         # Environment setup script
├── models.py                 # Database models (User, ControlTable, Task)
├── app_setup.py              # Database initialization script
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Modern Python project configuration
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

## Key Files

### Core Application

- **app.py**: Main Flask application containing routes, API endpoints, and application logic
- **utils/config.py**: Configuration handling and environment variable loading
- **models.py**: SQLAlchemy database models (ORM)
- **main.py**: Simple entry point script that imports app.py
- **app_setup.py**: Interactive configuration setup script for first-time users

### Configuration Files

- **requirements.txt**: Python package dependencies
- **.env_example**: Example environment variable file (create .env based on this)
- **pyproject.toml**: Project metadata and tool configurations
- **mkdocs.yml**: Documentation generation configuration

## Directories

### Templates

The `templates/` directory contains Jinja2 HTML templates:

- **base.html**: Base template with common layout elements
- **index.html**: Home page template (control table view)
- **login.html**: Login page
- **tasks.html**: Task management view
- **activity_monitor.html**: Real-time activity monitor view
- **admin/**: Admin-specific templates

### Static Assets

The `static/` directory contains:

- **css/**: Stylesheets including custom CSS and Bootstrap
- **js/**: JavaScript files 
- **img/**: Images and icons
- **lib/**: Third-party libraries

### Real-time Plotting

The `real_time_plot/` directory contains:

- **get_activity.py**: Database query functions for activity data
- **real_time_events.py**: Standalone Dash application (legacy)

### Documentation

The `docs/` directory contains Markdown documentation:

- **index.md**: Home page and overview
- **setup.md**: Setup and installation guide
- **monitoring.md**: Monitoring and control features
- **activity_monitor.md**: Real-time activity monitor documentation
- **user_management.md**: User management documentation
- **api/**: API documentation
- **development/**: Development guides

## Database Models

The main database models defined in `models.py` are:

- **User**: Application user accounts
- **ControlTable**: Main control table tracking setup statuses
- **Task**: Available tasks that can be assigned to setups

### Database Initialization

The application uses a centralized database initialization approach:

- **utils/init_db.py**: Handles database table creation and admin user setup
- **app_setup.py**: Interactive setup script that uses init_db.py functions
- **main.py**: Automatically initializes database on application startup

This approach ensures consistent database setup across all environments without requiring separate migration systems.

## Key Routes and Endpoints

Routes are defined in `app.py` and include:

### Web Pages

- **/** - Main control table view
- **/login** - Login page
- **/activity-monitor** - Real-time activity monitor
- **/tasks** - Task management view

### API Endpoints

- **/api/control-table** - List control table entries
- **/api/control-table/<setup>** - Retrieve or update a specific setup
- **/api/control-table/<setup>/reboot** - Reboot a specific setup
- **/api/activity-data** - Real-time activity data for plots

## Making Changes

When making changes to the application, follow these guidelines:

### Adding a New Page

1. Create a new template in the `templates/` directory
2. Add a route in `app.py` that renders the template
3. Update the navigation in `templates/base.html`
4. Document the new page in the appropriate docs file

### Modifying Database Models

1. Update the model in `models.py`
2. Re-initialize the database using `python init_db.py` for development
3. Update related API endpoints in `app.py`
4. Update documentation in `docs/api/models.md`

### Adding a New API Endpoint

1. Add the endpoint function in `app.py`
2. Document the endpoint in `docs/api/endpoints.md`
3. Add tests in the `tests/` directory

### Frontend Changes

1. Add or modify templates in the `templates/` directory
2. Add or update JavaScript in the `static/js/` directory
3. Add or update CSS in the `static/css/` directory

## Development Workflow

1. Create a virtual environment: `python -m venv .venv`
2. Activate the environment: `.venv/bin/activate` (Unix) or `.venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install .`
4. Run complete setup: `python app_setup.py` (creates .env file, validates config, and initializes database)
5. Run the development server: `python main.py`
6. Run tests: `pytest`
7. Build documentation: `mkdocs build`

### Database Schema Changes

When making changes to database models:

1. Update the model definitions in `models.py`
2. For development: Re-run `python app_setup.py` to recreate tables
3. For production: Coordinate schema changes with database administrator
4. Update related API endpoints and documentation 