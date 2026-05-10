"""trend_insight: add title and source_urls columns

Revision ID: a3f1e9d42c08
Revises: 7d8a1c2b9f30
Create Date: 2026-05-10 23:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a3f1e9d42c08"
down_revision = "7d8a1c2b9f30"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trend_insight", sa.Column("title", sa.String(200), nullable=True))
    op.add_column("trend_insight", sa.Column("source_urls", postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.alter_column("trend_insight", "evidence_quote", nullable=True)


def downgrade() -> None:
    op.drop_column("trend_insight", "source_urls")
    op.drop_column("trend_insight", "title")
    op.alter_column("trend_insight", "evidence_quote", nullable=False)
