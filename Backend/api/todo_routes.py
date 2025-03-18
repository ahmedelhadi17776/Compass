from fastapi import APIRouter, Depends, HTTPException
from Backend.services.todo_service import TodoService
from Backend.data_layer.repositories.todo_repository import TodoRepository
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.data_layer.database.connection import get_db
# Import the Pydantic models
from Backend.app.schemas.todo_schemas import TodoCreate, TodoUpdate, Todo
from typing import List, Optional
from Backend.data_layer.database.models.todo import TodoStatus
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.services.task_service import TaskService

router = APIRouter()


@router.post("/", response_model=Todo, status_code=201)
async def create_todo(todo: TodoCreate, db: AsyncSession = Depends(get_db)):
    """Create a new todo."""
    # Pass the repository with session
    todo_service = TodoService(repository=TodoRepository(db))
    return await todo_service.create_todo(**todo.dict())


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
    return await todo_service.convert_task_to_todo(task)
