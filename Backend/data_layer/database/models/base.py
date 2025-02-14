from data_layer.database.models.user import User, Role, UserRole
from data_layer.database.models.task import Task
from data_layer.database.models.project import Project, Organization
from data_layer.database.models.workflow import Workflow
from sqlalchemy.orm import declarative_base

# ✅ Correct Base Model (Remove @as_declarative)
Base = declarative_base()

# ✅ Ensure all models are imported
__all__ = [
    "User",
    "Role",
    "UserRole",
    "Task",
    "Project",
    "Organization",
    "Workflow"
]
