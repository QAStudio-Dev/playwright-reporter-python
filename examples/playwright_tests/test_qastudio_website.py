"""
Basic Playwright test example for QAStudio.dev website.

This demonstrates:
- Basic page navigation and assertions
- Screenshot capture
- Trace recording
- Integration with qastudio-pytest reporter
"""

import pytest
from playwright.sync_api import Page, expect


def test_homepage_has_content(page: Page):
    """Test that homepage has expected content elements."""
    # Navigate to homepage
    page.goto("https://qastudio.dev")

    # Wait for page to load
    page.wait_for_load_state("domcontentloaded")

    # Verify page has content (body should not be empty)
    body = page.locator("body")
    expect(body).not_to_be_empty()

    # Verify response status is 200
    response = page.goto("https://qastudio.dev")
    assert response is not None
    assert response.status == 200, f"Expected status 200, got {response.status}"


def test_homepage_navigation(page: Page):
    """Test basic navigation on the homepage."""
    # Navigate to homepage
    response = page.goto("https://qastudio.dev")

    # Verify successful response
    assert response is not None, "Failed to load page"
    assert response.ok, f"Response not OK: {response.status} {response.status_text}"

    # Verify URL is correct
    assert page.url.startswith("https://qastudio.dev"), f"Unexpected URL: {page.url}"

    # Take screenshot for documentation
    page.screenshot(path="examples/playwright_tests/screenshots/navigation.png")


@pytest.mark.qastudio_priority("high")
def test_response_time(page: Page):
    """Test that the page loads within acceptable time."""
    import time

    start_time = time.time()

    # Navigate to homepage
    response = page.goto("https://qastudio.dev", wait_until="domcontentloaded")

    elapsed_time = time.time() - start_time

    # Verify response
    assert response is not None
    assert response.ok, f"Failed to load: {response.status}"

    # Verify response time is under 5 seconds
    assert elapsed_time < 5.0, f"Page took {elapsed_time:.2f}s to load (expected < 5s)"
