"""Main application module."""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import logging.config
import json
import os
from pathlib import Path
from contextlib import asynccontextmanager

from src.core.config import settings
from src.core.exceptions import AuthError
from src.core.security import SecurityHeaders
from src.middleware.auth_middleware import setup_auth_middleware
from src.middleware.session_middleware import setup_session_middleware
from src.middleware.security_middleware import setup_security_middleware
from src.application.api.routes import api_router
from src.services.background_tasks import background_tasks
from src.core.logging import setup_logging

# Setup logging
logger = setup_logging()

# Configure logging
with open("configs/logging_config.json") as f:
    logging_config = json.load(f)
logging.config.dictConfig(logging_config)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    background_tasks.app = app
    await background_tasks.start()
    yield
    # Shutdown
    await background_tasks.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Set up security middleware (should be first)
setup_security_middleware(app)

# Set up authentication middleware
setup_auth_middleware(app)

# Set up session middleware
setup_session_middleware(app)

# Include API router
app.include_router(api_router, prefix="/api")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )

@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError):
    """Handle authentication errors."""
    logger.error(f"Authentication error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={**exc.headers} if exc.headers else None
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error occurred. Please try again later."
        }
    )

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    SecurityHeaders.apply_security_headers(response)
    return response

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Check API health status."""
    return {"status": "healthy"}

logger.info("Application startup complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL.lower(),
    )
