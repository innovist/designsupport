"""Generated migration for abstraction module.

This migration creates the initial database tables for the abstraction module.
"""
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AbstractionRuleModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        serialize=False,
                        default=uuid.uuid4,
                        editable=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "session_id",
                    models.UUIDField(db_index=True),
                ),
                (
                    "concept_id",
                    models.UUIDField(db_index=True),
                ),
                (
                    "axis",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("form", "Form"),
                            ("structure", "Structure"),
                            ("surface", "Surface"),
                            ("color_material", "Color Material"),
                            ("meaning", "Meaning"),
                            ("usability", "Usability"),
                        ],
                    ),
                ),
                ("observation", models.TextField()),
                ("applied_rule", models.TextField()),
                ("source_refs", models.JSONField(default=list)),
                ("risk_note", models.TextField(null=True, blank=True)),
            ],
            options={
                "db_table": "abstraction_rules",
                "indexes": [
                    models.Index(fields=["session_id"], name="abstr_sess_idx"),
                    models.Index(fields=["concept_id"], name="abstr_conc_idx"),
                    models.Index(fields=["axis"], name="abstr_axis_idx"),
                    models.Index(fields=["-created_at"], name="abstr_created_idx"),
                ],
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="SketchPromptModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        serialize=False,
                        default=uuid.uuid4,
                        editable=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "session_id",
                    models.UUIDField(db_index=True),
                ),
                (
                    "kind",
                    models.CharField(
                        max_length=30,
                        choices=[
                            ("preserve_original", "Preserve Original"),
                            ("expand_concept", "Expand Concept"),
                        ],
                    ),
                ),
                ("template", models.TextField()),
                ("variables", models.JSONField(default=dict)),
                ("source_refs", models.JSONField(default=list)),
            ],
            options={
                "db_table": "sketch_prompts",
                "indexes": [
                    models.Index(fields=["session_id"], name="sketch_sess_idx"),
                    models.Index(fields=["kind"], name="sketch_kind_idx"),
                    models.Index(fields=["-created_at"], name="sketch_created_idx"),
                ],
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PromptPatternModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        serialize=False,
                        default=uuid.uuid4,
                        editable=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255, unique=True)),
                (
                    "category",
                    models.CharField(
                        max_length=50,
                        choices=[
                            ("line_to_render", "Line to Render"),
                            ("multi_reference_fusion", "Multi Reference Fusion"),
                            ("product_packaging", "Product Packaging"),
                            ("material_texture", "Material Texture"),
                            ("exploded_view", "Exploded View"),
                            ("storyboard", "Storyboard"),
                            ("moodboard_collage", "Moodboard Collage"),
                            ("diagram_annotation", "Diagram Annotation"),
                            ("domain_application", "Domain Application"),
                            ("refinement_preserve_original", "Refinement Preserve Original"),
                        ],
                    ),
                ),
                ("source_reference", models.TextField()),
                ("input_slots", models.JSONField(default=list)),
                ("output_constraints", models.JSONField(default=list)),
                ("safety_rules", models.JSONField(default=list)),
                ("domain_tags", models.JSONField(default=list)),
                ("active", models.BooleanField(default=True)),
            ],
            options={
                "db_table": "prompt_patterns",
                "indexes": [
                    models.Index(fields=["category"], name="pattern_cat_idx"),
                    models.Index(fields=["active"], name="pattern_active_idx"),
                    models.Index(fields=["-created_at"], name="pattern_created_idx"),
                ],
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PromptSafetyViolationModel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        serialize=False,
                        default=uuid.uuid4,
                        editable=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "session_id",
                    models.UUIDField(db_index=True),
                ),
                (
                    "prompt_id",
                    models.UUIDField(null=True, blank=True, db_index=True),
                ),
                ("reason", models.TextField()),
                ("source_refs", models.JSONField(default=list)),
            ],
            options={
                "db_table": "prompt_safety_violations",
                "indexes": [
                    models.Index(fields=["session_id"], name="violation_sess_idx"),
                    models.Index(fields=["prompt_id"], name="violation_prompt_idx"),
                    models.Index(fields=["-created_at"], name="violation_created_idx"),
                ],
                "ordering": ["-created_at"],
            },
        ),
    ]
