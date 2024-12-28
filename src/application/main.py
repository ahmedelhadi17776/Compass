from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.application.routers.auth import router as auth_router
from src.application.routers.authorization import router as authorization_router
from src.application.routers.tasks import router as tasks_router
from src.application.routers.notifications import router as notifications_router
from src.application.middlewares.security_audit import SecurityAuditMiddleware
from src.core.logging import setup_logging
from src.core.database import engine, Base
from src.core.config import settings

# Initialize logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(authorization_router)
app.include_router(tasks_router)
app.include_router(notifications_router)

# Add Middleware
app.add_middleware(SecurityAuditMiddleware)


@app.on_event("startup")
async def startup_event():
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def root():
    return {
        "message": "Welcome to AIWA Backend!",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
