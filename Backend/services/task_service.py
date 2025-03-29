from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from Backend.data_layer.database.models.calendar_event import RecurrenceType
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.data_layer.database.models.task import Task, TaskStatus, TaskPriority
from Backend.data_layer.database.models.task_history import TaskHistory
from Backend.data_layer.database.models.event_occurrence import TaskOccurrence
from Backend.data_layer.database.errors import TaskNotFoundError
from Backend.celery_app.tasks.task_tasks import process_task, execute_task_step
from celery.result import AsyncResult
from Backend.ai_services.rag.rag_service import RAGService
from Backend.utils.cache_utils import cache_response, cache_entity, invalidate_cache
import asyncio
import logging
import json

logger = logging.getLogger(__name__)


class TaskUpdateError(Exception):
    """Custom exception for task update errors."""
    pass


class TaskService:
    def __init__(self, repository: TaskRepository):
        self.repo = repository
        self.rag_service = RAGService()

    async def update_task_status(self, task_id: int, new_status: TaskStatus, user_id: int) -> Task:
        """Update task status with validation and history tracking."""
        try:
            task = await self.repo.get_task(task_id)
            if not task:
                raise TaskNotFoundError(f"Task {task_id} not found")

            # Validate status transition using the transition rules
            if not self._is_valid_status_transition(task.status, new_status):
                raise TaskUpdateError(
                    f"Invalid status transition from {task.status} to {new_status}")

            # Check dependencies if transitioning to COMPLETED
            if new_status == TaskStatus.COMPLETED:
                dependencies_completed = await self.check_dependencies(task_id)
                if not dependencies_completed:
                    raise TaskUpdateError(
                        "Cannot complete task: dependencies not completed")

            # Update task status
            updated_task = await self.repo.update_task(
                task_id, {"status": new_status,
                          "status_updated_at": datetime.utcnow()}
            )

            # Add task history entry
            await self.repo.add_task_history(
                task_id=task_id,
                user_id=user_id,
                field_name="status",
                old_value=str(task.status),
                new_value=str(new_status)
            )

            return updated_task

        except Exception as e:
            logger.error(f"Error updating task status: {str(e)}")
            raise TaskUpdateError(f"Failed to update task status: {str(e)}")

    def _is_valid_status_transition(self, current_status: TaskStatus, new_status: TaskStatus) -> bool:
        """
        Validate if a status transition is allowed based on rules.
        """
        # Allow transitioning to the same status (no change)
        if current_status == new_status:
            return True

        # Define valid transition rules
        valid_transitions = {
            TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED, TaskStatus.DEFERRED, TaskStatus.COMPLETED],
            TaskStatus.IN_PROGRESS: [TaskStatus.COMPLETED, TaskStatus.BLOCKED, TaskStatus.UNDER_REVIEW, TaskStatus.TODO],
            TaskStatus.COMPLETED: [TaskStatus.TODO, TaskStatus.IN_PROGRESS],
            TaskStatus.CANCELLED: [TaskStatus.TODO],
            TaskStatus.BLOCKED: [TaskStatus.IN_PROGRESS, TaskStatus.TODO, TaskStatus.CANCELLED],
            TaskStatus.UNDER_REVIEW: [TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS],
            TaskStatus.DEFERRED: [TaskStatus.TODO, TaskStatus.CANCELLED]
        }

        # Check if the transition is allowed
        return new_status in valid_transitions.get(current_status, [])

    async def detect_dependency_cycles(self, task_id: int, dependencies: List[int]) -> bool:
        """Detect cycles in task dependencies."""
        visited = set()
        path = set()

        async def dfs(current_id: int) -> bool:
            if current_id in path:
                return True  # Cycle detected
            if current_id in visited:
                return False

            visited.add(current_id)
            path.add(current_id)

            # If we're checking the original task and it would depend on any of the new dependencies
            if current_id == task_id:
                for dep_id in dependencies:
                    if await dfs(dep_id):
                        return True
            else:
                # Check existing dependencies
                task = await self.repo.get_task(current_id)
                if task and task.dependencies:
                    deps = json.loads(task.dependencies) if isinstance(
                        task.dependencies, str) else []
                    for dep_id in deps:
                        if await dfs(int(dep_id)):
                            return True

            path.remove(current_id)
            return False

        # Start DFS from the task that would have new dependencies
        if await dfs(task_id):
            return True

        return False

    async def _calculate_health_score(
        self,
        task: Task,
        new_status: Optional[TaskStatus],
        new_due_date: Optional[datetime],
        blockers: Optional[Dict]
    ) -> float:
        """Calculate task health score based on various factors."""
        score = 1.0  # Start with perfect health

        # Status impact
        if new_status == TaskStatus.BLOCKED:
            score *= 0.5
        elif new_status == TaskStatus.DEFERRED:
            score *= 0.7

        # Due date impact
        if new_due_date and new_due_date < datetime.utcnow():
            score *= 0.8

        # Blockers impact
        if blockers and len(blockers) > 0:
            score *= 0.9

        # Bound score between 0 and 1
        return max(0.0, min(1.0, score))

    async def create_task(
        self,
        title: str,
        description: str,
        creator_id: int,
        project_id: int,
        organization_id: int,
        start_date: datetime,
        status: TaskStatus = TaskStatus.TODO,  # Add status parameter with default
        # Add priority parameter with default
        priority: TaskPriority = TaskPriority.MEDIUM,
        workflow_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        reviewer_id: Optional[int] = None,
        category_id: Optional[int] = None,
        parent_task_id: Optional[int] = None,
        estimated_hours: Optional[float] = None,
        duration: Optional[float] = None,  # Updated
        due_date: Optional[datetime] = None,  # New
        recurrence: Optional[RecurrenceType] = RecurrenceType.NONE,  # New
        recurrence_end_date: Optional[datetime] = None,  # New
        dependencies: Optional[List[int]] = None,
        ai_suggestions: Optional[Dict] = None,
        complexity_score: Optional[float] = None,
        time_estimates: Optional[Dict] = None,
        focus_sessions: Optional[Dict] = None,
        interruption_logs: Optional[Dict] = None,
        progress_metrics: Optional[Dict] = None,
        blockers: Optional[List[str]] = None,
        health_score: Optional[float] = None,
        risk_factors: Optional[Dict] = None,
        _dependencies_list: Optional[str] = None
    ) -> Task:
        """Create a new task and index it in RAG knowledge base."""
        if not start_date:
            raise ValueError("start_date is required for task creation")

        if due_date and start_date > due_date:
            raise ValueError("Start date must be before end date")

        if duration and duration < 0:
            raise ValueError("Duration must be positive")

        task_data = {
            "title": title,
            "description": description,
            "creator_id": creator_id,
            "project_id": project_id,
            "organization_id": organization_id,
            "status": status,
            "priority": priority,
            "workflow_id": workflow_id if workflow_id and workflow_id > 0 else None,
            "assignee_id": assignee_id,
            "reviewer_id": reviewer_id,
            "category_id": category_id if category_id and category_id > 0 else None,
            "parent_task_id": parent_task_id if parent_task_id and parent_task_id > 0 else None,
            "estimated_hours": estimated_hours,
            "start_date": start_date,
            "duration": duration,  # Updated
            "due_date": due_date,  # New
            "recurrence": recurrence,  # New
            "recurrence_end_date": recurrence_end_date,  # New
            "_dependencies_list": json.dumps(dependencies or []),
            "ai_suggestions": ai_suggestions or {},
            "complexity_score": complexity_score,
            "time_estimates": time_estimates or {},
            "focus_sessions": focus_sessions or {},
            "interruption_logs": interruption_logs or {},
            "progress_metrics": progress_metrics or {},
            "blockers": blockers or [],
            "health_score": health_score,
            "risk_factors": risk_factors or {}
        }

        task = await self.repo.create(**task_data)

        # Generate task occurrences for recurring tasks
        if recurrence != RecurrenceType.NONE:
            current_date = start_date
            occurrence_num = 0

            while not recurrence_end_date or current_date <= recurrence_end_date:
                # Create occurrence data
                occurrence_data = {
                    "task_id": task.id,
                    "occurrence_num": occurrence_num,
                    "title": title,
                    "start_date": current_date,
                    "due_date": current_date + timedelta(hours=duration) if duration else None,
                    "status": status,
                    "priority": priority,
                    "modified_by_id": creator_id
                }

                # Create the occurrence record
                await self.repo.create_task_occurrence(occurrence_data)

                # Calculate next occurrence date
                if recurrence == RecurrenceType.DAILY:
                    current_date += timedelta(days=1)
                elif recurrence == RecurrenceType.WEEKLY:
                    current_date += timedelta(weeks=1)
                elif recurrence == RecurrenceType.MONTHLY:
                    current_date += relativedelta(months=1)
                elif recurrence == RecurrenceType.YEARLY:
                    current_date += relativedelta(years=1)
                elif recurrence == RecurrenceType.CUSTOM and task.recurrence_custom_days:
                    custom_days = [int(d) for d in task.recurrence_custom_days]
                    if custom_days:
                        current_date += timedelta(
                            days=custom_days[occurrence_num % len(custom_days)])
                    else:
                        break
                else:
                    break

                occurrence_num += 1

        # Index the task in RAG knowledge base
        try:
            content = f"{title}\n{description}"
            await self.rag_service.add_to_knowledge_base(
                content=content,
                metadata={
                    "id": str(task.id),
                    "title": title,
                    "status": status,
                    "priority": str(priority) if priority else None,
                    "project_id": project_id
                }
            )
        except Exception as e:
            logger.error(f"Error indexing task in RAG: {str(e)}")

        return task

    async def update_task(self, task_id: int, task_data: Dict, update_all_occurrences: bool = True) -> Task:
        """Update an existing task.

        Args:
            task_id: The ID of the task to update
            task_data: Dictionary containing the fields to update
            update_all_occurrences: If True, update all occurrences of a recurring task. If False, only update this occurrence.
        """
        # Get existing task first
        existing_task = await self.repo.get_task(task_id)
        if not existing_task:
            raise TaskNotFoundError(f"Task {task_id} not found")

        # Handle dependencies consistently
        if 'dependencies' in task_data:
            deps = task_data['dependencies']
            task_data['_dependencies_list'] = json.dumps(deps)
            task_data['dependencies'] = deps
        elif '_dependencies_list' in task_data and not isinstance(task_data['_dependencies_list'], str):
            deps = task_data['_dependencies_list']
            task_data['_dependencies_list'] = json.dumps(deps)
            task_data['dependencies'] = deps

        # Check if this is a recurring task
        is_recurring = existing_task.recurrence != RecurrenceType.NONE

        # Extract the occurrence information from the task_id if it's a virtual ID
        occurrence_num = 0
        original_task_id = task_id
        is_virtual_id = False

        # Check if this is a virtual occurrence ID (e.g., "123_2" for the 3rd occurrence of task 123)
        task_id_str = str(task_id)
        if '_' in task_id_str:
            parts = task_id_str.split('_')
            original_task_id = int(parts[0])
            occurrence_num = int(parts[1])
            is_virtual_id = True

            # If it's a virtual ID, we need to get the actual task
            if original_task_id != task_id:
                existing_task = await self.repo.get_task(original_task_id)
                if not existing_task:
                    raise TaskNotFoundError(
                        f"Original task {original_task_id} not found")

        # If this is a recurring task and we're not updating all occurrences,
        # or if this is a virtual ID (which always refers to a specific occurrence)
        if (is_recurring and not update_all_occurrences) or is_virtual_id:
            # For single occurrence updates, we don't modify the original task
            # Instead, we create or update a TaskOccurrence record

            # Get or create the occurrence record
            occurrence = await self.repo.get_task_occurrence(original_task_id, occurrence_num)

            # Prepare occurrence data
            occurrence_data = {
                'task_id': original_task_id,
                'occurrence_num': occurrence_num,
                'modified_by_id': task_data.get('modified_by_id', existing_task.creator_id)
            }

            # Add all the fields that can be modified for a specific occurrence
            for field in ['title', 'description', 'status', 'priority', 'assignee_id',
                          'reviewer_id', 'category_id', 'start_date', 'duration', 'due_date',
                          'progress_metrics', 'blockers', 'health_score', 'risk_factors']:
                if field in task_data:
                    occurrence_data[field] = task_data[field]

            # If we don't have start_date in the update data but we need it for a new occurrence
            if 'start_date' not in occurrence_data and not occurrence:
                # Calculate the start date for this occurrence based on the recurrence pattern
                occurrence_data['start_date'] = self._calculate_occurrence_start_date(
                    existing_task, occurrence_num)

            # Create or update the occurrence
            if occurrence:
                updated_occurrence = await self.repo.update_task_occurrence(occurrence.id, occurrence_data)
            else:
                updated_occurrence = await self.repo.create_task_occurrence(occurrence_data)

            # Return the original task (not modified)
            return existing_task
        else:
            # Normal update behavior for non-recurring tasks or when updating all occurrences

            # Validate date fields
            if "start_date" in task_data or "duration" in task_data:
                new_start = task_data.get(
                    "start_date", existing_task.start_date)
                new_duration = task_data.get(
                    "duration", existing_task.duration)

                if new_duration and new_duration < 0:
                    raise TaskUpdateError("Duration must be positive")

                task_data["start_date"] = new_start
                task_data["duration"] = new_duration

            # Validate recurrence end date
            if "recurrence_end_date" in task_data and task_data["recurrence_end_date"]:
                start_date = task_data.get(
                    "start_date", existing_task.start_date)
                if task_data["recurrence_end_date"] < start_date:
                    raise TaskUpdateError(
                        "Recurrence end date cannot be before start date")

            # Update status_updated_at if status is changing
            if "status" in task_data and task_data["status"] != existing_task.status:
                task_data["status_updated_at"] = datetime.utcnow()

            # Handle foreign key IDs - if they're 0, set them to None to avoid foreign key violations
            for field in ['category_id', 'workflow_id', 'parent_task_id', 'assignee_id', 'reviewer_id']:
                if field in task_data and task_data[field] == 0:
                    task_data[field] = None

            # Update the task
            updated_task = await self.repo.update_task(original_task_id, task_data)

            # If this is a recurring task and we're updating all occurrences,
            # we should also update any existing occurrence records to match the new base task
            if is_recurring and update_all_occurrences:
                # Get all occurrences for this task
                occurrences = await self.repo.get_task_occurrences(original_task_id)

                # For each occurrence, update the fields that weren't specifically modified for that occurrence
                for occurrence in occurrences:
                    # Only update fields that weren't specifically overridden for this occurrence
                    occurrence_update = {}

                    # Fields to potentially update in occurrences when the base task changes
                    # Only update fields that aren't specifically set in the occurrence
                    for field in ['title', 'description', 'priority', 'category_id']:
                        if field in task_data and getattr(occurrence, field) is None:
                            occurrence_update[field] = task_data[field]

                    if occurrence_update:
                        await self.repo.update_task_occurrence(occurrence.id, occurrence_update)

            # Invalidate cache for this task
            invalidate_cache('task', original_task_id)

            return updated_task

    def _calculate_occurrence_start_date(self, task: Task, occurrence_num: int) -> datetime:
        """Calculate the start date for a specific occurrence of a recurring task."""
        base_start = task.start_date

        if task.recurrence == RecurrenceType.DAILY:
            return base_start + timedelta(days=occurrence_num)
        elif task.recurrence == RecurrenceType.WEEKLY:
            return base_start + timedelta(weeks=occurrence_num)
        elif task.recurrence == RecurrenceType.MONTHLY:
            # Add months using relative delta to handle month boundaries correctly
            return base_start + relativedelta(months=occurrence_num)
        elif task.recurrence == RecurrenceType.YEARLY:
            return base_start + relativedelta(years=occurrence_num)
        elif task.recurrence == RecurrenceType.CUSTOM and task.recurrence_custom_days:
            # For custom recurrence, calculate based on the custom days pattern
            custom_days = task.recurrence_custom_days
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


    @cache_entity(entity_type='task')
    async def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID with error handling."""
        try:
            task = await self.repo.get_task(task_id)
            if not task:
                return None
            # Initialize dependencies from _dependencies_list
            try:
                deps = json.loads(
                    task._dependencies_list) if task._dependencies_list else []
                task.dependencies = deps

            except (json.JSONDecodeError, TypeError):
                task.dependencies = []

            return task
        except Exception as e:
            logger.error(f"Error getting task: {str(e)}")
            return None

    @cache_response(cache_type='task_dependencies')
    async def check_dependencies(self, task_id: int) -> bool:
        """Check if all dependencies are completed."""
        try:
            task = await self.repo.get_task(task_id)
            if not task:
                return True

            # Get dependencies from _dependencies_list
            deps = json.loads(
                task._dependencies_list) if task._dependencies_list else []

            if not deps:
                return True

            for dep_id in deps:
                # Skip invalid dependency IDs (0 or negative values)
                if dep_id == 0 or dep_id < 0:
                    logger.warning(
                        f"Skipping invalid dependency ID {dep_id} for task {task_id}")
                    continue

                dep_task = await self.repo.get_task(int(dep_id))
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking task dependencies: {str(e)}")
            return False

    # @cache_response(cache_type='task_list')
    async def get_tasks(
        self,
        project_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assignee_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        duration: Optional[float] = None,
        due_date: Optional[datetime] = None,
        recurrence: Optional[RecurrenceType] = None,
        end_date: Optional[datetime] = None,
        include_recurring: bool = True
    ) -> List[Task]:
        """Get tasks with optional filters and calendar support."""
        try:
            # Ensure timezone-naive datetime objects
            if start_date and start_date.tzinfo:
                start_date = start_date.replace(tzinfo=None)
            if end_date and end_date.tzinfo:
                end_date = end_date.replace(tzinfo=None)
            if due_date and due_date.tzinfo:
                due_date = due_date.replace(tzinfo=None)

            # Convert enum values to strings for repository layer
            status_str = status.value if status else None
            priority_str = priority.value if priority else None

            # Get tasks from repository
            if project_id:
                tasks = await self.repo.get_tasks_by_project(
                    project_id=project_id,
                    skip=skip,
                    limit=limit,
                    status=status_str,
                    priority=priority_str,
                    assignee_id=assignee_id,
                    creator_id=creator_id,
                    start_date=start_date,
                    duration=duration,
                    due_date=due_date,
                    recurrence=recurrence,
                    end_date=end_date,
                    include_recurring=include_recurring
                )
            else:
                tasks = await self.repo.get_tasks(
                    skip=skip,
                    limit=limit,
                    status=status_str,
                    priority=priority_str,
                    assignee_id=assignee_id,
                    creator_id=creator_id,
                    start_date=start_date,
                    duration=duration,
                    due_date=due_date,
                    recurrence=recurrence,
                    end_date=end_date,
                    include_recurring=include_recurring
                )

            # Initialize dependencies for each task
            for task in tasks:
                try:
                    deps = json.loads(
                        task._dependencies_list) if isinstance(task._dependencies_list, str) else []
                    task.dependencies = deps
                except (json.JSONDecodeError, TypeError):
                    task.dependencies = []

            return tasks
        except Exception as e:
            logger.error(f"Error getting tasks: {str(e)}")
            return []

    @cache_response(cache_type='task_details')
    async def get_task_with_details(self, task_id: int) -> Dict:
        """Get task with all related details."""
        task = await self.repo.get_task_with_details(task_id)
        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")

        # Get comments, attachments, and history
        comments = await self.get_task_comments(task_id)
        attachments = await self.get_task_attachments(task_id)
        history = await self.repo.get_task_history(task_id)

        # Convert task model to dictionary
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "creator_id": task.creator_id,
            "assignee_id": task.assignee_id,
            "reviewer_id": task.reviewer_id,
            "project_id": task.project_id,
            "organization_id": task.organization_id,
            "workflow_id": task.workflow_id,
            "current_workflow_step_id": task.current_workflow_step_id,
            "health_score": task.health_score,
            "category_id": task.category_id,
            "start_date": task.start_date,
            "duration": task.duration,
            "due_date": task.due_date,
            "recurrence": task.recurrence,
            "recurrence_end_date": task.recurrence_end_date,
            "estimated_hours": task.estimated_hours,
            "actual_hours": task.actual_hours,
            "dependencies": task.dependencies,
            "attachments": [{
                "id": a.id,
                "file_name": a.file_name,
                "file_path": a.file_path,
                "file_type": a.file_type,
                "file_size": a.file_size,
                "uploaded_by": a.uploaded_by,
                "created_at": a.created_at
            } for a in attachments],
            "comments": [{
                "id": c.id,
                "content": c.content,
                "user_id": c.user_id,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "parent_id": c.parent_id
            } for c in comments],
            "history": [{
                "id": h.id,
                "task_id": h.task_id,
                "user_id": h.user_id,
                "action": h.action,
                "field": h.field,
                "old_value": h.old_value,
                "new_value": h.new_value,
                "created_at": h.created_at
            } for h in history]
        }

    @cache_response(cache_type='task_metrics')
    async def get_task_metrics(self, task_id: int) -> Optional[Dict]:
        """Get task metrics and analytics."""
        try:
            task = await self.repo.get_task(task_id)
            if not task:
                return None

            # Safely get blockers value
            blockers = getattr(task, 'blockers', None)
            blockers_list = json.loads(
                blockers) if isinstance(blockers, str) else []

            metrics = {
                "dependencies_completed": await self.check_dependencies(task_id),
                "has_blockers": len(blockers_list) > 0,
                "time_spent": getattr(task, 'actual_hours', 0) or 0,
                "estimated_completion": getattr(task, 'estimated_hours', 0) or 0,
                "progress": getattr(task, 'progress_metrics', {})
            }
            return metrics
        except Exception as e:
            logger.error(f"Error getting task metrics: {str(e)}")
            return None

    # Task Comment Methods
    async def create_comment(self, task_id: int, user_id: int, content: str, parent_id: Optional[int] = None):
        """Create a new comment for a task."""
        # Verify task exists
        task = await self.repo.get_task(task_id)
        if not task:
            raise TaskNotFoundError(f"Task with id {task_id} not found")

        return await self.repo.create_comment(task_id, user_id, content, parent_id)

    async def get_task_comments(self, task_id: int, skip: int = 0, limit: int = 50):
        """Get all comments for a task."""
        # Verify task exists
        task = await self.repo.get_task(task_id)
        if not task:
            raise TaskNotFoundError(f"Task with id {task_id} not found")

        return await self.repo.get_task_comments(task_id, skip, limit)

    async def update_comment(self, comment_id: int, user_id: int, content: str):
        """Update a comment."""
        return await self.repo.update_comment(comment_id, user_id, content)

    async def delete_comment(self, comment_id: int, user_id: int) -> bool:
        """Delete a comment."""
        return await self.repo.delete_comment(comment_id, user_id)

    # Task Category Methods
    async def create_category(self, name: str, organization_id: int, description: Optional[str] = None,
                              color_code: Optional[str] = None, icon: Optional[str] = None,
                              parent_id: Optional[int] = None):
        """Create a new task category."""
        return await self.repo.create_category(
            name=name,
            organization_id=organization_id,
            description=description,
            color_code=color_code,
            icon=icon,
            parent_id=parent_id
        )

    async def get_categories(self, organization_id: int):
        """Get all categories for an organization."""
        return await self.repo.get_categories(organization_id)

    async def get_category(self, category_id: int):
        """Get a category by ID."""
        return await self.repo.get_category(category_id)

    async def update_category(self, category_id: int, **update_data):
        """Update a category."""
        return await self.repo.update_category(category_id, **update_data)

    async def delete_category(self, category_id: int) -> bool:
        """Delete a category."""
        return await self.repo.delete_category(category_id)

    # Task Attachment Methods
    async def create_attachment(self, task_id: int, file_name: str, file_path: str,
                                uploaded_by: int, file_type: Optional[str] = None,
                                file_size: Optional[int] = None):
        """Create a new attachment for a task."""
        # Verify task exists
        task = await self.repo.get_task(task_id)
        if not task:
            raise TaskNotFoundError(f"Task with id {task_id} not found")

        return await self.repo.create_attachment(
            task_id=task_id,
            file_name=file_name,
            file_path=file_path,
            uploaded_by=uploaded_by,
            file_type=file_type,
            file_size=file_size
        )

    async def get_task_attachments(self, task_id: int):
        """Get all attachments for a task."""
        # Verify task exists
        task = await self.repo.get_task(task_id)
        if not task:
            raise TaskNotFoundError(f"Task with id {task_id} not found")

        return await self.repo.get_task_attachments(task_id)

    async def get_attachment(self, attachment_id: int):
        """Get an attachment by ID."""
        return await self.repo.get_attachment(attachment_id)

    async def delete_attachment(self, attachment_id: int, user_id: int) -> bool:
        """Delete an attachment."""
        return await self.repo.delete_attachment(attachment_id, user_id)

    async def execute_task_step(self, task_id: int, workflow_step_id: int, user_id: int) -> Dict:
        """Execute a workflow step for a task."""
        task = await self.repo.get_task(task_id)
        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")

        # Start step execution in background
        task_result = execute_task_step.delay(
            task_id=task_id,
            workflow_step_id=workflow_step_id,
            user_id=user_id
        )

        return {
            "task_id": task_id,
            "step_id": workflow_step_id,
            "status": "PENDING",
            "task_result_id": task_result.id
        }

    async def get_task_status(self, task_id: str) -> Dict:
        """Get the status of an asynchronous task."""
        result = AsyncResult(task_id)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None
        }

    async def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID."""
        try:
            result = await self.repo.delete_task(task_id)
            if result:
                # Invalidate cache for this task
                invalidate_cache('task', task_id)
            return result
        except Exception as e:
            logger.error(f"Error deleting task: {str(e)}")
            return False

    async def update_task_dependencies(self, task_id: int, dependencies: List[int]) -> bool:
        """Update task dependencies with validation."""
        try:
            task = await self.repo.get_task(task_id)
            if not task:
                return False

            # Validate dependencies
            for dep_id in dependencies:
                dep_task = await self.repo.get_task(dep_id)
                if not dep_task:
                    raise ValueError(f"Dependency task {dep_id} not found")

            # Update task with new dependencies
            logger.info(
                f"Updating task {task_id} with dependencies: {dependencies}")
            result = await self.repo.update_task_dependencies(task_id, dependencies)

            # Refresh task after update to ensure we have the latest state
            updated_task = await self.repo.get_task(task_id)
            if updated_task and updated_task.dependencies == dependencies:
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating task dependencies: {str(e)}")
            return False

    async def expand_recurring_task(self, task: Task, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Expand a recurring task into individual occurrences within a date range.

        This method takes a recurring task and generates virtual occurrences
        based on the recurrence pattern for display in calendar views.

        Args:
            task: The recurring task to expand
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            List of task occurrence dictionaries with start_date and end_date
        """
        try:
            # Handle case where task might be a dict or doesn't have recurrence
            if not hasattr(task, 'recurrence') or task.recurrence == RecurrenceType.NONE:
                # Non-recurring task, just return the original
                return [{
                    "id": str(task.id) if hasattr(task, 'id') else "unknown",
                    "title": task.title if hasattr(task, 'title') else "Untitled Task",
                    "start_date": task.start_date if hasattr(task, 'start_date') else None,
                    "due_date": task.due_date if hasattr(task, 'due_date') else None,
                    "duration": task.duration if hasattr(task, 'duration') else None,
                    "is_recurring": False,
                    "is_original": True,
                    "status": task.status.value if hasattr(task.status, 'value') else task.status,
                    "priority": task.priority.value if hasattr(task.priority, 'value') else task.priority,
                    "recurrence": task.recurrence,
                    "recurrence_end_date": task.recurrence_end_date
                }]

            occurrences = []
            current_date = task.start_date
            occurrence_num = 0

            # Safely handle recurrence_end_date
            recurrence_end = None
            if hasattr(task, 'recurrence_end_date') and task.recurrence_end_date:
                recurrence_end = task.recurrence_end_date
            else:
                recurrence_end = end_date + timedelta(days=365)

            # Determine recurrence type and set appropriate delta
            delta = timedelta(days=1)  # Default to daily

            if hasattr(task, 'recurrence'):
                if task.recurrence == RecurrenceType.DAILY:
                    delta = timedelta(days=1)
                elif task.recurrence == RecurrenceType.WEEKLY:
                    delta = timedelta(weeks=1)
                elif task.recurrence == RecurrenceType.BIWEEKLY:
                    delta = timedelta(weeks=2)
                elif task.recurrence == RecurrenceType.MONTHLY:
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
                elif task.recurrence == RecurrenceType.YEARLY:
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
                elif task.recurrence == RecurrenceType.CUSTOM and hasattr(task, 'recurrence_custom_days') and task.recurrence_custom_days:
                    # Custom recurrence is handled differently
                    return self._expand_custom_recurrence(task, start_date, end_date)

            # Generate occurrences until we reach the end date or recurrence end
            while current_date <= min(end_date, recurrence_end):
                # Only include occurrences that fall within our range
                if current_date >= start_date:
                    # Calculate the due date for this occurrence
                    occurrence_due_date = None
                    if hasattr(task, 'due_date') and task.due_date:
                        # Maintain the same duration between start and due date
                        original_duration = (
                            task.due_date - task.start_date).total_seconds()
                        occurrence_due_date = current_date + \
                            timedelta(seconds=original_duration)

                    occurrences.append({
                        # Virtual ID for the occurrence
                        "id": f"{task.id}_{occurrence_num}",
                        "original_id": task.id,  # Reference to the original task
                        "title": task.title if hasattr(task, 'title') else "Untitled Task",
                        "start_date": current_date,
                        "due_date": occurrence_due_date,
                        "duration": task.duration if hasattr(task, 'duration') else None,
                        "is_recurring": True,
                        "is_original": occurrence_num == 0,
                        "occurrence_num": occurrence_num,
                        "status": task.status.value if hasattr(task.status, 'value') else task.status,
                        "priority": task.priority.value if hasattr(task.priority, 'value') else task.priority,
                        "recurrence": task.recurrence,
                        "recurrence_end_date": task.recurrence_end_date
                    })

                # Move to the next occurrence
                current_date += delta
                occurrence_num += 1

            return occurrences
        except Exception as e:
            logger.error(f"Error expanding recurring task: {str(e)}")
            # Return just the original task as a fallback
            return [{
                "id": str(task.id) if hasattr(task, 'id') else "unknown",
                "title": task.title if hasattr(task, 'title') else "Untitled Task",
                "start_date": task.start_date if hasattr(task, 'start_date') else None,
                "due_date": task.due_date if hasattr(task, 'due_date') else None,
                "duration": task.duration if hasattr(task, 'duration') else None,
                "is_recurring": False,
                "is_original": True,
                "status": task.status.value if hasattr(task.status, 'value') else task.status,
                "priority": task.priority.value if hasattr(task.priority, 'value') else task.priority,
                "recurrence": task.recurrence,
                "recurrence_end_date": task.recurrence_end_date,
                "error": str(e)
            }]

    def _expand_custom_recurrence(self, task: Task, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Handle custom recurrence patterns with specific days."""
        try:
            occurrences = []

            # Start with the original task
            occurrences.append({
                "id": str(task.id) if hasattr(task, 'id') else "unknown",
                "title": task.title if hasattr(task, 'title') else "Untitled Task",
                "start_date": task.start_date if hasattr(task, 'start_date') else None,
                "due_date": task.due_date if hasattr(task, 'due_date') else None,
                "duration": task.duration if hasattr(task, 'duration') else None,
                "is_recurring": True,
                "is_original": True,
                "occurrence_num": 0
            })

            # Check if task has recurrence_custom_days attribute
            if not hasattr(task, 'recurrence_custom_days') or not task.recurrence_custom_days:
                return occurrences

            try:
                custom_days = task.recurrence_custom_days
                day_mapping = {
                    "Monday": 0, "Tuesday": 1, "Wednesday": 2,
                    "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
                }

                # Convert day names to day numbers (0=Monday, 6=Sunday)
                day_numbers = []
                for day in custom_days:
                    if day in day_mapping:
                        day_numbers.append(day_mapping[day])

                if not day_numbers:
                    return occurrences

                # Start from the day after the original task
                current_date = task.start_date + timedelta(days=1)
                occurrence_num = 1

                # Safely handle recurrence_end_date
                recurrence_end = None
                if hasattr(task, 'recurrence_end_date') and task.recurrence_end_date:
                    recurrence_end = task.recurrence_end_date
                else:
                    recurrence_end = end_date + timedelta(days=365)

                # Generate occurrences until we reach the end date or recurrence end
                while current_date <= min(end_date, recurrence_end):
                    # Check if the current day is in our custom days
                    if current_date.weekday() in day_numbers:
                        # Calculate the due date for this occurrence
                        occurrence_due_date = None
                        if hasattr(task, 'due_date') and task.due_date:
                            # Maintain the same duration between start and due date
                            original_duration = (
                                task.due_date - task.start_date).total_seconds()
                            occurrence_due_date = current_date + \
                                timedelta(seconds=original_duration)

                        occurrences.append({
                            # Virtual ID for the occurrence
                            "id": f"{task.id}_{occurrence_num}",
                            "original_id": task.id,  # Reference to the original task
                            "title": task.title if hasattr(task, 'title') else "Untitled Task",
                            "start_date": current_date,
                            "due_date": occurrence_due_date,
                            "duration": task.duration if hasattr(task, 'duration') else None,
                            "is_recurring": True,
                            "is_original": False,
                            "occurrence_num": occurrence_num
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
            # Return just the original task as a fallback
            return [{
                "id": str(task.id) if hasattr(task, 'id') else "unknown",
                "title": task.title if hasattr(task, 'title') else "Untitled Task",
                "start_date": task.start_date if hasattr(task, 'start_date') else None,
                "due_date": task.due_date if hasattr(task, 'due_date') else None,
                "duration": task.duration if hasattr(task, 'duration') else None,
                "is_recurring": True,
                "is_original": True,
                "occurrence_num": 0,
                "error": str(e)
            }]

    async def get_calendar_tasks(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        include_recurring: bool = True
    ) -> List[Dict]:
        """Get tasks formatted for calendar view with expanded recurring tasks.

        This method retrieves tasks for a calendar view and optionally expands
        recurring tasks into individual occurrences.

        Args:
            start_date: Start of the calendar range
            end_date: End of the calendar range
            user_id: Optional user ID to filter tasks
            project_id: Optional project ID to filter tasks
            include_recurring: Whether to include recurring tasks

        Returns:
            List of task dictionaries formatted for calendar display
        """
        try:
            # Get base tasks
            tasks = await self.repo.get_tasks_by_project(
                project_id=project_id,
                creator_id=user_id,
                start_date=start_date,
                end_date=end_date,
                include_recurring=include_recurring
            ) if project_id else await self.repo.get_tasks(
                creator_id=user_id,
                start_date=start_date,
                end_date=end_date,
                include_recurring=include_recurring
            )

            # Format tasks for calendar view
            calendar_tasks = []
            for task in tasks:
                # For recurring tasks, generate occurrences
                if task.recurrence != RecurrenceType.NONE and include_recurring:
                    # Get any modified occurrences for this task
                    modified_occurrences = await self.repo.get_task_occurrences(task.id)
                    modified_occurrences_dict = {
                        occ.occurrence_num: occ for occ in modified_occurrences}

                    # Generate all occurrences within the date range
                    occurrences = []
                    current_date = task.start_date
                    occurrence_num = 0

                    while current_date <= end_date and (not task.recurrence_end_date or current_date <= task.recurrence_end_date):
                        if current_date >= start_date:
                            # Check if this occurrence has been modified
                            modified_occurrence = modified_occurrences_dict.get(
                                occurrence_num)

                            if modified_occurrence:
                                occurrences.append({
                                    'id': f"{task.id}_{occurrence_num}",
                                    'title': modified_occurrence.title or task.title,
                                    'start': modified_occurrence.start_date,
                                    'end': modified_occurrence.due_date or (modified_occurrence.start_date + timedelta(hours=task.duration) if task.duration else None),
                                    'status': modified_occurrence.status or task.status,
                                    'priority': modified_occurrence.priority or task.priority,
                                    'recurrence': task.recurrence,
                                    'recurrence_end_date': task.recurrence_end_date,
                                    'occurrence_num': occurrence_num,
                                    'is_modified': True
                                })
                            else:
                                occurrences.append({
                                    'id': f"{task.id}_{occurrence_num}",
                                    'title': task.title,
                                    'start': current_date,
                                    'end': current_date + timedelta(hours=task.duration) if task.duration else None,
                                    'status': task.status,
                                    'priority': task.priority,
                                    'recurrence': task.recurrence,
                                    'recurrence_end_date': task.recurrence_end_date,
                                    'occurrence_num': occurrence_num,
                                    'is_modified': False
                                })

                        # Calculate next occurrence date
                        if task.recurrence == RecurrenceType.DAILY:
                            current_date += timedelta(days=1)
                        elif task.recurrence == RecurrenceType.WEEKLY:
                            current_date += timedelta(weeks=1)
                        elif task.recurrence == RecurrenceType.MONTHLY:
                            current_date += relativedelta(months=1)
                        elif task.recurrence == RecurrenceType.YEARLY:
                            current_date += relativedelta(years=1)
                        elif task.recurrence == RecurrenceType.CUSTOM and task.recurrence_custom_days:
                            custom_days = [int(d)
                                           for d in task.recurrence_custom_days]
                            if custom_days:
                                current_date += timedelta(
                                    days=custom_days[occurrence_num % len(custom_days)])
                            else:
                                break
                        else:
                            break

                        occurrence_num += 1

                    calendar_tasks.extend(occurrences)
                else:
                    # Non-recurring tasks are added as-is
                    calendar_tasks.append({
                        'id': str(task.id),
                        'title': task.title,
                        'start': task.start_date,
                        'end': task.due_date or (task.start_date + timedelta(hours=task.duration) if task.duration else None),
                        'status': task.status,
                        'priority': task.priority,
                        'recurrence': task.recurrence,
                        'recurrence_end_date': task.recurrence_end_date
                    })

            return calendar_tasks

        except Exception as e:
            logger.error(f"Error retrieving calendar tasks: {str(e)}")
            raise Exception(f"Error retrieving calendar tasks: {str(e)}")
