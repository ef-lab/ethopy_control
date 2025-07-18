# Setup Monitoring and Control

## Setup Activity Monitoring

The Control Table Monitor includes features to help you monitor the activity and health of your setups.

### Last Ping Monitoring

The system tracks when each setup last communicated with the server:

- **Last Ping Time**: Displayed in the "Last Ping" column
- **Visual Indicators**: 
  - Setups with last ping > 10 minutes are highlighted with a light red background
  - The timestamp is shown in red text with the time elapsed (e.g., "2025-03-08 14:30:22 (15 min ago)")

### Filtering Active Setups

For easy monitoring of currently active setups:

1. Use the "Active (< 10min)" filter button above the setup filter dropdown
2. This will automatically select only setups that have pinged within the last 10 minutes

Other filter options include:
- All: Show all setups
- Ready: Show setups in "ready" state
- Running: Show setups in "running" state
- Stopped: Show setups in "stop" state

## Remote Reboot Functionality

The application now supports remotely rebooting setups via SSH, which is useful for troubleshooting or resolving issues with lab equipment.

### Requirements

To use the remote reboot functionality:

1. Each setup must have an IP address configured
2. The target machines must:
   - Accept SSH connections
   - Allow the configured user to run `sudo reboot` without a password prompt
3. SSH credentials must be configured in the environment:
   - `SSH_USERNAME`: Default is "pi" (standard Raspberry Pi username)
   - `SSH_PASSWORD`: Default is "raspberry" (standard Raspberry Pi password)

### Configuring IP Addresses

To set or update a setup's IP address:

1. Click the "Edit" button for the setup
2. Enter the IP address in the format `xxx.xxx.xxx.xxx`
3. Click "Save changes"

### Performing a Reboot

Once an IP address is configured for a setup, a "Reboot" button will appear next to the "Edit" button in the Actions column:

1. Click the "Reboot" button for the setup you want to reboot
2. Confirm the reboot when prompted
3. The system will attempt to connect to the setup via SSH and execute a reboot command
4. You'll see a success or error message depending on the result

### Security Considerations

- Store SSH credentials securely in environment variables, not in code
- Use dedicated user accounts with limited privileges for the reboot functionality
- Consider using SSH keys instead of passwords for authentication (requires code modification)
- Update the default Raspberry Pi credentials on your devices

## Status Management

### Updating Status

You can update the status of setups individually or in bulk:

- **Individual Update**: Use the Edit button and select a new status
- **Bulk Update**: Select multiple setups using checkboxes, choose a status from the dropdown, and click "Apply"

### Status Transitions

The system enforces valid status transitions:

- `ready` → `running`
- `running` → `stop`
- `stop` → `ready`

Invalid transitions will be rejected with an error message.

### Field Updates Without Status Change

You can update fields like Animal ID and Task Index without changing the status:

1. Click the "Edit" button for the setup
2. Leave "Status" set to "Keep Current Status"
3. Update the Animal ID and/or Task Index fields
4. Click "Save changes"