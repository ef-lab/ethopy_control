# Contributing Guide

## Development Setup

1. Clone the repository
2. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install .
   ```
4. Run complete setup:
   ```bash
   python app_setup.py
   ```
   This will interactively create the .env file and initialize the database.

## Development Workflow

1. Create a new branch for your feature
2. Write tests for new functionality
3. Implement your changes
4. Run the test suite: `pytest tests/`
5. Update documentation if needed
6. Submit a pull request

## Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Include docstrings for public functions
- Keep functions focused and concise

## Documentation

- Update relevant documentation in `docs/`
- Use markdown format
- Include examples where appropriate
- Build docs locally: `mkdocs serve`
