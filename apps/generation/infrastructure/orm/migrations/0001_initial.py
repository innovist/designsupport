"""Initial migration for generation module.

Generated for SPEC-03-CREATION implementation.
"""
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="GenerationJobModel",
            fields=[
                ("id", models.UUIDField(primary_key=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("session_id", models.UUIDField(db_index=True)),
                (
                    "kind",
                    models.CharField(
                        max_length=30,
                        choices=[
                            ("sketch", "Sketch"),
                            ("refinement", "Refinement"),
                            ("variation", "Variation"),
                            ("domain_application", "Domain Application"),
                        ],
                        db_index=True,
                    ),
                ),
                ("prompt_id", models.UUIDField(db_index=True, null=True, blank=True)),
                ("brief_id", models.UUIDField(db_index=True, null=True, blank=True)),
                ("concept_id", models.UUIDField(db_index=True, null=True, blank=True)),
                ("rule_ids", models.JSONField(default=list)),
                ("sketch_id", models.UUIDField(db_index=True, null=True, blank=True)),
                ("reference_ids", models.JSONField(default=list)),
                (
                    "status",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("queued", "Queued"),
                            ("running", "Running"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="queued",
                        db_index=True,
                    ),
                ),
                ("model_policy_key", models.CharField(max_length=100)),
                ("retries", models.IntegerField(default=0)),
                ("cost_meta", models.JSONField(null=True, blank=True)),
                ("error_message", models.TextField(null=True, blank=True)),
                ("completed_at", models.DateTimeField(db_index=True, null=True, blank=True)),
            ],
            options={
                "db_table": "generation_jobs",
                "indexes": [
                    models.Index(fields=["session_id", "-created_at"], name="gen_job_sess_idx"),
                    models.Index(fields=["status", "-created_at"], name="gen_job_status_idx"),
                    models.Index(fields=["kind", "-created_at"], name="gen_job_kind_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="GeneratedDesignModel",
            fields=[
                ("id", models.UUIDField(primary_key=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("job_id", models.UUIDField(db_index=True)),
                ("asset_uri", models.TextField()),
                (
                    "asset_kind",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("image", "Image"),
                            ("thumbnail", "Thumbnail"),
                            ("annotated", "Annotated"),
                            ("composite", "Composite"),
                        ],
                        default="image",
                    ),
                ),
                ("parent_sketch_id", models.UUIDField(db_index=True, null=True, blank=True)),
                ("brief_id", models.UUIDField(db_index=True, null=True, blank=True)),
                ("concept_id", models.UUIDField(db_index=True, null=True, blank=True)),
                ("rule_ids", models.JSONField(default=list)),
                ("reference_ids", models.JSONField(default=list)),
                ("model_policy_key", models.CharField(max_length=100)),
                ("prompt_id", models.UUIDField(db_index=True, null=True, blank=True)),
            ],
            options={
                "db_table": "generated_designs",
                "indexes": [
                    models.Index(fields=["job_id"], name="gen_des_job_idx"),
                    models.Index(fields=["created_at"], name="gen_des_created_idx"),
                ],
            },
        ),
    ]
