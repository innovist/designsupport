"""admin_console_models

Revision ID: 075f36dca65b
Revises: 
Create Date: 2026-05-08 05:09:35.142157

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '075f36dca65b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create admin_sessions table
    op.create_table(
        'admin_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('admin_sessions_user_id_is_active_idx', 'admin_sessions', ['user_id', 'is_active'], unique=False)
    op.create_index('admin_sessions_tenant_id_is_active_idx', 'admin_sessions', ['tenant_id', 'is_active'], unique=False)
    op.create_index('admin_sessions_user_id_idx', 'admin_sessions', ['user_id'], unique=False)
    op.create_index('admin_sessions_tenant_id_idx', 'admin_sessions', ['tenant_id'], unique=False)
    op.create_index('admin_sessions_expires_at_idx', 'admin_sessions', ['expires_at'], unique=False)
    op.create_index('admin_sessions_is_active_idx', 'admin_sessions', ['is_active'], unique=False)

    # Create policy_change_log table
    op.create_table(
        'policy_change_log',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('policy_id', sa.String(length=255), nullable=False),
        sa.Column('policy_type', sa.String(length=20), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('changed_by', sa.UUID(), nullable=False),
        sa.Column('change_type', sa.String(length=20), nullable=False),
        sa.Column('previous_version', sa.Integer(), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=False),
        sa.Column('change_details', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('policy_change_log_policy_id_version_idx', 'policy_change_log', ['policy_id', sa.text('version DESC')], unique=False)
    op.create_index('policy_change_log_policy_type_created_at_idx', 'policy_change_log', ['policy_type', sa.text('created_at DESC')], unique=False)
    op.create_index('policy_change_log_changed_by_created_at_idx', 'policy_change_log', ['changed_by', sa.text('created_at DESC')], unique=False)
    op.create_index('policy_change_log_policy_id_idx', 'policy_change_log', ['policy_id'], unique=False)
    op.create_index('policy_change_log_version_idx', 'policy_change_log', ['version'], unique=False)
    op.create_index('policy_change_log_changed_by_idx', 'policy_change_log', ['changed_by'], unique=False)

    # Create admin_metrics table
    op.create_table(
        'admin_metrics',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('period', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('feature_key', sa.String(length=100), nullable=True),
        sa.Column('total_cost', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('cost_by_feature', sa.JSON(), nullable=False),
        sa.Column('total_tokens', sa.BigInteger(), nullable=False),
        sa.Column('tokens_by_feature', sa.JSON(), nullable=False),
        sa.Column('prompt_tokens', sa.BigInteger(), nullable=False),
        sa.Column('completion_tokens', sa.BigInteger(), nullable=False),
        sa.Column('total_invocations', sa.Integer(), nullable=False),
        sa.Column('invocations_by_feature', sa.JSON(), nullable=False),
        sa.Column('successful_invocations', sa.Integer(), nullable=False),
        sa.Column('failed_invocations', sa.Integer(), nullable=False),
        sa.Column('failure_rate', sa.Float(), nullable=False),
        sa.Column('failure_reasons', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('admin_metrics_period_start_date_idx', 'admin_metrics', ['period', sa.text('start_date DESC')], unique=False)
    op.create_index('admin_metrics_feature_key_period_start_date_idx', 'admin_metrics', ['feature_key', 'period', sa.text('start_date DESC')], unique=False)
    op.create_index('admin_metrics_created_at_idx', 'admin_metrics', [sa.text('created_at DESC')], unique=False)
    op.create_index('admin_metrics_period_idx', 'admin_metrics', ['period'], unique=False)
    op.create_index('admin_metrics_start_date_idx', 'admin_metrics', ['start_date'], unique=False)
    op.create_index('admin_metrics_end_date_idx', 'admin_metrics', ['end_date'], unique=False)
    op.create_index('admin_metrics_feature_key_idx', 'admin_metrics', ['feature_key'], unique=False)

    # Create feature_policies table
    op.create_table(
        'feature_policies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('feature_key', sa.String(length=100), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('primary_model', sa.String(length=255), nullable=False),
        sa.Column('fallback_models', sa.JSON(), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False),
        sa.Column('max_cost_per_request', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('max_cost_per_day', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('max_cost_per_month', sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('required_model_types', sa.JSON(), nullable=False),
        sa.Column('min_context_length', sa.Integer(), nullable=False),
        sa.Column('supports_streaming', sa.Boolean(), nullable=False),
        sa.Column('supports_function_calling', sa.Boolean(), nullable=False),
        sa.Column('max_tokens_per_request', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('modified_by', sa.UUID(), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('feature_key')
    )
    op.create_index('feature_policies_feature_key_version_idx', 'feature_policies', ['feature_key', sa.text('version DESC')], unique=False)
    op.create_index('feature_policies_is_active_feature_key_idx', 'feature_policies', ['is_active', 'feature_key'], unique=False)
    op.create_index('feature_policies_feature_key_idx', 'feature_policies', ['feature_key'], unique=True)
    op.create_index('feature_policies_version_idx', 'feature_policies', ['version'], unique=False)
    op.create_index('feature_policies_is_active_idx', 'feature_policies', ['is_active'], unique=False)

    # Create admin_prompt_policies table
    op.create_table(
        'admin_prompt_policies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('feature_key', sa.String(length=100), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('user_template', sa.Text(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False),
        sa.Column('max_tokens', sa.Integer(), nullable=False),
        sa.Column('top_p', sa.Float(), nullable=False),
        sa.Column('frequency_penalty', sa.Float(), nullable=False),
        sa.Column('presence_penalty', sa.Float(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('modified_by', sa.UUID(), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('feature_key')
    )
    op.create_index('admin_prompt_policies_feature_key_version_idx', 'admin_prompt_policies', ['feature_key', sa.text('version DESC')], unique=False)
    op.create_index('admin_prompt_policies_is_active_feature_key_idx', 'admin_prompt_policies', ['is_active', 'feature_key'], unique=False)
    op.create_index('admin_prompt_policies_feature_key_idx', 'admin_prompt_policies', ['feature_key'], unique=True)
    op.create_index('admin_prompt_policies_version_idx', 'admin_prompt_policies', ['version'], unique=False)
    op.create_index('admin_prompt_policies_is_active_idx', 'admin_prompt_policies', ['is_active'], unique=False)

    # Create admin_tenants table
    op.create_table(
        'admin_tenants',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('plan', sa.String(length=50), nullable=False),
        sa.Column('max_users', sa.Integer(), nullable=False),
        sa.Column('max_projects', sa.Integer(), nullable=False),
        sa.Column('max_storage_gb', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('admin_tenants_is_active_plan_idx', 'admin_tenants', ['is_active', 'plan'], unique=False)
    op.create_index('admin_tenants_created_at_idx', 'admin_tenants', [sa.text('created_at DESC')], unique=False)
    op.create_index('admin_tenants_is_active_idx', 'admin_tenants', ['is_active'], unique=False)

    # Create user_tenant_roles table
    op.create_table(
        'user_tenant_roles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'tenant_id', name='user_tenant_roles_user_id_tenant_id_key')
    )
    op.create_index('user_tenant_roles_tenant_id_role_idx', 'user_tenant_roles', ['tenant_id', 'role'], unique=False)
    op.create_index('user_tenant_roles_user_id_is_active_idx', 'user_tenant_roles', ['user_id', 'is_active'], unique=False)
    op.create_index('user_tenant_roles_user_id_idx', 'user_tenant_roles', ['user_id'], unique=False)
    op.create_index('user_tenant_roles_tenant_id_idx', 'user_tenant_roles', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_table('user_tenant_roles')
    op.drop_table('admin_tenants')
    op.drop_table('admin_prompt_policies')
    op.drop_table('feature_policies')
    op.drop_table('admin_metrics')
    op.drop_table('policy_change_log')
    op.drop_table('admin_sessions')