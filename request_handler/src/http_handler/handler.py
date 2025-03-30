import asyncio
from json import JSONDecodeError
import logging
import httpx
import time
import random
from typing import Optional, List, Dict, Any


class HttpRequestHandler:
    """
    Handles HTTP requests with features like automatic retries, timeouts,
    and connection pooling using httpx.
    Supports both synchronous and asynchronous requests.

    Remember to call close() or aclose() when done with the handler
    to clean up underlying client resources.
    """

    def __init__(
            self,
            base_url: str,
            max_retries: int = 3,
            min_retry_delay: float = 1.0,  # Base delay for exponential backoff
            max_retry_delay: float = 5.0,  # Maximum delay cap
            timeout: Optional[float] = 10.0,  # Default timeout for requests
            logger: Optional[logging.Logger] = None,
    ):
        """
        Initializes the HttpRequestHandler.

        Args:
            base_url: The base URL for all requests.
            max_retries: Maximum number of retries for failed requests.
            min_retry_delay: Minimum delay (and base for exponential backoff) between retries in seconds.
            max_retry_delay: Maximum delay between retries in seconds.
            timeout: Default request timeout in seconds.
            logger: Optional logger instance.
        """
        self.base_url = base_url.rstrip('/')  # Ensure no trailing slash
        self.max_retries = max_retries
        self.min_retry_delay = min_retry_delay
        self.max_retry_delay = max_retry_delay
        self.timeout = timeout
        self.logger = logger

        # Lazy-initialized clients
        self._client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None

    def _log(self, level: int, message: str, exc_info: bool = False):
        """Logs a message using the configured logger."""
        if self.logger:
            self.logger.log(level, message, exc_info=exc_info)

    def _get_client(self) -> httpx.Client:
        """Lazily initializes and returns the synchronous httpx client."""
        if self._client is None or self._client.is_closed:
            self._log(logging.DEBUG, "Initializing synchronous httpx client.")
            self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)
        return self._client

    def _get_async_client(self) -> httpx.AsyncClient:
        """Lazily initializes and returns the asynchronous httpx client."""
        if self._async_client is None or self._async_client.is_closed:
            self._log(logging.DEBUG, "Initializing asynchronous httpx client.")
            self._async_client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self._async_client

    def _prepare_request_kwargs(self, method: str, endpoint: str, json=None, params=None, headers=None, **kwargs) -> \
            Dict[str, Any]:
        """Prepares the keyword arguments for httpx's request method."""
        # URL is now relative, base_url is handled by the client
        relative_url = endpoint.lstrip('/')
        # Filter out None values to avoid overriding client defaults unintentionally
        request_kwargs = {
            "method": method,
            "url": relative_url,
            **kwargs,  # Include any other httpx request arguments
        }
        if json is not None:
            request_kwargs["json"] = json
        if params is not None:
            request_kwargs["params"] = params
        if headers is not None:
            request_kwargs["headers"] = headers
        # Note: timeout is primarily handled by the client, but can be overridden
        # if 'timeout' is present in kwargs.

        return request_kwargs

    def _handle_response(self, response: httpx.Response, is_json: bool):
        """Processes the HTTP response, raising errors or parsing JSON."""
        try:
            response.raise_for_status()  # Raise HTTPStatusError for 4xx/5xx responses
            if is_json:
                try:
                    return response.json()
                except JSONDecodeError as e:
                    self._log(logging.ERROR,
                              f"JSON decoding error: {e}. Response text: {response.text[:500]}...")  # Log snippet
                    raise ValueError(
                        f"JSON decoding error: {e}, Response content snippet: {response.text[:100]}") from e
            else:
                return response
        except httpx.HTTPStatusError as e:
            self._log(logging.WARNING,
                      f"HTTP error occurred: {e.response.status_code} {e.response.reason_phrase} for {e.request.url}")
            raise  # Re-raise after logging

    def _calculate_retry_delay(self, retry_count: int, error: Exception) -> Optional[float]:
        """
        Calculates the delay for the next retry attempt based on the error and retry count.
        Implements exponential backoff with jitter.

        Returns:
            Delay in seconds if a retry should be attempted, None otherwise.
        """
        should_retry = False
        status_code = -1  # Default invalid status code

        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            # Retry on 429 Too Many Requests or 5xx Server Errors
            if status_code == 429 or 500 <= status_code < 600:
                should_retry = True
        elif isinstance(error, (httpx.RequestError, httpx.TimeoutException)):
            # Includes ConnectError, ReadTimeout, PoolTimeout, etc.
            should_retry = True
        # Add other retryable exception types if needed here

        if should_retry and retry_count < self.max_retries:
            # Exponential backoff with jitter
            # delay = base * (2 ** retry_count) + random_jitter
            exponential_delay = self.min_retry_delay * (2 ** retry_count)
            # Add jitter: random fraction between 0 and min(exponential_delay, max_delay) * 0.5 (e.g., up to 50% jitter)
            # Ensure jitter calculation doesn't exceed max delay boundary significantly
            effective_max_for_jitter = min(exponential_delay, self.max_retry_delay)
            jitter = random.uniform(0, effective_max_for_jitter * 0.5)

            delay = min(exponential_delay + jitter, self.max_retry_delay)
            # Ensure delay respects min_retry_delay, especially at retry_count=0
            final_delay = max(delay, self.min_retry_delay)

            log_message = (
                f"Error encountered: {error}. Status code: {status_code if status_code != -1 else 'N/A'}. "
                f"Retrying in {final_delay:.2f} seconds ({retry_count + 1}/{self.max_retries})..."
            )
            self._log(logging.WARNING, log_message)
            return final_delay
        else:
            # Condition not met for retry or max retries exceeded
            if should_retry and retry_count >= self.max_retries:
                self._log(logging.ERROR,
                          f"Maximum retries ({self.max_retries}) exceeded for request. Last error: {error}")
            elif not should_retry:
                self._log(logging.WARNING, f"Non-retryable error encountered: {error}")
            return None

    def _request(self, method: str, endpoint: str, json=None, params=None, headers=None, is_json: bool = True,
                 **kwargs):
        """Makes a synchronous HTTP request with retry logic."""
        request_kwargs = self._prepare_request_kwargs(method, endpoint, json, params, headers, **kwargs)
        sync_client = self._get_client()
        retry_count = 0
        last_error: Optional[Exception] = None

        while retry_count <= self.max_retries:
            try:
                response = sync_client.request(**request_kwargs)
                return self._handle_response(response, is_json)
            except (
                    httpx.HTTPStatusError, httpx.RequestError,
                    ValueError) as e:  # Include ValueError for JSON decode issues
                last_error = e
                # ValueError from _handle_response should not be retried generally
                if isinstance(e, ValueError):
                    self._log(logging.ERROR, f"Data processing error: {e}", exc_info=True)
                    raise  # Non-retryable data error

                delay = self._calculate_retry_delay(retry_count, e)
                if delay is not None:
                    time.sleep(delay)
                    retry_count += 1
                else:
                    # No more retries (max reached or non-retryable error)
                    raise last_error  # Re-raise the specific error
            except Exception as e:  # Catch any other unexpected errors
                last_error = e
                self._log(logging.ERROR, f"An unexpected error occurred: {e}", exc_info=True)
                raise  # Unexpected errors are typically not retryable

        # This point should ideally not be reached if logic above is correct,
        # but as a safeguard:
        raise httpx.RequestError(f"Request failed after maximum retries ({self.max_retries}). Last error: {last_error}",
                                 request=request_kwargs)

    async def _async_request(self, method: str, endpoint: str, json=None, params=None, headers=None,
                             is_json: bool = True, **kwargs):
        """Makes an asynchronous HTTP request with retry logic."""
        request_kwargs = self._prepare_request_kwargs(method, endpoint, json, params, headers, **kwargs)
        async_client = self._get_async_client()
        retry_count = 0
        last_error: Optional[Exception] = None

        while retry_count <= self.max_retries:
            try:
                response = await async_client.request(**request_kwargs)
                # Pass the original response for handling, including potential JSON errors
                return self._handle_response(response, is_json)
            except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as e:  # Include ValueError
                last_error = e
                # ValueError from _handle_response should not be retried generally
                if isinstance(e, ValueError):
                    self._log(logging.ERROR, f"Data processing error: {e}", exc_info=True)
                    raise  # Non-retryable data error

                delay = self._calculate_retry_delay(retry_count, e)
                if delay is not None:
                    await asyncio.sleep(delay)  # Use asyncio.sleep for async
                    retry_count += 1
                else:
                    # No more retries (max reached or non-retryable error)
                    raise last_error  # Re-raise the specific error
            except Exception as e:  # Catch any other unexpected errors
                last_error = e
                self._log(logging.ERROR, f"An unexpected error occurred: {e}", exc_info=True)
                raise  # Unexpected errors are typically not retryable

        # Safeguard raise
        raise httpx.RequestError(f"Request failed after maximum retries ({self.max_retries}). Last error: {last_error}",
                                 request=request_kwargs)

    # --- Convenience Methods ---
    def get(self, endpoint: str, params=None, headers=None, **kwargs):
        return self._request("GET", endpoint, params=params, headers=headers, **kwargs)

    def post(self, endpoint: str, json=None, headers=None, **kwargs):
        return self._request("POST", endpoint, json=json, headers=headers, **kwargs)

    def put(self, endpoint: str, json=None, headers=None, **kwargs):
        return self._request("PUT", endpoint, json=json, headers=headers, **kwargs)

    def delete(self, endpoint: str, headers=None, **kwargs):
        return self._request("DELETE", endpoint, headers=headers, **kwargs)

    async def aget(self, endpoint: str, params=None, headers=None, **kwargs):
        return await self._async_request("GET", endpoint, params=params, headers=headers, **kwargs)

    async def apost(self, endpoint: str, json=None, headers=None, **kwargs):
        return await self._async_request("POST", endpoint, json=json, headers=headers, **kwargs)

    async def aput(self, endpoint: str, json=None, headers=None, **kwargs):
        return await self._async_request("PUT", endpoint, json=json, headers=headers, **kwargs)

    async def adelete(self, endpoint: str, headers=None, **kwargs):
        return await self._async_request("DELETE", endpoint, headers=headers, **kwargs)

    # --- Parallel Execution ---
    def parallel_requests(self, requests: List[Dict[str, Any]], is_json: bool = True):
        """
        Executes multiple HTTP requests concurrently using an async event loop.
        WARNING: This uses asyncio.run() and may not work if called from an already
                 running asyncio event loop.

        Args:
            requests: A list of request dictionaries. Each dictionary should contain
                      parameters like 'method', 'endpoint', 'json', 'params', 'headers'.
            is_json: Whether to parse response content as JSON. Default is True.

        Returns:
            A list containing results or Exception objects for each request,
            corresponding to the order of the input requests.
        """
        self._log(logging.INFO, f"Starting {len(requests)} parallel synchronous requests (via asyncio.run).")
        # Ensure the async client is potentially initialized before running the loop
        _ = self._get_async_client()
        try:
            # Note: asyncio.run creates a new event loop
            return asyncio.run(self.parallel_async_requests(requests, is_json))
        except RuntimeError as e:
            self._log(logging.ERROR, f"RuntimeError in parallel_requests (potentially nested event loops): {e}")
            raise

    async def _raise_value_error(self, message: str):
        """Helper coroutine to raise ValueError, for use with asyncio.gather."""
        raise ValueError(message)

    async def parallel_async_requests(self, requests: List[Dict[str, Any]], is_json: bool = True):
        """
        Executes multiple HTTP requests concurrently using asyncio.gather.

        Args:
            requests: A list of request dictionaries (keys: 'method', 'endpoint', etc.).
            is_json: Whether to parse response content as JSON. Default is True.

        Returns:
            A list containing results or Exception objects for each request,
            corresponding to the order of the input requests.
        """
        self._log(logging.INFO, f"Starting {len(requests)} parallel asynchronous requests.")
        tasks = []
        for i, req in enumerate(requests):
            method = req.get('method')
            endpoint = req.get('endpoint')

            if not method or not endpoint:
                error_msg = f"Request {i}: 'method' and 'endpoint' are required."
                self._log(logging.ERROR, error_msg)
                # Schedule a coroutine that will raise the error
                tasks.append(self._raise_value_error(error_msg))
                continue

            # Extract known args for _async_request and pass the rest as kwargs
            known_args = {'json', 'params', 'headers'}
            request_params = {k: v for k, v in req.items() if k in known_args}
            other_kwargs = {k: v for k, v in req.items() if k not in ['method', 'endpoint', *known_args]}

            tasks.append(
                self._async_request(
                    method=method,
                    endpoint=endpoint,
                    is_json=is_json,
                    **request_params,
                    **other_kwargs
                )
            )

        # return_exceptions=True ensures all tasks complete and exceptions are returned as results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        self._log(logging.INFO, f"Finished {len(requests)} parallel asynchronous requests.")
        return results

    # --- Resource Cleanup ---
    def close(self):
        """Closes the underlying synchronous httpx client, releasing resources."""
        if self._client and not self._client.is_closed:
            try:
                self._client.close()
                self._log(logging.INFO, "Synchronous HTTP client closed.")
            except Exception as e:
                self._log(logging.ERROR, f"Error closing synchronous client: {e}", exc_info=True)
        self._client = None

    async def aclose(self):
        """Closes the underlying asynchronous httpx client, releasing resources."""
        if self._async_client and not self._async_client.is_closed:
            try:
                await self._async_client.aclose()
                self._log(logging.INFO, "Asynchronous HTTP client closed.")
            except Exception as e:
                self._log(logging.ERROR, f"Error closing asynchronous client: {e}", exc_info=True)
        self._async_client = None
