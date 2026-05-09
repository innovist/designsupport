# SPEC-02: 파이프라인 자동 오케스트레이터

**작성일**: 2026-05-09  
**상태**: APPROVED  
**우선순위**: Critical

---

## 1. 목적

사용자가 "자동 진행" 모드를 선택하면, 시스템이 브리프 → 트렌드 → 컨셉 → 레퍼런스 → 추상화 → 스펙 순으로 전체 파이프라인을 자동으로 실행한다.  
각 단계의 진행 상황은 `auto_progress_log`에 기록되고, `pipeline_stage`는 실시간으로 업데이트된다.  
사용자는 진행 중에 현재 단계와 수집 근거를 실시간으로 확인할 수 있다.

---

## 2. 배경

기존에 `DesignSession.pipeline_stage`와 `auto_progress_log` 필드가 모델에 정의되어 있으나,  
이를 자동으로 전진시키는 워크플로 엔진이 없었다.  
각 단계별 use case(search_trends, generate_concepts, search_references, generate_abstraction, generate_spec)도 구현되어 있으므로,  
이를 연결하는 오케스트레이터만 추가하면 된다.

---

## 3. 요구사항 (EARS 형식)

### REQ-PO-001: 자동 모드 트리거
WHEN 사용자가 `/api/sessions/{id}/auto` POST 요청을 보내면,  
THE SYSTEM SHALL 세션 mode를 `auto`로 업데이트하고, BackgroundTask로 파이프라인 오케스트레이터를 실행한다.

### REQ-PO-002: 단계 순서
THE SYSTEM SHALL 다음 순서로 파이프라인 단계를 실행한다:
`brief_input → researching → concepting → referencing → abstracting → documenting → review_ready`

### REQ-PO-003: 진행 로그
AT EACH STAGE, THE SYSTEM SHALL `auto_progress_log`에 `{stage, started_at, completed_at, result_count, note}` 항목을 추가한다.

### REQ-PO-004: 단계별 pipeline_stage 업데이트
WHEN 각 단계가 시작되면, THE SYSTEM SHALL `DesignSession.pipeline_stage`를 해당 단계로 업데이트한다.

### REQ-PO-005: 실패 처리
WHEN 어떤 단계에서 예외가 발생하면,  
THE SYSTEM SHALL `pipeline_stage`를 `failed`로 설정하고, `auto_progress_log`에 오류 항목을 추가한다.  
THE SYSTEM SHALL NOT 임의 폴백값이나 가짜 데이터를 반환한다.

### REQ-PO-006: 진행 상황 조회
WHEN 클라이언트가 `/api/sessions/{id}/progress` GET 요청을 보내면,  
THE SYSTEM SHALL `pipeline_stage`, `auto_progress_log`, `status`를 반환한다.

### REQ-PO-007: 브리프 완성 전제
THE SYSTEM SHALL 브리프(`is_complete=True`)가 없으면 자동 모드를 거부하고 422를 반환한다.

### REQ-PO-008: 근거 메시지 생성
AT EACH STAGE, THE SYSTEM SHALL 수행 결과를 요약한 ChatMessage를 생성하고,  
해당 메시지의 `evidence_links`에 수집된 출처 URL 목록을 저장한다.

---

## 4. 기술 설계

### 4.1 신규 파일

- `app/application/services/pipeline_orchestrator.py`  
  - `DesignPipelineOrchestrator` 클래스
  - `async run(session_id, db_factory)` 메서드 — 전체 파이프라인 실행
  - 각 단계별 private async 메서드

### 4.2 변경 파일

- `app/infrastructure/repositories/session_repository.py`  
  - `append_progress_log(session_id, entry)` 추가
  - `set_stage_with_log(session_id, stage, entry)` 추가

- `app/api/routes/sessions.py`  
  - `POST /sessions/{id}/auto` 엔드포인트 추가
  - `GET /sessions/{id}/progress` 엔드포인트 추가

- `static/js/pages/session_detail.js`  
  - 자동 진행 버튼 및 상태 표시 추가
  - 진행 중 폴링 로직 추가 (3초 간격)
  - 단계별 진행바 표시

---

## 5. 인수 조건

- [ ] `POST /api/sessions/{id}/auto` 호출 시 202 반환
- [ ] 브리프 미완성이면 422 반환
- [ ] 각 단계 전환 시 `pipeline_stage` 즉시 업데이트
- [ ] `auto_progress_log`에 모든 단계 기록 (started_at, completed_at, result_count)
- [ ] 단계 실패 시 `pipeline_stage = "failed"`, 오류 정보 기록
- [ ] `GET /api/sessions/{id}/progress` 실시간 진행 상황 반환
- [ ] 각 단계 완료 ChatMessage에 evidence_links 포함
- [ ] 이미지 생성 단계는 별도 트리거(수동)로 유지 — 자동모드는 스펙 생성까지만
