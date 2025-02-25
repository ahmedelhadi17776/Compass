from Backend.api.routes import status
from Backend.core.celery_app import celery_app
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
