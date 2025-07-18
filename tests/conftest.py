import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

import pytest

# Set testing environment BEFORE importing app
os.environ["FLASK_CONFIG"] = "testing"

from app import app, db


@pytest.fixture
def test_app():
    """Test application fixture with proper configuration and safety checks."""
    # Double-check we're in testing mode
    assert os.environ.get("FLASK_CONFIG") == "testing", (
        "Tests must run with FLASK_CONFIG=testing"
    )

    # Override config to ensure in-memory database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True

    # Set authentication configuration for tests
    app.config["USE_LDAP_AUTH"] = False
    app.config["USE_LOCAL_AUTH"] = True

    with app.app_context():
        # Safety check: ensure we're using in-memory SQLite
        db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        assert "sqlite:///:memory:" in db_uri, (
            f"Tests must use in-memory SQLite, got: {db_uri}"
        )

        db.create_all()
        yield app
        db.session.remove()


@pytest.fixture
def client(test_app):
    """Test client fixture."""
    return test_app.test_client()


@pytest.fixture
def authenticated_client(test_app):
    """Test client with authenticated session."""
    with test_app.test_client() as client:
        with client.session_transaction() as session:
            session["username"] = "test_user"
        yield client
