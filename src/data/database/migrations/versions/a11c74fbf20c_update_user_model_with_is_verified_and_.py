"""Update user model with is_verified and full_name changes

Revision ID: a11c74fbf20c
Revises: 62a1d1a625f4
Create Date: 2024-12-01 12:14:53.130395

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = 'a11c74fbf20c'
down_revision: Union[str, None] = '62a1d1a625f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create temporary nullable full_name column
    op.add_column('users', sa.Column('full_name', sa.String(length=100), nullable=True))
    
    # Create a table object for the update
    users = table('users',
        column('first_name', sa.String),
        column('last_name', sa.String),
        column('full_name', sa.String)
    )
    
    # Update full_name with concatenated first_name and last_name
    op.execute(
        users.update()
        .values(
            full_name=sa.func.btrim(
                sa.func.concat(
                    sa.func.coalesce(users.c.first_name, ''),
                    sa.text("' '"),
                    sa.func.coalesce(users.c.last_name, '')
                )
            )
        )
    )
    
    # Update any remaining NULL full_names to a default value
    op.execute(
        users.update()
        .where(users.c.full_name == None)
        .values(full_name='Unknown User')
    )
    
    # Now make full_name non-nullable
    op.alter_column('users', 'full_name',
        existing_type=sa.String(length=100),
        nullable=False
    )
    
    # Add other columns
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))
    
    # Drop old indexes and constraints
    op.drop_index('idx_users_email_username', table_name='users')
    op.drop_index('ix_users_username', table_name='users')
    op.drop_constraint('uq_users_username', 'users', type_='unique')
    
    # Create new index
    op.create_index('idx_users_email', 'users', ['email'], unique=False)
    
    # Drop old columns
    op.drop_constraint('users_role_id_fkey', 'users', type_='foreignkey')
    op.drop_column('users', 'role_id')
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'username')
    op.drop_column('users', 'last_name')


def downgrade() -> None:
    # Add back old columns
    op.add_column('users', sa.Column('last_name', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('username', sa.VARCHAR(length=50), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('first_name', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('role_id', sa.INTEGER(), autoincrement=False, nullable=True))
    
    # Restore foreign key
    op.create_foreign_key('users_role_id_fkey', 'users', 'roles', ['role_id'], ['id'])
    
    # Drop new index
    op.drop_index('idx_users_email', table_name='users')
    
    # Restore old constraints and indexes
    op.create_unique_constraint('uq_users_username', 'users', ['username'])
    op.create_index('ix_users_username', 'users', ['username'], unique=False)
    op.create_index('idx_users_email_username', 'users', ['email', 'username'], unique=False)
    
    # Drop new columns
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'is_verified')
    op.drop_column('users', 'full_name')
