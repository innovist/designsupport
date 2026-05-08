"""Trend Knowledge repository implementations.

Django ORM implementations of repository ports.
"""
from apps.trend_knowledge.infrastructure.repositories.parsing_failure_repository import (
    DjangoParsingFailureQueueRepository,
)
from apps.trend_knowledge.infrastructure.repositories.trend_document_repository import (
    DjangoTrendDocumentRepository,
)
from apps.trend_knowledge.infrastructure.repositories.trend_insight_repository import (
    DjangoTrendInsightRepository,
)
from apps.trend_knowledge.infrastructure.repositories.trend_source_repository import (
    DjangoTrendSourceRepository,
)
from apps.trend_knowledge.infrastructure.repositories.trend_taxonomy_repository import (
    DjangoTrendTaxonomyRepository,
)

__all__ = [
    "DjangoTrendSourceRepository",
    "DjangoTrendDocumentRepository",
    "DjangoTrendInsightRepository",
    "DjangoTrendTaxonomyRepository",
    "DjangoParsingFailureQueueRepository",
]
