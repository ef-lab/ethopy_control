# Testing Guide

## Running Tests

The project uses pytest for testing. To run the test suite:

```bash
pytest tests/
```

## Test Structure

### Model Tests (`tests/test_models.py`)
- Tests for the ControlTable model
- Status transition validation
- Default values and constraints

### API Tests (`tests/test_api.py`)
- Endpoint testing
- Request validation
- Error handling
- Bulk operations

## Writing Tests

1. Use the provided fixtures in `conftest.py`
2. Follow the existing test patterns
3. Include both positive and negative test cases
4. Test edge cases and error conditions

## Test Database

Tests use SQLite in-memory database by default. The test configuration automatically creates and tears down the database for each test.
