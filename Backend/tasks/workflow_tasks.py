from Backend.api.routes import status
from Backend.core.celery_app import celery_app
from typing import Dict, List, Optional
from datetime import datetime
from Backend.data_layer.database.models.workflow import WorkflowStatus
import enum


class StepStatus(str, enum.Enum):
    SUCCESS = "success"
    COMPLETED = "completed"
    FAILED = "failed"


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
    user_id: int
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
            "result": "Step executed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        execute_workflow_step.retry(exc=e)


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
    results = []
    current_context = context or {}

    for step in steps:
        try:
            # Execute each step with the current context
            result = execute_workflow_step.delay(
                workflow_id=workflow_id,
                step_id=step["id"],
                input_data={**step["input"], **current_context},
                user_id=user_id
            )

            # Update context with step result
            step_result = result.get()
            current_context.update(step_result.get("result", {}))

            results.append({
                "step_id": step["id"],
                "task_id": result.id,
                "status": StepStatus.COMPLETED,
                "result": step_result
            })
        except Exception as e:
            results.append({
                "step_id": step["id"],
                "error": str(e),
                "status": StepStatus.FAILED
            })
            # Optionally break workflow on failure
            break

    return {
        "workflow_id": workflow_id,
        "status": WorkflowStatus.ACTIVE.value if all(r["status"] == StepStatus.COMPLETED for r in results) else WorkflowStatus.ARCHIVED.value,
        "steps": results,
        "final_context": current_context
    }
