"""Workspace board API endpoints backed by persisted session data."""
import hashlib
from uuid import uuid4

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.response import Response

from apps.abstraction.infrastructure.orm.models import AbstractionRuleModel
from apps.concepts.infrastructure.orm.models import ConceptCandidateModel, ConceptDecisionModel
from apps.conversations.infrastructure.orm.models import ChatMessage, Conversation
from apps.design_sessions.infrastructure.orm.models import DecisionLog, DesignSession
from apps.generation.infrastructure.orm.models import GeneratedDesignModel, GenerationJobModel
from apps.references.infrastructure.orm.models import ReferenceAnalysis, ReferenceAsset
from apps.specs.infrastructure.orm.models import SpecDocumentModel
from apps.user_assets.infrastructure.orm.models import SketchAnalysis, UserSketchAsset
from shared.presentation.base_views import BaseAPIView


def _session_response_meta(session: DesignSession) -> dict:
    return {
        "current_step": session.current_step,
        "mode": session.mode,
        "evidence_refs": [],
        "is_hypothesis": False,
        "decision_required": session.decision_required,
        "next_actions": [],
    }


class SessionListAPIView(BaseAPIView):
    """List sessions for the current workspace or project."""

    def get(self, request):
        queryset = DesignSession.objects.all().order_by("-created_at")
        project_id = request.query_params.get("project_id")
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return Response([self._serialize(session) for session in queryset[:100]])

    def _serialize(self, session: DesignSession) -> dict:
        return {
            "id": str(session.id),
            "project_id": str(session.project_id),
            "status": session.status,
            "mode": session.mode,
            "current_step": session.current_step,
            "version": session.version,
            "progress_percent": round((session.current_step / 17) * 100, 2),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }


class SessionMessagesAPIView(BaseAPIView):
    """Read and append chat messages for a session."""

    def get(self, request, pk):
        session = self._get_session(pk)
        conversation = Conversation.objects.filter(session_id=session.id).first()
        if not conversation:
            return Response([])
        messages = ChatMessage.objects.filter(
            conversation_id=conversation.id,
        ).order_by("created_at")
        return Response([self._serialize_message(message) for message in messages])

    def post(self, request, pk):
        session = self._get_session(pk)
        content = (request.data.get("content") or "").strip()
        if not content:
            return Response({"detail": "content is required"}, status=status.HTTP_400_BAD_REQUEST)

        conversation, _ = Conversation.objects.get_or_create(
            session_id=session.id,
            defaults={"id": uuid4()},
        )
        message = ChatMessage.objects.create(
            id=uuid4(),
            conversation_id=conversation.id,
            role="user",
            content=content,
            evidence_refs=[],
            is_hypothesis=False,
        )
        return Response(self._serialize_message(message), status=status.HTTP_201_CREATED)

    def _get_session(self, pk):
        return DesignSession.objects.get(id=pk)

    def _serialize_message(self, message: ChatMessage) -> dict:
        return {
            "id": str(message.id),
            "role": message.role,
            "content": message.content,
            "evidence_refs": message.evidence_refs,
            "is_hypothesis": message.is_hypothesis,
            "created_at": message.created_at.isoformat(),
        }


class SessionSketchAPIView(BaseAPIView):
    """Latest sketch read and immutable upload endpoint."""

    def get(self, request, pk):
        session = DesignSession.objects.get(id=pk)
        sketch = UserSketchAsset.objects.filter(session_id=session.id).order_by("-version", "-created_at").first()
        if not sketch:
            if request.path.endswith("/interpretation"):
                return Response(None)
            return Response({"original": None, "interpretation": None})
        if request.path.endswith("/interpretation"):
            return Response(self._serialize_analysis(sketch.id))
        return Response({
            "original": self._serialize_sketch(sketch),
            "interpretation": self._serialize_analysis(sketch.id),
        })

    def post(self, request, pk):
        session = DesignSession.objects.get(id=pk)
        upload = request.FILES.get("file") or request.FILES.get("files")
        if not upload:
            return Response({"detail": "file is required"}, status=status.HTTP_400_BAD_REQUEST)

        data = upload.read()
        sha256 = hashlib.sha256(data).hexdigest()
        latest = UserSketchAsset.objects.filter(session_id=session.id).order_by("-version").first()
        version = (latest.version + 1) if latest else 1
        path = default_storage.save(
            f"sketches/{session.id}/{uuid4()}_{upload.name}",
            ContentFile(data),
        )
        sketch = UserSketchAsset.all_objects.create(
            id=uuid4(),
            tenant_id=request.tenant_id,
            workspace_id=request.workspace_id,
            session_id=session.id,
            uploader_id=request.current_user_id,
            original_uri=default_storage.url(path),
            sha256=sha256,
            mime_type=getattr(upload, "content_type", "") or "application/octet-stream",
            size_bytes=len(data),
            version=version,
            parent_asset_id=latest.id if latest else None,
        )
        return Response(self._serialize_sketch(sketch), status=status.HTTP_201_CREATED)

    def _serialize_sketch(self, sketch: UserSketchAsset) -> dict:
        return {
            "id": str(sketch.id),
            "url": sketch.original_uri,
            "mime_type": sketch.mime_type,
            "size_bytes": sketch.size_bytes,
            "version": sketch.version,
            "parent_asset_id": str(sketch.parent_asset_id) if sketch.parent_asset_id else None,
            "created_at": sketch.created_at.isoformat(),
        }

    def _serialize_analysis(self, sketch_id) -> dict | None:
        analysis = SketchAnalysis.objects.filter(sketch_id=sketch_id).first()
        if not analysis:
            return None
        return {
            "id": str(analysis.id),
            "intent": analysis.intent,
            "form": analysis.form_notes,
            "structure": analysis.structure_notes,
            "uncertain_elements": [analysis.unclear_points] if analysis.unclear_points else [],
            "questions": [],
            "is_hypothesis": analysis.status == "hypothesis",
        }


class SessionEvidenceAPIView(BaseAPIView):
    """Return evidence objects linked to the session."""

    def get(self, request, pk):
        session = DesignSession.objects.get(id=pk)
        references = ReferenceAsset.objects.filter(session_id=session.id).order_by("-collected_at")
        return Response({"insights": [self._serialize_reference(asset) for asset in references[:100]]})

    def _serialize_reference(self, asset: ReferenceAsset) -> dict:
        return {
            "id": str(asset.id),
            "source_url": asset.source_url or asset.external_url,
            "content": asset.relevance_reason or asset.title,
            "summary": asset.relevance_reason or asset.title,
            "publish_date": asset.published_at.isoformat() if asset.published_at else "",
            "credibility_score": 1.0 if asset.license_risk == "low" else 0.5,
            "tags": asset.domain_tags,
        }


class SessionReferencesAPIView(BaseAPIView):
    """Return session references and source clusters."""

    def get(self, request, pk):
        session = DesignSession.objects.get(id=pk)
        assets = list(ReferenceAsset.objects.filter(session_id=session.id).order_by("-collected_at")[:100])
        clusters = {}
        for asset in assets:
            clusters[asset.provider] = clusters.get(asset.provider, 0) + 1
        return Response({
            "clusters": [{"source": key, "count": value} for key, value in clusters.items()],
            "grid": [self._serialize_asset(asset) for asset in assets],
        })

    def _serialize_asset(self, asset: ReferenceAsset) -> dict:
        analysis = ReferenceAnalysis.objects.filter(asset_id=asset.id).first()
        return {
            "id": str(asset.id),
            "title": asset.title,
            "url": asset.source_url or asset.external_url or asset.thumbnail_uri,
            "thumbnail_url": asset.thumbnail_uri,
            "category": ", ".join(asset.domain_tags),
            "license": asset.license_id,
            "license_risk": asset.license_risk,
            "similarity_score": analysis.relevance if analysis else None,
        }


class SessionAbstractionRulesAPIView(BaseAPIView):
    """Return abstraction rules for the session."""

    def get(self, request, pk):
        session = DesignSession.objects.get(id=pk)
        rules = AbstractionRuleModel.objects.filter(session_id=session.id).order_by("-created_at")
        return Response([
            {
                "id": str(rule.id),
                "axis": rule.axis,
                "observation": rule.observation,
                "applied_rule": rule.applied_rule,
                "risk_level": "medium" if rule.risk_note else "low",
                "source_refs": rule.source_refs,
            }
            for rule in rules[:100]
        ])


class SessionGenerationsAPIView(BaseAPIView):
    """Return generated designs grouped by their persisted jobs."""

    def get(self, request, pk):
        session = DesignSession.objects.get(id=pk)
        jobs = {job.id: job for job in GenerationJobModel.objects.filter(session_id=session.id)}
        designs = GeneratedDesignModel.objects.filter(job_id__in=jobs.keys()).order_by("-created_at")
        return Response([self._serialize_design(design, jobs.get(design.job_id)) for design in designs[:100]])

    def post(self, request, pk):
        return Response({"detail": "generation execution must be started through /api/generation/jobs/"}, status=409)

    def _serialize_design(self, design: GeneratedDesignModel, job: GenerationJobModel | None) -> dict:
        return {
            "id": str(design.id),
            "job_id": str(design.job_id),
            "url": design.asset_uri,
            "kind": job.kind if job else "unknown",
            "model_policy_key": design.model_policy_key,
            "parent_sketch_id": str(design.parent_sketch_id) if design.parent_sketch_id else None,
            "prompt": str(design.prompt_id) if design.prompt_id else "",
            "created_at": design.created_at.isoformat(),
        }


class SessionConceptsAPIView(BaseAPIView):
    """Return or decide concept candidates."""

    def get(self, request, pk):
        session = DesignSession.objects.get(id=pk)
        candidates = ConceptCandidateModel.objects.filter(session_id=session.id).order_by("-created_at")
        return Response([self._serialize_candidate(candidate) for candidate in candidates[:100]])

    def post(self, request, pk, concept_id):
        session = DesignSession.objects.get(id=pk)
        candidate = ConceptCandidateModel.objects.get(id=concept_id, session_id=session.id)
        decision = request.data.get("decision")
        if decision not in {"adopt", "discard", "hold", "explore_more"}:
            return Response({"detail": "invalid decision"}, status=status.HTTP_400_BAD_REQUEST)

        ConceptDecisionModel.objects.create(
            id=uuid4(),
            concept_id=candidate.id,
            decision=decision,
            actor_kind="user",
            actor_id=request.current_user_id,
            rationale=request.data.get("rationale", ""),
            evidence_refs=request.data.get("evidence_refs", []),
        )
        if decision == "adopt":
            candidate.status = "adopted"
        elif decision == "discard":
            candidate.status = "discarded"
        else:
            candidate.status = "proposed"
        candidate.save(update_fields=["status", "updated_at"])
        return Response(self._serialize_candidate(candidate))

    def _serialize_candidate(self, candidate: ConceptCandidateModel) -> dict:
        return {
            "id": str(candidate.id),
            "title": candidate.title,
            "description": candidate.description,
            "status": candidate.status,
            "scores": {
                "creativity": candidate.novelty or 0,
                "feasibility": candidate.fit_score or 0,
                "market_fit": candidate.score or 0,
            },
            "rationale": candidate.rationale,
            "risks": candidate.risks,
            "domain_tags": candidate.domain_tags,
            "thumbnail_url": None,
            "url": None,
        }


class SessionSpecAPIView(BaseAPIView):
    """Return latest spec document for a session."""

    def get(self, request, pk):
        session = DesignSession.objects.get(id=pk)
        spec = SpecDocumentModel.objects.filter(session_id=session.id).order_by("-version").first()
        if not spec:
            return Response(None)
        return Response({
            "id": str(spec.id),
            "domain": spec.domain,
            "version": spec.version,
            "status": spec.status,
            "sections": spec.sections,
            "evidence_links": spec.evidence_links,
            "created_at": spec.created_at.isoformat(),
            "updated_at": spec.updated_at.isoformat(),
        })

    def post(self, request, pk, section_id):
        return Response({"detail": "section memo persistence is not configured"}, status=409)
