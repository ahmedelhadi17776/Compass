#!/usr/bin/env python3
import httpx
import asyncio
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Development JWT token for testing
DEV_JWT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjb21wYXNzLWFwaSIsInN1YiI6IjEiLCJleHAiOjE3NDE3OTcyMDAsIm5iZiI6MTcwOTQwNjQwMCwiaWF0IjoxNzA5NDA2NDAwLCJqdGkiOiJQNUNVcEE1dHBvRCIsInJvbGUiOiJhZG1pbiIsInNlc3Npb24iOiIifQ.Pu3UTvZo4AvkYGLq0XJwcfT6GTHx1dXiOgCvn-laTNBQp_cVi-gu--0DaGZcEwyjCcIBUFyj8KYo-03v6hv3fw"

# Define multiple backend URLs to try for Docker/non-Docker environments
GO_BACKEND_URLS = [
    # Docker service name (preferred for Docker environments)
    "http://api:8000",
    "http://backend_go-api-1:8000",      # Docker Compose auto-generated name
    "http://localhost:8000",             # Local development
    "http://127.0.0.1:8000",             # Local development alternative
]


async def try_backend_urls(client_func, endpoint: str, **kwargs):
    """Try to connect to multiple backend URLs in sequence."""
    errors = []
    # Increase timeout for Docker networking
    timeout = httpx.Timeout(10.0, connect=5.0)

    for base_url in GO_BACKEND_URLS:
        full_url = f"{base_url}{endpoint}"
        logger.info(f"Trying backend URL: {full_url}")

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                # Call the appropriate HTTP method function
                response = await client_func(client, full_url, **kwargs)
                response.raise_for_status()

                # If successful, log success
                logger.info(f"Successfully connected to backend at {base_url}")

                try:
                    return response.json(), base_url
                except Exception as json_error:
                    # Handle case where response isn't valid JSON
                    logger.warning(f"Response not JSON: {str(json_error)}")
                    return {"status": "success", "message": response.text}, base_url
        except httpx.ConnectError as e:
            # Connection errors are expected when trying different URLs
            logger.warning(f"Connection error to {base_url}: {str(e)}")
            errors.append({"url": base_url, "error": str(e),
                          "type": "connection_error"})
        except httpx.TimeoutException as e:
            # Timeout errors
            logger.warning(f"Timeout connecting to {base_url}: {str(e)}")
            errors.append(
                {"url": base_url, "error": str(e), "type": "timeout"})
        except httpx.HTTPStatusError as e:
            # HTTP status errors (4xx, 5xx)
            logger.warning(
                f"HTTP error from {base_url}: {e.response.status_code}")
            errors.append({"url": base_url, "error": f"HTTP {e.response.status_code}",
                          "type": "http_error", "status": e.response.status_code})
        except Exception as e:
            # Other unexpected errors
            logger.warning(f"Failed to connect to {base_url}: {str(e)}")
            errors.append(
                {"url": base_url, "error": str(e), "type": "unexpected"})

    # If we get here, all URLs failed
    error_msg = f"Failed to connect to any backend URL: {[e['url'] for e in errors]}"
    logger.error(error_msg)

    # Return a structured error response
    return {
        "status": "error",
        "error": error_msg,
        "type": "connection_error",
        "details": errors
    }, None


async def test_todo_lists():
    """Test getting todo lists from the Go backend."""
    async def get_func(client, url, **kwargs):
        return await client.get(url, **kwargs)

    # Request headers with JWT token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEV_JWT_TOKEN}"
    }

    result, working_url = await try_backend_urls(
        get_func,
        "/api/todo-lists",
        headers=headers
    )

    logger.info(f"Test result: {json.dumps(result, indent=2)}")
    if working_url:
        logger.info(f"Successfully connected to: {working_url}")
        return True
    else:
        logger.error("All connection attempts failed")
        return False


async def test_health():
    """Test the health endpoint of the Go backend."""
    async def get_func(client, url, **kwargs):
        return await client.get(url, **kwargs)

    result, working_url = await try_backend_urls(
        get_func,
        "/health",
    )

    logger.info(f"Health check result: {json.dumps(result, indent=2)}")
    if working_url:
        logger.info(
            f"Successfully connected to health endpoint at: {working_url}")
        return True
    else:
        logger.error("All health check attempts failed")
        return False


async def main():
    """Run all tests."""
    logger.info("Starting connection tests...")

    # Test health endpoint first
    health_ok = await test_health()
    if health_ok:
        logger.info("Health check successful!")
    else:
        logger.error("Health check failed!")

    # Test todo lists endpoint
    todos_ok = await test_todo_lists()
    if todos_ok:
        logger.info("Todo lists test successful!")
    else:
        logger.error("Todo lists test failed!")

    # Summary
    logger.info("Test Summary:")
    logger.info(f"- Health check: {'SUCCESS' if health_ok else 'FAILED'}")
    logger.info(f"- Todo lists: {'SUCCESS' if todos_ok else 'FAILED'}")

    if health_ok and not todos_ok:
        logger.info(
            "The backend is running (health check passed) but todo lists endpoint has authorization issues or is not implemented correctly.")
    elif not health_ok:
        logger.info(
            "The backend is not reachable at all. Check if the Go backend is running and network connectivity between containers.")

if __name__ == "__main__":
    asyncio.run(main())
