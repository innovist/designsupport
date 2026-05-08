"""Django ORM models for prompt library.

Maps domain entities to database tables using Django ORM.
"""
from django.db import models

from apps.prompt_library.domain import PromptPattern, PromptSafetyViolation
from apps.abstraction.domain.value_objects import PromptCategory


class PromptPatternModel(models.Model):
    """Django ORM model for PromptPattern entity.

    REQ-03-PROMPT-001: Prompt pattern library with safety validation.
    """

    # Primary key
    id = models.UUIDField(primary_key=True)

    # Pattern metadata
    name = models.CharField(max_length=255, db_index=True)
    category = models.CharField(
        max_length=50,
        choices=[(c.value, c.value) for c in PromptCategory],
        db_index=True,
    )
    source_reference = models.TextField()

    # Pattern structure
    input_slots = models.JSONField(default=list)
    output_constraints = models.JSONField(default=list)
    safety_rules = models.JSONField(default=list)
    domain_tags = models.JSONField(default=list, db_index=True)

    # Status
    active = models.BooleanField(default=True, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'prompt_library'
        db_table = 'prompt_patterns'
        indexes = [
            models.Index(fields=['category', 'active']),
            models.Index(fields=['domain_tags']),
        ]

    def to_domain(self) -> PromptPattern:
        """Convert ORM model to domain entity.

        Returns:
            PromptPattern domain entity
        """
        from apps.abstraction.domain.value_objects import PromptCategory

        return PromptPattern(
            id=self.id,
            name=self.name,
            category=PromptCategory(self.category),
            source_reference=self.source_reference,
            input_slots=self.input_slots,
            output_constraints=self.output_constraints,
            safety_rules=self.safety_rules,
            domain_tags=self.domain_tags,
            active=self.active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, pattern: PromptPattern) -> 'PromptPatternModel':
        """Create ORM model from domain entity.

        Args:
            pattern: PromptPattern domain entity

        Returns:
            PromptPatternModel instance
        """
        return cls(
            id=pattern.id,
            name=pattern.name,
            category=pattern.category.value,
            source_reference=pattern.source_reference,
            input_slots=pattern.input_slots,
            output_constraints=pattern.output_constraints,
            safety_rules=pattern.safety_rules,
            domain_tags=pattern.domain_tags,
            active=pattern.active,
            created_at=pattern.created_at,
            updated_at=pattern.updated_at,
        )


class PromptSafetyViolationModel(models.Model):
    """Django ORM model for PromptSafetyViolation entity.

    REQ-03-PROMPT-006: Record safety violations for auditing.
    """

    # Primary key
    id = models.UUIDField(primary_key=True)

    # References
    session_id = models.UUIDField(db_index=True)
    prompt_id = models.UUIDField(null=True, blank=True, db_index=True)

    # Violation details
    reason = models.TextField()
    source_refs = models.JSONField(default=list)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        app_label = 'prompt_library'
        db_table = 'prompt_safety_violations'
        indexes = [
            models.Index(fields=['session_id', 'created_at']),
            models.Index(fields=['prompt_id']),
        ]

    def to_domain(self) -> PromptSafetyViolation:
        """Convert ORM model to domain entity.

        Returns:
            PromptSafetyViolation domain entity
        """
        from uuid import UUID

        return PromptSafetyViolation(
            id=self.id,
            session_id=UUID(str(self.session_id)),
            prompt_id=UUID(str(self.prompt_id)) if self.prompt_id else None,
            reason=self.reason,
            source_refs=[UUID(str(ref)) for ref in self.source_refs],
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, violation: PromptSafetyViolation) -> 'PromptSafetyViolationModel':
        """Create ORM model from domain entity.

        Args:
            violation: PromptSafetyViolation domain entity

        Returns:
            PromptSafetyViolationModel instance
        """
        return cls(
            id=violation.id,
            session_id=violation.session_id,
            prompt_id=violation.prompt_id,
            reason=violation.reason,
            source_refs=violation.source_refs,
            created_at=violation.created_at,
        )
