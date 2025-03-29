from typing import Dict, List, Any, Optional, cast, Sequence
from sqlalchemy import select, and_, or_, Float
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from Backend.data_layer.database.models.calendar_event import CalendarEvent, RecurrenceType
from Backend.data_layer.database.models.task import TaskStatus, TaskPriority
from Backend.data_layer.database.models.ai_interactions import AIAgentInteraction
from datetime import datetime, timedelta
from Backend.data_layer.repositories.base_repository import BaseRepository
import logging
import json
from Backend.data_layer.database.models.event_occurrence import EventOccurrence
from Backend.events.event_dispatcher import dispatcher
from Backend.events.event_registry import EVENT_UPDATED

logger = logging.getLogger(__name__)


class EventNotFoundError(Exception):
    """Raised when an event is not found."""
    pass


class EventRepository(BaseRepository[CalendarEvent]):
    def __init__(self, db):
        self.db = db

    async def create(self, start_date: datetime, duration: Optional[float] = None, **event_data) -> CalendarEvent:
        """Create a new event."""

        required_fields = {
            'title',
            'user_id',
        }

        missing = required_fields - event_data.keys()
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        valid_columns = {c.name for c in CalendarEvent.__table__.columns}
        filtered_data = {k: v for k,
                         v in event_data.items() if k in valid_columns}

        new_event = CalendarEvent(
            start_date=start_date,
            duration=duration,
            **filtered_data
        )
        self.db.add(new_event)
        await self.db.flush()
        return new_event

    async def create_event_occurrence(self, occurrence_data: dict) -> None:
        """Create an event occurrence for a recurring event.

        Args:
            occurrence_data: Dictionary containing the occurrence data
        """
        from Backend.data_layer.database.models.event_occurrence import EventOccurrence

        # Create a copy of the data to avoid modifying the original
        occurrence_data = occurrence_data.copy()

        # Handle enum values for status and priority
        if 'status' in occurrence_data:
            if isinstance(occurrence_data['status'], str):
                try:
                    occurrence_data['status'] = TaskStatus(
                        occurrence_data['status'])
                except ValueError:
                    logger.warning(
                        f"Invalid status value: {occurrence_data['status']}")
                    del occurrence_data['status']
            elif not isinstance(occurrence_data['status'], TaskStatus):
                logger.warning(
                    f"Invalid status type: {type(occurrence_data['status'])}")
                del occurrence_data['status']

        if 'priority' in occurrence_data:
            if isinstance(occurrence_data['priority'], str):
                try:
                    occurrence_data['priority'] = TaskPriority(
                        occurrence_data['priority'])
                except ValueError:
                    logger.warning(
                        f"Invalid priority value: {occurrence_data['priority']}")
                    del occurrence_data['priority']
            elif not isinstance(occurrence_data['priority'], TaskPriority):
                logger.warning(
                    f"Invalid priority type: {type(occurrence_data['priority'])}")
                del occurrence_data['priority']

        occurrence = EventOccurrence(**occurrence_data)
        self.db.add(occurrence)
        await self.db.flush()

    async def get_by_id(self, event_id: int, user_id: Optional[int] = None) -> Optional[CalendarEvent]:
        """Get an event by ID with optional user ID check."""
        query = select(CalendarEvent).where(CalendarEvent.id == event_id)
        if user_id is not None:
            query = query.where(CalendarEvent.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_event(self, event_id: int) -> Optional[CalendarEvent]:
        """Get an event by ID without user_id check."""
        return await self.get_by_id(event_id)

    async def delete_event(self, event_id: int) -> bool:
        """Delete an event by ID without user_id check."""
        event = await self.get_event(event_id)
        if event:
            await self.db.delete(event)
            await self.db.flush()
            return True
        return False

    async def update(self, id: int, user_id: int, **update_data) -> Optional[CalendarEvent]:
        """Update an event. Implementation of abstract method from BaseRepository."""
        event = await self.get_by_id(id, user_id)
        if event:
            # Update event fields
            for key, value in update_data.items():
                if hasattr(event, key):
                    setattr(event, key, value)
            await self.db.flush()
            await dispatcher.dispatch(EVENT_UPDATED, {"event_id": id, "event_data": update_data})
            return event
        return None

    async def delete(self, id: int, user_id: int) -> bool:
        """Delete an entity. Implementation of abstract method from BaseRepository."""
        # Using delete_event with user_id check
        event = await self.get_by_id(id, user_id)
        if event:
            await self.db.delete(event)
            await self.db.flush()  # Consistent with delete_event
            return True
        return False

    async def get_user_events(self, user_id: int, status: Optional[str] = None) -> List[CalendarEvent]:
        """Get all events for a user with optional status filter."""
        query = select(CalendarEvent).where(CalendarEvent.user_id == user_id)
        if status:
            query = query.where(CalendarEvent.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_event_with_details(self, event_id: int) -> Optional[CalendarEvent]:
        """Get an event with all its related details."""
        query = (
            select(CalendarEvent)
            .options(
                joinedload(CalendarEvent.meeting_notes),
                joinedload(CalendarEvent.occurrences),
                joinedload(CalendarEvent.task),
                joinedload(CalendarEvent.linked_todos)
            )
            .where(CalendarEvent.id == event_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def update_event(self, event_id: int, event_data: dict) -> Optional[CalendarEvent]:
        """Update an event with the given data without user_id check."""
        event = await self.get_by_id(event_id)
        if not event:
            raise EventNotFoundError(f"CalendarEvent with id {event_id} not found")

        if "start_date" in event_data or "duration" in event_data:
            new_start = event_data.get("start_date", event.start_date)
            new_duration = event_data.get("duration", event.duration)

            if new_duration and new_duration < 0:
                raise ValueError("Duration must be positive")

            event.start_date = new_start
            event.duration = new_duration

        if "due_date" in event_data:
            event.due_date = event_data["due_date"]

        if "recurrence_end_date" in event_data:
            if event_data["recurrence_end_date"] and event_data["recurrence_end_date"] < event.start_date:
                raise ValueError(
                    "Recurrence end date cannot be before start date")

        # Update event fields
        for key, value in event_data.items():
            # Skip date fields as they're handled separately above
            if key not in ["start_date", "due_date", "duration"] and hasattr(event, key):
                setattr(event, key, value)

        await self.db.flush()
        await dispatcher.dispatch(EVENT_UPDATED, {"event_id": event_id, "event_data": event_data})

        return event
        
    async def get_events_by_task(self, task_id: int) -> List[CalendarEvent]:
        """Get all events associated with a specific task."""
        query = select(CalendarEvent).where(CalendarEvent.task_id == task_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())
        
    async def get_events_in_date_range(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        include_recurring: bool = True
    ) -> List[CalendarEvent]:
        """Get events within a specific date range.
        
        This handles both single occurrence and recurring events.
        """
        # For regular events, use direct date filtering
        date_filter = or_(
            # Events starting within the range
            and_(
                CalendarEvent.start_date >= start_date,
                CalendarEvent.start_date <= end_date
            ),
            # Events ending within the range
            and_(
                CalendarEvent.due_date >= start_date,
                CalendarEvent.due_date <= end_date
            ),
            # Events spanning across the range
            and_(
                CalendarEvent.start_date <= start_date,
                CalendarEvent.due_date >= end_date
            )
        )
        
        if not include_recurring:
            query = select(CalendarEvent).where(
                and_(
                    CalendarEvent.user_id == user_id,
                    date_filter,
                    CalendarEvent.recurrence == RecurrenceType.NONE
                )
            )
        else:
            query = select(CalendarEvent).where(
                and_(
                    CalendarEvent.user_id == user_id,
                    or_(
                        date_filter,
                        CalendarEvent.recurrence != RecurrenceType.NONE
                    )
                )
            )
            
        result = await self.db.execute(query)
        return list(result.scalars().all())
        
    async def get_event_occurrences_in_range(
        self, 
        event_id: int, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> List[EventOccurrence]:
        """Get event occurrences within a date range."""
        query = select(EventOccurrence).where(EventOccurrence.calendar_event_id == event_id)
        
        if start_date and end_date:
            query = query.where(
                or_(
                    # Occurrences starting within the range
                    and_(
                        EventOccurrence.start_date >= start_date,
                        EventOccurrence.start_date <= end_date
                    ),
                    # Occurrences ending within the range
                    and_(
                        EventOccurrence.due_date >= start_date,
                        EventOccurrence.due_date <= end_date
                    ),
                    # Occurrences spanning across the range
                    and_(
                        EventOccurrence.start_date <= start_date,
                        EventOccurrence.due_date >= end_date
                    )
                )
            )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    def _create_virtual_event_from_occurrence(self, base_event: CalendarEvent, occurrence: EventOccurrence) -> CalendarEvent:
        """Create a virtual event object from an event occurrence.
        
        This creates a copy of the base event with the occurrence's overridden properties.
        The event ID is modified to include the occurrence number for identification.
        """
        # Create a shallow copy of the base event
        virtual_event = CalendarEvent()
        
        # Copy all attributes from the base event
        for column in CalendarEvent.__table__.columns:
            if column.name != 'id':  # Don't copy the ID
                setattr(virtual_event, column.name, getattr(base_event, column.name))
        
        # Override with occurrence-specific attributes if they exist
        if occurrence.title:
            virtual_event.title = occurrence.title
        if occurrence.description:
            virtual_event.description = occurrence.description
        if occurrence.status:
            virtual_event.status = occurrence.status
        if occurrence.priority:
            virtual_event.priority = occurrence.priority
        
        # Always override date-related fields
        virtual_event.start_date = occurrence.start_date
        if occurrence.duration:
            virtual_event.duration = occurrence.duration
        if occurrence.due_date:
            virtual_event.due_date = occurrence.due_date
        
        # Set a virtual ID that combines the event ID and occurrence number
        # This will be used to identify the specific occurrence when updating
        virtual_event.id = int(f"{base_event.id}_{occurrence.occurrence_num}")
        
        # Add occurrence metadata
        virtual_event.is_occurrence = True
        virtual_event.occurrence_num = occurrence.occurrence_num
        virtual_event.original_event_id = base_event.id
        virtual_event.occurrence_id = occurrence.id
        
        return virtual_event
        
    async def get_events_with_occurrences(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        """Get all events with their occurrences for a specific date range.
        
        This method handles recurring events by generating virtual event objects
        for each occurrence in the specified date range.
        """
        # First, get all regular (non-recurring) events in the date range
        regular_events_query = select(CalendarEvent).where(
            and_(
                CalendarEvent.user_id == user_id,
                CalendarEvent.recurrence == RecurrenceType.NONE,
                or_(
                    # Events starting within the range
                    and_(
                        CalendarEvent.start_date >= start_date,
                        CalendarEvent.start_date <= end_date
                    ),
                    # Events ending within the range
                    and_(
                        CalendarEvent.due_date >= start_date,
                        CalendarEvent.due_date <= end_date
                    ),
                    # Events spanning across the range
                    and_(
                        CalendarEvent.start_date <= start_date,
                        CalendarEvent.due_date >= end_date
                    )
                )
            )
        )
        
        regular_events_result = await self.db.execute(regular_events_query)
        regular_events = list(regular_events_result.scalars().all())
        
        # Now, get all recurring events
        recurring_events_query = select(CalendarEvent).where(
            and_(
                CalendarEvent.user_id == user_id,
                CalendarEvent.recurrence != RecurrenceType.NONE
            )
        )
        
        recurring_events_result = await self.db.execute(recurring_events_query)
        recurring_events = list(recurring_events_result.scalars().all())
        
        # Process recurring events to get their occurrences in the date range
        all_events = regular_events.copy()
        
        for event in recurring_events:
            # Get occurrences for this event in the date range
            occurrences = await self.get_event_occurrences_in_range(
                event.id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Create virtual events for each occurrence
            for occurrence in occurrences:
                virtual_event = self._create_virtual_event_from_occurrence(event, occurrence)
                all_events.append(virtual_event)
        
        # Sort events by start date
        all_events.sort(key=lambda e: e.start_date)
        
        return all_events

    async def get_recent_events(
        self,
        user_id: int,
        days: int = 7,
        limit: int = 10
    ) -> List[CalendarEvent]:
        """Get recent events for a user."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = (
            select(CalendarEvent)
            .where(
                and_(
                    CalendarEvent.user_id == user_id,
                    or_(
                        CalendarEvent.created_at >= cutoff_date,
                        CalendarEvent.updated_at >= cutoff_date
                    )
                )
            )
            .order_by(CalendarEvent.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
        
    # Event Occurrence Methods
    async def get_event_occurrence(self, event_id: int, occurrence_num: int) -> Optional[EventOccurrence]:
        """Get a specific occurrence of a recurring event."""
        query = select(EventOccurrence).where(
            and_(
                EventOccurrence.calendar_event_id == event_id,
                EventOccurrence.occurrence_num == occurrence_num
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def update_event_occurrence(self, occurrence_id: int, update_data: dict) -> Optional[EventOccurrence]:
        """Update an event occurrence."""
        query = select(EventOccurrence).where(EventOccurrence.id == occurrence_id)
        result = await self.db.execute(query)
        occurrence = result.scalars().first()
        
        if occurrence:
            for key, value in update_data.items():
                if hasattr(occurrence, key):
                    setattr(occurrence, key, value)
            await self.db.flush()
            return occurrence
        return None
    
    async def get_event_occurrences(self, event_id: int) -> List[EventOccurrence]:
        """Get all occurrences for an event."""        
        query = select(EventOccurrence).where(EventOccurrence.calendar_event_id == event_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_event_occurrence(self, occurrence_id: int) -> bool:
        """Delete an event occurrence record."""
        query = select(EventOccurrence).where(
            EventOccurrence.id == occurrence_id)
        result = await self.db.execute(query)
        occurrence = result.scalars().first()

        if occurrence:
            await self.db.delete(occurrence)
            await self.db.flush()
            return True
        return False
        
    async def update_event_occurrence_by_info(self, event_id: int, occurrence_num: int, update_data: dict) -> Optional[EventOccurrence]:
        """Update an event occurrence by event_id and occurrence_num."""
        occurrence = await self.get_event_occurrence(event_id, occurrence_num)
        
        if occurrence:
            for key, value in update_data.items():
                if hasattr(occurrence, key):
                    setattr(occurrence, key, value)
            await self.db.flush()
            return occurrence
        return None
