from Backend.api.routes import status
from Backend.celery_app import celery_app
from typing import Dict, List, Optional
from datetime import datetime
from Backend.data_layer.database.models.workflow import WorkflowStatus
from celery import chain, group
import enum


class StepStatus(str, enum.Enum):
    SUCCESS = "success"
    COMPLETED = "completed"
    FAILED = "failed"
    PENDING = "pending"


@celery_app.task(
    name="tasks.workflow_tasks.execute_workflow_step",
    queue="workflow",
    priority=6,
    retry_backoff=True,
    max_retries=3
)
def execute_workflow_step(
    workflow_id: int,
    step_id: int,
    input_data: Dict,
    user_id: int,
    execution_id: Optional[int] = None
) -> Dict:
    """
    Execute a single workflow step asynchronously.
    """
    try:
        # TODO: Implement actual workflow step execution logic
        return {
            "status": StepStatus.SUCCESS,
            "workflow_id": workflow_id,
            "step_id": step_id,
            "execution_id": execution_id,
            "result": "Step executed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        result = {
            "status": StepStatus.FAILED,
            "workflow_id": workflow_id,
            "step_id": step_id,
            "execution_id": execution_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
        execute_workflow_step.retry(exc=e)
        return result


@celery_app.task(
    name="Backend.celery_app.tasks.workflow_tasks.create_workflow_task",
    queue="workflow",
    priority=5,
    retry_backoff=True,
    max_retries=3
)
async def create_workflow_task(workflow_data: Dict) -> Dict:
    """Create a new workflow in the database."""
    from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
    from Backend.data_layer.database.connection import get_db

    async for session in get_db():
        try:
            repo = WorkflowRepository(session)
            workflow = await repo.create_workflow(**workflow_data)
            await session.commit()
            return {"id": workflow.id, "status": workflow.status.value}
        except Exception as e:
            await session.rollback()
            create_workflow_task.retry(exc=e)
            raise


@celery_app.task(
    name="Backend.celery_app.tasks.workflow_tasks.delete_workflow_task",
    queue="workflow",
    priority=5,
    retry_backoff=True,
    max_retries=3
)
async def delete_workflow_task(workflow_id: int) -> Dict:
    """Delete a workflow from the database."""
    from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
    from Backend.data_layer.database.connection import get_db

    async for session in get_db():
        try:
            repo = WorkflowRepository(session)
            await repo.delete_workflow(workflow_id)
            await session.commit()
            return {"status": "success", "deleted_id": workflow_id}
        except Exception as e:
            await session.rollback()
            delete_workflow_task.retry(exc=e)
            raise


@celery_app.task(
    name="Backend.celery_app.tasks.workflow_tasks.update_workflow_task",
    queue="workflow",
    priority=5,
    retry_backoff=True,
    max_retries=3
)
async def update_workflow_task(workflow_id: int, updates: Dict) -> Dict:
    """Update an existing workflow in the database."""
    from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
    from Backend.data_layer.database.connection import get_db

    async for session in get_db():
        try:
            repo = WorkflowRepository(session)
            workflow = await repo.update_workflow(workflow_id, updates)
            await session.commit()
            return {"id": workflow.id, "status": workflow.status.value}
        except Exception as e:
            await session.rollback()
            update_workflow_task.retry(exc=e)
            raise


@celery_app.task(
    name="Backend.celery_app.tasks.workflow_tasks.get_workflows_task",
    queue="workflow",
    priority=6
)
async def get_workflows_task() -> List[Dict]:
    """Retrieve all workflows from the database."""
    from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
    from Backend.data_layer.database.connection import get_db

    async for session in get_db():
        repo = WorkflowRepository(session)
        workflows = await repo.get_all_workflows()
        return [{"id": w.id, "name": w.name, "status": w.status.value} for w in workflows]


@celery_app.task(
    name="Backend.celery_app.tasks.workflow_tasks.get_workflow_by_id_task",
    queue="workflow",
    priority=6
)
async def get_workflow_by_id_task(workflow_id: int) -> Optional[Dict]:
    """Retrieve a workflow by ID from the database."""
    from Backend.data_layer.repositories.workflow_repository import WorkflowRepository
    from Backend.data_layer.database.connection import get_db

    async for session in get_db():
        repo = WorkflowRepository(session)
        workflow = await repo.get_workflow(workflow_id)
        return workflow.to_dict() if workflow else None


@celery_app.task(
    name="tasks.workflow_tasks.collect_results",
    queue="workflow"
)
def collect_results(results: List[Dict]) -> Dict:
    """
    Collect and process the results of all workflow steps.
    """
    return {
        "status": StepStatus.COMPLETED if all(r.get("status") == StepStatus.SUCCESS for r in results) else StepStatus.FAILED,
        "steps": results
    }


@celery_app.task(
    name="tasks.workflow_tasks.process_workflow",
    queue="workflow",
    priority=7
)
def process_workflow(
    workflow_id: int,
    steps: List[Dict],
    user_id: int,
    context: Optional[Dict] = None
) -> Dict:
    """
    Process an entire workflow by executing its steps in sequence.
    """
    current_context = context or {}

    # Create a list of tasks to execute
    workflow_steps = []
    for step in steps:
        step_task = execute_workflow_step.s(
            workflow_id=workflow_id,
            step_id=step["id"],
            input_data={**step["input"], **current_context},
            user_id=user_id
        )
        workflow_steps.append(step_task)

    # Execute steps in parallel and collect results
    workflow_chain = group(workflow_steps) | collect_results.s()
    result = workflow_chain.apply_async()

    # Return initial response
    return {
        "workflow_id": workflow_id,
        "status": WorkflowStatus.ACTIVE.value,
        "task_id": result.id,
        "steps": [{"step_id": step["id"], "status": StepStatus.PENDING} for step in steps]
    }
