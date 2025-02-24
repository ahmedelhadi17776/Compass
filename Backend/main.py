from fastapi import FastAPI
from contextlib import asynccontextmanager
import redis.asyncio as redis
import logging
from Backend.core.config import settings
from Backend.data_layer.database.connection import get_db
from Backend.core.logging import setup_logging
from Backend.core.celery_app import celery_app
from Backend.middleware.rate_limiter import RateLimiterMiddleware
from Backend.api.routes import router as api_router
from Backend.api.todo_routes import router as todo_router
from sqlalchemy import text
from Backend.api.auth import router as auth_router
from Backend.api.roles import router as role_router
from Backend.api.workflows import router as workflow_router
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

    # Initialize Celery Beat schedule for periodic tasks
    celery_app.conf.beat_schedule = {
        'process-scheduled-notifications': {
            'task': 'tasks.notification_tasks.process_scheduled_notifications',
            'schedule': 60.0,  # Every minute
            'args': (datetime.utcnow().isoformat(),)
        },
        'generate-productivity-insights': {
            'task': 'tasks.ai_tasks.generate_productivity_insights',
            'schedule': 3600.0,  # Every hour
            'args': (None, 'hourly', ['focus', 'productivity', 'breaks'])
        }
    }

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

# Include Todo routes
app.include_router(todo_router, prefix="/todos", tags=["todos"])

# Include authentication endpoints
app.include_router(auth_router, prefix="/auth")
app.include_router(role_router, prefix="/admin")
app.include_router(workflow_router)

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
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
