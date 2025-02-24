from typing import Optional, List
from pydantic import validator
from Backend.app.schemas.task_schemas import TaskBase


class TaskCreate(TaskBase):
    project_id: int
    organization_id: int
    workflow_id: Optional[int] = None
    dependencies: Optional[List[int]] = []

    @validator('dependencies')
    def validate_dependencies(cls, v):
        if v and len(v) > 0:
            # Ensure no self-dependencies
            if any(not isinstance(dep_id, int) or dep_id < 1 for dep_id in v):
                raise ValueError("Invalid dependency ID")
        return v
