from typing import Any, List
import httpx
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
import uvicorn
from ai_services.llm.llm_service import LLMService

# Initialize FastMCP server and LLM service
mcp = FastMCP("llm-tools")
llm_service = LLMService()

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

# Sample todos data
TODOS = [
    {"id": 1, "title": "Complete the MCP integration", "status": "in_progress"},
    {"id": 2, "title": "Write documentation", "status": "pending"},
    {"id": 3, "title": "Test the application", "status": "completed"},
    {"id": 4, "title": "Deploy to production", "status": "pending"},
    {"id": 5, "title": "Review pull requests", "status": "in_progress"}
]

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


@mcp.tool()
async def generate_text(prompt: str) -> str:
    """Generate text using the LLM service.

    Args:
        prompt: The prompt to generate text from
    """
    response = await llm_service.generate_response(prompt=prompt)
    if isinstance(response, dict) and "text" in response:
        return response["text"]
    return "Failed to generate response"


@mcp.tool()
async def analyze_workflow(workflow_id: int, historical_data: list[dict]) -> str:
    """Analyze workflow efficiency using LLM.

    Args:
        workflow_id: ID of the workflow to analyze
        historical_data: List of historical workflow data
    """
    response = await llm_service.analyze_workflow(workflow_id, historical_data)
    if isinstance(response, dict):
        return f"""
Efficiency Score: {response.get('efficiency_score', 0.0)}
Bottlenecks: {', '.join(response.get('bottlenecks', []))}
Recommendations: {', '.join(response.get('recommendations', []))}
"""
    return "Failed to analyze workflow"


@mcp.tool()
async def summarize_meeting(transcript: str, participants: list[str], duration: int) -> str:
    """Generate meeting summary using LLM.

    Args:
        transcript: Meeting transcript text
        participants: List of participant names
        duration: Meeting duration in minutes
    """
    response = await llm_service.summarize_meeting(transcript, participants, duration)
    if isinstance(response, dict):
        return f"""
Summary: {response.get('summary', '')}
Action Items: {', '.join(response.get('action_items', []))}
Key Points: {', '.join(response.get('key_points', []))}
"""
    return "Failed to summarize meeting"


@mcp.tool()
async def get_todos(status: str = None) -> str:
    """Get a list of todos, optionally filtered by status.

    Args:
        status: Filter todos by status (pending, in_progress, completed). If None, returns all todos.
    """
    filtered_todos = TODOS
    if status:
        filtered_todos = [todo for todo in TODOS if todo["status"] == status]
    
    if not filtered_todos:
        return "No todos found with the specified status."
    
    formatted_todos = []
    for todo in filtered_todos:
        formatted_todos.append(
            f"ID: {todo['id']}\n"
            f"Title: {todo['title']}\n"
            f"Status: {todo['status']}\n"
        )
    
    return "\n---\n".join(formatted_todos)


def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the provided mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


if __name__ == "__main__":
    mcp_server = mcp._mcp_server  # noqa: WPS437

    import argparse
    
    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8002, help='Port to listen on')
    args = parser.parse_args()

    # Bind SSE request handling to MCP server
    starlette_app = create_starlette_app(mcp_server, debug=True)

    uvicorn.run(starlette_app, host=args.host, port=args.port)