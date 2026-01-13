# Custom Event Types

## Overview

The activity monitor provides a **real-time overview of behavioral events during a session**. It automatically discovers and plots all types of animal/subject behaviors you define.

### What are Behavior Events?

**Behavior events are actions performed by the subject** (mouse, rat, etc.) during an experiment:

- **Lick** - Subject licks a port/spout
- **Lever press** - Subject presses a lever
- **Nose poke** - Subject pokes into a port
- **Touch** - Subject touches a screen location

**Use this monitor to visualize the subject's actions** and get a quick overview of session activity patterns.

---

## Quick Start

### For DataJoint/ethopy Users

**Add a Part table to your `Activity` class:**

```python
@behavior.schema
class Activity(dj.Manual):
    definition = """
    -> experiment.Trial
    """

    class Lever(dj.Part):
        """Lever press behavior events."""
        definition = """
        -> Activity
        port : tinyint
        time : int
        ---
        press_duration : int  # optional: duration of press in ms
        """
```
---

## How It Works

### Convention-Based Auto-Discovery

The system automatically:

1. **Finds behavior tables** named `activity__<type>` (e.g., `activity__lever`, `activity__touch`)
2. **Reads port configs** from `configuration__port` table
3. **Queries behavior data** for the current session
4. **Generates colors** - Unique color per behavior type (consistent across sessions)
5. **Assigns markers** - Distinct shapes per behavior type
6. **Plots everything** - Gives you an instant overview of session activity

### DataJoint Integration

If using ethopy's DataJoint schema:
- `Activity.Lick` → `activity__lick` table (lick behaviors)
- `Activity.Proximity` → `activity__proximity` table (proximity behaviors)
- `Activity.Lever` → `activity__lever` table (your custom lever press behavior!)
- `Activity.Touch` → `activity__touch` table (touch behaviors)

The naming convention is automatic - just add Part tables for each behavior type!

---

## Examples

### Example 1: Lever Press Behavior

Track when the subject presses a lever:

```python
class Activity(dj.Manual):
    class Lever(dj.Part):
        """Lever press events."""
        definition = """
        -> Activity
        port : tinyint          # which lever
        time : int              # when pressed (ms from session start)
        ---
        press_duration : int    # how long pressed (ms)
        force : float           # press force (optional)
        """
```

### Example 2: Nose Poke Behavior

Track when the subject pokes into a port:

```python
class Activity(dj.Manual):
    class Nosepoke(dj.Part):
        """Nose poke events."""
        definition = """
        -> Activity
        port : tinyint          # which port
        time : int              # when poked
        ---
        duration : int          # duration in port (ms)
        """
```

### Example 3: Multiple Behavior Types

Track different behaviors in the same session:

```python
class Activity(dj.Manual):
    class Lick(dj.Part):
        definition = """
        -> Activity
        port : tinyint
        time : int
        """

    class Lever(dj.Part):
        definition = """
        -> Activity
        port : tinyint
        time : int
        ---
        press_duration : int
        """

    class Nosepoke(dj.Part):
        definition = """
        -> Activity
        port : tinyint
        time : int
        ---
        duration : int
        """
```

All behavior types appear on the same plot - **giving you a complete overview of what the subject did during the session**!

---

## Session Overview

### What This Plot Shows

The Activity Monitor gives you a **real-time overview of a behavioral session**:

- **Quick glance** - See all subject behaviors at once
- **Pattern recognition** - Identify behavioral patterns over time
- **Quality check** - Verify subject is engaging with the task
- **Trial context** - Vertical lines show trial boundaries

### When to Use

- **During sessions** - Monitor ongoing experiments in real-time
- **Debugging** - Check if subject is performing expected behaviors

---

## Automatic Styling

### Color & Marker Assignment

Colors and markers are **auto-generated from behavior type names**:

- **Consistent** - always gets the same color
- **Distinct** - Each behavior type gets a visually different color
- **No limits** - Add unlimited behavior types
- **No configuration** - Just create the table and go!

**Special case:** Events with an `in_position` field (like proximity sensors) use green (in position) / red (not in position) coloring.

### Customizing (Optional)

To override auto-generated styling, edit the hash functions in `templates/activity_monitor.html`, or create a custom plot page.

---

## Creating Custom Analysis Plots

The Activity Monitor is for **quick session overview**. For detailed analysis, create custom plots:

**1. Copy the template:**
```bash
cp templates/activity_monitor.html templates/my_analysis.html
```

**2. Add your analysis code:**
```javascript
function createAnalysisPlot(data) {
    // Example: Plot lick rate over time
    const lickRate = calculateLickRate(data.events.lick);

    // Example: Create histogram of inter-lick intervals
    const intervals = calculateIntervals(data.events.lick);

    // Use any Plotly chart type
    Plotly.newPlot('myPlot', traces, layout);
}
```

**3. Add Flask route:**
```python
@app.route("/my-analysis")
@login_required
def my_analysis():
    from models import ControlTable
    setups = ControlTable.query.all()
    return render_template("my_analysis.html", setups=setups)
```

See [Plotly JavaScript docs](https://plotly.com/javascript/) for analysis options (histograms, heatmaps, statistics, etc.).

---

## Troubleshooting

### Behaviors Not Showing

**Verify naming:**
- Table must be `activity__<type>` (two underscores, lowercase)
- DataJoint: class name becomes lowercase (e.g., `Lever` → `activity__lever`)

**Check port config:**

**Verify columns:**
```sql
DESCRIBE activity__yourtype;
```
Must have: `animal_id`, `session`, `port`, `time`

### No Data Visible

- Try "All time" view (behaviors might be outside time window)
- Check browser console (F12) for errors
- Verify `time` column is in milliseconds from session start
- Check that subject actually performed the behavior during the session

---

## API Response Format

The `/api/activity-data` endpoint returns:

```json
{
  "control_data": {
    "animal_id": "mouse123",
    "session": 1,
    "status": "running",
    "trials": 42
  },
  "events": {
    "lick": [
      {"port": 1, "time": "2024-01-13T10:30:15.123Z", "ms_time": 1000}
    ],
    "lever": [
      {"port": 1, "time": "2024-01-13T10:30:18.123Z", "ms_time": 4000, "press_duration": 150}
    ]
  },
  "trial_events": [
    {"trial_idx": 1, "time": "2024-01-13T10:30:10.000Z", "ms_time": 0}
  ]
}
```

---

## Summary

**Purpose:** Real-time overview of subject behaviors during a session

**To add a custom behavior type:**

1. **DataJoint:** Add `Activity.YourBehavior` Part table
2. **Register port** in `configuration__port`
3. **Done!** Behaviors appear automatically in the overview plot

Examples of behaviors to track:
- Lever presses
- Nose pokes
- Touch screen interactions
- Licks

No code changes. No configuration files. Instant session overview.
