import pytest
import json

from exception.exception_handler import exception_handler


# Mock logger for testing
class MockLogger:
    def __init__(self):
        self.logs = []

    def error(self, message):
        print(message)
        self.logs.append(message)


def test_exception_handler_file_not_found():
    logger = MockLogger()
    with pytest.raises(FileNotFoundError):
        with exception_handler(file_name="test.txt", logger=logger):
            raise FileNotFoundError("File not found")


def test_exception_handler_json_decode_error():
    logger = MockLogger()
    with pytest.raises(json.JSONDecodeError):
        invalid = '{"aa":b}'
        with exception_handler(data=invalid, logger=logger):
            json.loads(invalid)


def test_exception_handler_generic_exception():
    logger = MockLogger()
    with pytest.raises(Exception):
        with exception_handler(context="example", logger=logger):
            raise Exception("Generic error")
