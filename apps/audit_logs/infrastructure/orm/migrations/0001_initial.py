"""Initial migration for audit_logs app."""
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("actor_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("tenant_id", models.CharField(db_index=True, max_length=255)),
                ("workspace_id", models.UUIDField(blank=True, db_index=True, null=True)),
                (
                    "action_type",
                    models.CharField(
                        db_index=True,
                        max_length=100,
                    ),
                ),
                ("target_type", models.CharField(max_length=100)),
                ("target_id", models.CharField(max_length=255)),
                ("payload_digest", models.CharField(max_length=64)),
            ],
            options={
                "verbose_name": "Audit Log",
                "verbose_name_plural": "Audit Logs",
                "db_table": "audit_logs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["tenant_id", "created_at"],
                name="audit_logs_tenant_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["actor_id", "action_type"],
                name="audit_logs_actor_action_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["workspace_id", "created_at"],
                name="audit_logs_workspace_created_idx",
            ),
        ),
    ]
