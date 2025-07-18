#!/usr/bin/env python3
"""
Main entry point for SQL Control Manager.
This is the primary way to start the application.
"""

import logging
import os
from app import app
from utils.init_db import validate_database_connection

# Configure logging
logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    logger.info("Starting SQL Control Manager...")

    # Validate database connection before starting the server
    logger.info("Validating database connection...")
    if not validate_database_connection(app):
        logger.error("Database connection failed. Cannot start server.")
        logger.error("Please ensure your database is running and properly configured.")
        logger.error("Run 'python init_db.py' to initialize the database if needed.")
        return False

    # Start the Flask application
    logger.info("Starting web server...")
    debug_mode = os.environ.get("FLASK_CONFIG", "development") == "development"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
