from fastapi import FastAPI
from contextlib import asynccontextmanager
import redis.asyncio as redis
import logging
from core.config import settings
from core.dependencies import get_db
from core.logging import setup_logging
from middleware.rate_limiter import RateLimiterMiddleware
from api.routes import router as api_router
from sqlalchemy import text
from api.auth import router as auth_router
from api.roles import router as role_router
from fastapi.middleware.cors import CORSMiddleware

# ✅ Set up structured logging
setup_logging()

# ✅ Lifespan event: Handle startup/shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🔹 Connect to Redis
    app.state.redis = await redis.from_url(settings.REDIS_URL, decode_responses=True)

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

#CORS middleware
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

# ✅ Root Health Check
@app.get("/")
async def health_check():
    return {"status": "OK", "message": "COMPASS API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
