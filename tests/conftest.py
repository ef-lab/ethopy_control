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

        # Assert on the ENGINE, not just the config above. The config value is
        # what we ASKED for; db.engine.url is what create_all/drop_all actually
        # operate on. If an engine had already been built from another URI, the
        # config check would pass while the engine still pointed at a real
        # database. #control and #task are mapped models, so drop_all() on the
        # production server would drop the live experiment tables.
        engine_url = str(db.engine.url)
        assert engine_url == "sqlite:///:memory:", (
            f"REFUSING TO RUN: tests are bound to {engine_url}, not in-memory "
            "SQLite. db.drop_all() below would DROP the #control and #task tables."
        )

        db.create_all()
        yield app
        db.session.remove()
        # Drop tables between tests. `app` is a module-level singleton, so the
        # in-memory SQLite engine is reused across the whole session; without
        # this, rows created by one test's fixtures collide with the next
        # test's inserts (UNIQUE constraint failed: #control.setup).
        db.drop_all()


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
