"""Add task models

Revision ID: 6ffbe0b5f346
Revises: 313ab9bd883a
Create Date: 2024-12-02 12:39:47.426569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6ffbe0b5f346'
down_revision: Union[str, None] = '313ab9bd883a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop tables in correct order (respecting foreign key constraints)
    op.drop_table('role_permissions')
    
    op.drop_index('ix_permissions_id', table_name='permissions')
    op.drop_index('ix_permissions_name', table_name='permissions')
    op.drop_table('permissions')
    
    op.drop_index('ix_user_roles_id', table_name='user_roles')
    op.drop_table('user_roles')
    
    op.drop_index('ix_roles_id', table_name='roles')
    op.drop_index('ix_roles_name', table_name='roles')
    op.drop_table('roles')
    
    op.drop_index('ix_user_sessions_id', table_name='user_sessions')
    op.drop_index('ix_user_sessions_session_token', table_name='user_sessions')
    op.drop_table('user_sessions')
    
    op.drop_index('idx_password_resets_expires_at', table_name='password_resets')
    op.drop_index('idx_password_resets_token', table_name='password_resets')
    op.drop_index('idx_password_resets_user_id', table_name='password_resets')
    op.drop_index('ix_password_resets_id', table_name='password_resets')
    op.drop_index('ix_password_resets_token', table_name='password_resets')
    op.drop_table('password_resets')

    # Create or update task-related indexes
    op.create_index(op.f('ix_task_attachments_id'), 'task_attachments', ['id'], unique=False)
    
    op.drop_index('idx_task_categories_name', table_name='task_categories')
    op.create_index(op.f('ix_task_categories_id'), 'task_categories', ['id'], unique=False)
    
    op.create_index(op.f('ix_task_comments_id'), 'task_comments', ['id'], unique=False)
    op.create_index(op.f('ix_task_history_id'), 'task_history', ['id'], unique=False)
    
    op.drop_index('idx_task_priorities_name', table_name='task_priorities')
    op.create_index(op.f('ix_task_priorities_id'), 'task_priorities', ['id'], unique=False)
    
    op.drop_index('idx_task_status_name', table_name='task_status')
    op.create_index(op.f('ix_task_status_id'), 'task_status', ['id'], unique=False)
    
    # Update tasks table
    op.alter_column('tasks', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)


def downgrade() -> None:
    # Revert tasks table changes
    op.alter_column('tasks', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    
    # Drop task-related indexes
    op.drop_index(op.f('ix_task_status_id'), table_name='task_status')
    op.create_index('idx_task_status_name', 'task_status', ['name'], unique=False)
    
    op.drop_index(op.f('ix_task_priorities_id'), table_name='task_priorities')
    op.create_index('idx_task_priorities_name', 'task_priorities', ['name'], unique=False)
    
    op.drop_index(op.f('ix_task_history_id'), table_name='task_history')
    op.drop_index(op.f('ix_task_comments_id'), table_name='task_comments')
    
    op.drop_index(op.f('ix_task_categories_id'), table_name='task_categories')
    op.create_index('idx_task_categories_name', 'task_categories', ['name'], unique=False)
    
    op.drop_index(op.f('ix_task_attachments_id'), table_name='task_attachments')

    # Recreate original tables
    op.create_table('password_resets',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('token', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('expires_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='password_resets_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='password_resets_pkey')
    )
    op.create_index('ix_password_resets_token', 'password_resets', ['token'], unique=True)
    op.create_index('ix_password_resets_id', 'password_resets', ['id'], unique=False)
    op.create_index('idx_password_resets_user_id', 'password_resets', ['user_id'], unique=False)
    op.create_index('idx_password_resets_token', 'password_resets', ['token'], unique=False)
    op.create_index('idx_password_resets_expires_at', 'password_resets', ['expires_at'], unique=False)
    
    op.create_table('user_sessions',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('session_token', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('expires_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='user_sessions_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='user_sessions_pkey')
    )
    op.create_index('ix_user_sessions_session_token', 'user_sessions', ['session_token'], unique=True)
    op.create_index('ix_user_sessions_id', 'user_sessions', ['id'], unique=False)
    
    op.create_table('roles',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='roles_pkey'),
    sa.UniqueConstraint('name', name='roles_name_key')
    )
    op.create_index('ix_roles_name', 'roles', ['name'], unique=False)
    op.create_index('ix_roles_id', 'roles', ['id'], unique=False)
    
    op.create_table('user_roles',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('role_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name='user_roles_role_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='user_roles_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='user_roles_pkey')
    )
    op.create_index('ix_user_roles_id', 'user_roles', ['id'], unique=False)
    
    op.create_table('permissions',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('resource', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('action', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='permissions_pkey'),
    sa.UniqueConstraint('name', name='permissions_name_key')
    )
    op.create_index('ix_permissions_name', 'permissions', ['name'], unique=False)
    op.create_index('ix_permissions_id', 'permissions', ['id'], unique=False)
    
    op.create_table('role_permissions',
    sa.Column('role_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('permission_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], name='role_permissions_permission_id_fkey'),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name='role_permissions_role_id_fkey'),
    sa.PrimaryKeyConstraint('role_id', 'permission_id', name='role_permissions_pkey')
    )
