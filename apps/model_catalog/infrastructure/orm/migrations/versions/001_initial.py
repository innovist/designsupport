"""Initial migration for model_catalog module.

Revision ID: 001
Revises:
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create model_catalog tables."""

    # Create model_providers table
    op.create_table(
        'model_providers',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('name', sa.String(255), unique=True, nullable=False),
        sa.Column('api_key_env', sa.String(255), nullable=False),
        sa.Column('base_url', sa.String(500), nullable=True),
        sa.Column('endpoint_path', sa.String(255), nullable=True),
        sa.Column('auth_scheme', sa.String(50), nullable=False, default='Bearer'),
        sa.Column('active', sa.Boolean(), nullable=False, default=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index('ix_model_providers_name', 'name'),
        sa.Index('ix_model_providers_name_active', 'name', 'active'),
    )

    # Create model_catalog table
    op.create_table(
        'model_catalog',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('provider_id', sa.String(255), sa.ForeignKey('model_providers.id'), nullable=False),
        sa.Column('model_name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('context_limit', sa.Integer(), nullable=True),
        sa.Column('cost_estimate', sa.Numeric(10, 4), nullable=True),
        sa.Column('modalities', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('active', sa.Boolean(), nullable=False, default=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('provider_id', 'model_name', name='uq_model_catalog_provider_model'),
        sa.Index('ix_model_catalog_provider', 'provider_id'),
        sa.Index('ix_model_catalog_provider_active', 'provider_id', 'active'),
        sa.Index('ix_model_catalog_type', 'type'),
        sa.Index('ix_model_catalog_type_active', 'type', 'active'),
    )

    # Create feature_model_policies table
    op.create_table(
        'feature_model_policies',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('feature_key', sa.String(255), unique=True, nullable=False),
        sa.Column('primary_model_id', sa.String(255), sa.ForeignKey('model_catalog.id'), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('max_cost_per_call', sa.Numeric(10, 4), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, default=1, server_default='1'),
        sa.Column('active', sa.Boolean(), nullable=False, default=True, server_default='true'),
        sa.Column('reviewer', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index('ix_feature_model_policies_feature_key', 'feature_key'),
        sa.Index('ix_feature_model_policies_feature_key_active', 'feature_key', 'active'),
        sa.Index('ix_feature_model_policies_version', 'version'),
    )

    # Create feature_model_policies_fallback_models table (M2M)
    op.create_table(
        'feature_model_policies_fallback_models',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('featuremodelpolicy_id', sa.String(255), sa.ForeignKey('feature_model_policies.id')),
        sa.Column('modelcatalog_id', sa.String(255), sa.ForeignKey('model_catalog.id')),
    )

    # Create prompt_policies table
    op.create_table(
        'prompt_policies',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('feature_key', sa.String(255), nullable=False),
        sa.Column('prompt_version', sa.String(255), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('user_template', sa.Text(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, default=True, server_default='true'),
        sa.Column('reviewer', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('feature_key', 'prompt_version', name='uq_prompt_policies_feature_version'),
        sa.Index('ix_prompt_policies_feature_key', 'feature_key'),
        sa.Index('ix_prompt_policies_feature_key_active', 'feature_key', 'active'),
    )

    # Create model_invocations table
    op.create_table(
        'model_invocations',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('feature_key', sa.String(255), nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('workspace_id', sa.String(36), nullable=False),  # UUID as string
        sa.Column('session_id', sa.String(36), nullable=True),  # UUID as string
        sa.Column('model_id', sa.String(255), sa.ForeignKey('model_catalog.id'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('tokens_in', sa.Integer(), nullable=True),
        sa.Column('tokens_out', sa.Integer(), nullable=True),
        sa.Column('cost_estimate', sa.Numeric(10, 4), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('error_code', sa.String(255), nullable=True),
        sa.Column('error_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index('ix_model_invocations_feature_key', 'feature_key'),
        sa.Index('ix_model_invocations_feature_key_created', 'feature_key', sa.desc('created_at')),
        sa.Index('ix_model_invocations_tenant_id', 'tenant_id'),
        sa.Index('ix_model_invocations_tenant_created', 'tenant_id', sa.desc('created_at')),
        sa.Index('ix_model_invocations_status', 'status'),
        sa.Index('ix_model_invocations_status_created', 'status', sa.desc('created_at')),
    )

    # Create policy_change_logs table
    op.create_table(
        'policy_change_logs',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('target_type', sa.String(255), nullable=False),
        sa.Column('target_id', sa.String(255), nullable=False),
        sa.Column('version_from', sa.Integer(), nullable=True),
        sa.Column('version_to', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.String(255), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Index('ix_policy_change_logs_target_type', 'target_type'),
        sa.Index('ix_policy_change_logs_target', 'target_type', 'target_id', sa.desc('created_at')),
        sa.Index('ix_policy_change_logs_actor', 'actor_id', sa.desc('created_at')),
    )


def downgrade() -> None:
    """Drop model_catalog tables."""

    op.drop_table('policy_change_logs')
    op.drop_table('model_invocations')
    op.drop_table('prompt_policies')
    op.drop_table('feature_model_policies_fallback_models')
    op.drop_table('feature_model_policies')
    op.drop_table('model_catalog')
    op.drop_table('model_providers')
