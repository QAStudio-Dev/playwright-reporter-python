"""API client for QAStudio.dev integration."""

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
                json_response: Dict[str, Any] = response.json()
                return json_response
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

        response = self._make_request("POST", "/runs", json_data=data)

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

        response = self._make_request("POST", "/results", json_data=data)

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

        response = self._make_request("POST", f"/runs/{test_run_id}/complete", json_data=data)

        self._log("Test run completed successfully")
        return response

    def upload_attachment(
        self,
        test_result_id: str,
        file_path: str,
        attachment_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload an attachment file to a test result.

        Args:
            test_result_id: Test result ID to attach file to
            file_path: Path to file to upload
            attachment_type: Optional type (e.g., 'screenshot', 'video', 'log')

        Returns:
            Response data with attachment info

        Raises:
            APIError: If upload fails
        """
        import os
        import mimetypes

        if not os.path.exists(file_path):
            raise APIError(400, f"File not found: {file_path}")

        filename = os.path.basename(file_path)
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        self._log(f"Uploading attachment: {filename} ({content_type})")

        with open(file_path, "rb") as f:
            file_data = f.read()

        # Prepare multipart form data
        fields = {
            "testResultId": test_result_id,
        }

        if attachment_type:
            fields["type"] = attachment_type

        return self._upload_multipart("/attachments", fields, filename, content_type, file_data)

    def _upload_multipart(
        self,
        path: str,
        fields: Dict[str, str],
        filename: str,
        content_type: str,
        file_data: bytes,
    ) -> Dict[str, Any]:
        """
        Upload multipart/form-data request with retry logic.

        Args:
            path: API endpoint path
            fields: Form fields
            filename: Name of file being uploaded
            content_type: MIME type of file
            file_data: File content as bytes

        Returns:
            Response JSON data

        Raises:
            APIError: If request fails
        """
        url = f"{self.base_url}{path}"
        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries):
            try:
                if attempt > 0:
                    self._log(f"Retry attempt {attempt + 1}/{self.config.max_retries}")
                    import time

                    time.sleep(min(1 * (2**attempt), 10))  # Exponential backoff

                return self._make_multipart_request(url, fields, filename, content_type, file_data)

            except APIError as e:
                last_error = e
                self._log(f"Upload failed (attempt {attempt + 1}/{self.config.max_retries}): {e}")

                # Don't retry on 4xx errors (client errors)
                if 400 <= e.status_code < 500:
                    raise

            except Exception as e:
                last_error = e
                self._log(f"Upload failed (attempt {attempt + 1}/{self.config.max_retries}): {e}")

        if last_error:
            raise last_error
        raise APIError(500, "Upload failed after all retries")

    def _make_multipart_request(
        self,
        url: str,
        fields: Dict[str, str],
        filename: str,
        content_type: str,
        file_data: bytes,
    ) -> Dict[str, Any]:
        """
        Make a multipart/form-data HTTP request.

        Args:
            url: Full URL to request
            fields: Form fields (non-file)
            filename: Name of file being uploaded
            content_type: MIME type of file
            file_data: File content as bytes

        Returns:
            Response JSON data

        Raises:
            APIError: If request fails
        """
        import uuid

        # Generate boundary
        boundary = f"----FormBoundary{uuid.uuid4().hex}"

        # Build multipart body
        body_parts = []

        # Add form fields
        for key, value in fields.items():
            body_parts.append(f"--{boundary}\r\n".encode())
            body_parts.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
            body_parts.append(f"{value}\r\n".encode())

        # Add file field
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode()
        )
        body_parts.append(f"Content-Type: {content_type}\r\n\r\n".encode())
        body_parts.append(file_data)
        body_parts.append(b"\r\n")

        # Add closing boundary
        body_parts.append(f"--{boundary}--\r\n".encode())

        body = b"".join(body_parts)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "qastudio-pytest/1.0.0",
        }

        try:
            response = self.session.request(
                method="POST",
                url=url,
                data=body,
                headers=headers,
                timeout=self.config.timeout,
            )

            # Raise for 4xx/5xx status codes
            if not response.ok:
                error_msg = response.text or response.reason
                raise APIError(response.status_code, error_msg)

            # Return JSON if present
            if response.content:
                json_response: Dict[str, Any] = response.json()
                return json_response
            return {}

        except requests.exceptions.Timeout as e:
            raise APIError(408, f"Request timeout: {str(e)}")
        except requests.exceptions.ConnectionError as e:
            raise APIError(503, f"Connection error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise APIError(500, f"Request failed: {str(e)}")

    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.config.verbose:
            print(f"[QAStudio] {message}")

    def close(self) -> None:
        """Close the session."""
        self.session.close()
