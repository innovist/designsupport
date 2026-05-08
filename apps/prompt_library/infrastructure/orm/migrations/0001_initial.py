"""Initial migration for prompt_library module.

Creates tables for prompt patterns and safety violations.
"""
from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PromptPatternModel',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4)),
                ('name', models.CharField(max_length=255, db_index=True)),
                (
                    'category',
                    models.CharField(
                        max_length=50,
                        choices=[
                            ('line_to_render', 'Line to Render'),
                            ('multi_reference_fusion', 'Multi-Reference Fusion'),
                            ('product_packaging', 'Product Packaging'),
                            ('material_texture', 'Material Texture'),
                            ('exploded_view', 'Exploded View'),
                            ('storyboard', 'Storyboard'),
                            ('moodboard_collage', 'Moodboard Collage'),
                            ('diagram_annotation', 'Diagram Annotation'),
                            ('domain_application', 'Domain Application'),
                            ('refinement_preserve_original', 'Refinement Preserve Original'),
                        ],
                        db_index=True,
                    ),
                ),
                ('source_reference', models.TextField()),
                ('input_slots', models.JSONField(default=list)),
                ('output_constraints', models.JSONField(default=list)),
                ('safety_rules', models.JSONField(default=list)),
                ('domain_tags', models.JSONField(default=list, db_index=True)),
                ('active', models.BooleanField(default=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'prompt_patterns',
                'indexes': [
                    models.Index(fields=['category', 'active'], name='prompt_lib_cat_active_idx'),
                    models.Index(fields=['domain_tags'], name='prompt_lib_tags_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='PromptSafetyViolationModel',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4)),
                ('session_id', models.UUIDField(db_index=True)),
                ('prompt_id', models.UUIDField(null=True, blank=True, db_index=True)),
                ('reason', models.TextField()),
                ('source_refs', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'db_table': 'prompt_safety_violations',
                'indexes': [
                    models.Index(fields=['session_id', 'created_at'], name='prompt_viol_session_idx'),
                    models.Index(fields=['prompt_id'], name='prompt_viol_prompt_idx'),
                ],
            },
        ),
    ]
