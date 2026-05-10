"""generated_design: allow concept-only draft generation

Revision ID: b4a9c6e2f105
Revises: a3f1e9d42c08
Create Date: 2026-05-11 02:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "b4a9c6e2f105"
down_revision = "a3f1e9d42c08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "generated_design",
        "rule_id",
        existing_type=sa.UUID(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "generated_design",
        "rule_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
