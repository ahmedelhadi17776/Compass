from fastapi import APIRouter, Depends, HTTPException, Query
from Backend.services.todo_service import TodoService
from Backend.data_layer.repositories.todo_repository import TodoRepository
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.data_layer.database.connection import get_db
# Import the Pydantic models
from Backend.app.schemas.todo_schemas import (
    TodoCreate, TodoUpdate, Todo, 
    TodoSearchResult, TodoSearchResponse,
    TodoSuggestion, TodoAnalytics
)
from typing import List, Optional, Dict, Any
from Backend.data_layer.database.models.todo import TodoStatus
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.services.task_service import TaskService
import logging

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/", response_model=Todo, status_code=201)
async def create_todo(todo: TodoCreate, db: AsyncSession = Depends(get_db)):
    """Create a new todo."""
    # Pass the repository with session
    todo_service = TodoService(repository=TodoRepository(db))
    created_todo = await todo_service.create_todo(**todo.dict())
    
    return created_todo


@router.get("/{todo_id}", response_model=Todo)
async def get_todo(todo_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    """Get a todo by ID."""
    # Pass the repository with session
    todo_service = TodoService(repository=TodoRepository(db))
    todo = await todo_service.get_todo_by_id(todo_id, user_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.get("/user/{user_id}", response_model=List[Todo])
async def get_user_todos(
    user_id: int,
    status: Optional[TodoStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all todos for a user."""
    # Pass the repository with session
    todo_service = TodoService(repository=TodoRepository(db))
    return await todo_service.get_user_todos(user_id, status.value if status else None)


@router.put("/{todo_id}", response_model=Todo)
async def update_todo(todo_id: int, todo: TodoUpdate, user_id: int, db: AsyncSession = Depends(get_db)):
    """Update a todo."""
    # Pass the repository with session
    todo_service = TodoService(repository=TodoRepository(db))
    updated_todo = await todo_service.update_todo(
        todo_id,
        user_id,
        **todo.dict(exclude_unset=True)
    )
    if not updated_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return updated_todo


@router.delete("/{todo_id}")
async def delete_todo(todo_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a todo."""
    # Pass the repository with session
    todo_service = TodoService(repository=TodoRepository(db))
    success = await todo_service.delete_todo(todo_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return {"success": True}


@router.post("/tasks/{task_id}/convert")
async def convert_task_to_todo(task_id: int, db: AsyncSession = Depends(get_db)):
    """Convert a task to a todo."""
    task_service = TaskService(repository=TaskRepository(db))
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    todo_service = TodoService(repository=TodoRepository(db))
    converted_todo = await todo_service.convert_task_to_todo(task)
    
    return converted_todo


@router.get("/search/{user_id}", response_model=TodoSearchResponse)
async def search_todos(
    user_id: int,
    query: str,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """Search todos semantically by query.
    
    This endpoint uses vector similarity search to find todos similar to the query.
    """
    todo_service = TodoService(repository=TodoRepository(db))
    results = await todo_service.semantic_search_todos(query, user_id, limit)
    
    # Handle potential errors
    if "error" in results:
        raise HTTPException(
            status_code=500, 
            detail=f"Error searching todos: {results.get('error', 'Unknown error')}"
        )
        
    return results


@router.get("/similar/{user_id}", response_model=List[TodoSearchResult])
async def find_similar_todos(
    user_id: int,
    query: str,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """Find todos similar to the query.
    
    This endpoint uses vector similarity to find similar todos.
    """
    todo_service = TodoService(repository=TodoRepository(db))
    return await todo_service.find_similar_todos(query, user_id, limit)


@router.get("/suggestions/{user_id}", response_model=List[TodoSuggestion])
async def get_todo_suggestions(
    user_id: int,
    count: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """Get AI-generated todo suggestions for a user."""
    todo_service = TodoService(repository=TodoRepository(db))
    return await todo_service.get_todo_suggestions(user_id, count)


@router.get("/analytics/{user_id}", response_model=TodoAnalytics)
async def get_todo_analytics(
    user_id: int,
    time_period: str = Query("week", pattern="^(day|week|month)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics for a user's todos."""
    todo_service = TodoService(repository=TodoRepository(db))
    analytics = await todo_service.get_todo_analytics(user_id, time_period)
    
    # Handle potential errors
    if "error" in analytics:
        raise HTTPException(
            status_code=500, 
            detail=f"Error getting analytics: {analytics.get('error', 'Unknown error')}"
        )
        
    return analytics
