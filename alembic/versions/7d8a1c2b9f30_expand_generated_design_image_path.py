"""expand_generated_design_image_path

Revision ID: 7d8a1c2b9f30
Revises: 29f52f1264be
Create Date: 2026-05-10 05:35:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "7d8a1c2b9f30"
down_revision = "29f52f1264be"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "generated_design",
        "image_path",
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "generated_design",
        "image_path",
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
