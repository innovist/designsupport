"""Parser adapters for different file types.

Implements ParserPort interface with specific parsers.
"""
from apps.trend_knowledge.infrastructure.adapters.parsers.doc_parser import (
    DocParser,
    get_doc_parser,
)
from apps.trend_knowledge.infrastructure.adapters.parsers.parser_registry import (
    ParserRegistry,
    get_parser_registry,
)
from apps.trend_knowledge.infrastructure.adapters.parsers.pdf_parser import (
    PDFParser,
    get_pdf_parser,
)

__all__ = [
    "PDFParser",
    "DocParser",
    "ParserRegistry",
    "get_pdf_parser",
    "get_doc_parser",
    "get_parser_registry",
]
