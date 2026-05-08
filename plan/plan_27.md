# Plan 27: AI 직접 조사 파이프라인 통합 (Gemini/Perplexity/GLM 검색 API)

**작성일**: 2025-12-24 10:30
**목적**: 크롤러 데이터와 클라우드 AI의 실시간 웹 검색/조사 결과를 통합하여 더 정확하고 풍부한 패션 트렌드 인사이트를 추출한다.

---

## 0. 배경 및 동기

### 현재 한계점
1. **크롤러 한계**: 키워드 기반 검색으로 정확한 글자가 아니면 조사 불가
2. **노이즈 문제**: 수집된 데이터에 관련 없는 정보 다수 포함
3. **맥락 부재**: AI가 이미 보유한 패션 도메인 지식 활용 미흡
4. **깊이 vs 넓이**: 크롤러는 깊이 있는 특정 데이터, AI는 주요 트렌드 개요에 강점

### 제안 솔루션
크롤러 데이터 + AI 직접 조사 결과를 통합하여 **상호 보완적 인사이트** 도출

### 지원 AI 검색 서비스
| 서비스 | 기능 | 가격 | SDK |
|--------|------|------|-----|
| **Gemini** | Grounding with Google Search | $14/1K 쿼리 | `google-genai` |
| **Perplexity** | Sonar 모델 (검색 특화) | $5/1K 검색 | `perplexityai` |
| **GLM** | 자율 웹 리서치 | $0.60-2.00/1M 토큰 | `zhipuai` |

---

## 1. 전제/제약

- 파일 ≤ 300 LOC, 함수 ≤ 50 LOC, 매개변수 ≤ 5, 순환 복잡도 ≤ 10
- 변경 전 관련 파일 전체 읽기 필수
- 실제 실행 로그 기반 테스트 필수
- 백엔드/프론트엔드 동시 점검
- 기존 폴백 체인 패턴 및 키 관리 구조 재사용
- AI 조사 기능은 **선택적** (사용자가 활성화/비활성화 가능)

---

## 2. 아키텍처 설계

### 2.1 수정된 파이프라인 흐름

```
기존 7단계:
1→2→3→4→5→6→7

수정 8단계:
1→2→3→[3.5: AI 직접 조사]→4→5→6→7→8

상세 흐름:
1. 입력 분석 (_build_input_context)
2. 키워드 추출 (_extract_keywords)
3. 데이터 수집 (_collect_data) - 크롤러
3.5. AI 직접 조사 (_conduct_ai_research) [NEW]
4. 트렌드 분석 (_analyze_trends) - 크롤러+AI 조사 데이터 통합
5. 디자인 아이디어 생성 (_generate_ideas)
6. 보고서 생성 (_generate_report_payload)
7. 이미지 생성 (_generate_images)
8. 블루프린트 생성 (_generate_blueprints)
```

### 2.2 신규 파일 구조

```
ai_clients/
├── research/                      [NEW 디렉토리]
│   ├── __init__.py
│   ├── base_research_client.py    # 연구 클라이언트 베이스 인터페이스
│   ├── gemini_research_client.py  # Gemini Grounding 검색
│   ├── perplexity_client.py       # Perplexity Sonar API
│   └── glm_research_client.py     # GLM 웹 리서치

app/services/
├── ai_research_service.py         [NEW] AI 조사 오케스트레이터

app/core/
├── settings_storage.py            [MODIFY] Perplexity 설정 추가

templates/pages/
├── settings.html                  [MODIFY] AI 조사 설정 UI 추가

static/js/
├── settings.js                    [MODIFY] AI 조사 설정 로직 추가
```

### 2.3 데이터 흐름

```
[키워드 추출 완료]
        │
        ▼
┌───────────────────────────────────────────────────────┐
│              3단계: 크롤러 데이터 수집                    │
│  keywords → CrawlerService → raw_crawled_data         │
└───────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────┐
│           3.5단계: AI 직접 조사 [NEW]                    │
│                                                        │
│  context_query 생성:                                   │
│  "2026년 봄여름 20~30대 여성 캐주얼 패션 트렌드 전망"      │
│                                                        │
│  ┌─────────┐   ┌─────────────┐   ┌─────────┐          │
│  │ Gemini  │   │ Perplexity  │   │   GLM   │          │
│  │ Search  │   │   Sonar     │   │ Research│          │
│  └────┬────┘   └──────┬──────┘   └────┬────┘          │
│       │               │               │               │
│       └───────────────┼───────────────┘               │
│                       ▼                               │
│              ai_research_results                      │
└───────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────┐
│              4단계: 통합 트렌드 분석                      │
│                                                        │
│  INPUT:                                               │
│  - raw_crawled_data (크롤러)                           │
│  - ai_research_results (AI 조사) [NEW]                 │
│                                                        │
│  OUTPUT:                                              │
│  - 통합 인사이트 (상호 검증, 보완)                        │
└───────────────────────────────────────────────────────┘
```

---

## 3. 상세 구현 계획

### 3.1 Phase 1: 설정 인프라 구축

#### 3.1.1 settings_storage.py 수정

```python
# 추가할 내용
AVAILABLE_MODELS = {
    # ... 기존 ...
    "research": {  # NEW
        "gemini_search": True,      # Grounding with Google Search
        "perplexity": ["sonar", "sonar-pro"],
        "glm_research": True
    }
}

DEFAULT_SETTINGS = {
    "api_keys": {
        # ... 기존 ...
        "perplexity": None  # NEW
    },
    "ai_research": {  # NEW 섹션
        "enabled": False,
        "models": {
            "gemini_search": False,
            "perplexity": False,
            "glm_research": False
        },
        "perplexity_model": "sonar",
        "research_depth": "standard"  # standard / deep
    }
}

# 새 함수들
def get_ai_research_config() -> Dict[str, Any]: ...
def save_ai_research_config(config: Dict[str, Any]) -> bool: ...
def is_ai_research_enabled() -> bool: ...
def get_enabled_research_models() -> List[str]: ...
```

#### 3.1.2 설정 API 엔드포인트 확장 (app/api/settings.py)

```python
@router.get("/ai-research")
async def get_ai_research_settings(): ...

@router.post("/ai-research")
async def save_ai_research_settings(config: AIResearchConfig): ...
```

### 3.2 Phase 2: AI 연구 클라이언트 구현

#### 3.2.1 base_research_client.py

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ResearchResult:
    """AI 조사 결과 데이터 클래스"""
    source: str           # gemini / perplexity / glm
    query: str            # 조사 쿼리
    content: str          # 조사 결과 텍스트
    citations: List[str]  # 출처 URL 목록
    timestamp: str        # 조사 시간
    model: str            # 사용된 모델

class BaseResearchClient(ABC):
    """AI 연구 클라이언트 베이스 클래스"""

    @abstractmethod
    async def research(
        self,
        query: str,
        context: Optional[str] = None
    ) -> ResearchResult:
        """주어진 쿼리로 웹 조사 수행"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """API 키 설정 여부 확인"""
        pass
```

#### 3.2.2 gemini_research_client.py

```python
from google import genai
from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

class GeminiResearchClient(BaseResearchClient):
    """Gemini Grounding with Google Search 클라이언트"""

    async def research(self, query: str, context: Optional[str] = None) -> ResearchResult:
        response = await self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=self._build_prompt(query, context),
            config=GenerateContentConfig(
                tools=[Tool(google_search=GoogleSearch())]
            )
        )
        return self._parse_response(response, query)
```

#### 3.2.3 perplexity_client.py

```python
from openai import OpenAI  # Perplexity는 OpenAI 호환 API

class PerplexityClient(BaseResearchClient):
    """Perplexity Sonar API 클라이언트"""

    def __init__(self):
        self.client = OpenAI(
            api_key=get_api_key("perplexity"),
            base_url="https://api.perplexity.ai"
        )

    async def research(self, query: str, context: Optional[str] = None) -> ResearchResult:
        response = self.client.chat.completions.create(
            model=get_perplexity_model(),  # sonar / sonar-pro
            messages=[
                {"role": "system", "content": FASHION_RESEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": self._build_prompt(query, context)}
            ],
            search_recency_filter="month"  # 최근 1개월 데이터 우선
        )
        return self._parse_response(response, query)
```

#### 3.2.4 glm_research_client.py

```python
from zhipuai import ZhipuAI

class GLMResearchClient(BaseResearchClient):
    """GLM 웹 리서치 클라이언트"""

    async def research(self, query: str, context: Optional[str] = None) -> ResearchResult:
        response = self.client.chat.completions.create(
            model="glm-4.7",
            messages=[
                {"role": "system", "content": FASHION_RESEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": self._build_prompt(query, context)}
            ],
            tools=[{"type": "web_search", "web_search": {"enable": True}}]
        )
        return self._parse_response(response, query)
```

### 3.3 Phase 3: AI 조사 서비스 구현

#### 3.3.1 ai_research_service.py

```python
class AIResearchService:
    """AI 직접 조사 오케스트레이터"""

    def __init__(self):
        self.gemini_client = GeminiResearchClient()
        self.perplexity_client = PerplexityClient()
        self.glm_client = GLMResearchClient()

    async def conduct_research(
        self,
        session_data: Dict[str, Any],
        keywords: List[str],
        progress_cb: ProgressCallback
    ) -> Dict[str, Any]:
        """
        맥락 기반 AI 조사 수행

        1. 세션 데이터에서 맥락 쿼리 생성
        2. 활성화된 모델들로 병렬 조사
        3. 결과 통합 및 정제
        """
        if not is_ai_research_enabled():
            return {"enabled": False, "results": []}

        # 맥락 쿼리 생성 (예: "2026년 봄여름 20~30대 여성 캐주얼 패션 트렌드")
        context_query = self._build_context_query(session_data, keywords)

        progress_cb("ai_research", 51, f"AI 조사 시작: {context_query[:50]}...")

        # 활성화된 모델들로 병렬 조사
        enabled_models = get_enabled_research_models()
        tasks = []

        if "gemini_search" in enabled_models:
            tasks.append(self._safe_research(self.gemini_client, context_query))
        if "perplexity" in enabled_models:
            tasks.append(self._safe_research(self.perplexity_client, context_query))
        if "glm_research" in enabled_models:
            tasks.append(self._safe_research(self.glm_client, context_query))

        results = await asyncio.gather(*tasks)
        valid_results = [r for r in results if r is not None]

        progress_cb("ai_research", 54, f"AI 조사 완료: {len(valid_results)}개 모델 응답")

        return {
            "enabled": True,
            "context_query": context_query,
            "results": valid_results,
            "merged_insights": self._merge_results(valid_results)
        }

    def _build_context_query(
        self,
        session_data: Dict[str, Any],
        keywords: List[str]
    ) -> str:
        """세션 데이터와 키워드로 맥락 쿼리 생성"""
        filters = session_data.get("filters") or {}

        parts = []

        # 시즌/연도
        if filters.get("season"):
            parts.append(filters["season"])

        # 타겟 연령대
        if filters.get("age_group"):
            parts.append(filters["age_group"])

        # 성별
        if filters.get("gender"):
            parts.append(filters["gender"])

        # 카테고리
        if filters.get("category"):
            parts.append(filters["category"])

        # 기본 키워드 추가
        if keywords:
            parts.extend(keywords[:3])

        # 패션 트렌드 전망 접미사
        base_query = " ".join(parts)
        return f"{base_query} 패션 트렌드 전망 분석"

    async def _safe_research(
        self,
        client: BaseResearchClient,
        query: str
    ) -> Optional[ResearchResult]:
        """안전한 조사 실행 (에러 처리 포함)"""
        try:
            if not client.is_available():
                return None
            return await client.research(query)
        except Exception as e:
            logger.warning(f"{client.__class__.__name__} research failed: {e}")
            return None

    def _merge_results(self, results: List[ResearchResult]) -> Dict[str, Any]:
        """여러 AI 조사 결과 통합"""
        if not results:
            return {}

        all_citations = []
        all_content = []

        for r in results:
            all_content.append(f"[{r.source}] {r.content}")
            all_citations.extend(r.citations)

        return {
            "combined_content": "\n\n".join(all_content),
            "all_citations": list(set(all_citations)),
            "source_count": len(results)
        }
```

### 3.4 Phase 4: 파이프라인 통합

#### 3.4.1 pipeline_orchestrator.py 수정

```python
class FashionPipelineOrchestrator:
    def __init__(self):
        # ... 기존 ...
        self.ai_research_service = AIResearchService()  # NEW

    async def run_complete_pipeline(self, ...):
        # ... 1~3단계 기존 ...

        # 3.5단계: AI 직접 조사 [NEW]
        ai_research = await self._conduct_ai_research(
            session_data, keywords, progress_cb
        )

        # 4단계: 트렌드 분석 (수정 - AI 조사 데이터 추가)
        analysis = await self._analyze_trends(
            session_data, crawled, keywords, ai_research, progress_cb
        )

        # ... 나머지 단계 기존 ...

        return {
            # ... 기존 ...
            "ai_research": ai_research,  # NEW
        }

    async def _conduct_ai_research(
        self,
        session_data: Dict[str, Any],
        keywords: List[str],
        progress_cb: ProgressCallback
    ) -> Dict[str, Any]:
        """3.5단계: AI 직접 조사"""
        return await self.ai_research_service.conduct_research(
            session_data, keywords, progress_cb
        )
```

#### 3.4.2 analysis_service.py 수정

```python
async def analyze_trends(
    self,
    raw_data: List[Dict[str, Any]],
    filters: Dict[str, Any],
    user_input: str,
    ai_research: Optional[Dict[str, Any]] = None  # NEW 파라미터
) -> Dict[str, Any]:
    """
    크롤러 데이터 + AI 조사 결과 통합 분석
    """
    # 기존 크롤러 데이터 분석
    crawler_analysis = await self._analyze_crawler_data(raw_data, filters, user_input)

    # AI 조사 결과가 있으면 통합
    if ai_research and ai_research.get("enabled"):
        return await self._integrate_research(crawler_analysis, ai_research)

    return crawler_analysis

async def _integrate_research(
    self,
    crawler_analysis: Dict[str, Any],
    ai_research: Dict[str, Any]
) -> Dict[str, Any]:
    """크롤러 분석 + AI 조사 결과 통합"""
    merged_insights = ai_research.get("merged_insights", {})

    # 통합 프롬프트로 최종 분석
    integration_prompt = f"""
    다음 두 가지 소스의 정보를 통합하여 패션 트렌드 분석을 완성하세요:

    [크롤러 수집 데이터 분석]
    {json.dumps(crawler_analysis, ensure_ascii=False, indent=2)}

    [AI 직접 조사 결과]
    {merged_insights.get('combined_content', '')}

    통합 시 고려사항:
    1. 양쪽에서 공통으로 언급된 트렌드는 신뢰도 높음
    2. 크롤러 데이터는 구체적 사례, AI 조사는 전반적 맥락 제공
    3. 상충되는 정보는 출처와 함께 명시
    4. 최종 인사이트는 양쪽 정보를 균형 있게 반영
    """

    # GLM으로 최종 통합 (기존 패턴 유지)
    response = await self.glm_client.generate_content(
        prompt=integration_prompt,
        system_prompt=TREND_ANALYSIS_SYSTEM_PROMPT
    )

    return parse_json(response.text)
```

### 3.5 Phase 5: 프론트엔드 UI 구현

#### 3.5.1 settings.html 수정 - AI 조사 섹션 추가

```html
<!-- AI 조사 설정 섹션 -->
<div class="settings-section" id="ai-research-section">
    <h3 data-i18n="settings.aiResearch.title">AI 조사 설정</h3>

    <!-- 전체 활성화 토글 -->
    <div class="setting-item">
        <label>
            <input type="checkbox" id="ai-research-enabled">
            <span data-i18n="settings.aiResearch.enable">AI 직접 조사 활성화</span>
        </label>
        <p class="hint" data-i18n="settings.aiResearch.hint">
            크롤러 수집 후 AI가 추가로 웹 검색하여 트렌드를 조사합니다
        </p>
    </div>

    <!-- 모델 선택 (체크박스) -->
    <div class="setting-item" id="research-models-group">
        <label data-i18n="settings.aiResearch.selectModels">조사에 사용할 모델</label>

        <div class="checkbox-group">
            <label>
                <input type="checkbox" id="research-gemini" value="gemini_search">
                Gemini (Google Search)
            </label>
            <label>
                <input type="checkbox" id="research-perplexity" value="perplexity">
                Perplexity (Sonar)
            </label>
            <label>
                <input type="checkbox" id="research-glm" value="glm_research">
                GLM (웹 리서치)
            </label>
        </div>
    </div>

    <!-- Perplexity API 키 입력 -->
    <div class="setting-item" id="perplexity-key-group">
        <label for="perplexity-api-key">Perplexity API Key</label>
        <input type="password" id="perplexity-api-key" placeholder="pplx-...">
        <button id="save-perplexity-key" class="btn-secondary">저장</button>
    </div>

    <!-- Perplexity 모델 선택 -->
    <div class="setting-item" id="perplexity-model-group">
        <label for="perplexity-model">Perplexity 모델</label>
        <select id="perplexity-model">
            <option value="sonar">Sonar (기본)</option>
            <option value="sonar-pro">Sonar Pro (고급)</option>
        </select>
    </div>

    <!-- 조사 깊이 설정 -->
    <div class="setting-item">
        <label for="research-depth">조사 깊이</label>
        <select id="research-depth">
            <option value="standard">표준 (빠른 조사)</option>
            <option value="deep">심층 (다중 검색)</option>
        </select>
    </div>
</div>
```

#### 3.5.2 세션 상세 페이지 - AI 조사 단계 표시

```html
<!-- 파이프라인 진행 표시에 3.5단계 추가 -->
<div class="pipeline-step" data-step="ai_research">
    <span class="step-icon">🔍</span>
    <span class="step-name" data-i18n="pipeline.aiResearch">AI 조사</span>
    <span class="step-status"></span>
</div>
```

---

## 4. 엣지 케이스

1. **API 키 미설정**: 해당 모델 건너뜀, 로그 기록
2. **모든 모델 비활성화**: AI 조사 단계 스킵, 기존 파이프라인 유지
3. **API 호출 실패**: 개별 모델 실패 시 다른 모델 결과만 사용
4. **API 할당량 초과**: 명확한 에러 메시지, 재시도 안내
5. **검색 결과 없음**: 빈 결과 처리, 크롤러 데이터만으로 분석 진행
6. **응답 시간 초과**: 30초 타임아웃, 부분 결과 사용
7. **중복 인용**: citations 중복 제거
8. **언어 불일치**: 한국어 쿼리에 영어 결과 시 번역 처리

---

## 5. 구현 순서 및 체크리스트

### Phase 1: 설정 인프라 (우선순위: 높음)
- [ ] settings_storage.py에 AI 조사 설정 추가
- [ ] Perplexity API 키 저장 함수 추가
- [ ] 설정 API 엔드포인트 확장
- [ ] 단위 테스트 작성

### Phase 2: AI 클라이언트 (우선순위: 높음)
- [ ] base_research_client.py 생성
- [ ] gemini_research_client.py 구현
- [ ] perplexity_client.py 구현
- [ ] glm_research_client.py 구현
- [ ] 각 클라이언트 단위 테스트

### Phase 3: AI 조사 서비스 (우선순위: 높음)
- [ ] ai_research_service.py 생성
- [ ] 맥락 쿼리 생성 로직 구현
- [ ] 병렬 조사 실행 구현
- [ ] 결과 통합 로직 구현
- [ ] 통합 테스트

### Phase 4: 파이프라인 통합 (우선순위: 중간)
- [ ] pipeline_orchestrator.py 수정
- [ ] analysis_service.py 수정 (통합 분석)
- [ ] 진행률 표시 업데이트
- [ ] E2E 테스트

### Phase 5: 프론트엔드 (우선순위: 중간)
- [ ] settings.html AI 조사 섹션 추가
- [ ] settings.js 로직 추가
- [ ] 세션 상세 페이지 단계 표시 추가
- [ ] 다국어 번역 키 추가 (ko, en, zh-CN, zh-TW)
- [ ] UI 테스트

---

## 6. 테스트 계획

### 6.1 단위 테스트
```python
# tests/test_ai_research.py
def test_gemini_research_client(): ...
def test_perplexity_client(): ...
def test_glm_research_client(): ...
def test_context_query_generation(): ...
def test_result_merging(): ...
```

### 6.2 통합 테스트
```python
# tests/test_pipeline_with_research.py
async def test_full_pipeline_with_ai_research(): ...
async def test_pipeline_without_ai_research(): ...
async def test_partial_model_failure(): ...
```

### 6.3 E2E 테스트
1. 설정 페이지에서 AI 조사 활성화
2. Perplexity API 키 저장
3. Gemini + Perplexity 모델 선택
4. 새 세션 생성 및 파이프라인 실행
5. AI 조사 단계 진행 확인
6. 최종 분석에 AI 조사 결과 포함 확인

---

## 7. 완료 기준

1. **기능적 완료**
   - [ ] 3개 AI 검색 서비스 모두 정상 동작
   - [ ] 설정에서 개별 모델 활성화/비활성화 가능
   - [ ] 파이프라인에서 AI 조사 단계 정상 실행
   - [ ] 크롤러 + AI 조사 결과 통합 분석 완료

2. **비기능적 완료**
   - [ ] AI 조사 비활성화 시 기존 파이프라인과 동일 동작
   - [ ] API 실패 시 graceful degradation
   - [ ] 진행률 표시 정확
   - [ ] 에러 메시지 명확

3. **문서화**
   - [ ] API 키 설정 가이드
   - [ ] 모델별 특성 및 비용 안내
   - [ ] 트러블슈팅 가이드

---

## 8. 비용 고려사항

| 시나리오 | Gemini | Perplexity | GLM | 총 비용/세션 |
|----------|--------|------------|-----|-------------|
| 전체 활성화 | $0.014 | $0.005 | ~$0.002 | ~$0.021 |
| Perplexity만 | - | $0.005 | - | $0.005 |
| GLM만 | - | - | ~$0.002 | ~$0.002 |

**권장**: 비용 최적화를 위해 GLM 또는 Perplexity 단독 사용 옵션 제공

---

## 9. 향후 확장 가능성

1. **추가 검색 서비스**: OpenAI 검색, Bing API 등
2. **검색 결과 캐싱**: 동일 쿼리 재사용
3. **커스텀 도메인 필터**: 패션 전문 사이트만 검색
4. **조사 이력 저장**: 세션별 AI 조사 결과 아카이브
5. **사용자 피드백**: AI 조사 품질 평가 수집
