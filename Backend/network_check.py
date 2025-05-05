#!/usr/bin/env python3
import httpx
import asyncio
import sys

# JWT token for testing - this is a development token
DEV_JWT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjb21wYXNzLWFwaSIsInN1YiI6IjEiLCJleHAiOjE3NDE3OTcyMDAsIm5iZiI6MTcwOTQwNjQwMCwiaWF0IjoxNzA5NDA2NDAwLCJqdGkiOiJQNUNVcEE1dHBvRCIsInJvbGUiOiJhZG1pbiIsInNlc3Npb24iOiIifQ.Pu3UTvZo4AvkYGLq0XJwcfT6GTHx1dXiOgCvn-laTNBQp_cVi-gu--0DaGZcEwyjCcIBUFyj8KYo-03v6hv3fw"


async def check_health_endpoints():
    """Test connectivity to the Go API backend health endpoints."""
    urls_to_test = [
        "http://127.0.0.1:8000/health",
        "http://localhost:8000/health",
        "http://api:8000/health",
        "http://backend_go-api-1:8000/health"
    ]

    print(f"Testing connectivity to Go backend health endpoints...")

    results = []
    for url in urls_to_test:
        try:
            print(f"Trying URL: {url}")
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                results.append({
                    "url": url,
                    "status": response.status_code,
                    "response": response.text,
                    "success": True
                })
                print(
                    f"  SUCCESS! Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            results.append({
                "url": url,
                "error": str(e),
                "success": False
            })
            print(f"  FAILED! Error: {str(e)}")

    # Print summary
    print("\nHealth endpoints test summary:")
    success_count = sum(1 for r in results if r.get("success", False))
    print(
        f"- Successfully connected to {success_count} of {len(urls_to_test)} health endpoints")

    # Return working URLs for further testing
    return [r["url"].replace("/health", "") for r in results if r.get("success", False)]


async def check_todo_lists_endpoints(base_urls):
    """Test the todo-lists endpoint with proper authorization."""
    if not base_urls:
        print("\nNo working base URLs found. Cannot test todo-lists endpoints.")
        return

    print(f"\nTesting todo-lists endpoints with proper authorization...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEV_JWT_TOKEN}"
    }

    results = []
    for base_url in base_urls:
        todo_url = f"{base_url}/api/todo-lists"
        try:
            print(f"Trying todo-lists URL: {todo_url}")
            print(
                f"Using authorization header: Bearer {DEV_JWT_TOKEN[:20]}...")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(todo_url, headers=headers)
                results.append({
                    "url": todo_url,
                    "status": response.status_code,
                    "response": response.text,
                    "success": response.status_code < 400
                })
                print(f"  Response status: {response.status_code}")
                print(f"  Response body: {response.text}")
        except Exception as e:
            results.append({
                "url": todo_url,
                "error": str(e),
                "success": False
            })
            print(f"  FAILED! Error: {str(e)}")

    # Print summary
    print("\nTodo-lists endpoints test summary:")
    success_count = sum(1 for r in results if r.get("success", False))
    print(
        f"- Successfully accessed {success_count} of {len(results)} todo-lists endpoints")

    if success_count == 0:
        print("- All requests to todo-lists endpoints failed")
        print("- Common issues:")
        print("  1. Invalid or expired JWT token")
        print("  2. Authorization issues in the Go backend")
        print("  3. Todo-lists endpoint not properly implemented or has different path")
    else:
        print("- Successfully accessed at least one todo-lists endpoint")
        working_urls = [r["url"] for r in results if r.get("success", False)]
        print(f"- Working endpoints: {', '.join(working_urls)}")


async def main():
    """Main function to run all tests."""
    working_base_urls = await check_health_endpoints()
    await check_todo_lists_endpoints(working_base_urls)

if __name__ == "__main__":
    asyncio.run(main())
