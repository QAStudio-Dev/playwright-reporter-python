# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is `qastudio-pytest`, a Python package that provides a pytest plugin for QAStudio.dev test management platform. The package is published to PyPI as `qastudio-pytest`.

**Package name**: `qastudio-pytest`
**Language**: Python
**Target**: Python >=3.8
**Peer dependency**: `pytest` ^7.0.0

## Build Commands

**IMPORTANT**: This project uses a virtual environment located at `venv/`. Always activate it before running commands:

```bash
# Activate virtual environment (required for all commands below)
source venv/bin/activate

# Install dependencies for development
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/qastudio_pytest --cov-report=term-missing

# Type checking
mypy src/qastudio_pytest

# Linting
ruff check src/ tests/

# Format code (ALWAYS run before committing)
black src/ tests/

# Build package
python -m build

# Clean build artifacts
rm -rf dist/ build/ *.egg-info src/*.egg-info

# Install locally
pip install -e .
```

## Architecture

### Core Components

The package consists of four main modules in `src/qastudio_pytest/`:

1. **`plugin.py`** - Main pytest plugin class (`QAStudioPlugin`)
   - Implements pytest hooks: `pytest_configure`, `pytest_sessionstart`, `pytest_runtest_makereport`, `pytest_sessionfinish`
   - Lifecycle: Session start → Test execution → Result collection → Session finish
   - Manages test run creation, result collection, and batch submission
   - Handles plugin state and counters (total, passed, failed, skipped tests)

2. **`api_client.py`** - HTTP client for QAStudio.dev API (`QAStudioAPIClient`)
   - Handles all API communication with retry logic and exponential backoff
   - Methods: `create_test_run()`, `submit_test_results()`, `complete_test_run()`, `upload_attachment()`
   - Built using `requests` library with retry strategy
   - Includes custom `APIError` exception for structured error handling

3. **`models.py`** - Python data models and types
   - `ReporterConfig` - Configuration dataclass with all plugin options
   - `TestResult` - Test result data model with conversion from pytest reports
   - `TestRunSummary` - Summary statistics for completed test runs
   - `TestStatus` - Enum for test states (PASSED, FAILED, SKIPPED)
   - API request/response type hints

4. **`utils.py`** - Helper functions
   - `extract_test_case_id()` - Extracts test case IDs from markers, test names, or docstrings
   - `strip_ansi()` - Removes ANSI escape codes from strings
   - `batch_list()` - Splits lists into batches for efficient API calls
   - `format_duration()` - Converts seconds to readable duration strings

### Plugin Workflow

1. **`pytest_configure`**: Registers plugin if API key is configured
2. **`pytest_sessionstart`**: Creates test run via API (or uses existing test_run_id)
3. **`pytest_runtest_makereport`**: Collects test results during execution (call phase only)
4. **`pytest_sessionfinish`**:
   - Converts all test results to QAStudio.dev format
   - Batches results (default: 10 per batch)
   - Submits batches sequentially with error handling
   - Completes test run with summary stats

### Key Design Patterns

- **Silent Mode** (`silent: true` by default): API failures don't raise exceptions, preventing test suite failures
- **Hook Priority**: Uses `tryfirst=True` and `trylast=True` to control execution order
- **Batch Processing**: Results sent in configurable batches to avoid overwhelming API
- **Graceful Degradation**: Continues on API errors when silent mode enabled
- **Test Linking**: Three methods to link tests to QAStudio.dev cases:
  1. Marker: `@pytest.mark.qastudio_id("QA-123")`
  2. Test name pattern: `def test_QA123_feature_name():`
  3. Docstring: `"""QAStudio ID: QA-123"""`

## Python Configuration

- **Python version**: >=3.8
- **Type hints**: Full type annotations throughout
- **Code style**: Black formatter (line length 100)
- **Linting**: Ruff for fast Python linting
- **Type checking**: MyPy with strict mode
- **Testing**: pytest with pytest-cov for coverage

## Package Structure

```
src/qastudio_pytest/    # Source code
  ├── __init__.py       # Package initialization
  ├── plugin.py         # Main pytest plugin
  ├── api_client.py     # API client
  ├── models.py         # Data models
  └── utils.py          # Utilities
tests/                  # Unit tests
  ├── __init__.py
  └── test_utils.py     # Utility function tests
examples/               # Usage examples (not published)
  ├── test_example.py   # Example tests
  ├── pytest.ini        # Example config
  └── .env.example      # Example environment vars
dist/                   # Build output (not in git)
```

Files published to PyPI (see `pyproject.toml` tool.setuptools):

- `src/qastudio_pytest/` - All Python source files
- `README.md`
- `LICENSE`

## Publishing

### Automated (Recommended)

The repository uses GitHub Actions for automated releases and publishing:

1. **`.github/workflows/test.yml`** - CI testing on push/PR
2. **`.github/workflows/release.yml`** - Creates releases (manual trigger)
3. **`.github/workflows/publish.yml`** - Publishes to PyPI on release

Workflow requirements:
- `PYPI_TOKEN` secret must be set in GitHub repository settings
- Token should have upload permissions for `qastudio-pytest` package

See `.github/WORKFLOWS.md` for complete documentation.

### Manual

```bash
# Install build tools
pip install --upgrade build twine

# Build the package
python -m build

# Check the build
twine check dist/*

# Test on TestPyPI (recommended first)
twine upload --repository testpypi dist/*

# Publish to PyPI
twine upload dist/*
```

Configure credentials in `~/.pypirc`:
```ini
[pypi]
  username = __token__
  password = pypi-YOUR_TOKEN_HERE

[testpypi]
  username = __token__
  password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

## Testing Locally

To test changes with a local pytest project:

```bash
# In this package directory
pip install -e .

# In your pytest project, configure pytest.ini
[pytest]
addopts =
    --qastudio-api-key=YOUR_API_KEY
    --qastudio-project-id=YOUR_PROJECT_ID

# Or use environment variables
export QASTUDIO_API_KEY="your_api_key"
export QASTUDIO_PROJECT_ID="your_project_id"
pytest
```

## Important Notes

- **API URL**: Default is `https://qastudio.dev/api`
- **User-Agent**: Set to `qastudio-pytest/1.0.0` in API requests
- **Error messages**: Prefixed with `[QAStudio.dev]` for easy identification
- **Environment variables**: Expected format is `QASTUDIO_API_URL`, `QASTUDIO_API_KEY`, `QASTUDIO_PROJECT_ID`
- **pytest Integration**: Registered via entry point `pytest11` in pyproject.toml

## Configuration Defaults

Key default values in reporter configuration:

- `environment`: `'default'`
- `create_test_run`: `True`
- `verbose`: `False`
- `batch_size`: `10`
- `upload_screenshots`: `True`
- `upload_videos`: `True`
- `max_retries`: `3`
- `timeout`: `30` (30 seconds)
- `silent`: `True`

## Configuration Methods

The plugin can be configured via multiple methods (in priority order):

1. **Command-line options**:
   ```bash
   pytest --qastudio-api-key=KEY --qastudio-project-id=ID
   ```

2. **pytest.ini configuration**:
   ```ini
   [pytest]
   qastudio_api_key = YOUR_KEY
   qastudio_project_id = YOUR_PROJECT
   ```

3. **Environment variables**:
   ```bash
   export QASTUDIO_API_KEY="your_key"
   export QASTUDIO_PROJECT_ID="your_project"
   ```

## Pytest Hooks Used

- **`pytest_configure(config)`**: Plugin registration
- **`pytest_sessionstart(session)`**: Test run creation (tryfirst=True)
- **`pytest_runtest_makereport(item, call)`**: Result collection (hookwrapper=True)
- **`pytest_sessionfinish(session)`**: Result submission (trylast=True)

## Development

### Development Workflow

**IMPORTANT**: Always use the virtual environment at `venv/` for all development work:

```bash
# Activate virtual environment first
source venv/bin/activate

# If black is not installed, install it
pip install black
```

### Pre-Commit Checklist

Before committing any changes, ALWAYS run:

```bash
# 1. Format code with black (REQUIRED)
black src/ tests/

# 2. Run tests
pytest

# 3. Check types
mypy src/qastudio_pytest

# 4. Run linting
ruff check src/ tests/
```

### Adding New Features

1. Update relevant module in `src/qastudio_pytest/`
2. Add unit tests in `tests/`
3. Update type hints and docstrings
4. Run tests: `pytest`
5. Check types: `mypy src/qastudio_pytest`
6. **Format code: `black src/ tests/` (REQUIRED before commit)**

### Common Tasks

```bash
# Watch tests during development
pytest --watch

# Generate coverage report
pytest --cov=src/qastudio_pytest --cov-report=html
open htmlcov/index.html

# Test against specific Python version
tox -e py38  # or py39, py310, py311, py312
```

## Differences from Node.js Version

Key architectural differences from `@qastudio-dev/playwright`:

1. **Plugin System**: Uses pytest hooks instead of Reporter interface
2. **Configuration**: Multiple config sources (CLI, pytest.ini, env vars) vs single object
3. **Test Discovery**: Pytest's test collection vs Playwright's test suite
4. **Markers**: Uses `@pytest.mark.qastudio_id()` instead of annotations
5. **Attachment Handling**: Pytest doesn't have built-in screenshot/video like Playwright

## Related Packages

- **Node.js/Playwright**: `@qastudio-dev/playwright` - Sister package for JavaScript/TypeScript
- **QAStudio.dev**: https://qastudio.dev - Test management platform
