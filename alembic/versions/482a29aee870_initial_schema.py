"""initial_schema

Revision ID: 482a29aee870
Revises:
Create Date: 2026-05-09 04:00:03.072713
"""

from alembic import op

from app.models.base import Base
import app.models  # noqa: F401 - registers ORM models


revision = "482a29aee870"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
