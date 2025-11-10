"""
Pytest configuration for Playwright tests.

This configures:
- Playwright browser setup
- Screenshot and trace collection on failure
- Attachment handling for QAStudio reporter
- Custom fixtures for test organization
"""

import os
import pytest
from typing import Generator, List
from playwright.sync_api import Page, BrowserContext, Playwright, Browser

# Well-known attribute name for QAStudio reporter to find attachments
QASTUDIO_ATTACHMENTS_ATTR = "_qastudio_attachments"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context with additional options."""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "locale": "en-US",
    }


@pytest.fixture(scope="function")
def context(
    browser: Browser,
    browser_context_args: dict,
    pytestconfig,
    request,
) -> Generator[BrowserContext, None, None]:
    """Create a new browser context for each test with tracing enabled."""
    context = browser.new_context(**browser_context_args)

    # Start tracing before creating the page
    context.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield context

    # Initialize attachment list for this test
    attachments: List[str] = []

    # Get test name
    test_name = (
        pytestconfig._current_test_name if hasattr(pytestconfig, "_current_test_name") else "trace"
    )

    # Always save trace file
    trace_dir = os.path.join(os.path.dirname(__file__), "traces")
    os.makedirs(trace_dir, exist_ok=True)
    trace_path = os.path.join(trace_dir, f"{test_name}.zip")
    context.tracing.stop(path=trace_path)

    # Add trace to attachments
    if os.path.exists(trace_path):
        attachments.append(os.path.abspath(trace_path))

    # Store attachments as node attribute for QAStudio reporter
    if attachments:
        setattr(request.node, QASTUDIO_ATTACHMENTS_ATTR, attachments)

    context.close()


@pytest.fixture(scope="function", autouse=True)
def setup_test_tracking(request, pytestconfig):
    """Track current test name for trace file naming."""
    test_name = request.node.name.replace("[", "_").replace("]", "_")
    pytestconfig._current_test_name = test_name
    yield


@pytest.fixture(scope="function")
def page(context: BrowserContext, request) -> Generator[Page, None, None]:
    """Create a new page for each test with screenshot on failure."""
    page = context.new_page()
    yield page

    # Capture screenshot on test failure
    if request.node.rep_call and request.node.rep_call.failed:
        screenshot_dir = os.path.join(os.path.dirname(__file__), "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)

        test_name = request.node.name.replace("[", "_").replace("]", "_")
        screenshot_path = os.path.join(screenshot_dir, f"{test_name}_failure.png")

        try:
            page.screenshot(path=screenshot_path, full_page=True)
            # Add screenshot to attachments
            existing = getattr(request.node, QASTUDIO_ATTACHMENTS_ATTR, [])
            existing.append(os.path.abspath(screenshot_path))
            setattr(request.node, QASTUDIO_ATTACHMENTS_ATTR, existing)
        except Exception as e:
            print(f"Failed to capture screenshot: {e}")

    page.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item):
    """Store test result in item for screenshot capture."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="session", autouse=True)
def setup_directories():
    """Create necessary directories for test artifacts."""
    base_dir = os.path.dirname(__file__)
    directories = [
        os.path.join(base_dir, "screenshots"),
        os.path.join(base_dir, "traces"),
        os.path.join(base_dir, "videos"),
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    yield

    # Cleanup is optional - leaving artifacts for review
