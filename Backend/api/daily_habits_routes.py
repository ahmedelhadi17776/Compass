from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from Backend.services.daily_habits_service import DailyHabitService
from Backend.data_layer.repositories.daily_habits_repository import DailyHabitRepository
from Backend.data_layer.database.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field


# Pydantic models for request/response validation
class DailyHabitBase(BaseModel):
    habit_name: str
    description: Optional[str] = None
    start_day: date
    end_day: Optional[date] = None


class DailyHabitCreate(DailyHabitBase):
    user_id: int


class DailyHabitUpdate(BaseModel):
    habit_name: Optional[str] = None
    description: Optional[str] = None
    start_day: Optional[date] = None
    end_day: Optional[date] = None


class DailyHabitResponse(DailyHabitBase):
    id: int
    user_id: int
    current_streak: int
    longest_streak: int
    is_completed: bool
    last_completed_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


router = APIRouter()


@router.post("/", response_model=DailyHabitResponse, status_code=201)
async def create_habit(habit: DailyHabitCreate, db: AsyncSession = Depends(get_db)):
    """Create a new daily habit."""
    habit_service = DailyHabitService(repository=DailyHabitRepository(db))
    return await habit_service.create_habit(**habit.dict())


@router.get("/{habit_id}", response_model=DailyHabitResponse)
async def get_habit(habit_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    """Get a habit by ID."""
    habit_service = DailyHabitService(repository=DailyHabitRepository(db))
    habit = await habit_service.get_habit_by_id(habit_id, user_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit


@router.get("/user/{user_id}", response_model=List[DailyHabitResponse])
async def get_user_habits(user_id: int, active_only: bool = False, db: AsyncSession = Depends(get_db)):
    """Get all habits for a user."""
    habit_service = DailyHabitService(repository=DailyHabitRepository(db))

    if active_only:
        return await habit_service.get_active_habits(user_id)
    else:
        return await habit_service.get_user_habits(user_id)


@router.get("/user/{user_id}/due", response_model=List[DailyHabitResponse])
async def get_habits_due_today(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get habits that are due today (active but not completed)."""
    habit_service = DailyHabitService(repository=DailyHabitRepository(db))
    return await habit_service.get_habits_due_today(user_id)


@router.get("/user/{user_id}/top-streaks", response_model=List[DailyHabitResponse])
async def get_top_streaks(user_id: int, limit: int = 5, db: AsyncSession = Depends(get_db)):
    """Get habits with the highest current streaks."""
    habit_service = DailyHabitService(repository=DailyHabitRepository(db))
    return await habit_service.get_top_streaks(user_id, limit)


@router.put("/{habit_id}", response_model=DailyHabitResponse)
async def update_habit(habit_id: int, habit: DailyHabitUpdate, user_id: int, db: AsyncSession = Depends(get_db)):
    """Update a habit."""
    habit_service = DailyHabitService(repository=DailyHabitRepository(db))
    updated_habit = await habit_service.update_habit(habit_id, user_id, **habit.dict(exclude_unset=True))

    if not updated_habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    return updated_habit


@router.delete("/{habit_id}")
async def delete_habit(habit_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a habit."""
    habit_service = DailyHabitService(repository=DailyHabitRepository(db))
    result = await habit_service.delete_habit(habit_id, user_id)

    if not result:
        raise HTTPException(status_code=404, detail="Habit not found")

    return {"message": "Habit deleted successfully"}


@router.post("/{habit_id}/complete", response_model=DailyHabitResponse)
async def mark_habit_completed(habit_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    """Mark a habit as completed for today and update streak."""
    habit_service = DailyHabitService(repository=DailyHabitRepository(db))
    habit = await habit_service.mark_habit_completed(habit_id, user_id)

    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    return habit


@router.post("/process-daily-reset")
async def process_daily_reset(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Process daily reset operations (reset completion status and check for broken streaks).
    This endpoint should be called once per day, typically at midnight.
    """
    # Run in background to avoid blocking the request
    habit_service = DailyHabitService(repository=DailyHabitRepository(db))
    background_tasks.add_task(habit_service.process_daily_reset)

    return {"message": "Daily reset process started"}
