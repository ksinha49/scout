"""add unique constraint to user email

Revision ID: b8a2c3f2d1a4
Revises: c69f45358db4, 57c599a3cb57
Create Date: 2025-02-14 00:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b8a2c3f2d1a4'
down_revision = ('c69f45358db4', '57c599a3cb57')
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint('uq_user_email', 'user', ['email'])


def downgrade() -> None:
    op.drop_constraint('uq_user_email', 'user', type_='unique')
