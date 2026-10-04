"""Tests for reporter models and streaming batch submission."""

from unittest.mock import MagicMock

from qastudio_pytest.models import ReporterConfig, TestResult, TestStatus
from qastudio_pytest.plugin import QAStudioPlugin


def _config(**overrides):
    data = dict(
        api_url="https://example.test/api",
        api_key="key",
        project_id="proj",
        batch_size=10,
        silent=True,
        verbose=False,
        upload_attachments=False,
    )
    data.update(overrides)
    return ReporterConfig(**data)


def _result(title, status=TestStatus.PASSED):
    return TestResult(
        test_case_id="QA-1",
        title=title,
        full_title=f"suite > {title}",
        status=status,
        duration=0.12,
        error="boom" if status == TestStatus.FAILED else None,
        stack_trace="trace" if status == TestStatus.FAILED else None,
        error_snippet="expect(1).toBe(2)" if status == TestStatus.FAILED else None,
        error_location={"file": "test.py", "line": 4},
        steps=[{"title": "step", "status": "passed"}],
        console_output={"stdout": "hello"},
        start_time="2024-01-01T00:00:00",
        end_time="2024-01-01T00:00:01",
    )


def test_to_dict_includes_api_fields():
    payload = _result("login", TestStatus.FAILED).to_dict()
    assert payload["status"] == "failed"
    assert payload["testCaseId"] == "QA-1"
    assert payload["errorMessage"] == "boom"
    assert payload["errorSnippet"] == "expect(1).toBe(2)"
    assert payload["errorLocation"]["line"] == 4
    assert payload["steps"][0]["title"] == "step"
    assert payload["consoleOutput"]["stdout"] == "hello"
    assert payload["startTime"]
    assert payload["duration"] == 120


def test_to_dict_maps_error_status_to_failed():
    payload = _result("setup", TestStatus.ERROR).to_dict()
    assert payload["status"] == "failed"


def test_to_dict_truncates_long_stack_traces():
    result = _result("login", TestStatus.FAILED)
    result.stack_trace = "x" * 60000
    payload = result.to_dict()
    assert payload["stackTrace"].endswith("...[truncated]")
    assert len(payload["stackTrace"]) < 60000


def test_plugin_flushes_when_batch_size_is_reached():
    plugin = QAStudioPlugin(_config(batch_size=10))
    plugin.test_run_id = "run-1"
    plugin.api_client = MagicMock()
    plugin.api_client.submit_test_results.return_value = {"results": []}

    for i in range(25):
        result = _result(f"test {i}")
        plugin.results.append(result)
        plugin.pending_results.append(result)
        if len(plugin.pending_results) >= plugin.config.batch_size:
            plugin._flush_pending_results()

    plugin._flush_pending_results()
    assert plugin.api_client.submit_test_results.call_count == 3
    sizes = [len(call.args[1]) for call in plugin.api_client.submit_test_results.call_args_list]
    assert sizes == [10, 10, 5]
