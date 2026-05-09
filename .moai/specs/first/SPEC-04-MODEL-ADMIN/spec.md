---
id: SPEC-04-MODEL-ADMIN
title: 모델 카탈로그·기능별 정책·ModelRouter + 관리자 콘솔(테넌트/사용자/큐/모니터/감사/롤백)
version: 0.1.0
status: draft
created: 2026-05-07
domain: model-admin
priority: P0
dependencies: [SPEC-01-FOUNDATION-SESSION]
---

# SPEC-04-MODEL-ADMIN: 모델 카탈로그 + 관리자 콘솔

## 1. 개요 (Overview)

### 1.1 목적
시스템의 모든 AI 호출이 통과하는 단일 진입점(ModelRouter)과, 관리자가 운영하는 완전한 관리자 콘솔 UX(모델 카탈로그·기능별 정책·프롬프트 정책·트렌드 큐·사용자/권한·관측·감사·롤백)를 정의한다. `.env`는 Provider/API Key/사용 가능한 모델만 제공하고, 코드에는 모델명/키를 절대 하드코딩하지 않는다. 9개 기능별 정책으로 모델 사용을 정확히 제어하며, fallback은 거짓 결과를 반환하지 않고 “실패 명확 보고 + 다른 정책 재시도” 방식만 허용한다.

### 1.2 범위 (In Scope)
- 모델 카탈로그 도메인: `ModelProvider`, `ModelCatalog`, `FeatureModelPolicy`, `PromptPolicy`
- ModelRouter: 9개 기능 키별 정책 적용·재시도·fallback·비용/토큰/실패 메트릭 수집
- 관리자 콘솔 프런트엔드/UX: 테넌트/사용자/권한, 트렌드 출처 큐(SPEC-02 운영 화면 위임), 모델 카탈로그, 기능별 정책, 프롬프트 정책, 비용·실패율·토큰 모니터링, 감사로그 뷰, 정책 버전·롤백, 작업 로그, 빈/오류/권한 상태
- 관리자 권한 가드와 감사

### 1.3 범위 외 (Out of Scope)
- 트렌드 수집 파이프라인 자체(SPEC-02), 컨셉/생성/스펙(SPEC-03), 사용자 워크스페이스 UX(SPEC-05)
- 디자인 세션 상태머신/도메인 모델(SPEC-01)

### 1.4 가치 제안
- 단일 ModelRouter가 9개 기능에 대해 “정책으로만” 동작 → 코드 변경 없이 모델 교체/fallback 가능
- 거짓 fallback 금지 정책으로 환각·허위 결과 차단
- 비용/토큰/실패율 가시화로 운영 통제

### 1.5 User_Needs.md 매핑
- §3.8(관리 가능한 AI 시스템), §11.7(관리자 프로그램), §13.2(관리자 영역), §14(AI 모델 카탈로그), §17(모델 라우터 도식)

---

## 2. 사용자 스토리 (User Stories)

- US-04-01 (관리자): Provider/모델 목록을 카탈로그로 등록·수정·비활성화한다.
- US-04-02 (관리자): 9개 기능 키마다 “기본 모델 + fallback 후보 + 파라미터 + max_cost”를 설정한다.
- US-04-03 (관리자): 정책 변경 후 문제 발생 시 한 번의 클릭으로 이전 버전으로 롤백한다.
- US-04-04 (관리자): 모델 비용·토큰·실패율을 기능 키 단위로 모니터링한다.
- US-04-05 (관리자): 사용자/관리자/AI 호출 감사 로그를 필터링/검색한다.
- US-04-06 (개발자/시스템): 코드에서는 `ModelRouter.invoke(feature_key, payload)`만 호출하고 모델명/키는 알 필요 없다.
- US-04-07 (관리자): 큐 실패, 비용 초과, 키 누락, 정책 충돌 같은 운영 이슈를 콘솔에서 원인·영향·복구 액션과 함께 확인한다.
- US-04-08 (관리자): 정책 변경 전후 diff, 예상 비용 영향, fallback 체인 검증 결과를 확인한 뒤 저장한다.

---

## 3. 요구사항 (EARS Format Requirements)

### 3.1 모델 카탈로그 (REQ-04-CATALOG)

- REQ-04-CATALOG-001 (Ubiquitous): THE SYSTEM SHALL `ModelProvider(id, name, api_key_env, base_url, endpoint_path, auth_scheme, active)`로 Provider를 관리한다. `base_url`과 `endpoint_path`는 중복 경로가 생기지 않도록 정규화한다. (근거: §14.2)
- REQ-04-CATALOG-002 (Ubiquitous): THE SYSTEM SHALL `ModelCatalog(id, provider_id, model_name, type, context_limit, cost_estimate, modalities, active)`로 모델 목록을 관리하며 type ∈ {text, chat, vision, image, search, embedding, multimodal}. (근거: §14.2)
- REQ-04-CATALOG-003 (Unwanted): IF 코드에서 모델명, API 키, base URL이 문자열 리터럴로 하드코딩되면, THEN THE SYSTEM SHALL CI에서 거부한다. (근거: §3.8, 작성자 지침)
- REQ-04-CATALOG-004 (Ubiquitous): THE SYSTEM SHALL `.env`는 Provider/Key/사용 가능한 모델 식별자만 제공하고, 기능 키 ↔ 모델 매핑은 `FeatureModelPolicy`에만 둔다. (근거: §14)

### 3.2 기능별 정책 (REQ-04-POLICY)

- REQ-04-POLICY-001 (Ubiquitous): THE SYSTEM SHALL 다음 9개 기능 키를 정의한다(고정): `TrendResearch`, `ConceptChat`, `UserSketchAnalysis`, `ReferenceAnalysis`, `Abstraction`, `SketchPrompt`, `ImageGeneration`, `SpecWriting`, `Verification`. (근거: §14.1)
- REQ-04-POLICY-002 (Ubiquitous): THE SYSTEM SHALL `FeatureModelPolicy(feature_key, primary_model_id, fallback_model_ids[], parameters, max_cost_per_call, max_tokens, version, active, reviewer)`로 정책을 보관한다. (근거: §14.2)
- REQ-04-POLICY-003 (Ubiquitous): THE SYSTEM SHALL `PromptPolicy(feature_key, prompt_version, system_prompt, user_template, active, reviewer)`로 프롬프트를 분리 관리한다. (근거: §14.2)
- REQ-04-POLICY-004 (Event-driven): WHEN 정책이 변경되면, THE SYSTEM SHALL 새 버전을 발행하고 이전 버전은 보관(롤백 가능)한다. (근거: §22)
- REQ-04-POLICY-005 (Ubiquitous): THE SYSTEM SHALL 모든 정책 변경은 SPEC-01 `AuditLog`에 actor·target·diff_digest로 기록한다. (근거: §13.2)
- REQ-04-POLICY-006 (Ubiquitous): THE SYSTEM SHALL `FeatureModelPolicy` 시드 데이터에서 `feature_key='ImageGeneration'`의 primary는 `bytedance/seedream-4.5`(provider=`bytedance`, model_name=`seedream-4.5`, base_url=`https://ark.ap-southeast.bytepluses.com/api/v3`, endpoint_path=`/images/generations`, api_key_env=`BYTEDANCE_SEEDREAM_API_KEY`, auth=`Bearer`)로 설정하고, fallback 체인은 `[bytedance/seedream-4.5 → alibaba/z-image-turbo → google/gemini-3.1-flash-image-preview(별칭 nanobanana2) → openai/gpt-image-2]` 4단계로 정의한다. 체인은 관리자 콘솔에서 수정 가능하며, 모든 변경은 REQ-04-POLICY-004 버전 발행을 따른다. (근거: 작성자 지침, §14)
- REQ-04-POLICY-007 (Ubiquitous): THE SYSTEM SHALL Provider 시드에 `bytedance`(BytePlus Ark, base_url=`https://ark.ap-southeast.bytepluses.com/api/v3`, endpoint_path=`/images/generations`, api_key_env=`BYTEDANCE_SEEDREAM_API_KEY`, auth_scheme=`Bearer`), `alibaba`(api_key_env=`ALIBABA_API_KEY`), `google`(image 모델 가능: `gemini-3.1-flash-image-preview`/별칭 `nanobanana2`, api_key_env=`GEMINI_API_KEYS`), `openai`(api_key_env=`OPENAI_API_KEY`, image model `gpt-image-2`)을 포함한다. 키 부재 시 해당 Provider는 자동 비활성으로 표기되고 fallback 체인에서 건너뛴다. 어댑터 위치는 `apps/generation/infrastructure/image_providers/{seedream,alibaba_zimage,gemini_image,openai_image}_adapter.py`로 한다.

### 3.3 ModelRouter 동작 (REQ-04-ROUTER)

- REQ-04-ROUTER-001 (Ubiquitous): THE SYSTEM SHALL `ModelRouter.invoke(feature_key, payload, options)`를 단일 진입점으로 제공하고, 호출자는 모델명/Provider를 알 필요가 없다. (근거: §14, §17)
- REQ-04-ROUTER-002 (Ubiquitous): THE SYSTEM SHALL 라우터는 활성 `FeatureModelPolicy`를 조회하여 primary 모델 호출, 실패 시 정의된 fallback 후보로 순차 재시도한다. (근거: §14)
- REQ-04-ROUTER-003 (Unwanted): IF 모든 모델 호출이 실패하면, THEN THE SYSTEM SHALL 거짓 결과 또는 placeholder 결과를 반환하지 않고, 명시적 실패(`error_code`, `failed_models[]`, `last_error`)를 반환한다. (근거: §14, 작성자 지침)
- REQ-04-ROUTER-004 (Ubiquitous): THE SYSTEM SHALL 호출마다 `tokens_in`, `tokens_out`, `cost_estimate`, `latency_ms`, `provider`, `model`, `success/failure`, `feature_key`, `tenant_id`, `workspace_id`, `session_id`를 메트릭으로 수집한다.
- REQ-04-ROUTER-005 (State-driven): WHILE 정책의 `max_cost_per_call`을 초과할 가능성이 있으면, THE SYSTEM SHALL 호출 전 차단하고 “비용 한도 초과”로 명확히 보고한다. (근거: §22)
- REQ-04-ROUTER-006 (Ubiquitous): THE SYSTEM SHALL 모든 호출은 SPEC-01 NFR의 SSRF allowlist와 객체 스토리지 정책을 준수한다.
- REQ-04-ROUTER-007 (Optional): WHERE Verification 기능이 활성화된 경우, THE SYSTEM SHALL 1차 결과를 별도 정책의 모델로 검증하고 불일치 시 사용자에게 명시한다. (근거: §14.1 Verification)

### 3.4 관리자 콘솔 (REQ-04-ADMIN)

- REQ-04-ADMIN-001 (Ubiquitous): THE SYSTEM SHALL 관리자 콘솔(포트 14001)은 사용자 워크스페이스(14000)와 분리된 Django 앱/사이트로 운영한다. (근거: §13)
- REQ-04-ADMIN-002 (Ubiquitous): THE SYSTEM SHALL 관리자 콘솔은 다음 화면을 제공한다: 테넌트/사용자/권한, 트렌드 출처 큐(SPEC-02 큐 임베드), 모델 카탈로그, 기능별 정책, 프롬프트 정책, 메트릭 대시보드, 감사 로그 뷰, 롤백. (근거: §11.7)
- REQ-04-ADMIN-003 (Ubiquitous): THE SYSTEM SHALL 관리자 콘솔의 모든 변경은 정책 버전·변경 로그와 SPEC-01 AuditLog 두 곳에 기록한다. (근거: §22)
- REQ-04-ADMIN-004 (Event-driven): WHEN 관리자가 “롤백” 액션을 수행하면, THE SYSTEM SHALL 지정 버전의 정책을 활성화하고 변경 로그에 사유를 저장한다. (근거: §22)
- REQ-04-ADMIN-005 (Unwanted): IF 관리자가 다른 테넌트의 사용자 데이터에 직접 접근을 시도하면, THEN THE SYSTEM SHALL 권한 매트릭스에 따라 차단하고 침해 시도로 기록한다. (근거: SPEC-01 REQ-01-TENANT-005)
- REQ-04-ADMIN-006 (Ubiquitous): THE SYSTEM SHALL 관리자 콘솔의 모든 화면을 실제 운영 가능한 SSR/Vanilla JS UI로 구현하며, 목록·상세·생성·수정·비활성·롤백·검증·필터·검색·페이지네이션·빈 상태·오류 상태·권한 없음 상태를 제공한다.
- REQ-04-ADMIN-007 (Ubiquitous): THE SYSTEM SHALL 정책 편집 화면에서 primary/fallback 체인의 모델 타입·활성 상태·키 존재·비용 한도·지원 modality를 저장 전 검증하고, 충돌이 있으면 저장을 막고 수정 가능한 필드 단위 오류를 표시한다.
- REQ-04-ADMIN-008 (Ubiquitous): THE SYSTEM SHALL 트렌드 큐/모델 호출/비용 대시보드는 실제 작업 로그와 상태 전이를 표시한다. 로딩은 SPEC-05와 동일한 스켈레톤 + 작업 로그 패턴을 사용하며 단순 스피너만 사용하는 화면을 금지한다.
- REQ-04-ADMIN-009 (Ubiquitous): THE SYSTEM SHALL 관리자 UI도 ko/en/zh-CN/zh-TW i18n 키와 WCAG 2.1 AA 접근성 기준을 따른다. 하드코딩 자연어 라벨과 색상만으로 의미를 전달하는 UI를 금지한다.

### 3.5 모니터링·메트릭 (REQ-04-METRIC)

- REQ-04-METRIC-001 (Ubiquitous): THE SYSTEM SHALL 기능 키별 일/주/월 단위 비용·토큰·실패율 집계 뷰를 제공한다. (근거: §11.7, §22)
- REQ-04-METRIC-002 (Event-driven): WHEN 일일 비용이 임계값을 초과하면, THE SYSTEM SHALL 관리자 알림(이메일/콘솔)을 발생시킨다. (근거: §22)
- REQ-04-METRIC-003 (Ubiquitous): THE SYSTEM SHALL 메트릭은 PostgreSQL 집계 테이블 + Celery beat 주기 집계 + 콘솔 SSR 페이지로 노출한다(외부 옵저버빌리티 SaaS 강제 의존 없음).

---

## 4. 인수 기준 (Acceptance Criteria)

- AC-04-P-001: Given 정책에 primary 모델만 있고 fallback이 없을 때, When primary 호출이 실패하면, Then 라우터는 거짓 결과를 만들지 않고 `error_code=ALL_MODELS_FAILED`와 함께 호출자에게 실패를 반환한다. (REQ-04-ROUTER-003)
- AC-04-P-002: Given 정책 v3이 활성 상태이고 v2가 보관 중일 때, When 관리자가 “v2로 롤백”을 누르면, Then v2가 활성화되고 v3은 보관 상태가 되며 변경 로그에 사유가 저장된다. (REQ-04-POLICY-004, REQ-04-ADMIN-004)
- AC-04-P-003: Given `FeatureModelPolicy.max_cost_per_call=$0.05`일 때, When 추정 비용이 0.07로 산정되면, Then 호출은 차단되고 사용자/시스템에 “비용 한도 초과”가 표시된다. (REQ-04-ROUTER-005)
- AC-04-P-004: Given 코드 검사 시 문자열 리터럴 모델명 `"gpt-4o"` 또는 `os.environ["OPENAI_API_KEY"]`이 비공식 위치에서 발견되면, When CI가 실행되면, Then 빌드는 실패한다. (REQ-04-CATALOG-003)
- AC-04-A-005: Given 일반 사용자가 관리자 콘솔(14001)에 접근을 시도할 때, When 권한이 없으면, Then 403이 반환되고 AuditLog에 기록된다. (REQ-04-ADMIN-005)
- AC-04-M-006: Given 1주일치 호출이 누적되었을 때, When 메트릭 대시보드를 조회하면, Then 9개 기능 키 각각에 대해 비용/토큰/성공률/실패 모델 목록이 표시된다. (REQ-04-METRIC-001)
- AC-04-P-007: Given 신규 설치 후 시드 마이그레이션이 적용된 환경에서, When `FeatureModelPolicy(feature_key='ImageGeneration')`를 조회하면, Then primary는 `bytedance/seedream-4.5`이고 fallback은 `[alibaba/z-image-turbo, google/gemini-3.1-flash-image-preview, openai/gpt-image-2]` 정확히 3단계(전체 4단계)로 등록되어 있으며 `google/gemini-3.1-flash-image-preview`는 별칭 `nanobanana2`로도 조회 가능하다. 또한 `ModelProvider` 시드에 `bytedance`(base_url=`https://ark.ap-southeast.bytepluses.com/api/v3`, endpoint_path=`/images/generations`, api_key_env=`BYTEDANCE_SEEDREAM_API_KEY`), `google`(api_key_env=`GEMINI_API_KEYS`), `openai`(api_key_env=`OPENAI_API_KEY`) Provider가 존재한다. (REQ-04-POLICY-006, REQ-04-POLICY-007)
- AC-04-U-008: Given 관리자가 기능별 정책 편집 화면에서 image 모델이 아닌 text 모델을 `ImageGeneration` fallback에 추가하려 할 때, When 저장을 누르면, Then 저장은 차단되고 modality 충돌, 예상 영향, 수정 액션이 필드 단위 오류로 표시된다. (REQ-04-ADMIN-007)
- AC-04-U-009: Given 트렌드 수집 큐에 실패 항목 1건과 재시도 가능 항목 1건이 있을 때, When 관리자 콘솔 큐 화면이 로드되면, Then 두 상태가 다른 시각 토큰/라벨/액션으로 표시되고 재시도 버튼은 권한 있는 관리자에게만 활성화된다. (REQ-04-ADMIN-006, REQ-04-ADMIN-008)
- AC-04-U-010: Given 관리자 콘솔의 모델 메트릭 대시보드가 데이터를 로딩 중일 때, When 화면을 확인하면, Then 차트/테이블 모양의 스켈레톤과 실제 집계 작업 로그가 함께 보이고 단순 스피너만 있는 요소는 없다. (REQ-04-ADMIN-008)

---

## 5. 도메인 모델 (Domain Model)

### 5.1 엔티티
- `ModelProvider(id, name, api_key_env, base_url, endpoint_path, auth_scheme, active)`
- `ModelCatalog(id, provider_id, model_name, type, context_limit, cost_estimate, modalities, active)`
- `FeatureModelPolicy(id, feature_key, primary_model_id, fallback_model_ids[], parameters, max_cost_per_call, max_tokens, version, active, reviewer, created_at)`
- `PromptPolicy(id, feature_key, prompt_version, system_prompt, user_template, active, reviewer, created_at)`
- `ModelInvocation(id, feature_key, tenant_id, workspace_id, session_id, model_id, status, tokens_in, tokens_out, cost_estimate, latency_ms, error_code?, error_summary?, created_at)`
- `PolicyChangeLog(id, target_type, target_id, version_from, version_to, actor_id, reason, created_at)`

### 5.1.1 관리자 화면 모델

```text
AdminConsoleViewModel {
  active_tenant_id, actor_role, nav_sections[],
  health_summary, pending_actions[], permission_matrix,
  i18n_locale, csrf_meta
}

PolicyEditorViewModel {
  feature_key, active_policy, draft_policy,
  provider_options[], model_options[], validation_errors[],
  estimated_cost_impact, fallback_chain_preview, diff_summary
}

OperationsQueueViewModel {
  queue_kind, filters, rows[], retryable_count,
  failed_count, selected_row_detail?, next_actions[]
}
```

### 5.2 라우팅 도식

```mermaid
flowchart LR
  Caller[Caller (SPEC-02/03)] --> Router[ModelRouter]
  Router --> PolicyRepo[FeatureModelPolicy/PromptPolicy]
  Router --> Catalog[ModelCatalog]
  Router --> Provider[Provider Adapter]
  Provider --> External[(LLM/Vision/Image API)]
  Router --> Metrics[ModelInvocation Metrics]
  Router --> Audit[AuditLog]
  Router -->|fail| Fallback[Fallback Loop]
  Fallback --> Provider
```

### 5.3 9개 기능 키 매핑(고정)

| 기능 키 | 사용처 | 모델 type 기대치 |
|---|---|---|
| TrendResearch | SPEC-02 인사이트 추출 | text/search |
| ConceptChat | SPEC-01 챗 + SPEC-03 컨셉 토론 | chat |
| UserSketchAnalysis | SPEC-01 SketchAnalysis | vision/multimodal |
| ReferenceAnalysis | SPEC-02 ReferenceAnalysis | vision/multimodal |
| Abstraction | SPEC-03 AbstractionRule 도출 | text/chat (reasoning) |
| SketchPrompt | SPEC-03 SketchPrompt 작성 | text |
| ImageGeneration | SPEC-03 GenerationJob | image |
| SpecWriting | SPEC-03 SpecDocument 작성 | text (long-context) |
| Verification | SPEC-04 옵셔널 검증 | text/vision |

---

## 6. 아키텍처 결정 (Architecture Decisions)

### 6.1 라이브러리 채택/보류

| 후보 | 판정 | 사유 |
|---|---|---|
| 자체 ModelRouter (Python, Django app) | 채택 | 코드 하드코딩 금지 + 정책 외부화 강제 |
| Dify | 보류 | 워크플로우 외주는 운영 종속성 ↑, 본 시스템은 자체 라우터에 정책 관리 콘솔만 |
| LangChain/LiteLLM 등 | 보류(검토) | 도입 시 Provider Adapter 계층에서만 선택적 사용. 현 SPEC은 비의존 |
| 옵저버빌리티 SaaS(Datadog 등) | 보류 | 자체 PostgreSQL 집계로 시작 |
| `seedream_adapter` (BytePlus Ark) | 채택(이미지 기본) | `apps/generation/infrastructure/image_providers/seedream_adapter.py`. POST `{base_url}{endpoint_path}` + Bearer 인증. `BYTEDANCE_SEEDREAM_API_KEY` |
| `alibaba_zimage_adapter` (z-image-turbo) | 채택(이미지 fallback #1) | `image_providers/alibaba_zimage_adapter.py`. `ALIBABA_API_KEY` |
| `gemini_image_adapter` (gemini-3.1-flash-image-preview / 별칭 nanobanana2) | 채택(이미지 fallback #2) | `image_providers/gemini_image_adapter.py`. `GEMINI_API_KEYS` |
| `openai_image_adapter` (gpt-image-2) | 채택(이미지 fallback #3) | `image_providers/openai_image_adapter.py`. `OPENAI_API_KEY` |

### 6.2 모듈 경계
- `apps/model_catalog`: Provider/Catalog/FeatureModelPolicy/PromptPolicy/ModelInvocation/PolicyChangeLog
- `apps/admin_console`: 관리자 화면, 권한, 메트릭 뷰. 본 모듈은 `model_catalog`, SPEC-01 `accounts`/`audit_logs`, SPEC-02 트렌드 큐 뷰를 application port로만 호출

### 6.3 포트 사용 (SPEC-01 §6.2)
- 14001 = 관리자 콘솔 Django 사이트
- 14060 = ModelRouter 헬스/메트릭 스크레이프 엔드포인트

### 6.4 Clean Architecture 4-layer 매핑
- domain: 정책/카탈로그/라우팅 결정 VO
- application: `InvokeModel` UseCase, 정책 CRUD UseCase, 롤백 UseCase, 메트릭 집계 UseCase
- infrastructure: Provider 어댑터(텍스트/비전/이미지/검색), 메트릭 Repository
- presentation: 관리자 Django 사이트(14001), 모델/정책/큐/감사/메트릭 SSR 템플릿, Vanilla JS 상호작용, i18n/접근성/스켈레톤 상태

---

## 7. 비기능 요구사항 (NFR)

- NFR-04-PERF-001: ModelRouter 자체 오버헤드 p95 ≤ 30ms (네트워크 호출 시간 제외).
- NFR-04-SEC-001: API 키는 `.env`에서만 로드, 메모리 외 직렬화 금지(로그/예외 메시지에 마스킹).
- NFR-04-SEC-002: 관리자 콘솔은 별도 도메인/포트로 운영, 강제 MFA 옵션 지원.
- NFR-04-OBS-001: `ModelInvocation`은 최소 90일 보관(테넌트별 설정 가능), 익명화 후 장기 보관.
- NFR-04-COMP-001: 외부 모델 사용에 대한 “AI 사용 고지” 메타가 SPEC-03 SpecDocument와 SPEC-05 사용자 화면에서 자동 노출되도록 정책 출력에 포함.
- NFR-04-LIC-001: Provider별 사용 약관/지역 제한을 카탈로그에 기록.
- NFR-04-UX-001: 관리자 콘솔은 운영자가 3클릭 이내에 실패 원인, 영향 범위, 복구 액션을 찾을 수 있어야 한다.
- NFR-04-A11Y-001: 관리자 콘솔은 SPEC-05와 동일하게 WCAG 2.1 AA, 키보드 탐색, 포커스 인디케이터, ARIA 라벨, i18n 4언어를 만족한다.

---

## 8. 불변 조건 (Invariants)

- INV-04-01: 모델명/Provider 식별자/키는 코드에 하드코딩되지 않는다. (User_Needs §3.8)
- INV-04-02: ModelRouter는 거짓 결과를 만들지 않는다. 실패는 `error_code` 형태로만 반환한다. (§14)
- INV-04-03: 정책 변경은 새 버전을 만든다(파괴적 수정 금지). (§22)
- INV-04-04: 9개 기능 키 외의 새 기능 키는 SPEC 개정 + 본 SPEC §5.3 갱신을 통해서만 추가된다.
- INV-04-05: 모든 모델 호출은 `tenant_id`/`workspace_id`/`session_id`를 추적 메타로 갖는다. (SPEC-01 INV-01-05)
- INV-04-06: 관리자 콘솔의 UI 상태는 실제 도메인 상태와 일치해야 하며, 키 누락·모델 비활성·fallback 실패를 정상처럼 보이게 하는 표시용 fallback을 금지한다.

---

## 9. 위험과 대응 (Risks)

| 위험 (User_Needs §22) | 대응 |
|---|---|
| 모델 비용 증가 | `max_cost_per_call` + 메트릭 알림 + 정책 롤백 |
| 모델 실패 누수 | 명시적 실패 반환, 거짓 fallback 금지 |
| 관리자 설정 오류 | 정책 버전·변경 로그·롤백 |
| Provider 장애 | fallback 후보 정의 + 다른 Provider 전환 |
| 키 유출 | `.env` 격리 + 로그 마스킹 + AuditLog |
| 관리자 UI와 실제 정책 불일치 | 저장 전 정책 검증 + diff preview + 실제 활성 정책 재조회 후 렌더 |
| 운영 이슈 원인 파악 지연 | 큐/모델/비용 화면에 원인·영향·복구 액션을 함께 표시 |

---

## 10. 의존성 (Dependencies)

- SPEC-01: 멀티테넌시·AuditLog·계정/권한 (관리자 콘솔 권한 가드)
- SPEC-02: 호출자(TrendResearch, ReferenceAnalysis), 트렌드 출처 큐(콘솔에서 임베드)
- SPEC-03: 호출자(ConceptChat, Abstraction, SketchPrompt, ImageGeneration, SpecWriting, Verification)
- SPEC-05: 관리자 콘솔 UX는 SPEC-05의 i18n/접근성 표준을 준수

---

## 11. 범위 외 (Out of Scope)

- 트렌드 수집 자체(SPEC-02), 컨셉/생성/스펙(SPEC-03), 사용자 화면(SPEC-05)
- 외부 옵저버빌리티 SaaS 통합

---

## 12. 추적 매트릭스 (Traceability)

| REQ ID | User_Needs 매핑 | 인수 기준 |
|---|---|---|
| REQ-04-CATALOG-003 | §3.8, §14 | AC-04-P-004 |
| REQ-04-POLICY-001 | §14.1 | (9 키 정의) |
| REQ-04-POLICY-002 | §14.2 | (정책 스키마) |
| REQ-04-POLICY-004 | §22 | AC-04-P-002 |
| REQ-04-ROUTER-003 | §14, 작성자 지침 | AC-04-P-001 |
| REQ-04-ROUTER-005 | §22 | AC-04-P-003 |
| REQ-04-ADMIN-002 | §11.7 | AC-04-A-005, AC-04-U-009 |
| REQ-04-ADMIN-004 | §22 | AC-04-P-002 |
| REQ-04-ADMIN-006~009 | §11.7, §12, 사용자 추가 지시 | AC-04-U-008, AC-04-U-009, AC-04-U-010 |
| REQ-04-METRIC-001 | §11.7, §22 | AC-04-M-006 |

---

문서 종료. 본 SPEC의 ModelRouter는 SPEC-02·SPEC-03 모든 모델 호출의 단일 진입점이며, 관리자 콘솔은 SPEC-05의 사용자 워크스페이스와 분리된다.
