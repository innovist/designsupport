# SPEC-DESIGN-TOOL-001: Research Document

**작성일**: 2026-05-09  
**분석 대상**: DesignSupport 프로젝트 (`app/` 디렉토리 기반 FastAPI 구현체)  
**목적**: 현재 구현 상태와 User_Needs_v01.md 요구사항의 갭 분석

---

## 1. 현재 코드베이스 구조

### 1.1 백엔드 구조 (FastAPI)

```
app/
  main.py                         FastAPI 앱 진입점, 라우터 등록, 헬스체크
  core/
    config.py                     pydantic-settings BaseSettings, .env 기반 설정
    database.py                   SQLAlchemy 세션, get_db 의존성
    logging.py                    구조화 로거
    security.py                   최소 유틸리티 (인증 없음)
  api/
    errors.py                     표준 에러 응답 헬퍼 (settings_required, validation_error)
    pages.py                      HTML 페이지 라우터 (레거시 Jinja2)
    routes/                       10개 API 라우터 모듈
  application/
    ports/                        ai_client, search_client, storage 포트 인터페이스
    dtos/                         6개 DTO 모듈 (asset, concept, generation, reference, session, workspace)
    use_cases/                    14개 유스케이스 (abstraction, assets, concepts, conversations,
                                  generation, references, sessions, specs, trends, workspace)
  domain/
    entities/                     도메인 엔티티 (현재 대부분 미구현, 뼈대만 존재)
    services/                     도메인 서비스 (미구현)
  infrastructure/
    ai_clients/                   anthropic, gemini, openai 클라이언트 + factory
    repositories/                 project, session, trend, workspace 리포지토리
    search/                       web_search (SearXNG 기반), image_search
    storage/                      파일 저장소 (로컬)
    parsers/                      문서 파서 (뼈대)
  models/                         11개 SQLAlchemy ORM 모델 모듈
  utils/                          encryption, searxng_runner, system_detector
```

### 1.2 프론트엔드 구조

```
templates/
  base.html                       레거시 공통 레이아웃
  pages/
    session_detail.html           세션 워크스페이스 (9탭: brief/chat/sketch/trend/concepts/references/abstraction/generation/spec)
    settings.html                 워크스페이스 설정
    new_session.html              세션 생성
    project_detail.html           프로젝트 상세
    projects.html                 프로젝트 목록
    home.html                     홈
    chatbot.html                  챗봇
    library.html                  라이브러리

static/js/pages/
  session_detail.js               세션 워크스페이스 코어 (상태, 탭, 브리프, 챗)
  session_detail_actions.js       세션 워크스페이스 액션 (스케치, 트렌드, 컨셉, 레퍼런스, 추상화, 생성, 스펙)
  settings.js                     워크스페이스 설정 JS
  dashboard.js + dashboard/       대시보드 모듈
```

### 1.3 DB 마이그레이션

```
alembic/versions/482a29aee870_initial_schema.py   초기 스키마 전체 (단일 마이그레이션)
```

---

## 2. 구현된 ORM 모델 목록

| 모델 파일 | 테이블 | 비고 |
|---|---|---|
| workspace.py | workspace, workspace_setting, feature_model_setting, workspace_trend_setting | |
| project.py | design_project | |
| session.py | design_session, design_brief, design_evaluation | |
| assets.py | user_sketch_asset, sketch_analysis | |
| concepts.py | concept_candidate, concept_decision | |
| references.py | reference_asset, reference_analysis | |
| abstraction.py | abstraction_rule | title 필드 추가됨 (User_Needs에 없음) |
| generation.py | generated_design | |
| specs.py | spec_document | |
| trends.py | trend_source, trend_document, trend_insight | |
| base.py | Base, TimestampMixin | created_at/updated_at 공통 |

**총 17개 테이블** — User_Needs_v01.md 섹션 17 ERD와 일치.

### 2.1 User_Needs 대비 모델 차이점

| 항목 | User_Needs | 실제 구현 | 비고 |
|---|---|---|---|
| design_session.mode | chatbot/auto/sketch | 동일 | |
| design_session.pipeline_stage | queued~failed 상태 | 동일 | |
| sketch_analysis 관계 | 1:N | 1:1 (unique constraint) | User_Needs는 N이지만 현재 1:1 구현 |
| abstraction_rule.title | 없음 | 추가됨 | 구현 시 편의상 추가 |
| abstraction_rule.axes_count | 없음 | 추가됨 | 최소 2축 검증용 |
| design_evaluation | session_id 연결 | 동일 | |

---

## 3. 구현된 API 엔드포인트 (실측)

총 **57개 라우트** (HEAD 포함).

### 워크스페이스
| Method | Path | 구현 상태 |
|---|---|---|
| GET | /workspace | ✅ HTML 페이지 |
| GET | /workspace/settings | ✅ HTML 페이지 |
| GET | /api/workspace/settings | ✅ |
| PUT | /api/workspace/settings | ✅ |
| GET | /api/workspace/feature-models | ✅ |
| PUT | /api/workspace/feature-models/{feature_key} | ✅ |
| GET | /api/workspace/trend-settings | ✅ |
| PUT | /api/workspace/trend-settings | ✅ |
| GET | /api/workspace/api-key-aliases | ✅ SPEC에 누락 |

### 프로젝트 / 세션
| Method | Path | 구현 상태 |
|---|---|---|
| GET | /projects | ✅ HTML |
| GET | /api/projects | ✅ |
| POST | /api/projects | ✅ |
| GET | /api/projects/{project_id} | ✅ |
| POST | /api/sessions | ✅ |
| GET | /api/sessions/{session_id} | ✅ |
| GET | /sessions/{session_id} | ✅ HTML 세션 워크스페이스 |
| PATCH | /api/sessions/{session_id}/stage | ✅ |
| POST | /api/sessions/{session_id}/brief | ✅ |
| POST | /api/sessions/{session_id}/rerun | ✅ |

### 대화
| Method | Path | 구현 상태 |
|---|---|---|
| POST | /api/sessions/{session_id}/messages | ✅ |
| GET | /api/sessions/{session_id}/messages | ✅ |

### 스케치
| Method | Path | 구현 상태 |
|---|---|---|
| POST | /api/sessions/{session_id}/sketches | ✅ |
| GET | /api/sessions/{session_id}/sketches | ✅ |
| GET | /api/sketches/{sketch_id} | ✅ |
| GET | /api/sketches/{sketch_id}/analysis | ✅ |
| POST | /api/sketches/{sketch_id}/analyze | ✅ SPEC 섹션 5.4에 누락 |
| POST | /api/sketches/{sketch_id}/confirm-analysis | ✅ |

### 트렌드
| Method | Path | 구현 상태 |
|---|---|---|
| POST | /api/sessions/{session_id}/trends/search | ✅ |
| GET | /api/sessions/{session_id}/trends | ✅ SPEC 섹션 5.5에 누락 |
| GET | /api/trend-sources | ✅ |
| POST | /api/trend-sources | ✅ |

### 레퍼런스
| Method | Path | 구현 상태 |
|---|---|---|
| POST | /api/sessions/{session_id}/references/search | ✅ |
| GET | /api/sessions/{session_id}/references | ✅ |
| POST | /api/references/{reference_id}/analyze | ✅ |
| PATCH | /api/references/{reference_id}/risk | ✅ SPEC은 POST flag-risk로 오기재 |

### 컨셉
| Method | Path | 구현 상태 |
|---|---|---|
| POST | /api/sessions/{session_id}/concepts | ✅ |
| GET | /api/sessions/{session_id}/concepts | ✅ |
| POST | /api/concepts/{concept_id}/decisions | ✅ |

### 추상화
| Method | Path | 구현 상태 |
|---|---|---|
| POST | /api/sessions/{session_id}/abstractions | ✅ source_id 선택적 (배치 생성 지원) |
| GET | /api/sessions/{session_id}/abstractions | ✅ |

### 생성
| Method | Path | 구현 상태 |
|---|---|---|
| POST | /api/sessions/{session_id}/generations | ✅ |
| GET | /api/sessions/{session_id}/generations | ✅ |
| GET | /api/generations/{generation_id} | ✅ |

### 스펙 문서
| Method | Path | 구현 상태 |
|---|---|---|
| POST | /api/sessions/{session_id}/specs | ✅ |
| GET | /api/sessions/{session_id}/specs | ✅ 목록 반환 |
| GET | /api/specs/{spec_id} | ✅ |
| POST | /api/specs/{spec_id}/version | ✅ |

---

## 4. 유스케이스 구현 상태

| 유스케이스 | 파일 | AI 호출 | 구현 완성도 |
|---|---|---|---|
| generate_abstraction | abstraction/generate_abstraction.py | ✅ | ✅ 완성, 배치 지원 추가 |
| generate_abstractions_for_session | 동일 | ✅ | ✅ source_id 없을 때 세션 전체 배치 |
| analyze_sketch | assets/analyze_sketch.py | ✅ 비전 모델 | ✅ 완성 |
| upload_sketch | assets/upload_sketch.py | - | ✅ 완성 |
| generate_concepts | concepts/generate_concepts.py | ✅ | ✅ 완성 |
| send_message | conversations/send_message.py | ✅ | ✅ 완성 |
| create_generation_job | generation/create_generation_job.py | ✅ 이미지 모델 | ✅ BackgroundTasks 사용 |
| search_references | references/search_references.py | ✅ | ✅ 완성 |
| create_session | sessions/create_session.py | - | ✅ 완성 |
| get_session_detail | sessions/get_session_detail.py | - | ✅ 완성 |
| rerun_step | sessions/rerun_step.py | - | ⚠️ 뼈대만 존재 |
| structure_brief | sessions/structure_brief.py | ✅ | ✅ 완성 |
| generate_spec | specs/generate_spec.py | ✅ | ✅ 완성 |
| search_trends | trends/search_trends.py | - | ✅ SearXNG 사용 |
| get_api_key_aliases | workspace/get_workspace_settings.py | - | ✅ |
| update_feature_model | workspace/update_feature_model.py | - | ✅ |
| update_workspace_settings | workspace/update_workspace_settings.py | - | ✅ |

---

## 5. AI 클라이언트 팩토리

`app/infrastructure/ai_clients/factory.py`가 `feature_key`를 받아 DB에서 `FeatureModelSetting`을 조회하고 적절한 클라이언트를 반환하는 팩토리 패턴 구현.

### 5.1 지원 Provider

| Provider | 클라이언트 | 텍스트 | 이미지 생성 |
|---|---|---|---|
| anthropic | anthropic_client.py | ✅ | ❌ |
| openai | openai_client.py | ✅ | ✅ |
| gemini | gemini_client.py | ✅ | ✅ |

### 5.2 Feature Key 목록 (실제 구현에서 사용되는 키)

| feature_key | 유스케이스 |
|---|---|
| `abstraction` | generate_abstraction |
| `sketch_analysis` | analyze_sketch |
| `concept_generation` | generate_concepts |
| `chat` | send_message |
| `image_generation` | create_generation_job |
| `reference_analysis` | search_references (분석 시) |
| `brief_structuring` | structure_brief |
| `spec_writing` | generate_spec |
| `trend_analysis` | search_trends (인사이트 추출) |

---

## 6. 검색 인프라

### 6.1 웹 검색 (트렌드)
- `app/infrastructure/search/web_search.py`: SearXNG 클라이언트
- SearXNG URL이 .env에 없으면 `NoOpSearchClient`로 폴백 (빈 결과 반환)
- `SEARXNG_URL` 환경변수로 활성화

### 6.2 이미지 검색 (레퍼런스)
- `app/infrastructure/search/image_search.py`: 웹 이미지 검색
- `search_references.py`에서 이미지 검색 후 레퍼런스로 저장

---

## 7. 프론트엔드 현황

### 7.1 세션 워크스페이스 탭 구성

`session_detail.html` → 9탭 구조:
- `brief`: 브리프 입력 폼 (purpose, domain, target_user, constraints, use_case, result_form)
- `chat`: 챗봇 대화 (AI 근거 출처 링크 포함)
- `sketch`: 스케치 업로드 + AI 해석 + 분석 패널
- `trend`: 트렌드 검색 + 인사이트 카드 (evidence_quote, is_hypothesis 배지)
- `concepts`: 컨셉 후보 카드 (점수바, 채택/보류/폐기/탐색 버튼)
- `references`: 레퍼런스 그리드 (저작권 위험 배지, 고위험 차단 오버레이)
- `abstraction`: 추상화 규칙 카드 (6축 표시)
- `generation`: 생성 이미지 그리드 (상태 배지, 3초 폴링)
- `spec`: 스펙 문서 (섹션별 표시, 인쇄 버튼)

### 7.2 URL 일치 여부 (이번 세션 수정 완료)

| JS 호출 | 백엔드 라우트 | 상태 |
|---|---|---|
| `/api/sketches/{id}/analyze` | 동일 | ✅ 수정됨 |
| `/api/concepts` POST | 동일 | ✅ 수정됨 |
| `/api/concepts/{id}/decisions` | 동일 | ✅ 수정됨 |
| `/api/references/{id}/analyze` | 동일 | ✅ 수정됨 |
| `/api/sessions/{id}/abstractions` | 동일 | ✅ 수정됨 |
| `/api/generations/{id}` | 동일 | ✅ 수정됨 |
| `/api/sessions/{id}/specs` | 동일 | ✅ 수정됨 |
| trends response `.insights` 추출 | `{count, insights}` 형식 | ✅ 수정됨 |
| brief save POST | 동일 | ✅ 수정됨 |

---

## 8. 미구현 또는 불완전 항목

| 항목 | 상태 | 비고 |
|---|---|---|
| rerun_step 유스케이스 | ⚠️ 뼈대 | 실제 단계 재실행 로직 미구현 |
| auto 모드 상태 실시간 업데이트 | ⚠️ 부분 | pipeline_stage 저장은 됨, SSE/폴링 UI 미구현 |
| 도메인팩 (산업/패션/시각/광고) | ❌ 미구현 | User_Needs §9 내용 전체 미반영 |
| 레퍼런스 검색 유형 확장 | ⚠️ 부분 | 키워드+이미지만, 스케치기반/문서/내부자산 미구현 |
| DesignEvaluation 사용 흐름 | ⚠️ 부분 | 모델은 있지만 UI/API 연결 없음 |
| domain/entities, domain/services | ❌ 미구현 | 뼈대만 존재 (필요 시 추가 구현) |
| TrendDocument 크롤링 | ❌ 미구현 | TrendSource 등록 후 실제 크롤링 미구현 |
| `is_hypothesis` 필터링 | ⚠️ 부분 | 저장은 됨, 컨셉 결정 차단 로직 미구현 |
| 스펙 문서 버전 되돌리기 UI | ❌ 미구현 | API는 있음 (`/api/specs/{id}/version`) |

---

## 9. 환경 설정 요구사항

`.env` 필수/선택 키:

| 키 | 필수 | 용도 |
|---|---|---|
| DATABASE_URL | ✅ | PostgreSQL 연결 |
| SECRET_KEY | ✅ | 암호화 |
| OPENAI_API_KEY | 선택 | OpenAI 사용 시 |
| ANTHROPIC_API_KEY | 선택 | Anthropic 사용 시 |
| GEMINI_API_KEY | 선택 | Gemini 사용 시 |
| SEARXNG_URL | 선택 | 트렌드 검색 활성화 |
| UPLOAD_DIR | 선택 | 기본값 ./uploads |

---

## 10. 갭 요약 (SPEC 보완 필요 항목)

1. **API 목록**: 누락된 8개 엔드포인트 추가, `flag-risk` → `PATCH /risk` 수정
2. **feature_key 목록**: 9개 feature key 명시 필요
3. **자동 모드 9가지 상태**: SPEC에 명시 필요
4. **sketch_analysis 1:1 관계**: User_Needs의 1:N과 다름, 의도적 결정 명시 필요
5. **배치 추상화**: source_id 선택적 처리 설계 결정 명시
6. **미구현 항목**: rerun, 도메인팩, TrendDocument 크롤링 — SPEC 수락 기준에서 제외 또는 다음 SPEC으로 이월

---

Version: 1.0.0  
Source: 코드베이스 직접 분석 (2026-05-09)
