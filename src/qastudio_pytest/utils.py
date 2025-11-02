"""Utility functions for QAStudio pytest plugin."""

import re
from datetime import datetime
from typing import Any, List, Optional, TypeVar

T = TypeVar("T")


def extract_test_case_id(item: Any) -> Optional[str]:
    """
    Extract QAStudio test case ID from pytest item.

    Checks in order:
    1. @pytest.mark.qastudio_id marker
    2. Test name pattern (test_QA123_name or test_name_QA123)
    3. Docstring pattern (QAStudio ID: QA-123)
    """
    # Check for qastudio_id marker
    marker = item.get_closest_marker("qastudio_id")
    if marker and marker.args:
        return str(marker.args[0])

    # Check test name for ID pattern
    name = item.name
    # Pattern: QA-123 or QA123
    match = re.search(r"QA[-_]?(\d+)", name, re.IGNORECASE)
    if match:
        return f"QA-{match.group(1)}"

    # Check docstring
    if item.function.__doc__:
        doc = item.function.__doc__
        match = re.search(r"QAStudio\s+ID:\s*(QA[-_]?\d+)", doc, re.IGNORECASE)
        if match:
            test_id = match.group(1).upper()
            # Normalize to QA-123 format
            return re.sub(r"QA[-_]?(\d+)", r"QA-\1", test_id)

    return None


def get_full_test_name(item: Any) -> str:
    """
    Get full test name including class and module hierarchy.

    Examples:
        test_example.py::test_function
        test_example.py::TestClass::test_method
        test_example.py::TestClass::test_method[param]
    """
    parts = []

    # Add module/file name
    if hasattr(item, "fspath"):
        parts.append(item.fspath.basename)

    # Add class name if exists
    if item.cls:
        parts.append(item.cls.__name__)

    # Add test function name
    parts.append(item.name)

    return "::".join(parts)


def generate_test_run_name() -> str:
    """Generate default test run name with timestamp."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M-%S")
    return f"pytest Run - {date_str} {time_str}"


def batch_list(items: List[T], batch_size: int) -> List[List[T]]:
    """Split list into batches of specified size."""
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"

    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def strip_ansi(text: str) -> str:
    """
    Strip ANSI escape codes from string.

    Removes color codes and terminal formatting that can interfere with API calls.
    """
    if not text:
        return text

    # Remove ANSI escape sequences
    text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
    # Remove bracket codes
    text = re.sub(r"\[\d+m", "", text)
    # Remove multi-digit bracket codes
    text = re.sub(r"\[\d+;\d+m", "", text)

    return text.strip()


def sanitize_string(text: Optional[str]) -> Optional[str]:
    """Sanitize string by removing ANSI codes."""
    if text is None:
        return None
    return strip_ansi(text)


def validate_config(config: Any) -> None:
    """
    Validate required configuration options.

    Raises:
        ValueError: If required config is missing
    """
    if not config.api_url:
        raise ValueError("QAStudio API URL is required")

    if not config.api_key:
        raise ValueError("QAStudio API key is required")

    if not config.project_id:
        raise ValueError("QAStudio project ID is required")

    # Validate URL format
    if not config.api_url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid API URL format: {config.api_url}")


def extract_error_snippet(report: Any) -> Optional[str]:
    """
    Extract code snippet showing where the error occurred.

    Args:
        report: pytest test report

    Returns:
        Code snippet with context around the error line, or None if not available
    """
    if not hasattr(report, "longrepr") or not report.longrepr:
        return None

    try:
        # Try to extract from longrepr
        longrepr_str = str(report.longrepr)

        # Look for code sections in the traceback (lines starting with >)
        lines = longrepr_str.split("\n")
        snippet_lines = []
        in_code_section = False

        for line in lines:
            # Detect code lines (often prefixed with spaces or >)
            if line.strip().startswith(">") or (in_code_section and line.startswith(" " * 4)):
                snippet_lines.append(line)
                in_code_section = True
            elif in_code_section and line.strip():
                # Continue collecting until we hit a non-code line
                if not line.startswith("E "):
                    snippet_lines.append(line)
                else:
                    break

        if snippet_lines:
            return "\n".join(snippet_lines[:10])  # Limit to 10 lines

    except Exception:
        pass

    return None


def extract_error_location(report: Any) -> Optional[dict]:
    """
    Extract precise error location (file, line, column).

    Args:
        report: pytest test report

    Returns:
        Dictionary with file, line, and column information, or None if not available
    """
    if not hasattr(report, "longrepr") or not report.longrepr:
        return None

    try:
        # Try to get location from reprcrash
        if hasattr(report.longrepr, "reprcrash"):
            crash = report.longrepr.reprcrash
            return {
                "file": str(crash.path) if hasattr(crash, "path") else None,
                "line": crash.lineno if hasattr(crash, "lineno") else None,
                "column": 0,  # pytest doesn't provide column info
            }

        # Try to parse from longrepr string
        longrepr_str = str(report.longrepr)
        # Look for file:line pattern
        match = re.search(r"([^\s]+\.py):(\d+):", longrepr_str)
        if match:
            return {"file": match.group(1), "line": int(match.group(2)), "column": 0}

    except Exception:
        pass

    return None


def extract_console_output(report: Any) -> Optional[dict]:
    """
    Extract console output (stdout/stderr) from test execution.

    Args:
        report: pytest test report

    Returns:
        Dictionary with stdout and stderr, or None if no output
    """
    stdout = None
    stderr = None

    try:
        # Extract captured stdout
        if hasattr(report, "capstdout") and report.capstdout:
            stdout = sanitize_string(report.capstdout)

        # Extract captured stderr
        if hasattr(report, "capstderr") and report.capstderr:
            stderr = sanitize_string(report.capstderr)

        # Also try sections
        if hasattr(report, "sections"):
            for section_name, section_content in report.sections:
                if "stdout" in section_name.lower():
                    stdout_text = sanitize_string(section_content)
                    if stdout_text:
                        stdout = stdout_text
                elif "stderr" in section_name.lower():
                    stderr_text = sanitize_string(section_content)
                    if stderr_text:
                        stderr = stderr_text

    except Exception:
        pass

    if stdout or stderr:
        return {"stdout": stdout, "stderr": stderr}

    return None


def extract_test_steps(report: Any) -> Optional[List[dict]]:
    """
    Extract test execution steps.

    Note: pytest doesn't have built-in step tracking like Playwright.
    This is a placeholder that returns None for now.
    Users can implement custom step tracking using pytest plugins if needed.

    Args:
        report: pytest test report

    Returns:
        List of step dictionaries, or None if not available
    """
    # pytest doesn't have native step tracking
    # This could be enhanced with pytest-bdd or custom plugins in the future
    return None
