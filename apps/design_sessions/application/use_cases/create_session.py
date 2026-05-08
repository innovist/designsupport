"""CreateSession use case.

REQ-01-SESSION-001: DesignProject, DesignSession, DesignBrief as separate aggregates.
REQ-01-SESSION-002: Initial status = queued; mode in {guided, auto}.
REQ-01-SESSION-003: Produce clarifying_questions when brief is incomplete.
"""
from uuid import UUID, uuid4

from apps.design_sessions.application.ports import (
    BriefRepositoryPort,
    DecisionLogRepositoryPort,
    SessionRepositoryPort,
)
from apps.design_sessions.domain.entities import (
    DecisionLog,
    DesignBrief,
    DesignSession,
    PipelineStep,
    SessionMode,
    SessionStatus,
)
from shared.application.decorators.audit import audit
from shared.domain.exceptions import ValidationError


_REQUIRED_BRIEF_FIELDS = ("purpose", "audience", "result_form")

# @MX:NOTE: [AUTO] Clarifying question templates for brief completeness validation
# @MX:REASON: Business rule - REQ-01-SESSION-003 requires questions for incomplete briefs
_CLARIFYING_QUESTIONS_TEMPLATES = {
    "purpose": "What is the primary purpose of this design?",
    "audience": "Who is the target audience for this design?",
    "result_form": "What is the expected output format (e.g., logo, UI mockup, illustration)?",
}


def _build_clarifying_questions(purpose: str, audience: str, result_form: str) -> list:
    """Return list of clarifying question dicts for empty required fields."""
    questions = []
    for field, value in [("purpose", purpose), ("audience", audience), ("result_form", result_form)]:
        if not value or not value.strip():
            questions.append({
                "field": field,
                "question": _CLARIFYING_QUESTIONS_TEMPLATES[field],
            })
    return questions


# @MX:ANCHOR: [AUTO] Session creation use case - REQ-01-SESSION-001,002,003
# @MX:REASON: High fan_in - called by SessionCreateAPIView, orchestrator, tests
@audit(
    "design_session.create",
    target_type_extractor=lambda **kw: "DesignSession",
    target_id_extractor=lambda **kw: "",
)
class CreateSessionUseCase:
    """Create a new DesignSession with DesignBrief.

    Validates brief completeness and generates clarifying_questions if incomplete.
    """

    def __init__(
        self,
        session_repository: SessionRepositoryPort,
        brief_repository: BriefRepositoryPort,
        decision_repository: DecisionLogRepositoryPort,
    ) -> None:
        self._session_repo = session_repository
        self._brief_repo = brief_repository
        self._decision_repo = decision_repository

    # @MX:ANCHOR: [AUTO] Session execution - creates session, brief, decision log
    # @MX:REASON: High fan_in - called by API view, test suites, retry flows
    async def execute(
        self,
        project_id: UUID,
        started_by: UUID,
        tenant_id: str,
        workspace_id: UUID,
        mode: str = "guided",
        purpose: str = "",
        audience: str = "",
        usage_context: str = "",
        constraints: str = "",
        result_form: str = "",
    ) -> DesignSession:
        """Create session and brief.

        Args:
            project_id: Parent project UUID
            started_by: User UUID
            tenant_id: Tenant ID
            workspace_id: Workspace UUID
            mode: "guided" or "auto"
            purpose: Design purpose
            audience: Target audience
            usage_context: Context of use
            constraints: Design constraints
            result_form: Expected output format

        Returns:
            Created DesignSession entity with brief attached as .brief attribute

        Raises:
            ValidationError: If mode is invalid
        """
        if mode not in {"guided", "auto"}:
            raise ValidationError(field="mode", message=f"Invalid mode: {mode}")

        session_mode = SessionMode(mode)

        # Build clarifying questions for incomplete brief
        clarifying_questions = _build_clarifying_questions(purpose, audience, result_form)

        session = DesignSession(
            project_id=project_id,
            started_by=started_by,
            mode=session_mode,
            status=SessionStatus.QUEUED,
            current_step=PipelineStep.PURPOSE_INPUT,
            version=1,
        )
        # Attach tenant/workspace — repos need these for persistence
        session.tenant_id = tenant_id  # type: ignore[attr-defined]
        session.workspace_id = workspace_id  # type: ignore[attr-defined]

        saved_session = await self._session_repo.save(session)

        brief = DesignBrief(
            session_id=saved_session.id,
            purpose=purpose,
            audience=audience,
            usage_context=usage_context,
            constraints=constraints,
            result_form=result_form,
            clarifying_questions=clarifying_questions,
            score=0.0,
        )
        saved_brief = await self._brief_repo.save(brief)

        # Record creation decision
        decision = DecisionLog(
            session_id=saved_session.id,
            step=PipelineStep.PURPOSE_INPUT,
            action="session_created",
            actor_kind="user",
            actor_id=started_by,
            rationale="Session created",
        )
        await self._decision_repo.save(decision)

        # Attach brief for caller convenience
        saved_session.brief = saved_brief  # type: ignore[attr-defined]
        return saved_session
