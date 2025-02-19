from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, JSON, Text, DateTime, Boolean
from alembic import context
from Backend.data_layer.database.models.base import Base
from Backend.data_layer.database.models import (
    User, Role, UserRole, UserPreferences,
    Organization, Project, ProjectMember,
    Task, TaskStatus, Workflow, WorkflowStep,
    WorkflowTransition, WorkflowExecution, WorkflowAgentLink,
    TaskCategory, TaskAttachment, TaskComment, TaskHistory,
    Session, CalendarEvent, AgentAction, AgentFeedback,
    AIModel, AgentType, ModelType, ContextSnapshot,
    KnowledgeBase, File, SystemLog, SubscriptionPlan,
    Subscription, Payment, Permission, RolePermission,
    SecurityAuditLog, DailySummary, AIAgentInteraction,
    EmailOrganization, RAGQuery, MeetingNotes,
    ProductivityMetrics, EmotionalMetrics,
    UserWorkspaceSettings, Todo, TodoHistory,
    TodoPriority, TodoStatus, WorkflowStepExecution
)
import os
import sys
from pathlib import Path

# Add the parent directory of Backend to the Python path
# Go up 4 levels to reach the parent of Backend
project_root = str(Path(__file__).parents[3].parent)
sys.path.append(project_root)


# Load Alembic configuration
config = context.config

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use SQLAlchemy metadata for migrations
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Compare column types
        compare_server_default=True,  # Compare default values
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Compare column types
            compare_server_default=True,  # Compare default values
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
