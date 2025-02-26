from typing import List, Dict, Optional, Any
from datetime import datetime
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.data_layer.database.models.task import Task, TaskStatus, TaskPriority
from Backend.data_layer.database.models.task_history import TaskHistory
from Backend.data_layer.database.errors import TaskNotFoundError
from Backend.tasks.task_tasks import process_task, execute_task_step
from celery.result import AsyncResult
from Backend.ai_services.rag.rag_service import RAGService
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

            # Validate status transition
            if task.status == TaskStatus.TODO and new_status == TaskStatus.COMPLETED:
                raise TaskUpdateError("Cannot transition directly from TODO to COMPLETED")

            # Check dependencies if transitioning to COMPLETED
            if new_status == TaskStatus.COMPLETED:
                dependencies_completed = await self.check_dependencies(task_id)
                if not dependencies_completed:
                    raise TaskUpdateError("Cannot complete task: dependencies not completed")

            # Update task status
            updated_task = await self.repo.update_task(task_id, {"status": new_status})

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
        """Validate if the status transition is allowed."""
        # Define valid transitions
        valid_transitions = {
            TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.DEFERRED],
            TaskStatus.IN_PROGRESS: [TaskStatus.BLOCKED, TaskStatus.COMPLETED, TaskStatus.DEFERRED],
            TaskStatus.BLOCKED: [TaskStatus.TODO, TaskStatus.IN_PROGRESS],
            TaskStatus.COMPLETED: [TaskStatus.IN_PROGRESS],  # Allow reopening
            TaskStatus.DEFERRED: [TaskStatus.TODO, TaskStatus.IN_PROGRESS]
        }

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

            task = await self.repo.get_task(current_id)
            if task and task.dependencies:
                deps = json.loads(task.dependencies) if isinstance(task.dependencies, str) else []
                for dep_id in deps:
                    if await dfs(int(dep_id)):
                        return True

            path.remove(current_id)
            return False

        # Check if adding new dependencies would create a cycle
        for dep_id in dependencies:
            if await dfs(dep_id):
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
        workflow_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        reviewer_id: Optional[int] = None,
        priority: Optional[TaskPriority] = None,
        category_id: Optional[int] = None,
        parent_task_id: Optional[int] = None,
        estimated_hours: Optional[float] = None,
        due_date: Optional[datetime] = None,
        dependencies: Optional[List[int]] = None,
        _dependencies_list: Optional[str] = None
    ) -> Task:
        """Create a new task and index it in RAG knowledge base."""
        task = await self.repo.create_task(
            title=title,
            description=description,
            creator_id=creator_id,
            project_id=project_id,
            organization_id=organization_id,
            workflow_id=workflow_id,
            assignee_id=assignee_id,
            reviewer_id=reviewer_id,
            priority=priority,
            category_id=category_id,
            parent_task_id=parent_task_id,
            estimated_hours=estimated_hours,
            due_date=due_date,
            _dependencies_list=json.dumps(dependencies or []),
            dependencies=dependencies or []
        )

        # Index the task in RAG knowledge base
        try:
            content = f"{title}\n{description}"
            await self.rag_service.add_to_knowledge_base(
                content=content,
                metadata={
                    "id": str(task.id),
                    "title": title,
                    "status": task.status,
                    "priority": str(priority) if priority else None,
                    "project_id": project_id
                }
            )
        except Exception as e:
            logger.error(f"Error indexing task in RAG: {str(e)}")
            # Don't raise the error as indexing failure shouldn't prevent task creation

        return task

    async def update_task(self, task_id: int, task_data: Dict) -> Task:
        """Update an existing task."""
        # Handle dependencies consistently
        if 'dependencies' in task_data:
            deps = task_data['dependencies']
            task_data['_dependencies_list'] = json.dumps(deps)
            task_data['dependencies'] = deps
        elif '_dependencies_list' in task_data and not isinstance(task_data['_dependencies_list'], str):
            deps = task_data['_dependencies_list']
            task_data['_dependencies_list'] = json.dumps(deps)
            task_data['dependencies'] = deps

        task = await self.repo.update_task(task_id, task_data)
        return task

    async def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID with error handling."""
        try:
            task = await self.repo.get_task(task_id)
            if not task:
                return None
            # Initialize dependencies from _dependencies_list
            try:
                deps = json.loads(task._dependencies_list) if task._dependencies_list else []
                task.dependencies = deps
                task.task_dependencies = deps
            except (json.JSONDecodeError, TypeError):
                task.dependencies = []
                task.task_dependencies = []
            return task
        except Exception as e:
            logger.error(f"Error getting task: {str(e)}")
            return None

    async def check_dependencies(self, task_id: int) -> bool:
        """Check if all dependencies are completed."""
        try:
            task = await self.repo.get_task(task_id)
            if not task:
                return True

            # Get dependencies from _dependencies_list
            deps = json.loads(task._dependencies_list) if task._dependencies_list else []

            if not deps:
                return True

            for dep_id in deps:
                dep_task = await self.repo.get_task(int(dep_id))
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking task dependencies: {str(e)}")
            return False

    async def get_task_with_details(self, task_id: int) -> Dict:
        """Get task with all related details."""
        task = await self.repo.get_task_with_details(task_id)
        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")

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
            "attachments": [dict(a.__dict__) for a in task.attachments] if task.attachments else [],
            "comments": [dict(c.__dict__) for c in task.comments] if task.comments else [],
            "history": [dict(h.__dict__) for h in task.history] if task.history else []
        }

    async def get_task_metrics(self, task_id: int) -> Optional[Dict]:
        """Get task metrics and analytics."""
        try:
            task = await self.repo.get_task(task_id)
            if not task:
                return None

            # Safely get blockers value
            blockers = getattr(task, 'blockers', None)
            blockers_list = json.loads(blockers) if isinstance(blockers, str) else []

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

    @property
    def dependencies(self) -> List[int]:
        """Get task dependencies."""
        return json.loads(self._dependencies_list) if hasattr(self, '_dependencies_list') else []

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
            return await self.repo.delete_task(task_id)
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
            logger.info(f"Updating task {task_id} with dependencies: {dependencies}")
            result = await self.repo.update_task_dependencies(task_id, dependencies)
            
            # Refresh task after update to ensure we have the latest state
            updated_task = await self.repo.get_task(task_id)
            if updated_task and updated_task.dependencies == dependencies:
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating task dependencies: {str(e)}")
            return False
# Add to TaskService class
