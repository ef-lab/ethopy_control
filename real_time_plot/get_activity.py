import sys
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from flask import has_app_context  # Only import what we need

# Add the project root to the Python path to import from the main app
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import config after adding to path
# ruff: noqa: E402
from utils.config import get_config


def convert_ms_to_datetime(session_start: datetime, ms_time: int) -> datetime:
    """
    Convert milliseconds from session start to real datetime.

    Args:
        session_start: The session start time as datetime
        ms_time: Time in milliseconds from session start

    Returns:
        The real datetime value
    """
    return session_start + timedelta(milliseconds=ms_time)


def get_animal_and_session(setup_ind: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Retrieve animal_id and session from the control table based on setup_ind.

    Args:
        setup_ind: The setup identifier to look up in the control table

    Returns:
        A tuple containing (animal_id, session) if found, (None, None) otherwise
    """
    try:
        # Use the experiment database engine directly instead of Flask's app context
        with get_experiment_db_session() as db_session:
            # Query the control table using raw SQL
            query = text("""
                SELECT * FROM `#control`
                WHERE setup = :setup_ind
            """)

            result = db_session.execute(query, {"setup_ind": setup_ind}).first()

            if result:
                return result.animal_id, result.session
            else:
                return None, None

    except Exception as err:
        print(f"Database error: {err}")
        return None, None


# Database configuration
class DatabaseConfig:
    """Configuration handler for database connections."""

    @staticmethod
    def load_config() -> Dict[str, str]:
        """
        Load database configuration from the main app config.

        Returns:
            Database configuration dictionary
        """
        app_config = get_config()
        print("Database host ", app_config.DB_HOST)
        # Get database parameters from the main app config
        config = {
            "host": app_config.DB_HOST,
            "user": app_config.DB_USER,
            "password": app_config.DB_PASSWORD,
            "port": app_config.DB_PORT,
            "db_experiment": app_config.DB_NAME,
            # For the other databases, we'll use the same host but different database names
            "db_behavior": "lab_behavior",
            "db_interface": "lab_interface",
        }

        return config

    @staticmethod
    def get_connection_string(database: str, config: Dict[str, str] = None) -> str:
        """
        Get database connection string for specified database.

        Args:
            database: Database name from config to use
            config: Optional configuration dictionary

        Returns:
            SQLAlchemy connection string
        """
        if config is None:
            config = DatabaseConfig.load_config()

        return (
            f"mysql+pymysql://{config['user']}:{config['password']}@"
            f"{config['host']}:{config.get('port', '3306')}/{config[database]}"
        )


# Load database configuration
db_config = DatabaseConfig.load_config()

# Create engines with the same configuration options as the main app
engine_options = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Create engines for different databases
engine = create_engine(
    DatabaseConfig.get_connection_string("db_behavior", db_config), **engine_options
)
SessionFactory = sessionmaker(bind=engine)

interface_engine = create_engine(
    DatabaseConfig.get_connection_string("db_interface", db_config), **engine_options
)
InterfaceSessionFactory = sessionmaker(bind=interface_engine)

experiment_engine = create_engine(
    DatabaseConfig.get_connection_string("db_experiment", db_config), **engine_options
)
ExperimentSessionFactory = sessionmaker(bind=experiment_engine)


@contextmanager
def get_db_session():
    """
    Context manager for SQLAlchemy session that ensures proper resource cleanup.

    Yields:
        An SQLAlchemy session object
    """
    session = scoped_session(SessionFactory)
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


@contextmanager
def get_interface_db_session():
    """
    Context manager for SQLAlchemy session connected to lab_interface schema.

    Yields:
        An SQLAlchemy session object
    """
    session = scoped_session(InterfaceSessionFactory)
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


@contextmanager
def get_experiment_db_session():
    """
    Context manager for SQLAlchemy session connected to lab_experiment schema.

    Yields:
        An SQLAlchemy session object
    """
    session = scoped_session(ExperimentSessionFactory)
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_port_config_types(animal_id: str, session: int) -> List[Tuple[str, int]]:
    """
    Extract configuration type and port number from configuration_port records.

    Args:
        animal_id: The animal identifier
        session: The session number

    Returns:
        A list of tuples containing (config_type, port_number)
    """
    if animal_id is None or session is None:
        return []

    try:
        with get_interface_db_session() as db_session:
            # Query only the needed fields
            query = text("""
                SELECT type, port
                FROM configuration__port
                WHERE animal_id = :animal_id AND session = :session
                ORDER BY type
            """)

            result = db_session.execute(
                query, {"animal_id": animal_id, "session": session}
            )

            # Convert to list of tuples (configuration_type, port)
            port_configs = [(row.type, row.port) for row in result]

            return port_configs

    except Exception as err:
        print(f"Database error when querying port configurations: {err}")
        return []


def get_session_timestamp(animal_id: str, session: int) -> Optional[str]:
    """
    Retrieve session_tmst from the session table in lab_experiment schema.

    Args:
        animal_id: The animal identifier
        session: The session number

    Returns:
        The session timestamp as a string if found, None otherwise
    """
    if animal_id is None or session is None:
        print("Animal id or session is None")
        return None

    try:
        with get_experiment_db_session() as db_session:
            # Query the session table for session_tmst
            query = text("""
                SELECT session_tmst
                FROM session
                WHERE animal_id = :animal_id AND session = :session
            """)

            result = db_session.execute(
                query, {"animal_id": animal_id, "session": session}
            ).scalar()

            return result

    except Exception as err:
        print(f"Database error when querying session timestamp: {err}")
        return None


def get_time_window_ms(session_start: datetime, seconds: int) -> int:
    """
    Calculate the time window in milliseconds from session start to current time minus specified seconds.

    Args:
        session_start: The session start time
        seconds: Number of seconds to look back from current time

    Returns:
        Time window in milliseconds
    """
    current_time = datetime.now()
    time_diff = current_time - session_start
    window_start = time_diff - timedelta(seconds=seconds)
    return int(window_start.total_seconds() * 1000)


def get_recent_lick_events(
    animal_id: str,
    session: int,
    seconds: Optional[int],
    lick_ports: Optional[List[int]] = None,
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Get lick events from the last X seconds efficiently.

    Args:
        animal_id: The animal identifier
        session: The session number
        seconds: Number of seconds to look back. If None, returns all activity from the start of the session.
        lick_ports: Optional list of specific lick port numbers to filter by

    Returns:
        A dictionary mapping port numbers to lists of timing records
    """
    if animal_id is None or session is None:
        return {}

    try:
        # Get session start time
        session_start = get_session_timestamp(animal_id, session)
        if not session_start:
            print("Could not get session start time")
            return {}
        if seconds is None:
            seconds = (datetime.now() - session_start).total_seconds()

        # Calculate time window in milliseconds
        time_window_ms = get_time_window_ms(session_start, seconds)

        with get_db_session() as db_session:
            # Build query with time window and optional port filtering
            query_text = """
                SELECT port, time
                FROM activity__lick
                WHERE animal_id = :animal_id
                AND session = :session
                AND time >= :time_window
            """

            # Add port filtering if specified
            if lick_ports and len(lick_ports) > 0:
                port_list = ",".join(str(port) for port in lick_ports)
                query_text += f" AND port IN ({port_list})"

            query_text += " ORDER BY port, time"

            # Execute query with time window
            result = db_session.execute(
                text(query_text),
                {
                    "animal_id": animal_id,
                    "session": session,
                    "time_window": time_window_ms,
                },
            )

            # Group by port number
            port_timings = {}
            for row in result:
                row_dict = dict(row._mapping)
                port = row_dict["port"]
                ms_time = row_dict["time"]

                # Convert ms time to real datetime
                real_time = convert_ms_to_datetime(session_start, ms_time)
                row_dict["real_time"] = real_time

                if port not in port_timings:
                    port_timings[port] = []

                port_timings[port].append(row_dict)

            return port_timings

    except Exception as err:
        print(f"Database error when querying recent lick events: {err}")
        return {}


def get_recent_proximity_events(
    animal_id: str,
    session: int,
    seconds: Optional[int],
    proximity_ports: Optional[List[int]] = None,
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Get proximity events from the last X seconds efficiently.

    Args:
        animal_id: The animal identifier
        session: The session number
        seconds: Number of seconds to look back. If None, returns all activity from the start of the session.
        proximity_ports: Optional list of specific proximity port numbers to filter by

    Returns:
        A dictionary mapping port numbers to lists of proximity records
    """
    if animal_id is None or session is None:
        return {}

    try:
        # Get session start time
        session_start = get_session_timestamp(animal_id, session)
        if not session_start:
            print("Could not get session start time")
            return {}
        if seconds is None:
            seconds = (datetime.now() - session_start).total_seconds()
        # Calculate time window in milliseconds
        time_window_ms = get_time_window_ms(session_start, seconds)

        with get_db_session() as db_session:
            # Check if activity__proximity table exists
            table_check = text("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'lab_behavior'
                AND table_name = 'activity__proximity'
            """)

            table_exists = db_session.execute(table_check).scalar() > 0

            if not table_exists:
                print("Table activity__proximity does not exist in lab_behavior schema")
                return {}

            # Build query with time window and optional port filtering
            query_text = """
                SELECT port, time, in_position
                FROM activity__proximity
                WHERE animal_id = :animal_id
                AND session = :session
                AND time >= :time_window
            """

            # Add port filtering if specified
            if proximity_ports and len(proximity_ports) > 0:
                port_list = ",".join(str(port) for port in proximity_ports)
                query_text += f" AND port IN ({port_list})"

            query_text += " ORDER BY port, time"

            # Execute query with time window
            result = db_session.execute(
                text(query_text),
                {
                    "animal_id": animal_id,
                    "session": session,
                    "time_window": time_window_ms,
                },
            )

            # Group by port number
            port_data = {}
            for row in result:
                row_dict = dict(row._mapping)
                port = row_dict["port"]
                ms_time = row_dict["time"]

                # Convert ms time to real datetime
                real_time = convert_ms_to_datetime(session_start, ms_time)
                row_dict["real_time"] = real_time

                if port not in port_data:
                    port_data[port] = []

                port_data[port].append(row_dict)

            return port_data

    except Exception as err:
        print(f"Database error when querying recent proximity events: {err}")
        return {}


def get_available_setups() -> List[Dict[str, Any]]:
    """
    Get all available setups from the control table.

    Returns:
        A list of dictionaries containing setup information (setup, animal_id, session)
    """
    try:
        # Use the experiment database engine directly instead of Flask's app context
        with get_experiment_db_session() as db_session:
            # Query all setups from the control table
            query = text("SELECT setup, animal_id, session FROM `#control`")
            setups = db_session.execute(query).fetchall()

            # Convert to list of dictionaries
            setup_list = [
                {
                    "setup": setup.setup,
                    "animal_id": setup.animal_id,
                    "session": setup.session,
                }
                for setup in setups
            ]

            return setup_list

    except Exception as err:
        print(f"Database error when querying available setups: {err}")
        return []


def use_flask_db_if_available():
    """
    Check if we're running within a Flask application context.

    Returns:
        True if running within Flask app context, False otherwise
    """
    return has_app_context()


def get_control_entry_details(setup_id: str) -> Dict[str, Any]:
    """
    Get all available fields from the control table for a specific setup.
    Uses the Flask SQLAlchemy ORM when available, falls back to direct query when not.

    Args:
        setup_id: The setup identifier to look up in the control table

    Returns:
        A dictionary containing all available fields from the control table
    """
    # Try using the ORM if we're within Flask application context
    if use_flask_db_if_available():
        try:
            from models import ControlTable

            control_entry = ControlTable.query.filter_by(setup=setup_id).first()

            if control_entry:
                # Convert SQLAlchemy model to dictionary
                result = {
                    column.name: getattr(control_entry, column.name)
                    for column in control_entry.__table__.columns
                }

                # Calculate time difference for last_ping if it exists
                if "last_ping" in result and result["last_ping"]:
                    time_diff = datetime.now() - result["last_ping"]
                    result["last_ping_seconds"] = time_diff.total_seconds()

                return result

        except Exception as err:
            print(f"Error using Flask ORM, falling back to direct query: {err}")

    # Fall back to direct database query if not in Flask context or ORM failed
    try:
        # Use the experiment database engine directly
        with get_experiment_db_session() as db_session:
            # Query the control table using raw SQL
            query = text("""
                SELECT * FROM `#control`
                WHERE setup = :setup_id
            """)

            control_entry = db_session.execute(query, {"setup_id": setup_id}).first()

            if not control_entry:
                return {}

            # Convert row to dictionary
            result = {}
            for key in control_entry._mapping.keys():
                result[key] = getattr(control_entry, key)

            # Calculate time difference for last_ping if it exists
            if "last_ping" in result and result["last_ping"]:
                time_diff = datetime.now() - result["last_ping"]
                result["last_ping_seconds"] = time_diff.total_seconds()

            return result

    except Exception as err:
        print(f"Database error when querying control entry details: {err}")
        return {}


def get_recent_trial_states(
    animal_id: str,
    session: int,
    seconds: Optional[int],
    trial_indices: Optional[List[int]] = None,
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Get trial state names and their timings from the last X seconds efficiently.

    Args:
        animal_id: The animal identifier
        session: The session number
        seconds: Number of seconds to look back. If None, returns all activity from the start of the session.
        trial_indices: Optional list of specific trial_idx values to filter by

    Returns:
        A dictionary mapping trial_idx to lists of state/timing records
    """
    if animal_id is None or session is None:
        return {}

    try:
        # Get session start time
        session_start = get_session_timestamp(animal_id, session)
        if not session_start:
            print("Could not get session start time")
            return {}
        if seconds is None:
            seconds = (datetime.now() - session_start).total_seconds()

        # Calculate time window in milliseconds
        time_window_ms = get_time_window_ms(session_start, seconds)

        with get_experiment_db_session() as db_session:
            # Build query with time window and optional trial_idx filtering
            query_text = """
                SELECT trial_idx, time
                FROM trial
                WHERE animal_id = :animal_id
                AND session = :session
                AND time >= :time_window
            """

            # Add trial_idx filtering if specified
            if trial_indices and len(trial_indices) > 0:
                idx_list = ",".join(str(idx) for idx in trial_indices)
                query_text += f" AND trial_idx IN ({idx_list})"

            query_text += " ORDER BY trial_idx, time"

            # Execute query with time window
            result = db_session.execute(
                text(query_text),
                {
                    "animal_id": animal_id,
                    "session": session,
                    "time_window": time_window_ms,
                },
            )
            # Group by trial_idx
            trial_states = {}
            for row in result:
                row_dict = dict(row._mapping)
                trial_idx = row_dict["trial_idx"]
                ms_time = row_dict["time"]

                # Convert ms time to real datetime
                real_time = convert_ms_to_datetime(session_start, ms_time)
                row_dict["real_time"] = real_time

                if trial_idx not in trial_states:
                    trial_states[trial_idx] = []

                trial_states[trial_idx].append(row_dict)
            return trial_states

    except Exception as err:
        print(f"Database error when querying recent trial states: {err}")
        return {}


def get_events_auto(
    animal_id: str, session: int, seconds: Optional[int]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Auto-discover and fetch all event types for a session.

    Convention: All activity tables named 'activity__*' with columns (animal_id, session, port, time).
    The function queries configuration__port to discover which event types are configured,
    then automatically fetches data from the corresponding activity__ tables.

    Args:
        animal_id: The animal identifier
        session: The session number
        seconds: Number of seconds to look back (None for all)

    Returns:
        Dictionary mapping event types to lists of events
        Format: {
            'lick': [{port: 1, time: datetime, ...}, ...],
            'proximity': [{port: 1, time: datetime, in_position: True, ...}, ...],
            'lever': [{port: 1, time: datetime, ...}, ...],
            ...
        }
    """
    if not animal_id or session is None:
        return {}

    # Get session start time
    session_start = get_session_timestamp(animal_id, session)
    if not session_start:
        print(
            f"Could not get session start time for animal {animal_id}, session {session}"
        )
        return {}

    if seconds is None:
        seconds = (datetime.now() - session_start).total_seconds()

    # Calculate time window in milliseconds
    time_window_ms = get_time_window_ms(session_start, seconds)

    # Get configured port types for this session
    port_configs = get_port_config_types(animal_id, session)
    if not port_configs:
        print(f"No port configurations found for animal {animal_id}, session {session}")
        return {}

    # Group ports by event type
    event_types = {}
    for config_type, port in port_configs:
        event_type = config_type.lower()
        if event_type not in event_types:
            event_types[event_type] = []
        event_types[event_type].append(port)

    # Fetch data for each event type
    all_events = {}

    with get_db_session() as db_session:
        for event_type, ports in event_types.items():
            # Construct table name following convention
            table_name = f"activity__{event_type}"

            # Check if table exists
            table_check = text("""
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'lab_behavior'
                AND table_name = :table_name
                LIMIT 1
            """)

            table_exists = db_session.execute(
                table_check, {"table_name": table_name}
            ).scalar()

            if not table_exists:
                print(
                    f"Table {table_name} does not exist in lab_behavior schema, skipping"
                )
                continue

            # Build query for this event type
            port_list = ",".join(str(p) for p in ports)
            query_text = f"""
                SELECT *
                FROM {table_name}
                WHERE animal_id = :animal_id
                AND session = :session
                AND time >= :time_window
                AND port IN ({port_list})
                ORDER BY port, time
            """

            try:
                result = db_session.execute(
                    text(query_text),
                    {
                        "animal_id": animal_id,
                        "session": session,
                        "time_window": time_window_ms,
                    },
                )

                # Process events
                events = []
                for row in result:
                    event = dict(row._mapping)
                    # Convert ms time to real datetime
                    event["real_time"] = convert_ms_to_datetime(
                        session_start, event["time"]
                    )
                    events.append(event)

                if events:
                    all_events[event_type] = events
                    print(f"Found {len(events)} {event_type} events")

            except Exception as err:
                print(f"Error querying {table_name}: {err}")
                continue

    return all_events
