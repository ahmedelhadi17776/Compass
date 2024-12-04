"""merge heads

Revision ID: 313ab9bd883a
Revises: 2024_01_task_models, ccc6e6b3d3d4
Create Date: 2024-12-02 12:39:29.885128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '313ab9bd883a'
down_revision: Union[str, None] = ('2024_01_task_models', 'ccc6e6b3d3d4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
