"""add first and last name fields

Revision ID: add_name_fields
Revises: 5ad61ee3cad4
Create Date: 2024-12-01 06:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_name_fields'
down_revision: Union[str, None] = '5ad61ee3cad4'  # Points to the initial migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the full_name column if it exists
    op.drop_column('users', 'full_name')
    
    # Add first_name and last_name columns
    op.add_column('users', sa.Column('first_name', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(50), nullable=True))


def downgrade() -> None:
    # Remove first_name and last_name columns
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')
    
    # Add back the full_name column
    op.add_column('users', sa.Column('full_name', sa.String(100), nullable=True))
