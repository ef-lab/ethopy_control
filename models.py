from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False


class ControlTable(db.Model):
    __tablename__ = "#control"

    setup = db.Column(db.String(100), primary_key=True)
    status = db.Column(db.String(20), nullable=False)
    last_ping = db.Column(db.DateTime, default=datetime.utcnow)
    queue_size = db.Column(db.Integer, default=0)
    trials = db.Column(db.Integer, default=0)
    total_liquid = db.Column(db.Float, default=0.0)
    state = db.Column(db.String(50))
    task_idx = db.Column(db.Integer, default=0)
    animal_id = db.Column(db.String(100))
    ip = db.Column(db.String(15), default=None)
    start_time = db.Column(db.Time, default=None)
    stop_time = db.Column(db.Time, default=None)
    session = db.Column(db.Integer, default=0)
    difficulty = db.Column(db.SmallInteger, default=0)
    notes = db.Column(db.String(255), default=None)
    user_name = db.Column(db.String(100), default=None)

    def __repr__(self):
        return f"<ControlTable {self.setup}>"

    def can_change_status(self, new_status):
        """Validate status transitions"""
        valid_transitions = {
            "ready": ["running", "ready"],
            "running": ["stop", "running"],
            "sleeping": ["stop", "sleeping"],
        }
        return new_status in valid_transitions.get(self.status, [])


class Task(db.Model):
    __tablename__ = "#task"

    task_idx = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Task {self.task_idx}: {self.task}>"
