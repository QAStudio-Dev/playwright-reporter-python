"""
Pytest configuration for Playwright tests.

This configures:
- Playwright browser setup
- Screenshot and trace collection
- Custom fixtures for test organization
"""

import os
import pytest
from typing import Generator
from playwright.sync_api import Page, BrowserContext, Playwright, Browser


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
) -> Generator[BrowserContext, None, None]:
    """Create a new browser context for each test with tracing enabled."""
    context = browser.new_context(**browser_context_args)

    # Start tracing before creating the page
    context.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield context

    # Stop tracing and save to file
    trace_dir = "examples/playwright_tests/traces"
    os.makedirs(trace_dir, exist_ok=True)

    # Get test name from request
    test_name = (
        pytestconfig._current_test_name if hasattr(pytestconfig, "_current_test_name") else "trace"
    )
    trace_path = os.path.join(trace_dir, f"{test_name}.zip")

    context.tracing.stop(path=trace_path)
    context.close()


@pytest.fixture(scope="function", autouse=True)
def setup_test_tracking(request, pytestconfig):
    """Track current test name for trace file naming."""
    test_name = request.node.name.replace("[", "_").replace("]", "_")
    pytestconfig._current_test_name = test_name
    yield


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """Create a new page for each test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="session", autouse=True)
def setup_directories():
    """Create necessary directories for test artifacts."""
    directories = [
        "examples/playwright_tests/screenshots",
        "examples/playwright_tests/traces",
        "examples/playwright_tests/videos",
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    yield

    # Cleanup is optional - leaving artifacts for review
