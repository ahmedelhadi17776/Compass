from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from Backend.data_layer.database.models.calendar_event import CalendarEvent, RecurrenceType, EventType
from Backend.data_layer.repositories.event_repository import EventRepository
from Backend.data_layer.database.models.event_occurrence import EventOccurrence
from Backend.data_layer.repositories.event_repository import EventNotFoundError
from Backend.ai_services.rag.rag_service import RAGService
from Backend.utils.cache_utils import cache_response, cache_entity, invalidate_cache
import asyncio
import logging
import json

logger = logging.getLogger(__name__)


class EventUpdateError(Exception):
    """Custom exception for event update errors."""
    def __init__(self, message: str, status_code: int = 400, error_code: str = "EVENT_UPDATE_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)
        
    def __str__(self):
        return self.message


class EventService:
    def __init__(self, repository: EventRepository):
        self.repo = repository
        self.rag_service = RAGService()

    async def update_event_status(self, event_id: int, new_status: str, user_id: int) -> CalendarEvent:
        """Update event status with validation and history tracking."""
        try:
            event = await self.repo.get_event(event_id)
            if not event:
                raise EventNotFoundError(f"Event {event_id} not found")

            # Update event status
            updated_event = await self.repo.update_event(
                event_id, {"status": new_status, "updated_at": datetime.utcnow()}
            )

            return updated_event

        except Exception as e:
            logger.error(f"Error updating event status: {str(e)}")
            raise EventUpdateError(f"Failed to update event status: {str(e)}")

    async def create_event(
        self,
        title: str,
        description: Optional[str],
        user_id: int,
        start_date: datetime,
        duration: Optional[float] = None,
        due_date: Optional[datetime] = None,
        event_type: EventType = EventType.NONE,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        task_id: Optional[int] = None,
        location: Optional[str] = None,
        is_all_day: bool = False,
        external_id: Optional[str] = None,
        recurrence: RecurrenceType = RecurrenceType.NONE,
        recurrence_custom_days: Optional[List[str]] = None,
        recurrence_end_date: Optional[datetime] = None,
        recurrence_count: Optional[int] = None,
        reminder_minutes_before: Optional[int] = None,
        notification_method: Optional[str] = None,
        time_zone: Optional[str] = None,
        transparency: Optional[str] = "opaque",
        color: Optional[str] = None
    ) -> CalendarEvent:
        """Create a new event and index it in RAG knowledge base."""
        if not start_date:
            raise ValueError("start_date is required for event creation")

        if due_date and start_date > due_date:
            raise ValueError("Start date must be before due date")

        if duration and duration < 0:
            raise ValueError("Duration must be positive")

        event_data = {
            "title": title,
            "description": description,
            "user_id": user_id,
            "due_date": due_date,
            "event_type": event_type,
            "status": status,
            "priority": priority,
            "task_id": task_id,
            "location": location,
            "is_all_day": is_all_day,
            "external_id": external_id,
            "recurrence": recurrence,
            "recurrence_custom_days": recurrence_custom_days,
            "recurrence_end_date": recurrence_end_date,
            "recurrence_count": recurrence_count,
            "reminder_minutes_before": reminder_minutes_before,
            "time_zone": time_zone,
            "transparency": transparency,
            "color": color,
            "notification_method": notification_method
        }

        event = await self.repo.create(start_date=start_date, duration=duration, **event_data)

        # Generate event occurrences for recurring events
        if recurrence != RecurrenceType.NONE:
            current_date = start_date
            occurrence_num = 0

            while not recurrence_end_date or current_date <= recurrence_end_date:
                # Create occurrence data
                occurrence_data = {
                    "calendar_event_id": event.id,
                    "occurrence_num": occurrence_num,
                    "title": title,
                    "start_date": current_date,
                    "due_date": current_date + timedelta(hours=duration) if duration else None,
                    "status": status,
                    "priority": priority,
                    "modified_by_id": user_id
                }

                # Create the occurrence record
                await self.repo.create_event_occurrence(occurrence_data)

                # Calculate next occurrence date
                if recurrence == RecurrenceType.DAILY:
                    current_date += timedelta(days=1)
                elif recurrence == RecurrenceType.WEEKLY:
                    current_date += timedelta(weeks=1)
                elif recurrence == RecurrenceType.BIWEEKLY:
                    current_date += timedelta(weeks=2)
                elif recurrence == RecurrenceType.MONTHLY:
                    current_date += relativedelta(months=1)
                elif recurrence == RecurrenceType.YEARLY:
                    current_date += relativedelta(years=1)
                elif recurrence == RecurrenceType.CUSTOM and recurrence_custom_days:
                    custom_days = [d for d in recurrence_custom_days]
                    if custom_days:
                        current_date += timedelta(
                            days=int(custom_days[occurrence_num % len(custom_days)]))
                    else:
                        break
                else:
                    break

                occurrence_num += 1

        # Index the event in RAG knowledge base
        try:
            content = f"{title}\n{description}" if description else title
            await self.rag_service.add_to_knowledge_base(
                content=content,
                metadata={
                    "id": str(event.id),
                    "title": title,
                    "event_type": str(event_type),
                    "user_id": user_id
                }
            )
        except Exception as e:
            logger.error(f"Error indexing event in RAG: {str(e)}")

        return event

    async def update_event(self, event_id: int, event_data: Dict, update_option: str = "this_occurrence") -> CalendarEvent:
        """Update an existing event.

        Args:
            event_id: The ID of the event to update
            event_data: Dictionary containing the fields to update
            update_option: How to handle recurring events:
                - "this_occurrence": Update only this specific occurrence
                - "this_and_future_occurrences": Update this and all future occurrences
                - "all_occurrences": Update the original event and all occurrences
        """
        # Extract the occurrence information from the event_id if it's a virtual ID
        occurrence_num = 0
        original_event_id = event_id
        is_virtual_id = False

        # Check if this is a virtual occurrence ID (e.g., "123_2" for the 3rd occurrence of event 123)
        event_id_str = str(event_id)
        if '_' in event_id_str:
            parts = event_id_str.split('_')
            original_event_id = int(parts[0])
            occurrence_num = int(parts[1])
            is_virtual_id = True
            
        # Get existing event first - using the original event ID, not the virtual ID
        existing_event = await self.repo.get_event(original_event_id)
        if not existing_event:
            raise EventNotFoundError(f"Event {original_event_id} not found")

        # Check if this is a recurring event
        is_recurring = existing_event.recurrence != RecurrenceType.NONE

        # If this is a non-recurring event, always update all occurrences
        if not is_recurring:
            update_option = "all_occurrences"
            
        # If this is a recurring event and we're updating only this occurrence
        if is_recurring and update_option == "this_occurrence" and (is_virtual_id or occurrence_num > 0):
            # For single occurrence updates, we don't modify the original event
            # Instead, we create or update an EventOccurrence record

            # Get or create the occurrence record
            occurrence = await self.repo.get_event_occurrence(original_event_id, occurrence_num)

            # Prepare occurrence data
            occurrence_data = {
                'calendar_event_id': original_event_id,
                'occurrence_num': occurrence_num,
                'modified_by_id': event_data.get('modified_by_id', existing_event.user_id)
            }

            # Add all the fields that can be modified for a specific occurrence
            for field in ['title', 'description', 'status', 'priority', 'event_type',
                         'start_date', 'duration', 'due_date', 'location', 'is_all_day', 
                         'transparency', 'color', 'time_zone']:
                if field in event_data:
                    occurrence_data[field] = event_data[field]

            # If we don't have start_date in the update data but we need it for a new occurrence
            if 'start_date' not in occurrence_data and not occurrence:
                # Calculate the start date for this occurrence based on the recurrence pattern
                occurrence_data['start_date'] = self._calculate_occurrence_start_date(
                    existing_event, occurrence_num)

            # Create or update the occurrence
            if occurrence:
                updated_occurrence = await self.repo.update_event_occurrence(occurrence.id, occurrence_data)
            else:
                updated_occurrence = await self.repo.create_event_occurrence(occurrence_data)

            # Return the original event (not modified)
            return existing_event
            
        elif is_recurring and update_option == "this_and_future_occurrences":
            # Update this occurrence and all future occurrences
            # Use the occurrence_num from virtual ID if available
            occ_num = occurrence_num if is_virtual_id else 0
            
            # First, update the base event to reflect the changes
            # but we need to keep the original recurrence pattern
            base_event_data = event_data.copy()
            
            # Get all occurrences for this event
            all_occurrences = await self.repo.get_event_occurrences(original_event_id)
            
            # Create a copy of event_data without date-related fields
            occurrence_update_data = event_data.copy()
            if 'start_date' in occurrence_update_data:
                del occurrence_update_data['start_date']
            if 'due_date' in occurrence_update_data:
                del occurrence_update_data['due_date']
            if 'duration' in occurrence_update_data:
                del occurrence_update_data['duration']
            
            # Update existing future occurrences with the new data while preserving their dates
            for occ in all_occurrences:
                if occ.occurrence_num >= occ_num:
                    # Create occurrence-specific update data
                    occ_data = occurrence_update_data.copy()
                    occ_data['modified_by_id'] = event_data.get('modified_by_id', existing_event.user_id)
                    
                    # Update the occurrence
                    await self.repo.update_event_occurrence(occ.id, occ_data)
            
            # Update the original event with the new data
            updated_event = await self.repo.update_event(original_event_id, event_data)
            
            # Get the updated parent event
            parent_event = await self.repo.get_event(original_event_id)
            if not parent_event:
                raise EventNotFoundError(f"Failed to retrieve updated event {original_event_id}")
            
            # If there are no occurrences yet, or we need to generate more future occurrences,
            # use _regenerate_future_occurrences with the last known occurrence number
            max_occurrence_num = max([o.occurrence_num for o in all_occurrences]) if all_occurrences else occ_num - 1
            
            # Generate any missing occurrences if we have a recurrence end date
            if parent_event.recurrence_end_date:
                await self._regenerate_future_occurrences(
                    parent_event,
                    start_occurrence_num=max_occurrence_num + 1,
                    modified_by_id=event_data.get('modified_by_id', parent_event.user_id),
                    regenerate_all=False
                )
            
            return updated_event
            
        else:
            # Normal update behavior for non-recurring events or when updating all occurrences
            
            # Validate date fields
            if "start_date" in event_data or "duration" in event_data:
                new_start = event_data.get("start_date", existing_event.start_date)
                new_duration = event_data.get("duration", existing_event.duration)

                if new_duration and new_duration < 0:
                    raise EventUpdateError("Duration must be positive")

                event_data["start_date"] = new_start
                event_data["duration"] = new_duration

            # Validate recurrence end date
            if "recurrence_end_date" in event_data and event_data["recurrence_end_date"]:
                start_date = event_data.get("start_date", existing_event.start_date)
                if event_data["recurrence_end_date"] < start_date:
                    raise EventUpdateError("Recurrence end date cannot be before start date")

            # Update the event
            updated_event = await self.repo.update_event(original_event_id, event_data)

            # If this is a recurring event and we're updating all occurrences,
            # we should also update any existing occurrence records to match the new base event
            if is_recurring and update_option == "all_occurrences":
                # Get all occurrences for this event
                occurrences = await self.repo.get_event_occurrences(original_event_id)
                
                # Create a copy of event_data without date-related fields
                occurrence_update_data = event_data.copy()
                if 'start_date' in occurrence_update_data:
                    del occurrence_update_data['start_date']
                if 'due_date' in occurrence_update_data:
                    del occurrence_update_data['due_date']
                if 'duration' in occurrence_update_data:
                    del occurrence_update_data['duration']
                
                # Update each occurrence with the new data while preserving their dates
                for occurrence in occurrences:
                    # Create occurrence-specific update data
                    occ_data = occurrence_update_data.copy()
                    occ_data['modified_by_id'] = event_data.get('modified_by_id', existing_event.user_id)
                    
                    # Update the occurrence
                    await self.repo.update_event_occurrence(occurrence.id, occ_data)
                    
                # If there are no occurrences yet, or we need to generate more future occurrences,
                # use _regenerate_future_occurrences with the last known occurrence number
                max_occurrence_num = max([o.occurrence_num for o in occurrences]) if occurrences else -1
                
                # Get the updated parent event
                parent_event = await self.repo.get_event(original_event_id)
                
                # Generate any missing occurrences
                if parent_event.recurrence_end_date:
                    await self._regenerate_future_occurrences(
                        parent_event,
                        start_occurrence_num=max_occurrence_num + 1,
                        modified_by_id=event_data.get('modified_by_id', parent_event.user_id),
                        regenerate_all=False
                    )

            # Invalidate cache for this event
            invalidate_cache('event', original_event_id)

            return updated_event
            
    def _calculate_occurrence_start_date(self, event: CalendarEvent, occurrence_num: int) -> datetime:
        """Calculate the start date for a specific occurrence of a recurring event."""
        base_start = event.start_date

        if event.recurrence == RecurrenceType.DAILY:
            return base_start + timedelta(days=occurrence_num)
        elif event.recurrence == RecurrenceType.WEEKLY:
            return base_start + timedelta(weeks=occurrence_num)
        elif event.recurrence == RecurrenceType.BIWEEKLY:
            return base_start + timedelta(weeks=2 * occurrence_num)
        elif event.recurrence == RecurrenceType.MONTHLY:
            # Add months using relative delta to handle month boundaries correctly
            return base_start + relativedelta(months=occurrence_num)
        elif event.recurrence == RecurrenceType.YEARLY:
            return base_start + relativedelta(years=occurrence_num)
        elif event.recurrence == RecurrenceType.CUSTOM and event.recurrence_custom_days:
            # For custom recurrence, calculate based on the custom days pattern
            custom_days = event.recurrence_custom_days
            if custom_days:
                # Convert string array to integers if needed
                if isinstance(custom_days[0], str):
                    custom_days = [int(d) for d in custom_days]

                # Calculate total days based on the pattern
                if len(custom_days) > 0:
                    # Calculate how many complete cycles and remaining days
                    complete_cycles = occurrence_num // len(custom_days)
                    remaining_idx = occurrence_num % len(custom_days)

                    # Calculate days from complete cycles
                    total_days = sum(custom_days) * complete_cycles

                    # Add days from the remaining partial cycle
                    total_days += sum(custom_days[:remaining_idx])

                    return base_start + timedelta(days=total_days)

            # Default fallback
            return base_start
        else:
            return base_start
            
    @cache_entity(entity_type='event')
    async def get_event(self, event_id: int) -> Optional[CalendarEvent]:
        """Get an event by ID with error handling."""
        try:
            event = await self.repo.get_event(event_id)
            if not event:
                return None
            return event
        except Exception as e:
            logger.error(f"Error getting event: {str(e)}")
            return None
            
    async def get_event_with_details(self, event_id: int) -> Optional[CalendarEvent]:
        """Get an event with all its related details."""
        try:
            event = await self.repo.get_event_with_details(event_id)
            if not event:
                raise EventNotFoundError(f"Event {event_id} not found")
            return event
        except Exception as e:
            logger.error(f"Error getting event details: {str(e)}")
            return None
            
    @cache_response(cache_type='event_list')
    async def get_events_in_date_range(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        include_recurring: bool = True
    ) -> List[CalendarEvent]:
        """Get events within a specific date range."""
        try:
            # Ensure timezone-naive datetime objects
            if start_date and start_date.tzinfo:
                start_date = start_date.replace(tzinfo=None)
            if end_date and end_date.tzinfo:
                end_date = end_date.replace(tzinfo=None)
                
            events = await self.repo.get_events_in_date_range(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                include_recurring=include_recurring
            )
            
            return events
        except Exception as e:
            logger.error(f"Error getting events in date range: {str(e)}")
            return []
            
    async def get_events_with_occurrences(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        """Get all events with their occurrences for a specific date range."""
        try:
            # Ensure timezone-naive datetime objects
            if start_date and start_date.tzinfo:
                start_date = start_date.replace(tzinfo=None)
            if end_date and end_date.tzinfo:
                end_date = end_date.replace(tzinfo=None)
                
            events = await self.repo.get_events_with_occurrences(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            return events
        except Exception as e:
            logger.error(f"Error getting events with occurrences: {str(e)}")
            return []
            
    async def delete_event(self, event_id: int, user_id: Optional[int] = None) -> bool:
        """Delete an event by ID."""
        try:
            if user_id:
                result = await self.repo.delete(event_id, user_id)
            else:
                result = await self.repo.delete_event(event_id)
                
            if result:
                # Invalidate cache for this event
                invalidate_cache('event', event_id)
            return result
        except Exception as e:
            logger.error(f"Error deleting event: {str(e)}")
            return False
            
    async def expand_recurring_event(self, event: CalendarEvent, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Expand a recurring event into individual occurrences within a date range.
        
        This method takes a recurring event and generates virtual occurrences
        based on the recurrence pattern for display in calendar views.
        
        Args:
            event: The recurring event to expand
            start_date: Start of the date range
            end_date: End of the date range
            
        Returns:
            List of event occurrence dictionaries with start_date and end_date
        """
        try:
            # Handle case where event might not have recurrence
            if not hasattr(event, 'recurrence') or event.recurrence == RecurrenceType.NONE:
                # Non-recurring event, just return the original
                return [{
                    "id": str(event.id) if hasattr(event, 'id') else "unknown",
                    "title": event.title if hasattr(event, 'title') else "Untitled Event",
                    "start_date": event.start_date if hasattr(event, 'start_date') else None,
                    "due_date": event.due_date if hasattr(event, 'due_date') else None,
                    "duration": event.duration if hasattr(event, 'duration') else None,
                    "is_recurring": False,
                    "is_original": True,
                    "status": event.status.value if hasattr(event.status, 'value') else event.status,
                    "priority": event.priority.value if hasattr(event.priority, 'value') else event.priority,
                    "event_type": event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
                    "recurrence": event.recurrence,
                    "recurrence_end_date": event.recurrence_end_date
                }]
                
            occurrences = []
            current_date = event.start_date
            occurrence_num = 0
            
            # Safely handle recurrence_end_date
            recurrence_end = None
            if hasattr(event, 'recurrence_end_date') and event.recurrence_end_date:
                recurrence_end = event.recurrence_end_date
            else:
                recurrence_end = end_date + timedelta(days=365)
                
            # Determine recurrence type and set appropriate delta
            delta = timedelta(days=1)  # Default to daily
            
            if hasattr(event, 'recurrence'):
                if event.recurrence == RecurrenceType.DAILY:
                    delta = timedelta(days=1)
                elif event.recurrence == RecurrenceType.WEEKLY:
                    delta = timedelta(weeks=1)
                elif event.recurrence == RecurrenceType.BIWEEKLY:
                    delta = timedelta(weeks=2)
                elif event.recurrence == RecurrenceType.MONTHLY:
                    # Calculate next month by adding the same day in the next month
                    # This handles month length differences properly
                    current_month = current_date.month
                    current_year = current_date.year
                    next_month = current_month + 1
                    next_year = current_year
                    
                    if next_month > 12:
                        next_month = 1
                        next_year += 1
                        
                    # Handle day overflow (e.g., Jan 31 -> Feb 28/29)
                    try:
                        delta = datetime(next_year, next_month,
                                        current_date.day) - current_date
                    except ValueError:
                        # If the day doesn't exist in the next month, use the last day
                        if next_month == 2:  # February
                            # Check for leap year
                            last_day = 29 if (next_year % 4 == 0 and (
                                next_year % 100 != 0 or next_year % 400 == 0)) else 28
                        elif next_month in [4, 6, 9, 11]:  # 30-day months
                            last_day = 30
                        else:  # 31-day months
                            last_day = 31
                        delta = datetime(next_year, next_month,
                                        last_day) - current_date
                elif event.recurrence == RecurrenceType.YEARLY:
                    # Calculate next year on the same month and day
                    # This handles leap years properly
                    try:
                        delta = datetime(
                            current_date.year + 1, current_date.month, current_date.day) - current_date
                    except ValueError:
                        # Handle February 29 in leap years
                        if current_date.month == 2 and current_date.day == 29:
                            delta = datetime(
                                current_date.year + 1, 2, 28) - current_date
                elif event.recurrence == RecurrenceType.CUSTOM and hasattr(event, 'recurrence_custom_days') and event.recurrence_custom_days:
                    # Custom recurrence is handled differently
                    return self._expand_custom_recurrence(event, start_date, end_date)
                    
            # Generate occurrences until we reach the end date or recurrence end
            while current_date <= min(end_date, recurrence_end):
                # Only include occurrences that fall within our range
                if current_date >= start_date:
                    # Calculate the due date for this occurrence
                    occurrence_due_date = None
                    if hasattr(event, 'due_date') and event.due_date:
                        # Maintain the same duration between start and due date
                        original_duration = (
                            event.due_date - event.start_date).total_seconds()
                        occurrence_due_date = current_date + \
                            timedelta(seconds=original_duration)
                            
                    occurrences.append({
                        # Virtual ID for the occurrence
                        "id": f"{event.id}_{occurrence_num}",
                        "original_id": event.id,  # Reference to the original event
                        "title": event.title if hasattr(event, 'title') else "Untitled Event",
                        "start_date": current_date,
                        "due_date": occurrence_due_date,
                        "duration": event.duration if hasattr(event, 'duration') else None,
                        "is_recurring": True,
                        "is_original": occurrence_num == 0,
                        "occurrence_num": occurrence_num,
                        "status": event.status.value if hasattr(event.status, 'value') else event.status,
                        "priority": event.priority.value if hasattr(event.priority, 'value') else event.priority,
                        "event_type": event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
                        "recurrence": event.recurrence,
                        "recurrence_end_date": event.recurrence_end_date
                    })
                    
                # Move to the next occurrence
                current_date += delta
                occurrence_num += 1
                
            return occurrences
        except Exception as e:
            logger.error(f"Error expanding recurring event: {str(e)}")
            # Return just the original event as a fallback
            return [{
                "id": str(event.id) if hasattr(event, 'id') else "unknown",
                "title": event.title if hasattr(event, 'title') else "Untitled Event",
                "start_date": event.start_date if hasattr(event, 'start_date') else None,
                "due_date": event.due_date if hasattr(event, 'due_date') else None,
                "duration": event.duration if hasattr(event, 'duration') else None,
                "is_recurring": False,
                "is_original": True,
                "status": event.status.value if hasattr(event.status, 'value') else event.status,
                "priority": event.priority.value if hasattr(event.priority, 'value') else event.priority,
                "event_type": event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
                "recurrence": event.recurrence,
                "recurrence_end_date": event.recurrence_end_date,
                "error": str(e)
            }]

    def _expand_custom_recurrence(self, event: CalendarEvent, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Handle custom recurrence patterns with specific days."""
        try:
            occurrences = []

            # Start with the original event
            occurrences.append({
                "id": str(event.id) if hasattr(event, 'id') else "unknown",
                "title": event.title if hasattr(event, 'title') else "Untitled Event",
                "start_date": event.start_date if hasattr(event, 'start_date') else None,
                "due_date": event.due_date if hasattr(event, 'due_date') else None,
                "duration": event.duration if hasattr(event, 'duration') else None,
                "is_recurring": True,
                "is_original": True,
                "occurrence_num": 0,
                "status": event.status.value if hasattr(event.status, 'value') else event.status,
                "priority": event.priority.value if hasattr(event.priority, 'value') else event.priority,
                "event_type": event.event_type.value if hasattr(event.event_type, 'value') else event.event_type
            })

            # Check if event has recurrence_custom_days attribute
            if not hasattr(event, 'recurrence_custom_days') or not event.recurrence_custom_days:
                return occurrences

            try:
                custom_days = event.recurrence_custom_days
                day_mapping = {
                    "Monday": 0, "Tuesday": 1, "Wednesday": 2,
                    "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
                }

                # Convert day names to day numbers (0=Monday, 6=Sunday)
                day_numbers = []
                for day in custom_days:
                    if day in day_mapping:
                        day_numbers.append(day_mapping[day])
                    elif isinstance(day, str) and day.isdigit():
                        day_numbers.append(int(day))
                    elif isinstance(day, int):
                        day_numbers.append(day)

                if not day_numbers:
                    return occurrences

                # Start from the day after the original event
                current_date = event.start_date + timedelta(days=1)
                occurrence_num = 1

                # Safely handle recurrence_end_date
                recurrence_end = None
                if hasattr(event, 'recurrence_end_date') and event.recurrence_end_date:
                    recurrence_end = event.recurrence_end_date
                else:
                    recurrence_end = end_date + timedelta(days=365)

                # Generate occurrences until we reach the end date or recurrence end
                while current_date <= min(end_date, recurrence_end):
                    # Check if the current day is in our custom days
                    if current_date.weekday() in day_numbers:
                        # Calculate the due date for this occurrence
                        occurrence_due_date = None
                        if hasattr(event, 'due_date') and event.due_date:
                            # Maintain the same duration between start and due date
                            original_duration = (
                                event.due_date - event.start_date).total_seconds()
                            occurrence_due_date = current_date + \
                                timedelta(seconds=original_duration)

                        occurrences.append({
                            # Virtual ID for the occurrence
                            "id": f"{event.id}_{occurrence_num}",
                            "original_id": event.id,  # Reference to the original event
                            "title": event.title if hasattr(event, 'title') else "Untitled Event",
                            "start_date": current_date,
                            "due_date": occurrence_due_date,
                            "duration": event.duration if hasattr(event, 'duration') else None,
                            "is_recurring": True,
                            "is_original": False,
                            "occurrence_num": occurrence_num,
                            "status": event.status.value if hasattr(event.status, 'value') else event.status,
                            "priority": event.priority.value if hasattr(event.priority, 'value') else event.priority,
                            "event_type": event.event_type.value if hasattr(event.event_type, 'value') else event.event_type
                        })
                        occurrence_num += 1

                    # Move to the next day
                    current_date += timedelta(days=1)

                return occurrences
            except Exception as e:
                logger.error(
                    f"Error processing custom recurrence days: {str(e)}")
                return occurrences
        except Exception as e:
            logger.error(f"Error in _expand_custom_recurrence: {str(e)}")
            # Return just the original event as a fallback
            return [{
                "id": str(event.id) if hasattr(event, 'id') else "unknown",
                "title": event.title if hasattr(event, 'title') else "Untitled Event",
                "start_date": event.start_date if hasattr(event, 'start_date') else None,
                "due_date": event.due_date if hasattr(event, 'due_date') else None,
                "duration": event.duration if hasattr(event, 'duration') else None,
                "is_recurring": True,
                "is_original": True,
                "occurrence_num": 0,
                "status": event.status.value if hasattr(event.status, 'value') else event.status,
                "priority": event.priority.value if hasattr(event.priority, 'value') else event.priority,
                "event_type": event.event_type.value if hasattr(event.event_type, 'value') else event.event_type,
                "error": str(e)
            }]

    async def get_calendar_events(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None,
        include_recurring: bool = True
    ) -> List[Dict]:
        """Get events formatted for calendar view with expanded recurring events.

        This method retrieves events for a calendar view and optionally expands
        recurring events into individual occurrences.

        Args:
            start_date: Start of the calendar range
            end_date: End of the calendar range
            user_id: Optional user ID to filter events
            include_recurring: Whether to include recurring events

        Returns:
            List of event dictionaries formatted for calendar display
        """
        try:
            # Ensure timezone-naive datetime objects
            if start_date.tzinfo:
                start_date = start_date.replace(tzinfo=None)
            if end_date.tzinfo:
                end_date = end_date.replace(tzinfo=None)

            if not user_id:
                return []

            # Get all events in the date range
            events = await self.repo.get_events_in_date_range(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                include_recurring=include_recurring
            )

            calendar_events = []
            
            for event in events:
                # For recurring events, get their occurrences from the database
                if event.recurrence != RecurrenceType.NONE and include_recurring:
                    # Get occurrences for this event in the date range
                    occurrences = await self.repo.get_event_occurrences_in_range(
                        event_id=event.id,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    for occurrence in occurrences:
                        calendar_events.append({
                            'id': f"{event.id}_{occurrence.occurrence_num}",
                            'title': occurrence.title or event.title,
                            'start': occurrence.start_date,
                            'end': occurrence.due_date or (occurrence.start_date + timedelta(hours=event.duration) if event.duration else None),
                            'status': occurrence.status.value if occurrence.status else event.status.value,
                            'priority': occurrence.priority.value if occurrence.priority else event.priority.value,
                            'event_type': occurrence.event_type.value if occurrence.event_type else event.event_type.value,
                            'recurrence': event.recurrence.value,
                            'recurrence_end_date': event.recurrence_end_date,
                            'location': occurrence.location or event.location,
                            'is_all_day': occurrence.is_all_day if occurrence.is_all_day is not None else event.is_all_day,
                            'occurrence_num': occurrence.occurrence_num,
                            'is_modified': bool(occurrence.title or occurrence.description or occurrence.status or 
                                             occurrence.priority or occurrence.event_type or occurrence.location or 
                                             occurrence.is_all_day is not None)
                        })
                else:
                    # Non-recurring events are added as-is
                    calendar_events.append({
                        'id': str(event.id),
                        'title': event.title,
                        'start': event.start_date,
                        'end': event.due_date or (event.start_date + timedelta(hours=event.duration) if event.duration else None),
                        'status': event.status.value,
                        'priority': event.priority.value,
                        'event_type': event.event_type.value,
                        'recurrence': event.recurrence.value,
                        'recurrence_end_date': event.recurrence_end_date,
                        'location': event.location,
                        'is_all_day': event.is_all_day,
                        'is_modified': False
                    })

            # Sort events by start date
            calendar_events.sort(key=lambda x: x['start'])
            return calendar_events

        except Exception as e:
            logger.error(f"Error retrieving calendar events: {str(e)}")
            return []

    async def _regenerate_future_occurrences(
        self, 
        event: CalendarEvent, 
        start_occurrence_num: int,
        modified_by_id: int,
        regenerate_all: bool = False
    ) -> None:
        """Regenerate future occurrences of a recurring event starting from a specific occurrence number.
        
        Args:
            event: The recurring event to regenerate occurrences for
            start_occurrence_num: The occurrence number to start from
            modified_by_id: The user ID who triggered the regeneration
            regenerate_all: If True, regenerate all occurrences starting from 0, ignoring start_occurrence_num
        """
        if event.recurrence == RecurrenceType.NONE:
            return
            
        # Determine the starting occurrence number
        actual_start_num = 0 if regenerate_all else start_occurrence_num
            
        # Calculate the start date for the specified occurrence
        occurrence_start_date = self._calculate_occurrence_start_date(event, actual_start_num)
        
        # Initialize occurrence counter and current date
        occurrence_num = actual_start_num
        current_date = occurrence_start_date
        
        # Generate occurrences until reaching the recurrence end date
        while not event.recurrence_end_date or current_date <= event.recurrence_end_date:
            # Create occurrence data
            occurrence_data = {
                "calendar_event_id": event.id,
                "occurrence_num": occurrence_num,
                "start_date": current_date,
                "modified_by_id": modified_by_id
            }
            
            # Add the due date if the event has a duration
            if event.duration:
                occurrence_data["due_date"] = current_date + timedelta(hours=event.duration)
            elif event.due_date:
                # Maintain the same duration between start and due dates
                original_duration = (event.due_date - event.start_date).total_seconds()
                occurrence_data["due_date"] = current_date + timedelta(seconds=original_duration)
                
            # Create the occurrence record
            await self.repo.create_event_occurrence(occurrence_data)
            
            # Calculate next occurrence date
            if event.recurrence == RecurrenceType.DAILY:
                current_date += timedelta(days=1)
            elif event.recurrence == RecurrenceType.WEEKLY:
                current_date += timedelta(weeks=1)
            elif event.recurrence == RecurrenceType.BIWEEKLY:
                current_date += timedelta(weeks=2)
            elif event.recurrence == RecurrenceType.MONTHLY:
                current_date += relativedelta(months=1)
            elif event.recurrence == RecurrenceType.YEARLY:
                current_date += relativedelta(years=1)
            elif event.recurrence == RecurrenceType.CUSTOM and event.recurrence_custom_days:
                custom_days = event.recurrence_custom_days
                if custom_days:
                    # Handle custom recurrence pattern
                    try:
                        if isinstance(custom_days[0], str) and custom_days[0].isdigit():
                            custom_days = [int(d) for d in custom_days]
                        
                        # Get the index in the custom_days array
                        idx = occurrence_num % len(custom_days)
                        days_to_add = custom_days[idx]
                        
                        current_date += timedelta(days=int(days_to_add))
                    except (ValueError, IndexError) as e:
                        logger.error(f"Error calculating custom recurrence: {str(e)}")
                        # Default fallback
                        current_date += timedelta(days=1)
                else:
                    # No custom days defined, can't continue
                    break
            else:
                # Unknown recurrence type, stop generating
                break
                
            occurrence_num += 1
