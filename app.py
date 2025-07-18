import logging
import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_ldap3_login import AuthenticationResponseStatus, LDAP3LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Import configuration
from utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Load configuration from config.py
app.config.from_object(get_config())

# Initialize extensions
db.init_app(app)


# Initialize LDAP if enabled
ldap_manager = None
if app.config["USE_LDAP_AUTH"]:
    ldap_manager = LDAP3LoginManager(app)


# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    # For development purposes - allow bypass of authentication
    dev_mode = os.environ.get("FLASK_ENV") == "development"
    use_local_auth = app.config["USE_LOCAL_AUTH"]
    use_ldap_auth = app.config["USE_LDAP_AUTH"]

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # In development mode, allow any login
        if dev_mode and username and password:
            logger.info(f"DEV MODE: User {username} logged in without verification")
            session["username"] = username
            next_url = request.args.get("next")
            if next_url:
                return redirect(next_url)
            return redirect(url_for("index"))

        # Try local authentication first if enabled
        if use_local_auth:
            from models import User

            try:
                user = User.query.filter_by(username=username).first()
                if user and user.check_password(password):
                    logger.info(f"Local auth: User {username} logged in successfully")
                    session["username"] = username
                    session["is_admin"] = user.is_admin

                    next_url = request.args.get("next")
                    if next_url:
                        return redirect(next_url)
                    return redirect(url_for("index"))
            except Exception as e:
                logger.error(f"Local auth error: {str(e)}", exc_info=True)

        # Try LDAP authentication if enabled and local auth failed
        if use_ldap_auth and ldap_manager:
            try:
                response = ldap_manager.authenticate(username, password)

                if response.status == AuthenticationResponseStatus.success:
                    logger.info(f"LDAP auth: User {username} logged in successfully")
                    session["username"] = username

                    # Redirect to the next parameter or index
                    next_url = request.args.get("next")
                    if next_url:
                        return redirect(next_url)
                    return redirect(url_for("index"))
            except Exception as e:
                logger.error(f"LDAP connection error: {str(e)}", exc_info=True)
                error = "Authentication failed. Please check your credentials."

        # If we got here, authentication failed
        logger.warning(f"Failed login attempt for user {username}")
        error = "Invalid username or password"

    return render_template(
        "login.html",
        error=error,
        dev_mode=dev_mode,
        use_local_auth=use_local_auth,
        use_ldap_auth=use_ldap_auth,
    )


@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    from models import ControlTable

    setups = db.session.query(ControlTable.setup, ControlTable.status).distinct().all()
    return render_template(
        "index.html",
        setups=[{"name": s[0], "status": s[1]} for s in setups],
        username=session.get("username"),
    )


@app.route("/api/control-table", methods=["GET"])
@login_required
def get_control_table():
    try:
        from models import ControlTable

        selected_setups = request.args.getlist("setups[]")
        current_username = session.get("username")

        query = ControlTable.query

        # If specific setups are selected, filter by those
        if selected_setups:
            query = query.filter(ControlTable.setup.in_(selected_setups))
        # Otherwise, filter by current username
        else:
            query = query.filter(
                (ControlTable.user_name == current_username)
                | (
                    ControlTable.user_name.is_(None)
                )  # Also include setups with no user assigned
            )

        records = query.all()
        logger.debug(
            f"Fetched {len(records)} records. Selected setups: {selected_setups}"
        )

        data = [
            {
                "setup": record.setup,
                "status": record.status,
                "last_ping": record.last_ping.strftime("%Y-%m-%d %H:%M:%S"),
                "queue_size": record.queue_size,
                "trials": record.trials,
                "total_liquid": record.total_liquid,
                "state": record.state,
                "task_idx": record.task_idx,
                "animal_id": record.animal_id,
                "ip_address": record.ip or "",
                "start_time": (
                    record.start_time.strftime("%H:%M") if record.start_time else ""
                ),
                "stop_time": (
                    record.stop_time.strftime("%H:%M") if record.stop_time else ""
                ),
                "session": record.session or 0,
                "difficulty": record.difficulty or 0,
                "notes": record.notes or "",
                "user_name": record.user_name or "",
            }
            for record in records
        ]
        return jsonify({"data": data})
    except Exception as e:
        logger.error(f"Error fetching control table data: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/control-table/bulk-update", methods=["PUT"])
@login_required
def bulk_update_control_table():
    try:
        from models import ControlTable

        data = request.json
        setups = data.get("setups", [])
        updates = data.get("updates", {})

        if not setups or not updates:
            return jsonify({"error": "Setups and updates are required"}), 400

        logger.info(f"Bulk update request for setups: {setups} with updates: {updates}")

        records = ControlTable.query.filter(ControlTable.setup.in_(setups)).all()
        if not records:
            return jsonify({"error": "No matching records found"}), 404

        updated_count = 0
        for record in records:
            # Update fields separately
            if "task_idx" in updates:
                record.task_idx = updates["task_idx"]

            if "animal_id" in updates:
                record.animal_id = updates["animal_id"]

            # Only update status if explicitly requested and valid
            if (
                "status" in updates and updates["status"]
            ):  # Check if status is not None or empty
                new_status = updates["status"]
                if record.can_change_status(new_status):
                    record.status = new_status
                    updated_count += 1
                else:
                    logger.warning(
                        f"Invalid status transition for {record.setup}: {record.status} -> {new_status}"
                    )
                    # Still count as updated if we're updating other fields
                    if any(
                        field in updates
                        for field in [
                            "task_idx",
                            "animal_id",
                            "start_time",
                            "stop_time",
                        ]
                    ):
                        updated_count += 1
            else:
                # Count as updated if we're only updating other fields
                if any(
                    field in updates
                    for field in ["task_idx", "animal_id", "start_time", "stop_time"]
                ):
                    updated_count += 1

            record.last_ping = datetime.utcnow()

        db.session.commit()
        logger.info(f"Successfully updated {updated_count} records")

        return jsonify(
            {"message": "Records updated successfully", "updated_count": updated_count}
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in bulk update: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/control-table/<setup>", methods=["PUT"])
@login_required
def update_control_table(setup):
    try:
        from datetime import time
        from models import ControlTable

        record = ControlTable.query.get_or_404(setup)
        data = request.json
        logger.info(f"Update request for setup {setup}: {data}")

        # Update fields separately
        if "task_idx" in data:
            record.task_idx = data["task_idx"]
            logger.info(f"Updated task_idx for {setup} to {data['task_idx']}")

        if "animal_id" in data:
            record.animal_id = data["animal_id"]
            logger.info(f"Updated animal_id for {setup} to {data['animal_id']}")

        if "ip_address" in data:
            record.ip = data["ip_address"]
            logger.info(f"Updated ip_address for {setup} to {data['ip_address']}")

        if "start_time" in data:
            if data["start_time"]:
                # Convert string time (HH:MM) to time object
                hours, minutes = map(int, data["start_time"].split(":"))
                record.start_time = time(hour=hours, minute=minutes)
                logger.info(f"Updated start_time for {setup} to {data['start_time']}")
            else:
                record.start_time = None
                logger.info(f"Cleared start_time for {setup}")

        if "stop_time" in data:
            if data["stop_time"]:
                # Convert string time (HH:MM) to time object
                hours, minutes = map(int, data["stop_time"].split(":"))
                record.stop_time = time(hour=hours, minute=minutes)
                logger.info(f"Updated stop_time for {setup} to {data['stop_time']}")
            else:
                record.stop_time = None
                logger.info(f"Cleared stop_time for {setup}")

        if "user_name" in data:
            record.user_name = data["user_name"] if data["user_name"] else None
            logger.info(f"Updated user_name for {setup} to {data['user_name']}")

        # Only update status if explicitly requested and valid
        if "status" in data and data["status"]:  # Check if status is not None or empty
            new_status = data["status"]
            if not record.can_change_status(new_status):
                error_msg = (
                    f"Invalid status transition from {record.status} to {new_status}"
                )
                logger.warning(error_msg)
                return jsonify({"error": error_msg}), 400
            record.status = new_status
            logger.info(f"Updated status for {setup} to {new_status}")

        record.last_ping = datetime.utcnow()
        db.session.commit()
        logger.info(f"Successfully updated setup {setup}")

        return jsonify(
            {
                "message": "Record updated successfully",
                "setup": record.setup,
                "status": record.status,
                "last_ping": record.last_ping.strftime("%Y-%m-%d %H:%M:%S"),
                "animal_id": record.animal_id,
                "task_idx": record.task_idx,
                "ip_address": record.ip,
                "start_time": (
                    record.start_time.strftime("%H:%M") if record.start_time else ""
                ),
                "stop_time": (
                    record.stop_time.strftime("%H:%M") if record.stop_time else ""
                ),
                "user_name": record.user_name or "",
            }
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating setup {setup}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# Reboot API endpoint
@app.route("/api/control-table/<setup>/reboot", methods=["POST"])
@login_required
def reboot_setup(setup):
    try:
        import os

        import paramiko

        from models import ControlTable

        record = ControlTable.query.get_or_404(setup)

        if not record.ip:
            return jsonify({"error": "No IP address configured for this setup"}), 400

        # Get SSH credentials from environment variables
        ssh_username = os.environ.get("SSH_USERNAME")
        ssh_password = os.environ.get("SSH_PASSWORD")
        
        if not ssh_username or not ssh_password:
            return jsonify({"error": "SSH credentials not configured"}), 500

        # Log the reboot attempt
        logger.info(f"Attempting to reboot setup {setup} at IP {record.ip}")

        try:
            # Create SSH client
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect with timeout
            client.connect(
                hostname=record.ip,
                username=ssh_username,
                password=ssh_password,
                timeout=5,
            )

            # Execute reboot command
            _, stdout, stderr = client.exec_command("sudo reboot")

            # Close connection
            client.close()

            # Update last ping time
            record.last_ping = datetime.utcnow()
            db.session.commit()

            return jsonify(
                {
                    "message": f"Reboot command sent to {setup} successfully",
                    "setup": setup,
                    "ip_address": record.ip,
                }
            )

        except Exception as e:
            logger.error(f"SSH connection error to {record.ip}: {str(e)}")
            return jsonify({"error": f"Failed to connect to {setup}: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Error rebooting setup {setup}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# User management routes
@app.route("/admin/users")
@login_required
def list_users():
    # Check if user is admin
    if not session.get("is_admin", False):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for("index"))

    from models import User

    users = User.query.all()
    return render_template(
        "admin/users.html", users=users, username=session.get("username")
    )


@app.route("/admin/users/add", methods=["GET", "POST"])
@login_required
def add_user():
    # Check if user is admin
    if not session.get("is_admin", False):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        from models import User

        username = request.form.get("username")
        password = request.form.get("password")
        is_admin = request.form.get("is_admin") == "on"

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash(f"User {username} already exists", "danger")
            return redirect(url_for("list_users"))

        # Create new user
        new_user = User(username=username, is_admin=is_admin)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash(f"User {username} created successfully", "success")
        return redirect(url_for("list_users"))

    return render_template("admin/add_user.html", username=session.get("username"))


@app.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    # Check if user is admin
    if not session.get("is_admin", False):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for("index"))

    from models import User

    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        user.username = request.form.get("username")

        # Only update password if provided
        password = request.form.get("password")
        if password:
            user.set_password(password)

        user.is_admin = request.form.get("is_admin") == "on"

        db.session.commit()
        flash(f"User {user.username} updated successfully", "success")
        return redirect(url_for("list_users"))

    return render_template(
        "admin/edit_user.html", user=user, username=session.get("username")
    )


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    # Check if user is admin
    if not session.get("is_admin", False):
        flash("You don't have permission to access this page", "danger")
        return redirect(url_for("index"))

    from models import User

    user = User.query.get_or_404(user_id)

    # Don't allow deleting yourself
    if user.username == session.get("username"):
        flash("You cannot delete your own account", "danger")
        return redirect(url_for("list_users"))

    db.session.delete(user)
    db.session.commit()

    flash(f"User {user.username} deleted successfully", "success")
    return redirect(url_for("list_users"))


# Task management routes
@app.route("/tasks")
@login_required
def task_list():
    from models import Task as TaskModel

    tasks = TaskModel.query.order_by(TaskModel.task_idx).all()
    return render_template("tasks.html", tasks=tasks, username=session.get("username"))


@app.route("/api/tasks", methods=["GET"])
@login_required
def get_tasks():
    try:
        from models import Task as TaskModel

        tasks = TaskModel.query.order_by(TaskModel.task_idx).all()

        data = [
            {
                "task_idx": task.task_idx,
                "task": task.task,
                "description": task.description,
                "timestamp": (
                    task.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    if task.timestamp
                    else ""
                ),
            }
            for task in tasks
        ]
        return jsonify({"data": data})
    except Exception as e:
        logger.error(f"Error fetching tasks data: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/tasks", methods=["POST"])
@login_required
def add_task():
    try:
        from models import Task as TaskModel

        data = request.json

        if not data.get("task"):
            return jsonify({"error": "Task name is required"}), 400

        # If task_idx is not provided, use the next available index
        task_idx = data.get("task_idx")
        if task_idx is None:
            max_idx = db.session.query(db.func.max(TaskModel.task_idx)).scalar() or 0
            task_idx = max_idx + 1

        # Check if task_idx already exists
        existing_task = TaskModel.query.filter_by(task_idx=task_idx).first()
        if existing_task:
            return jsonify({"error": f"Task index {task_idx} already exists"}), 400

        new_task = TaskModel(
            task_idx=task_idx,
            task=data.get("task"),
            description=data.get("description", ""),
            timestamp=datetime.utcnow(),
        )

        db.session.add(new_task)
        db.session.commit()

        logger.info(f"Added new task: {new_task}")

        return (
            jsonify(
                {
                    "message": "Task added successfully",
                    "task": {
                        "task_idx": new_task.task_idx,
                        "task": new_task.task,
                        "description": new_task.description,
                        "timestamp": new_task.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                }
            ),
            201,
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding task: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/tasks/<int:task_idx>", methods=["PUT"])
@login_required
def update_task(task_idx):
    try:
        from models import Task as TaskModel

        task = TaskModel.query.get_or_404(task_idx)
        data = request.json

        if "task" in data and data["task"]:
            task.task = data["task"]

        if "description" in data:
            task.description = data["description"]

        task.timestamp = datetime.utcnow()

        db.session.commit()
        logger.info(f"Updated task {task_idx}")

        return jsonify(
            {
                "message": "Task updated successfully",
                "task": {
                    "task_idx": task.task_idx,
                    "task": task.task,
                    "description": task.description,
                    "timestamp": task.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                },
            }
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating task {task_idx}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/tasks/<int:task_idx>", methods=["DELETE"])
@login_required
def delete_task(task_idx):
    try:
        from models import Task as TaskModel

        task = TaskModel.query.get_or_404(task_idx)

        db.session.delete(task)
        db.session.commit()

        logger.info(f"Deleted task {task_idx}")

        return jsonify({"message": f"Task {task_idx} deleted successfully"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting task {task_idx}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/activity-monitor")
@login_required
def activity_monitor():
    """Render the real-time activity monitor page."""
    from real_time_plot.get_activity import get_available_setups

    setups = get_available_setups()
    return render_template(
        "activity_monitor.html",
        setups=setups,
        username=session.get("username"),
    )


@app.route("/api/activity-data", methods=["GET"])
@login_required
def get_activity_data():
    """API endpoint to fetch activity data for plotting."""
    try:
        from real_time_plot.get_activity import (
            get_recent_lick_events,
            get_recent_proximity_events,
            get_port_config_types,
            get_control_entry_details,
            get_recent_trial_states
        )

        setup_id = request.args.get("setup")
        time_window = request.args.get("time_window", "60")
        time_window = int(time_window) if time_window != "all" else None

        # Get control entry details to find animal_id and session
        control_data = get_control_entry_details(setup_id)
        if not control_data:
            return jsonify({"error": f"No data found for setup {setup_id}"}), 404

        animal_id = control_data.get("animal_id")
        session = control_data.get("session")

        if animal_id is None or session is None:
            return jsonify({"error": "Missing animal_id or session"}), 404

        # Get port configurations
        port_configs = get_port_config_types(animal_id, session)
        lick_ports = [
            port for config_type, port in port_configs if config_type.lower() == "lick"
        ]
        proximity_ports = [
            port
            for config_type, port in port_configs
            if config_type.lower() == "proximity"
        ]

        # Get events
        lick_events = get_recent_lick_events(
            animal_id, session, time_window, lick_ports
        )
        proximity_events = get_recent_proximity_events(
            animal_id, session, time_window, proximity_ports
        )

        trial_events = get_recent_trial_states(
            animal_id, session, time_window
        )
        # Format data for response - ensure all values are JSON serializable
        formatted_data = {
            "lick_events": [],
            "proximity_events": [],
            "control_data": {},
            "trial_events": [],
            "lick_ports": lick_ports,
            "proximity_ports": proximity_ports,
        }

        # Convert control_data to ensure all values are JSON serializable
        for key, value in control_data.items():
            # Handle datetime objects
            if hasattr(value, "isoformat"):
                formatted_data["control_data"][key] = value.isoformat()
            # Handle timedelta objects
            elif hasattr(value, "total_seconds"):
                formatted_data["control_data"][key] = value.total_seconds()
            else:
                formatted_data["control_data"][key] = value

        # Process lick events
        for port, events in lick_events.items():
            for event in events:
                formatted_data["lick_events"].append(
                    {
                        "port": port,
                        "time": event["real_time"].isoformat(),
                        "ms_time": event["time"],
                    }
                )

        # Process proximity events
        for port, events in proximity_events.items():
            for event in events:
                formatted_data["proximity_events"].append(
                    {
                        "port": port,
                        "time": event["real_time"].isoformat(),
                        "ms_time": event["time"],
                        "in_position": event.get("in_position", False),
                    }
                )

        for trial_idx, events in trial_events.items():
            for event in events:
                formatted_data["trial_events"].append(
                    {
                        "ms_time": event["time"],
                        "time": event["real_time"].isoformat(),
                        "trial_idx": trial_idx
                    }
                )
        # print("formatted_data ", formatted_data)
        return jsonify(formatted_data)

    except Exception as e:
        import traceback

        logger.error(f"Error fetching activity data: {str(e)}", exc_info=True)
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


# Note: To run the application, use main.py instead of running this file directly
