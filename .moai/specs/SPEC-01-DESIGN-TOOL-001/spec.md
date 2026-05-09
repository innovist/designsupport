# SPEC-DESIGN-TOOL-001: 범용 디자인 창작 지원 시스템

**버전**: 1.1.0  
**상태**: DRAFT  
**작성일**: 2026-05-09  
**최종 업데이트**: 2026-05-09 (research.md 기반 갭 보완)  
**기반 문서**: User_Needs_v01.md  

---

## 1. 개요

### 1.1 제품 정의

이 시스템은 **근거 기반 디자인 발상 시스템**이다. 디자이너의 창작 과정을 지원하며:
- 목적을 구조화하고
- 트렌드와 실제 레퍼런스를 근거로 컨셉을 결정하며
- 레퍼런스를 디자인 문법으로 추상화하고
- 결과를 검토 가능한 스펙 문서로 남긴다

이미지 편집 도구나 캔버스 편집기가 **아니다**.

### 1.2 기술 스택

| 영역 | 선택 |
|---|---|
| Backend | FastAPI |
| Database | PostgreSQL |
| Migration | Alembic |
| Template | Jinja2 (기존 레거시 HTML 유지) |
| Frontend | Vanilla HTML, Vanilla JS, Vanilla CSS |
| Auth | 없음 (단일 사용자) |
| File Storage | 로컬 파일 저장소 (./uploads/) |
| AI Provider | .env 기반 API Key + 워크스페이스 설정 |

### 1.3 아키텍처 원칙

- 관리자 페이지 없음 — 설정은 워크스페이스 내부
- 인증 없음 — 단일 사용자 워크스페이스
- 기존 레거시 HTML 템플릿 유지 (base.html, pages/)
- 신규 기능은 기존 화면의 패널/모달/카드 패턴으로 삽입
- 하드코딩 분류 없음 — DB 설정과 사용자 입력으로 확장
- 거짓 fallback 없음 — 실패는 실패로 명시

---

## 2. 도메인 모델

### 2.1 핵심 엔티티

```
Workspace (1개)
├── WorkspaceSetting (1:1)
├── FeatureModelSetting (1:N, 기능별 AI 모델 설정)
├── DesignProject (1:N)
│   └── DesignSession (1:N)
│       ├── DesignBrief (1:1)
│       ├── ChatMessage (1:N)
│       ├── UserSketchAsset (1:N)
│       │   └── SketchAnalysis (1:1) *설계 결정: 스케치당 분석 1건 유지
│       ├── ConceptCandidate (1:N)
│       │   └── ConceptDecision (1:N)
│       ├── ReferenceAsset (1:N)
│       │   └── ReferenceAnalysis (1:1)
│       ├── AbstractionRule (1:N)
│       ├── GeneratedDesign (1:N)
│       ├── DesignEvaluation (1:N)
│       └── SpecDocument (1:N)
TrendSource (N)
├── TrendDocument (1:N)
│   └── TrendInsight (1:N)
WorkspaceTrendSetting (1개)
```

### 2.2 테이블 정의

| 테이블 | 주요 필드 |
|---|---|
| workspace | id, name, created_at |
| workspace_setting | workspace_id, default_domain, recency_policy |
| feature_model_setting | workspace_id, feature_key, provider, model, temperature, max_tokens, extra_params | feature_key 목록은 섹션 2.3 참조 |
| design_project | id, workspace_id, name, domain, purpose, status, created_at |
| design_session | id, project_id, mode (chatbot/auto/sketch), pipeline_stage, status, created_at |
| design_brief | id, session_id, purpose, domain, target_user, context, constraints, use_case |
| chat_message | id, session_id, role (user/assistant), content, stage, evidence_links, created_at |
| user_sketch_asset | id, session_id, file_path, original_filename, user_memo, upload_at, is_deleted |
| sketch_analysis | id, sketch_id, intent, form_elements, structure_elements, unclear_points, questions, keep_elements, vary_elements, created_at |
| concept_candidate | id, session_id, name, description, score, rationale, risk, evidence_ids, status, created_at |
| concept_decision | id, candidate_id, decision (adopt/hold/discard/explore), decider (user/auto), reason, created_at |
| reference_asset | id, session_id, url, title, thumbnail_path, source_domain, license_type, copyright_risk, collected_at, published_at, domain_tags, relevance_reason, abstraction_elements |
| reference_analysis | id, reference_id, form_grammar, structure_grammar, material_direction, meaning_symbols, usability_notes, replication_risk, abstraction_fitness, created_at |
| abstraction_rule | id, session_id, source_type (reference/sketch), source_id, form, structure, surface, color_material, meaning, usability, sketch_prompt, risk_notes, created_at |
| generated_design | id, session_id, rule_id, prompt, provider, model, image_path, status, generation_params, created_at |
| design_evaluation | id, session_id, candidate_designs, criteria, scores, winner_id, notes, created_at |
| spec_document | id, session_id, version, content_json, status (draft/review/approved), created_at |
| trend_source | id, name, url, domain, crawl_interval, reliability_score, license_notes, is_active |
| trend_document | id, source_id, title, url, published_at, collected_at, raw_file_path, parsed_text, content_hash |
| trend_insight | id, document_id, summary, keywords, domain_tags, evidence_quote, confidence_score |
| workspace_trend_setting | workspace_id, enabled_source_ids, default_domain, recency_days |

### 2.3 Feature Key 목록

`feature_model_setting.feature_key` 값으로 사용되는 9개 식별자:

| feature_key | 담당 유스케이스 | 모달리티 |
|---|---|---|
| `abstraction` | generate_abstraction | 텍스트 |
| `sketch_analysis` | analyze_sketch | 비전(이미지 입력) |
| `concept_generation` | generate_concepts | 텍스트 |
| `chat` | send_message | 텍스트 |
| `image_generation` | create_generation_job | 이미지 생성 |
| `reference_analysis` | search_references (분석 단계) | 텍스트 |
| `brief_structuring` | structure_brief | 텍스트 |
| `spec_writing` | generate_spec | 텍스트 |
| `trend_analysis` | search_trends (인사이트 추출) | 텍스트 |

### 2.4 자동 모드 파이프라인 상태

`design_session.pipeline_stage` 값 (9가지):

| 상태 값 | 의미 | 전이 조건 |
|---|---|---|
| `queued` | 실행 대기 | 자동 모드 시작 시 초기값 |
| `researching` | 트렌드 조사 중 | queued 완료 후 |
| `concepting` | 컨셉 후보 생성 중 | researching 완료 후 |
| `referencing` | 레퍼런스 수집 중 | concepting 완료 후 |
| `abstracting` | 추상화 규칙 생성 중 | referencing 완료 후 |
| `generating` | 이미지 생성 중 | abstracting 완료 후 |
| `documenting` | 스펙 문서 생성 중 | generating 완료 후 |
| `review_ready` | 검토 대기 (완료) | documenting 완료 후 |
| `failed` | 실패 | 임의 단계 오류 시 |

---

## 3. EARS 형식 요구사항

### 3.1 워크스페이스와 설정 (Phase 1)

**REQ-WS-001**: WHEN 앱이 처음 실행되면, THE SYSTEM SHALL 기본 Workspace와 WorkspaceSetting을 자동 생성한다.

**REQ-WS-002**: WHEN 사용자가 `/workspace/settings`에 접근하면, THE SYSTEM SHALL 현재 설정을 조회하고 편집 가능한 UI를 표시한다.

**REQ-WS-003**: WHEN 사용자가 기능별 AI 모델 설정을 저장하면, THE SYSTEM SHALL provider, model, temperature, max_tokens를 `feature_model_setting`에 저장하고 성공 여부를 반환한다.

**REQ-WS-004**: IF API Key가 .env에 설정되지 않았거나 FeatureModelSetting이 없으면, THE SYSTEM SHALL 해당 기능 실행 전에 명확한 안내와 설정 페이지 CTA를 표시하고 기능 실행을 차단한다.

**REQ-WS-005**: WHEN API Key 원문을 UI에 요청하면, THE SYSTEM SHALL Key alias만 표시하고 원문을 절대 반환하지 않는다.

**REQ-WS-006**: WHEN 사용자가 위험한 설정(데이터 삭제, 파일 초기화 등)을 요청하면, THE SYSTEM SHALL 즉시 저장하지 않고 확인 모달을 표시한다.

### 3.2 디자인 세션과 브리프 (Phase 2)

**REQ-SESSION-001**: WHEN 사용자가 새 디자인 세션을 생성하면, THE SYSTEM SHALL 자연어 목적 입력을 받고, 대상/도메인/결과물 형태를 추출해 `design_brief`에 저장한다.

**REQ-SESSION-002**: WHEN DesignBrief에 목적/도메인/대상/결과물 중 하나 이상이 누락되면, THE SYSTEM SHALL 챗봇을 통해 명확화 질문을 생성한다.

**REQ-SESSION-003**: WHEN 챗봇 메시지가 생성되면, THE SYSTEM SHALL 메시지를 session_id, stage, created_at과 함께 저장하고, 근거가 있는 주장에는 evidence_links를 포함한다.

**REQ-SESSION-004**: WHEN 자동 모드가 진행되면, THE SYSTEM SHALL queued/researching/concepting/referencing/abstracting/generating/documenting/review_ready/failed 상태를 실시간으로 업데이트하고 각 상태를 DB에 기록한다.

**REQ-SESSION-005**: WHEN 자동 모드에서 불확실성 임계값 초과 항목이 발견되면, THE SYSTEM SHALL 자동 진행을 중단하고 "검토 필요" 상태로 사용자에게 표시한다.

**REQ-SESSION-006**: THE SYSTEM SHALL 사용자가 특정 단계부터 재실행(rerun from step)할 수 있는 기능을 제공한다.

### 3.3 사용자 스케치 (Phase 3)

**REQ-SKETCH-001**: WHEN 사용자가 스케치를 업로드하면, THE SYSTEM SHALL 원본 파일을 `uploads/sketches/{session_id}/`에 저장하고 원본을 덮어쓰지 않는다.

**REQ-SKETCH-002**: WHEN 스케치 분석이 완료되면, THE SYSTEM SHALL 의도/형태 요소/구조 요소/불명확한 요소/질문을 `sketch_analysis`에 저장하고 사용자 확인이 필요한 항목을 표시한다.

**REQ-SKETCH-003**: WHEN AI가 스케치를 해석하면, THE SYSTEM SHALL "가설" 레이블을 붙이고 사용자 확인 이전에 결정 근거로 사용하지 않는다.

**REQ-SKETCH-004**: THE SYSTEM SHALL 사용자 업로드 스케치를 외부 ReferenceAsset과 별도 타입으로 구분하여 저장하고 표시한다.

### 3.4 레퍼런스 검색 (Phase 3)

**REQ-REF-001**: WHEN 레퍼런스 검색이 요청되면, THE SYSTEM SHALL 키워드/이미지/스케치 기반/문서 검색 유형을 지원하고, 각 결과에 source URL, 수집일, 발행일, 라이선스를 저장한다.

**REQ-REF-002**: WHEN 저작권 위험이 높은 레퍼런스가 탐지되면, THE SYSTEM SHALL 직접 스타일 적용을 차단하고 추상화 전용으로만 사용 가능하게 표시한다.

**REQ-REF-003**: WHEN 레퍼런스 카드가 표시되면, THE SYSTEM SHALL 썸네일/제목/출처 URL/수집일/라이선스/도메인 태그/관련 이유/추상화 가능 요소를 포함한다.

### 3.5 트렌드 조사 (Phase 3)

**REQ-TREND-001**: WHEN 트렌드 조사가 요청되면, THE SYSTEM SHALL 활성화된 TrendSource에서 문서를 검색하고, 결과에 출처 URL과 발행일을 포함한다.

**REQ-TREND-002**: WHEN 트렌드 주장이 저장되면, THE SYSTEM SHALL 출처가 없는 주장을 "가설" 또는 "검증 필요"로 표시하고 컨셉 결정 근거로 사용하지 않는다.

**REQ-TREND-003**: WHEN TrendInsight가 저장되면, THE SYSTEM SHALL document_id, evidence_quote, confidence_score를 필수 저장한다.

### 3.6 컨셉 후보와 결정 (Phase 4)

**REQ-CONCEPT-001**: WHEN 컨셉 후보가 생성되면, THE SYSTEM SHALL 각 후보에 이름/설명/점수/근거/리스크를 저장하고 UI에 표시한다.

**REQ-CONCEPT-002**: WHEN 사용자가 컨셉을 선택/보류/폐기/더 탐색 중 하나를 선택하면, THE SYSTEM SHALL `concept_decision`에 결정자/시각/사유를 저장한다.

**REQ-CONCEPT-003**: WHEN 자동 모드가 컨셉을 결정하면, THE SYSTEM SHALL 결정자를 "auto"로 기록하고 점수/근거/대안/리스크를 함께 저장한다.

### 3.7 추상화 (Phase 4)

**REQ-ABST-001**: WHEN 추상화가 요청되면, THE SYSTEM SHALL 형태/구조/표면/색상재료/의미/사용성 축 중 최소 2개를 도출하여 `abstraction_rule`에 저장한다.

**REQ-ABST-002**: THE SYSTEM SHALL 원본 레퍼런스 구도를 그대로 복제한 추상화 규칙을 생성하지 않는다.

**REQ-ABST-003**: WHEN 사용자 스케치 기반 추상화가 요청되면, THE SYSTEM SHALL 유지할 핵심 실루엣/강화할 구조/불명확한 기능 요소/구체화 방향 3~5개/원본 보존형 프롬프트/컨셉 확장형 프롬프트를 생성한다.

### 3.8 이미지 생성 (Phase 4)

**REQ-GEN-001**: WHEN 이미지 생성이 요청되면, THE SYSTEM SHALL 브리프/컨셉/레퍼런스/추상화 규칙 중 필요한 근거와 연결되어야 하며, 근거 없는 생성 요청을 차단한다.

**REQ-GEN-002**: WHEN 생성된 이미지가 저장되면, THE SYSTEM SHALL 사용된 모델/프롬프트/연결된 규칙/생성 파라미터를 함께 저장한다.

**REQ-GEN-003**: WHEN 생성 모델이 실패하면, THE SYSTEM SHALL 거짓 결과를 저장하지 않고 실패 상태, 실패 모델명, 재시도 가능 여부를 반환한다.

### 3.9 스펙 문서 (Phase 5)

**REQ-SPEC-001**: WHEN 스펙 문서가 생성되면, THE SYSTEM SHALL 프로젝트 브리프/트렌드 근거/컨셉 후보와 평가/최종 컨셉/스케치 분석/레퍼런스 보드/추상화 규칙/생성 이미지/버린 대안과 선택 사유/출처를 포함한다.

**REQ-SPEC-002**: THE SYSTEM SHALL 스펙 문서 버전 관리를 지원하고 이전 버전으로 되돌릴 수 있어야 한다.

**REQ-SPEC-003**: WHEN 스펙 문서가 표시되면, THE SYSTEM SHALL 모든 섹션의 출처 링크와 결정 로그를 검토 가능한 형태로 포함한다.

---

## 4. 파이프라인 불변 조건 (Invariants)

1. 출처 없는 트렌드 주장 → 컨셉 결정 근거로 사용 불가
2. 사용자 스케치 원본 → 절대 덮어쓰기 불가, 외부 레퍼런스와 구분
3. AI 해석 → "가설" 레이블 필수, 사용자 확인 전 결정 근거로 사용 불가
4. 자동 모드 결정 → Decision Log 저장 필수
5. 이미지 생성 요청 → 근거(브리프/컨셉/규칙) 연결 필수
6. 스펙 문서 → 버린 대안과 선택 사유 포함 필수
7. 저작권 위험 레퍼런스 → 직접 스타일 적용 차단
8. 설정 누락 → 기능 실행 차단 + 명확한 안내
9. 거짓 성공 응답 → 절대 금지 (실패는 실패로 표시)

---

## 5. API 엔드포인트

### 5.1 워크스페이스

```
GET  /workspace                          워크스페이스 홈
GET  /workspace/settings                 설정 페이지 (HTML)
GET  /api/workspace/settings             설정 조회 (JSON)
PUT  /api/workspace/settings             설정 저장
GET  /api/workspace/feature-models       기능별 모델 설정 조회
PUT  /api/workspace/feature-models/{feature_key}  기능별 모델 설정 저장
GET  /api/workspace/trend-settings       트렌드 설정 조회
PUT  /api/workspace/trend-settings       트렌드 설정 저장
GET  /api/workspace/api-key-aliases      API Key alias 목록 (원문 미반환)
```

### 5.2 프로젝트와 세션

```
GET  /projects                           프로젝트 목록 (HTML)
GET  /api/projects                       프로젝트 목록 (JSON)
POST /api/projects                       프로젝트 생성
GET  /api/projects/{project_id}          프로젝트 조회
POST /api/sessions                       세션 생성
GET  /api/sessions/{session_id}          세션 상세 조회 (JSON)
GET  /sessions/{session_id}              세션 워크스페이스 (HTML)
PATCH /api/sessions/{session_id}/stage   파이프라인 단계 업데이트
POST /api/sessions/{session_id}/brief    브리프 구조화
POST /api/sessions/{session_id}/rerun    특정 단계부터 재실행 (부분 구현)
```

### 5.3 대화

```
POST /api/sessions/{session_id}/messages    메시지 전송
GET  /api/sessions/{session_id}/messages    대화 내역 조회
```

### 5.4 스케치

```
POST /api/sessions/{session_id}/sketches              스케치 업로드
GET  /api/sessions/{session_id}/sketches              스케치 목록
GET  /api/sketches/{sketch_id}                        스케치 단건 조회
POST /api/sketches/{sketch_id}/analyze                스케치 AI 분석 실행
GET  /api/sketches/{sketch_id}/analysis               스케치 분석 결과 조회
POST /api/sketches/{sketch_id}/confirm-analysis       AI 해석 확인/수정
```

### 5.5 트렌드

```
POST /api/sessions/{session_id}/trends/search         트렌드 검색
GET  /api/sessions/{session_id}/trends                저장된 트렌드 인사이트 목록
GET  /api/trend-sources                               트렌드 소스 목록
POST /api/trend-sources                               트렌드 소스 등록
```

### 5.6 레퍼런스

```
POST /api/sessions/{session_id}/references/search     레퍼런스 검색
GET  /api/sessions/{session_id}/references            저장된 레퍼런스 목록
POST /api/references/{reference_id}/analyze           레퍼런스 분석
PATCH /api/references/{reference_id}/risk             라이선스 위험 표시 (부분 업데이트)
```

### 5.7 컨셉

```
POST /api/sessions/{session_id}/concepts              컨셉 후보 생성
GET  /api/sessions/{session_id}/concepts              컨셉 목록
POST /api/concepts/{concept_id}/decisions             컨셉 결정 기록
```

### 5.8 추상화

```
POST /api/sessions/{session_id}/abstractions          추상화 규칙 생성
GET  /api/sessions/{session_id}/abstractions          추상화 규칙 목록
```

### 5.9 생성

```
POST /api/sessions/{session_id}/generations           이미지 생성 요청
GET  /api/sessions/{session_id}/generations           생성 결과 목록
GET  /api/generations/{generation_id}                 생성 상태/결과 조회
```

### 5.10 스펙 문서

```
POST /api/sessions/{session_id}/specs                 스펙 문서 생성
GET  /api/sessions/{session_id}/specs                 스펙 문서 목록
GET  /api/specs/{spec_id}                             스펙 문서 조회
POST /api/specs/{spec_id}/version                     버전 생성
```

---

## 6. 디렉토리 구조

```
app/
  main.py                    FastAPI 앱 진입점
  core/
    config.py                환경 설정 (PostgreSQL, no auth)
    database.py              SQLAlchemy 세션 관리
    security.py              유틸리티 (없음 또는 최소화)
  api/
    routes/
      workspace.py           워크스페이스 설정 라우터
      sessions.py            세션/브리프 라우터
      conversations.py       챗봇 메시지 라우터
      assets.py              스케치 업로드 라우터
      trends.py              트렌드 조사 라우터
      references.py          레퍼런스 검색 라우터
      concepts.py            컨셉 후보/결정 라우터
      abstraction.py         추상화 라우터
      generation.py          이미지 생성 라우터
      specs.py               스펙 문서 라우터
    pages.py                 HTML 페이지 라우터 (레거시 유지)
  domain/
    entities/                Pydantic 도메인 엔티티
    services/                도메인 서비스
  application/
    use_cases/               유스케이스
    ports/                   포트 인터페이스
    dtos/                    데이터 전송 객체
  infrastructure/
    repositories/            SQLAlchemy 리포지토리
    ai_clients/              AI provider 클라이언트
    search/                  레퍼런스/트렌드 검색
    storage/                 파일 저장
    parsers/                 문서 파서
  models/                    SQLAlchemy ORM 모델
templates/                   레거시 Jinja2 템플릿 (유지)
static/                      정적 파일 (유지 + 신규 추가)
alembic/                     Alembic 마이그레이션
uploads/                     사용자 업로드 파일
```

---

## 7. 수락 기준 (Acceptance Criteria)

### AC-001 구조
- [ ] FastAPI 서버가 `uvicorn main:app`으로 정상 시작됨
- [ ] PostgreSQL 연결 성공 및 Alembic 마이그레이션 완료
- [ ] 레거시 HTML 템플릿이 기존과 동일하게 표시됨
- [ ] Django apps/ 및 관련 파일 완전 제거됨

### AC-002 워크스페이스 설정
- [ ] `/workspace/settings` 에서 기능별 모델 설정 가능
- [ ] API Key alias 조회 가능, 원문 미노출
- [ ] 설정 누락 시 기능 실행 차단 + 안내 표시

### AC-003 세션 파이프라인
- [ ] 세션 생성 → 브리프 구조화 → 챗봇 대화 흐름 동작
- [ ] 파이프라인 단계별 상태 저장 및 조회
- [ ] 재실행(rerun from step) API 라우트 존재 (뼈대 구현, 완전 동작은 다음 SPEC으로 이월)

### AC-004 스케치
- [ ] 스케치 업로드 시 원본 보존
- [ ] AI 해석 결과에 "가설" 레이블 표시
- [ ] 외부 레퍼런스와 구분된 스케치 카드 표시

### AC-005 레퍼런스/트렌드
- [ ] 레퍼런스 검색 결과에 출처/수집일/라이선스 포함
- [ ] 저작권 위험 레퍼런스 직접 적용 차단
- [ ] 트렌드 주장에 출처 연결 (없으면 "가설" 표시)

### AC-006 컨셉/추상화/생성
- [ ] 컨셉 후보 카드에 점수/근거/리스크 표시
- [ ] 채택/보류/폐기/더 탐색 결정이 DB 저장됨
- [ ] 추상화 규칙에 최소 2개 축 포함
- [ ] 이미지 생성에 근거 연결 필수

### AC-007 스펙 문서
- [ ] 스펙 문서에 버린 대안과 선택 사유 포함
- [ ] 버전 관리 동작

### AC-008 UX
- [ ] 생성/검색/분석 대기 중 스켈레톤 로딩 표시
- [ ] 빈 상태에 다음 행동 제안 표시
- [ ] 신규 UI가 기존 레거시 디자인과 시각적으로 단절 없음

---

## 8. 구현 우선순위

### Phase 1 (필수 기반)
1. 불필요한 코드/파일 삭제 (apps/, config/, manage.py 등)
2. FastAPI 구조 정리 + PostgreSQL 연결 + Alembic 설정
3. 핵심 ORM 모델 전체 작성 (17개 테이블)
4. 워크스페이스 초기화 로직
5. 워크스페이스 설정 API + UI

### Phase 2 (세션 흐름)
1. 프로젝트 + 세션 생성 API
2. 브리프 구조화 API (AI 기반)
3. 챗봇 대화 API
4. 파이프라인 상태 관리
5. Decision Panel UI

### Phase 3 (증거 수집)
1. 스케치 업로드 + 분석 API
2. 레퍼런스 검색 + 저장 API
3. 트렌드 조사 API
4. 레퍼런스 카드 + 스케치 카드 UI
5. 스켈레톤 로딩 UI

### Phase 4 (컨셉과 생성)
1. 컨셉 후보 생성 + 결정 API
2. 추상화 규칙 생성 API
3. 이미지 생성 요청 API
4. 자동 모드 상태 실시간 표시

### Phase 5 (스펙과 검증)
1. 스펙 문서 생성 API
2. 버전 관리
3. 전체 파이프라인 검증
4. 오류 상황 처리

---

---

## 9. 설계 결정 기록

### D-001: SketchAnalysis 1:1 관계

- **User_Needs 원문**: `UserSketchAsset (1:N) → SketchAnalysis`
- **구현 결정**: `sketch_analysis.sketch_id`에 UNIQUE 제약 적용 → 1:1
- **이유**: 스케치당 최신 분석 1건 유지가 UX상 명확하고 단순함. 분석 재실행 시 기존 레코드 업데이트.
- **영향**: `analyze_sketch` 유스케이스는 기존 분석 존재 시 덮어씀.

### D-002: 배치 추상화 (source_id 선택적)

- **배경**: UI에서 "추상화 생성" 버튼은 source_type만 전달, 개별 source_id를 전달하지 않음.
- **구현 결정**: `POST /api/sessions/{id}/abstractions` 요청에서 `source_id`를 선택적(optional)으로 처리.
  - `source_id` 없음 → 세션 내 분석 완료된 전체 소스에 대해 배치 생성.
  - `source_id` 있음 → 단건 생성.
- **영향**: `generate_abstraction.py`에 `generate_abstractions_for_session()` 함수 추가.

---

## 10. 이월 항목 (다음 SPEC)

이 SPEC 범위에 포함하지 않는 항목들. 현재 수락 기준(AC)에서 제외됨.

| 항목 | 상태 | 이유 |
|---|---|---|
| `rerun_step` 완전 구현 | ⚠️ 뼈대만 | 단계별 재실행 로직 복잡도 높음, API 존재만 확인 |
| 자동 모드 실시간 SSE/폴링 UI | ⚠️ 부분 | `pipeline_stage` DB 저장은 구현됨, 실시간 UI 미구현 |
| 도메인팩 (산업/패션/시각/광고) | ❌ 미구현 | User_Needs §9 전체 미반영, 별도 SPEC 필요 |
| TrendDocument 크롤링 자동화 | ❌ 미구현 | TrendSource 등록 후 실제 크롤링 파이프라인 미구현 |
| 레퍼런스 스케치기반/문서 검색 | ⚠️ 부분 | 키워드+이미지만 구현, 스케치기반/문서/내부자산 검색 미구현 |
| 스펙 문서 버전 되돌리기 UI | ❌ 미구현 | API(`/api/specs/{id}/version`)는 존재, UI 연결 없음 |
| `is_hypothesis` 컨셉 결정 차단 | ⚠️ 부분 | 저장은 됨, 차단 로직 미구현 |

---

Version: 1.1.0
Source: User_Needs_v01.md
Research: research.md (2026-05-09)
