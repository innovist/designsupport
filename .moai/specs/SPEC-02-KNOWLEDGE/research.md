# Research: SPEC-02-KNOWLEDGE

Codebase analysis for knowledge management, trend crawling, reference search, image providers, and library integration.

## API Keys Status (Verified from .env)

ALL provider API keys are configured:

| Provider | Key Variable | Status |
|----------|-------------|--------|
| Google Gemini | `GEMINI_API_KEYS` | Configured |
| DeepSeek | `DEEPSEEK_API_KEY` | Configured |
| ByteDance Seedream | `BYTEDANCE_SEEDREAM_API_KEY` | Configured (`a79b284f-...`) |
| OpenAI | `OPENAI_API_KEY` | Configured (`sk-proj-...`) |
| Alibaba/Qwen | `ALIBABA_API_KEY` | Configured (`sk-e1f87...`) |
| Xiaomi MiMo | `XIAOMI_MIMO_API_KEY` | Configured |
| MiniMax | `MINIMAX_API_KEY` | Configured |
| Kimi/Moonshot | `KIMI_API_KEY` | Configured |
| KIPRIS (Patent) | `KIPRIS_API_KEY` | Configured |
| Pexels | `PEXELS_API_KEY` | Configured |
| Pixabay | `PIXABAY_API_KEY` | Configured |
| Unsplash | `UNSPLASH_ACCESS_KEY` | Configured |
| Web Search Crawler | `WEB_SEARCH_CRAWLER_API_BASE_URL` | Configured (`http://119.207.232.98:9123`) |
| YouTube Data | `YOUTUBE_API_KEYS` | Configured (2 keys) |

## Crawling Tool Integration (Reference Library Research)

### Tool Role Assignment by Use Case

| Tool | Role | Use Case | API Pattern |
|------|------|----------|-------------|
| **Scrapy** (61K+ stars) | Primary framework | Structured site crawling, spiders, pipelines | `scrapy.Spider` with `yield` items, `CrawlPipeline` |
| **Crawlee** (Python) | JS-heavy sites | SPA, React/Vue sites needing browser rendering | `PlaywrightCrawler` with `async handler`, proxy rotation via `ProxyConfiguration` |
| **Crawl4AI** (50K+ stars) | LLM-aware crawling | Trend article extraction, markdown output | `AsyncWebCrawler.arun(url)` → `result.markdown`, `LLMExtractionStrategy` with schema |
| **Scrapling** (37K+ stars) | Anti-bot bypass | Cloudflare-protected trend sites | `StealthyFetcher.fetch(url, solve_cloudflare=True)`, adaptive selectors |

### Crawlee Integration Pattern

```python
# SPEC-02 crawling service pattern
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

crawler = PlaywrightCrawler(
    max_requests_per_crawl=50,
    headless=True,
    browser_type='chromium',
)

@crawler.router.default_handler
async def handler(context: PlaywrightCrawlingContext) -> None:
    title = await context.page.title()
    await context.page.wait_for_selector('.article-content')
    content = await context.page.query_selector('.article-content')
    text = await content.inner_text() if content else None
    await context.push_data({'url': context.request.url, 'title': title, 'content': text})
    await context.enqueue_links(selector='a.next-page')

await crawler.run(['https://trend-site.com'])
```

**Proxy support:** `ProxyConfiguration(proxy_urls=[...])` with tiered escalation (free→premium→residential).

### Crawl4AI Integration Pattern

```python
# LLM-extraction for trend documents
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai import LLMExtractionStrategy, LLMConfig

llm_strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv('OPENAI_API_KEY')),
    schema=TrendArticle.schema_json(),
    extraction_type="schema",
    instruction="Extract trend article data: title, summary, keywords, sentiment",
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://trend-source.com", config=CrawlerRunConfig(
        extraction_strategy=llm_strategy, cache_mode=CacheMode.BYPASS
    ))
    data = json.loads(result.extracted_content)
```

### Scrapling Integration Pattern

```python
# Cloudflare bypass for protected trend sites
from scrapling.fetchers import StealthyFetcher

StealthyFetcher.adaptive = True
page = StealthyFetcher.fetch('https://protected-trend-site.com', solve_cloudflare=True, headless=True)
elements = page.css('.trend-article', auto_save=True)  # Adaptive: survives DOM changes
```

**Key feature:** `adaptive=True` enables element tracking across site redesigns - critical for long-running crawlers.

## File Processing Pipeline (Reference Library Research)

### Magika - File Type Detection (Google, 200+ formats, 99% accuracy)

```python
from magika import Magika

m = Magika()

# Single file detection
result = m.identify_path('./uploaded_file')
print(result.output.label)       # 'pdf', 'jpeg', 'png', etc.
print(result.output.mime_type)   # 'application/pdf'
print(result.output.is_text)     # False
print(result.prediction.score)   # 0.997

# Batch processing
results = m.identify_paths(['./file1.pdf', './file2.jpg', './file3.docx'])

# Raw bytes (for upload handling)
result = m.identify_bytes(file_bytes)
```

**Integration point:** Upload handler → Magika detect → route to appropriate parser.

### opendataloader-pdf - PDF Parsing (Benchmark #1, accuracy 0.907)

```python
import opendataloader_pdf

# Basic PDF → Markdown
opendataloader_pdf.convert(
    input_path="trend_report.pdf",
    output_dir="output/",
    format="json,markdown",
)

# Advanced: page selection, table extraction, hybrid AI mode
opendataloader_pdf.convert(
    input_path="complex_report.pdf",
    output_dir="output/",
    format="json,markdown",
    pages="1,3,5-10",              # Selective page extraction
    use_struct_tree=True,          # Use Tagged PDF structure
    hybrid="docling-fast",         # AI backend for complex layouts
    table_method="cluster",        # Enhanced table detection
    sanitize=True,                 # Replace sensitive data
)
```

**Output schema:** JSON with `type` (heading/paragraph/table/list/formula/picture), `bounding_box`, `page_number`, `content`.

**Note:** Requires Java 11+ runtime.

### PageIndex - Document Indexing (FinanceBench 98.7%, vectorless)

```python
from pageindex import PageIndexClient

client = PageIndexClient()
doc_id = client.index("./document.pdf")

# Get hierarchical tree structure (table-of-contents style)
tree = json.loads(client.get_document_structure(doc_id))

# Reasoning-based retrieval: LLM navigates tree to find relevant pages
# → returns page ranges → fetch specific pages
pages_str = "1,3,5-7"
content = json.loads(client.get_page_content(doc_id, pages_str))
```

**Architecture:** Vectorless RAG - builds semantic tree, uses LLM reasoning for retrieval instead of embedding similarity. Better for structured documents (reports, patents, research papers).

## LightRAG - Knowledge Graph RAG (EMNLP 2025)

```python
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed

rag = LightRAG(
    working_dir="./rag_storage",
    embedding_func=openai_embed,
    llm_model_func=gpt_4o_mini_complete,
)
await rag.initialize_storages()

# Insert documents (triggers chunking, entity extraction, graph merging, vector indexing)
await rag.ainsert("Trend document text...")

# Query modes:
# - "mix" (recommended): knowledge graph + vector retrieval
# - "local": entity-centric
# - "global": relationship patterns
# - "naive": pure vector similarity (no knowledge graph)
answer = await rag.aquery(
    "What are the key fashion trends for 2026?",
    param=QueryParam(mode="mix", top_k=10),
)
```

**6 retrieval modes:** local, global, hybrid, naive, mix, bypass.

## Image Provider Integration (API Keys Verified)

### Tier 1 - Direct Use (API Keys Available)

**Unsplash:**
```python
# Access Key: UNSPLASH_ACCESS_KEY
headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
# GET https://api.unsplash.com/search/photos?query=fashion+design
```

**Pexels:**
```python
# API Key: PEXELS_API_KEY
headers = {"Authorization": PEXELS_API_KEY}
# GET https://api.pexels.com/v1/search?query=fashion+trend&per_page=15
```

**Pixabay:**
```python
# API Key: PIXABAY_API_KEY
# GET https://pixabay.com/api/?key={KEY}&q=fashion+design&image_type=photo
```

**KIPRIS (Korean Patent):**
```python
# API Key: KIPRIS_API_KEY
# GET http://plus.kipris.or.kr/openapi/rest/patUtiModInfoSearchSevice/patentUtiModInfoSearch?serviceKey={KEY}
```

### Adapter Registry Pattern

```python
# Normalized response schema across all providers
class ReferenceImageResult:
    url: str
    thumbnail_url: str
    width: int
    height: int
    license_type: str       # CC0, CC-BY, CC-BY-SA, proprietary
    attribution_text: str
    provider: str           # unsplash, pexels, pixabay, etc.
    source_url: str
    tier: int               # 1, 2, 3

class ImageProviderAdapter(Protocol):
    async def search(self, query: str, count: int) -> list[ReferenceImageResult]: ...
    async def download(self, url: str, max_px: int = 1024) -> bytes: ...
    async def get_attribution(self, image_id: str) -> str: ...
```

**Storage policy:** Max 1024px WebP 80% for Tier 1/2, no download for Tier 3 (link-only).

## Existing Crawling Data

- `crawling_data/Youtube.json` - YouTube trend data (via YOUTUBE_API_KEYS)
- `crawling_data/Youtube_comments.json` - YouTube comment analysis
- Web Search Crawler API at `http://119.207.232.98:9123` (supports google, bing, duckduckgo, yahoo)

## Processing Pipeline: End-to-End Flow

```
Upload / Crawl → Magika (detect type) → Route:
  ├─ PDF → opendataloader-pdf (extract) → PageIndex (index tree) → LightRAG (insert)
  ├─ HTML → Crawl4AI / Scrapling (extract) → LightRAG (insert)
  ├─ Image → Magika (confirm) → ReferenceAsset (store metadata)
  └─ Unknown → reject with type error
```

## Key Gaps

| Gap | Severity | Description |
|-----|----------|-------------|
| No reference search | CRITICAL | Entire reference system is new |
| No RAG infrastructure | HIGH | LightRAG integration needed (6 query modes) |
| No file processing | HIGH | Magika→opendataloader→PageIndex pipeline needed |
| No license tracking | HIGH | ReferenceAsset tier/license model needed |
| No taxonomy service | MEDIUM | Category hierarchy management |
| Crawling tools partial | MEDIUM | Scrapy in requirements, need Crawlee/Crawl4AI/Scrapling |
| No adapter registry | MEDIUM | Image provider adapter pattern needed |

## Dependencies to Add

```
# Crawling
crawlee[all]           # PlaywrightCrawler + proxy management
crawl4ai               # LLM-aware extraction
scrapling              # Anti-bot bypass, adaptive selectors

# File Processing
magika                 # Google AI file type detection
opendataloader-pdf     # PDF parsing (requires Java 11+)
pageindex              # Vectorless document indexing

# RAG
lightrag               # Knowledge graph + vector RAG
```
