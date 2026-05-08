"""Unit tests for trend_knowledge application use cases.

Tests cover search, document parsing, and insight extraction use cases.
"""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock

from apps.trend_knowledge.application.use_cases.search_trends import SearchTrendsUseCase
from apps.trend_knowledge.application.dtos import SearchTrendRequest, TrendSearchResponse
from apps.trend_knowledge.domain.entities import TrendInsight
from shared.domain.exceptions import ValidationError


class TestSearchTrendsUseCase:
    """Test search trends use case."""

    @pytest.fixture
    def mock_rag_port(self):
        """Create mock RAG port."""
        rag_port = Mock()
        rag_port.search = AsyncMock()
        return rag_port

    @pytest.fixture
    def search_use_case(self, mock_rag_port):
        """Create search use case with mocked dependencies."""
        return SearchTrendsUseCase(rag_port=mock_rag_port)

    @pytest.fixture
    def sample_insight(self):
        """Create sample trend insight."""
        return TrendInsight(
            document_id=uuid4(),
            summary="Minimalist design continues to dominate",
            keywords=["minimalism", "clean", "simple"],
            domain_tags=["industrial", "product"],
            evidence_quote="The trend toward minimalism shows no sign of slowing",
            confidence=0.85,
            recency_score=0.72,
        )

    @pytest.mark.asyncio
    async def test_valid_search_returns_results(self, search_use_case, mock_rag_port, sample_insight):
        """Test that valid search returns results."""
        # Setup mock response
        mock_rag_port.search.return_value = [sample_insight]

        # Create request
        request = SearchTrendRequest(
            query="minimalist design trends",
            domain="industrial",
            min_confidence=0.7,
            max_results=10,
        )

        # Execute
        result = await search_use_case.execute(request)

        # Assertions
        assert isinstance(result, TrendSearchResponse)
        assert len(result.insights) == 1
        assert result.total == 1
        assert result.insufficient_evidence is False

        # Verify insight data
        insight_dto = result.insights[0]
        assert insight_dto["summary"] == "Minimalist design continues to dominate"
        assert insight_dto["confidence"] == 0.85
        assert insight_dto["keywords"] == ["minimalism", "clean", "simple"]

        # Verify RAG port was called correctly
        mock_rag_port.search.assert_called_once_with(
            query_text="minimalist design trends",
            domain="industrial",
            date_range=None,
            min_confidence=0.7,
            limit=10,
        )

    @pytest.mark.asyncio
    async def test_empty_query_raises_validation_error(self, search_use_case):
        """Test that empty query raises ValidationError."""
        request = SearchTrendRequest(
            query="",  # Empty query
            domain="fashion",
        )

        with pytest.raises(ValidationError) as exc_info:
            await search_use_case.execute(request)

        # ValidationError stores the full message in the exception
        assert "query" in str(exc_info.value).lower() or "empty" in str(exc_info.value).lower()
        assert exc_info.value.field == "query"

    @pytest.mark.asyncio
    async def test_whitespace_only_query_raises_error(self, search_use_case):
        """Test that whitespace-only query raises ValidationError."""
        request = SearchTrendRequest(
            query="   ",  # Only whitespace
            domain="fashion",
        )

        with pytest.raises(ValidationError) as exc_info:
            await search_use_case.execute(request)

        # ValidationError stores the full message in the exception
        assert "query" in str(exc_info.value).lower() or "empty" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_no_results_returns_insufficient_evidence(self, search_use_case, mock_rag_port):
        """Test that no results sets insufficient_evidence flag."""
        # Setup mock to return empty list
        mock_rag_port.search.return_value = []

        request = SearchTrendRequest(
            query="obscure trend term",
            domain="fashion",
        )

        result = await search_use_case.execute(request)

        assert result.total == 0
        assert len(result.insights) == 0
        assert result.insufficient_evidence is True

    @pytest.mark.asyncio
    async def test_search_with_dict_results_from_rag(self, search_use_case, mock_rag_port):
        """Test handling dict results from RAG port (non-entity format)."""
        # Setup mock to return dict (as some RAG implementations might)
        mock_rag_port.search.return_value = [
            {
                "id": str(uuid4()),
                "summary": "Sustainable packaging trends",
                "keywords": ["sustainability", "eco-friendly"],
                "evidence_quote": "Packaging is becoming more sustainable",
                "confidence": 0.78,
                "document_id": str(uuid4()),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ]

        request = SearchTrendRequest(
            query="sustainable packaging",
            domain="industrial",
        )

        result = await search_use_case.execute(request)

        assert len(result.insights) == 1
        assert result.insights[0]["summary"] == "Sustainable packaging trends"

    @pytest.mark.asyncio
    async def test_search_with_date_range(self, search_use_case, mock_rag_port):
        """Test search with date range filter."""
        mock_rag_port.search.return_value = []

        date_range = (
            (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
            datetime.now(timezone.utc).isoformat(),
        )

        request = SearchTrendRequest(
            query="recent trends",
            domain="fashion",
            date_range=date_range,
        )

        await search_use_case.execute(request)

        # Verify date_range was passed to RAG port
        mock_rag_port.search.assert_called_once()
        call_kwargs = mock_rag_port.search.call_args.kwargs
        assert call_kwargs["date_range"] == date_range

    @pytest.mark.asyncio
    async def test_search_with_default_max_results(self, search_use_case, mock_rag_port):
        """Test that default max_results is 10 when not specified."""
        mock_rag_port.search.return_value = []

        request = SearchTrendRequest(
            query="design trends",
            domain="industrial",
            # max_results not specified
        )

        await search_use_case.execute(request)

        # Verify default limit of 10
        call_kwargs = mock_rag_port.search.call_args.kwargs
        assert call_kwargs["limit"] == 10

    @pytest.mark.asyncio
    async def test_search_exception_propagates(self, search_use_case, mock_rag_port):
        """Test that RAG port exceptions are propagated."""
        # Setup mock to raise exception
        mock_rag_port.search.side_effect = Exception("RAG service unavailable")

        request = SearchTrendRequest(
            query="test query",
            domain="fashion",
        )

        with pytest.raises(Exception) as exc_info:
            await search_use_case.execute(request)

        assert "RAG service unavailable" in str(exc_info.value)


class TestIngestDocumentUseCase:
    """Test document ingestion use case."""

    def test_create_trend_document_from_raw(self):
        """Test creating a TrendDocument from raw crawl data."""
        from apps.trend_knowledge.domain.entities import TrendDocument

        source_id = uuid4()
        raw_data = {
            "title": "Summer 2026 Fashion Forecast",
            "url": "https://example.com/article",
            "published_at": "2026-05-01T10:00:00Z",
            "raw_uri": "s3://bucket/raw/123.pdf",
            "hash": "abc123def456",
        }

        document = TrendDocument(
            source_id=source_id,
            title=raw_data["title"],
            url=raw_data["url"],
            published_at=datetime.fromisoformat(raw_data["published_at"].replace("Z", "+00:00")),
            raw_uri=raw_data["raw_uri"],
            hash=raw_data["hash"],
        )

        assert document.title == "Summer 2026 Fashion Forecast"
        assert document.parse_status == "pending"
        assert document.source_id == source_id

    def test_ingest_triggers_parsing_workflow(self):
        """Test that document ingestion triggers parsing status transition."""
        from apps.trend_knowledge.domain.entities import TrendDocument

        document = TrendDocument(
            source_id=uuid4(),
            title="Test Article",
            url="https://example.com/test",
            published_at=datetime.now(timezone.utc),
            raw_uri="s3://bucket/raw/test.pdf",
            hash="hash123",
            parse_status="pending",
        )

        # Simulate workflow: pending → parsing → parsed
        assert document.parse_status == "pending"

        document.mark_parsing()
        assert document.parse_status == "parsing"

        document.mark_parsed("s3://bucket/parsed/test.txt")
        assert document.parse_status == "parsed"
        assert document.parsed_text_uri == "s3://bucket/parsed/test.txt"


class TestParseDocumentUseCase:
    """Test document parsing use case."""

    def test_parse_success_creates_insights(self):
        """Test that successful parsing creates TrendInsights."""
        from apps.trend_knowledge.domain.entities import TrendDocument, TrendInsight

        document = TrendDocument(
            source_id=uuid4(),
            title="Design Trends 2026",
            url="https://example.com/trends",
            published_at=datetime.now(timezone.utc),
            raw_uri="s3://bucket/raw/trends.pdf",
            hash="trends_hash",
        )

        # Simulate parsing
        document.mark_parsing()

        # Simulate insight extraction
        insights = [
            TrendInsight(
                document_id=document.id,
                summary="Bold typography is trending",
                keywords=["typography", "bold", "fonts"],
                domain_tags=["visual", "graphic"],
                evidence_quote="Designers are embracing bold, oversized typography",
                confidence=0.82,
                recency_score=0.91,
            )
        ]

        document.mark_parsed("s3://bucket/parsed/trends.txt")

        assert document.parse_status == "parsed"
        assert len(insights) == 1
        assert insights[0].document_id == document.id

    def test_parse_failure_creates_queue_entry(self):
        """Test that parse failure creates ParsingFailureQueue entry."""
        from apps.trend_knowledge.domain.entities import TrendDocument, ParsingFailureQueue

        document = TrendDocument(
            source_id=uuid4(),
            title="Corrupted PDF",
            url="https://example.com/bad",
            published_at=datetime.now(timezone.utc),
            raw_uri="s3://bucket/raw/bad.pdf",
            hash="bad_hash",
        )

        document.mark_parsing()
        document.mark_failed()

        # Create failure queue entry
        failure = ParsingFailureQueue(
            document_id=document.id,
            reason="PDF extraction failed: file corrupted or invalid format",
        )

        assert document.parse_status == "failed"
        assert failure.document_id == document.id
        assert failure.retried_count == 0
