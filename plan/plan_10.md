# Plan 10: 전 페이지 i18n 완전 적용 + 파이프라인/라이브러리 정합성 검증

**작성일**: 2025-12-22 03:58
**목표**: 모든 페이지 언어 변경 완전 적용, 파이프라인 결과 구조/카운트 정합화, 실사용 검증 강화

---

## 1. 문제점 정리

### 1.1 i18n 적용 누락
- base + library 일부만 data-i18n 적용
- 다른 페이지는 한국어 하드코딩/알림 메시지 고정
- i18n JSON에 nav.library, library.* 등 키 누락
- HTML lang 초기값 고정(ko) → 언어 변경 반영 누락

### 1.2 데이터 구조 불일치
- Dashboard UI: keyword/design/model 카운트 사용 → API 응답에 필드 없음
- Session Detail: generated_images/blueprints 구조 불일치로 표시 실패
- Library: project.name 사용(실제는 title), 이미지 URL/BASE64 처리 미정합

### 1.3 파일 규모/모듈화
- dashboard/library/new_session 템플릿 300+ LOC 초과
- CSS/JS 분리 필요 (규칙 준수 및 유지보수성)

---

## 2. 목표 아키텍처 (정합/표준화)

### 2.1 i18n 구조
- nav/library/settings 포함 모든 페이지 data-i18n 적용
- data-i18n-placeholder, data-i18n-options 사용
- 언어 변경 이벤트 시 동적 렌더링 재반영

### 2.2 파이프라인 결과 표준
- generated_images: flat list (type=design/model, base64 + data URL)
- blueprints: flat list (type=sketch/layout/pattern, base64 + data URL)
- counts: keyword/design/model/blueprint/crawled 일관화

---

## 3. 구현 Phase

### Phase 1: i18n 키/언어 적용
- i18n JSON: nav.library + 각 페이지 키 추가
- i18n.js 초기 lang 반영
- 페이지 title 키 적용

### Phase 2: 템플릿 분리 & 전면 i18n
- dashboard/library/new_session CSS/JS 분리
- 모든 페이지 텍스트/알림 i18n 적용
- 언어 변경 시 UI 재렌더링

### Phase 3: 데이터 정합화
- sessions: keyword/design/model/blueprint 카운트 제공
- pipeline: images/blueprints 결과 구조 통일
- library/session_detail 표시 로직 수정

### Phase 4: 검증/테스트
- i18n 키 매칭/누락 검증
- 유스케이스/엣지/레드팀 테스트 3세트 수행
- 이슈 발생 시 반복 수정/재검증

---

## 4. 완료 기준

- 모든 페이지 언어 변경 즉시 반영
- dashboard/session_detail/library 결과 표시 정상화
- 파이프라인 결과 구조 통일 및 카운트 정확
- 3종 테스트 세트(유스케이스/엣지/레드팀) 완료

---

## 5. 검토 기록

### 1차 검토 (정합성)
- i18n 누락 페이지/키 전수 점검 ✓
- pipeline 결과 ↔ UI 기대 구조 불일치 확인 ✓

### 2차 검토 (안전성)
- 동적 렌더링 시 언어 변경 반영 방식 점검 ✓
- library/blueprint 구조 변환 시 데이터 손실 위험 점검 ✓

### 3차 검토 (규칙 준수)
- 템플릿 LOC 제한 준수 방안 확인 ✓
- 최소 수정/핵심 집중 원칙 확인 ✓
