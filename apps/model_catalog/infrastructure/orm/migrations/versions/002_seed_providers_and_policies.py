"""Seed data migration for model_catalog.

Revision ID: 002
Revises: 001
Create Date: 2026-05-08

This migration seeds the model_catalog with:
- Initial model providers (bytedance, alibaba, google, openai)
- Model catalog entries for each provider
- Feature model policies with fallback chains

Implements REQ-04-POLICY-006 and REQ-04-POLICY-007.

This migration is IDEMPOTENT - safe to run multiple times.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


# Define table objects for data insertion
model_providers = table(
    'model_providers',
    column('id', sa.String),
    column('name', sa.String),
    column('api_key_env', sa.String),
    column('base_url', sa.String),
    column('endpoint_path', sa.String),
    column('auth_scheme', sa.String),
    column('active', sa.Boolean),
    column('created_at', sa.DateTime),
    column('updated_at', sa.DateTime),
)

model_catalog = table(
    'model_catalog',
    column('id', sa.String),
    column('provider_id', sa.String),
    column('model_name', sa.String),
    column('type', sa.String),
    column('context_limit', sa.Integer),
    column('cost_estimate', sa.Numeric),
    column('modalities', sa.JSON),
    column('active', sa.Boolean),
    column('created_at', sa.DateTime),
    column('updated_at', sa.DateTime),
)

feature_model_policies = table(
    'feature_model_policies',
    column('id', sa.String),
    column('feature_key', sa.String),
    column('primary_model_id', sa.String),
    column('parameters', sa.JSON),
    column('max_cost_per_call', sa.Numeric),
    column('max_tokens', sa.Integer),
    column('version', sa.Integer),
    column('active', sa.Boolean),
    column('reviewer', sa.String),
    column('created_at', sa.DateTime),
    column('updated_at', sa.DateTime),
)

feature_model_policies_fallback_models = table(
    'feature_model_policies_fallback_models',
    column('id', sa.Integer),
    column('featuremodelpolicy_id', sa.String),
    column('modelcatalog_id', sa.String),
)


def upgrade() -> None:
    """Seed model catalog with providers, models, and policies.

    This function is idempotent - it checks for existing data before inserting.
    Safe to run multiple times without creating duplicates.
    """
    connection = op.get_bind()

    # Check if data already exists (idempotency check)
    existing_providers = connection.execute(
        sa.text("SELECT COUNT(*) FROM model_providers WHERE id IN ('prov-bytedance', 'prov-alibaba', 'prov-google', 'prov-openai')")
    ).scalar()

    if existing_providers > 0:
        print("Model catalog seed data already exists. Skipping seed.")
        return

    print("Seeding model catalog with providers, models, and policies...")

    # Insert providers
    providers = [
        {
            'id': 'prov-bytedance',
            'name': 'bytedance',
            'api_key_env': 'BYTEDANCE_SEEDREAM_API_KEY',
            'base_url': 'https://ark.ap-southeast.bytepluses.com/api/v3',
            'endpoint_path': '/images/generations',
            'auth_scheme': 'Bearer',
            'active': True,
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        {
            'id': 'prov-alibaba',
            'name': 'alibaba',
            'api_key_env': 'ALIBABA_API_KEY',
            'base_url': 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1',
            'endpoint_path': '/images/generations',
            'auth_scheme': 'Bearer',
            'active': True,
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        {
            'id': 'prov-google',
            'name': 'google',
            'api_key_env': 'GEMINI_API_KEYS',
            'base_url': 'https://generativelanguage.googleapis.com/v1beta',
            'endpoint_path': '/models/gemini-3.1-flash-image-preview:generateContent',
            'auth_scheme': 'Bearer',
            'active': True,
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        {
            'id': 'prov-openai',
            'name': 'openai',
            'api_key_env': 'OPENAI_API_KEY',
            'base_url': 'https://api.openai.com/v1',
            'endpoint_path': '/images/generations',
            'auth_scheme': 'Bearer',
            'active': True,
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
    ]

    for provider in providers:
        op.bulk_insert(model_providers, [provider])

    # Insert models
    models = [
        # ByteDance models
        {
            'id': 'mdl-bytedance-seedream-4.5',
            'provider_id': 'prov-bytedance',
            'model_name': 'seedream-4.5',
            'type': 'image',
            'context_limit': None,
            'cost_estimate': 0.02,
            'modalities': ['image'],
            'active': True,
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        # Alibaba models
        {
            'id': 'mdl-alibaba-z-image-turbo',
            'provider_id': 'prov-alibaba',
            'model_name': 'z-image-turbo',
            'type': 'image',
            'context_limit': None,
            'cost_estimate': 0.015,
            'modalities': ['image'],
            'active': True,
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        # Google models
        {
            'id': 'mdl-google-gemini-3.1-flash-image-preview',
            'provider_id': 'prov-google',
            'model_name': 'gemini-3.1-flash-image-preview',
            'type': 'multimodal',
            'context_limit': 28000,
            'cost_estimate': 0.001,
            'modalities': ['text', 'image', 'vision'],
            'active': True,
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        {
            'id': 'mdl-google-gemini-2.5-pro',
            'provider_id': 'prov-google',
            'model_name': 'gemini-2.5-pro',
            'type': 'chat',
            'context_limit': 1000000,
            'cost_estimate': 0.002,
            'modalities': ['text', 'code'],
            'active': True,
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        # OpenAI models
        {
            'id': 'mdl-openai-gpt-image-2',
            'provider_id': 'prov-openai',
            'model_name': 'gpt-image-2',
            'type': 'image',
            'context_limit': None,
            'cost_estimate': 0.03,
            'modalities': ['image'],
            'active': True,
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        {
            'id': 'mdl-openai-gpt-4o',
            'provider_id': 'prov-openai',
            'model_name': 'gpt-4o',
            'type': 'chat',
            'context_limit': 128000,
            'cost_estimate': 0.005,
            'modalities': ['text', 'vision'],
            'active': True,
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
    ]

    for model in models:
        op.bulk_insert(model_catalog, [model])

    # Insert feature policies
    policies = [
        {
            'id': 'policy-imagegeneration-v1',
            'feature_key': 'ImageGeneration',
            'primary_model_id': 'mdl-bytedance-seedream-4.5',
            'parameters': {'quality': 'high', 'size': '1024x1024'},
            'max_cost_per_call': 0.05,
            'max_tokens': None,
            'version': 1,
            'active': True,
            'reviewer': 'system',
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        {
            'id': 'policy-trendresearch-v1',
            'feature_key': 'TrendResearch',
            'primary_model_id': 'mdl-google-gemini-2.5-pro',
            'parameters': {'temperature': 0.7, 'max_tokens': 2000},
            'max_cost_per_call': 0.01,
            'max_tokens': 2000,
            'version': 1,
            'active': True,
            'reviewer': 'system',
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        {
            'id': 'policy-conceptchat-v1',
            'feature_key': 'ConceptChat',
            'primary_model_id': 'mdl-google-gemini-2.5-pro',
            'parameters': {'temperature': 0.8, 'max_tokens': 1500},
            'max_cost_per_call': 0.01,
            'max_tokens': 1500,
            'version': 1,
            'active': True,
            'reviewer': 'system',
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        {
            'id': 'policy-usersketchanalysis-v1',
            'feature_key': 'UserSketchAnalysis',
            'primary_model_id': 'mdl-google-gemini-3.1-flash-image-preview',
            'parameters': {'temperature': 0.5},
            'max_cost_per_call': 0.01,
            'max_tokens': 1000,
            'version': 1,
            'active': True,
            'reviewer': 'system',
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        {
            'id': 'policy-referenceanalysis-v1',
            'feature_key': 'ReferenceAnalysis',
            'primary_model_id': 'mdl-google-gemini-2.5-pro',
            'parameters': {'temperature': 0.6, 'max_tokens': 2000},
            'max_cost_per_call': 0.01,
            'max_tokens': 2000,
            'version': 1,
            'active': True,
            'reviewer': 'system',
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        {
            'id': 'policy-abstraction-v1',
            'feature_key': 'Abstraction',
            'primary_model_id': 'mdl-google-gemini-2.5-pro',
            'parameters': {'temperature': 0.7, 'max_tokens': 1500},
            'max_cost_per_call': 0.01,
            'max_tokens': 1500,
            'version': 1,
            'active': True,
            'reviewer': 'system',
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        {
            'id': 'policy-sketchprompt-v1',
            'feature_key': 'SketchPrompt',
            'primary_model_id': 'mdl-google-gemini-2.5-pro',
            'parameters': {'temperature': 0.8, 'max_tokens': 1000},
            'max_cost_per_call': 0.01,
            'max_tokens': 1000,
            'version': 1,
            'active': True,
            'reviewer': 'system',
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        {
            'id': 'policy-specwriting-v1',
            'feature_key': 'SpecWriting',
            'primary_model_id': 'mdl-google-gemini-2.5-pro',
            'parameters': {'temperature': 0.6, 'max_tokens': 3000},
            'max_cost_per_call': 0.02,
            'max_tokens': 3000,
            'version': 1,
            'active': True,
            'reviewer': 'system',
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
        {
            'id': 'policy-verification-v1',
            'feature_key': 'Verification',
            'primary_model_id': 'mdl-google-gemini-2.5-pro',
            'parameters': {'temperature': 0.3, 'max_tokens': 2000},
            'max_cost_per_call': 0.01,
            'max_tokens': 2000,
            'version': 1,
            'active': True,
            'reviewer': 'system',
            'created_at': sa.func.now(),
            'updated_at': sa.func.now(),
        },
    ]

    for policy in policies:
        op.bulk_insert(feature_model_policies, [policy])

    # Insert fallback models for ImageGeneration policy
    # This uses the M2M relationship table
    fallback_models = [
        {
            'id': 1,
            'featuremodelpolicy_id': 'policy-imagegeneration-v1',
            'modelcatalog_id': 'mdl-alibaba-z-image-turbo',
        },
        {
            'id': 2,
            'featuremodelpolicy_id': 'policy-imagegeneration-v1',
            'modelcatalog_id': 'mdl-google-gemini-3.1-flash-image-preview',
        },
        {
            'id': 3,
            'featuremodelpolicy_id': 'policy-imagegeneration-v1',
            'modelcatalog_id': 'mdl-openai-gpt-image-2',
        },
    ]

    for fallback in fallback_models:
        op.bulk_insert(feature_model_policies_fallback_models, [fallback])

    print("Model catalog seed data inserted successfully.")


def downgrade() -> None:
    """Remove seeded data from model catalog.

    This removes only the data that was inserted by this migration.
    """
    connection = op.get_bind()

    # Delete fallback models (M2M relationships)
    connection.execute(
        sa.text(
            "DELETE FROM feature_model_policies_fallback_models "
            "WHERE featuremodelpolicy_id = 'policy-imagegeneration-v1'"
        )
    )

    # Delete feature policies
    policy_ids = [
        'policy-imagegeneration-v1',
        'policy-trendresearch-v1',
        'policy-conceptchat-v1',
        'policy-usersketchanalysis-v1',
        'policy-referenceanalysis-v1',
        'policy-abstraction-v1',
        'policy-sketchprompt-v1',
        'policy-specwriting-v1',
        'policy-verification-v1',
    ]
    for policy_id in policy_ids:
        connection.execute(
            sa.text("DELETE FROM feature_model_policies WHERE id = :id"),
            {'id': policy_id}
        )

    # Delete models
    model_ids = [
        'mdl-bytedance-seedream-4.5',
        'mdl-alibaba-z-image-turbo',
        'mdl-google-gemini-3.1-flash-image-preview',
        'mdl-google-gemini-2.5-pro',
        'mdl-openai-gpt-image-2',
        'mdl-openai-gpt-4o',
    ]
    for model_id in model_ids:
        connection.execute(
            sa.text("DELETE FROM model_catalog WHERE id = :id"),
            {'id': model_id}
        )

    # Delete providers
    provider_ids = [
        'prov-bytedance',
        'prov-alibaba',
        'prov-google',
        'prov-openai',
    ]
    for provider_id in provider_ids:
        connection.execute(
            sa.text("DELETE FROM model_providers WHERE id = :id"),
            {'id': provider_id}
        )

    print("Model catalog seed data removed successfully.")
