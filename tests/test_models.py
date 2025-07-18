import pytest
from datetime import datetime
from app import db
from models import ControlTable


@pytest.fixture
def test_setup(test_app):
    """Test setup fixture that creates a test ControlTable entry."""
    setup = ControlTable(
        setup="test_setup_1",
        status="ready",
        last_ping=datetime.utcnow(),
        queue_size=0,
        trials=0,
        total_liquid=0.0,
        state="Offtime",
        task_idx=1,
        animal_id="mouse_test",
    )
    db.session.add(setup)
    db.session.commit()
    return setup


def test_create_setup(test_app):
    setup = ControlTable(setup="test_setup_2", status="ready")
    db.session.add(setup)
    db.session.commit()

    assert setup.setup == "test_setup_2"
    assert setup.status == "ready"
    assert setup.queue_size == 0
    assert setup.trials == 0
    assert setup.total_liquid == 0.0


def test_status_transitions(test_setup):
    # Test valid transitions
    assert test_setup.can_change_status("running") == True
    assert test_setup.can_change_status("stop") == False

    # Change status to running
    test_setup.status = "running"
    db.session.commit()

    assert test_setup.can_change_status("stop") == True
    assert test_setup.can_change_status("ready") == False


def test_invalid_status_transitions(test_setup):
    assert test_setup.can_change_status("invalid_status") == False
    assert test_setup.can_change_status("exit") == False
