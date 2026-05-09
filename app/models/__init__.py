"""
ORM models package. Import all models here so Alembic can discover them.
"""

from app.models.base import Base, TimestampMixin  # noqa: F401
from app.models.workspace import Workspace, WorkspaceSetting, FeatureModelSetting, WorkspaceTrendSetting  # noqa: F401
from app.models.project import DesignProject  # noqa: F401
from app.models.session import DesignSession, DesignBrief, ChatMessage  # noqa: F401
from app.models.assets import UserSketchAsset, SketchAnalysis  # noqa: F401
from app.models.concepts import ConceptCandidate, ConceptDecision  # noqa: F401
from app.models.references import ReferenceAsset, ReferenceAnalysis  # noqa: F401
from app.models.abstraction import AbstractionRule  # noqa: F401
from app.models.generation import GeneratedDesign, DesignEvaluation  # noqa: F401
from app.models.specs import SpecDocument  # noqa: F401
from app.models.trends import TrendSource, TrendDocument, TrendInsight  # noqa: F401
