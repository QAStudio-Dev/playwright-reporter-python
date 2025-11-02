"""
Example test file showing different ways to use QAStudio pytest plugin.
"""

import pytest


# Example 1: Using qastudio_id marker
@pytest.mark.qastudio_id("QA-123")
def test_login_with_marker():
    """Test user login functionality."""
    # Your test code here
    assert True


# Example 2: Using test ID in test name
def test_QA124_registration():
    """Test user registration."""
    assert True


# Example 3: Using docstring
def test_password_reset():
    """
    Test password reset functionality.

    QAStudio ID: QA-125
    """
    assert True


# Example 4: With additional metadata
@pytest.mark.qastudio_id("QA-126")
@pytest.mark.qastudio_priority("high")
@pytest.mark.qastudio_tags("smoke", "authentication")
def test_important_feature():
    """Critical authentication test."""
    assert True


# Example 5: Parametrized test
@pytest.mark.qastudio_id("QA-127")
@pytest.mark.parametrize(
    "username,password",
    [
        ("user1", "pass1"),
        ("user2", "pass2"),
        ("user3", "pass3"),
    ],
)
def test_login_with_different_users(username, password):
    """Test login with various user credentials."""
    assert len(username) > 0
    assert len(password) > 0


# Example 6: Test class
class TestUserManagement:
    """User management test suite."""

    @pytest.mark.qastudio_id("QA-128")
    def test_create_user(self):
        """Test user creation."""
        assert True

    @pytest.mark.qastudio_id("QA-129")
    def test_update_user(self):
        """Test user update."""
        assert True

    @pytest.mark.qastudio_id("QA-130")
    def test_delete_user(self):
        """Test user deletion."""
        assert True


# Example 7: Skipped test
@pytest.mark.qastudio_id("QA-131")
@pytest.mark.skip(reason="Feature not implemented yet")
def test_future_feature():
    """Test for future feature."""
    pass


# Example 8: Failing test (for demonstration)
@pytest.mark.qastudio_id("QA-132")
def test_failing_example():
    """Example of a failing test."""
    assert False, "This is an intentional failure for demonstration"


# Example 9: Test with fixture
@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return {"user": "testuser", "email": "test@example.com"}


@pytest.mark.qastudio_id("QA-133")
def test_with_fixture(sample_data):
    """Test using a fixture."""
    assert sample_data["user"] == "testuser"
    assert "@" in sample_data["email"]


# Example 10: Test without QAStudio ID
def test_without_qastudio_id():
    """This test won't be linked to any QAStudio test case."""
    assert 1 + 1 == 2
