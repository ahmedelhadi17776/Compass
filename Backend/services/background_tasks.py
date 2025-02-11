"""Background tasks for the application."""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI
from Backend.services.authentication.auth_service import AuthService
from Backend.dependencies import get_auth_service
from Backend.core.config import settings

class BackgroundTasks:
    """Background tasks manager."""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.tasks = {}
        self.is_running = False
    
    async def start(self):
        """Start background tasks."""
        if not self.is_running:
            self.is_running = True
            self.tasks["session_cleanup"] = asyncio.create_task(self.cleanup_expired_sessions())
    
    async def stop(self):
        """Stop background tasks."""
        if self.is_running:
            self.is_running = False
            for task in self.tasks.values():
                task.cancel()
            self.tasks.clear()
    
    async def cleanup_expired_sessions(self):
        """Periodically cleanup expired sessions."""
        auth_service = get_auth_service()
        cleanup_interval = timedelta(minutes=settings.SESSION_CLEANUP_INTERVAL_MINUTES)
        
        while self.is_running:
            try:
                # Cleanup expired sessions
                auth_service.cleanup_expired_sessions()
                
                # Wait for next cleanup interval
                await asyncio.sleep(cleanup_interval.total_seconds())
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue running
                print(f"Error in session cleanup task: {str(e)}")
                await asyncio.sleep(60)  # Wait a minute before retrying

background_tasks = BackgroundTasks(None)  # Will be initialized with app instance
