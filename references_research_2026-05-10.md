# 외부 레퍼런스 조사 보고서

작성일: 2026-05-10
조사 범위: 사용자가 지정한 14개 GitHub 저장소
목적: 본 프로젝트(DesignSupport)의 검색·크롤링·RAG 백엔드 강화에 응용 가능한 후보군 분석
구현 여부: **본 보고서는 조사만 수행. 구현은 별도 승인 후 진행.**

본 프로젝트의 현재 결함:
- `app/infrastructure/search/web_search.py`는 `SearXNGSearchClient` / `NoOpSearchClient` 두 클라이언트만 제공
- `.env`의 `WEB_SEARCH_CRAWLER_API_BASE_URL` 설정값은 코드에 연결되지 않은 상태(grep 0건)
- 검색 빈 결과 → 추상화 규칙 0건 → `generating` 단계에서 hard error
  (예: 세션 `d25bcb42-15d6-41c2-bb52-271f280086f0`, 2026-05-10 01:21:10)

이 결함을 해소하기 위한 후보 라이브러리·서비스를 아래와 같이 4개 그룹(A~D)으로 분류하였다.

---

## A. 범용 크롤링·스크래핑 프레임워크

### A-1. Scrapy
- URL: https://github.com/scrapy/scrapy
- 라이선스: BSD-3-Clause | 언어: Python 99.5% | ★ 61.6k | 최신 2.15.2 (2026-04)
- 핵심: 대규모·구조화 크롤링 표준 프레임워크. 비동기 트위스티드 기반, 셀렉터·파이프라인·미들웨어 체계.
- 본 프로젝트 적용 가능성:
  - **중**. 트렌드/레퍼런스 수집 단계에서 도메인별 크롤러를 구축할 때 표준 후보. 그러나 LLM 친화적 출력 변환 레이어는 별도 작성 필요.
  - 단점: JS-heavy 사이트는 별도 Splash/Playwright 통합 필요. SaaS화·앱화 시 인프라 복잡도 증가.

### A-2. Crawlee-Python (Apify)
- URL: https://github.com/apify/crawlee-python
- 라이선스: Apache-2.0 | 언어: Python 77% | ★ 9.0k
- 핵심: HTTP / 헤드리스(Playwright) 통합 인터페이스. 자동 병렬·프록시 로테이션·세션 관리·재시도 내장.
- 본 프로젝트 적용 가능성:
  - **상**. 현재 구조의 `SearchClient` 포트와 호환되는 비동기 크롤러 어댑터로 가장 적합. RAG·LLM 활용을 명시적으로 의도한 라이브러리.
  - 장점: BeautifulSoup·Parsel·Playwright 다층 파싱, asyncio 친화. 본 프로젝트의 FastAPI 비동기 구조와 자연스러움.

### A-3. Crawl4AI
- URL: https://github.com/unclecode/crawl4ai
- 라이선스: Apache-2.0 | 언어: Python 98.8% | ★ 65.3k
- 핵심: "LLM-friendly"를 표방. 깨끗한 Markdown / JSON / 인용 포함 fit-markdown 출력. litellm 호환. 시맨틱 청크·코사인 필터링 내장.
- 본 프로젝트 적용 가능성:
  - **최상**. 본 프로젝트의 `concepts.generate_concepts` / `references.search_references`의 입력은 결국 LLM 프롬프트로 들어간다. 따라서 LLM 가공된 markdown을 직접 출력하는 Crawl4AI는 추상화 단계 품질을 직접 끌어올릴 수 있다.
  - 단점: 의존성이 큼(playwright + litellm). 컨테이너화 권장.

### A-4. Scrapling
- URL: https://github.com/D4Vinci/Scrapling
- 라이선스: BSD-3-Clause | 언어: Python 99.9% | ★ 48.2k
- 핵심: 적응형 셀렉터(사이트 레이아웃 변경 시 자동 재배치) + StealthyFetcher로 Cloudflare Turnstile 우회.
- 본 프로젝트 적용 가능성:
  - **중상**. Pinterest·Instagram·디자인 갤러리 사이트 등 봇 차단이 있는 시각 레퍼런스 출처를 다룰 때 효과적.
  - 주의: 약관 위배·법적 리스크 발생 가능. "조사·교육 목적" 한정 사용.

### A-5. AnyCrawl
- URL: https://github.com/any4ai/AnyCrawl
- 라이선스: MIT | 언어: TypeScript/Node.js | ★ 3.2k
- 핵심: REST API(`/v1/scrape` `/v1/crawl` `/v1/search`). Google/Bing/Baidu SERP 구조화 추출.
- 본 프로젝트 적용 가능성:
  - **중**. 별도 Node 서비스로 띄우고 본 Python 백엔드는 HTTP 호출만 하면 됨 → 현재 `WEB_SEARCH_CRAWLER_API_BASE_URL`(외부 크롤러 패턴)과 100% 부합.
  - 단점: TS 스택 운영 부담 증가. 본 프로젝트가 모두 Python인 점과 이질적.

### A-6. MediaCrawler
- URL: https://github.com/NanmiCoder/MediaCrawler
- 라이선스: 학습·연구용 한정(상업적 사용 금지) | 언어: Python | ★ 49.2k
- 핵심: Xiaohongshu / Douyin / Kuaishou / Bilibili / Weibo / Tieba / Zhihu 7개 중국 SNS 통합 수집기.
- 본 프로젝트 적용 가능성:
  - **하**. 본 프로젝트가 SaaS·앱 확장을 명시하므로 라이선스 충돌. 또한 한국·글로벌 사용자가 주 타깃이면 효용 낮음.
  - 단, 트렌드 분석에서 중국 시장 디자인 동향 참고용 별도 도구로는 가치 있음.

### A-7. Obscura
- URL: https://github.com/h4ckf0r0day/obscura
- 라이선스: Apache-2.0 | 언어: Rust | ★ 11.3k
- 핵심: V8 기반 헤드리스 브라우저. CDP 호환. 세션별 fingerprint 랜덤화, 트래커 3,520개 도메인 차단.
- 본 프로젝트 적용 가능성:
  - **중**. Playwright/Puppeteer 호환이라 기존 Crawlee/Crawl4AI의 백엔드 브라우저 교체 후보.
  - Rust 바이너리만 배포 → 배포 단순. 단, 안정성·생태계는 Chrome+Playwright 조합이 우위.

---

## B. RAG·문서 인덱싱 시스템

### B-1. OpenRAG (Langflow)
- URL: https://github.com/langflow-ai/openrag
- 라이선스: Apache-2.0 | 언어: Python 62.1% / TS 31.1% | ★ 4.0k
- 핵심: Langflow 시각 워크플로우 빌더 + Docling + OpenSearch.
- 본 프로젝트 적용 가능성:
  - **중**. 사용자 자체 문서(예: 브랜드북·과거 디자인 자료)를 인덱싱·재참조하는 기능을 추가할 때 후보.
  - 단점: 별도 OpenSearch 인프라 필요. 본 프로젝트 현재 SQLite 기반과 격차.

### B-2. LightRAG (HKUDS)
- URL: https://github.com/HKUDS/LightRAG
- 라이선스: MIT | 언어: Python 81.3% | ★ 35.0k | EMNLP 2025 채택
- 핵심: 엔티티·관계 추출 → 지식 그래프 + 벡터 이중 검색. NaiveRAG/RQ-RAG/HyDE 대비 우수.
- 본 프로젝트 적용 가능성:
  - **중상**. 디자인 컨셉 → "주 피사체 / 재질 / 조명 / 구도" 같은 구조적 관계는 지식 그래프와 친화. 추상화 단계의 "규칙 추출" 품질을 끌어올릴 잠재력.
  - 단점: 인덱싱 비용 큼(엔티티 추출 LLM 호출). 단발성 트렌드 검색에는 과한 솔루션.

### B-3. PageIndex (VectifyAI)
- URL: https://github.com/VectifyAI/PageIndex
- 라이선스: MIT | 언어: Python | ★ 30.2k
- 핵심: **벡터 DB 없이** 문서 트리 인덱스 + LLM 추론 기반 검색. Mafin 2.5가 FinanceBench 98.7% 달성.
- 본 프로젝트 적용 가능성:
  - **중**. PDF·Markdown·비전 처리 강점이지만 본 프로젝트의 주 입력(웹 검색·이미지 레퍼런스)과는 결이 다름. 사용자가 자체 디자인 매뉴얼·스펙 PDF를 업로드해 추론 시 참고하는 시나리오에서 유용.

### B-4. OpenDeepSearch (Sentient AI)
- URL: https://github.com/sentient-agi/OpenDeepSearch
- 라이선스: Apache-2.0 | 언어: Python | ★ 3.8k
- 핵심: SmolAgents 통합 추론형 검색 도구. LiteLLM로 OpenAI/Anthropic/Google/OpenRouter 등 지원. SimpleQA 단일 홉은 동급, 다중 홉(FRAMES) 우월.
- 본 프로젝트 적용 가능성:
  - **상**. 본 프로젝트의 `concepts.generate_concepts`은 이미 다중 홉 추론(브리프 → 트렌드 → 컨셉 → 레퍼런스)이라 deep search 패러다임에 부합.
  - 도구로 직접 임포트 가능(`OpenDeepSearchTool`). LiteLLM이라 본 프로젝트의 다중 제공자 카탈로그(8개)와 매끄럽게 연결.

### B-5. Vane (ItzCrazyKns)
- URL: https://github.com/ItzCrazyKns/Vane
- 라이선스: MIT | 언어: TypeScript 98.8% | ★ 34.2k
- 핵심: Perplexity 방식 답변 엔진. SearxNG 백엔드 + Ollama·OpenAI·Claude·Groq·Gemini. Speed/Balanced/Quality 3 모드.
- 본 프로젝트 적용 가능성:
  - **하 (참고만)**. 본 프로젝트는 백엔드 라이브러리가 필요하지 답변 UI 제품이 필요하지 않음. 단, **SearxNG 운영 패턴**(쿼리 멀티엔진·인용 부착)은 그대로 차용 가능.

---

## C. 통합·도구·인프라

### C-1. Google Workspace CLI
- URL: https://github.com/googleworkspace/cli
- 라이선스: Apache-2.0 (비공식 도구) | 언어: Rust 98.8% | ★ 26.0k
- 핵심: Drive/Gmail/Calendar/Sheets/Docs/Chat 통합 CLI. Discovery Service 기반 동적 명령. 100+ Agent Skills, MCP Registry.
- 본 프로젝트 적용 가능성:
  - **하**. 본 프로젝트 핵심 흐름과 직결되지 않음. 단, 사용자가 Drive 자료를 자동 업로드하거나 Sheets로 트렌드 데이터를 내보낼 때 후속 통합 옵션.

### C-2. NotebookLM-py
- URL: https://github.com/teng-lin/notebooklm-py
- 라이선스: MIT | 언어: Python | ★ 12.9k
- 핵심: NotebookLM 비공식 API. 노트북 관리·소스 인제스트(URL/PDF/YouTube/Drive)·콘텐츠 생성(오디오·비디오·퀴즈·슬라이드·인포그래픽·마인드맵).
- 본 프로젝트 적용 가능성:
  - **하**. 비공식 + Playwright 로그인 기반이라 운영 안정성 낮음. 데모·실험 용도로만 권장.

---

## D. 우선순위·권장 조합 (요약)

본 프로젝트의 **현재 결함 해소(검색 백엔드 미설정)** 관점에서 우선순위:

| 순위 | 후보 | 역할 | 근거 |
|------|------|------|------|
| ★1 | **Crawl4AI** | LLM-친화 markdown 산출 1차 검색·요약 | 단독으로도 동작, litellm 호환, ★65.3k 안정성 |
| ★2 | **OpenDeepSearch** | 다중 홉 추론 검색 도구로 직접 import | 본 프로젝트 use_cases와 시그니처 호환 |
| ★3 | **Crawlee-Python** | 도메인별 정밀 크롤러가 필요할 때 | 본 FastAPI 비동기와 매끄러움 |
| ★4 | **SearxNG (기존 코드 유지)** | 로컬 자체 호스팅 옵션 | 코드 이미 존재, Docker 기동만 필요 |
| ★5 | AnyCrawl | 외부 크롤러 서비스 패턴 유지 시 | `.env`의 `WEB_SEARCH_CRAWLER_API_BASE_URL`과 호환되는 SaaS 후보 |
| - | LightRAG | 추상화 규칙 품질 강화 시 후속 | 인덱싱 비용 고려 |
| - | PageIndex | 사용자 PDF 매뉴얼 인제스트 시 | 별도 모듈 |
| - | Scrapling | Cloudflare 차단 사이트 한정 |
| - | Obscura | Playwright 대체 브라우저 |
| - | Vane | 운영 모범 참고만 |
| - | OpenRAG | 자체 문서 RAG 추가 기능 |
| - | Scrapy | 대형 크롤러 사업 확장 시 |
| - | MediaCrawler | 라이선스 충돌, 비권장 |
| - | Google CLI / NotebookLM-py | 본 프로젝트 흐름 외 |

### 권장 단계적 적용안 (구현 시점에 별도 plan_03.md로 상세화 예정)

1. **단계 1 (즉시 결함 해소)**:
   - 기존 `SearchClient` 포트 유지 + `Crawl4AISearchClient` 신규 구현 + 기존 `SearXNGSearchClient` + `NoOpSearchClient` + 사용자 수동 입력 fallback.
   - `.env` 우선순위: `CRAWL4AI_API_URL` → `SEARXNG_API_URL` → 수동 입력.

2. **단계 2 (품질 강화)**:
   - 추상화 단계 입력에 OpenDeepSearch 다중 홉 도구 통합.

3. **단계 3 (선택)**:
   - 사용자 자체 자료(브랜드북·과거 작업) 인제스트 위해 LightRAG 또는 PageIndex 도입 검토.

---

## E. 주의사항 (모든 적용에 공통)

- 라이선스 분류:
  - 상용·SaaS 가능: Apache-2.0 (Crawlee, Crawl4AI, OpenRAG, OpenDeepSearch, Obscura, Google CLI), BSD-3 (Scrapy, Scrapling), MIT (Vane, LightRAG, PageIndex, AnyCrawl, NotebookLM-py)
  - **상용 불가**: MediaCrawler (학습·연구 한정)
- 비공식 API 의존(NotebookLM-py)은 운영 환경 금지.
- Cloudflare 우회·fingerprint 회피(Scrapling, Obscura)는 사이트 약관·국내법 검토 후에만.
- 모든 후보 도입 시 본 프로젝트의 8개 LLM 제공자 카탈로그(`app/core/model_catalog.py`)·feature key 체계와 호환성 검증 필요.

---

## 출처(Sources)

- https://github.com/scrapy/scrapy
- https://github.com/apify/crawlee-python
- https://github.com/unclecode/crawl4ai
- https://github.com/D4Vinci/Scrapling
- https://github.com/any4ai/AnyCrawl
- https://github.com/ItzCrazyKns/Vane
- https://github.com/NanmiCoder/MediaCrawler
- https://github.com/langflow-ai/openrag
- https://github.com/HKUDS/LightRAG
- https://github.com/VectifyAI/PageIndex
- https://github.com/sentient-agi/OpenDeepSearch
- https://github.com/googleworkspace/cli
- https://github.com/teng-lin/notebooklm-py
- https://github.com/h4ckf0r0day/obscura

조사 일자: 2026-05-10. 별·버전 등 수치는 조사 시점 기준이며 시간 경과에 따라 변동 가능.
