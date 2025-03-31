import asyncio
import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, Response, HTTPException, status, Request, Body

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.ERROR)

app = FastAPI(title="Test Server for HttpRequestHandler")

# --- State for simulating transient errors (optional) ---
# Simple counter to simulate temporary issues like 429 or 503
request_counts = {"/data_retry": 0}


@app.get("/")
async def read_root():
    """Root endpoint for basic connectivity check."""
    return {"message": "Test server is running"}


async def handle_data_request(
        request: Request,
        error: Optional[int] = None,
        delay: Optional[float] = None,
        return_text: bool = False,
        data: Optional[Dict[str, Any]] = None  # Accept body for POST/PUT
):
    """Handles logic for /data endpoint based on query params."""
    method = request.method
    logger.info(f"Received {method} request to /data")
    logger.info(f"Query params: error={error}, delay={delay}, return_text={return_text}")
    if data:
        logger.info(f"Request body: {data}")

    # --- Simulate Delay ---
    if delay is not None and delay > 0:
        logger.info(f"Simulating delay of {delay} seconds...")
        await asyncio.sleep(delay)

    # --- Simulate Errors ---
    if error is not None:
        logger.warning(f"Simulating error response: status_code={error}")
        if error == status.HTTP_400_BAD_REQUEST:
            raise HTTPException(status_code=error, detail="Simulated Bad Request")
        elif error == status.HTTP_404_NOT_FOUND:
            raise HTTPException(status_code=error, detail="Simulated Not Found")
        elif error == status.HTTP_429_TOO_MANY_REQUESTS:
            raise HTTPException(status_code=error, detail="Simulated Too Many Requests")
        elif status.HTTP_500_INTERNAL_SERVER_ERROR <= error < 600:
            raise HTTPException(status_code=error, detail=f"Simulated Server Error {error}")
        else:
            # Generic error for other codes
            raise HTTPException(status_code=error, detail=f"Simulated Error {error}")

    # --- Simulate Non-JSON Response ---
    if return_text:
        logger.info("Returning plain text response.")
        return Response(content="This is plain text", media_type="text/plain", status_code=status.HTTP_200_OK)

    # --- Default Success Response ---
    success_payload = {"message": "success", "method": method}
    if data:
        success_payload["received_data"] = data  # Echo back received data
    return success_payload


@app.get("/data", status_code=status.HTTP_200_OK)
async def get_data(request: Request, error: Optional[int] = None, delay: Optional[float] = None,
                   return_text: bool = False):
    return await handle_data_request(request, error=error, delay=delay, return_text=return_text)


@app.post("/data", status_code=status.HTTP_201_CREATED)
async def post_data(request: Request, error: Optional[int] = None, delay: Optional[float] = None,
                    return_text: bool = False, data: Optional[Dict[str, Any]] = Body(None)):
    return await handle_data_request(request, error=error, delay=delay, return_text=return_text, data=data)


@app.put("/data", status_code=status.HTTP_201_CREATED)
async def put_data(request: Request, error: Optional[int] = None, delay: Optional[float] = None,
                   return_text: bool = False, data: Optional[Dict[str, Any]] = Body(None)):
    return await handle_data_request(request, error=error, delay=delay, return_text=return_text, data=data)


@app.delete("/data", status_code=status.HTTP_200_OK)
async def delete_data(request: Request, error: Optional[int] = None, delay: Optional[float] = None,
                      return_text: bool = False):
    return await handle_data_request(request, error=error, delay=delay, return_text=return_text)


# --- Endpoint for Retry Simulation ---
@app.get("/data_retry")
async def get_data_with_retry_simulation():
    """Simulates an endpoint that fails twice then succeeds."""
    endpoint = "/data_retry"
    request_counts[endpoint] += 1
    count = request_counts[endpoint]

    logger.info(f"Request {count} to {endpoint}")

    if count <= 2:  # Fail first two times
        logger.warning(f"Simulating 503 error for request {count}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service temporarily unavailable")
    else:
        logger.info(f"Returning success for request {count}")
        request_counts[endpoint] = 0
        return {"message": "success after retries", "attempt": count}


# --- Simple Endpoints for Parallel Tests ---
@app.get("/req1")
async def get_req1():
    logger.info("Request received for /req1")
    return {"id": 1, "data": "Response from /req1"}


@app.post("/req2")
async def post_req2(data: Optional[Dict[str, Any]] = Body(None)):
    logger.info(f"Request received for /req2 with data: {data}")
    return {"id": 2, "status": "Created resource from /req2", "received": data}


@app.get("/req3")
async def get_req3():
    # Simulate an endpoint that might fail sometimes (e.g., for parallel mixed test)
    # Keep it simple for now, return success. Errors can be tested via /data?error=...
    logger.info("Request received for /req3")
    return {"id": 3, "info": "Response from /req3"}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting test server on http://127.0.0.1:8000")
    uvicorn.run("mock_server:app", host="127.0.0.1", port=8000)
