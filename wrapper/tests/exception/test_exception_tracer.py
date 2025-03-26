import pytest

from src.exception.exception_tracer import exception_tracer


# Mock logger for testing
class MockLogger:
    def __init__(self):
        self.logs = []

    def error(self, message):
        self.logs.append(message)


def test_exception_tracer_without_exception():
    """Test case where no exception is raised."""
    with exception_tracer():
        assert True  # If no exception, pass the test.


def test_exception_tracer_with_exception_and_logging():
    """Test case where an exception is raised and logging is enabled."""
    mock_logger = MockLogger()
    with pytest.raises(ValueError):
        with exception_tracer(logger=mock_logger):
            raise ValueError("Test Exception")

    assert mock_logger.logs  # Logger should capture the error message.
    assert "ValueError" in mock_logger.logs[0]


def test_exception_tracer_with_disabled_flag():
    """Test case where an exception is raised and disabled is set to True."""
    with pytest.raises(ValueError, match="Test Exception"):
        with exception_tracer(disabled=True):
            raise ValueError("Test Exception")
