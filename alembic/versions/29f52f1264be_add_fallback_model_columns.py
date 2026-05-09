"""add_fallback_model_columns

Revision ID: 29f52f1264be
Revises: 482a29aee870
Create Date: 2026-05-09 15:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '29f52f1264be'
down_revision = '482a29aee870'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('feature_model_setting',
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='2'))
    op.add_column('feature_model_setting',
        sa.Column('fallback_provider', sa.String(50), nullable=True))
    op.add_column('feature_model_setting',
        sa.Column('fallback_model', sa.String(100), nullable=True))
    op.add_column('feature_model_setting',
        sa.Column('fallback_retry_count', sa.Integer(), nullable=False, server_default='1'))


def downgrade() -> None:
    op.drop_column('feature_model_setting', 'fallback_retry_count')
    op.drop_column('feature_model_setting', 'fallback_model')
    op.drop_column('feature_model_setting', 'fallback_provider')
    op.drop_column('feature_model_setting', 'retry_count')
