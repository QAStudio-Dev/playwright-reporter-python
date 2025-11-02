"""pytest plugin for QAStudio.dev integration."""

import time
from typing import Any, Dict, List, Optional
import pytest

from .api_client import QAStudioAPIClient, APIError
from .models import ReporterConfig, TestResult, TestRunSummary
from .utils import (
    batch_list,
    format_duration,
    generate_test_run_name,
    validate_config,
)


class QAStudioPlugin:
    """pytest plugin for reporting test results to QAStudio.dev."""

    def __init__(self, config: ReporterConfig):
        """Initialize the plugin with configuration."""
        self.config = config
        self.api_client = QAStudioAPIClient(config)
        self.test_run_id: Optional[str] = None
        self.results: List[TestResult] = []
        self.start_time: float = 0
        self.session_duration: float = 0

        # Counters
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
        self.error_tests = 0

    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionstart(self, session: Any) -> None:
        """
        Called before test session starts.

        Creates a new test run in QAStudio.dev.
        """
        self.start_time = time.time()
        self._log("QAStudio.dev Reporter initialized")
        self._log(f"Environment: {self.config.environment}")

        try:
            if self.config.create_test_run and not self.config.test_run_id:
                # Create new test run
                test_run_name = self.config.test_run_name or generate_test_run_name()
                response = self.api_client.create_test_run(
                    name=test_run_name,
                    description=self.config.test_run_description,
                )
                self.test_run_id = response.get("id")
                self._log(f"Created test run: {self.test_run_id}")
            else:
                # Use existing test run ID
                self.test_run_id = self.config.test_run_id
                self._log(f"Using existing test run: {self.test_run_id}")

        except APIError as e:
            self._handle_error("Failed to create test run", e)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: Any, call: Any) -> Any:
        """
        Called to create test report for each test phase.

        We only care about the 'call' phase (actual test execution).
        """
        outcome = yield
        report = outcome.get_result()

        # Only process the actual test execution phase
        if report.when == "call":
            try:
                result = TestResult.from_pytest_report(item, report, self.config)
                self.results.append(result)

                # Update counters
                self.total_tests += 1
                if result.status.value == "passed":
                    self.passed_tests += 1
                elif result.status.value == "failed":
                    self.failed_tests += 1
                elif result.status.value == "skipped":
                    self.skipped_tests += 1
                elif result.status.value == "error":
                    self.error_tests += 1

                self._log(
                    f"Test completed: {item.name} - {result.status.value} ({result.duration:.2f}s)"
                )

            except Exception as e:
                self._log(f"Error processing test result: {e}")

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session: Any) -> None:
        """
        Called after all tests have finished.

        Submits results to QAStudio.dev and completes the test run.
        """
        self.session_duration = time.time() - self.start_time

        self._log("Test session completed")
        self._log(
            f"Total: {self.total_tests}, "
            f"Passed: {self.passed_tests}, "
            f"Failed: {self.failed_tests}, "
            f"Skipped: {self.skipped_tests}, "
            f"Errors: {self.error_tests}"
        )
        self._log(f"Duration: {format_duration(self.session_duration)}")

        if not self.test_run_id:
            self._log("No test run ID available, skipping result submission")
            return

        try:
            # Submit test results in batches
            self._submit_results()

            # Complete the test run
            summary = TestRunSummary(
                total=self.total_tests,
                passed=self.passed_tests,
                failed=self.failed_tests,
                skipped=self.skipped_tests,
                errors=self.error_tests,
                duration=self.session_duration,
            )

            self.api_client.complete_test_run(self.test_run_id, summary)
            self._log("Results submitted successfully to QAStudio.dev")

        except APIError as e:
            self._handle_error("Failed to submit results", e)
        finally:
            self.api_client.close()

    def _submit_results(self) -> None:
        """Submit test results in batches."""
        if not self.results:
            self._log("No results to submit")
            return

        batches = batch_list(self.results, self.config.batch_size)
        self._log(f"Submitting {len(self.results)} results in {len(batches)} batch(es)")

        for i, batch in enumerate(batches, 1):
            try:
                self._log(f"Submitting batch {i}/{len(batches)} ({len(batch)} results)")
                self.api_client.submit_test_results(
                    self.test_run_id,  # type: ignore
                    batch,
                )
            except APIError as e:
                self._handle_error(f"Failed to submit batch {i}", e)

    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.config.verbose:
            print(f"[QAStudio] {message}")

    def _handle_error(self, message: str, error: Exception) -> None:
        """Handle errors based on silent mode."""
        error_msg = f"{message}: {str(error)}"

        if self.config.silent:
            print(f"[QAStudio] ERROR: {error_msg}")
        else:
            raise Exception(error_msg) from error


def pytest_addoption(parser: Any) -> None:
    """Add command line options for QAStudio configuration."""
    group = parser.getgroup("qastudio", "QAStudio.dev integration")

    group.addoption(
        "--qastudio-api-url",
        action="store",
        dest="qastudio_api_url",
        help="QAStudio.dev API URL",
    )

    group.addoption(
        "--qastudio-api-key",
        action="store",
        dest="qastudio_api_key",
        help="QAStudio.dev API key",
    )

    group.addoption(
        "--qastudio-project-id",
        action="store",
        dest="qastudio_project_id",
        help="QAStudio.dev project ID",
    )

    group.addoption(
        "--qastudio-environment",
        action="store",
        dest="qastudio_environment",
        default="default",
        help="Test environment name (default: default)",
    )

    group.addoption(
        "--qastudio-test-run-id",
        action="store",
        dest="qastudio_test_run_id",
        help="Existing test run ID (skip creation)",
    )

    group.addoption(
        "--qastudio-test-run-name",
        action="store",
        dest="qastudio_test_run_name",
        help="Custom test run name",
    )

    group.addoption(
        "--qastudio-verbose",
        action="store_true",
        dest="qastudio_verbose",
        help="Enable verbose logging",
    )

    group.addoption(
        "--qastudio-silent",
        action="store_true",
        dest="qastudio_silent",
        default=True,
        help="Fail silently on API errors (default: True)",
    )

    group.addoption(
        "--qastudio-include-error-snippet",
        action="store_true",
        dest="qastudio_include_error_snippet",
        default=True,
        help="Include error code snippet (default: True)",
    )

    group.addoption(
        "--qastudio-include-error-location",
        action="store_true",
        dest="qastudio_include_error_location",
        default=True,
        help="Include precise error location (default: True)",
    )

    group.addoption(
        "--qastudio-include-test-steps",
        action="store_true",
        dest="qastudio_include_test_steps",
        default=True,
        help="Include test execution steps (default: True)",
    )

    group.addoption(
        "--qastudio-include-console-output",
        action="store_true",
        dest="qastudio_include_console_output",
        default=False,
        help="Include console output (default: False)",
    )

    # Add pytest.ini configuration
    parser.addini("qastudio_api_url", "QAStudio.dev API URL")
    parser.addini("qastudio_api_key", "QAStudio.dev API key")
    parser.addini("qastudio_project_id", "QAStudio.dev project ID")
    parser.addini("qastudio_environment", "Test environment name")
    parser.addini("qastudio_test_run_id", "Existing test run ID")
    parser.addini("qastudio_test_run_name", "Custom test run name")
    parser.addini("qastudio_test_run_description", "Test run description")
    parser.addini("qastudio_create_test_run", "Create new test run (true/false)")
    parser.addini("qastudio_batch_size", "Results batch size")
    parser.addini("qastudio_silent", "Fail silently on API errors (true/false)")
    parser.addini("qastudio_verbose", "Enable verbose logging (true/false)")
    parser.addini("qastudio_max_retries", "Maximum API retry attempts")
    parser.addini("qastudio_timeout", "API request timeout in seconds")
    parser.addini(
        "qastudio_include_error_snippet",
        "Include error code snippet (true/false)",
    )
    parser.addini(
        "qastudio_include_error_location",
        "Include precise error location (true/false)",
    )
    parser.addini(
        "qastudio_include_test_steps",
        "Include test execution steps (true/false)",
    )
    parser.addini(
        "qastudio_include_console_output",
        "Include console output (true/false)",
    )


def pytest_configure(config: Any) -> None:
    """
    Configure pytest plugin.

    Registers the plugin if API key is provided.
    """
    # Check if we have minimum required config
    api_key = (
        config.getini("qastudio_api_key")
        or config.getoption("--qastudio-api-key", default=None)
        or None
    )

    if not api_key:
        # No API key provided, skip plugin registration
        return

    try:
        # Create reporter config
        reporter_config = ReporterConfig.from_pytest_config(config)

        # Validate config
        validate_config(reporter_config)

        # Register plugin
        plugin = QAStudioPlugin(reporter_config)
        config.pluginmanager.register(plugin, "qastudio")

        # Register custom markers
        config.addinivalue_line(
            "markers",
            "qastudio_id(id): Link test to QAStudio test case ID",
        )
        config.addinivalue_line(
            "markers",
            "qastudio_priority(level): Set test priority (low/medium/high/critical)",
        )
        config.addinivalue_line(
            "markers",
            "qastudio_tags(*tags): Add tags to test case",
        )

    except Exception as e:
        print(f"[QAStudio] Failed to initialize plugin: {e}")
        raise
