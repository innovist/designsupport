"""Trend Knowledge infrastructure layer.

ORM models, repositories, adapters, tasks, and seed data.
"""
from apps.trend_knowledge.infrastructure.adapters import (
    BaseCrawler,
    CrawleeCrawlerAdapter,
    Crawl4AICrawlerAdapter,
    DocParser,
    FileTypeDetector,
    LightRAGAdapter,
    PDFParser,
    ParserRegistry,
    ScraplingCrawlerAdapter,
    ScrapyCrawlerAdapter,
    get_doc_parser,
    get_file_type_detector,
    get_lightrag_adapter,
    get_parser_registry,
    get_pdf_parser,
)
from apps.trend_knowledge.infrastructure.orm import (
    ParsingFailureQueue,
    TrendDocument,
    TrendInsight,
    TrendSource,
    TrendTaxonomy,
)
from apps.trend_knowledge.infrastructure.repositories import (
    DjangoParsingFailureQueueRepository,
    DjangoTrendDocumentRepository,
    DjangoTrendInsightRepository,
    DjangoTrendSourceRepository,
    DjangoTrendTaxonomyRepository,
)
from apps.trend_knowledge.infrastructure.seed_data import (
    get_seed_taxonomy_count,
    seed_taxonomy_data,
)

__all__ = [
    # ORM Models
    "TrendSource",
    "TrendDocument",
    "TrendInsight",
    "TrendTaxonomy",
    "ParsingFailureQueue",
    # Repositories
    "DjangoTrendSourceRepository",
    "DjangoTrendDocumentRepository",
    "DjangoTrendInsightRepository",
    "DjangoTrendTaxonomyRepository",
    "DjangoParsingFailureQueueRepository",
    # Adapters
    "BaseCrawler",
    "ScrapyCrawlerAdapter",
    "CrawleeCrawlerAdapter",
    "Crawl4AICrawlerAdapter",
    "ScraplingCrawlerAdapter",
    "FileTypeDetector",
    "PDFParser",
    "DocParser",
    "ParserRegistry",
    "LightRAGAdapter",
    "get_file_type_detector",
    "get_pdf_parser",
    "get_doc_parser",
    "get_parser_registry",
    "get_lightrag_adapter",
    # Seed Data
    "seed_taxonomy_data",
    "get_seed_taxonomy_count",
]
