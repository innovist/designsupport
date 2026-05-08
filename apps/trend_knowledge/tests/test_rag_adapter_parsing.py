"""Test LightRAG adapter citation parsing."""
import pytest
from apps.trend_knowledge.infrastructure.adapters.rag_adapter import LightRAGAdapter


class TestLightRAGCitationParsing:
    """Test citation extraction from LightRAG responses."""

    def test_extract_document_id_from_response(self):
        """Test extracting document ID from LightRAG response format."""
        adapter = LightRAGAdapter()

        # Mock LightRAG response with document ID marker
        response = """[Document ID: 123e4567-e89b-12d3-a456-426614174000]
Fashion trends for 2024 include sustainable materials and bold colors.
published_at: 2024-01-15
url: https://example.com/article

The fashion industry is moving towards eco-friendly materials."""

        results = adapter._parse_lightrag_response(response, limit=10)

        assert len(results) == 1
        assert results[0]["document_id"] == "123e4567-e89b-12d3-a456-426614174000"
        assert results[0]["published_at"] == "2024-01-15"
        assert "sustainable materials" in results[0]["answer"]
        assert results[0]["evidence_quote"] is not None
        assert len(results[0]["evidence_quote"]) > 0

    def test_extract_metadata_fields(self):
        """Test extracting various metadata fields from response."""
        adapter = LightRAGAdapter()

        response = """[Document ID: 987fcdeb-51a2-43f1-a456-426614174000]
published_at: 2024-03-20
author: Jane Doe
source: Fashion Weekly
url: https://fashionweekly.com/trends

Spring 2024 trends focus on pastel colors and lightweight fabrics."""

        results = adapter._parse_lightrag_response(response, limit=10)

        assert len(results) == 1
        assert results[0]["document_id"] == "987fcdeb-51a2-43f1-a456-426614174000"
        assert results[0]["published_at"] == "2024-03-20"
        assert "pastel colors" in results[0]["answer"]

    def test_evidence_quote_extraction(self):
        """Test that evidence_quote contains actual cited passage."""
        adapter = LightRAGAdapter()

        text = """Fashion trends for 2024 include sustainable materials. The industry is moving towards eco-friendly fabrics like organic cotton and recycled polyester. Consumers are increasingly demanding transparency in supply chains."""

        evidence = adapter._extract_evidence_quote(text)

        # Should extract the first meaningful sentence
        assert "sustainable materials" in evidence or "Fashion trends" in evidence
        assert len(evidence) > 20
        assert len(evidence) <= 303  # max_length + "..."

    def test_multiple_sections_parsing(self):
        """Test parsing multiple document sections."""
        adapter = LightRAGAdapter()

        response = """[Document ID: doc-001]
published_at: 2024-01-10
First document about minimalism in fashion.

[Document ID: doc-002]
published_at: 2024-02-15
Second document about maximalism trends.

[Document ID: doc-003]
Third document about sustainable fashion."""

        results = adapter._parse_lightrag_response(response, limit=10)

        assert len(results) == 3
        assert results[0]["document_id"] == "doc-001"
        assert results[1]["document_id"] == "doc-002"
        assert results[2]["document_id"] == "doc-003"

    def test_no_stub_values_in_results(self):
        """Test that no None/placeholder values remain in parsed results."""
        adapter = LightRAGAdapter()

        response = """[Document ID: test-doc-123]
published_at: 2024-04-01
Test content about fashion trends.

This is a test response to verify citation parsing."""

        results = adapter._parse_lightrag_response(response, limit=10)

        assert len(results) == 1
        # Check that we don't have stub None values when data exists
        if results[0]["answer"]:
            # If we have an answer, we should have extracted the evidence
            assert results[0]["evidence_quote"] is not None
            assert results[0]["evidence_quote"] != ""
            assert not results[0]["evidence_quote"].startswith("Would be")

    def test_insufficient_evidence_response(self):
        """Test that insufficient evidence returns proper structure."""
        adapter = LightRAGAdapter()

        result = adapter._insufficient_evidence_response("test query")

        assert len(result) == 1
        assert result[0]["answer"] == "Insufficient evidence in the knowledge base to answer this query."
        assert result[0]["score"] == 0.0
        assert result[0]["query"] == "test query"
