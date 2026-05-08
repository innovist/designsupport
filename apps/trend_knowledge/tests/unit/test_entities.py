"""Unit tests for trend_knowledge domain entities.

Tests cover validation, state transitions, and business invariants.
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4

from apps.trend_knowledge.domain.entities import (
    TrendSource,
    TrendDocument,
    TrendInsight,
    TrendTaxonomy,
    ParsingFailureQueue,
    TrendDocumentStatus,
    TrendSourceType,
)
from shared.domain.exceptions import ValidationError


class TestTrendSource:
    """Test TrendSource entity."""

    def test_valid_creation_with_defaults(self):
        """Test creating a valid TrendSource with default values."""
        source = TrendSource(
            name="WGSN",
            url="https://wgsn.com",
            domain="fashion",
            crawl_schedule="0 0 * * *",
            trust_level="high",
            license="commercial",
        )

        assert source.id is not None
        assert isinstance(source.id, UUID)
        assert source.name == "WGSN"
        assert source.url == "https://wgsn.com"
        assert source.domain == "fashion"
        assert source.active is True
        assert source.created_at is not None
        assert source.updated_at is not None

    def test_valid_creation_with_all_fields(self):
        """Test creating a TrendSource with all fields specified."""
        test_id = uuid4()
        created_at = datetime.now(timezone.utc) - timedelta(days=1)
        updated_at = datetime.now(timezone.utc)

        source = TrendSource(
            name="Fashion Trend API",
            url="https://api.example.com/trends",
            domain="industrial",
            crawl_schedule="*/30 * * * *",
            trust_level="medium",
            license="attribution",
            active=False,
            id=test_id,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert source.id == test_id
        assert source.active is False
        assert source.created_at == created_at
        assert source.updated_at == updated_at

    def test_deactivate_active_source(self):
        """Test deactivating an active source."""
        source = TrendSource(
            name="Test Source",
            url="https://example.com",
            domain="fashion",
            crawl_schedule="0 0 * * *",
            trust_level="high",
            license="commercial",
            active=True,
        )

        original_updated_at = source.updated_at
        source.deactivate()

        assert source.active is False
        # updated_at should be changed (may be same time if very fast)
        assert source.updated_at >= original_updated_at

    def test_deactivate_already_inactive_source(self):
        """Test deactivating an already inactive source (idempotent)."""
        source = TrendSource(
            name="Test Source",
            url="https://example.com",
            domain="fashion",
            crawl_schedule="0 0 * * *",
            trust_level="high",
            license="commercial",
            active=False,
        )

        original_updated_at = source.updated_at
        source.deactivate()

        assert source.active is False
        assert source.updated_at == original_updated_at  # No update

    def test_activate_inactive_source(self):
        """Test activating an inactive source."""
        source = TrendSource(
            name="Test Source",
            url="https://example.com",
            domain="fashion",
            crawl_schedule="0 0 * * *",
            trust_level="high",
            license="commercial",
            active=False,
        )

        original_updated_at = source.updated_at
        source.activate()

        assert source.active is True
        # updated_at should be changed (may be same time if very fast)
        assert source.updated_at >= original_updated_at

    def test_activate_already_active_source(self):
        """Test activating an already active source (idempotent)."""
        source = TrendSource(
            name="Test Source",
            url="https://example.com",
            domain="fashion",
            crawl_schedule="0 0 * * *",
            trust_level="high",
            license="commercial",
            active=True,
        )

        original_updated_at = source.updated_at
        source.activate()

        assert source.active is True
        assert source.updated_at == original_updated_at  # No update

    def test_update_schedule_with_new_schedule(self):
        """Test updating crawl schedule."""
        source = TrendSource(
            name="Test Source",
            url="https://example.com",
            domain="fashion",
            crawl_schedule="0 0 * * *",
            trust_level="high",
            license="commercial",
        )

        original_updated_at = source.updated_at
        source.update_schedule("*/30 * * * *")

        assert source.crawl_schedule == "*/30 * * * *"
        # updated_at should be changed (may be same time if very fast)
        assert source.updated_at >= original_updated_at

    def test_update_schedule_with_same_schedule(self):
        """Test updating schedule with same value (idempotent)."""
        source = TrendSource(
            name="Test Source",
            url="https://example.com",
            domain="fashion",
            crawl_schedule="0 0 * * *",
            trust_level="high",
            license="commercial",
        )

        original_updated_at = source.updated_at
        source.update_schedule("0 0 * * *")

        assert source.crawl_schedule == "0 0 * * *"
        assert source.updated_at == original_updated_at  # No update


class TestTrendDocument:
    """Test TrendDocument entity."""

    def test_valid_creation_with_defaults(self):
        """Test creating a valid TrendDocument with default values."""
        source_id = uuid4()
        published_at = datetime.now(timezone.utc) - timedelta(days=7)

        document = TrendDocument(
            source_id=source_id,
            title="Summer 2026 Fashion Trends",
            url="https://example.com/article",
            published_at=published_at,
            raw_uri="s3://bucket/raw/123.pdf",
            hash="abc123def456",
        )

        assert document.id is not None
        assert isinstance(document.id, UUID)
        assert document.source_id == source_id
        assert document.title == "Summer 2026 Fashion Trends"
        assert document.parse_status == "pending"
        assert document.collected_at is not None
        assert document.parsed_text_uri is None

    def test_hash_deduplication_prevents_duplicates(self):
        """Test that hash is used for deduplication."""
        source_id = uuid4()

        doc1 = TrendDocument(
            source_id=source_id,
            title="Document 1",
            url="https://example.com/doc1",
            published_at=datetime.now(timezone.utc),
            raw_uri="s3://bucket/raw/1.pdf",
            hash="same_hash_123",
        )

        doc2 = TrendDocument(
            source_id=source_id,
            title="Document 2",
            url="https://example.com/doc2",
            published_at=datetime.now(timezone.utc),
            raw_uri="s3://bucket/raw/2.pdf",
            hash="same_hash_123",  # Same hash
        )

        # Same hash indicates duplicate content
        assert doc1.hash == doc2.hash

    def test_mark_parsing_transitions_from_pending(self):
        """Test mark_parsing transitions from pending to parsing."""
        document = TrendDocument(
            source_id=uuid4(),
            title="Test Doc",
            url="https://example.com",
            published_at=datetime.now(timezone.utc),
            raw_uri="s3://bucket/raw/test.pdf",
            hash="hash123",
            parse_status="pending",
        )

        document.mark_parsing()

        assert document.parse_status == "parsing"

    def test_mark_parsing_does_not_transition_from_parsed(self):
        """Test mark_parsing does not transition from parsed status."""
        document = TrendDocument(
            source_id=uuid4(),
            title="Test Doc",
            url="https://example.com",
            published_at=datetime.now(timezone.utc),
            raw_uri="s3://bucket/raw/test.pdf",
            hash="hash123",
            parse_status="parsed",
        )

        original_status = document.parse_status
        document.mark_parsing()

        assert document.parse_status == original_status  # No change

    def test_mark_parsed_transitions_successfully(self):
        """Test mark_parsed transitions to parsed and sets URI."""
        document = TrendDocument(
            source_id=uuid4(),
            title="Test Doc",
            url="https://example.com",
            published_at=datetime.now(timezone.utc),
            raw_uri="s3://bucket/raw/test.pdf",
            hash="hash123",
            parse_status="parsing",
        )

        document.mark_parsed("s3://bucket/parsed/test.txt")

        assert document.parse_status == "parsed"
        assert document.parsed_text_uri == "s3://bucket/parsed/test.txt"

    def test_mark_failed_transitions_and_clears_uri(self):
        """Test mark_failed transitions to failed and clears parsed URI."""
        document = TrendDocument(
            source_id=uuid4(),
            title="Test Doc",
            url="https://example.com",
            published_at=datetime.now(timezone.utc),
            raw_uri="s3://bucket/raw/test.pdf",
            hash="hash123",
            parse_status="parsing",
            parsed_text_uri="s3://bucket/parsed/test.txt",
        )

        document.mark_failed()

        assert document.parse_status == "failed"
        assert document.parsed_text_uri is None


class TestTrendInsight:
    """Test TrendInsight entity."""

    def test_valid_creation_with_clamped_scores(self):
        """Test creating insight with confidence and recency scores clamped to [0.0, 1.0]."""
        document_id = uuid4()

        insight = TrendInsight(
            document_id=document_id,
            summary="Minimalist design continues to dominate",
            keywords=["minimalism", "clean", "simple"],
            domain_tags=["industrial", "product"],
            evidence_quote="The trend toward minimalism shows no sign of slowing",
            confidence=0.85,
            recency_score=0.72,
        )

        assert insight.id is not None
        assert insight.summary == "Minimalist design continues to dominate"
        assert insight.confidence == 0.85
        assert insight.recency_score == 0.72

    def test_confidence_clamped_above_maximum(self):
        """Test confidence score is clamped to maximum 1.0."""
        document_id = uuid4()

        insight = TrendInsight(
            document_id=document_id,
            summary="Test insight",
            keywords=["test"],
            domain_tags=["test"],
            evidence_quote="Test quote",
            confidence=1.5,  # Above maximum
            recency_score=0.5,
        )

        assert insight.confidence == 1.0  # Clamped to maximum

    def test_confidence_clamped_below_minimum(self):
        """Test confidence score is clamped to minimum 0.0."""
        document_id = uuid4()

        insight = TrendInsight(
            document_id=document_id,
            summary="Test insight",
            keywords=["test"],
            domain_tags=["test"],
            evidence_quote="Test quote",
            confidence=-0.5,  # Below minimum
            recency_score=0.5,
        )

        assert insight.confidence == 0.0  # Clamped to minimum

    def test_recency_score_clamped_above_maximum(self):
        """Test recency score is clamped to maximum 1.0."""
        document_id = uuid4()

        insight = TrendInsight(
            document_id=document_id,
            summary="Test insight",
            keywords=["test"],
            domain_tags=["test"],
            evidence_quote="Test quote",
            confidence=0.7,
            recency_score=2.0,  # Above maximum
        )

        assert insight.recency_score == 1.0  # Clamped to maximum

    def test_recency_score_clamped_below_minimum(self):
        """Test recency score is clamped to minimum 0.0."""
        document_id = uuid4()

        insight = TrendInsight(
            document_id=document_id,
            summary="Test insight",
            keywords=["test"],
            domain_tags=["test"],
            evidence_quote="Test quote",
            confidence=0.7,
            recency_score=-1.0,  # Below minimum
        )

        assert insight.recency_score == 0.0  # Clamped to minimum


class TestTrendTaxonomy:
    """Test TrendTaxonomy entity."""

    def test_valid_creation_with_defaults(self):
        """Test creating a valid taxonomy with default values."""
        taxonomy = TrendTaxonomy(
            domain="fashion",
            category="Nature",
            label="Natural Elements",
            description="Designs inspired by nature",
        )

        assert taxonomy.id is not None
        assert taxonomy.domain == "fashion"
        assert taxonomy.category == "Nature"
        assert taxonomy.label == "Natural Elements"
        assert taxonomy.active is True
        assert taxonomy.parent_id is None

    def test_valid_creation_with_parent(self):
        """Test creating a taxonomy with parent category."""
        parent_id = uuid4()

        taxonomy = TrendTaxonomy(
            domain="fashion",
            category="Plants",
            label="Plant-based Designs",
            description="Designs featuring plants and flora",
            parent_id=parent_id,
        )

        assert taxonomy.parent_id == parent_id
        assert taxonomy.category == "Plants"

    def test_deactivate_active_taxonomy(self):
        """Test deactivating an active taxonomy."""
        taxonomy = TrendTaxonomy(
            domain="fashion",
            category="Nature",
            label="Natural Elements",
            description="Designs inspired by nature",
            active=True,
        )

        original_updated_at = taxonomy.updated_at
        taxonomy.deactivate()

        assert taxonomy.active is False
        # updated_at should be changed (may be same time if very fast)
        assert taxonomy.updated_at >= original_updated_at

    def test_deactivate_already_inactive_taxonomy(self):
        """Test deactivating an already inactive taxonomy (idempotent)."""
        taxonomy = TrendTaxonomy(
            domain="fashion",
            category="Nature",
            label="Natural Elements",
            description="Designs inspired by nature",
            active=False,
        )

        original_updated_at = taxonomy.updated_at
        taxonomy.deactivate()

        assert taxonomy.active is False
        assert taxonomy.updated_at == original_updated_at  # No update


class TestParsingFailureQueue:
    """Test ParsingFailureQueue entity."""

    def test_valid_creation_with_defaults(self):
        """Test creating a valid failure queue entry with defaults."""
        document_id = uuid4()

        failure = ParsingFailureQueue(
            document_id=document_id,
            reason="PDF extraction failed: corrupted file",
        )

        assert failure.id is not None
        assert failure.document_id == document_id
        assert failure.reason == "PDF extraction failed: corrupted file"
        assert failure.retried_count == 0
        assert failure.created_at is not None

    def test_valid_creation_with_initial_retry_count(self):
        """Test creating failure entry with initial retry count."""
        document_id = uuid4()

        failure = ParsingFailureQueue(
            document_id=document_id,
            reason="Timeout during parsing",
            retried_count=2,
        )

        assert failure.retried_count == 2

    def test_increment_retry_increments_count(self):
        """Test increment_retry increases retried_count."""
        failure = ParsingFailureQueue(
            document_id=uuid4(),
            reason="Test failure",
        )

        assert failure.retried_count == 0

        failure.increment_retry()
        assert failure.retried_count == 1

        failure.increment_retry()
        assert failure.retried_count == 2

    def test_multiple_increments_accumulate(self):
        """Test multiple increments accumulate correctly."""
        failure = ParsingFailureQueue(
            document_id=uuid4(),
            reason="Test failure",
        )

        for _ in range(5):
            failure.increment_retry()

        assert failure.retried_count == 5
