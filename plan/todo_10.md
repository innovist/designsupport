# Todo 10: i18n 전면 적용 + 파이프라인/라이브러리 정합성 검증

**작성일**: 2025-12-22 03:58
**기준**: plan_10.md

---

## Phase 1: i18n 키/언어 적용

- [x] i18n JSON 키 추가 (nav.library, 페이지별 키)
- [x] i18n.js 초기 lang 반영 수정
- [x] 페이지 title i18n 키 적용

---

## Phase 2: 템플릿 분리 & 전면 i18n

- [x] dashboard/library/new_session CSS/JS 분리
- [x] 모든 페이지 텍스트/알림 i18n 적용
- [x] 언어 변경 이벤트 시 동적 렌더링 반영

---

## Phase 3: 데이터 정합화

- [x] sessions 카운트 필드 정합 (keyword/design/model/blueprint)
- [x] pipeline images/blueprints 구조 통일
- [x] library/session_detail 표시 로직 수정

---

## Phase 4: 검증/테스트

- [x] i18n 키 매칭/누락 검증
- [x] 유스케이스 3개 테스트
- [x] 엣지케이스 3개 테스트
- [x] 레드팀 테스트 3개 수행
- [x] 이슈 수정 후 재검증 반복
