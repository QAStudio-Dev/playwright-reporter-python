# Playwright Test Example

This directory contains a basic Playwright test framework that demonstrates testing the QAStudio.dev website.

## Quick Start

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 3. Run tests
./run_tests.sh
```

## Setup

### 1. Install Dependencies

First, create and activate a virtual environment (recommended):

```bash
# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Then install dependencies:

```bash
# Install Playwright for Python
pip install playwright pytest-playwright

# Install qastudio-pytest reporter
pip install qastudio-pytest

# Install Playwright browsers
playwright install chromium
```

### 2. Configure QAStudio Reporter (Optional)

To enable reporting to QAStudio.dev, choose one of these methods:

#### Option A: Edit `run_tests.sh` (Recommended for local development)

Open `run_tests.sh` and uncomment the configuration section:

```bash
# Uncomment and fill in your credentials
export QASTUDIO_API_KEY="your_api_key_here"
export QASTUDIO_PROJECT_ID="your_project_id_here"

# Optional configuration
export QASTUDIO_ENVIRONMENT="local"
export QASTUDIO_TEST_RUN_NAME="My Test Run"
export QASTUDIO_VERBOSE="true"
```

#### Option B: Set Environment Variables (Recommended for CI/CD)

```bash
export QASTUDIO_API_KEY="your_api_key"
export QASTUDIO_PROJECT_ID="your_project_id"
```

#### Option C: Update `pytest.ini`

Edit `pytest.ini` and uncomment the credentials:

```ini
qastudio_api_key = YOUR_API_KEY_HERE
qastudio_project_id = YOUR_PROJECT_ID_HERE
```

**Get your credentials**: Visit https://qastudio.dev/settings

## Running Tests

**Important**: Always activate your virtual environment first!

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test
pytest test_qastudio_website.py::test_homepage_loads

# Run tests with specific marker
pytest -m "qastudio_id"

# Using the convenience script (recommended)
./run_tests.sh
```

### Running with QAStudio Reporter

```bash
# With environment variables
export QASTUDIO_API_KEY="your_key"
export QASTUDIO_PROJECT_ID="your_project"
pytest

# With command line options
pytest --qastudio-api-key=YOUR_KEY \
       --qastudio-project-id=YOUR_PROJECT \
       --qastudio-environment=local \
       --qastudio-verbose
```

## Test Structure

### Test Files

- **`test_qastudio_website.py`** - Main test file with example tests
- **`conftest.py`** - Pytest configuration and fixtures
- **`pytest.ini`** - Pytest and QAStudio reporter settings

### Fixtures

- **`page`** - Playwright page instance (function-scoped)
- **`context`** - Browser context with tracing enabled
- **`setup_directories`** - Creates artifact directories

### Test Artifacts

Tests automatically generate:

- **Screenshots**: `screenshots/` - PNG files from test executions
- **Traces**: `traces/` - Playwright trace files (`.zip`) for debugging
- **Videos**: `videos/` - Video recordings (if enabled)

## Test Examples

### QA-001: Homepage Load Test
```python
@pytest.mark.qastudio_id("QA-001")
def test_homepage_loads(page: Page):
    page.goto("https://qastudio.dev")
    expect(page).to_have_title(pytest.approx(".*QAStudio.*", abs=0))
```

### QA-002: Content Verification
```python
@pytest.mark.qastudio_id("QA-002")
def test_homepage_has_content(page: Page):
    page.goto("https://qastudio.dev")
    response = page.goto("https://qastudio.dev")
    assert response.status == 200
```

### QA-003: Navigation Test
```python
@pytest.mark.qastudio_id("QA-003")
def test_homepage_navigation(page: Page):
    response = page.goto("https://qastudio.dev")
    assert response.ok
    assert page.url.startswith("https://qastudio.dev")
```

### QA-004: Performance Test
```python
@pytest.mark.qastudio_id("QA-004")
@pytest.mark.qastudio_priority("high")
def test_response_time(page: Page):
    start_time = time.time()
    response = page.goto("https://qastudio.dev")
    elapsed_time = time.time() - start_time
    assert elapsed_time < 5.0
```

## Viewing Traces

Playwright traces can be viewed using the Playwright trace viewer:

```bash
# View a specific trace
playwright show-trace traces/test_homepage_loads.zip

# Or upload to https://trace.playwright.dev
```

## Integration with QAStudio.dev

When the QAStudio reporter is enabled, tests will:

1. ✅ Create a test run in QAStudio.dev
2. ✅ Link tests using `@pytest.mark.qastudio_id("QA-XXX")`
3. ✅ Upload test results (passed/failed/skipped)
4. ✅ Upload screenshots automatically
5. ✅ Upload trace files (`.zip`) as attachments
6. ✅ Include error messages and stack traces for failures

## Customization

### Adding Custom Fixtures

Edit `conftest.py` to add project-specific fixtures:

```python
@pytest.fixture
def authenticated_page(page: Page):
    # Login logic
    page.goto("https://qastudio.dev/login")
    # ... authentication steps
    yield page
```

### Configuring Browser Options

Update `browser_context_args` in `conftest.py`:

```python
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "permissions": ["geolocation"],
    }
```

## Troubleshooting

### Playwright Not Installed
```bash
playwright install chromium
```

### Tests Failing Due to Network
Check your internet connection and verify https://qastudio.dev is accessible.

### Traces Not Saving
Ensure the `traces/` directory has write permissions:
```bash
chmod -R 755 examples/playwright_tests/traces
```

### Reporter Not Working
Verify API credentials are set:
```bash
echo $QASTUDIO_API_KEY
echo $QASTUDIO_PROJECT_ID
```

## Additional Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [pytest-playwright](https://github.com/microsoft/playwright-pytest)
- [QAStudio.dev Documentation](https://qastudio.dev/docs)
- [qastudio-pytest Repository](https://github.com/QAStudio-Dev/playwright-reporter-python)
