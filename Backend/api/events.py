from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from Backend.data_layer.database.connection import get_db
from Backend.data_layer.database.models.calendar_event import CalendarEvent, RecurrenceType, EventType
from Backend.data_layer.database.models.task import TaskStatus, TaskPriority
from Backend.data_layer.database.models.event_occurrence import EventOccurrence
from Backend.app.schemas.event_schemas import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventWithDetails,
    EventOccurrenceResponse
)
from Backend.services.event_service import EventService
from Backend.data_layer.repositories.event_repository import EventRepository, EventNotFoundError
from Backend.api.auth import get_current_user

router = APIRouter()


@router.post("/", response_model=EventResponse, status_code=http_status.HTTP_201_CREATED)
async def create_event(
    event: EventCreate,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Create a new calendar event."""
    try:
        repo = EventRepository(db)
        service = EventService(repo)
        event_data = event.dict()

        # Validate duration
        if event_data.get("duration") and event_data["duration"] < 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Duration must be positive"
            )

        # Ensure datetime objects are timezone-naive
        for field in ["start_date", "due_date", "recurrence_end_date"]:
            if field in event_data and event_data[field] is not None:
                # Remove timezone info if present
                if event_data[field].tzinfo:
                    event_data[field] = event_data[field].replace(tzinfo=None)

        # Create case-insensitive mappings for enums
        status_map = {status.value.upper(): status for status in TaskStatus}
        priority_map = {priority.value.upper(): priority for priority in TaskPriority}
        event_type_map = {event_type.value.upper(): event_type for event_type in EventType}
        recurrence_map = {recurrence.value.upper(): recurrence for recurrence in RecurrenceType}
        
        # Handle status enum - case insensitive match
        if isinstance(event_data.get('status'), str):
            status_upper = event_data['status'].upper()
            if status_upper in status_map:
                event_data['status'] = status_map[status_upper]
            else:
                # Direct assignment for the known enum object
                event_data['status'] = TaskStatus.UPCOMING
            
        # Handle priority enum - case insensitive match  
        if isinstance(event_data.get('priority'), str):
            priority_upper = event_data['priority'].upper()
            if priority_upper in priority_map:
                event_data['priority'] = priority_map[priority_upper]
            else:
                event_data['priority'] = TaskPriority.MEDIUM
            
        # Handle event_type enum - case insensitive match
        if isinstance(event_data.get('event_type'), str):
            event_type_upper = event_data['event_type'].upper()
            if event_type_upper in event_type_map:
                event_data['event_type'] = event_type_map[event_type_upper]
            else:
                event_data['event_type'] = EventType.NONE
            
        # Handle recurrence enum - case insensitive match
        if isinstance(event_data.get('recurrence'), str):
            recurrence_upper = event_data['recurrence'].upper()
            if recurrence_upper in recurrence_map:
                event_data['recurrence'] = recurrence_map[recurrence_upper]
            else:
                event_data['recurrence'] = RecurrenceType.NONE
            
        # Validate dates
        if event_data.get("due_date") and event_data["start_date"] > event_data["due_date"]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before due date"
            )

        # Validate recurrence end date
        if event_data.get("recurrence_end_date") and event_data["recurrence_end_date"] < event_data["start_date"]:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Recurrence end date cannot be before start date"
            )

        result = await service.create_event(**event_data)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating event: {str(e)}"
        )


@router.get("/by_id/{event_id}", response_model=EventWithDetails)
async def get_event(
    event_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Get event details by ID."""
    try:
        repo = EventRepository(db)
        service = EventService(repo)
        event = await service.get_event_with_details(event_id)
        if not event:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID {event_id} not found"
            )
        return event
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving event: {str(e)}"
        )


@router.get("/", response_model=List[EventResponse])
async def get_events_in_date_range(
    user_id: int,
    start_date: datetime,
    end_date: datetime,
    include_recurring: bool = Query(True, description="Include recurring events"),
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Get events within a specific date range."""
    try:
        # Ensure timezone-naive datetime objects
        if start_date.tzinfo:
            start_date = start_date.replace(tzinfo=None)
        if end_date.tzinfo:
            end_date = end_date.replace(tzinfo=None)
            
        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )
            
        repo = EventRepository(db)
        service = EventService(repo)
        
        events = await service.get_events_in_date_range(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            include_recurring=include_recurring
        )
        
        return events
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving events: {str(e)}"
        )


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    user_id: int,
    event_update: EventUpdate,
    update_option: str = Query(
        "this_occurrence", 
        description="How to handle recurring events: 'this_occurrence', 'this_and_future_occurrences', or 'all_occurrences'"),
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
) -> EventResponse:
    """Update an existing event."""
    try:
        repo = EventRepository(db)
        service = EventService(repo)

        # Get existing event
        existing_event = await service.get_event(event_id)
        if not existing_event:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )
            
        # Validate update_option
        valid_options = ["this_occurrence", "this_and_future_occurrences", "all_occurrences"]
        if update_option not in valid_options:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid update_option. Must be one of: {', '.join(valid_options)}"
            )

        event_data = event_update.dict(exclude_unset=True)
        
        # Handle status updates if needed
        if 'status' in event_data:
            try:
                updated_event = await service.update_event_status(
                    event_id,
                    event_data['status'],
                    user_id
                )
                # Remove status from event_data as it's already updated
                event_data.pop('status')
            except Exception as e:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        # Update remaining fields if any
        if event_data:
            updated_event = await service.update_event(
                event_id, 
                event_data, 
                update_option=update_option
            )

        return updated_event
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating event: {str(e)}"
        )


@router.delete("/{event_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Delete an event."""
    try:
        repo = EventRepository(db)
        service = EventService(repo)

        success = await service.delete_event(event_id, user_id)
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        return {"message": "Event deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting event: {str(e)}"
        )


@router.get("/calendar", response_model=List[Dict[str, Any]])
async def get_calendar_events(
    start_date: datetime,
    end_date: datetime,
    user_id: int,
    include_recurring: bool = Query(
        True, description="Whether to include recurring events and their occurrences"),
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Get events formatted for calendar view with expanded recurring events.

    This endpoint retrieves events for a calendar view and expands recurring events
    into individual occurrences based on their recurrence pattern.
    """
    try:
        repo = EventRepository(db)
        service = EventService(repo)

        # Ensure timezone-naive datetime objects
        if start_date.tzinfo:
            start_date = start_date.replace(tzinfo=None)
        if end_date.tzinfo:
            end_date = end_date.replace(tzinfo=None)

        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Start date must be before end date"
            )

        # Limit range to prevent performance issues (e.g., max 3 months)
        max_range = timedelta(days=90)
        if end_date - start_date > max_range:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Date range too large. Maximum range is {max_range.days} days"
            )

        calendar_events = await service.get_calendar_events(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            include_recurring=include_recurring
        )

        return calendar_events
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving calendar events: {str(e)}"
        )


@router.get("/{event_id}/occurrences", response_model=List[EventOccurrenceResponse])
async def get_event_occurrences(
    event_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Get all occurrences for a recurring event."""
    try:
        repo = EventRepository(db)
        event_occurrences = await repo.get_event_occurrences(event_id)
        return event_occurrences
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving event occurrences: {str(e)}"
        )


@router.put("/occurrences/{event_id}/{occurrence_num}", response_model=EventOccurrenceResponse)
async def update_event_occurrence(
    event_id: int,
    occurrence_num: int,
    user_id: int,
    event_update: EventUpdate,
    update_option: str = Query(
        "this_occurrence", 
        description="How to handle this occurrence: 'this_occurrence' or 'this_and_future_occurrences'"),
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Update a specific occurrence of a recurring event.
    
    Args:
        event_id: The event ID
        occurrence_num: The occurrence number to update
        user_id: The user ID
        event_update: The fields to update
        update_option: How to handle this update:
            - this_occurrence: Update only this occurrence
            - this_and_future_occurrences: Update this and all future occurrences
    """
    try:
        repo = EventRepository(db)
        service = EventService(repo)
        
        # Validate update_option for occurrences
        valid_options = ["this_occurrence", "this_and_future_occurrences"]
        if update_option not in valid_options:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid update_option for occurrence. Must be one of: {', '.join(valid_options)}"
            )
        
        # Check if the event exists
        event = await service.get_event(event_id)
        if not event:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )
            
        # Check if this is a recurring event
        if event.recurrence == RecurrenceType.NONE:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="This operation is only valid for recurring events"
            )
        
        # Update the specific occurrence
        event_data = event_update.dict(exclude_unset=True)
        event_data["modified_by_id"] = user_id
        
        # Use the virtual ID format that EventService recognizes for occurrences
        virtual_id = f"{event_id}_{occurrence_num}"
        
        # Update using the specified update option
        updated_event = await service.update_event(
            virtual_id,  # Use the virtual ID
            event_data,
            update_option=update_option
        )
        
        # If we're updating just this occurrence, return the occurrence
        if update_option == "this_occurrence":
            # Retrieve the updated occurrence
            updated_occurrence = await repo.get_event_occurrence(event_id, occurrence_num)
            if not updated_occurrence:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail=f"Failed to update occurrence {occurrence_num} of event {event_id}"
                )
                
            return updated_occurrence
        else:
            # For this_and_future_occurrences, we'll return the first updated occurrence
            updated_occurrence = await repo.get_event_occurrence(event_id, occurrence_num) 
            if updated_occurrence:
                return updated_occurrence
            else:
                # If no specific occurrence was created yet, return a virtual representation
                # Get the original event to create a virtual occurrence
                event = await service.get_event(event_id)
                
                # Create a mock occurrence for response
                mock_occurrence = EventOccurrence()
                mock_occurrence.id = -1  # Placeholder ID
                mock_occurrence.calendar_event_id = event_id
                mock_occurrence.occurrence_num = occurrence_num
                mock_occurrence.start_date = service._calculate_occurrence_start_date(event, occurrence_num)
                mock_occurrence.title = event.title
                mock_occurrence.description = event.description
                mock_occurrence.status = event.status
                mock_occurrence.priority = event.priority
                mock_occurrence.event_type = event.event_type
                
                # Calculate due date if event has duration
                if event.duration:
                    mock_occurrence.due_date = mock_occurrence.start_date + timedelta(hours=event.duration)
                
                return mock_occurrence
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating event occurrence: {str(e)}"
        )


@router.delete("/occurrences/{event_id}/{occurrence_num}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_event_occurrence(
    event_id: int,
    occurrence_num: int,
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # current_user=Depends(get_current_user)
):
    """Delete a specific occurrence of a recurring event."""
    try:
        repo = EventRepository(db)
        
        # Get the occurrence
        occurrence = await repo.get_event_occurrence(event_id, occurrence_num)
        if not occurrence:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Occurrence {occurrence_num} of event {event_id} not found"
            )
        
        # Delete the occurrence
        success = await repo.delete_event_occurrence(occurrence.id)
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete occurrence {occurrence_num} of event {event_id}"
            )
            
        return {"message": "Event occurrence deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting event occurrence: {str(e)}"
        ) 