# Todo 19: SearXNG 설정/키워드·크롤링 로그·진행률 재검토 및 수정

**작성일**: 2025-12-23 02:49  
**관련 계획**: plan_19.md

---

## Phase 0: 사전 확인
- [x] CLAUDE.md 1~150줄 및 worksheet 최신 200줄 확인
- [x] 기존 plan/todo 검토(plan_18/todo_18)
- [x] Git 저장소 여부 확인 및 제약 기록

## Phase 1: 코드/문서 전체 읽기
- [x] SearXNG/설정 경로 파일 전체 읽기
- [x] 파이프라인/크롤링 유틸 전체 읽기
- [x] 대시보드(세션/개요/크롤러) JS 및 CSS 전체 읽기

## Phase 2: 원인 분석/설계
- [x] 로그/키워드/진행률/설정 충돌 원인 정리
- [x] SearXNG 설정 UX/에러 메시지 설계

## Phase 3: 구현
- [x] settings_storage/settings_shared/settings_ui/settings.html 업데이트
- [x] i18n 4개 언어 키 추가
- [x] 파이프라인 키워드 프롬프트/로그/진행률 개선
- [x] 대시보드에서 SearXNG 설정 상태 반영

## Phase 4: 검증/테스트
- [x] 정적 검증 1차 실행
- [x] 정적 검증 2차 실행
- [x] 정적 검증 3차 실행
- [x] 전체 정적 검증 1차 실행
- [x] 전체 정적 검증 2차 실행
- [x] 전체 정적 검증 3차 실행
- [x] 전체 정적 검증 4차 실행
- [x] 전체 정적 검증 5차 실행
- [x] 실제 크롤링 테스트 1회 (YouTube/NateNews 소량)
- [x] SearXNG 미설정 선택 오류 확인

## Phase 5: 기록/정리
- [x] worksheet.md 작업 기록
- [x] todo_19 체크리스트 갱신
- [x] 결과 요약 및 후속 작업 정리

## N/A (제약)
- [ ] 새 브랜치 생성 및 Draft PR (Git 저장소 부재)
