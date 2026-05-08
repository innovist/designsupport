# Generated manually for Task #3
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ConceptCandidateModel',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4)),
                ('session_id', models.UUIDField(db_index=True)),
                ('title', models.CharField(max_length=500)),
                ('description', models.TextField()),
                ('rationale', models.TextField()),
                ('rationale_refs', models.JSONField(default=list)),
                ('domain_tags', models.JSONField(default=list)),
                ('status', models.CharField(
                    max_length=20,
                    choices=[
                        ('draft', 'Draft'),
                        ('proposed', 'Proposed'),
                        ('adopted', 'Adopted'),
                        ('discarded', 'Discarded'),
                    ],
                    default='draft',
                )),
                ('score', models.FloatField(null=True, blank=True)),
                ('novelty', models.FloatField(null=True, blank=True)),
                ('fit_score', models.FloatField(null=True, blank=True)),
                ('created_by', models.UUIDField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'concept_candidates',
                'indexes': [
                    models.Index(fields=['session_id'], name='concept_cand_session_idx'),
                    models.Index(fields=['status'], name='concept_cand_status_idx'),
                    models.Index(fields=['created_at'], name='concept_cand_created_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='ConceptDecisionModel',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4)),
                ('concept_id', models.UUIDField(db_index=True)),
                ('decision', models.CharField(
                    max_length=20,
                    choices=[
                        ('adopt', 'Adopt'),
                        ('hold', 'Hold'),
                        ('discard', 'Discard'),
                        ('explore_more', 'Explore More'),
                    ],
                )),
                ('actor_kind', models.CharField(
                    max_length=10,
                    choices=[
                        ('user', 'User'),
                        ('auto', 'Auto'),
                    ],
                )),
                ('actor_id', models.UUIDField()),
                ('rationale', models.TextField()),
                ('evidence_refs', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'concept_decisions',
                'indexes': [
                    models.Index(fields=['concept_id'], name='concept_decision_concept_idx'),
                    models.Index(fields=['created_at'], name='concept_decision_created_idx'),
                ],
            },
        ),
    ]
