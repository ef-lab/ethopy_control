#!/usr/bin/env python3
"""
Web-based real-time plot that shows lick port and proximity port events over time.
Uses Dash (built on Flask) and Plotly for interactive visualization.
"""

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any

from get_activity import (
    get_session_timestamp,
    get_recent_lick_events,
    get_recent_proximity_events,
    get_port_config_types,
    get_available_setups,
    get_control_entry_details,
)

# Constants
TIME_WINDOWS = {"30sec": 30, "60sec": 60, "5min": 300, "all": None}
UPDATE_INTERVAL_MS = 1000  # Update every 1 second
SETUP_ID = "alexandross-MacBook-Air.local"  # Default setup ID


class EventDataManager:
    """Manages event data from the database and prepares it for visualization."""

    def __init__(self, setup_id: str):
        """Initialize the event data manager.

        Args:
            setup_id: The setup identifier to lookup animal and session
        """
        self.setup_id = setup_id
        self.animal_id = None
        self.session = None
        self.session_start = None
        self.lick_ports = []
        self.proximity_ports = []

        # Control table data
        self.control_data = {}
        self.latest_state = None
        self.latest_status = None
        self.total_liquid = None
        self.difficulty = None
        self.last_ping = None

        # Initialize connection
        self.initialize()

    def set_setup(self, setup_id: str) -> bool:
        """Change the current setup and reinitialize.

        Args:
            setup_id: The new setup identifier

        Returns:
            True if successful, False otherwise
        """
        self.setup_id = setup_id
        return self.initialize()

    def initialize(self) -> bool:
        """Initialize the connection and get basic data.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get control table entry with all details
            self.control_data = get_control_entry_details(self.setup_id)
            if not self.control_data:
                print(f"Could not find control entry for setup {self.setup_id}")
                return False

            # Extract key values
            self.animal_id = self.control_data.get("animal_id")
            self.session = self.control_data.get("session")
            self.latest_state = self.control_data.get("state")
            self.latest_status = self.control_data.get("status")
            self.total_liquid = self.control_data.get("total_liquid")
            self.difficulty = self.control_data.get("difficulty")
            self.last_ping = self.control_data.get("last_ping_seconds")

            # Check if animal_id exists (could be 0) and session is not None
            if self.animal_id is None or self.session is None:
                print(f"Missing animal_id or session for setup {self.setup_id}")
                return False

            # Get session start time
            self.session_start = get_session_timestamp(self.animal_id, self.session)
            if not self.session_start:
                print(
                    f"Could not get session start time for animal {self.animal_id}, session {self.session}"
                )
                return False

            # Get port configurations
            port_configs = get_port_config_types(self.animal_id, self.session)

            # Extract lick ports and proximity ports
            self.lick_ports = [
                port
                for config_type, port in port_configs
                if config_type.lower() == "lick"
            ]
            self.proximity_ports = [
                port
                for config_type, port in port_configs
                if config_type.lower() == "proximity"
            ]

            print(f"Initialized with animal {self.animal_id}, session {self.session}")
            print(f"Lick ports: {self.lick_ports}")
            print(f"Proximity ports: {self.proximity_ports}")

            return True

        except Exception as err:
            print(f"Error during initialization: {err}")
            return False

    def get_latest_data(self, time_window: Optional[int] = None) -> Dict[str, Any]:
        """Get the latest data based on the time window.

        Args:
            time_window: Time window in seconds to look back, None for all data

        Returns:
            Dictionary containing formatted data for plotting
        """

        try:
            # Update control table data
            self.control_data = get_control_entry_details(self.setup_id)
            if self.control_data:
                self.latest_state = self.control_data.get("state")
                self.latest_status = self.control_data.get("status")
                self.total_liquid = self.control_data.get("total_liquid")
                self.difficulty = self.control_data.get("difficulty")
                self.last_ping = self.control_data.get("last_ping_seconds")

            # Get lick events
            lick_events = get_recent_lick_events(
                self.animal_id, self.session, time_window or 3600000, self.lick_ports
            )

            # Get proximity events
            proximity_events = get_recent_proximity_events(
                self.animal_id, self.session, time_window or 3600000, self.proximity_ports
            )

            # Format data for plotting
            formatted_data = {
                "lick_events": [],
                "proximity_events": [],
                "control_data": self.control_data,
            }

            # Process lick events
            for port, events in lick_events.items():
                for event in events:
                    formatted_data["lick_events"].append(
                        {
                            "port": port,
                            "time": event["real_time"],
                            "ms_time": event["time"],
                        }
                    )

            # Process proximity events
            for port, events in proximity_events.items():
                for event in events:
                    formatted_data["proximity_events"].append(
                        {
                            "port": port,
                            "time": event["real_time"],
                            "ms_time": event["time"],
                            "in_position": event.get("in_position", False),
                        }
                    )

            return formatted_data

        except Exception as err:
            print(f"Error getting latest data: {err}")
            return {
                "lick_events": [],
                "proximity_events": [],
                "control_data": {},
            }


# Initialize the Dash app
app = dash.Dash(
    __name__,
    title="Real-time Animal Activity Monitor",
    update_title=None,  # Don't show "Updating..." title
)
server = app.server  # Expose Flask server for production deployment

# Initialize event data manager
event_manager = EventDataManager(SETUP_ID)

# Get available setups for dropdown
available_setups = get_available_setups()
setup_options = [
    {
        "label": f"{setup['setup']}",
        "value": setup["setup"],
    }
    for setup in available_setups
]

if not setup_options:
    # Add default if no setups available
    setup_options = [{"label": SETUP_ID, "value": SETUP_ID}]

# App layout
app.layout = html.Div(
    [
        html.H1("Real-time Animal Activity Monitor", className="header"),
        html.Div(
            [
                # Combined configuration panel with setup and time window
                html.Div(
                    [
                        # Setup selector
                        html.Div(
                            [
                                html.Label("Select Setup:"),
                                dcc.Dropdown(
                                    id="setup-selector",
                                    options=setup_options,
                                    value=SETUP_ID,
                                    clearable=False,
                                    className="setup-dropdown",
                                ),
                            ],
                            className="setup-selector-container",
                        ),
                        # Time window selector
                        html.Div(
                            [
                                html.Label("Time Window:"),
                                dcc.RadioItems(
                                    id="time-window",
                                    options=[
                                        {"label": "Last 30 seconds", "value": "30sec"},
                                        {"label": "Last 60 seconds", "value": "60sec"},
                                        {"label": "Last 5 minutes", "value": "5min"},
                                        {"label": "All time", "value": "all"},
                                    ],
                                    value="60sec",
                                    className="radio-items",
                                ),
                            ],
                            className="time-window-container",
                        ),
                        # Refresh button
                        html.Button(
                            "Refresh Session",
                            id="refresh-button",
                            className="refresh-button",
                        ),
                    ],
                    className="combined-config-panel",
                ),
                # Status panel with plot controls
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Animal ID:"),
                                html.Span(id="animal-id", className="status-value"),
                            ],
                            className="status-item",
                        ),
                        html.Div(
                            [
                                html.Label("Session:"),
                                html.Span(
                                    id="session-number", className="status-value"
                                ),
                            ],
                            className="status-item",
                        ),
                        html.Div(
                            [
                                html.Label("Session Start:"),
                                html.Span(id="session-start", className="status-value"),
                            ],
                            className="status-item",
                        ),
                        html.Div(
                            [
                                html.Label("Current State:"),
                                html.Span(
                                    id="trial-state", className="status-value highlight"
                                ),
                            ],
                            className="status-item",
                        ),
                        html.Div(
                            [
                                html.Label("Status:"),
                                html.Span(id="trial-status", className="status-value"),
                            ],
                            className="status-item",
                        ),
                        html.Div(
                            [
                                html.Label("Total Liquid:"),
                                html.Span(id="total-liquid", className="status-value"),
                            ],
                            className="status-item",
                        ),
                        html.Div(
                            [
                                html.Label("Difficulty:"),
                                html.Span(id="difficulty", className="status-value"),
                            ],
                            className="status-item",
                        ),
                        html.Div(
                            [
                                html.Label("Last Ping:"),
                                html.Span(id="last-ping", className="status-value"),
                            ],
                            className="status-item",
                        ),
                        # Plot Updates controls
                        html.Div(
                            [
                                html.Label("Plot Updates:"),
                                html.Div(
                                    [
                                        html.Button(
                                            "Start",
                                            id="start-button",
                                            className="control-button start",
                                        ),
                                        html.Button(
                                            "Stop",
                                            id="stop-button",
                                            className="control-button stop",
                                        ),
                                        html.Div(
                                            id="update-status",
                                            children="Running",
                                            className="status-indicator running",
                                        ),
                                    ],
                                    className="button-group",
                                ),
                            ],
                            className="status-item plot-controls",
                        ),
                    ],
                    className="status-panel combined-status-panel",
                ),
                # Main plot
                dcc.Graph(id="activity-plot", className="plot"),
                # Update interval - initially active
                dcc.Interval(
                    id="interval-component",
                    interval=UPDATE_INTERVAL_MS,
                    n_intervals=0,
                    disabled=False,
                ),
                # Store for tracking if updates are active
                dcc.Store(id="update-active", data=True),
                # Store for tracking if setup was changed
                dcc.Store(id="setup-changed", data=False),
            ],
            className="container",
        ),
    ],
    className="app",
)

# Add CSS styling
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f5f5f5;
            }
            .app {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                color: #2c3e50;
                text-align: center;
                padding: 10px;
                margin-bottom: 20px;
            }
            .container {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                padding: 20px;
            }
            .combined-config-panel {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-bottom: 20px;
                padding: 15px;
                background-color: #f0f7fa;
                border-radius: 4px;
                align-items: center;
            }
            .setup-selector-container {
                flex: 1;
                min-width: 180px;
                max-width: 250px;
            }
            .setup-dropdown {
                margin-top: 5px;
                width: 100%;
                font-size: 14px;
            }
            .time-window-container {
                flex: 2;
                min-width: 300px;
            }
            .refresh-button {
                padding: 8px 16px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
                margin-top: 5px;
            }
            .refresh-button:hover {
                background-color: #2980b9;
            }
            .radio-items {
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin-top: 10px;
            }
            .radio-items label {
                margin-right: 10px;
                cursor: pointer;
            }
            .button-group {
                display: flex;
                gap: 10px;
                align-items: center;
                margin-top: 10px;
            }
            .control-button {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
                transition: background-color 0.2s;
            }
            .start {
                background-color: #27ae60;
                color: white;
            }
            .start:hover {
                background-color: #2ecc71;
            }
            .stop {
                background-color: #e74c3c;
                color: white;
            }
            .stop:hover {
                background-color: #f25342;
            }
            .status-indicator {
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 14px;
                margin-left: 10px;
            }
            .running {
                background-color: #e1f5e1;
                color: #27ae60;
            }
            .paused {
                background-color: #fadbd8;
                color: #e74c3c;
            }
            .plot {
                height: 600px;
                border-radius: 4px;
                overflow: hidden;
            }
            .status-panel {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-bottom: 20px;
                padding: 15px;
                background-color: #e8f4f8;
                border-radius: 4px;
            }
            .combined-status-panel {
                background: linear-gradient(135deg, #e8f4f8 0%, #f0f8ea 100%);
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }
            .trial-info-panel {
                background-color: #f0f8ea;
            }
            .status-item {
                min-width: 180px;
                flex: 1;
            }
            .status-item label {
                font-weight: bold;
                display: block;
                margin-bottom: 5px;
                color: #34495e;
            }
            .status-value {
                font-size: 16px;
            }
            .highlight {
                font-weight: bold;
                color: #2980b9;
            }
            .plot-controls {
                margin-top: 10px;
                min-width: 250px;
                grid-column: span 2;
            }
            .plot-controls .button-group {
                display: flex;
                align-items: center;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


# Callback to handle setup changes and refresh
@app.callback(
    Output("setup-changed", "data"),
    [Input("setup-selector", "value"), Input("refresh-button", "n_clicks")],
    [State("setup-changed", "data")],
    prevent_initial_call=True,
)
def handle_setup_change(setup_id, refresh_clicks, current_state):
    """Handle setup changes and refresh button clicks.

    Args:
        setup_id: The selected setup identifier
        refresh_clicks: Number of times refresh button was clicked
        current_state: Current state of setup changed flag

    Returns:
        New setup changed state
    """
    ctx = dash.callback_context

    if not ctx.triggered:
        return current_state

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == "setup-selector":
        # Change setup
        event_manager.set_setup(setup_id)
        return not current_state  # Toggle to trigger redraw
    elif trigger_id == "refresh-button":
        # Refresh current setup
        event_manager.initialize()
        return not current_state  # Toggle to trigger redraw

    return current_state


# Callback to update status information
@app.callback(
    [
        Output("animal-id", "children"),
        Output("session-number", "children"),
        Output("session-start", "children"),
        Output("trial-state", "children"),
        Output("trial-status", "children"),
        Output("total-liquid", "children"),
        Output("difficulty", "children"),
        Output("last-ping", "children"),
    ],
    [Input("interval-component", "n_intervals"), Input("setup-changed", "data")],
    [State("update-active", "data")],
)
def update_status(
    n_intervals: int, setup_changed: bool, update_active: bool
) -> Tuple[str, str, str, str, str, str, str, str]:
    """Update the status information.

    Args:
        n_intervals: Number of intervals elapsed (from Dash)
        setup_changed: Whether setup was changed
        update_active: Whether real-time updates are active

    Returns:
        Tuple of status information values
    """
    if update_active:
        # Update control table data
        event_manager.control_data = get_control_entry_details(event_manager.setup_id)
        if event_manager.control_data:
            event_manager.latest_state = event_manager.control_data.get("state")
            event_manager.latest_status = event_manager.control_data.get("status")
            event_manager.total_liquid = event_manager.control_data.get("total_liquid")
            event_manager.difficulty = event_manager.control_data.get("difficulty")
            event_manager.last_ping = event_manager.control_data.get(
                "last_ping_seconds"
            )

    # Format the session start time
    session_start_display = (
        event_manager.session_start.strftime("%Y-%m-%d %H:%M:%S")
        if event_manager.session_start
        else "Unknown"
    )

    # Format last ping time
    last_ping_display = "Unknown"
    if event_manager.last_ping is not None:
        if event_manager.last_ping < 60:
            last_ping_display = f"{int(event_manager.last_ping)}s ago"
        elif event_manager.last_ping < 3600:
            minutes = int(event_manager.last_ping // 60)
            seconds = int(event_manager.last_ping % 60)
            last_ping_display = f"{minutes}m {seconds}s ago"
        else:
            hours = int(event_manager.last_ping // 3600)
            minutes = int((event_manager.last_ping % 3600) // 60)
            last_ping_display = f"{hours}h {minutes}m ago"

    # Return status information
    return (
        str(event_manager.animal_id) if event_manager.animal_id is not None else "Unknown",
        str(event_manager.session or "Unknown"),
        session_start_display,
        event_manager.latest_state or "Unknown",
        event_manager.latest_status or "Unknown",
        f"{event_manager.total_liquid or 0} μL",
        str(event_manager.difficulty or "Unknown"),
        last_ping_display,
    )


# Callback to update the plot
@app.callback(
    Output("activity-plot", "figure"),
    [
        Input("interval-component", "n_intervals"),
        Input("time-window", "value"),
        Input("setup-changed", "data"),
    ],
    [State("update-active", "data")],
)
def update_plot(
    n_intervals: int, time_window_key: str, setup_changed: bool, update_active: bool
) -> go.Figure:
    """Update the plot with new data.

    Args:
        n_intervals: Number of intervals elapsed (from Dash)
        time_window_key: Key for selected time window
        setup_changed: Whether setup was changed
        update_active: Whether real-time updates are active

    Returns:
        Updated Plotly figure
    """
    # Get the selected time window in seconds
    time_window = TIME_WINDOWS[time_window_key]

    # Only fetch new data if updates are active
    if update_active:
        data = event_manager.get_latest_data(time_window)
    else:
        # Use cached data or empty data
        data = {
            "lick_events": [],
            "proximity_events": [],
            "control_data": event_manager.control_data,
        }

    # Initialize figure
    fig = go.Figure()

    # Calculate y-positions for each port
    all_ports = set()
    for event in data["lick_events"]:
        all_ports.add(("lick", event["port"]))
    for event in data["proximity_events"]:
        all_ports.add(("proximity", event["port"]))

    # Sort ports for consistent y-positions
    sorted_ports = sorted(all_ports)
    port_positions = {port: i for i, port in enumerate(sorted_ports, 1)}

    # Add lick events
    if data["lick_events"]:
        times = [event["time"] for event in data["lick_events"]]
        y_positions = [
            port_positions[("lick", event["port"])] for event in data["lick_events"]
        ]

        fig.add_trace(
            go.Scatter(
                x=times,
                y=y_positions,
                mode="markers",
                name="Lick Events",
                marker=dict(symbol="circle", size=12, color="blue", opacity=0.5),
                hovertemplate="Port: %{text}<br>Time: %{x}<extra></extra>",
                text=[f"Lick Port {event['port']}" for event in data["lick_events"]],
            )
        )

    # Add proximity events
    if data["proximity_events"]:
        times = [event["time"] for event in data["proximity_events"]]
        y_positions = [
            port_positions[("proximity", event["port"])]
            for event in data["proximity_events"]
        ]
        in_position = [
            event.get("in_position", False) for event in data["proximity_events"]
        ]

        # Use different colors based on in_position value
        colors = ["green" if pos else "red" for pos in in_position]

        fig.add_trace(
            go.Scatter(
                x=times,
                y=y_positions,
                mode="markers",
                name="Proximity Events",
                marker=dict(symbol="square", size=12, color=colors, opacity=0.5),
                hovertemplate="Port: %{text}<br>Time: %{x}<br>In Position: %{customdata}<extra></extra>",
                text=[
                    f"Proximity Port {event['port']}"
                    for event in data["proximity_events"]
                ],
                customdata=in_position,
            )
        )

    # Calculate appropriate time range for x-axis
    current_time = datetime.now()

    if time_window is not None:
        # Fixed window size based on selection
        x_start = current_time - timedelta(seconds=time_window)
        x_end = current_time + timedelta(seconds=2)  # small buffer
        title = f"Animal Activity Monitor (Last {time_window} seconds)"
    else:
        # Dynamic window size based on all available data
        all_times = []
        all_times.extend([event["time"] for event in data["lick_events"]])
        all_times.extend([event["time"] for event in data["proximity_events"]])

        if all_times:
            x_start = min(all_times) - timedelta(seconds=5)
            x_end = max(all_times) + timedelta(seconds=5)
        else:
            x_start = current_time - timedelta(seconds=60)
            x_end = current_time + timedelta(seconds=2)

        title = "Animal Activity Monitor (All time)"

    # Add setup info to title
    title = f"{title} - Setup: {event_manager.setup_id}"

    # Add state and status info to title
    if event_manager.latest_state:
        title += f" - State: {event_manager.latest_state}"

    if event_manager.latest_status:
        title += f" - Status: {event_manager.latest_status}"

    # Add info about liquid and difficulty
    if event_manager.total_liquid is not None:
        title += f" - Liquid: {event_manager.total_liquid}μL"

    if event_manager.difficulty is not None:
        title += f" - Difficulty: {event_manager.difficulty}"

    # Add paused indicator if updates are not active
    if not update_active:
        title += " (PAUSED)"

    # Create tick labels for the y-axis
    tick_vals = list(port_positions.values())
    tick_text = [
        f"{port_type.capitalize()} Port {port}"
        for (port_type, port) in port_positions.keys()
    ]

    # Update layout
    fig.update_layout(
        title=None,
        xaxis=dict(
            title="Time",
            range=[x_start, x_end],
            gridcolor="#e0e0e0",
            type="date",
        ),
        yaxis=dict(
            title="Port",
            tickvals=tick_vals,
            ticktext=tick_text,
            range=[0, len(port_positions) + 0.5],  # Make range more compact
            gridcolor="#e0e0e0",
        ),
        plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(t=20, l=50, r=20, b=50),
        height=400,  # Reduced from 600 to 400
    )

    return fig


# Callback to handle start/stop buttons
@app.callback(
    [
        Output("interval-component", "disabled"),
        Output("update-active", "data"),
        Output("update-status", "children"),
        Output("update-status", "className"),
    ],
    [Input("start-button", "n_clicks"), Input("stop-button", "n_clicks")],
    [State("update-active", "data")],
    prevent_initial_call=True,
)
def toggle_updates(start_clicks, stop_clicks, current_state):
    """Toggle the real-time updates based on button clicks.

    Args:
        start_clicks: Number of times start button was clicked
        stop_clicks: Number of times stop button was clicked
        current_state: Current state of updates (active or not)

    Returns:
        New interval disabled state, update active state, status text, and status class
    """
    ctx = dash.callback_context

    if not ctx.triggered:
        # No button clicked yet, maintain current state
        return (
            not current_state,
            current_state,
            f"{'Running' if current_state else 'Paused'}",
            "status-indicator running" if current_state else "status-indicator paused",
        )

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "start-button":
        # Start updates
        return False, True, "Running", "status-indicator running"
    else:
        # Stop updates
        return True, False, "Paused", "status-indicator paused"


# Callback to refresh available setups
@app.callback(
    Output("setup-selector", "options"),
    [Input("refresh-button", "n_clicks")],
    prevent_initial_call=True,
)
def refresh_setup_options(refresh_clicks):
    """Refresh the available setup options.

    Args:
        refresh_clicks: Number of times refresh button was clicked

    Returns:
        Updated list of setup options
    """
    # Get fresh list of available setups
    available_setups = get_available_setups()

    if available_setups:
        setup_options = [
            {
                "label": f"{setup['setup']} - {setup['animal_id']}",
                "value": setup["setup"],
            }
            for setup in available_setups
        ]
    else:
        # Add default if no setups available
        setup_options = [{"label": SETUP_ID, "value": SETUP_ID}]

    return setup_options


if __name__ == "__main__":
    print("Starting Real-time Animal Activity Monitor")
    print("Open your web browser and navigate to: http://127.0.0.1:8050/")
    app.run(debug=True)
