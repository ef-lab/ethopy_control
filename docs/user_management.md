# User Management

The SQL Control Manager now includes a local user management system that allows administrators to create, edit, and delete users directly within the application.

## User Types

The system supports two types of users:

1. **Regular Users**: Can view and control setups, but cannot manage users
2. **Administrators**: Have full access to all features, including user management

## Accessing User Management

The User Management interface is available to administrators through the Admin menu in the navigation bar.

## Managing Users

### Viewing Users

The User Management page displays a list of all users with the following information:
- Username
- Administrator status
- Creation date
- Actions (Edit, Delete)

### Adding Users

To add a new user:

1. Click the "Add User" button on the User Management page
2. Enter the required information:
   - Username
   - Password
   - Administrator status (checkbox)
3. Click "Create User"

### Editing Users

To edit an existing user:

1. Click the "Edit" button next to the user
2. Modify any of the following:
   - Username
   - Password (leave blank to keep current password)
   - Administrator status
3. Click "Update User"

### Deleting Users

To delete a user:

1. Click the "Delete" button next to the user
2. Confirm the deletion when prompted

**Note**: You cannot delete your own account.

## Default Administrator

When the application is first run, a default administrator account is created:
- Username: `admin`
- Password: `admin`

**Important Security Warning**: Change the default administrator password immediately after installation!

## Authentication Methods

The system supports two authentication methods:

1. **Local Authentication**: Uses the user accounts stored in the database
2. **LDAP Authentication**: Uses an external LDAP directory

Both methods can be enabled simultaneously. When a user attempts to log in, the system will:
1. First check against local user accounts
2. If no matching local account is found or the password is incorrect, attempt LDAP authentication

You can enable or disable either method using environment variables:
- `USE_LOCAL_AUTH`: Set to "True" to enable local authentication (default)
- `USE_LDAP_AUTH`: Set to "True" to enable LDAP authentication (default)

## Best Practices

1. Create individual accounts for each user rather than sharing credentials
2. Limit administrator access to only those who need it
3. Use strong passwords for all accounts
4. Change the default admin password immediately
5. Regularly review the user list and remove accounts that are no longer needed