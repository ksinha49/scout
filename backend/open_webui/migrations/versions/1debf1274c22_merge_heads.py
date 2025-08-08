"""Merge heads

Revision ID: 1debf1274c22
Revises: 3781e22d8b01, b8a2c3f2d1a4
Create Date: 2025-08-08 22:23:48.037559

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import open_webui.internal.db


# revision identifiers, used by Alembic.
revision: str = '1debf1274c22'
down_revision: Union[str, None] = ('3781e22d8b01', 'b8a2c3f2d1a4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
