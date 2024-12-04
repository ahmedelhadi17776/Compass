"""add_user_locking_fields

Revision ID: ce77738ded48
Revises: 7ae1c0975b85
Create Date: 2024-12-02 11:07:06.543494

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce77738ded48'
down_revision: Union[str, None] = '7ae1c0975b85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user locking fields
    op.add_column('users', sa.Column('is_locked', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    # Remove user locking fields
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'is_locked')
