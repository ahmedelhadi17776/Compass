"""Session middleware for FastAPI."""
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..data.database.connection import get_db
from ..services.authentication import AuthenticationService
from ..dependencies import get_auth_service

def setup_session_middleware(app: FastAPI) -> None:
    """Set up session middleware."""
    
    @app.middleware("http")
    async def session_middleware(request: Request, call_next: Callable) -> Response:
        """Validate session token and update session data."""
        try:
            # Skip session validation for authentication endpoints
            if request.url.path.startswith("/api/auth"):
                return await call_next(request)
            
            # Get authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return await call_next(request)
            
            # Get session token
            session_token = auth_header.split(" ")[1]
            
            # Validate session
            auth_service = get_auth_service()
            if not auth_service.validate_session(session_token):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or expired session"}
                )
            
            # Update session data
            auth_service.update_session_data(
                session_token,
                {
                    "last_activity": "now()",
                    "user_agent": str(request.headers.get("user-agent")),
                    "ip_address": request.client.host
                }
            )
            
            return await call_next(request)
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"detail": f"Session middleware error: {str(e)}"}
            )
