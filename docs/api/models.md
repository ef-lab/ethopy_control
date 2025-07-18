# Data Models

## ControlTable

The `ControlTable` model represents an experimental setup in the control system.

### Fields

| Field        | Type      | Description                                    |
|--------------|-----------|------------------------------------------------|
| setup        | String    | Primary key, hostname of the machine           |
| status       | String    | Current setup status (ready/running/stop/exit) |
| last_ping    | DateTime  | Timestamp of the last status update            |
| queue_size   | Integer   | Number of pending operations                   |
| trials       | Integer   | Current trial index in the session             |
| total_liquid | Float     | Total amount of reward delivered               |
| state        | String    | Current experiment execution state             |
| task_idx     | Integer   | Index of the task to be executed               |
| animal_id    | String    | Identifier for the test subject                |

### Status Transitions

The model enforces strict status transitions:

1. From `ready` → `running`
2. From `running` → `stop`
3. From `sleeping` → `stop`

Any other transition will be rejected with an error.
