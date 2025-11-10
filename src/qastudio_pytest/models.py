"""Data models for QAStudio.dev API integration."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class TestStatus(Enum):
    """Test execution status."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Test result data to send to QAStudio.dev."""

    test_case_id: Optional[str]
    title: str
    full_title: str
    status: TestStatus
    duration: float  # in seconds
    error: Optional[str] = None
    stack_trace: Optional[str] = None
    error_snippet: Optional[str] = None
    error_location: Optional[Dict[str, Any]] = None
    steps: Optional[List[Dict[str, Any]]] = None
    console_output: Optional[Dict[str, str]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    attachment_paths: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    result_id: Optional[str] = None  # API result ID for uploading attachments

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API submission."""
        result: Dict[str, Any] = {
            "testCaseId": self.test_case_id,
            "title": self.title,
            "fullTitle": self.full_title,
            "status": self.status.value,
            "duration": int(self.duration * 1000),  # Convert to milliseconds
            "error": self.error,
            "stackTrace": self.stack_trace,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "metadata": {
                **self.metadata,
                "filePath": self.file_path,
                "lineNumber": self.line_number,
            },
        }

        # Add optional fields if present
        if self.error_snippet is not None:
            result["errorSnippet"] = self.error_snippet
        if self.error_location is not None:
            result["errorLocation"] = self.error_location
        if self.steps is not None:
            result["steps"] = self.steps
        if self.console_output is not None:
            result["consoleOutput"] = self.console_output
        if self.attachments is not None:
            result["attachments"] = self.attachments

        return result

    @classmethod
    def from_pytest_report(
        cls, item: Any, report: Any, config: Optional["ReporterConfig"] = None
    ) -> "TestResult":
        """Create TestResult from pytest item and report."""
        from .utils import (
            extract_test_case_id,
            get_full_test_name,
            extract_error_snippet,
            extract_error_location,
            extract_console_output,
            extract_test_steps,
        )

        # Extract test case ID from markers or test name
        test_case_id = extract_test_case_id(item)

        # Determine status
        if report.passed:
            status = TestStatus.PASSED
        elif report.failed:
            status = TestStatus.FAILED if report.when == "call" else TestStatus.ERROR
        elif report.skipped:
            status = TestStatus.SKIPPED
        else:
            status = TestStatus.ERROR

        # Extract error information
        error = None
        stack_trace = None
        error_snippet = None
        error_location = None
        if report.longrepr:
            if hasattr(report.longrepr, "reprcrash"):
                error = str(report.longrepr.reprcrash.message)
            if hasattr(report.longrepr, "reprtraceback"):
                stack_trace = str(report.longrepr.reprtraceback)
            elif isinstance(report.longrepr, tuple):
                # For skipped tests
                error = str(report.longrepr[2])
            else:
                error = str(report.longrepr)

            # Extract error snippet and location if enabled
            if config:
                if config.include_error_snippet:
                    error_snippet = extract_error_snippet(report)
                if config.include_error_location:
                    error_location = extract_error_location(report)

        # Extract metadata from markers
        metadata = {}
        for marker in item.iter_markers():
            if marker.name.startswith("qastudio_"):
                key = marker.name.replace("qastudio_", "")
                if key != "id":  # Already extracted as test_case_id
                    metadata[key] = marker.args[0] if marker.args else True

        # Get location information
        file_path = str(item.fspath) if hasattr(item, "fspath") else None
        line_number = item.location[1] if hasattr(item, "location") else None

        # Extract console output if enabled
        console_output = None
        if config and config.include_console_output:
            console_output = extract_console_output(report)

        # Extract test steps if enabled
        steps = None
        if config and config.include_test_steps:
            steps = extract_test_steps(report)

        return cls(
            test_case_id=test_case_id,
            title=item.name,
            full_title=get_full_test_name(item),
            status=status,
            duration=report.duration,
            error=error,
            stack_trace=stack_trace,
            error_snippet=error_snippet,
            error_location=error_location,
            steps=steps,
            console_output=console_output,
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            file_path=file_path,
            line_number=line_number,
            metadata=metadata,
        )


@dataclass
class TestRunSummary:
    """Summary of test run results."""

    total: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float  # in seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API submission."""
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped + self.errors,
            "duration": int(self.duration * 1000),  # Convert to milliseconds
        }


@dataclass
class ReporterConfig:
    """Configuration for QAStudio reporter."""

    api_url: str
    api_key: str
    project_id: str
    environment: str = "default"
    test_run_id: Optional[str] = None
    test_run_name: Optional[str] = None
    test_run_description: Optional[str] = None
    create_test_run: bool = True
    batch_size: int = 10
    silent: bool = True
    verbose: bool = False
    max_retries: int = 3
    timeout: int = 30
    include_error_snippet: bool = True
    include_error_location: bool = True
    include_test_steps: bool = True
    include_console_output: bool = False
    upload_attachments: bool = True
    attachments_dir: Optional[str] = None

    @classmethod
    def from_pytest_config(cls, config: Any) -> "ReporterConfig":
        """Create ReporterConfig from pytest config."""
        import os

        def get_option(name: str, default: Any = None) -> Any:
            """Get option from pytest config, environment, or default."""
            # Try pytest config first
            value = config.getini(name)
            if value:
                return value

            # Try command line option
            cli_name = f"--{name.replace('_', '-')}"
            value = config.getoption(cli_name, default=None)
            if value is not None:
                return value

            # Try environment variable
            env_name = name.upper()
            value = os.environ.get(env_name)
            if value is not None:
                # Convert string booleans
                if value.lower() in ("true", "1", "yes"):
                    return True
                elif value.lower() in ("false", "0", "no"):
                    return False
                # Convert string numbers
                try:
                    return int(value)
                except ValueError:
                    return value

            return default

        return cls(
            api_url=get_option("qastudio_api_url", "https://qastudio.dev/api"),
            api_key=get_option("qastudio_api_key"),
            project_id=get_option("qastudio_project_id"),
            environment=get_option("qastudio_environment", "default"),
            test_run_id=get_option("qastudio_test_run_id"),
            test_run_name=get_option("qastudio_test_run_name"),
            test_run_description=get_option("qastudio_test_run_description"),
            create_test_run=get_option("qastudio_create_test_run", True),
            batch_size=get_option("qastudio_batch_size", 10),
            silent=get_option("qastudio_silent", True),
            verbose=get_option("qastudio_verbose", False),
            max_retries=get_option("qastudio_max_retries", 3),
            timeout=get_option("qastudio_timeout", 30),
            include_error_snippet=get_option("qastudio_include_error_snippet", True),
            include_error_location=get_option("qastudio_include_error_location", True),
            include_test_steps=get_option("qastudio_include_test_steps", True),
            include_console_output=get_option("qastudio_include_console_output", False),
            upload_attachments=get_option("qastudio_upload_attachments", True),
            attachments_dir=get_option("qastudio_attachments_dir"),
        )
