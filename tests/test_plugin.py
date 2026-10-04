"""Tests for result ID assignment, batch flush, and API retries."""

from unittest.mock import Mock, patch

from qastudio_pytest.api_client import APIError, QAStudioAPIClient
from qastudio_pytest.models import ReporterConfig, TestResult, TestStatus
from qastudio_pytest.plugin import QAStudioPlugin, assign_result_ids


def _result(title: str) -> TestResult:
    return TestResult(
        test_case_id=None,
        title=title,
        full_title=title,
        status=TestStatus.PASSED,
        duration=0.1,
    )


def _config(**overrides: object) -> ReporterConfig:
    values = {
        "api_url": "https://example.test/api",
        "api_key": "key",
        "project_id": "proj",
        "silent": True,
        "verbose": False,
        "max_retries": 3,
        "batch_size": 10,
    }
    values.update(overrides)
    return ReporterConfig(**values)  # type: ignore[arg-type]


def test_assign_result_ids_title_match_does_not_steal_used_slots():
    batch = [_result("A"), _result("B")]
    assign_result_ids(
        batch,
        [{"title": "B", "testResultId": "id-b"}, {"testResultId": "id-a"}],
    )

    assert batch[0].result_id == "id-a"
    assert batch[1].result_id == "id-b"


def test_assign_result_ids_skips_used_slots_when_counts_differ():
    batch = [_result("A"), _result("B")]
    assign_result_ids(
        batch,
        [{"title": "B", "testResultId": "id-b"}],
    )

    assert batch[0].result_id is None
    assert batch[1].result_id == "id-b"


def test_assign_result_ids_fills_unused_after_title_match():
    batch = [_result("A"), _result("B"), _result("C")]
    assign_result_ids(
        batch,
        [
            {"title": "B", "testResultId": "id-b"},
            {"title": "Other", "testResultId": "id-other"},
        ],
    )

    assert [result.result_id for result in batch] == ["id-other", "id-b", None]


def test_flush_keeps_failed_batches():
    plugin = QAStudioPlugin(_config())
    plugin.test_run_id = "run1"
    failed = _result("keep-me")
    plugin.pending_results = [failed]
    plugin.api_client.submit_test_results = Mock(side_effect=APIError(503, "unavailable"))

    plugin._flush_pending_results()

    assert plugin.pending_results == [failed]


def test_flush_clears_successful_batches():
    plugin = QAStudioPlugin(_config())
    plugin.test_run_id = "run1"
    result = _result("ok")
    plugin.pending_results = [result]
    plugin.api_client.submit_test_results = Mock(
        return_value={"results": [{"title": "ok", "testResultId": "tr1"}]}
    )

    plugin._flush_pending_results()

    assert plugin.pending_results == []
    assert result.result_id == "tr1"


def test_attachment_uploads_report_every_api_error():
    plugin = QAStudioPlugin(_config())
    result = _result("with-files")
    result.result_id = "tr1"
    result.attachment_paths = ["one.png", "two.png"]
    plugin.results = [result]
    plugin._handle_error = Mock()

    def fail(_result: TestResult, file_path: str) -> None:
        raise APIError(500, file_path)

    plugin._upload_one_attachment = fail  # type: ignore[method-assign]
    plugin._collect_and_upload_attachments()

    plugin._handle_error.assert_called_once()
    message, error = plugin._handle_error.call_args[0]
    assert message == "Attachment uploads failed"
    combined = str(error)
    assert "one.png" in combined
    assert "two.png" in combined


def test_submit_test_results_retries_transient_post_failures():
    client = QAStudioAPIClient(_config(max_retries=3))
    result = _result("ok")
    responses = [
        APIError(503, "unavailable"),
        APIError(500, "boom"),
        {"results": [{"testResultId": "tr1"}]},
    ]

    with patch.object(client, "_make_request", side_effect=responses) as request:
        with patch("qastudio_pytest.api_client.time.sleep"):
            payload = client.submit_test_results("run1", [result])

    assert payload == {"results": [{"testResultId": "tr1"}]}
    assert request.call_count == 3


def test_submit_test_results_does_not_retry_client_errors():
    client = QAStudioAPIClient(_config(max_retries=3))
    result = _result("ok")

    with patch.object(client, "_make_request", side_effect=APIError(400, "bad")) as request:
        with patch("qastudio_pytest.api_client.time.sleep"):
            try:
                client.submit_test_results("run1", [result])
            except APIError as exc:
                assert exc.status_code == 400
            else:
                raise AssertionError("expected APIError")

    assert request.call_count == 1
