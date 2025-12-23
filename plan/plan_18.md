# Plan 18: SEARXNG_API_URL 설명 정리 및 세션 모달 STT 토글 추가

**작성일**: 2025-12-23 02:24  
**목적**: SEARXNG_API_URL의 의미/설정 위치를 명확히 설명하고, 세션 생성 모달에 STT 토글을 추가하여 유튜브 STT 사용 여부가 crawler_config에 반영되도록 한다.

---

## 0. 전제/제약
- Git 저장소 부재로 브랜치/PR 단계 수행 불가.
- 파일 ≤ 300 LOC, 함수 ≤ 50 LOC, 매개변수 ≤ 5, 순환 복잡도 ≤ 10 준수.
- 변경 전 관련 파일 전체 읽기(부분 읽기 금지).
- 분리 작업은 복잡도를 높이지 않도록 최소화.

## 1. 핵심 구성 요소 및 기대 기능
- SEARXNG_API_URL: SearXNG 검색 API 베이스 URL로 크롤러 호출에 사용됨.
- STT 토글: 세션 모달에서 STT 사용 여부를 명시적으로 선택.
- 데이터 흐름: UI → crawler_config.youtube_enable_stt → YouTubeAdapter.apply_config → YoutubeCrawler STT 활성화.

## 2. 기술 문서 리서치/검색
- 코드 내 SearxngCrawler 설정 확인: `crawlers/searxng_crawler.py`, `app/core/config.py`.
- STT 설정 전달 경로 확인: `templates/partials/dashboard/session-modal.html`, `static/js/pages/dashboard/sessions.js`, `crawlers/youtube_adapter.py`.

## 3. 엣지 케이스
- STT 토글 미선택 시 기본값 처리.
- 유튜브 크롤러 미선택 상태에서 STT 토글 존재.
- STT 기능 비활성(환경/의존성 부족) 시 경고만 표시.

## 4. 데이터 흐름/영향도 분석
- 세션 모달 입력 → sessions.js createSession payload → API 스키마 CrawlerConfig → pipeline_orchestrator → apply_crawler_config.
- i18n 키 추가가 모든 언어 파일에 반영되는지 확인.

## 5. 구현 단계(백엔드/프론트 동시)
1) 세션 모달에 STT 토글 UI 추가.
2) createSession에서 youtube_enable_stt 값 전달.
3) i18n 4개 언어 키 추가.
4) 정적 검증 3회 + 전체 정적 검증 5회 실행.

## 6. 테스트 계획
- 정적 검증 3회 + 전체 정적 검증 5회 로그 확보.
- 세션 생성 payload에 youtube_enable_stt 포함 여부 확인(프론트 로직 검증).

## 7. 완료 기준
- 세션 모달에서 STT 사용 여부를 선택 가능.
- 생성된 세션의 crawler_config에 youtube_enable_stt가 저장됨.
- i18n 키 누락 없음.

## 8. 대안 비교(결정 기록)
1) 체크박스(ON/OFF) 방식
   - 장점: UX 단순, 빠른 선택
   - 단점: 환경 기본값 자동 연동 불가
   - 위험: 기본값 오해 가능
2) 3단 선택(자동/사용/미사용)
   - 장점: 환경 기본값 유지 가능
   - 단점: UI 복잡도 증가
   - 위험: 사용자 혼동

→ 선택: 1) 체크박스(ON/OFF) 방식 (최소 수정, UX 단순)
