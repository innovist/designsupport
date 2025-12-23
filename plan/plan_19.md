# Plan 19: SearXNG 설정/키워드·크롤링 로그·진행률 재검토 및 수정

**작성일**: 2025-12-23 02:49  
**목적**: SearXNG API URL 설정을 사용자 친화적으로 반영하고, 키워드 생성·크롤링 로그·진행률·오류 메시지가 패션 트렌드 목적에 맞게 정확히 동작하도록 파이프라인을 재정비한다.

---

## 0. 전제/제약
- Git 저장소 부재로 브랜치/PR 단계 수행 불가.
- 파일 ≤ 300 LOC, 함수 ≤ 50 LOC, 매개변수 ≤ 5, 순환 복잡도 ≤ 10 준수.
- 변경 전 관련 파일 전체 읽기(부분 읽기 금지).
- 분리 작업은 복잡도를 높이지 않도록 최소화.

## 1. 핵심 구성 요소 및 기대 기능
- SearXNG 설정: 설정 UI/저장/로드 경로에 SearXNG API URL 포함.
- 크롤링 파이프라인: 키워드가 패션 트렌드 목적에 맞게 생성되고, 크롤러 결과/오류가 로그에 표시됨.
- 진행률: 하드코딩 의존도를 낮추고 실제 수집량(예상/누적)을 반영.
- 개요 탭: 키워드/크롤링 로그/오류 메시지 정확 표시.

## 2. 기술 문서 리서치/검색
- SearxngCrawler 설정 경로: `crawlers/searxng_crawler.py`, `app/core/config.py`.
- 설정 저장/로드/UI: `app/core/settings_storage.py`, `app/api/settings_shared.py`, `app/api/settings_ui.py`, `templates/pages/settings.html`.
- 파이프라인/로그: `app/services/pipeline_orchestrator.py`, `app/services/pipeline_crawl_utils.py`, `app/api/session_store.py`.

## 3. 엣지 케이스
- SearXNG 선택했으나 API URL 미설정.
- 크롤러 미선택(빈 배열) 또는 일부 크롤러만 선택.
- 키워드가 비패션으로 생성되거나 너무 짧음.
- 수집 결과 0건(크롤러 오류/검색 실패/필터 과도).

## 4. 데이터 흐름/영향도 분석
- Settings UI → settings_storage → config.searxng_api_url → SearxngCrawler.base_url.
- 세션 모달 → crawler_config → pipeline_orchestrator._collect_data → crawler_service.crawl_all.
- progress_cb → session logs → 개요 탭 terminal 로그 출력.

## 5. 구현 단계(백엔드/프론트 동시)
1) SearXNG API URL 설정 저장/로드/UI 추가 및 i18n 키 보강.
2) SearXNG 미설정 시 선택 제한/경고 처리(UX 고려).
3) 키워드 추출 프롬프트 강화(패션/의류/시즌/타깃/연도 명시) 및 결과 저장 보장.
4) 크롤링 로그 개선(선택 크롤러/키워드/수집 건수/에러 요약)과 진행률 계산 정밀화.
5) 세션 로그/메타데이터가 개요 탭에 정확히 반영되는지 확인.

## 6. 테스트 계획
- 정적 검증 3회 + 전체 정적 검증 5회 실행.
- 실제 크롤링 최소 1회: YouTube/NateNews 소량 설정으로 수집 로그 확인.
- SearXNG 미설정 상태에서 선택 시 오류 메시지 확인.

## 7. 완료 기준
- 설정 페이지에서 SearXNG API URL 저장/로드 가능.
- 세션 개요에 키워드/크롤링 로그/오류 메시지 명확 표시.
- 진행률이 수집량 변화에 따라 합리적으로 업데이트.
- 크롤러 설정(모달) 값이 실제 수집 제한에 반영됨.

## 8. 대안 비교(결정 기록)
1) SearXNG 미설정 시 선택 비활성화
   - 장점: 오류 예방, UX 명확
   - 단점: 즉시 사용 불가
   - 위험: 사용자가 설정 위치를 놓칠 수 있음
2) SearXNG 미설정 상태에서도 실행 후 실패
   - 장점: 구현 단순
   - 단점: 실패 원인 불명확
   - 위험: 사용자 혼란/불신

→ 선택: 1) 미설정 시 선택 비활성화 + 설정 안내 (오류 예방 우선)
