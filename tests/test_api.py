import pytest
import json
from unittest.mock import patch, MagicMock
from app import app, db, AuthenticationResponseStatus
from models import ControlTable


@pytest.fixture
def ldap_test_app():
    """Test application fixture specifically for LDAP testing."""
    # Override config for LDAP tests
    app.config["USE_LDAP_AUTH"] = True
    app.config["USE_LOCAL_AUTH"] = False
    return app


@pytest.fixture
def setup_data(test_app):
    """Test data fixture that creates sample ControlTable entries."""
    setups = [
        ControlTable(
            setup=f"setup_{i:02d}",
            status="ready" if i % 3 == 0 else "running" if i % 3 == 1 else "stop",
            animal_id=f"mouse_{i:02d}",
            task_idx=i,
        )
        for i in range(1, 4)
    ]
    db.session.bulk_save_objects(setups)
    db.session.commit()
    return setups


def test_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Username" in response.data
    assert b"Password" in response.data


@patch("app.LDAP3LoginManager")
def test_login_success(mock_ldap_manager_class, ldap_test_app):
    """Test successful LDAP login."""
    # Create a mock LDAP manager instance
    mock_ldap_manager = MagicMock()
    mock_ldap_manager_class.return_value = mock_ldap_manager

    # Create a mock authentication response
    class MockResponse:
        status = AuthenticationResponseStatus.success

    mock_ldap_manager.authenticate.return_value = MockResponse()

    # Patch the app's ldap_manager directly
    with patch("app.ldap_manager", mock_ldap_manager):
        with ldap_test_app.test_client() as client:
            response = client.post(
                "/login",
                data={"username": "valid_user", "password": "valid_password"},
                follow_redirects=True,
            )

            assert response.status_code == 200
            with client.session_transaction() as session:
                assert "username" in session
                assert session["username"] == "valid_user"


@patch("app.LDAP3LoginManager")
def test_login_failure(mock_ldap_manager_class, ldap_test_app):
    """Test failed LDAP login."""
    # Create a mock LDAP manager instance
    mock_ldap_manager = MagicMock()
    mock_ldap_manager_class.return_value = mock_ldap_manager

    # Create a mock authentication response for failure
    class MockResponse:
        status = AuthenticationResponseStatus.fail

    mock_ldap_manager.authenticate.return_value = MockResponse()

    # Patch the app's ldap_manager directly
    with patch("app.ldap_manager", mock_ldap_manager):
        with ldap_test_app.test_client() as client:
            response = client.post(
                "/login",
                data={"username": "invalid_user", "password": "invalid_password"},
            )

            assert response.status_code == 200
            assert b"Invalid username or password" in response.data
            with client.session_transaction() as session:
                assert "username" not in session


def test_logout(authenticated_client):
    response = authenticated_client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    with authenticated_client.session_transaction() as session:
        assert "username" not in session


def test_protected_routes_redirect_to_login(client, setup_data):
    # Test accessing the index page
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.location

    # Test accessing the API endpoints
    response = client.get("/api/control-table", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.location


def test_get_control_table(authenticated_client, setup_data):
    response = authenticated_client.get("/api/control-table")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data["data"]) == 3
    assert all(
        item["setup"] in ["setup_01", "setup_02", "setup_03"] for item in data["data"]
    )


def test_filter_setups(authenticated_client, setup_data):
    response = authenticated_client.get("/api/control-table?setups[]=setup_01")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data["data"]) == 1
    assert data["data"][0]["setup"] == "setup_01"


def test_update_setup(authenticated_client, setup_data):
    # Find a setup with 'ready' status to test valid transition to 'running'
    ready_setup = next(setup for setup in setup_data if setup.status == "ready")
    update_data = {"status": "running", "animal_id": "mouse_new", "task_idx": 5}
    response = authenticated_client.put(
        f"/api/control-table/{ready_setup.setup}",
        data=json.dumps(update_data),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "running"
    assert data["animal_id"] == "mouse_new"
    assert data["task_idx"] == 5


def test_invalid_status_transition(authenticated_client, setup_data):
    # Find a setup with 'ready' status to test invalid transition to 'stop'
    ready_setup = next(setup for setup in setup_data if setup.status == "ready")
    update_data = {
        "status": "stop",  # Invalid transition from ready to stop
        "animal_id": "mouse_new",
    }
    response = authenticated_client.put(
        f"/api/control-table/{ready_setup.setup}",
        data=json.dumps(update_data),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_bulk_update(authenticated_client, setup_data):
    update_data = {"setups": ["setup_01", "setup_02"], "updates": {"status": "running"}}
    response = authenticated_client.put(
        "/api/control-table/bulk-update",
        data=json.dumps(update_data),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["updated_count"] > 0
