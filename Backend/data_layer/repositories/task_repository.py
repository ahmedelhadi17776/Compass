from typing import Dict, List, Optional, cast, Sequence
from sqlalchemy import select, and_, or_, Float
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from Backend.data_layer.database.models.calendar_event import RecurrenceType
from Backend.data_layer.database.models.task import Task, TaskStatus, TaskPriority
from Backend.data_layer.database.models.task_history import TaskHistory
from Backend.data_layer.database.models.task_agent_interaction import TaskAgentInteraction
from Backend.data_layer.database.models.ai_interactions import AIAgentInteraction
from datetime import datetime, timedelta
from Backend.data_layer.repositories.base_repository import BaseRepository
import logging
import json
from Backend.data_layer.database.models.task_occurrence import TaskOccurrence
from Backend.events.event_dispatcher import dispatcher
from Backend.events.event_registry import TASK_UPDATED

logger = logging.getLogger(__name__)


class TaskNotFoundError(Exception):
    """Raised when a task is not found."""
    pass


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db):
        self.db = db

    async def create(self, start_date: datetime, duration: Optional[float] = None, **task_data) -> Task:
        """Create a new task."""

        required_fields = {
            'title',
            'project_id',
            'organization_id',
            'creator_id',
            'status',
            'priority'
        }

        missing = required_fields - task_data.keys()
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        valid_columns = {c.name for c in Task.__table__.columns}
        filtered_data = {k: v for k,
                         v in task_data.items() if k in valid_columns}

        new_task = Task(
            start_date=start_date,
            duration=duration,
            **filtered_data
        )
        self.db.add(new_task)
        await self.db.flush()
        return new_task

    async def create_task_occurrence(self, occurrence_data: dict) -> None:
        """Create a task occurrence for a recurring task.

        Args:
            occurrence_data: Dictionary containing the occurrence data
        """
        from Backend.data_layer.database.models.task_occurrence import TaskOccurrence

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

        occurrence = TaskOccurrence(**occurrence_data)
        self.db.add(occurrence)
        await self.db.flush()

    async def get_by_id(self, task_id: int, user_id: Optional[int] = None) -> Optional[Task]:
        """Get a task by ID with optional user ID check."""
        query = select(Task).where(Task.id == task_id)
        if user_id is not None:
            query = query.where(Task.creator_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID without user_id check."""
        return await self.get_by_id(task_id)

    async def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID without user_id check."""
        task = await self.get_task(task_id)
        if task:
            await self.db.delete(task)
            await self.db.flush()
            return True
        return False

    async def update(self, id: int, user_id: int, **update_data) -> Optional[Task]:
        """Update a task. Implementation of abstract method from BaseRepository."""
        task = await self.get_by_id(id, user_id)
        if task:
            # Update task fields
            for key, value in update_data.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            await self.db.flush()
            await dispatcher.dispatch(TASK_UPDATED, {"task_id": task_id, "task_data": update_data})
            return task
        return None

    async def delete(self, id: int, user_id: int) -> bool:
        """Delete an entity. Implementation of abstract method from BaseRepository."""
        # Using delete_task with user_id check
        task = await self.get_by_id(id, user_id)
        if task:
            await self.db.delete(task)
            await self.db.flush()  # Consistent with delete_task
            return True
        return False

    async def get_user_tasks(self, user_id: int, status: Optional[str] = None) -> List[Task]:
        """Get all tasks for a user with optional status filter."""
        query = select(Task).where(Task.creator_id == user_id)
        if status:
            query = query.where(Task.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_task_with_details(self, task_id: int) -> Optional[Task]:
        """Get a task with all its related details."""
        query = (
            select(Task)
            .options(
                joinedload(Task.history),
                joinedload(Task.agent_interactions)
            )
            .where(Task.id == task_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def update_task(self, task_id: int, task_data: dict) -> Optional[Task]:
        """Update a task with the given data without user_id check."""
        task = await self.get_by_id(task_id)
        if not task:
            raise TaskNotFoundError(f"Task with id {task_id} not found")

        if "start_date" in task_data or "duration" in task_data:
            new_start = task_data.get("start_date", task.start_date)
            new_duration = task_data.get("duration", task.duration)

            if new_duration and new_duration < 0:
                raise ValueError("Duration must be positive")

            task.start_date = new_start
            task.duration = new_duration

        if "due_date" in task_data:
            task.due_date = task_data["due_date"]

        if "recurrence_end_date" in task_data:
            if task_data["recurrence_end_date"] and task_data["recurrence_end_date"] < task.start_date:
                raise ValueError(
                    "Recurrence end date cannot be before start date")

        # Update task fields
        for key, value in task_data.items():
            # Skip date fields as they're handled separately above
            if key not in ["start_date", "due_date", "duration"] and hasattr(task, key):
                setattr(task, key, value)

        await self.db.flush()
        await dispatcher.dispatch(TASK_UPDATED, {"task_id": task_id, "task_data": update_data})

        return task

    async def get_tasks_by_project(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        due_date: Optional[datetime] = None,
        duration: Optional[float] = None,
        recurrence: Optional[RecurrenceType] = None,
        end_date: Optional[datetime] = None,
        include_recurring: bool = True
    ) -> List[Task]:
        """Get tasks by project with optional filters and calendar support.

        This method supports calendar view by filtering tasks based on date ranges
        and handling recurring tasks appropriately.
        """
        # First, get all regular tasks and recurring tasks without occurrences
        query = select(Task).where(Task.project_id == project_id)

        # Apply filters
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if assignee_id:
            query = query.where(Task.assignee_id == assignee_id)
        if creator_id:
            query = query.where(Task.creator_id == creator_id)
        if recurrence:
            query = query.where(Task.recurrence == recurrence)
        
        # Calendar-specific filters for regular tasks
        if start_date and end_date:
            # For regular tasks, use direct date filtering
            date_filter = or_(
                # Non-recurring tasks within the range
                and_(
                    Task.start_date >= start_date,
                    Task.start_date <= end_date,
                    Task.recurrence == RecurrenceType.NONE
                ),
                # Tasks ending within the range
                and_(
                    Task.due_date >= start_date,
                    Task.due_date <= end_date
                ),
                # Tasks spanning across the range
                and_(
                    Task.start_date <= start_date,
                    Task.due_date >= end_date
                )
            )
            
            if not include_recurring:
                # If we don't want recurring tasks, add the filter
                query = query.where(and_(date_filter, Task.recurrence == RecurrenceType.NONE))
            else:
                # Otherwise, get regular tasks and recurring tasks without occurrences
                query = query.where(
                    or_(
                        date_filter,
                        and_(
                            Task.recurrence != RecurrenceType.NONE,
                            ~Task.occurrences.any()  # No occurrences
                        )
                    )
                )
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute the query to get regular tasks
        result = await self.db.execute(query)
        regular_tasks = list(result.scalars().all())
        
        # Now, get recurring tasks with occurrences if needed
        recurring_tasks = []
        if include_recurring:
            # Get recurring tasks with occurrences
            recurring_query = select(Task).where(
                and_(
                    Task.project_id == project_id,
                    Task.recurrence != RecurrenceType.NONE,
                    Task.occurrences.any()  # Has occurrences
                )
            )
            
            # Apply the same filters as before
            if status:
                recurring_query = recurring_query.where(Task.status == status)
            if priority:
                recurring_query = recurring_query.where(Task.priority == priority)
            if assignee_id:
                recurring_query = recurring_query.where(Task.assignee_id == assignee_id)
            if creator_id:
                recurring_query = recurring_query.where(Task.creator_id == creator_id)
            
            recurring_result = await self.db.execute(recurring_query)
            recurring_tasks_with_occurrences = list(recurring_result.scalars().all())
            
            # For each recurring task, get its occurrences
            for task in recurring_tasks_with_occurrences:
                # Get occurrences for this task
                occurrences = await self.get_task_occurrences_in_range(
                    task.id, 
                    start_date=start_date, 
                    end_date=end_date
                )
                
                # Add virtual tasks for each occurrence
                for occurrence in occurrences:
                    # Create a virtual task based on the occurrence
                    virtual_task = self._create_virtual_task_from_occurrence(task, occurrence)
                    recurring_tasks.append(virtual_task)
        
        # Combine regular and recurring tasks
        all_tasks = regular_tasks + recurring_tasks
        
        # Sort by start date
        all_tasks.sort(key=lambda t: t.start_date if t.start_date else datetime.max)
        
        return all_tasks
    
    async def get_task_occurrences_in_range(
        self, 
        task_id: int, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> List[TaskOccurrence]:
        """Get task occurrences within a date range."""
        query = select(TaskOccurrence).where(TaskOccurrence.task_id == task_id)
        
        if start_date and end_date:
            query = query.where(
                or_(
                    # Occurrences starting within the range
                    and_(
                        TaskOccurrence.start_date >= start_date,
                        TaskOccurrence.start_date <= end_date
                    ),
                    # Occurrences ending within the range
                    and_(
                        TaskOccurrence.due_date >= start_date,
                        TaskOccurrence.due_date <= end_date
                    ),
                    # Occurrences spanning across the range
                    and_(
                        TaskOccurrence.start_date <= start_date,
                        TaskOccurrence.due_date >= end_date
                    )
                )
            )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    def _create_virtual_task_from_occurrence(self, base_task: Task, occurrence: TaskOccurrence) -> Task:
        """Create a virtual task object from a task occurrence.
        
        This creates a copy of the base task with the occurrence's overridden properties.
        The task ID is modified to include the occurrence number for identification.
        """
        # Create a shallow copy of the base task
        virtual_task = Task()
        
        # Copy all attributes from the base task
        for column in Task.__table__.columns:
            if column.name != 'id':  # Don't copy the ID
                setattr(virtual_task, column.name, getattr(base_task, column.name))
        
        # Override with occurrence-specific attributes if they exist
        if occurrence.title:
            virtual_task.title = occurrence.title
        if occurrence.description:
            virtual_task.description = occurrence.description
        if occurrence.status:
            virtual_task.status = occurrence.status
        if occurrence.priority:
            virtual_task.priority = occurrence.priority
        if occurrence.assignee_id:
            virtual_task.assignee_id = occurrence.assignee_id
        if occurrence.reviewer_id:
            virtual_task.reviewer_id = occurrence.reviewer_id
        if occurrence.category_id:
            virtual_task.category_id = occurrence.category_id
        if occurrence.progress_metrics:
            virtual_task.progress_metrics = occurrence.progress_metrics
        if occurrence.blockers:
            virtual_task.blockers = occurrence.blockers
        if occurrence.health_score:
            virtual_task.health_score = occurrence.health_score
        if occurrence.risk_factors:
            virtual_task.risk_factors = occurrence.risk_factors
        
        # Always override date-related fields
        virtual_task.start_date = occurrence.start_date
        if occurrence.duration:
            virtual_task.duration = occurrence.duration
        if occurrence.due_date:
            virtual_task.due_date = occurrence.due_date
        
        # Set a virtual ID that combines the task ID and occurrence number
        # This will be used to identify the specific occurrence when updating
        virtual_task.id = int(f"{base_task.id}_{occurrence.occurrence_num}")
        
        # Add occurrence metadata
        virtual_task.is_occurrence = True
        virtual_task.occurrence_num = occurrence.occurrence_num
        virtual_task.original_task_id = base_task.id
        virtual_task.occurrence_id = occurrence.id
        
        return virtual_task

    async def get_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        due_date: Optional[datetime] = None,
        duration: Optional[float] = None,
        recurrence: Optional[RecurrenceType] = None,
        end_date: Optional[datetime] = None,
        include_recurring: bool = True
    ) -> List[Task]:
        
        """Get all tasks with optional filters and calendar support.

        This method supports calendar view by filtering tasks based on date ranges
        and handling recurring tasks appropriately.

        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return (pagination)
            status: Filter by task status
            priority: Filter by task priority
            assignee_id: Filter by assignee
            creator_id: Filter by creator
            start_date: Filter tasks starting on or after this date
            due_date: Filter tasks due on this date
            duration: Filter tasks with this duration
            recurrence: Filter tasks with this recurrence pattern
            end_date: Filter tasks ending before this date (for calendar range)
            include_recurring: Whether to include recurring tasks in results

        Returns:
            List of Task objects matching the criteria
        """
        query = select(Task).outerjoin(Task.occurrences)

        # Apply filters
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if assignee_id:
            query = query.where(Task.assignee_id == assignee_id)
        if creator_id:
            query = query.where(Task.creator_id == creator_id)
        if recurrence:
            query = query.where(Task.recurrence == recurrence)

        # Calendar-specific filters for regular tasks
        if start_date and end_date:
            # For regular tasks, use direct date filtering
            date_filter = or_(
                # Non-recurring tasks within the range
                and_(
                    Task.start_date >= start_date,
                    Task.start_date <= end_date,
                    Task.recurrence == RecurrenceType.NONE
                ),
                # Tasks ending within the range
                and_(
                    Task.due_date >= start_date,
                    Task.due_date <= end_date
                ),
                # Tasks spanning across the range
                and_(
                    Task.start_date <= start_date,
                    Task.due_date >= end_date
                )
            )

            if not include_recurring:
                # If we don't want recurring tasks, add the filter
                query = query.where(
                    and_(date_filter, Task.recurrence == RecurrenceType.NONE))
            else:
                # Otherwise, get regular tasks and recurring tasks without occurrences
                query = query.where(
                    or_(
                        date_filter,
                        and_(
                            Task.recurrence != RecurrenceType.NONE,
                            ~Task.occurrences.any()  # No occurrences
                        )
                    )
                )

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute the query to get regular tasks
        result = await self.db.execute(query)
        regular_tasks = list(result.scalars().all())

        # Now, get recurring tasks with occurrences if needed
        recurring_tasks = []
        if include_recurring:
            # Get recurring tasks with occurrences
            recurring_query = select(Task).where(
                and_(
                    Task.project_id == project_id,
                    Task.recurrence != RecurrenceType.NONE,
                    Task.occurrences.any()  # Has occurrences
                )
            )

            # Apply the same filters as before
            if status:
                recurring_query = recurring_query.where(Task.status == status)
            if priority:
                recurring_query = recurring_query.where(
                    Task.priority == priority)
            if assignee_id:
                recurring_query = recurring_query.where(
                    Task.assignee_id == assignee_id)
            if creator_id:
                recurring_query = recurring_query.where(
                    Task.creator_id == creator_id)

            recurring_result = await self.db.execute(recurring_query)
            recurring_tasks_with_occurrences = list(
                recurring_result.scalars().all())

            # For each recurring task, get its occurrences
            for task in recurring_tasks_with_occurrences:
                # Get occurrences for this task
                occurrences = await self.get_task_occurrences_in_range(
                    task.id,
                    start_date=start_date,
                    end_date=end_date
                )

                # Add virtual tasks for each occurrence
                for occurrence in occurrences:
                    # Create a virtual task based on the occurrence
                    virtual_task = self._create_virtual_task_from_occurrence(
                        task, occurrence)
                    recurring_tasks.append(virtual_task)

        # Combine regular and recurring tasks
        tasks = regular_tasks + recurring_tasks

        # Sort by start date
        tasks.sort(
            key=lambda t: t.start_date if t.start_date else datetime.max)

        return tasks

    async def add_task_history(self, task_id: int, user_id: int, field_name: str, old_value: str, new_value: str, action: str = "update") -> TaskHistory:
        """Add a task history entry."""
        history = TaskHistory(
            task_id=task_id,
            user_id=user_id,
            action=action,
            field=field_name,
            old_value=old_value,
            new_value=new_value
        )
        self.db.add(history)
        await self.db.flush()
        return history

    async def get_task_history(
        self,
        task_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[TaskHistory]:
        """Get paginated task history entries for a specific task."""
        query = (
            select(TaskHistory)
            .where(TaskHistory.task_id == task_id)
            .order_by(TaskHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_recent_tasks(
        self,
        user_id: int,
        days: int = 7,
        limit: int = 10
    ) -> List[Task]:
        """Get recent tasks for a user."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = (
            select(Task)
            .where(
                and_(
                    Task.creator_id == user_id,
                    or_(
                        Task.created_at >= cutoff_date,
                        Task.status_updated_at >= cutoff_date
                    )
                )
            )
            .order_by(Task.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_task_dependencies(self, task_id: int, dependencies: List[int]) -> bool:
        """Update task dependencies."""
        try:
            task = await self.get_task(task_id)
            if not task:
                return False

            task._dependencies_list = json.dumps(dependencies)
            await self.db.flush()
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating task dependencies: {str(e)}")
            return False

    async def track_ai_interaction(self, task_id: int, ai_result: Dict) -> None:
        """Track AI interaction for a task."""
        try:
            # Use create_task_agent_interaction to avoid code duplication
            await self.create_task_agent_interaction(
                task_id=task_id,
                agent_type=ai_result.get("agent_type", "unknown"),
                interaction_type=ai_result.get("interaction_type", "analysis"),
                result=ai_result.get("result"),
                success_rate=ai_result.get("confidence", 1.0)
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to track AI interaction: {str(e)}")
            raise

    async def create_task_agent_interaction(self, **interaction_data) -> TaskAgentInteraction:
        """Create a new task agent interaction."""
        interaction = TaskAgentInteraction(**interaction_data)
        self.db.add(interaction)
        await self.db.flush()
        return interaction

    async def get_task_agent_interactions(self, task_id: int) -> List[TaskAgentInteraction]:
        """Get all agent interactions for a task."""
        query = select(TaskAgentInteraction).where(
            TaskAgentInteraction.task_id == task_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_task_ai_metrics(self, task_id: int, metrics: Dict) -> Optional[Task]:
        """Update AI-related metrics for a task."""
        task = await self.get_task(task_id)
        if task:
            task.ai_suggestions = metrics.get(
                'suggestions', task.ai_suggestions)
            task.complexity_score = metrics.get(
                'complexity_score', task.complexity_score)
            task.health_score = metrics.get('health_score', task.health_score)
            task.risk_factors = metrics.get('risk_factors', task.risk_factors)
            await self.db.flush()
            return task
        return None

    async def track_ai_optimization(self, task_id: int, optimization_data: Dict) -> None:
        """Track AI optimization attempts for a task."""
        try:
            # Use create_task_agent_interaction to avoid code duplication
            await self.create_task_agent_interaction(
                task_id=task_id,
                agent_type="optimizer",
                interaction_type="optimization",
                result=optimization_data.get('result')
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error tracking AI optimization: {str(e)}")
            raise

    # Task Comment Methods
    async def create_comment(self, task_id: int, user_id: int, content: str, parent_id: Optional[int] = None) -> "TaskComment":
        """Create a new comment for a task."""
        from Backend.data_layer.database.models.task_comment import TaskComment

        comment = TaskComment(
            task_id=task_id,
            user_id=user_id,
            content=content,
            parent_id=parent_id
        )
        self.db.add(comment)
        await self.db.flush()
        return comment

    async def get_task_comments(self, task_id: int, skip: int = 0, limit: int = 50) -> List["TaskComment"]:
        """Get all comments for a task."""
        from Backend.data_layer.database.models.task_comment import TaskComment
        from sqlalchemy import select

        query = (
            select(TaskComment)
            .where(TaskComment.task_id == task_id)
            .order_by(TaskComment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_comment(self, comment_id: int) -> Optional["TaskComment"]:
        """Get a comment by ID."""
        from Backend.data_layer.database.models.task_comment import TaskComment
        from sqlalchemy import select

        query = select(TaskComment).where(TaskComment.id == comment_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def update_comment(self, comment_id: int, user_id: int, content: str) -> Optional["TaskComment"]:
        """Update a comment."""
        comment = await self.get_comment(comment_id)
        if comment and comment.user_id == user_id:
            comment.content = content
            comment.updated_at = datetime.utcnow()
            await self.db.flush()
            return comment
        return None

    async def delete_comment(self, comment_id: int, user_id: int) -> bool:
        """Delete a comment."""
        comment = await self.get_comment(comment_id)
        if comment and comment.user_id == user_id:
            await self.db.delete(comment)
            await self.db.flush()
            return True
        return False

    # Task Category Methods
    async def create_category(self, name: str, organization_id: int, description: Optional[str] = None,
                              color_code: Optional[str] = None, icon: Optional[str] = None,
                              parent_id: Optional[int] = None) -> "TaskCategory":
        """Create a new task category."""
        from Backend.data_layer.database.models.task_category import TaskCategory

        category = TaskCategory(
            name=name,
            description=description,
            color_code=color_code,
            icon=icon,
            parent_id=parent_id,
            organization_id=organization_id
        )
        self.db.add(category)
        await self.db.flush()
        return category

    async def get_categories(self, organization_id: int) -> List["TaskCategory"]:
        """Get all categories for an organization."""
        from Backend.data_layer.database.models.task_category import TaskCategory
        from sqlalchemy import select

        query = select(TaskCategory).where(
            TaskCategory.organization_id == organization_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_category(self, category_id: int) -> Optional["TaskCategory"]:
        """Get a category by ID."""
        from Backend.data_layer.database.models.task_category import TaskCategory
        from sqlalchemy import select

        query = select(TaskCategory).where(TaskCategory.id == category_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def update_category(self, category_id: int, **update_data) -> Optional["TaskCategory"]:
        """Update a category."""
        category = await self.get_category(category_id)
        if category:
            for key, value in update_data.items():
                if hasattr(category, key):
                    setattr(category, key, value)
            await self.db.flush()
            return category
        return None

    async def delete_category(self, category_id: int) -> bool:
        """Delete a category."""
        category = await self.get_category(category_id)
        if category:
            await self.db.delete(category)
            await self.db.flush()
            return True
        return False

    # Task Attachment Methods
    async def create_attachment(self, task_id: int, file_name: str, file_path: str,
                                uploaded_by: int, file_type: Optional[str] = None,
                                file_size: Optional[int] = None) -> "TaskAttachment":
        """Create a new attachment for a task."""
        from Backend.data_layer.database.models.task_attachment import TaskAttachment

        attachment = TaskAttachment(
            task_id=task_id,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            uploaded_by=uploaded_by
        )
        self.db.add(attachment)
        await self.db.flush()
        return attachment

    async def get_task_attachments(self, task_id: int) -> List["TaskAttachment"]:
        """Get all attachments for a task."""
        from Backend.data_layer.database.models.task_attachment import TaskAttachment
        from sqlalchemy import select

        query = select(TaskAttachment).where(TaskAttachment.task_id == task_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_attachment(self, attachment_id: int) -> Optional["TaskAttachment"]:
        """Get an attachment by ID."""
        from Backend.data_layer.database.models.task_attachment import TaskAttachment
        from sqlalchemy import select

        query = select(TaskAttachment).where(
            TaskAttachment.id == attachment_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def delete_attachment(self, attachment_id: int, user_id: int) -> bool:
        """Delete an attachment."""
        attachment = await self.get_attachment(attachment_id)
        if attachment and attachment.uploaded_by == user_id:
            await self.db.delete(attachment)
            await self.db.flush()
            return True
        return False

    # Task Occurrence Methods
    async def get_task_occurrence(self, task_id: int, occurrence_num: int) -> Optional[TaskOccurrence]:
        """Get a specific occurrence of a recurring task."""
        query = select(TaskOccurrence).where(
            and_(
                TaskOccurrence.task_id == task_id,
                TaskOccurrence.occurrence_num == occurrence_num
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def update_task_occurrence(self, occurrence_id: int, update_data: dict) -> Optional[TaskOccurrence]:
        """Update a task occurrence."""
        query = select(TaskOccurrence).where(TaskOccurrence.id == occurrence_id)
        result = await self.db.execute(query)
        occurrence = result.scalars().first()
        
        if occurrence:
            for key, value in update_data.items():
                if hasattr(occurrence, key):
                    setattr(occurrence, key, value)
            await self.db.flush()
            return occurrence
        return None
    
    async def get_task_occurrences(self, task_id: int) -> List[TaskOccurrence]:
        """Get all occurrences for a task."""        
        query = select(TaskOccurrence).where(TaskOccurrence.task_id == task_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_task_occurrence(self, occurrence_id: int) -> bool:
        """Delete a task occurrence record."""
        from sqlalchemy import select

        query = select(TaskOccurrence).where(
            TaskOccurrence.id == occurrence_id)
        result = await self.db.execute(query)
        occurrence = result.scalars().first()

        if occurrence:
            await self.db.delete(occurrence)
            await self.db.flush()
            return True
        return False