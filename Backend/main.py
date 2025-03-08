from Backend.api.cache_test_routes import router as cache_test_router
from fastapi import FastAPI
from contextlib import asynccontextmanager
import redis.asyncio as redis
import logging
from Backend.core.config import settings
from Backend.data_layer.database.connection import get_db
from Backend.core.logging import setup_logging
from Backend.celery_app import celery_app
from Backend.middleware.rate_limiter import RateLimiterMiddleware
from Backend.api.routes import router as api_router
from Backend.api.todo_routes import router as todo_router
from sqlalchemy import text
from Backend.api.auth import router as auth_router
from Backend.api.roles import router as role_router
from Backend.api.workflows import router as workflow_router
from Backend.api.ai_routes import router as ai_router
from Backend.api.tasks import router as task_router
from Backend.api.organizations import router as organization_router
from Backend.api.projects import router as project_router
from Backend.api.cache_routes import router as cache_router
from Backend.api.daily_habits_routes import router as daily_habits_router
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

# ✅ Set up structured logging
setup_logging()

# ✅ Lifespan event: Handle startup/shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🔹 Connect to Redis
    app.state.redis = await redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )

    # 🔹 Test Database Connection
    async for db in get_db():
        try:
            await db.execute(text("SELECT 1"))  # ✅ Wrap in text()
            logging.info("✅ Database connected successfully.")
        except Exception as e:
            logging.error(f"❌ Database connection failed: {e}")
        break  # Exit loop after first attempt

    yield

    # 🔹 Close Redis connection
    await app.state.redis.close()
    logging.info("🛑 Redis connection closed.")

# ✅ Initialize FastAPI app
app = FastAPI(
    title="COMPASS API",
    version="1.0",
    lifespan=lifespan
)

# ✅ Middleware
app.add_middleware(RateLimiterMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ✅ Include API Routes
app.include_router(api_router)

# Include authentication endpoints
app.include_router(auth_router, prefix="/auth")
app.include_router(role_router, prefix="/admin")

app.include_router(organization_router,
                   prefix="/organizations", tags=["organizations"])

app.include_router(project_router, prefix="/projects", tags=["projects"])

app.include_router(task_router, prefix="/tasks", tags=["tasks"])

# Include cache test routes
app.include_router(cache_test_router)

# Include Todo routes
app.include_router(todo_router, prefix="/todos", tags=["todos"])

# Include Daily Habits routes
app.include_router(daily_habits_router,
                   prefix="/daily-habits", tags=["daily-habits"])

app.include_router(workflow_router)

app.include_router(ai_router)

app.include_router(cache_router)


# ✅ Root Health Check
@app.get("/")
async def health_check():
    return {
        "status": "OK",
        "message": "COMPASS API is running!",
        "celery_status": "Active",
        "redis_status": "Connected"
    }

# Celery Task Status Endpoint


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a Celery task by its ID.
    """
    from Backend.celery_app.monitoring import get_task_status
    return get_task_status(task_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
