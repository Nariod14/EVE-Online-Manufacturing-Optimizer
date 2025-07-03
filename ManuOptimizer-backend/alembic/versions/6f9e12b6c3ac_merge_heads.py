"""Merge heads

Revision ID: 6f9e12b6c3ac
Revises: fix_blueprint_columns, a2a58868ee8f
Create Date: 2025-06-10 13:53:43.209351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f9e12b6c3ac'
down_revision: Union[str, None] = ('a2a58868ee8f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
