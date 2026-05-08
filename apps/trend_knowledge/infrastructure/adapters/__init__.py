"""Trend Knowledge infrastructure adapters.

External service integrations and file processing adapters.
"""
from apps.trend_knowledge.infrastructure.adapters.crawlers import (
    BaseCrawler,
    CrawleeCrawlerAdapter,
    Crawl4AICrawlerAdapter,
    ScrapyCrawlerAdapter,
    ScraplingCrawlerAdapter,
)
from apps.trend_knowledge.infrastructure.adapters.file_type_detector import (
    FileTypeDetector,
    get_file_type_detector,
)
from apps.trend_knowledge.infrastructure.adapters.parsers import (
    DocParser,
    ParserRegistry,
    PDFParser,
    get_doc_parser,
    get_parser_registry,
    get_pdf_parser,
)
from apps.trend_knowledge.infrastructure.adapters.rag_adapter import (
    LightRAGAdapter,
    get_lightrag_adapter,
)

__all__ = [
    # Crawlers
    "BaseCrawler",
    "ScrapyCrawlerAdapter",
    "CrawleeCrawlerAdapter",
    "Crawl4AICrawlerAdapter",
    "ScraplingCrawlerAdapter",
    # Parsers
    "FileTypeDetector",
    "PDFParser",
    "DocParser",
    "ParserRegistry",
    "get_file_type_detector",
    "get_pdf_parser",
    "get_doc_parser",
    "get_parser_registry",
    # RAG
    "LightRAGAdapter",
    "get_lightrag_adapter",
]
