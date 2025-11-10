# QAStudio pytest Plugin

A pytest plugin that integrates with [QAStudio.dev](https://qastudio.dev) test management platform.

## Features

- 🔄 Automatic test result reporting to QAStudio.dev
- 📊 Real-time test run tracking
- 🏷️ Test case linking via markers or test IDs
- 📸 Screenshot and attachment support
- 🔧 Configurable via pytest.ini, command line, or environment variables
- 🎯 Batch result submission for performance
- 🛡️ Silent mode - won't fail tests if API is unavailable
- 📝 Error code snippets with context around failure points
- 📍 Precise error location tracking (file, line, column)
- 📤 Console output capture (stdout/stderr)
- 🔍 Enhanced debugging context for test failures

## Installation

```bash
pip install qastudio-pytest
```

## Quick Start

### 1. Configure via pytest.ini

```ini
[pytest]
qastudio_api_url = https://qastudio.dev/api
qastudio_api_key = your-api-key
qastudio_project_id = your-project-id
qastudio_environment = CI
```

### 2. Configure via Environment Variables

```bash
export QASTUDIO_API_URL=https://qastudio.dev/api
export QASTUDIO_API_KEY=your-api-key
export QASTUDIO_PROJECT_ID=your-project-id
export QASTUDIO_ENVIRONMENT=CI
```

### 3. Configure via Command Line

```bash
pytest --qastudio-api-url=https://qastudio.dev/api \
       --qastudio-api-key=your-api-key \
       --qastudio-project-id=your-project-id
```

## Usage

### Linking Tests to QAStudio Test Cases

#### Method 1: Using pytest markers

```python
import pytest

@pytest.mark.qastudio_id("QA-123")
def test_login():
    assert user.login("user", "pass")
```

#### Method 2: Using test ID in test name

```python
def test_QA123_login():
    """Test case QA-123"""
    assert user.login("user", "pass")
```

#### Method 3: Using docstring

```python
def test_login():
    """
    Test user login functionality

    QAStudio ID: QA-123
    """
    assert user.login("user", "pass")
```

### Adding Custom Metadata

```python
import pytest

@pytest.mark.qastudio_id("QA-456")
@pytest.mark.qastudio_priority("high")
@pytest.mark.qastudio_tags("smoke", "authentication")
def test_important_feature():
    assert True
```

## Configuration Options

| Option | Environment Variable | Description | Default |
|--------|---------------------|-------------|---------|
| `qastudio_api_url` | `QASTUDIO_API_URL` | QAStudio.dev API URL | `https://qastudio.dev/api` |
| `qastudio_api_key` | `QASTUDIO_API_KEY` | API authentication key | Required |
| `qastudio_project_id` | `QASTUDIO_PROJECT_ID` | Project ID | Required |
| `qastudio_environment` | `QASTUDIO_ENVIRONMENT` | Environment name | `default` |
| `qastudio_test_run_name` | `QASTUDIO_TEST_RUN_NAME` | Custom test run name | Auto-generated |
| `qastudio_test_run_id` | `QASTUDIO_TEST_RUN_ID` | Existing test run ID | None |
| `qastudio_create_test_run` | `QASTUDIO_CREATE_TEST_RUN` | Create new test run | `true` |
| `qastudio_batch_size` | `QASTUDIO_BATCH_SIZE` | Results batch size | `10` |
| `qastudio_silent` | `QASTUDIO_SILENT` | Fail silently on API errors | `true` |
| `qastudio_verbose` | `QASTUDIO_VERBOSE` | Enable verbose logging | `false` |
| `qastudio_include_error_snippet` | `QASTUDIO_INCLUDE_ERROR_SNIPPET` | Include error code snippet | `true` |
| `qastudio_include_error_location` | `QASTUDIO_INCLUDE_ERROR_LOCATION` | Include precise error location | `true` |
| `qastudio_include_test_steps` | `QASTUDIO_INCLUDE_TEST_STEPS` | Include test execution steps | `true` |
| `qastudio_include_console_output` | `QASTUDIO_INCLUDE_CONSOLE_OUTPUT` | Include console output | `false` |

## Error Context and Debugging

The plugin automatically captures rich debugging context for failed tests:

### Error Code Snippets

When a test fails, the plugin captures the relevant code snippet showing where the error occurred:

```python
def test_calculation():
    result = calculate(5, 0)  # This line will be captured in the error snippet
    assert result == 10
```

Disable with:
```ini
[pytest]
qastudio_include_error_snippet = false
```

### Error Location

Precise error location information (file path, line number) is automatically captured:

```json
{
  "errorLocation": {
    "file": "tests/test_example.py",
    "line": 42,
    "column": 0
  }
}
```

Disable with:
```ini
[pytest]
qastudio_include_error_location = false
```

### Console Output

Capture stdout and stderr from test execution (disabled by default to avoid sensitive data):

```ini
[pytest]
qastudio_include_console_output = true
```

Or via command line:
```bash
pytest --qastudio-include-console-output
```

## Advanced Usage

### Using with pytest-xdist (Parallel Testing)

```bash
pytest -n auto --qastudio-api-key=your-api-key
```

The plugin handles parallel test execution automatically.

### CI/CD Integration

#### GitHub Actions

```yaml
- name: Run Tests
  run: |
    pytest --junitxml=report.xml
  env:
    QASTUDIO_API_KEY: ${{ secrets.QASTUDIO_API_KEY }}
    QASTUDIO_PROJECT_ID: ${{ secrets.QASTUDIO_PROJECT_ID }}
    QASTUDIO_ENVIRONMENT: CI
```

#### GitLab CI

```yaml
test:
  script:
    - pytest
  variables:
    QASTUDIO_API_KEY: $QASTUDIO_API_KEY
    QASTUDIO_PROJECT_ID: $QASTUDIO_PROJECT_ID
    QASTUDIO_ENVIRONMENT: CI
```

## Examples

### Playwright Example

A complete Playwright test framework example is available in `examples/playwright_tests/`:

```bash
# Navigate to example directory
cd examples/playwright_tests

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run the tests
./run_tests.sh

# Or run directly with pytest
pytest -v
```

The example demonstrates:
- ✅ Testing the QAStudio.dev website
- ✅ Automatic screenshot capture
- ✅ Playwright trace recording (`.zip` files)
- ✅ Integration with qastudio-pytest reporter
- ✅ Test case linking with `@pytest.mark.qastudio_id()`

See [`examples/playwright_tests/README.md`](examples/playwright_tests/README.md) for detailed documentation.

## Development

```bash
# Clone repository
git clone https://github.com/QAStudio-Dev/playwright-reporter-python.git
cd playwright-reporter-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Run tests
pytest tests/

# Run linting
black src/ tests/
flake8 src/ tests/
mypy src/

# Build package
python -m build
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: ben@qastudio.dev
- 🐛 Issues: https://github.com/QAStudio-Dev/playwright-reporter-python/issues
- 📖 Documentation: https://qastudio.dev/docs
