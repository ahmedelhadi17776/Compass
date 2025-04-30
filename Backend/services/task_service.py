from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from Backend.data_layer.database.models.calendar_event import RecurrenceType
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.data_layer.database.models.task import Task, TaskStatus, TaskPriority
from Backend.data_layer.database.models.task_history import TaskHistory
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
            TaskStatus.UPCOMING: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED, TaskStatus.DEFERRED, TaskStatus.COMPLETED],
            TaskStatus.IN_PROGRESS: [TaskStatus.COMPLETED, TaskStatus.BLOCKED, TaskStatus.UNDER_REVIEW, TaskStatus.UPCOMING],
            TaskStatus.COMPLETED: [TaskStatus.UPCOMING, TaskStatus.IN_PROGRESS],
            TaskStatus.CANCELLED: [TaskStatus.UPCOMING],
            TaskStatus.BLOCKED: [TaskStatus.IN_PROGRESS, TaskStatus.UPCOMING, TaskStatus.CANCELLED],
            TaskStatus.UNDER_REVIEW: [TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS],
            TaskStatus.DEFERRED: [TaskStatus.UPCOMING, TaskStatus.CANCELLED]
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
        status: TaskStatus = TaskStatus.UPCOMING,  # Add status parameter with default
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

        # Index task in RAG knowledge base for improved searchability
        try:
            await self.rag_service.index_task(task)
        except Exception as e:
            # Log but don't fail if indexing encounters an issue
            logger.warning(f"Error indexing task in RAG: {e}")

        return task

    async def update_task(self, task_id: int, task_data: Dict) -> Task:
        """Update a task with validation and tracking."""
        # Get existing task first
        existing_task = await self.repo.get_task(task_id)
        if not existing_task:
            raise TaskNotFoundError(f"Task {task_id} not found")

        # Calculate health score if needed fields are being updated
        if any(key in task_data for key in ["status", "due_date", "blockers"]):
            health_score = await self._calculate_health_score(
                existing_task,
                task_data.get("status"),
                task_data.get("due_date"),
                task_data.get("blockers")
            )
            task_data["health_score"] = health_score

        # Update the task
        task = await self.repo.update_task(task_id, task_data)
        
        return task

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
