"""API client for QAStudio.dev integration."""

import time
from typing import Any, Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import ReporterConfig, TestResult, TestRunSummary
from .utils import sanitize_string


class APIError(Exception):
    """Custom exception for API errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"API Error {status_code}: {message}")


class QAStudioAPIClient:
    """Client for communicating with QAStudio.dev API."""

    def __init__(self, config: ReporterConfig):
        """Initialize API client with configuration."""
        self.config = config
        self.session = self._create_session()
        self.base_url = sanitize_string(config.api_url) or ""
        self.api_key = sanitize_string(config.api_key) or ""
        self.project_id = sanitize_string(config.project_id) or ""

    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _make_request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API with error handling.

        Args:
            method: HTTP method
            path: API endpoint path
            json_data: JSON data to send

        Returns:
            Response JSON data

        Raises:
            APIError: If request fails
        """
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "qastudio-pytest/1.0.0",
        }

        try:
            self._log(f"Making {method} request to {path}")

            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                headers=headers,
                timeout=self.config.timeout,
            )

            # Raise for 4xx/5xx status codes
            if not response.ok:
                error_msg = response.text or response.reason
                raise APIError(response.status_code, error_msg)

            # Return JSON if present
            if response.content:
                return response.json()
            return {}

        except requests.exceptions.Timeout as e:
            raise APIError(408, f"Request timeout: {str(e)}")
        except requests.exceptions.ConnectionError as e:
            raise APIError(503, f"Connection error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise APIError(500, f"Request failed: {str(e)}")

    def create_test_run(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new test run.

        Args:
            name: Test run name
            description: Optional description

        Returns:
            Test run data with 'id' field
        """
        self._log(f"Creating test run: {name}")

        data = {
            "projectId": self.project_id,
            "name": name,
            "environment": self.config.environment,
        }

        if description:
            data["description"] = description

        response = self._make_request("POST", "/test-runs", json_data=data)

        self._log(f"Created test run with ID: {response.get('id')}")
        return response

    def submit_test_results(
        self,
        test_run_id: str,
        results: List[TestResult],
    ) -> Dict[str, Any]:
        """
        Submit test results to a test run.

        Args:
            test_run_id: Test run ID
            results: List of test results

        Returns:
            Response data
        """
        self._log(f"Submitting {len(results)} test results to run {test_run_id}")

        data = {
            "testRunId": test_run_id,
            "results": [result.to_dict() for result in results],
        }

        response = self._make_request(
            "POST",
            f"/test-runs/{test_run_id}/results",
            json_data=data,
        )

        self._log(f"Successfully submitted {len(results)} results")
        return response

    def complete_test_run(
        self,
        test_run_id: str,
        summary: TestRunSummary,
    ) -> Dict[str, Any]:
        """
        Mark test run as complete with summary.

        Args:
            test_run_id: Test run ID
            summary: Test run summary

        Returns:
            Response data
        """
        self._log(f"Completing test run {test_run_id}")

        data = {
            "testRunId": test_run_id,
            "summary": summary.to_dict(),
        }

        response = self._make_request(
            "POST",
            f"/test-runs/{test_run_id}/complete",
            json_data=data,
        )

        self._log("Test run completed successfully")
        return response

    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.config.verbose:
            print(f"[QAStudio] {message}")

    def close(self) -> None:
        """Close the session."""
        self.session.close()
