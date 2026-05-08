"""User asset domain entities.

Immutable sketch storage with versioning.
"""
from dataclasses import dataclass
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from enum import Enum


class SketchStatus(Enum):
    """Sketch processing status."""

    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class AnalysisStatus(Enum):
    """Sketch analysis status."""

    HYPOTHESIS = "hypothesis"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


@dataclass
class UserSketchAsset:
    """User sketch asset aggregate root.

    IMMUTABLE: original_uri and sha256 never change after creation.
    """

    id: UUID
    session_id: UUID
    uploader_id: UUID
    original_uri: str
    sha256: str
    mime_type: str
    size_bytes: int
    version: int
    parent_asset_id: Optional[UUID]
    created_at: datetime

    def __init__(
        self,
        session_id: UUID,
        uploader_id: UUID,
        original_uri: str,
        sha256: str,
        mime_type: str,
        size_bytes: int,
        version: int = 1,
        parent_asset_id: Optional[UUID] = None,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
    ):
        """Initialize a new user sketch asset.

        Args:
            session_id: Parent design session UUID
            uploader_id: User who uploaded the sketch
            original_uri: Immutable URI to original file
            sha256: Immutable SHA-256 hash
            mime_type: MIME type of file
            size_bytes: File size in bytes
            version: Version number for re-uploads
            parent_asset_id: Parent asset UUID for versioning
            id: Asset UUID
            created_at: Timestamp
        """
        self.id = id or uuid4()
        self.session_id = session_id
        self.uploader_id = uploader_id
        self.original_uri = original_uri
        self.sha256 = sha256
        self.mime_type = mime_type
        self.size_bytes = size_bytes
        self.version = version
        self.parent_asset_id = parent_asset_id
        self.created_at = created_at or _utcnow()

    def is_first_version(self) -> bool:
        """Check if this is the first version."""
        return self.parent_asset_id is None

    def create_new_version(self, new_uri: str, new_sha256: str) -> "UserSketchAsset":
        """Create a new version of this asset.

        Args:
            new_uri: URI to new file
            new_sha256: SHA-256 hash of new file

        Returns:
            New UserSketchAsset with incremented version
        """
        return UserSketchAsset(
            session_id=self.session_id,
            uploader_id=self.uploader_id,
            original_uri=new_uri,
            sha256=new_sha256,
            mime_type=self.mime_type,
            size_bytes=self.size_bytes,
            version=self.version + 1,
            parent_asset_id=self.id,
        )


@dataclass
class SketchAnalysis:
    """Sketch analysis entity.

    AI-generated hypothesis about sketch content.
    """

    id: UUID
    sketch_id: UUID
    intent: str
    form_notes: str
    structure_notes: str
    unclear_points: str
    keep_elements: str
    vary_elements: str
    status: str
    created_at: datetime

    def __init__(
        self,
        sketch_id: UUID,
        intent: str,
        form_notes: str,
        structure_notes: str,
        unclear_points: str = "",
        keep_elements: str = "",
        vary_elements: str = "",
        status: str = AnalysisStatus.HYPOTHESIS,
        id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
    ):
        """Initialize a new sketch analysis.

        Args:
            sketch_id: Parent sketch asset UUID
            intent: Design intent
            form_notes: Form and shape observations
            structure_notes: Structural observations
            unclear_points: Unclear elements
            keep_elements: Elements to preserve
            vary_elements: Elements to vary
            status: Analysis status (hypothesis/confirmed/rejected)
            id: Analysis UUID
            created_at: Timestamp
        """
        self.id = id or uuid4()
        self.sketch_id = sketch_id
        self.intent = intent
        self.form_notes = form_notes
        self.structure_notes = structure_notes
        self.unclear_points = unclear_points
        self.keep_elements = keep_elements
        self.vary_elements = vary_elements
        self.status = status
        self.created_at = created_at or _utcnow()

    def confirm(self) -> None:
        """Confirm the hypothesis analysis."""
        self.status = AnalysisStatus.CONFIRMED

    def reject(self) -> None:
        """Reject the hypothesis analysis."""
        self.status = AnalysisStatus.REJECTED

    def is_hypothesis(self) -> bool:
        """Check if analysis is still a hypothesis."""
        return self.status == AnalysisStatus.HYPOTHESIS
