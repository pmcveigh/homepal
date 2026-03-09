"""add task template flag

Revision ID: 20260309_04
Revises: 20260307_03
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa


revision = "20260309_04"
down_revision = "20260307_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("is_template", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column("tasks", "is_template", server_default=None)


def downgrade() -> None:
    op.drop_column("tasks", "is_template")
