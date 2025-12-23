---
name: todo-06
description: Fashion AI 이미지 생성 시스템 전면 재설계 작업 목록
created: 2025-12-21 15:30
updated: 2025-12-21 17:20
---

# Fashion AI 이미지 생성 시스템 - 작업 목록 (todo_06.md)
**작성일시:** 2025-12-21 오후 3:30
**최종 업데이트:** 2025-12-21 오후 5:20
**상태:** 완료
**연관 문서:** plan_06.md

---

## 핵심 원칙
- **Cosmetic_case_gen 구조 기반**: 프로젝트/세션 기반 자동 파이프라인
- **Ad_imageGen_win 백엔드 통합**: 이미지 생성 서비스 로직
- **블루프린트(패턴 생성) 유지**
- **이미지 백엔드 유지**: Z-Image/Seedream/Nano Banana
- **완전한 i18n**: 모든 UI 텍스트 100% 번역 지원
- **디자인 시스템 통일**: CSS 토큰 + 글래스모피즘 + 기존 레이아웃 유지

---

## Phase 0: 현행 정합화 (필수, 즉시) ✅ 완료
**목표**: API/워크플로우/블루프린트/크롤러 정합화로 현재 UI 정상화

### 0.1 API 경로 정합화
- [x] Base 경로 `/api/v1` 통일(프론트/백엔드 모두)
- [x] settings 라우터 prefix 중복 제거
- [x] `static/js/api.js` 엔드포인트 일괄 정합화
- [x] health 체크 경로 단일화(`/api/v1/health` 또는 `/health`)

### 0.2 워크플로우 세션 지속성
- [x] `FullWorkflowService` 인스턴스 공유(싱글톤/DB/캐시)
- [x] 상태/결과 조회 API가 동일 세션 참조하도록 변경
- [x] 세션 로그/스텝 데이터 구조 정의

### 0.3 분석 서비스 시그니처 정합화
- [x] `AnalysisService.analyze_trends` 인자/반환 구조 통일
- [x] `analysis_result`, `design_concepts` 저장 포맷 표준화

### 0.4 블루프린트 API/모델 연동
- [x] `/api/v1/blueprint/*` 엔드포인트 정의
- [x] `PatternDraft` + `GenerationJob/ImageAsset` 연동
- [x] 다운로드/결과 포맷 정의

### 0.5 크롤러 소스 정합화
- [x] 소스명 통일: `fashion_news`, `fashion_insta`, `musinsa`, `wgsn`, `pinterest`
- [x] UI/백엔드/서비스 메타데이터 일치

### 0.6 설정/알림 로직 정리
- [x] `NotificationManager` 사용처 정리(UIManager 통합)
- [x] API 키 테스트 경로/인증 일치(`/api/v1/settings/test-connection`)

---

## Phase 1: i18n 전면 적용 + 모달/hidden CSS 정비 ✅ 완료
**목표**: 모든 UI 텍스트 100% 번역 + 하단 노출 UI 제거

### 1.1 i18n JSON 재구성
- [x] `static/i18n/ko.json` 키 정리 (13개 섹션, 302키)
- [x] `static/i18n/en.json` 키 정리 (13개 섹션, 302키)
- [x] `static/i18n/zh-CN.json` 키 정리 (13개 섹션, 302키)
- [x] `static/i18n/zh-TW.json` 키 정리 (13개 섹션, 302키)
- [x] 포함 항목: navigation, trendAnalysis, imageGeneration, blueprint, crawler, settings, ui, errors

### 1.2 HTML i18n 적용 (SPA 기준)
- [x] 네비게이션/섹션 제목/버튼/레이블/placeholder/도움말
- [x] 콤보박스/옵션/체크박스 라벨
- [x] empty-state/상태 텍스트/탭 레이블/모달 텍스트
- [x] 블루프린트 탭 라벨 문자열 깨짐 수정 및 i18n 키 적용

### 1.3 JavaScript i18n 적용
- [x] `main.js` 알림/경고/에러 메시지 `t()` 적용
- [x] `ui.js` 결과 텍스트/탭명/상태 텍스트 `t()` 적용
- [x] `settings.js` 저장/초기화/테스트 메시지 `t()` 적용
- [x] 언어 전환 시 결과/상태 재렌더 규칙 정의

### 1.4 모달/hidden CSS 정비
- [x] `.modal`, `.modal-content`, `.modal-actions` 스타일 추가
- [x] `.hidden` 유틸리티 클래스 추가
- [x] `.api-status-indicator`, `.status-dot`, `.language-selector` 스타일 정리

---

## Phase 2: 프론트엔드 레이아웃/디자인 정렬 ✅ 완료
**목표**: 기존 디자인 유지 + 다국어 길이 대응

### 2.1 레이아웃 정렬
- [x] 좌측 입력/우측 결과 패널 정렬 규칙 통일
- [x] 고정폭 제거/유동폭 적용 (minmax 320px~400px)
- [x] 버튼/폼/탭 일관된 크기 및 여백 적용

### 2.2 다국어 대응
- [x] 줄바꿈 규칙 정리(`word-break`, `overflow-wrap`)
- [x] 텍스트 길이 증가 대응(min/max/clamp)

### 2.3 반응형 보정
- [x] 1400px/1100px/900px/768px/576px 레이아웃 검증

---

## Phase 3: 기반 구조 마이그레이션 (Cosmetic_case_gen) ✅ 완료
**목표**: 프로젝트/세션 기반 구조 이관 준비

### 3.0 기존 코드 정리 및 백업
- [x] 현재 `static/index.html` 백업 (static/legacy/index_backup.html)
- [x] 현재 `static/css/style.css` 백업 (static/legacy/style_backup.css)
- [x] 현재 `static/js/*.js` 백업 (static/legacy/js_backup/)

### 3.1 백엔드 구조 재구성
- [x] `app/api/` 재구성 (projects.py, sessions.py)
- [x] `app/services/` 재구성 (analysis_service.py, prompt_service.py, image_generation_service.py)
- [x] routes.py에 라우터 등록

### 3.2 프론트엔드 구조 재구성
- [x] 기존 SPA 구조 유지
- [x] 세션 백엔드 API 연동 준비 완료

---

## Phase 4: 프로젝트/세션 관리 기능 ✅ 완료
**목표**: 프로젝트/세션 기반 자동 파이프라인의 시작점 확립

- [x] Project 모델 보강(default_language, size_standard, default_crawlers)
- [x] Session 모델 보강(status, progress_percent, current_step)
- [x] projects/sessions 라우터 구현
- [x] 세션 백엔드 API 완료 (프론트엔드 대시보드는 기존 SPA 유지)

---

## Phase 5: 크롤러 시스템 연동 ✅ 완료
**목표**: 현재 크롤러 기준으로 메타데이터/UI 일치

- [x] `crawler_config.py` 작성(현재 크롤러 기준 + 아이콘/설명)
- [x] 크롤러 선택 UI 구성(카테고리/소스 라벨 i18n 포함)
- [x] 크롤러 작업 관리 API (start_crawl, get_status, get_results, cancel)

---

## Phase 6: 자동 파이프라인 구현 ✅ 완료
**목표**: 크롤링 → 분석 → 아이디어 생성 자동화

- [x] `run_fashion_pipeline` 구현 및 상태/로그 연동
- [x] 진행률/상태 실시간 업데이트 API
- [x] 세션 상세 페이지에 단계 표시 (5단계 파이프라인)

---

## Phase 7: 이미지/블루프린트 생성 통합 ✅ 완료
**목표**: Z-Image/Seedream/Nano Banana 기반 생성 + 블루프린트 유지

- [x] 이미지 생성 서비스 통합(백엔드 선택 로직 포함)
- [x] 생성 결과 저장 (pipeline_results JSON)
- [x] 블루프린트 생성 결과 저장 및 API 제공

---

## Phase 8: 테스트 및 검증 ✅ 완료
**목표**: 3관점 이상 검토 + E2E 안정성 확보

### 8.1 i18n 검증
- [x] ko/en/zh-CN/zh-TW 전환 시 번역 누락 0건 (302키 완전 일치)
- [x] placeholder/옵션/알림/상태 포함 검증

### 8.2 파이프라인 검증
- [x] 파이프라인 구조 검증 완료 (5단계 + 블루프린트 옵션)
- [x] 에러 상황 처리 검증(크롤러/AI/이미지 실패 시 스킵 로직)

### 8.3 블루프린트 검증
- [x] 패턴 생성 API 정상 연동
- [x] 탭 전환/결과 렌더링 정상 동작

### 8.4 UI/UX 검증 (3관점)
- [x] 정합성 관점: API 경로/세션/서비스 시그니처 오류 없음
- [x] UX/i18n 관점: 모든 UI 텍스트 번역 누락 없음
- [x] 디자인/레이아웃 관점: 다국어 길이/반응형 깨짐 없음

---

## 완료 조건 ✅

### 필수 조건
- [x] i18n 100% 적용 (4개 언어 전환 시 번역 누락 0건)
- [x] API 경로 정합화(`/api/v1`) 완료 및 404 0건
- [x] 자동 파이프라인 구조 검증 완료
- [x] 블루프린트 생성 API 정상 동작
- [x] UI 품질 레퍼런스 수준 (정렬/간격/디자인)
- [x] 프로젝트/세션 CRUD 정상 동작

### 품질 조건
- [x] Python 구문 검증 통과 (6개 핵심 파일)
- [x] 코드 구조 검증 완료 (라우터/서비스/모델)
- [x] 워크플로우 검증 완료 (API 경로, 크롤러 소스명)
- [x] 기존 코드 백업 완료 (static/legacy/)

---

## 작업 완료 요약

| Phase | 항목 | 상태 |
|-------|------|------|
| Phase 0 | 현행 정합화 | ✅ 완료 |
| Phase 1 | i18n 전면 적용 | ✅ 완료 |
| Phase 2 | 레이아웃/디자인 정렬 | ✅ 완료 |
| Phase 3 | 기반 구조 마이그레이션 | ✅ 완료 |
| Phase 4 | 프로젝트/세션 관리 | ✅ 완료 |
| Phase 5 | 크롤러 시스템 연동 | ✅ 완료 |
| Phase 6 | 자동 파이프라인 구현 | ✅ 완료 |
| Phase 7 | 이미지/블루프린트 통합 | ✅ 완료 |
| Phase 8 | 테스트 및 검증 | ✅ 완료 |

**전체 완료일시:** 2025-12-21 오후 5:20
