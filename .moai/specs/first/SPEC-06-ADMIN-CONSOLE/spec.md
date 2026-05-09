---
id: SPEC-06-ADMIN-CONSOLE
title: 관리자 콘솔 - 전체 기능 모니터링 및 LLM 모델 설정
version: 0.1.0
status: draft
created: 2026-05-08
updated: 2026-05-08
author: innovist
priority: P0
issue_number: null
dependencies: [SPEC-04-MODEL-ADMIN, SPEC-01-FOUNDATION-SESSION]
---

# SPEC-06-ADMIN-CONSOLE: 관리자 콘솔 - 전체 기능 모니터링 및 LLM 모델 설정

## HISTORY

- 2026-05-08 (v0.1.0): 초안 작성. 6개 모듈(Infra, Session Monitor, Dashboard, Model Config, Metrics, Job Monitor)에 대한 EARS 요구사항 정의. SPEC-04-MODEL-ADMIN(LLM 설정 백엔드)과 SPEC-01-FOUNDATION-SESSION(세션 파이프라인)에 의존.

---

## 1. Overview

### 1.1 목적 (Why)

Fashion Trend AI Design Support 시스템은 두 개의 포트(14000: 사용자 워크스페이스, 14001: 관리자 콘솔)로 구동된다. 사용자 워크스페이스는 운영 중이지만, 관리자 콘솔은 인프라 결함(CSS/JS 경로 불일치, URL 라우팅 미완성, 미등록 i18n 필터 등)으로 인해 접근 자체가 불가능한 상태이며, 핵심 모니터링 기능(세션 파이프라인 가시화, Celery 워커 상태, API 키 헬스, 비용 트렌드)이 누락되어 있다.

본 SPEC은 이 결함을 제거하고, 관리자가 시스템 전반(세션, 잡 큐, 모델, 비용)을 한 화면에서 모니터링하고 LLM 모델 정책을 설정할 수 있는 운영 가능한 관리자 콘솔을 정의한다.

### 1.2 범위 (What)

본 SPEC이 다루는 6개 기능 모듈:
1. **REQ-06-INFRA**: 콘솔 접근을 막는 인프라 결함 수정 (path, auth bypass, URL routing, i18n filter)
2. **REQ-06-SESSION-MONITOR**: 세션 파이프라인 모니터링 (신규 화면)
3. **REQ-06-DASHBOARD**: 대시보드 실 데이터 연동 및 system health
4. **REQ-06-MODEL-CONFIG**: LLM 모델 설정 UI (Provider/Catalog/Policy)
5. **REQ-06-METRICS**: 비용/토큰 트렌드 차트 및 CSV Export
6. **REQ-06-JOB-MONITOR**: Job queue + Celery 워커 상태

### 1.3 비범위 (Exclusions - What NOT to Build)

[HARD] 본 SPEC에서 명시적으로 제외하는 항목:

- **사용자 계정 관리 기능**: 관리자 사용자의 생성/삭제/권한 부여 UI는 본 SPEC에 포함하지 않는다. 향후 별도 SPEC으로 분리.
- **로그인 인증/세션 관리**: 관리자 콘솔은 내부 도구로 운영되며, 본 SPEC 단계에서는 인증을 명시적으로 우회한다(LoginRequiredMixin 제거 또는 무력화). OAuth/SSO/MFA는 비범위.
- **백엔드 도메인 모델 신규 정의**: ModelProvider, ModelCatalog, FeatureModelPolicy, PromptPolicy 등의 엔티티 및 리포지토리는 SPEC-04-MODEL-ADMIN에서 이미 정의됨. 본 SPEC은 UI 레이어만 다룸.
- **AI 파이프라인 로직 변경**: 세션 진행 단계(researching → concepting → ...) 자체의 변경은 SPEC-01-FOUNDATION-SESSION 소관이며 본 SPEC은 가시화만 담당.
- **알림/통보 채널(Email, Slack, PagerDuty)**: 실패 잡, 예산 초과 등에 대한 외부 알림 발송은 비범위.
- **내장 차트 라이브러리 자체 구현**: Chart.js를 CDN으로 로드하여 사용. 자체 SVG 차트 엔진 작성은 비범위.
- **권한별 화면 분리**: 모든 관리자 콘솔 사용자는 동일한 UI를 본다 (RBAC 비범위).
- **다국어(i18n) 메시지 신규 번역**: 기존 `data-i18n` 키 체계만 활성화. 새 언어 팩 추가는 비범위.
- **모바일 반응형 최적화**: 데스크톱(>=1280px) 우선. 태블릿/모바일 레이아웃 보정은 비범위.

---

## 2. Stakeholders

| 역할 | 관심사 |
|------|--------|
| 시스템 관리자 | 세션 실패율, 비용, 모델 정책, 큐 적체 모니터링 |
| LLM 운영 담당자 | Provider 활성/비활성, 모델 카탈로그, Feature Policy 변경 |
| DevOps | Celery 워커 헬스, API 키 유효성, 시스템 헬스 |
| 운영 검수자 | 실패 잡 재시도, 롤백, Audit log 추적 |

---

## 3. Glossary

- **Feature Policy**: 9개 고정 feature_key(research, concept, reference, abstract, generate, document, review, ...)에 대해 사용할 LLM 모델 및 파라미터를 정의한 정책.
- **Model Catalog**: Provider 산하의 사용 가능한 모델 메타데이터 (모델명, context_limit, cost_estimate 등).
- **Prompt Policy**: feature_key별 system_prompt와 user_template, 버저닝.
- **Pipeline Step**: 세션이 거치는 17개 세부 처리 단계.
- **Session Status**: 9개 세션 상태(queued, researching, concepting, referencing, abstracting, generating, documenting, review_ready, failed).
- **Generation Job**: Celery 비동기 잡 단위(QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED) × 4개 잡 타입.

---

## 4. Functional Requirements (EARS Format)

### 4.1 REQ-06-INFRA — 관리자 콘솔 인프라 수정

**REQ-06-INFRA-01 (Ubiquitous)**
The 관리자 콘솔 base.html template **shall** reference CSS at `/static/admin_console/css/admin.css` and JS at `/static/admin_console/js/admin.js` so that 정적 자원이 404 없이 로드된다.

**REQ-06-INFRA-02 (Ubiquitous)**
The 관리자 콘솔 URL 설정 (config/urls_admin.py) **shall** mount HTML 페이지 라우트(dashboard, providers, models, policies, prompt_policies, metrics, audit_logs, job_queue, rollback, sessions)를 admin namespace 하위에 명시한다.

**REQ-06-INFRA-03 (Event-Driven)**
**When** 관리자가 포트 14001 의 어떤 admin URL에 접근하든, the 관리자 콘솔 **shall** LoginRequiredMixin 또는 동등한 인증 체크 없이 페이지를 응답한다.

**REQ-06-INFRA-04 (Ubiquitous)**
The 관리자 콘솔 템플릿 시스템 **shall** `|i18n` 커스텀 필터를 admin_console 앱의 templatetags 모듈에서 등록하여 모든 admin 템플릿에서 사용 가능하게 한다.

**REQ-06-INFRA-05 (Ubiquitous)**
The base.html navigation **shall** admin namespace 내에 정의된 url 태그(`{% url 'admin:dashboard' %}`, `{% url 'admin:settings' %}`, `{% url 'admin:logout' %}` 등)만 참조하며, 정의되지 않은 url 이름은 사용하지 않는다. (logout은 인증 비활성화 단계에서는 No-op redirect로 처리)

**REQ-06-INFRA-06 (Unwanted Behavior)**
**If** 관리자 콘솔이 시작 시 정적 파일 매핑 또는 i18n 필터 등록에 실패하면, **then** the 시스템 **shall** 서비스를 기동하지 않고 명확한 오류 메시지를 stderr에 출력한다(거짓 fallback 금지).

---

### 4.2 REQ-06-SESSION-MONITOR — 세션 파이프라인 모니터링 (신규)

**REQ-06-SM-01 (Ubiquitous)**
The 세션 모니터링 화면 (`/admin/sessions/`) **shall** 전체 세션을 9개 status별 chip 카운트, 검색, 필터(status, project, date range), 페이지네이션과 함께 표시한다.

**REQ-06-SM-02 (Event-Driven)**
**When** 관리자가 세션 모니터링 화면을 열면, the 화면 **shall** 5초 간격으로 setInterval 폴링하여 상태 변화를 자동 반영한다.

**REQ-06-SM-03 (Event-Driven)**
**When** 관리자가 세션 행을 클릭하면, the 화면 **shall** 17개 pipeline step의 진행 상태(완료/진행중/대기/실패), 단계별 소요 시간, 에러 메시지를 drill-down 패널에 표시한다.

**REQ-06-SM-04 (State-Driven)**
**While** 세션이 `failed` 상태인 동안, the 화면 **shall** 해당 행에 빨간색 chip과 inline action(Retry, View Error)을 표시한다.

**REQ-06-SM-05 (Optional)**
**Where** 세션 데이터가 100건 이상 존재할 때, the 화면 **shall** 가상 스크롤 또는 서버 사이드 페이지네이션(페이지당 50건)을 적용한다.

**REQ-06-SM-06 (Unwanted Behavior)**
**If** 세션 데이터 API가 5초 폴링 중 응답에 실패하면, **then** the 화면 **shall** 마지막으로 성공한 데이터를 유지하면서 비차단(non-blocking) 토스트로 재시도 상태를 알리고, 거짓 데이터를 표시하지 않는다.

---

### 4.3 REQ-06-DASHBOARD — 대시보드 실 데이터 연동

**REQ-06-DB-01 (Ubiquitous)**
The 대시보드 (`/admin/`) **shall** 다음 KPI를 실 DB/Celery 상태에서 조회하여 표시한다: 활성 세션 수, 24시간 내 완료/실패 잡 수, 24시간 누적 비용(USD), 활성 Provider 수.

**REQ-06-DB-02 (Ubiquitous)**
The 대시보드의 system health 영역 **shall** 다음 항목을 실측한다: DB 연결, Redis 연결, Celery broker 연결, 활성 워커 수. placeholder dict 또는 하드코딩 값은 사용하지 않는다.

**REQ-06-DB-03 (Event-Driven)**
**When** system health 항목 중 하나라도 비정상(연결 실패 또는 워커 0)이면, the 대시보드 **shall** 해당 항목에 경고 chip을 표시하고 마지막 점검 timestamp를 보여준다.

**REQ-06-DB-04 (Optional)**
**Where** 일별/월별 예산 한도가 `.moai/config` 또는 환경변수로 정의되어 있을 때, the 대시보드 **shall** 누적 비용 대비 사용률(%)을 progress bar로 표시한다.

**REQ-06-DB-05 (Unwanted Behavior)**
**If** KPI 계산을 위한 쿼리가 실패하거나 timeout(>3s)하면, **then** the 대시보드 **shall** 해당 KPI 카드에 명시적 오류 표시를 하고 0 또는 임의값으로 fallback하지 않는다.

---

### 4.4 REQ-06-MODEL-CONFIG — LLM 모델 설정 UI

**REQ-06-MC-01 (Ubiquitous)**
The Provider 관리 화면 (`/admin/providers/`) **shall** ModelProvider의 CRUD(Create/Read/Update, 비활성화)와 활성/비활성 토글을 제공하며, api_key는 환경변수 키 이름만 표시(값은 노출 금지).

**REQ-06-MC-02 (Event-Driven)**
**When** 관리자가 Provider의 "API Key Test" 버튼을 클릭하면, the 시스템 **shall** Provider별 ping 엔드포인트(또는 1-token completion)로 헬스 체크를 실행하고 결과(latency, status_code, error)를 표시한다.

**REQ-06-MC-03 (Ubiquitous)**
The Model Catalog 화면 (`/admin/models/`) **shall** ModelCatalog 엔티티(provider_id, model_name, type, context_limit, cost_estimate, active)의 CRUD를 제공한다.

**REQ-06-MC-04 (Ubiquitous)**
The Feature Policy 화면 (`/admin/policies/`) **shall** 9개 고정 feature_key 각각에 대해 primary_model_id, fallback_model_ids(다중), parameters(JSON), version, active를 편집할 수 있도록 한다.

**REQ-06-MC-05 (Event-Driven)**
**When** Feature Policy가 저장되면, the 시스템 **shall** version을 자동 증가하고, 직전 버전을 audit log에 기록하며, 활성화된 정책 1개만 유지(active=true는 feature_key당 단일).

**REQ-06-MC-06 (Optional)**
**Where** 정책 변경 전 미리보기가 가능할 때, the 화면 **shall** 변경 전/후 모델 호출 비용 추정(per 1k tokens)을 비교 표시한다.

**REQ-06-MC-07 (Unwanted Behavior)**
**If** Feature Policy의 primary_model_id가 비활성 ModelCatalog를 가리키면, **then** the 시스템 **shall** 저장을 거부하고 명시적 검증 오류를 반환한다.

---

### 4.5 REQ-06-METRICS — 비용/토큰 트렌드 차트 및 Export

**REQ-06-MX-01 (Ubiquitous)**
The Metrics 화면 (`/admin/metrics/`) **shall** 7일 및 30일 기준의 비용(USD) 및 토큰(input/output) 트렌드를 라인 차트로 표시한다 (Chart.js CDN 사용).

**REQ-06-MX-02 (Ubiquitous)**
The Metrics 화면 **shall** feature_key별 호출 수, 성공률, 평균 latency(ms), 총 비용을 테이블로 제공한다.

**REQ-06-MX-03 (Event-Driven)**
**When** 관리자가 "Export CSV" 버튼을 클릭하면, the 시스템 **shall** 현재 필터 조건의 metrics 데이터를 UTF-8 CSV(BOM 포함)로 다운로드 응답한다.

**REQ-06-MX-04 (State-Driven)**
**While** 차트 데이터가 로드 중인 동안, the 화면 **shall** 스켈레톤 로딩 애니메이션을 표시한다.

**REQ-06-MX-05 (Unwanted Behavior)**
**If** 트렌드 데이터 집계 쿼리가 timeout 또는 빈 결과를 반환하면, **then** the 차트 **shall** 빈 상태(empty state) UI를 명시적으로 표시하고 0으로 채워진 가짜 시리즈를 그리지 않는다.

---

### 4.6 REQ-06-JOB-MONITOR — Job Queue + Celery Worker 상태

**REQ-06-JM-01 (Ubiquitous)**
The Job Queue 화면 (`/admin/job_queue/`) **shall** GenerationJob을 status(QUEUED/RUNNING/COMPLETED/FAILED/CANCELLED) chip, 잡 타입 필터, 검색, 페이지네이션과 함께 표시한다.

**REQ-06-JM-02 (Ubiquitous)**
The Job Queue 화면 **shall** Celery 워커 상태 패널을 제공하며, 다음을 실측한다: 활성 워커 수, 워커별 hostname, 처리 중 task 수, 마지막 heartbeat (django-celery-results 또는 celery inspect 활용).

**REQ-06-JM-03 (Event-Driven)**
**When** 관리자가 FAILED 상태 잡의 "Retry" 버튼을 클릭하면, the 시스템 **shall** 해당 잡을 재큐잉하고 audit log에 retry 사유와 관리자 식별자를 기록한다.

**REQ-06-JM-04 (Event-Driven)**
**When** 관리자가 RUNNING 또는 QUEUED 잡의 "Cancel" 버튼을 클릭하면, the 시스템 **shall** Celery revoke를 실행하고 잡 상태를 CANCELLED로 갱신한다.

**REQ-06-JM-05 (State-Driven)**
**While** 활성 워커 수가 0인 동안, the 화면 **shall** 빨간색 경고 배너를 상단에 고정하여 "No active Celery workers" 메시지를 표시한다.

**REQ-06-JM-06 (Unwanted Behavior)**
**If** Celery broker(Redis) 연결이 실패하면, **then** the 화면 **shall** 워커 상태 패널을 "Unavailable"로 표시하고 임의 워커 수를 표시하지 않는다.

---

## 5. Non-Functional Requirements

### 5.1 Performance

- 모든 admin 페이지 초기 응답: P95 < 1.5s (DB 쿼리 포함)
- 폴링 API 응답: P95 < 500ms
- Chart.js 렌더링: 7일 데이터 < 200ms

### 5.2 Reliability

- 정적 자원(CSS/JS) 로드 실패 시 명확한 콘솔 오류
- API 폴링 실패 시 마지막 정상 데이터 유지(거짓 fallback 금지)
- system health 측정 실패 시 명시적 오류 표시

### 5.3 Consistency (Design)

- 사용자 페이지(포트 14000)와 동일한 디자인 토큰(design-system.css의 CSS 변수) 사용
- `data-i18n="key"` 패턴 일관 적용
- IIFE JS 모듈 패턴 유지
- 로딩 상태는 스켈레톤 애니메이션 통일

### 5.4 Security

- API 키 값은 절대 UI에 노출하지 않음 (환경변수 키 이름만 표시)
- 인증 비활성화 단계에서도 14001 포트는 내부 네트워크에서만 접근 가능해야 함 (운영 책임)
- 모든 변경(Policy, Provider 활성화 등)은 audit log에 관리자 식별자(IP 또는 hostname) 기록

### 5.5 Observability

- 모든 admin 액션은 audit_logs 테이블에 기록
- 폴링 실패는 클라이언트 콘솔에 경고로 출력
- 백엔드는 admin 액션을 structured logging으로 출력

---

## 6. Constraints

- Django 5.2 + DRF 환경 유지
- 신규 외부 의존성은 Chart.js(CDN) 만 허용. 추가 패키지 도입은 사전 승인 필요
- 기존 SPEC-04-MODEL-ADMIN에서 정의한 도메인 엔티티 및 리포지토리는 변경하지 않음(UI/뷰/시리얼라이저 레이어만 보강)
- 기존 `apps/admin_console/presentation/views.py`(1187 LOC)와 10개 템플릿은 가능한 재사용. 신규 모듈은 sessions 모니터링 1건만 신설
- 파일 ≤ 1000 LOC, 함수 ≤ 100 LOC, 매개변수 ≤ 10, 순환 복잡도 ≤ 20 준수

---

## 7. Assumptions

- SPEC-04-MODEL-ADMIN의 도메인/응용/인프라 레이어는 정상 동작한다고 가정
- SPEC-01-FOUNDATION-SESSION의 세션 상태/파이프라인 step 모델은 변경 없이 사용 가능하다고 가정
- 14001 포트는 내부망에서만 접근 가능한 운영 환경이라고 가정 (인증 우회의 전제)
- Celery 워커는 django-celery-results 또는 celery inspect API로 상태 조회가 가능하다고 가정
- Chart.js v4 (CDN) 사용 가능

---

## 8. Open Questions

| # | 질문 | 영향 모듈 |
|---|------|----------|
| Q1 | logout 메뉴는 인증 비활성화 단계에서 완전히 숨길지, No-op으로 둘지? | INFRA |
| Q2 | system health의 점검 주기는 폴링 5초 vs 별도 주기? | DASHBOARD |
| Q3 | API Key 테스트 시 사용할 ping 엔드포인트는 Provider별로 다른가? | MODEL-CONFIG |
| Q4 | 예산 한도 정의 위치는 환경변수 vs DB 테이블? | DASHBOARD |
| Q5 | CSV Export의 한글 헤더 사용 vs 영문? | METRICS |

---

## 9. Traceability Matrix (요약)

| 모듈 | EARS 요구사항 수 | 의존 SPEC |
|------|----------------|----------|
| INFRA | 6 | - |
| SESSION-MONITOR | 6 | SPEC-01-FOUNDATION-SESSION |
| DASHBOARD | 5 | SPEC-04-MODEL-ADMIN |
| MODEL-CONFIG | 7 | SPEC-04-MODEL-ADMIN |
| METRICS | 5 | SPEC-04-MODEL-ADMIN |
| JOB-MONITOR | 6 | SPEC-01-FOUNDATION-SESSION |
| **합계** | **35** | |
