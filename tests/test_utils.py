"""Tests for utility functions."""

from qastudio_pytest.utils import (
    extract_test_case_id,
    format_duration,
    batch_list,
    strip_ansi,
    sanitize_string,
)


class MockItem:
    """Mock pytest item for testing."""

    def __init__(self, name, markers=None, doc=None):
        self.name = name
        self._markers = markers or []
        self.function = type("obj", (object,), {"__doc__": doc})

    def get_closest_marker(self, name):
        for marker in self._markers:
            if marker.name == name:
                return marker
        return None

    def iter_markers(self):
        return iter(self._markers)


class MockMarker:
    """Mock pytest marker."""

    def __init__(self, name, args=None):
        self.name = name
        self.args = args or []


def test_extract_test_case_id_from_marker():
    """Test extracting test case ID from marker."""
    marker = MockMarker("qastudio_id", ["QA-123"])
    item = MockItem("test_something", markers=[marker])

    assert extract_test_case_id(item) == "QA-123"


def test_extract_test_case_id_from_test_name():
    """Test extracting test case ID from test name."""
    item = MockItem("test_QA123_something")

    assert extract_test_case_id(item) == "QA-123"


def test_extract_test_case_id_from_test_name_with_dash():
    """Test extracting test case ID from test name with dash."""
    item = MockItem("test_QA-456_something")

    assert extract_test_case_id(item) == "QA-456"


def test_extract_test_case_id_from_docstring():
    """Test extracting test case ID from docstring."""
    doc = """
    Test something.

    QAStudio ID: QA-789
    """
    item = MockItem("test_something", doc=doc)

    assert extract_test_case_id(item) == "QA-789"


def test_extract_test_case_id_returns_none():
    """Test that None is returned when no ID found."""
    item = MockItem("test_something")

    assert extract_test_case_id(item) is None


def test_format_duration_milliseconds():
    """Test formatting duration in milliseconds."""
    assert format_duration(0.5) == "500ms"
    assert format_duration(0.123) == "123ms"


def test_format_duration_seconds():
    """Test formatting duration in seconds."""
    assert format_duration(5) == "5s"
    assert format_duration(30) == "30s"


def test_format_duration_minutes():
    """Test formatting duration in minutes."""
    assert format_duration(90) == "1m 30s"
    assert format_duration(125) == "2m 5s"


def test_format_duration_hours():
    """Test formatting duration in hours."""
    assert format_duration(3665) == "1h 1m 5s"
    assert format_duration(7325) == "2h 2m 5s"


def test_batch_list():
    """Test splitting list into batches."""
    items = list(range(10))
    batches = batch_list(items, 3)

    assert len(batches) == 4
    assert batches[0] == [0, 1, 2]
    assert batches[1] == [3, 4, 5]
    assert batches[2] == [6, 7, 8]
    assert batches[3] == [9]


def test_batch_list_exact_division():
    """Test batching with exact division."""
    items = list(range(9))
    batches = batch_list(items, 3)

    assert len(batches) == 3
    assert batches[0] == [0, 1, 2]
    assert batches[1] == [3, 4, 5]
    assert batches[2] == [6, 7, 8]


def test_strip_ansi():
    """Test stripping ANSI codes."""
    text = "\x1b[31mRed text\x1b[0m"
    assert strip_ansi(text) == "Red text"


def test_strip_ansi_bracket_codes():
    """Test stripping bracket color codes."""
    text = "[31mRed text[0m"
    assert strip_ansi(text) == "Red text"


def test_strip_ansi_no_codes():
    """Test stripping with no ANSI codes."""
    text = "Plain text"
    assert strip_ansi(text) == "Plain text"


def test_sanitize_string():
    """Test sanitizing string."""
    assert sanitize_string("\x1b[31mtest\x1b[0m") == "test"
    assert sanitize_string("plain") == "plain"
    assert sanitize_string(None) is None
