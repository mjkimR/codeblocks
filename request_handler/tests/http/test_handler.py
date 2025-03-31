import pytest

from http_handler.handler import SyncHttpRequestHandler, AsyncHttpRequestHandler


@pytest.fixture
def sync_handler() -> SyncHttpRequestHandler:
    """Provides an instance of HttpRequestHandler for testing."""
    return SyncHttpRequestHandler(base_url="http://127.0.0.1:8000")


@pytest.fixture
async def async_handler() -> AsyncHttpRequestHandler:
    return AsyncHttpRequestHandler(base_url="http://127.0.0.1:8000")


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
async def test_sync_request_success(sync_handler: SyncHttpRequestHandler, method: str):
    """Tests successful synchronous requests against the test server."""
    kwargs = {}
    if method in ["POST", "PUT"]:
        kwargs["json"] = {"data": "payload"}
    elif method == "GET":
        kwargs["params"] = {"query": "param"}

    func = getattr(sync_handler, method.lower())
    response_body = func("/data", **kwargs)

    assert isinstance(response_body, dict)
    assert response_body["message"] == "success"
    assert response_body["method"] == method
    if method in ["POST", "PUT"]:
        assert response_body["received_data"] == kwargs["json"]


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
async def test_async_request_success(async_handler: AsyncHttpRequestHandler, method: str):
    """Tests successful asynchronous requests against the test server."""
    kwargs = {}
    if method in ["POST", "PUT"]:
        kwargs['json'] = {"data": "payload"}
    elif method == "GET":
        kwargs['params'] = {"query": "param"}

    func = getattr(async_handler, method.lower())
    response_body = await func("/data", **kwargs)

    assert isinstance(response_body, dict)
    assert response_body["message"] == "success"
    assert response_body["method"] == method
    if method in ["POST", "PUT"]:
        assert response_body["received_data"] == kwargs['json']
