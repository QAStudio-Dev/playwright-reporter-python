# Quick Start Guide - qastudio-pytest

## Installation

```bash
pip install qastudio-pytest
```

## Basic Usage

### 1. Configure via pytest.ini

Create a `pytest.ini` file in your project root:

```ini
[pytest]
qastudio_api_url = https://qastudio.dev/api
qastudio_api_key = your-api-key-here
qastudio_project_id = your-project-id-here
qastudio_environment = CI
```

### 2. Link Tests to QAStudio Test Cases

```python
import pytest

# Method 1: Using marker
@pytest.mark.qastudio_id("QA-123")
def test_login():
    assert user.login("admin", "password")

# Method 2: Using test name
def test_QA124_registration():
    assert user.register("newuser@example.com")

# Method 3: Using docstring
def test_password_reset():
    """
    Test password reset functionality.

    QAStudio ID: QA-125
    """
    assert reset_password("user@example.com")
```

### 3. Run Tests

```bash
pytest
```

That's it! Results will automatically be reported to QAStudio.dev.

## Environment Variables

Alternatively, configure using environment variables:

```bash
export QASTUDIO_API_KEY=your-api-key
export QASTUDIO_PROJECT_ID=your-project-id
export QASTUDIO_ENVIRONMENT=CI

pytest
```

## Command Line

Or pass options via command line:

```bash
pytest --qastudio-api-key=your-key \
       --qastudio-project-id=your-project \
       --qastudio-verbose
```

## Verifying Installation

Check if the plugin is installed:

```bash
pytest --help | grep qastudio
```

You should see the qastudio options listed.

## Next Steps

- Read the full [README.md](README.md) for all configuration options
- Check out [examples/](examples/) for more usage examples
- See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup

## Troubleshooting

### Plugin not loading?

Make sure you have configured at least the API key. The plugin only activates when an API key is provided.

### Tests not being linked?

Check that your test IDs match the pattern:
- Marker: `@pytest.mark.qastudio_id("QA-123")`
- Name: `test_QA123_something` or `test_something_QA123`
- Docstring: `QAStudio ID: QA-123`

### API errors?

Enable verbose mode to see detailed logs:

```bash
pytest --qastudio-verbose
```

## Support

- Issues: https://github.com/QAStudio-Dev/playwright-reporter-python/issues
- Email: ben@qastudio.dev
