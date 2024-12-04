"""API routes configuration."""
from fastapi import APIRouter
from ..routers.auth import router as auth_router
from ..routers.users import router as users_router
from ..routers.tasks import router as tasks_router
from ..routers.roles import router as roles_router
from ..routers.permissions import router as permissions_router
from ..routers.notifications import router as notifications_router

# Create main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(tasks_router)
api_router.include_router(roles_router)
api_router.include_router(permissions_router)
api_router.include_router(notifications_router)

# Export the main router
__all__ = ["api_router"]
