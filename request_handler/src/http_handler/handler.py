import asyncio
from json import JSONDecodeError
import logging
import httpx
import time
import random
from typing import Optional, List, Dict, Any


class BaseHttpRequestHandler:
    def __init__(
            self,
            base_url: str,
            max_retries: int = 3,
            min_retry_delay: float = 1.0,  # Base delay for exponential backoff
            max_retry_delay: float = 5.0,  # Maximum delay cap
            timeout: Optional[float] = 10.0,  # Default timeout for requests
            retryable_status_codes: Optional[List[int]] = None,  # List of status codes to retry
            logger: Optional[logging.Logger] = None,
    ):
        self.base_url = base_url.rstrip('/')
        self.max_retries = max_retries
        self.min_retry_delay = min_retry_delay
        self.max_retry_delay = max_retry_delay
        self.timeout = timeout
        self.logger = logger
        self.retryable_status_codes = retryable_status_codes or {429, 500, 502, 503, 504}

    def _log(self, level: int, message: str, exc_info: bool = False):
        """Logs a message using the configured logger."""
        if self.logger:
            self.logger.log(level, message, exc_info=exc_info)

    def _prepare_request_kwargs(self, method: str, endpoint: str, json=None, params=None, headers=None, **kwargs) -> \
            Dict[str, Any]:
        """Prepares the keyword arguments for httpx's request method."""
        # URL is now relative, base_url is handled by the client
        relative_url = endpoint.lstrip('/')
        # Filter out None values to avoid overriding client defaults unintentionally
        request_kwargs = {
            "method": method,
            "url": relative_url,
            **kwargs,
        }
        if json is not None:
            request_kwargs["json"] = json
        if params is not None:
            request_kwargs["params"] = params
        if headers is not None:
            request_kwargs["headers"] = headers
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
                              f"JSON decoding error: {e}. Response text: {response.text[:100]}...")  # Log snippet
                    raise ValueError(
                        f"JSON decoding error: {e}, Response content snippet: {response.text[:100]}...") from e
            else:
                return response
        except httpx.HTTPStatusError as e:
            self._log(
                logging.ERROR,
                f"HTTP error occurred: {e.response.status_code} {e.response.reason_phrase} for {e.request.url}"
            )
            raise  # Re-raise after logging

    def _calculate_retry_delay(self, retry_count: int, error: Exception) -> Optional[float]:
        """
        Calculates the delay for the next retry attempt based on the error and retry count.
        Implements exponential backoff.

        Returns:
            Delay in seconds if a retry should be attempted, None otherwise.
        """
        should_retry = False
        status_code = -1  # Default invalid status code

        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            if status_code in self.retryable_status_codes:  # 수정된 부분
                should_retry = True
        elif isinstance(error, (httpx.RequestError, httpx.TimeoutException)):
            # Includes ConnectError, ReadTimeout, PoolTimeout, etc.
            should_retry = True
        # Add other retryable exception types if needed here

        if should_retry and retry_count < self.max_retries:
            # Exponential backoff with jitter
            base_delay = min(self.min_retry_delay * (2 ** retry_count), self.max_retry_delay)
            jitter = random.uniform(0, base_delay * 0.3)
            delay = base_delay + jitter
            delay = min(delay, self.max_retry_delay)
            self._log(logging.WARNING,
                      f"Error encountered: {error}. Status code: {status_code if status_code != -1 else 'N/A'}. "
                      f"Retrying in {delay:.2f} seconds ({retry_count + 1}/{self.max_retries})...")
            return delay
        else:
            # Condition not met for retry or max retries exceeded
            if should_retry and retry_count >= self.max_retries:
                self._log(logging.ERROR,
                          f"Maximum retries ({self.max_retries}) exceeded for request. Last error: {error}")
            elif not should_retry:
                self._log(logging.WARNING, f"Non-retryable error encountered: {error}")
            return None

    async def _raise_value_error(self, message: str):
        """Helper coroutine to raise ValueError, for use with asyncio.gather."""
        raise ValueError(message)


class SyncHttpRequestHandler(BaseHttpRequestHandler):
    """
    Synchronous HTTP request handler using httpx.
    Provides methods for GET, POST, PUT, DELETE requests with retry logic.
    Supports connection pooling and timeout management.
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
        super().__init__(base_url, max_retries, min_retry_delay, max_retry_delay, timeout, logger)
        self.client = httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _request(self, method: str, endpoint: str, json=None, params=None, headers=None, is_json: bool = True,
                 **kwargs):
        """Makes a synchronous HTTP request with retry logic."""
        request_kwargs = self._prepare_request_kwargs(method, endpoint, json, params, headers, **kwargs)
        sync_client = self.client
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

    # --- Convenience Methods ---
    def get(self, endpoint: str, params=None, headers=None, **kwargs):
        return self._request("GET", endpoint, params=params, headers=headers, **kwargs)

    def post(self, endpoint: str, json=None, headers=None, **kwargs):
        return self._request("POST", endpoint, json=json, headers=headers, **kwargs)

    def put(self, endpoint: str, json=None, headers=None, **kwargs):
        return self._request("PUT", endpoint, json=json, headers=headers, **kwargs)

    def delete(self, endpoint: str, headers=None, **kwargs):
        return self._request("DELETE", endpoint, headers=headers, **kwargs)

    def parallel_requests(self, requests: List[Dict[str, Any]], is_json: bool = True, max_workers=5):
        """
        Executes multiple HTTP requests concurrently using ThreadPoolExecutor.

        Args:
            requests: A list of request dictionaries (keys: 'method', 'endpoint', etc.).
            is_json: Whether to parse response content as JSON. Default is True.
            max_workers: Number of threads to use for parallel requests. Default is 5.
        Returns:
            A list containing results or Exception objects for each request,
            corresponding to the order of the input requests.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = [None] * len(requests)
        futures_map = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:  # max_workers 설정 필요
            for i, req in enumerate(requests):
                future = executor.submit(
                    self._request,
                    method=req.get('method'),
                    endpoint=req.get('endpoint'),
                    json=req.get('json'),
                    params=req.get('params'),
                    headers=req.get('headers'),
                    is_json=is_json,
                    **{k: v for k, v in req.items() if k not in ['method', 'endpoint', 'json', 'params', 'headers']}
                )
                futures_map[future] = i

            for future in as_completed(futures_map):
                index = futures_map[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    self._log(logging.ERROR, f"Error in parallel request {index}: {e}", exc_info=True)
                    results[index] = e  # 오류를 결과 리스트에 저장
        return results

    # --- Resource Cleanup ---
    def close(self):
        """Closes the underlying synchronous httpx client, releasing resources."""
        if self.client and not self.client.is_closed:
            try:
                self.client.close()
                self._log(logging.INFO, "Synchronous HTTP client closed.")
            except Exception as e:
                self._log(logging.ERROR, f"Error closing synchronous client: {e}", exc_info=True)
        self.client = None


class AsyncHttpRequestHandler(BaseHttpRequestHandler):
    """
    Asynchronous HTTP request handler using httpx.
    Provides methods for GET, POST, PUT, DELETE requests with retry logic.
    Supports connection pooling and timeout management.
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
        super().__init__(base_url, max_retries, min_retry_delay, max_retry_delay, timeout, logger)
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _async_request(self, method: str, endpoint: str, json=None, params=None, headers=None,
                             is_json: bool = True, **kwargs):
        """Makes an asynchronous HTTP request with retry logic."""
        request_kwargs = self._prepare_request_kwargs(method, endpoint, json, params, headers, **kwargs)
        client = self.client
        retry_count = 0
        last_error: Optional[Exception] = None

        while retry_count <= self.max_retries:
            try:
                response = await client.request(**request_kwargs)
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
    async def get(self, endpoint: str, params=None, headers=None, **kwargs):
        return await self._async_request("GET", endpoint, params=params, headers=headers, **kwargs)

    async def post(self, endpoint: str, json=None, headers=None, **kwargs):
        return await self._async_request("POST", endpoint, json=json, headers=headers, **kwargs)

    async def put(self, endpoint: str, json=None, headers=None, **kwargs):
        return await self._async_request("PUT", endpoint, json=json, headers=headers, **kwargs)

    async def delete(self, endpoint: str, headers=None, **kwargs):
        return await self._async_request("DELETE", endpoint, headers=headers, **kwargs)

    async def parallel_requests(self, requests: List[Dict[str, Any]], is_json: bool = True):
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
    async def close(self):
        """Closes the underlying asynchronous httpx client, releasing resources."""
        if self.client and not self.client.is_closed:
            try:
                await self.client.aclose()
                self._log(logging.INFO, "Asynchronous HTTP client closed.")
            except Exception as e:
                self._log(logging.ERROR, f"Error closing asynchronous client: {e}", exc_info=True)
        self.client = None
