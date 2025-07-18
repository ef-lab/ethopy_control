# Environment Variables Configuration

The ethopy control requires specific environment variables to be set. **The application will refuse to start** without the required security-critical variables.

## Required Variables

These **MUST** be set or the application won't start:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask session encryption key (generate new) |
| `DB_USER` | Your existing database username |
| `DB_PASSWORD` | Your existing database password |
| `SSH_USERNAME` | Your existing SSH username |
| `SSH_PASSWORD` | Your existing SSH password |

## ✅ Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_CONFIG` | `development` | Environment: `development`, `production`, `testing` |
| `USE_LOCAL_AUTH` | `true` | Enable local database authentication |
| `DB_HOST` | `127.0.0.1` | Database server hostname/IP |
| `DB_PORT` | `3306` | Database port |
| `DB_NAME` | `lab_experiments` | Database name |


## Security Notes

- **SECRET_KEY**: Use the generated value (secure & random)
- **Passwords**: Use your existing credentials, don't change them
- **Never commit** .env files to version control
- **Different SECRET_KEY** for each environment (dev/staging/production)
