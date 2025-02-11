"""Main application module."""
from Backend.api.v1.endpoints import security
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
import secrets
import time
from sqlalchemy.ext.asyncio import AsyncSession

from Backend.core.config import settings
from Backend.core.security.exceptions import SecurityError, AuthError
from Backend.core.security import SecurityHeaders
from Backend.middleware.auth_middleware import setup_auth_middleware
from Backend.middleware.session_middleware import setup_session_middleware
from Backend.application.api.routes import api_router
from Backend.services.background_tasks import background_tasks
from Backend.core.logging import setup_logging
from Backend.middleware.rate_limiter import RateLimiter
from Backend.middleware.security import SecurityMiddleware
from Backend.core.security.auth import TokenManager
from Backend.core.security.encryption import EncryptionService
from Backend.middleware.security_context import SecurityContextMiddleware
from Backend.middleware.security_factory import setup_security_middleware
from Backend.core.security.events import SecurityEventService
from Backend.core.security.headers import SecurityHeadersService
from Backend.core.security.rate_limit import RateLimitConfig
from Backend.services.security.background_tasks import SecurityBackgroundTasks
from Backend.services.security.monitoring_service import SecurityMonitoringService
from Backend.services.security.alerts_service import SecurityAlertsService
from Backend.core.security.context import SecurityContext
from Backend.services.security.security_service import SecurityService

# Setup logging
logger = setup_logging()

# Configure logging
with open("configs/logging_config.json") as f:
    logging_config = json.load(f)
logging.config.dictConfig(logging_config)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize security services
token_manager = TokenManager()
encryption_service = EncryptionService()
security_headers_service = SecurityHeadersService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
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

# Initialize security background tasks
security_tasks = SecurityBackgroundTasks(app)

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
setup_security_middleware(
    app,
    token_manager=token_manager,
    encryption_service=encryption_service,
    rate_limit_config=RateLimitConfig(
        requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
        burst_size=settings.RATE_LIMIT_BURST_SIZE
    )
)

# Set up authentication middleware
setup_auth_middleware(app)

# Set up session middleware
setup_session_middleware(app)

# Include API router
app.include_router(api_router, prefix="/api")

# Add security middleware
app.add_middleware(
    SecurityMiddleware,
    security_service=SecurityService(
        db=AsyncSession(),
        context=SecurityContext.create(
            token_manager=token_manager,
            encryption_service=encryption_service,
            client_ip="0.0.0.0",  # Will be updated per-request
            path="/",  # Will be updated per-request
            method="GET"  # Will be updated per-request
        )
    )
)

# Add security event handling middleware


@app.middleware("http")
async def security_event_handler(request: Request, call_next):
    """Handle security events."""
    start_time = time.time()

    try:
        response = await call_next(request)

        # Log successful requests
        await request.state.security_service.audit_request(
            request=request,
            response_status=response.status_code,
            duration=time.time() - start_time
        )

        return response

    except Exception as e:
        # Log failed requests
        await request.state.security_service.audit_request(
            request=request,
            response_status=500,
            duration=time.time() - start_time,
            error=str(e)
        )
        raise

# Add security routes

app.include_router(
    security.router,
    prefix="/api/v1/security",
    tags=["security"]
)


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
