---
id: SPEC-06-ADMIN-CONSOLE
artifact: acceptance
version: 0.1.0
created: 2026-05-08
updated: 2026-05-08
---

# SPEC-06-ADMIN-CONSOLE — Acceptance Criteria

본 문서는 6개 모듈에 대한 Given-When-Then(GWT) 시나리오, 엣지 케이스, 품질 게이트 기준, Definition of Done을 정의한다. 시나리오는 EARS 요구사항(REQ-06-*)에 traceable 하다.

---

## 1. REQ-06-INFRA — 관리자 콘솔 인프라

### Scenario INFRA-1: 콘솔 접속 시 정적 자원이 정상 로드된다

**Given** 관리자가 서비스를 14001 포트로 기동했다
**And** static 디렉토리에 `/static/admin_console/css/admin.css`와 `/static/admin_console/js/admin.js`가 존재한다
**When** 관리자가 브라우저로 `http://localhost:14001/admin/`에 접근한다
**Then** HTTP 응답 코드는 200이다
**And** 브라우저 DevTools Network 탭에서 admin.css와 admin.js가 200으로 로드된다
**And** 콘솔에 404 또는 정적 자원 관련 오류가 없다

Traces: REQ-06-INFRA-01

### Scenario INFRA-2: 인증 없이 admin 페이지 접근이 가능하다

**Given** `settings.ADMIN_CONSOLE_AUTH_ENABLED = False`로 설정되어 있다
**And** 관리자는 로그인하지 않은 상태이다
**When** 관리자가 `/admin/`, `/admin/providers/`, `/admin/policies/`, `/admin/sessions/` 등 모든 admin URL에 접근한다
**Then** 모든 URL은 200 응답을 반환한다
**And** 로그인 페이지로 리다이렉트되지 않는다

Traces: REQ-06-INFRA-03

### Scenario INFRA-3: 미정의 url 태그로 인한 템플릿 렌더 실패가 없다

**Given** base.html이 `{% url 'admin:dashboard' %}`, `{% url 'admin:settings' %}`, `{% url 'admin:logout' %}`을 참조한다
**And** `urls_admin.py`의 admin namespace에 위 3개 url 이름이 모두 등록되어 있다 (logout/settings는 No-op redirect 또는 placeholder 라우트)
**When** 관리자가 admin 페이지를 렌더한다
**Then** NoReverseMatch 예외가 발생하지 않는다

Traces: REQ-06-INFRA-05

### Edge Cases (INFRA)

- 정적 파일 경로 변경이 사용자 페이지(14000)에 회귀 영향을 주지 않아야 한다 → 14000 smoke test 통과 확인
- i18n 필터에 미등록 키가 전달되면 키 자체를 그대로 출력해야 한다 (거짓 fallback 금지)
- collectstatic 미실행 환경에서도 dev 서버에서는 정상 로드되어야 한다

---

## 2. REQ-06-SESSION-MONITOR — 세션 파이프라인 모니터링

### Scenario SM-1: 관리자가 모든 세션의 상태를 실시간으로 본다

**Given** DB에 9개 status에 걸쳐 분포된 50개의 세션이 존재한다
**When** 관리자가 `/admin/sessions/` 페이지에 접근한다
**Then** 9개 status별 chip(queued/researching/.../failed)이 카운트와 함께 상단에 표시된다
**And** 세션 목록 테이블에 50건 중 첫 페이지(50건/페이지) 분량이 렌더된다
**And** 각 행에는 session_id, project, current_status, last_updated가 표시된다
**And** 5초 후 setInterval 폴링이 자동으로 fetch를 1회 실행한다 (Network 탭에서 확인)

Traces: REQ-06-SM-01, REQ-06-SM-02

### Scenario SM-2: 실패 세션의 17 step drill-down

**Given** session_id=S-001이 `failed` 상태이며, 17개 pipeline step 중 step 5(referencing)에서 실패했다
**When** 관리자가 해당 세션 행을 클릭한다
**Then** drill-down 패널이 열리며 17개 step이 나열된다
**And** step 1~4는 "completed", step 5는 "failed" + 에러 메시지, step 6~17은 "pending"으로 표시된다
**And** step 5 행에 소요 시간과 에러 stack trace 일부가 표시된다
**And** 행에 "Retry" inline action 버튼이 노출된다

Traces: REQ-06-SM-03, REQ-06-SM-04

### Edge Cases (SESSION-MONITOR)

- 세션이 0건일 때: empty state UI 표시 ("No sessions yet")
- 세션이 1000건일 때: 페이지네이션이 50/page로 분할되며 응답 < 1.5s
- 폴링 API가 timeout(>3s) 시: 마지막 정상 데이터 유지 + 토스트 경고 (거짓 fallback 금지)
- pipeline step 데이터가 부분적으로 누락된 경우: 누락 step은 "unknown"으로 명시 표시

---

## 3. REQ-06-DASHBOARD — 대시보드 실 데이터 연동

### Scenario DB-1: KPI 카드가 실측 데이터를 표시한다

**Given** 다음의 DB 상태가 존재한다:
  - 활성 세션 12건
  - 24h 내 완료 잡 87건, 실패 잡 3건
  - 24h 누적 비용 $12.45
  - 활성 Provider 2개
**When** 관리자가 `/admin/`에 접근한다
**Then** KPI 카드에 위 4개 값이 정확히 표시된다
**And** 어떤 카드도 placeholder 텍스트("--", "0", "TBD")를 표시하지 않는다

Traces: REQ-06-DB-01

### Scenario DB-2: System health 항목이 실측 결과로 표시된다

**Given** Redis 서버가 정지되어 있다
**And** DB는 정상이다
**And** Celery 활성 워커는 0개이다
**When** 관리자가 대시보드에 접근한다
**Then** system health 영역에서:
  - DB: 초록 chip "OK" + 마지막 점검 timestamp
  - Redis: 빨간 chip "Failed" + 에러 메시지
  - Celery broker: 빨간 chip "Failed"
  - 활성 워커: 빨간 chip "0 workers" + 경고
**And** 시스템은 "0" 등의 거짓 fallback이 아닌 명시적 오류 메시지를 표시한다

Traces: REQ-06-DB-02, REQ-06-DB-03, REQ-06-DB-05

### Edge Cases (DASHBOARD)

- KPI 쿼리가 3초 timeout 시: 해당 카드만 "Error" 표시, 다른 카드는 정상 렌더 (전체 페이지 차단 금지)
- 예산 환경변수 미정의 시: progress bar 영역이 숨김 처리됨
- 24h 비용 집계가 빈 결과(0건 호출)일 때: $0.00 정상 표시 (이는 거짓 fallback이 아닌 실제 값)

---

## 4. REQ-06-MODEL-CONFIG — LLM 모델 설정

### Scenario MC-1: 관리자가 Feature Policy를 변경하고 호출에 반영된다

**Given** feature_key=`research`의 active Policy v3가 primary_model=GPT-4o이다
**And** Provider OpenAI와 ModelCatalog GPT-4o, GPT-4o-mini가 모두 active이다
**When** 관리자가 `/admin/policies/`에서 `research`의 primary_model을 GPT-4o-mini로 변경하고 저장한다
**Then** Policy v4가 생성되고 active=true가 된다
**And** Policy v3는 active=false로 자동 변경된다
**And** audit_logs 테이블에 before_state(v3, GPT-4o)와 after_state(v4, GPT-4o-mini)가 기록된다
**When** 직후 `research` feature가 호출된다
**Then** invocation 로그의 model_id는 GPT-4o-mini를 가리킨다

Traces: REQ-06-MC-04, REQ-06-MC-05

### Scenario MC-2: API Key Test가 Provider 헬스를 검증한다

**Given** Provider Anthropic이 active이며 api_key_env=`ANTHROPIC_API_KEY`이다
**And** 환경변수 `ANTHROPIC_API_KEY`에 유효한 키가 설정되어 있다
**When** 관리자가 `/admin/providers/`에서 Anthropic의 "Test" 버튼을 클릭한다
**Then** 5초 이내 결과 모달이 표시된다
**And** 결과는 latency(ms), status_code(200), error(null)을 포함한다
**Given** 잘못된 API Key 환경에서
**When** 동일한 Test를 실행한다
**Then** 결과는 status_code(401) + error 메시지를 포함한다
**And** 화면 어디에도 실제 API Key 값은 표시되지 않는다

Traces: REQ-06-MC-02, NFR §5.4 (Security)

### Scenario MC-3: 비활성 모델을 primary로 지정 시 저장이 거부된다

**Given** ModelCatalog `claude-2`가 active=false 상태이다
**When** 관리자가 feature_key=`concept`의 primary_model_id를 `claude-2`로 지정하고 저장을 시도한다
**Then** 시스템은 저장을 거부한다
**And** UI에 "Cannot set inactive model as primary" 명시적 검증 오류가 표시된다
**And** 기존 Policy 버전은 변경되지 않는다

Traces: REQ-06-MC-07

### Edge Cases (MODEL-CONFIG)

- 동시에 두 관리자가 동일 feature_key의 Policy를 저장 시도 시: select_for_update로 직렬화, 두 번째 저장은 version 충돌 감지 후 재시도 안내
- API Key Test 호출이 60초 내 동일 Provider에 대해 재실행 시: rate limit으로 차단
- ModelCatalog 삭제 대신 active=false 권장 (이미 사용 중 Policy가 있을 수 있음)

---

## 5. REQ-06-METRICS — 비용/토큰 트렌드 차트 및 Export

### Scenario MX-1: 7일 비용 트렌드 차트가 정확히 그려진다

**Given** 지난 7일간 일별 비용이 [$1.20, $2.50, $0.80, $3.10, $4.50, $2.20, $1.90]이다
**When** 관리자가 `/admin/metrics/` 페이지에 접근하고 range를 "7d"로 선택한다
**Then** Chart.js 라인 차트가 렌더되며 7개 데이터 포인트가 위 값과 일치한다
**And** Y축 단위는 USD, X축은 일자(YYYY-MM-DD)이다
**And** 동일 영역에 input/output 토큰 라인 차트가 추가로 표시된다
**And** 로딩 중 스켈레톤 애니메이션이 잠시 표시된다

Traces: REQ-06-MX-01, REQ-06-MX-04

### Scenario MX-2: CSV Export가 한글 환경에서 깨지지 않는다

**Given** 관리자가 `/admin/metrics/`에서 30d 범위로 데이터를 조회한 상태이다
**When** 관리자가 "Export CSV" 버튼을 클릭한다
**Then** `metrics_30d_YYYYMMDD.csv` 파일이 다운로드된다
**And** 파일은 UTF-8 BOM(EF BB BF)으로 시작한다
**And** Microsoft Excel 한국어 환경에서 열었을 때 헤더와 데이터가 깨지지 않는다
**And** 헤더는 영문(date, feature_key, calls, success_rate, avg_latency_ms, total_cost_usd)이다

Traces: REQ-06-MX-03

### Edge Cases (METRICS)

- 데이터가 비어있을 때(0 호출): 차트 영역에 "No data for selected range" empty state 표시 (거짓 0 시리즈 그리지 않음)
- Chart.js CDN 차단 환경: 차트 영역에 "Chart library unavailable" 메시지 표시
- 30일 범위 집계 쿼리가 timeout 시: 명시적 에러 표시, 7일 데이터로 자동 fallback 금지

---

## 6. REQ-06-JOB-MONITOR — Job Queue + Celery Worker

### Scenario JM-1: 관리자가 실패한 잡을 재시도한다

**Given** GenerationJob J-100이 status=FAILED이며 error_message="API timeout"이다
**And** Celery 워커가 1개 이상 활성 상태이다
**When** 관리자가 `/admin/job_queue/`에서 J-100의 "Retry" 버튼을 클릭한다
**Then** J-100의 status가 QUEUED로 갱신된다
**And** Celery 큐에 J-100이 재등록된다 (worker가 받아 RUNNING으로 전환됨을 폴링에서 확인)
**And** audit_logs에 action=`job.retry`, actor, target_id=J-100이 기록된다

Traces: REQ-06-JM-03

### Scenario JM-2: Celery 워커가 0인 경우 경고가 노출된다

**Given** Celery 워커 프로세스가 모두 정지되었다
**When** 관리자가 `/admin/job_queue/` 페이지에 접근한다
**Then** 페이지 상단에 빨간 경고 배너 "No active Celery workers"가 고정 표시된다
**And** 워커 상태 패널에 "Active workers: 0"이 표시된다
**And** 어떤 임의의 워커 수도 표시되지 않는다 (거짓 fallback 금지)

Traces: REQ-06-JM-05

### Scenario JM-3: RUNNING 잡을 취소한다

**Given** Job J-200이 status=RUNNING이다
**When** 관리자가 "Cancel" 버튼을 클릭한다
**Then** Celery `app.control.revoke(task_id, terminate=False)`가 호출된다
**And** J-200의 status가 CANCELLED로 갱신된다
**And** audit_logs에 action=`job.cancel`이 기록된다

Traces: REQ-06-JM-04

### Edge Cases (JOB-MONITOR)

- broker(Redis) 다운 시: 워커 패널을 "Unavailable" 표시, retry/cancel 버튼은 비활성화
- 동일 잡에 대한 재시도가 단시간 내 반복 클릭될 때: 이미 QUEUED 상태면 재큐잉하지 않음 (idempotent)
- revoke 실패 시: 잡 status는 변경하지 않고 alert 표시

---

## 7. Cross-Cutting Acceptance

### Scenario CC-1: 디자인 일관성 (사용자 페이지와 admin 콘솔)

**Given** 사용자 페이지(14000)와 admin 콘솔(14001) 둘 다 design-system.css의 CSS 변수를 사용한다
**When** 관리자가 두 페이지를 동시에 비교한다
**Then** 색상 팔레트(primary, success, warning, danger), 타이포그래피, 버튼 스타일, chip 디자인이 일관된다
**And** 로딩 상태는 동일한 스켈레톤 애니메이션 클래스를 사용한다

### Scenario CC-2: 거짓 fallback 금지 룰

**Given** 어떤 admin API가 실패한다 (DB 오류, 외부 API 타임아웃, 빈 결과 등)
**When** UI가 응답을 받는다
**Then** UI는 다음 중 하나로 명시적으로 표시한다:
  - "Error: <message>"
  - "Unavailable"
  - "No data"
**And** 0, "--", placeholder dict, 임의 값으로 결코 치환하지 않는다

### Scenario CC-3: Audit log 일관성

**Given** 관리자가 변경 액션(Provider 활성화, Policy 저장, Job retry, Job cancel)을 수행한다
**When** 액션이 완료된다
**Then** audit_logs 테이블에 timestamp, action, actor, target_resource_*, before_state, after_state(JSON)가 기록된다
**And** `/admin/audit_logs/` 페이지에서 해당 기록을 확인할 수 있다

---

## 8. Quality Gates (TRUST 5)

| Pillar | 기준 |
|--------|------|
| Tested | 신규/수정 application service 메서드 단위 테스트 ≥ 85%, 핵심 view에 대한 통합 테스트(GET 200, action POST 결과 검증) |
| Readable | 함수명/변수명 영문, ruff 0 warnings |
| Unified | black/isort 통과, 기존 admin_console 모듈의 명명/레이아웃 컨벤션 준수 |
| Secured | API Key 값 응답 비포함, audit log 기록, OWASP A01(Access Control)는 14001 운영 환경 IP whitelist 전제 |
| Trackable | 모든 변경 액션이 audit_logs에 기록됨, Conventional commits, SPEC ID 참조 |

### 정적 분석 게이트

- 파일 ≤ 1000 LOC, 함수 ≤ 100 LOC, 매개변수 ≤ 10, 순환 복잡도 ≤ 20
- 신규 외부 의존성은 Chart.js CDN 외 금지

---

## 9. Definition of Done

본 SPEC은 다음 모두 충족 시 완료(Done)로 간주한다:

1. **35개 EARS 요구사항(REQ-06-*) 모두 acceptance scenario를 통과**한다
2. **Phase 1~6의 완료 기준** (plan.md §2.5, §3.5, §4.5, §5.5, §6.5, §7.5) 모두 통과
3. **사용자 페이지(14000) smoke test** 회귀 없음 확인
4. **TRUST 5 quality gate** 모두 통과 (커버리지 ≥ 85%, ruff/black/isort 통과, 보안 점검)
5. **CLAUDE.md 운영 룰** 준수: Celery 검증 시 워커 종료 확인, 거짓 fallback 부재, 하드코딩 카테고리/룰베이스 매핑 부재
6. **audit_logs**에 본 SPEC 동안 수행된 변경 액션이 모두 기록됨
7. **CSS/JS 정적 자원 404 0건**, **NoReverseMatch 0건**, **i18n 필터 미등록 오류 0건**
8. **system health 4개 항목**이 실측 데이터로 동작 (placeholder dict 부재)
9. **6개 모듈 화면**이 사용자 페이지와 동일한 design token 및 스켈레톤 로딩 패턴 사용
10. **본 SPEC §8 Open Questions** 5건이 모두 해결되거나 의도적으로 후속 SPEC으로 이관됨

---

## 10. Verification Checklist

```
[ ] INFRA-1, INFRA-2, INFRA-3 통과
[ ] SM-1, SM-2 통과
[ ] DB-1, DB-2 통과
[ ] MC-1, MC-2, MC-3 통과
[ ] MX-1, MX-2 통과
[ ] JM-1, JM-2, JM-3 통과
[ ] CC-1 (디자인 일관성), CC-2 (거짓 fallback 금지), CC-3 (audit log) 통과
[ ] TRUST 5 quality gate 통과
[ ] CLAUDE.md 운영 룰 준수 검증 완료
[ ] 사용자 페이지(14000) smoke test 회귀 없음
```
