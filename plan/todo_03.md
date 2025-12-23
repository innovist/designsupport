# 상세 작업 목록 (todo_03.md)
**작성일시:** 2025-12-20
**상태:** 진행 대기 (Pending)
**연관 문서:** plan_03.md

---

## 0. 환경 설정 및 공통 모듈 (Environment & Core)
- [ ] **Project Setup:**
    - [ ] Python 3.10+ 가상환경 구성 및 `requirements.txt` 확정.
    - [ ] `.env` 파일 템플릿 생성 (Gemini, GLM, Z-Image, Seedream, Nano API Keys).
    - [ ] 로깅(Logging) 설정: 파일/콘솔 동시 출력, 일자별 로테이션.
- [ ] **Database Design:**
    - [ ] SQLite/PostgreSQL 스키마 설계 (ORM: SQLAlchemy/Tortoise).
    - [ ] `Projects`, `CrawlResults`, `AnalysisReports`, `DesignConcepts`, `Images` 테이블 정의.
- [ ] **Utility Modules:**
    - [ ] `KeyManager`: API 키 로테이션 및 사용량 추적 클래스 구현.
    - [ ] `AsyncClient`: 비동기 HTTP 요청 래퍼 (Retry, Timeout 처리).

## 1. 데이터 수집 모듈 (Collector Engine)
- [ ] **Base Crawler:**
    - [ ] `AbstractCrawler` 클래스 정의 (공통 인터페이스).
    - [ ] `robots.txt` 파서 및 준수 로직 구현.
- [ ] **Target Crawlers:**
    - [ ] 패션 뉴스 사이트 크롤러 구현.
    - [ ] SNS/이미지 보드(Pinterest style) 메타데이터 수집기 구현.
- [ ] **Data Pipeline:**
    - [ ] 수집 데이터 정제 (HTML 태그 제거, 불용어 처리).
    - [ ] 중복 제거 로직 (URL 해시 및 내용 유사도 비교).

## 2. 인텔리전스 모듈 (Analysis Engine)
- [ ] **Prompt Engineering (Analysis):**
    - [ ] `Gemini-2.5-flash`용 트렌드 추출 및 심층 분석 프롬프트 작성.
    - [ ] `Gemini-3-flash`용 트렌드 추출 및 심층 분석 프롬프트 작성.
    - [ ] `GLM-4.7`용 트렌드 추출 및 심층 분석 프롬프트 작성.
    - [ ] `GLM-4.7`용 종합/조율(Synthesizer) 프롬프트 작성 (JSON 출력 강제).
- [ ] **Analysis Service:**
    - [ ] 3개 모델 병렬/직렬 호출 오케스트레이터 구현.
    - [ ] 분석 결과 파싱 및 `TrendReport` 객체 매핑.
    - [ ] 근거(Source URL) 매핑 로직 구현.

## 3. 크리에이티브 모듈 (Generation Engine)
- [ ] **Prompt Optimizer:**
    - [ ] `Concept` -> `Image Prompt` 변환기 구현 (한글 입력 -> 영문 번역 -> 스타일 태그 추가).
    - [ ] 모델별(Z-Image, Seedream, Nano) 전용 프롬프트 템플릿 구축.
- [ ] **Image Gen Service:**
    - [ ] **Step 1:** 의상 상세(Flat/Mannequin) 생성 API 연동.
    - [ ] **Step 2:** 일관성 유지(I2I/Reference)를 적용한 모델 착장 생성 로직 구현.
    - [ ] **Step 3:** 도면(Blueprint) 스타일 생성 로직 및 표준 치수 데이터 주입.
- [ ] **Verification:**
    - [ ] 생성된 이미지의 품질/내용 일치 여부 검증 (Gemini Vision 활용).

## 4. UI/UX 및 통합 (Application Layer)
- [ ] **Backend API (FastAPI):**
    - [ ] `/api/projects`: 프로젝트 생성/조회.
    - [ ] `/api/crawl`: 크롤링 시작/상태확인.
    - [ ] `/api/analyze`: 트렌드 분석 요청.
    - [ ] `/api/generate`: 이미지 생성/재생성 요청 (모델 선택 옵션 포함).
- [ ] **Frontend (Web):**
    - [ ] 대시보드 레이아웃 (좌측: 입력/설정, 중앙: 보고서/이미지, 우측: 이력).
    - [ ] **Interactive Viewer:** 생성된 의상, 모델, 도면을 탭으로 전환하며 보기.
    - [ ] 다운로드 기능 (보고서 PDF + 고해상도 이미지).

## 5. 테스트 및 검증 (QA)
- [ ] **Consistency Test:** 생성된 의상과 모델 착장 의상의 디자인 일치율 육안/시스템 검사.
- [ ] **Workflow Test:** 입력부터 결과물 다운로드까지 끊김 없는지 테스트.
- [ ] **Error Handling:** API 호출 실패, 크롤링 차단 시 우회/알림 로직 점검.

---
**Note:** 코드를 작성하기 전, 본 계획서(todo_03.md)의 모든 항목이 명확한지 다시 한번 확인하고 작업을 시작하시오.