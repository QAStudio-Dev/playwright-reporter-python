# Contributing to qastudio-pytest

Thank you for your interest in contributing to qastudio-pytest!

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/QAStudio-Dev/pytest.git
   cd pytest
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode**:
   ```bash
   pip install -e .[dev]
   ```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=qastudio_pytest --cov-report=term-missing

# Run specific test file
pytest tests/test_utils.py -v
```

## Code Quality

### Formatting

We use Black for code formatting:

```bash
# Format code
black src/ tests/

# Check formatting without changes
black --check src/ tests/
```

### Linting

We use flake8 for linting:

```bash
flake8 src/ tests/
```

### Type Checking

We use mypy for static type checking:

```bash
mypy src/
```

## Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and add tests

3. Run the test suite to ensure everything passes

4. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. Push to your fork and create a pull request

## Commit Message Guidelines

We follow conventional commits:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Ensure all tests pass and code is properly formatted
3. Update the CHANGELOG.md if applicable
4. The PR will be merged once you have the sign-off of a maintainer

## Questions?

Feel free to open an issue for any questions or concerns!
