# SPEC-06-ADMIN-CONSOLE Research

## 1. 현재 admin_console 구현 상태

### 구현 완료 (Back-End)
- **Domain layer**: `entities.py` — AdminRole(3종), AdminPermission, AdminSession, MetricsSummary, PolicyChangeLogEntry
- **Application layer**: `use_cases.py` — 11개 use case: GetAdminDashboard, GetMetrics, GetPolicyDetail, EditPolicy, RollbackPolicy, SearchAuditLogs, GetJobQueue 등
- **Infrastructure**: `repositories.py` — ModelCatalogRepository, PolicyRepository, AuditLogRepository, MetricsRepository, JobQueueRepository, PolicyChangeLogRepository
- **Presentation**: `views.py` (1187 lines), `urls.py` — 12개 route 완성

### 구현 완료 (Front-End Templates)
위치: `apps/admin_console/presentation/templates/admin/`
- base.html, dashboard.html, providers.html, models.html
- policies.html, prompt_policies.html, metrics.html
- audit_logs.html, job_queue.html, rollback.html

### CSS/JS 파일 (기 생성됨)
- `/static/admin_console/css/admin.css` (496 lines)
- `/static/admin_console/js/admin.js` (375 lines)
- `/static/css/pages/admin.css` (492 lines)
- `/static/js/pages/admin.js` (477 lines)

---

## 2. 현재 구현의 결함/미완성 목록

### 2.1 Critical Breaks (런타임 에러)
1. **CSS 경로 불일치**: `base.html`이 `/static/css/admin.css`를 참조하지만 실제 파일은 `/static/admin_console/css/admin.css`에 있음
2. **JS 경로 불일치**: `base.html`이 `/static/js/admin/main.js`를 참조하지만 파일 없음
3. **LoginRequiredMixin**: `AdminViewMixin`에 적용 중 → 로그인 없는 개발 환경에서 차단
4. **Template filter 미등록**: `{{ 'key'|i18n }}` 형식의 커스텀 filter가 Django에 등록되지 않음 (dashboard.html 등)
5. **URL 참조 오류**: `{% url 'settings' %}`, `{% url 'logout' %}` → admin namespace에 없음
6. **`urls_admin.py`에 HTML page 라우트 없음**: API 엔드포인트만 있고 HTML 페이지 서빙 URL이 없음

### 2.2 누락된 기능
1. **세션 파이프라인 모니터링 화면**: 모든 세션의 실시간 상태 조회 화면 없음 (가장 중요)
2. **Celery 워커 상태 표시**: 현재 job_queue는 Generation Job만 보여줌, Celery worker 상태 없음
3. **API 키 유효성 테스트**: Provider 화면에서 실제 key 동작 여부 확인 불가
4. **비용/토큰 트렌드 차트**: 현재 숫자만 표시, 시계열 차트 없음
5. **메트릭 Export**: CSV 내보내기 없음
6. **시스템 헬스 디테일**: `system_health` 딕셔너리가 실제 데이터 없이 placeholder

---

## 3. 모니터링 대상 (전체 프로그램 관점)

### 3.1 세션 파이프라인 (design_sessions)
SessionStatus 값 9개:
- QUEUED → RESEARCHING → CONCEPTING → REFERENCING → ABSTRACTING → GENERATING → DOCUMENTING → REVIEW_READY (terminal)
- FAILED (재시도 가능)

PipelineStep 17개 (1=PURPOSE_INPUT, …, 17=REVIEW):
- Steps 1-4: QUEUED
- Step 5: RESEARCHING
- Steps 6-8: CONCEPTING
- Steps 9-10: REFERENCING
- Steps 11-12: ABSTRACTING
- Steps 13-15: GENERATING
- Step 16: DOCUMENTING
- Step 17: REVIEW_READY

모니터링 필요 항목: 세션 상태, 현재 step, 소요 시간, 오류 메시지, 재시도 횟수

### 3.2 Generation Job Queue
Status: QUEUED → RUNNING → COMPLETED | FAILED | CANCELLED
Job 종류: SKETCH, REFINEMENT, VARIATION, DOMAIN_APPLICATION
메트릭: prompt_tokens, completion_tokens, cost_usd per job

### 3.3 LLM 모델 호출 메트릭 (model_catalog)
- per feature_key: invocation count, success/fail, avg latency, cost
- ModelInvocation entity: tokens_in, tokens_out, cost_estimate, latency_ms, error_code
- Fallback 체인 추적: primary → fallback1 → fallback2

### 3.4 Reference/Crawler 수집
- ReferenceAsset: provider (unsplash/pexels/pixabay 등), tier 1/2/3
- 수집 수량, license_risk 분포

---

## 4. LLM 모델 설정 백엔드 구조

### ModelProvider
```
id (string PK), name (unique), api_key_env (env var name),
base_url, endpoint_path, auth_scheme (BEARER/API_KEY/BASIC/CUSTOM), active
```

### ModelCatalog
```
id (string PK), provider_id (FK), model_name, type (TEXT/CHAT/VISION/IMAGE/SEARCH/EMBEDDING/MULTIMODAL),
context_limit, cost_estimate (USD/1M tokens), modalities, active
```

### FeatureModelPolicy (9개 feature_key)
```
feature_key, primary_model_id (FK ModelCatalog), fallback_model_ids (list),
parameters (JSON: temperature, top_p 등), max_cost_per_call, max_tokens,
version (int), active (1개만 active per feature_key)
```

### PromptPolicy
```
feature_key, prompt_version, system_prompt, user_template,
active, reviewer, created_at
```

---

## 5. 사용자 페이지 디자인 패턴 (일관성 기준)

### CSS
- `/static/css/design-system.css` 공유 (CSS 변수: `--color-primary`, `--border-color`, `--bg-primary` 등)
- 기존 admin base.html은 data-theme="light" 지원 (사용자 페이지와 동일)

### HTML 패턴
- `data-i18n="key"` 속성으로 i18n
- Skeleton loading: `{% if skeleton %}...{% endif %}`
- 오류 상태: context에 `error` key 포함 여부로 분기

### JS 패턴 (user page)
- IIFE `(function() { ... })()` 모듈 패턴
- `window.dashboardState` 상태 공유
- `window._t(key, params)` i18n 함수
- `fetch('/api/v1/...')` + `escapeHtml()`

---

## 6. 벤치마킹 — 유사 서비스 분석

### Langfuse (LLM Observability)
- Traces 테이블: request, response, latency, cost
- Generations 뷰: 모델별 토큰/비용 추이
- Sessions 그룹핑: 연관 호출 묶음
- Prompt management: 버전 관리 + A/B 테스트

### OpenAI Platform
- Usage dashboard: 일/월별 토큰/비용 차트
- API keys 관리: key별 사용량 추적
- Rate limits 표시

### Celery Flower
- Worker 목록 + active/idle 상태
- Task rate (tasks/sec) 실시간
- 실패 태스크 traceback 조회
- Retry/revoke 액션

### n8n / Flowise
- Workflow execution history
- Step-by-step 타이밍 뷰
- 오류 노드 하이라이트
- 재시도 워크플로

### 공통 패턴 요약
1. 상태 칩 (color-coded: green/yellow/red/gray)
2. 시계열 차트 (최소 7일, 최대 30일)
3. 테이블 + 검색/필터 + 페이지네이션
4. 드릴다운 (행 클릭 → 상세)
5. 인라인 액션 (재시도, 취소, 롤백)
6. 실시간 폴링 (1~5초 간격, 토글 가능)
7. 알림/배지 (에러 수, 대기 중 작업)
8. Export (CSV/JSON)

---

## 7. 핵심 제약

- **로그인 없음**: 개발 단계, auth bypass 필요 (LoginRequiredMixin 제거 또는 미적용 믹스인으로 교체)
- **포트 14001**: `config/urls_admin.py`에 HTML page 라우트 추가 필요
- **디자인 일관성**: `/static/css/design-system.css` 공유, i18n 패턴 동일
- **정적파일 경로**: `/static/admin_console/` 경로로 통일
- **실시간 요구사항**: WebSocket 불필요, 5-10초 polling으로 충분
- **사용자 계정 관리**: Out of scope (나중에 구현)
