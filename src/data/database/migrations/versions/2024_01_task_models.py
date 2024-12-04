"""Add task-related models.

Revision ID: 2024_01_task_models
Revises: f75f6fdb4c5d
Create Date: 2024-01-20 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '2024_01_task_models'
down_revision = 'f75f6fdb4c5d'  # Update this to match your previous migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create task_status table
    op.create_table(
        'task_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(255)),
        sa.Column('color_code', sa.String(7)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_task_status_name', 'task_status', ['name'])

    # Create task_priorities table
    op.create_table(
        'task_priorities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(255)),
        sa.Column('weight', sa.Integer()),
        sa.Column('color_code', sa.String(7)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_task_priorities_name', 'task_priorities', ['name'])

    # Create task_categories table
    op.create_table(
        'task_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(255)),
        sa.Column('color_code', sa.String(7)),
        sa.Column('icon', sa.String(50)),
        sa.Column('parent_id', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['parent_id'], ['task_categories.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_task_categories_name', 'task_categories', ['name'])

    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_workflows_name', 'workflows', ['name'])
    op.create_index('idx_workflows_created_by', 'workflows', ['created_by'])

    # Create workflow_steps table
    op.create_table(
        'workflow_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer()),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('order', sa.Integer()),
        sa.Column('requirements', postgresql.JSON()),
        sa.Column('auto_advance', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_workflow_steps_workflow_id', 'workflow_steps', ['workflow_id'])

    # Create workflow_step_transitions table
    op.create_table(
        'workflow_step_transitions',
        sa.Column('from_step_id', sa.Integer()),
        sa.Column('to_step_id', sa.Integer()),
        sa.ForeignKeyConstraint(['from_step_id'], ['workflow_steps.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_step_id'], ['workflow_steps.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('from_step_id', 'to_step_id')
    )
    op.create_index('idx_step_transitions_from', 'workflow_step_transitions', ['from_step_id'])
    op.create_index('idx_step_transitions_to', 'workflow_step_transitions', ['to_step_id'])

    # Create tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(255)),
        sa.Column('color_code', sa.String(7)),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_tags_name', 'tags', ['name'])
    op.create_index('idx_tags_created_by', 'tags', ['created_by'])

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('status_id', sa.Integer(), nullable=False),
        sa.Column('priority_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer()),
        sa.Column('due_date', sa.DateTime()),
        sa.Column('start_date', sa.DateTime()),
        sa.Column('completion_date', sa.DateTime()),
        sa.Column('estimated_hours', sa.Float()),
        sa.Column('actual_hours', sa.Float()),
        sa.Column('external_sync_id', sa.String(255), unique=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('workflow_step_id', sa.Integer()),
        sa.CheckConstraint('due_date > created_at', name='ck_tasks_due_date_after_creation'),
        sa.CheckConstraint('completion_date > created_at', name='ck_tasks_completion_after_creation'),
        sa.CheckConstraint('estimated_hours >= 0'),
        sa.CheckConstraint('actual_hours >= 0'),
        sa.ForeignKeyConstraint(['status_id'], ['task_status.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['priority_id'], ['task_priorities.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['category_id'], ['task_categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_step_id'], ['workflow_steps.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tasks_user_id', 'tasks', ['user_id'])
    op.create_index('idx_tasks_status_id', 'tasks', ['status_id'])
    op.create_index('idx_tasks_due_date', 'tasks', ['due_date'])
    op.create_index('idx_tasks_created_at', 'tasks', ['created_at'])

    # Create task_tags table
    op.create_table(
        'task_tags',
        sa.Column('task_id', sa.Integer()),
        sa.Column('tag_id', sa.Integer()),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('task_id', 'tag_id')
    )
    op.create_index('idx_task_tags_task_id', 'task_tags', ['task_id'])
    op.create_index('idx_task_tags_tag_id', 'task_tags', ['tag_id'])

    # Create task_attachments table
    op.create_table(
        'task_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer()),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('file_type', sa.String(100)),
        sa.Column('file_size', sa.Integer()),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('uploaded_by', sa.Integer()),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id']),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create task_comments table
    op.create_table(
        'task_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer()),
        sa.Column('user_id', sa.Integer()),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('parent_id', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['task_comments.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create task_history table
    op.create_table(
        'task_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer()),
        sa.Column('user_id', sa.Integer()),
        sa.Column('change_type', sa.String(50)),
        sa.Column('old_value', postgresql.JSON()),
        sa.Column('new_value', postgresql.JSON()),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create summarized_content table
    op.create_table(
        'summarized_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer()),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('key_points', sa.Text()),
        sa.Column('generated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id')
    )
    op.create_index('idx_summarized_content_task_id', 'summarized_content', ['task_id'])

def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('summarized_content')
    op.drop_table('task_history')
    op.drop_table('task_comments')
    op.drop_table('task_attachments')
    op.drop_table('task_tags')
    op.drop_table('tasks')
    op.drop_table('tags')
    op.drop_table('workflow_step_transitions')
    op.drop_table('workflow_steps')
    op.drop_table('workflows')
    op.drop_table('task_categories')
    op.drop_table('task_priorities')
    op.drop_table('task_status')
