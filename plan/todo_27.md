# Todo 27: AI 직접 조사 파이프라인 통합

**작성일**: 2025-12-24 10:30
**연관 계획**: plan_27.md

---

## Phase 1: 설정 인프라 구축

### 1.1 settings_storage.py 수정
- [x] AVAILABLE_MODELS에 "research" 섹션 추가
- [x] DEFAULT_SETTINGS에 "ai_research" 섹션 추가
- [x] DEFAULT_SETTINGS.api_keys에 "perplexity" 추가
- [x] get_ai_research_config() 함수 구현 (ai_research_service.py)
- [x] save_ai_research_config() 함수 구현 (ai_research_service.py)
- [x] is_ai_research_enabled() 함수 구현
- [x] get_enabled_research_models() 함수 구현
- [x] get_perplexity_model() 함수 구현

### 1.2 설정 API 엔드포인트
- [x] app/api/settings_ui.py에 GET /ai-research 추가
- [x] app/api/settings_ui.py에 POST /ai-research 추가
- [x] AIResearchConfig Pydantic 모델 정의 (settings_shared.py)

### 1.3 Phase 1 테스트
- [x] 설정 저장/로드 테스트 (정적 검증)
- [x] API 엔드포인트 테스트 (정적 검증)

---

## Phase 2: AI 연구 클라이언트 구현

### 2.1 기반 구조
- [x] ai_clients/research/ 디렉토리 생성
- [x] ai_clients/research/__init__.py 생성
- [x] ai_clients/research/base_research_client.py 구현
  - [x] ResearchResult 데이터클래스
  - [x] BaseResearchClient ABC

### 2.2 Gemini 검색 클라이언트
- [x] ai_clients/research/gemini_research_client.py 생성
- [x] google-genai 패키지 확인/설치
- [x] Grounding with Google Search 구현
- [x] 응답 파싱 로직 구현
- [x] is_available() 구현

### 2.3 Perplexity 클라이언트
- [x] ai_clients/research/perplexity_client.py 생성
- [x] openai 패키지 활용 (호환 API)
- [x] Sonar/Sonar Pro 모델 지원
- [x] search_recency_filter 적용
- [x] citations 파싱 구현

### 2.4 GLM 연구 클라이언트
- [x] ai_clients/research/glm_research_client.py 생성
- [x] 기존 glm_client.py 활용
- [x] web_search 도구 활성화
- [x] 응답 파싱 로직 구현

### 2.5 Phase 2 테스트
- [x] 각 클라이언트 개별 테스트 (정적 검증)
- [x] API 키 없을 때 동작 테스트 (정적 검증)
- [x] 에러 핸들링 테스트 (정적 검증)

---

## Phase 3: AI 조사 서비스 구현

### 3.1 서비스 구현
- [x] app/services/ai_research_service.py 생성
- [x] AIResearchService 클래스 구현
- [x] _build_context_query() 메서드 구현
- [x] conduct_research() 메서드 구현
- [x] _safe_research() 메서드 구현
- [x] _merge_results() 메서드 구현

### 3.2 맥락 쿼리 생성 로직
- [x] 필터(시즌/연령대/성별/카테고리) 반영
- [x] 키워드 통합
- [x] 패션 트렌드 접미사 추가

### 3.3 Phase 3 테스트
- [x] 맥락 쿼리 생성 테스트 (정적 검증)
- [x] 병렬 조사 테스트 (정적 검증)
- [x] 결과 통합 테스트 (정적 검증)
- [x] 부분 실패 시나리오 테스트 (정적 검증)

---

## Phase 4: 파이프라인 통합

### 4.1 pipeline_orchestrator.py 수정
- [x] AIResearchService import 추가
- [x] __init__에 ai_research_service 초기화
- [x] _conduct_ai_research() 메서드 추가
- [x] run_complete_pipeline() 흐름 수정
  - [x] 3.5단계 AI 조사 호출 추가
  - [x] 반환값에 ai_research 추가
- [x] 진행률 콜백 업데이트 (51~54%)

### 4.2 analysis_service.py 수정
- [x] analyze_trends()에 ai_research 파라미터 추가
- [x] _perform_final_synthesis()에서 ai_research 통합 구현
- [x] 통합 분석 로직 추가

### 4.3 Phase 4 테스트
- [x] AI 조사 활성화 시 전체 파이프라인 테스트 (정적 검증)
- [x] AI 조사 비활성화 시 기존 동작 확인 (정적 검증)
- [x] 진행률 표시 정확성 확인 (정적 검증)

---

## Phase 5: 프론트엔드 UI

### 5.1 설정 페이지 (settings.html)
- [x] AI 조사 설정 섹션 HTML 추가
- [x] 전체 활성화 토글
- [x] 모델 선택 체크박스 (Gemini/Perplexity/GLM)
- [x] Perplexity API 키 입력 필드
- [x] Perplexity 모델 선택 드롭다운
- [x] 조사 깊이 선택

### 5.2 설정 페이지 JavaScript (settings.html)
- [x] AI 조사 설정 로드 로직 (loadAIResearchSettings)
- [x] AI 조사 설정 저장 로직 (saveAIResearchSettings)
- [x] Perplexity API 키 저장 로직 (saveApiKeys에 추가)
- [x] 모델 선택 상태 관리
- [x] DOMContentLoaded/languageChanged 이벤트 연결

### 5.3 세션 상세 페이지
- [ ] 파이프라인 단계에 "AI 조사" 추가 (선택사항, 진행률만 반영)
- [ ] AI 조사 결과 표시 영역 (선택적)

### 5.4 다국어 지원
- [x] ko.json에 AI 조사 관련 키 추가
- [x] en.json에 AI 조사 관련 키 추가
- [x] zh-CN.json에 AI 조사 관련 키 추가
- [x] zh-TW.json에 AI 조사 관련 키 추가

### 5.5 Phase 5 테스트
- [x] 설정 저장/로드 UI 테스트 (정적 검증)
- [ ] 세션 실행 시 단계 표시 테스트
- [ ] 반응형 레이아웃 확인

---

## Phase 6: 통합 테스트 및 문서화

### 6.1 E2E 테스트
- [ ] 전체 시나리오 테스트 (모든 모델 활성화)
- [ ] Perplexity만 활성화 테스트
- [ ] GLM만 활성화 테스트
- [ ] AI 조사 비활성화 테스트
- [ ] API 키 오류 시나리오 테스트

### 6.2 엣지 케이스 테스트
- [ ] API 키 미설정 시 동작
- [ ] 모든 모델 실패 시 동작
- [ ] 타임아웃 시나리오
- [ ] 빈 검색 결과 처리

### 6.3 성능 테스트
- [ ] AI 조사 응답 시간 측정
- [ ] 병렬 처리 효율성 확인
- [ ] 메모리 사용량 확인

### 6.4 문서화
- [x] worksheet.md 업데이트
- [ ] 사용자 가이드 작성 (선택적)

---

## 완료 체크리스트

### 필수 완료 항목
- [x] 3개 AI 검색 서비스 구현 완료
- [x] 설정에서 개별 모델 활성화/비활성화 가능
- [x] 파이프라인 구조 수정 완료
- [x] 크롤러 + AI 조사 결과 통합 분석
- [x] AI 조사 비활성화 시 기존 동작 유지
- [x] API 실패 시 graceful degradation
- [x] 진행률 표시 정확

### 선택 완료 항목
- [ ] 조사 결과 상세 표시 UI
- [ ] 비용 추적 기능
- [ ] 검색 결과 캐싱
