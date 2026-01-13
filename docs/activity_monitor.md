# Real-Time Activity Monitor

The Activity Monitor provides a **real-time overview of behavioral events** during experimental sessions. It visualizes all configured behavior types - actions performed by the subject such as licks, lever presses, nose pokes, and touches.

## Features

- **Session overview** - Quick glance at all subject behaviors during a session
- **Auto-discovery** - Automatically detects all behavior types from database
- **Real-time updates** - 1-second refresh rate for live monitoring
- **Time windows** - View last 30s, 60s, 5m, or all data
- **Session info** - Animal ID, session number, trial count, state, etc.
- **Trial markers** - Vertical lines showing trial start times
- **Extensible** - Add custom behavior types without code changes

**What are behavior events?** Actions performed by the subject (mouse/rat) such as:
- Licks, lever presses, nose pokes, touches, proximity entries

See [Custom Event Types](custom_event_types.md) to track additional behaviors.

## Using the Activity Monitor

### Accessing the Monitor

Navigate to **Activity Monitor** from the main menu, or go to `/activity-monitor`.

### Controls

**Setup Selector** - Choose which experimental setup to monitor

**Time Window**:
- `30s` - Last 30 seconds
- `60s` - Last 60 seconds (default)
- `5m` - Last 5 minutes
- `All` - All data from session start

**Update Controls**:
- `Start` - Begin auto-refresh (updates every second)
- `Stop` - Pause auto-refresh
- `Refresh` - Manual refresh

**Note**: Auto-refresh automatically stops after 5 minutes to prevent excessive database queries.

### Session Information Panel

Displays current session details:
- Animal ID
- Session number
- Current state (e.g., trial, ITI)
- Status (ready, running, stop)
- Trial count
- Total liquid delivered
- Difficulty level
- Last ping time

### Plot Display

The plot shows a **session overview** of all subject behaviors:
- **Y-axis**: Port numbers grouped by behavior type
- **X-axis**: Time (absolute timestamps)
- **Markers**: Behavior events (color and shape based on type)
- **Vertical lines**: Trial start times (gray)

This gives you an instant view of what the subject did throughout the session.

**Interactivity**:
- Zoom: Click and drag
- Pan: Shift + click and drag
- Reset: Double-click
- Hover: See event details

## How It Works

### Data Flow

1. Frontend requests `/api/activity-data?setup=X&time_window=60`
2. Backend queries `#control` table for animal_id and session
3. Backend queries `configuration__port` to discover configured event types
4. Backend queries each `activity__<type>` table for event data
5. Backend returns JSON with all events grouped by type
6. Frontend generates plot with auto-assigned colors/markers

### Convention-Based Discovery

The system automatically discovers event types by:

1. Reading port configurations from `configuration__port`
2. Looking for corresponding `activity__<type>` tables
3. Querying event data for the current session
4. Auto-generating colors and markers from type names

### Database Tables

- `#control` - Session info and setup details
- `configuration__port` - Port configs (defines which behavior types exist)
- `activity__lick`, `activity__lever`, etc. - Behavior event data tables
- `session` - Session timestamps
- `trial` - Trial state events

**Note:** Only subject behaviors are tracked (licks, presses, pokes).

## Customization

### Adding Behavior Types

Track additional subject behaviors without code changes! See [Custom Event Types](custom_event_types.md).

Examples: lever presses, nose pokes, touch screen interactions, wheel turns, etc.

### Modifying Plot Appearance

Edit `templates/activity_monitor.html`:

**Change auto-refresh interval** (line ~406):
```javascript
setInterval(function() {
    fetchActivityData();
}, 1000);  // Change 1000 to desired milliseconds
```

**Modify plot layout** (line ~336):
```javascript
const layout = {
    xaxis: {title: 'Time'},
    yaxis: {title: 'Port'},
    height: 400,  // Change plot height
    // ... add more layout options
};
```

**Custom colors/markers** - Edit hash functions (lines 136-156) or create custom plot page.

### Creating Custom Analysis Plots

The Activity Monitor is for **quick session overview**. For detailed behavioral analysis (histograms, heatmaps, statistics), create custom plot pages.

See [Custom Event Types - Creating Custom Plots](custom_event_types.md#creating-custom-analysis-plots).

## Troubleshooting

### No Behaviors Showing

1. Verify time window includes behaviors
2. Verify database tables exist
5. Ensure subject actually performed behaviors during session

### Plot Not Updating

1. Click "Start" to enable auto-refresh
2. Check "Last Ping" time in session info
3. Verify setup is actively running
4. Check browser console for AJAX errors

### Wrong Behavior Types Displayed

1. Check `configuration__port` table for correct port configs
2. Verify `activity__<type>` tables exist for your behaviors
3. Check table naming: `activity__` prefix with two underscores
4. Remember: Only track subject behaviors, not stimuli (no tone/LED tables)

## API Reference

### GET `/api/activity-data`

**Parameters:**
- `setup` (required) - Setup identifier
- `time_window` (optional) - Seconds to look back, or "all" (default: 60)

**Response:**
```json
{
  "control_data": {
    "animal_id": "mouse123",
    "session": 1,
    "status": "running",
    "state": "trial",
    "trials": 42,
    "total_liquid": 150,
    "difficulty": 3,
    "last_ping_seconds": 5.2
  },
  "events": {
    "lick": [{"port": 1, "time": "2024-01-13T10:30:15.123Z", "ms_time": 1000}],
    ...
  },
  "trial_events": [
    {"trial_idx": 1, "time": "2024-01-13T10:30:10.000Z", "ms_time": 0}
  ]
}
```
