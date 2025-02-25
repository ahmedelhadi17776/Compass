"""fix enum types

Revision ID: fix_enum_types
Revises: e5997e29d6a1
Create Date: 2025-02-24 05:05:17.355+00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Enum
from Backend.data_layer.database.models.task import TaskStatus, TaskPriority
from Backend.data_layer.database.models.workflow import WorkflowStatus, WorkflowType

# revision identifiers, used by Alembic.
revision: str = 'fix_enum_types'
down_revision: Union[str, None] = 'e5997e29d6a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types first
    task_status = sa.Enum(TaskStatus, name='taskstatus')
    task_status.create(op.get_bind(), checkfirst=True)

    task_priority = sa.Enum(TaskPriority, name='taskpriority')
    task_priority.create(op.get_bind(), checkfirst=True)

    workflow_status = sa.Enum(WorkflowStatus, name='workflowstatus')
    workflow_status.create(op.get_bind(), checkfirst=True)

    workflow_type = sa.Enum(WorkflowType, name='workflowtype')
    workflow_type.create(op.get_bind(), checkfirst=True)

    # Drop existing tables if they exist
    op.execute('DROP TABLE IF EXISTS ai_models CASCADE')
    op.execute('DROP TABLE IF EXISTS agent_types CASCADE')
    op.execute('DROP TABLE IF EXISTS model_types CASCADE')
    op.execute('DROP TABLE IF EXISTS subscription_plans CASCADE')
    op.execute('DROP TABLE IF EXISTS permissions CASCADE')
    op.execute('DROP TABLE IF EXISTS roles CASCADE')
    op.execute('DROP TABLE IF EXISTS organizations CASCADE')

    # Create tables in correct order
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'subscription_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('price', sa.Numeric(10, 2)),
        sa.Column('features', sa.JSON()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'model_types',
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.PrimaryKeyConstraint('type')
    )

    op.create_table(
        'agent_types',
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.PrimaryKeyConstraint('type')
    )

    op.create_table(
        'ai_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50)),
        sa.Column('type', sa.String(100)),
        sa.Column('storage_path', sa.String(255)),
        sa.Column('model_metadata', sa.JSON()),
        sa.Column('status', sa.String(50)),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('ai_models')
    op.drop_table('agent_types')
    op.drop_table('model_types')
    op.drop_table('subscription_plans')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('organizations')

    # Drop enum types
    op.execute('DROP TYPE IF EXISTS workflowtype')
    op.execute('DROP TYPE IF EXISTS workflowstatus')
    op.execute('DROP TYPE IF EXISTS taskpriority')
    op.execute('DROP TYPE IF EXISTS taskstatus')