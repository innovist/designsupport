"""Design session Django ORM models.

Implements session orchestration with state machine.
"""
from django.db import models
from django.core.exceptions import ValidationError
from shared.infrastructure.orm.base_model import TimestampedModel, TenantScopedModel


class DesignSessionManager(models.Manager):
    """Manager for design session queries."""

    def for_project(self, project_id):
        """Filter sessions by project."""
        return self.filter(project_id=project_id)

    def active(self):
        """Get active (non-deleted) sessions."""
        return self.filter(status__in=["queued", "researching", "concepting", "referencing",
                                       "abstracting", "generating", "documenting", "review_ready"])

    def failed(self):
        """Get failed sessions."""
        return self.filter(status="failed")


class DesignSession(TenantScopedModel, TimestampedModel):
    """Design session model with state machine.

    Orchestrates the 17-step design creation pipeline.
    """

    id = models.UUIDField(primary_key=True)
    project_id = models.UUIDField(db_index=True)
    mode = models.CharField(
        max_length=10,
        choices=[("guided", "Guided"), ("auto", "Auto")],
        default="guided",
    )
    status = models.CharField(
        max_length=20,
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
        default="queued",
        db_index=True,
    )
    current_step = models.IntegerField(default=1)  # 1-17 pipeline steps
    version = models.IntegerField(default=1)
    decision_required = models.BooleanField(default=False)  # INV-01-07: decision gate flag
    started_by = models.UUIDField()

    objects = DesignSessionManager()
    all_objects = models.Manager()  # Unfiltered escape hatch for repository use

    class Meta:
        db_table = "design_sessions"
        verbose_name = "Design Session"
        verbose_name_plural = "Design Sessions"
        indexes = [
            models.Index(fields=["project_id", "status"]),
            models.Index(fields=["tenant_id", "workspace_id", "status"]),
            models.Index(fields=["started_by"]),
        ]

    def __str__(self) -> str:
        return f"Session {self.id} ({self.status})"

    def clean(self):
        """Validate status transitions."""
        if self.pk:
            old_instance = DesignSession.objects.get(pk=self.pk)
            old_status = old_instance.status
            new_status = self.status

            # Import state machine for validation
            from apps.design_sessions.domain.services import SessionStateMachine
            from apps.design_sessions.domain.value_objects import SessionStatus

            try:
                old_status_enum = SessionStatus(old_status)
                new_status_enum = SessionStatus(new_status)
                SessionStateMachine.validate_transition(old_status_enum, new_status_enum)
            except ValueError as e:
                raise ValidationError({"status": str(e)})


class DesignBrief(models.Model):
    """Design brief model.

    Contains structured design requirements for a session.
    """

    id = models.UUIDField(primary_key=True)
    session_id = models.UUIDField(unique=True, db_index=True)
    purpose = models.TextField()
    audience = models.TextField()
    usage_context = models.TextField()
    constraints = models.TextField()
    result_form = models.TextField()
    clarifying_questions = models.JSONField(default=list)
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "design_briefs"
        verbose_name = "Design Brief"
        verbose_name_plural = "Design Briefes"

    def __str__(self) -> str:
        return f"Brief for session {self.session_id}"


class DecisionLogManager(models.Manager):
    """Manager for decision log queries."""

    def for_session(self, session_id):
        """Filter decisions by session."""
        return self.filter(session_id=session_id).order_by("created_at")

    def by_actor(self, actor_id):
        """Filter decisions by actor."""
        return self.filter(actor_id=actor_id)


class DecisionLog(models.Model):
    """Decision log model.

    Records all decisions made during session execution.
    """

    id = models.UUIDField(primary_key=True)
    session_id = models.UUIDField(db_index=True)
    step = models.IntegerField()  # 1-17 pipeline step
    action = models.CharField(max_length=255)
    actor_kind = models.CharField(max_length=10, choices=[("user", "User"), ("auto", "Auto")])
    actor_id = models.UUIDField()
    rationale = models.TextField()
    evidence_refs = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = DecisionLogManager()

    class Meta:
        db_table = "decision_logs"
        verbose_name = "Decision Log"
        verbose_name_plural = "Decision Logs"
        indexes = [
            models.Index(fields=["session_id", "created_at"]),
            models.Index(fields=["actor_id", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.actor_kind} decision at step {self.step}: {self.action}"
