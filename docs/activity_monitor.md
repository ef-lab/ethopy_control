# Real-time Activity Monitor

The Real-time Activity Monitor is a feature that allows users to visualize and track animal activity in experimental setups in real-time. It displays lick events and proximity events on an interactive timeline plot.

## Overview

The activity monitor was integrated from a standalone Dash application into the main Flask-based web application. It provides:

- Real-time visualization of lick and proximity sensor events
- Session information display (animal ID, session number, trial state, etc.)
- Configurable time windows (30s, 60s, 5m, or all data)
- Color-coded events for better visibility and accessibility

## Architecture

### Components

The activity monitor feature consists of several key components:

1. **Flask Route** (`/activity-monitor`)
   - Defined in `app.py`
   - Renders the activity monitor template
   - Provides session information to the template

2. **API Endpoint** (`/api/activity-data`)
   - Defined in `app.py`
   - Returns JSON data for plotting
   - Fetches and formats database information

3. **HTML Template** (`templates/activity_monitor.html`)
   - Extends the base template
   - Contains the plot configuration and JavaScript code
   - Handles user interactions and plot updates

4. **Backend Data Access** (`real_time_plot/get_activity.py`)
   - Contains database query functions
   - Provides data to the Flask routes
   - Handles database connections

5. **Legacy Standalone Application** (`real_time_plot/real_time_events.py`)
   - Original Dash application (not used in the integrated version)
   - Kept for reference and standalone usage

### Data Flow

1. User visits the `/activity-monitor` page
2. Frontend JavaScript makes AJAX requests to `/api/activity-data`
3. The API endpoint fetches data from the database using functions in `get_activity.py`
4. Data is formatted and returned as JSON
5. The frontend JavaScript processes this data and updates the Plotly chart
6. Auto-refresh occurs at regular intervals (1 second by default)

## Database Integration

The activity monitor accesses the database using a hybrid approach:

- When running within the Flask application, it uses the Flask-SQLAlchemy ORM
- When running standalone, it uses direct SQLAlchemy connections
- The `use_flask_db_if_available()` function detects which context is active

### Database Tables Used

- `#control`: For session information and setup details
- `activity__lick`: For lick event data
- `session`: For session timestamps
- `configuration__port`: For port configuration information

## Frontend Implementation

The frontend uses:

- **Plotly.js**: For interactive data visualization
- **jQuery**: For DOM manipulation and AJAX requests
- **Bootstrap**: For responsive layout and styling

### Plot Configuration

The plot displays:

- Lick events as blue circles
- Proximity events as squares
  - In-position events in Bluish Green (`#009E73`)
  - Not-in-position events in Vermillion (`#D55E00`)

## Making Changes

### Modifying the Plot

To change the plot appearance or behavior:

1. Edit `templates/activity_monitor.html`
2. Look for the `updatePlot()` function (around line 170)
3. Modify the trace definitions or layout as needed
4. For color changes, update the color values in:
   - The `proximityColors` array
   - The `showNotification` function's `backgroundColor` property

Example of changing colors:

```javascript
// Change proximity event colors
proximityColors.push(event.in_position ? '#009E73' : '#D55E00'); // Bluish green and Vermillion

// Change notification colors
backgroundColor: type === 'success' ? '#009E73' : '#D55E00', // Bluish green and Vermillion
```

### Adding New Data Sources

To add a new type of event data:

1. Add a query function in `real_time_plot/get_activity.py`
2. Update the API endpoint in `app.py` to include this data
3. Modify the frontend code in `activity_monitor.html` to display the new data

### Modifying the Layout

To change the page layout:

1. Edit `templates/activity_monitor.html`
2. Modify the HTML structure within the `{% block content %}` section

## Testing Changes

To test changes to the activity monitor:

1. Run the application in development mode: `python app.py`
2. Navigate to `/activity-monitor`
3. Use your browser's developer tools to debug JavaScript
4. Check the Python console for backend errors

## Standalone Mode (Legacy)

The original standalone Dash application can still be run:

```bash
python real_time_plot/real_time_events.py
```

This will start a Dash server on port 8050. Note that it uses the same database functions from `get_activity.py` but operates independently from the Flask application. 