"""Initial migration for design_sessions app."""
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DesignSession",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("tenant_id", models.CharField(db_index=True, max_length=255)),
                ("workspace_id", models.UUIDField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("project_id", models.UUIDField(db_index=True)),
                (
                    "mode",
                    models.CharField(
                        choices=[("guided", "Guided"), ("auto", "Auto")],
                        default="guided",
                        max_length=10,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("queued", "Queued"),
                            ("researching", "Researching"),
                            ("concepting", "Concepting"),
                            ("referencing", "Referencing"),
                            ("abstracting", "Abstracting"),
                            ("generating", "Generating"),
                            ("documenting", "Documenting"),
                            ("review_ready", "Review Ready"),
                            ("failed", "Failed"),
                        ],
                        db_index=True,
                        default="queued",
                        max_length=20,
                    ),
                ),
                ("current_step", models.IntegerField(default=1)),
                ("version", models.IntegerField(default=1)),
                ("decision_required", models.BooleanField(default=False)),
                ("started_by", models.UUIDField()),
            ],
            options={
                "verbose_name": "Design Session",
                "verbose_name_plural": "Design Sessions",
                "db_table": "design_sessions",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="DesignBrief",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("session_id", models.UUIDField(db_index=True, unique=True)),
                ("purpose", models.TextField()),
                ("audience", models.TextField()),
                ("usage_context", models.TextField()),
                ("constraints", models.TextField()),
                ("result_form", models.TextField()),
                ("clarifying_questions", models.JSONField(default=list)),
                ("score", models.FloatField(default=0.0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Design Brief",
                "verbose_name_plural": "Design Briefes",
                "db_table": "design_briefs",
            },
        ),
        migrations.CreateModel(
            name="DecisionLog",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("session_id", models.UUIDField(db_index=True)),
                ("step", models.IntegerField()),
                ("action", models.CharField(max_length=255)),
                (
                    "actor_kind",
                    models.CharField(
                        choices=[("user", "User"), ("auto", "Auto")],
                        max_length=10,
                    ),
                ),
                ("actor_id", models.UUIDField()),
                ("rationale", models.TextField()),
                ("evidence_refs", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "verbose_name": "Decision Log",
                "verbose_name_plural": "Decision Logs",
                "db_table": "decision_logs",
            },
        ),
        migrations.AddIndex(
            model_name="designsession",
            index=models.Index(
                fields=["project_id", "status"],
                name="design_sessions_proj_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="designsession",
            index=models.Index(
                fields=["tenant_id", "workspace_id", "status"],
                name="design_sessions_tenant_ws_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="designsession",
            index=models.Index(
                fields=["started_by"],
                name="design_sessions_started_by_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="designsession",
            index=models.Index(
                fields=["tenant_id", "workspace_id"],
                name="design_sessions_tenant_ws_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="decisionlog",
            index=models.Index(
                fields=["session_id", "created_at"],
                name="decision_logs_session_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="decisionlog",
            index=models.Index(
                fields=["actor_id", "created_at"],
                name="decision_logs_actor_created_idx",
            ),
        ),
    ]
