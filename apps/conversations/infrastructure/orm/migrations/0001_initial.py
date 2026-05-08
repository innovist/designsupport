"""Initial migration for conversations app.

INV-01-03: ChatMessage.check constraint enforces AI messages have evidence_refs
or is_hypothesis=True. The Django model uses a Q()-based placeholder; this
migration overrides the constraint SQL with the actual PostgreSQL expression
using jsonb_array_length().
"""
from django.db import migrations, models


def add_ai_evidence_constraint(apps, schema_editor):
    """Add PostgreSQL-only JSON evidence constraint for AI messages."""
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(
        """
        ALTER TABLE chat_messages
        ADD CONSTRAINT chat_message_ai_evidence_or_hypothesis
        CHECK (
            role = 'user'
            OR is_hypothesis = TRUE
            OR jsonb_array_length(evidence_refs) > 0
        );
        """
    )


def drop_ai_evidence_constraint(apps, schema_editor):
    """Drop PostgreSQL-only JSON evidence constraint for AI messages."""
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(
        """
        ALTER TABLE chat_messages
        DROP CONSTRAINT IF EXISTS chat_message_ai_evidence_or_hypothesis;
        """
    )


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("session_id", models.UUIDField(db_index=True, unique=True)),
            ],
            options={
                "verbose_name": "Conversation",
                "verbose_name_plural": "Conversations",
                "db_table": "conversations",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("conversation_id", models.UUIDField(db_index=True)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("user", "User"),
                            ("assistant", "Assistant"),
                            ("system", "System"),
                        ],
                        max_length=10,
                    ),
                ),
                ("content", models.TextField()),
                ("evidence_refs", models.JSONField(default=list)),
                ("is_hypothesis", models.BooleanField(default=False)),
            ],
            options={
                "verbose_name": "Chat Message",
                "verbose_name_plural": "Chat Messages",
                "db_table": "chat_messages",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="chatmessage",
            index=models.Index(
                fields=["conversation_id", "created_at"],
                name="chat_messages_conv_created_idx",
            ),
        ),
        # INV-01-03 DB constraint: AI messages must have evidence_refs or is_hypothesis=True.
        # Uses raw SQL to leverage PostgreSQL jsonb_array_length() function.
        # Constraint: role = 'user' OR is_hypothesis = TRUE OR jsonb_array_length(evidence_refs) > 0
        migrations.RunPython(
            add_ai_evidence_constraint,
            reverse_code=drop_ai_evidence_constraint,
        ),
    ]
