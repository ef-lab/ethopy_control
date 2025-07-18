# API Endpoints

## Authentication Endpoints

### GET /login
Displays the login form.

### POST /login
Authenticates a user via local database or LDAP.

**Request Body:**
- `username`: Username
- `password`: Password

**Response:**
- Success: Redirects to the index page
- Failure: Redisplays the login form with an error message

**Authentication Process:**
1. If local authentication is enabled, checks username/password against the database
2. If LDAP authentication is enabled and local authentication fails or is disabled, attempts LDAP authentication
3. In development mode (FLASK_ENV=development), bypasses authentication checks

### GET /logout
Logs out the current user and redirects to the login page.

## Control Table Endpoints

### GET /api/control-table
Retrieves the control table data. Requires authentication.

**Query Parameters:**
- `setups[]`: Optional array of setup names to filter the results

**Response:**
```json
{
  "data": [
    {
      "setup": "setup_01",
      "status": "ready",
      "last_ping": "2025-02-25 08:48:21",
      "queue_size": 0,
      "trials": 10,
      "total_liquid": 0.5,
      "state": "WELCOME",
      "task_idx": 1,
      "animal_id": "mouse_01",
      "ip_address": "192.168.1.100"
    }
  ]
}
```

### PUT /api/control-table/{setup}
Updates a specific setup in the control table. Requires authentication.

**Path Parameters:**
- `setup`: The setup identifier

**Request Body:**
```json
{
  "status": "running",
  "animal_id": "mouse_02",
  "task_idx": 2,
  "ip_address": "192.168.1.101"
}
```

**Notes:**
- If `status` is not provided or empty, the current status will be preserved
- You can update `animal_id` and `task_idx` without changing the status
- The IP address is used for the remote reboot functionality

### PUT /api/control-table/bulk-update
Updates multiple setups simultaneously. Requires authentication.

**Request Body:**
```json
{
  "setups": ["setup_01", "setup_02"],
  "updates": {
    "status": "running",
    "task_idx": 1,
    "animal_id": "mouse_group_a"
  }
}
```

**Notes:**
- If `status` is not provided or empty, the current status will be preserved
- You can update other fields without changing the status

### POST /api/control-table/{setup}/reboot
Attempts to reboot a setup via SSH. Requires authentication.

**Path Parameters:**
- `setup`: The setup identifier

**Response:**
```json
{
  "message": "Reboot command sent to setup_01 successfully",
  "setup": "setup_01",
  "ip_address": "192.168.1.100"
}
```

**Requirements:**
- The setup must have an IP address configured
- SSH credentials must be configured in the environment
- The target machine must accept SSH connections and allow sudo reboot
