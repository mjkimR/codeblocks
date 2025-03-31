import pytest
import uvicorn
from multiprocessing import Process


@pytest.fixture(scope="session", autouse=True)
def start_test_server():
    """Starts the FastAPI test server."""
    process = Process(target=uvicorn.run, args=("mock_server:app",), kwargs={"host": "127.0.0.1", "port": 8000})
    process.start()
    yield
    process.terminate()
    process.join()
