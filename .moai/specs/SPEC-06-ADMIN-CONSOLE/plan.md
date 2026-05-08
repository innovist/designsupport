---
id: SPEC-06-ADMIN-CONSOLE
artifact: plan
version: 0.1.0
created: 2026-05-08
updated: 2026-05-08
---

# SPEC-06-ADMIN-CONSOLE — Implementation Plan

## 1. Plan Overview

본 계획은 6개 모듈(INFRA, SESSION-MONITOR, DASHBOARD, MODEL-CONFIG, METRICS, JOB-MONITOR)을 우선순위 기반으로 6개 Phase로 분할하여 진행한다. Phase 1(INFRA)이 완료되어야 콘솔 자체에 접근 가능하므로 반드시 선행되어야 한다. 이후 Phase 2~6은 모듈별로 분리 진행 가능하나, 본 계획은 운영 가치가 큰 순서(세션 가시화 → 대시보드 → 정책 → 메트릭 → 잡)로 정렬한다.

### 1.1 Priority Map

| Phase | 모듈 | Priority | 선행 조건 |
|-------|------|----------|----------|
| Phase 1 | REQ-06-INFRA | P0 (Critical) | 없음 |
| Phase 2 | REQ-06-SESSION-MONITOR | P0 | Phase 1 완료 |
| Phase 3 | REQ-06-DASHBOARD | P1 | Phase 1 완료 |
| Phase 4 | REQ-06-MODEL-CONFIG | P1 | Phase 1 완료, SPEC-04 백엔드 검증 |
| Phase 5 | REQ-06-METRICS | P2 | Phase 1, 3 완료 |
| Phase 6 | REQ-06-JOB-MONITOR | P2 | Phase 1 완료 |

### 1.2 Milestones

- **M1 — Console Accessible**: Phase 1 완료. 14001 포트에서 모든 admin 페이지가 200 OK 응답
- **M2 — Operational Visibility**: Phase 2, 3 완료. 세션/대시보드를 통한 실시간 운영 모니터링 가능
- **M3 — Policy Manageable**: Phase 4 완료. LLM 모델/정책을 UI에서 안전하게 변경 가능
- **M4 — Cost Observable**: Phase 5 완료. 비용/토큰 트렌드 차트 및 CSV Export 가능
- **M5 — Job Lifecycle Controllable**: Phase 6 완료. 워커 상태 가시화 및 잡 재시도/취소 가능

---

## 2. Phase 1 — Critical Infra Fixes (REQ-06-INFRA)

### 2.1 목표

콘솔 접근을 막는 6개 결함을 일괄 제거. Phase 1 완료 후 모든 admin URL이 401/404/500 없이 200 OK를 응답해야 한다.

### 2.2 작업 항목 (수정 파일)

| # | 작업 | 파일 |
|---|------|------|
| 1.1 | base.html의 CSS/JS 경로를 `/static/admin_console/css/admin.css`, `/static/admin_console/js/admin.js`로 수정 | `apps/admin_console/presentation/templates/admin/base.html` |
| 1.2 | `urls_admin.py`에 HTML 페이지 라우트 10개 등록 (dashboard, providers, models, policies, prompt_policies, metrics, audit_logs, job_queue, rollback, sessions) | `config/urls_admin.py` |
| 1.3 | views.py 클래스에서 `LoginRequiredMixin` 상속 제거 또는 settings 기반 토글 (인증 비활성화) | `apps/admin_console/presentation/views.py` |
| 1.4 | 커스텀 템플릿 필터 `i18n` 등록 — 신규 templatetags 모듈 작성 | `apps/admin_console/presentation/templatetags/admin_i18n.py` (신규), `__init__.py` |
| 1.5 | base.html의 `{% url 'settings' %}`, `{% url 'logout' %}` → admin namespace로 prefix하거나 No-op 라우트 정의 | `apps/admin_console/presentation/templates/admin/base.html`, `urls_admin.py` |
| 1.6 | INSTALLED_APPS에 admin_console이 포함되어 있는지, STATICFILES 경로가 collectstatic 대상인지 확인 | `config/settings/dev.py` |

### 2.3 기술적 결정

- **인증 우회 방식**: `LoginRequiredMixin`을 코드에서 완전히 제거하지 않고, `settings.ADMIN_CONSOLE_AUTH_ENABLED = False`(기본 False) 토글로 분기. 향후 인증 도입 시 토글만 True로 전환 가능.
- **i18n 필터**: 별도 외부 패키지 도입하지 않고, dict 기반의 단순 lookup 필터를 templatetags에 직접 구현(거짓 fallback 없이 미정의 키는 키 자체를 그대로 출력하여 누락 즉시 가시화).
- **URL namespace**: `app_name = 'admin'`을 `urls_admin.py`에 명시하여 `{% url 'admin:dashboard' %}` 패턴으로 일관화.

### 2.4 위험 (Risk)

| Risk | Mitigation |
|------|-----------|
| LoginRequiredMixin 제거가 다른 미인증 보호 로직(데코레이터 등)을 함께 무력화할 수 있음 | views.py에 grep으로 `login_required`, `permission_required` 흔적 모두 점검 후 토글 통일 |
| 정적 파일 경로 변경이 사용자 페이지(14000)에 영향 가능 | 사용자 페이지는 `/static/css/`, `/static/js/` 사용 — 경로 분리되어 있어 무영향. collectstatic 후 staging 검증 |
| URL namespace 변경 시 기존 admin API endpoint reverse가 깨짐 | API URL은 namespace 미적용 영역에 유지하고, HTML 페이지 URL만 namespace 적용 |

### 2.5 완료 기준

- 14001 포트에서 `/admin/`, `/admin/providers/`, `/admin/models/`, `/admin/policies/`, `/admin/prompt_policies/`, `/admin/metrics/`, `/admin/audit_logs/`, `/admin/job_queue/`, `/admin/rollback/` 모두 200 응답
- 브라우저 DevTools Network 탭에서 admin.css, admin.js 200 응답
- 콘솔에 i18n 필터 미등록 오류 부재

---

## 3. Phase 2 — Session Pipeline Monitor (REQ-06-SESSION-MONITOR) [신규]

### 3.1 목표

세션 9개 status, 17개 pipeline step의 실시간 가시화. 본 모듈은 본 SPEC에서 신설되는 유일한 신규 화면이다.

### 3.2 작업 항목

| # | 작업 | 파일 |
|---|------|------|
| 2.1 | 세션 목록 + 검색/필터/페이지네이션 화면 템플릿 작성 | `apps/admin_console/presentation/templates/admin/sessions.html` (신규) |
| 2.2 | 세션 목록 조회 view (HTML) + JSON API endpoint(`/admin/api/sessions/`) | `apps/admin_console/presentation/views.py` (SessionMonitorView 추가) |
| 2.3 | 세션 drill-down(17 step 상태) JSON API endpoint(`/admin/api/sessions/<id>/steps/`) | `views.py` |
| 2.4 | 세션 페이지 IIFE JS 모듈: 5초 폴링, drill-down 패널, status chip 렌더링 | `static/admin_console/js/pages/sessions.js` (신규) |
| 2.5 | session status별 chip 색상 CSS 변수 정의 (사용자 페이지 design-system.css 변수 재사용) | `static/admin_console/css/admin.css` (확장) |
| 2.6 | base.html 사이드바 navigation에 "Sessions" 메뉴 항목 추가 | `base.html` |

### 3.3 기술적 결정

- **데이터 소스**: 도메인 레이어의 SessionRepository를 application service에서 호출. presentation은 service 결과만 직렬화.
- **폴링 vs WebSocket**: 본 단계는 setInterval(5s) 폴링. WebSocket은 비범위.
- **실패 시 fallback**: 폴링 실패 시 마지막 정상 데이터 유지 + 토스트 경고. 거짓 데이터/0 치환 절대 금지(CLAUDE.md 운영 룰).
- **drill-down 데이터 모델**: pipeline_step 테이블이 별도 존재하지 않으면 SessionStateLog/Event 모델에서 step 단위로 집계.

### 3.4 위험

| Risk | Mitigation |
|------|-----------|
| 세션이 수천 건일 때 리스트 쿼리 부하 | 서버사이드 페이지네이션(50/page) + status chip 카운트는 GROUP BY 별도 경량 쿼리 |
| pipeline step 데이터 모델이 17 step을 명시적으로 표현하지 않을 수 있음 | research.md 기준 step 정의를 매핑 헬퍼로 정규화. 매핑 누락 시 "unknown step" 명시 표시 |
| drill-down 패널이 모바일에서 깨질 수 있음 | 데스크톱 우선(>=1280px). 모바일은 비범위(SPEC §1.3) |

### 3.5 완료 기준

- 50건 이상의 mock 세션이 있는 환경에서 화면이 1.5s 이내 초기 렌더
- status chip 합계 = 전체 세션 수 일치
- failed 세션 행에 Retry 버튼 노출
- 5초마다 데이터 자동 갱신 확인

---

## 4. Phase 3 — Dashboard Real Data Wiring (REQ-06-DASHBOARD)

### 4.1 목표

대시보드의 KPI 카드와 system health 영역을 placeholder dict에서 실측 데이터로 전환.

### 4.2 작업 항목

| # | 작업 | 파일 |
|---|------|------|
| 3.1 | DashboardView의 get_context_data에서 실제 KPI 쿼리 호출 (active_sessions, jobs_24h, cost_24h, active_providers) | `views.py` |
| 3.2 | system_health 측정 모듈: DB ping, Redis ping, Celery broker ping, active worker count | `apps/admin_console/application/health_check.py` (신규) |
| 3.3 | health check 결과를 dashboard context에 주입하는 use case 작성 | `apps/admin_console/application/dashboard_service.py` (신규 또는 확장) |
| 3.4 | 예산(budget) 한도 정의 — settings 또는 ENV(`MOAI_DAILY_BUDGET_USD`)에서 로드, progress bar 데이터 산출 | `views.py`, `settings/dev.py` |
| 3.5 | dashboard.html에서 KPI 카드 및 health 영역 렌더링 (placeholder 제거) | `templates/admin/dashboard.html` |
| 3.6 | KPI 폴링 JS (10초 간격, optional) | `static/admin_console/js/pages/dashboard.js` (신규) |

### 4.3 기술적 결정

- **health check 비용 방지**: 매 페이지 로드마다 ping을 실행하면 부하 증가. cache.set(health, ttl=10s)로 짧은 캐시 적용.
- **timeout 처리**: 각 ping은 1초 timeout. 초과 시 해당 항목만 fail로 표시(전체 페이지 차단 금지).
- **거짓 fallback 금지**: 측정 실패 시 KPI는 "Error" 표시. 0 또는 임의 값으로 치환 금지.

### 4.4 위험

| Risk | Mitigation |
|------|-----------|
| Celery inspect 호출이 broker 부하를 유발 | 캐시 TTL 10초 적용, ping은 lightweight inspect.active_queues 만 사용 |
| 24h 비용 집계 쿼리가 느림 | invocation 로그 테이블에 (created_at, cost) 인덱스 사전 확인 |

### 4.5 완료 기준

- 대시보드 KPI 4개 모두 실측 값
- system health 4개 항목이 색상 chip으로 표시되며 마지막 점검 timestamp 노출
- 예산 progress bar는 환경변수 정의 시에만 표시, 미정의 시 숨김

---

## 5. Phase 4 — Model Config UI Improvements (REQ-06-MODEL-CONFIG)

### 5.1 목표

기존 Provider/Catalog/Policy 화면을 보강하여 (a) API Key 테스트 (b) 정책 영향 미리보기 (c) 검증 강화를 추가.

### 5.2 작업 항목

| # | 작업 | 파일 |
|---|------|------|
| 4.1 | API Key 테스트 endpoint(`/admin/api/providers/<id>/test/`) — Provider별 ping/min-completion 호출 | `views.py`, `apps/admin_console/application/provider_health.py` (신규) |
| 4.2 | providers.html에 "Test" 버튼 + 결과 모달 (latency, status, error) | `templates/admin/providers.html`, `static/admin_console/js/pages/providers.js` (신규) |
| 4.3 | Feature Policy 저장 시 version 자동 증가 + 직전 active=false 자동 처리 use case 보강 | `apps/admin_console/application/policy_service.py` |
| 4.4 | Policy 변경 미리보기: 선택 모델의 cost_estimate(USD/1k tokens) 비교 표시 | `templates/admin/policies.html`, `static/admin_console/js/pages/policies.js` |
| 4.5 | 비활성 ModelCatalog를 primary로 지정 불가 검증 (도메인 또는 응용 레이어) | `apps/admin_console/application/policy_service.py` |
| 4.6 | api_key_env는 노출하되 실제 키 값은 서버 응답에 절대 포함하지 않도록 시리얼라이저 점검 | `apps/admin_console/presentation/serializers.py` (또는 해당 파일) |

### 5.3 기술적 결정

- **API Key 테스트**: provider별 client 추상화(IModelClient.health_check())를 사용. 신규 의존성 추가 없이 기존 client 인프라 재사용.
- **버저닝**: Policy 저장 시 version=max(existing)+1, 직전 active=False로 transaction 묶음. audit log에 before/after JSON 기록.
- **검증 위치**: 도메인 레이어 invariant로 정의(비활성 모델 참조 금지). 응용 레이어는 검증 결과 변환만 담당.

### 5.4 위험

| Risk | Mitigation |
|------|-----------|
| API Key 테스트가 외부 호출 비용 발생 | 하루 호출 횟수 제한(rate limit) — 동일 provider 60s 1회 |
| Policy 버저닝 race condition (동시 저장) | DB transaction + select_for_update로 동시성 제어 |

### 5.5 완료 기준

- 모든 활성 Provider에 대해 "Test" 클릭 → 5초 내 결과 표시
- Policy 변경 후 invocation 로그에 새 모델로 호출된 흔적 확인
- 비활성 모델을 primary로 저장 시도 → 저장 거부 + 명시적 에러 메시지

---

## 6. Phase 5 — Metrics Charts & Export (REQ-06-METRICS)

### 6.1 목표

비용/토큰 트렌드 차트 도입과 CSV Export 기능 추가.

### 6.2 작업 항목

| # | 작업 | 파일 |
|---|------|------|
| 5.1 | metrics 트렌드 집계 API(`/admin/api/metrics/trend/?range=7d|30d`) — 일별 cost, input_tokens, output_tokens | `views.py`, `apps/admin_console/application/metrics_service.py` |
| 5.2 | feature_key별 집계 API(`/admin/api/metrics/by_feature/?range=...`) — 호출 수, 성공률, avg_latency, total_cost | `views.py`, `metrics_service.py` |
| 5.3 | CSV Export endpoint(`/admin/api/metrics/export.csv?...`) — UTF-8 BOM, 헤더 영문 통일 | `views.py` |
| 5.4 | Chart.js v4 CDN을 base.html 또는 metrics.html에 로드 | `templates/admin/metrics.html` 또는 `base.html` |
| 5.5 | metrics.html에 라인차트 2개(cost, tokens), feature 테이블, range 선택 컨트롤 추가 | `templates/admin/metrics.html` |
| 5.6 | metrics.js IIFE 모듈: Chart 인스턴스 생성/업데이트, 스켈레톤 로딩 | `static/admin_console/js/pages/metrics.js` (신규) |

### 6.3 기술적 결정

- **CDN 의존성**: Chart.js v4 jsdelivr CDN 사용. 오프라인 환경 비요구로 CDN 채택. 추후 self-host 필요 시 별도 SPEC.
- **집계 성능**: 일별 집계는 DB GROUP BY date_trunc('day', created_at) 활용. 30일 데이터는 < 1000 row 수준이므로 인덱스 충분.
- **CSV 한글 헤더 vs 영문**: SPEC §8 Q5 결정 필요. 본 계획은 영문 헤더 default(글로벌 호환).

### 6.4 위험

| Risk | Mitigation |
|------|-----------|
| Chart.js CDN 차단 환경 | 폴백 메시지 표시 + self-host 옵션 후속 SPEC |
| 빈 결과 fallback 거짓 데이터 위험 | 빈 결과 시 차트 영역에 "No data" empty state 명시 표시 |

### 6.5 완료 기준

- 7d/30d toggle 시 < 200ms 차트 갱신
- CSV Export 파일을 Excel에서 한글 깨짐 없이 열림
- feature 테이블이 9개 feature_key 모두 표시

---

## 7. Phase 6 — Job Queue + Celery Worker Status (REQ-06-JOB-MONITOR)

### 7.1 목표

기존 job_queue 화면을 보강하여 Celery 워커 상태 가시화 및 retry/cancel inline action을 추가.

### 7.2 작업 항목

| # | 작업 | 파일 |
|---|------|------|
| 6.1 | Celery worker 상태 조회 모듈 — `app.control.inspect()` 활용, 캐시 TTL 10s | `apps/admin_console/application/worker_status.py` (신규) |
| 6.2 | job_queue.html에 워커 상태 패널(워커 수, hostname, processing tasks, last heartbeat) 추가 | `templates/admin/job_queue.html` |
| 6.3 | Job retry endpoint(`/admin/api/jobs/<id>/retry/`) — Celery 재큐잉 + audit log | `views.py`, `apps/admin_console/application/job_service.py` |
| 6.4 | Job cancel endpoint(`/admin/api/jobs/<id>/cancel/`) — `app.control.revoke()` + 상태 갱신 | `views.py`, `job_service.py` |
| 6.5 | 활성 워커 0인 경우 상단 경고 배너 렌더링 | `templates/admin/job_queue.html`, `static/admin_console/js/pages/job_queue.js` |
| 6.6 | broker 연결 실패 시 워커 패널을 "Unavailable"로 명시 표시 | `worker_status.py` |

### 7.3 기술적 결정

- **워커 inspect 비용**: inspect는 broker 라운드트립 발생. 캐시 TTL 10s + lazy 호출(페이지 진입 시만).
- **Cancel semantics**: revoke(terminate=False)로 graceful cancel. terminate=True는 별도 SPEC.
- **CLAUDE.md 운영 룰 준수**: 본 SPEC 진행 중 Celery 워커 기동 시 검증 후 반드시 종료(`ps aux | rg "celery"`로 확인).

### 7.4 위험

| Risk | Mitigation |
|------|-----------|
| inspect 호출이 broker 부하 | 캐시 TTL 10s |
| revoke 실패 시 잡 상태 불일치 | revoke 결과 확인 후만 상태 갱신, 실패 시 alert |

### 7.5 완료 기준

- 워커 0 상태에서 빨간 배너 노출 확인
- FAILED 잡 retry → QUEUED 전환 확인
- RUNNING 잡 cancel → CANCELLED 전환 확인 + audit log 기록

---

## 8. Cross-Phase Technical Approach

### 8.1 Architecture Layering (DDD 유지)

- **Presentation**: Django views (HTML rendering + JSON API). 신규 추가는 SessionMonitorView 1건.
- **Application**: use case service (`dashboard_service`, `policy_service`, `metrics_service`, `worker_status`, `provider_health`, `health_check`, `job_service`). 본 SPEC에서 7개 신규 또는 확장.
- **Domain**: 변경 없음 (SPEC-04, SPEC-01 산출물 재사용).
- **Infrastructure**: Celery inspect, DB ping, Redis ping wrapper만 신규.

### 8.2 Frontend Pattern Consistency

- IIFE JS 모듈 패턴: `(function() { /* ... */ })();`
- 폴링: `setInterval(fetchAndRender, INTERVAL_MS)` + AbortController로 페이지 이탈 시 정리
- 스켈레톤 로딩: 사용자 페이지의 skeleton CSS 클래스(`.skeleton`, `.skeleton-line` 등) 재사용
- design-system.css의 CSS 변수 직접 참조 (예: `var(--color-status-failed)`)
- `data-i18n="key"` 속성 일관 적용

### 8.3 API Naming Convention

- HTML 페이지: `/admin/<page>/`
- JSON API: `/admin/api/<resource>/[<id>/<action>/]`
- CSV Export: `/admin/api/<resource>/export.csv?<filters>`

### 8.4 Audit Logging

모든 변경 액션(Provider 활성/비활성, Policy 저장, Job retry/cancel)은 audit_logs 테이블에:
- timestamp
- action (string)
- actor (admin identifier — 인증 비활성화 단계에서는 X-Forwarded-For 또는 hostname)
- target_resource_type, target_resource_id
- before_state, after_state (JSON)

---

## 9. Cross-Cutting Risks

| 위험 | 영향 모듈 | 대응 |
|------|---------|------|
| 인증 비활성화 상태에서 14001 외부 노출 | INFRA | 운영 환경에서 reverse proxy 레벨 IP whitelist 강제 (운영 책임 명시) |
| 폴링이 다수 페이지에 누적되어 백엔드 부하 | SESSION-MONITOR, DASHBOARD | 페이지 단일 활성 가정. 동일 데이터 캐시 TTL 5~10s |
| 거짓 데이터 fallback 유혹 | 전 모듈 | 모든 실패는 명시적 에러 표시. 0 치환/placeholder 금지 (CLAUDE.md 룰) |
| CDN(Chart.js) 차단 | METRICS | self-host 옵션 후속 SPEC |
| Phase 1 파일 변경이 사용자 페이지에 회귀 영향 | INFRA | 정적 파일 경로/URL namespace 분리 확인. 사용자 페이지 e2e smoke 재실행 |

---

## 10. Verification Strategy

각 Phase 완료 시:
1. 해당 Phase의 acceptance.md 시나리오 모두 통과
2. TRUST 5 quality gate (Tested, Readable, Unified, Secured, Trackable) 충족
3. 사용자 페이지(14000) smoke test 회귀 검증
4. 14001 콘솔 수동 점검 체크리스트 (URL 200, 정적 자원 200, 폴링 동작, audit log 기록)

전체 SPEC 완료 시:
- 6개 모듈 35개 EARS 요구사항 모두 acceptance test 통과
- system health 측정 실측 동작
- audit_logs에 모든 admin 액션 기록
- CLAUDE.md 코딩 룰(파일 ≤ 1000 LOC, 함수 ≤ 100 LOC, 복잡도 ≤ 20) 준수
