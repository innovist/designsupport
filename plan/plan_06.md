---
name: plan-06
description: Cosmetic_case_gen 구조 기반 전면 재설계 - 자동 파이프라인 + 이미지 생성 통합
created: 2025-12-21 15:30
updated: 2025-12-21 15:30
---

# Fashion AI 이미지 생성 시스템 - 전면 재설계 계획서

## 1. 개요

### 1.1 현재 문제점 분석
1. **API 라우팅 불일치**: 프론트 `/api/v1/*` 호출 vs 서버 `/api/*`, settings 라우터 prefix 중복 → 404
2. **워크플로우 세션 지속성 부재**: 요청마다 신규 인스턴스 생성 → 상태/결과 조회 실패
3. **분석 서비스 시그니처 불일치**: `analyze_trends` 인자/반환 구조 불일치로 파이프라인 실패
4. **블루프린트 API 공백**: UI는 호출하지만 백엔드 엔드포인트/모델 연동 없음
5. **크롤러 소스 불일치**: UI/백엔드/크롤러 서비스 소스명이 달라 요청 실패/무시
6. **i18n 불완전**: 텍스트/버튼/옵션/placeholder/알림/상태/로딩/모달 하드코딩
7. **모달/hidden CSS 누락**: 하단에 버튼/레이어 노출
8. **프론트 UX 정렬 문제**: 고정폭/간격/텍스트 길이 대응 부재, 다국어 길이 변화 미반영
9. **설정/알림 로직 결손**: `NotificationManager` 미정의, API 키 테스트 경로/인증 불일치

### 1.2 해결 방향
- **현행 코드 정합화 우선**: API 경로/워크플로우/블루프린트/크롤러부터 정상화
- **Cosmetic_case_gen 구조 채택**: 프로젝트/세션 기반 자동 파이프라인
- **이미지 백엔드 유지**: Z-Image/Seedream/Nano Banana 중심으로 통합
- **디자인 시스템 통일**: 레퍼런스 디자인 토큰 + 기존 UI 레이아웃 유지
- **완전한 i18n**: 모든 UI 텍스트/옵션/placeholder/알림 100% 번역

### 1.3 확정 사항
- **블루프린트(패턴 생성) 기능 유지**
- **이미지 백엔드: Z-Image/Seedream/Nano Banana 유지**
- **프론트는 현행 SPA 레이아웃을 기준으로 정렬/간격 보정 후 단계적 구조 이관**

---

## 2. 아키텍처 설계

### 2.0 현행 구조 요약 (현재 코드 기준)
- **프론트**: `static/index.html` 단일 페이지(SPA) + 섹션별 폼/결과 패널
- **JS 모듈**: `static/js/main.js`, `static/js/ui.js`, `static/js/settings.js`, `static/js/i18n.js`
- **API 경로**: 서버는 `/api` 마운트, 프론트는 `/api/v1` 호출 → 경로 불일치
- **워크플로우**: `FullWorkflowService`가 요청마다 신규 인스턴스 → 상태/결과 유지 불가
- **크롤러 소스**: `crawlers/crawler_service.py` 기준 (`fashion_news`, `fashion_insta`, `musinsa`, `wgsn`, `pinterest`)
- **모델**: SQLAlchemy BaseModel 기반 + `PatternDraft`로 블루프린트 데이터 보유

### 2.1 목표 폴더 구조 (Cosmetic_case_gen 기반)
> 단기: 현행 SPA 구조를 유지하면서 정합성/UX 보정  
> 중기: 레퍼런스 구조로 점진적 이관
```
Fashion_Image_gen/
├── app/                              # 백엔드 (Cosmetic_case_gen 구조)
│   ├── main.py                       # FastAPI 진입점
│   ├── config.py                     # Pydantic 설정 관리
│   ├── crawler_config.py             # 크롤러 메타데이터
│   │
│   ├── models/                       # DB 모델 (SQLAlchemy 기준)
│   │   ├── base.py
│   │   ├── project.py                # 프로젝트 모델
│   │   ├── session.py                # 분석 세션 모델
│   │   ├── crawled_data.py           # 크롤링 데이터
│   │   ├── trend_analysis.py         # 트렌드 분석 결과
│   │   ├── design_idea.py            # 디자인 아이디어
│   │   └── generated_image.py        # 생성된 이미지
│   │
│   ├── routers/                      # FastAPI 라우터 (페이지 렌더링)
│   │   ├── pages.py                  # HTML 페이지 라우트
│   │   ├── sessions.py               # 세션 CRUD + 데이터 조회
│   │   ├── projects.py               # 프로젝트 관리
│   │   └── api_v1.py                 # API 통합 라우터
│   │
│   ├── api/v1/endpoints/             # RESTful API
│   │   ├── crawlers.py               # 크롤러 API
│   │   ├── analysis.py               # 트렌드 분석 API
│   │   ├── generation.py             # 이미지 생성 API
│   │   └── settings.py               # 설정 API
│   │
│   ├── services/                     # 비즈니스 로직
│   │   ├── crawler_service.py        # 크롤러 오케스트레이션
│   │   ├── analysis_service.py       # 트렌드 분석 (Gemini/GLM)
│   │   ├── idea_service.py           # 디자인 아이디어 생성
│   │   ├── image_generation_service.py # 이미지 생성 (Ad_imageGen_win)
│   │   ├── pipeline_orchestrator.py  # 전체 파이프라인 조율
│   │   └── gemini_service.py         # Gemini AI 클라이언트
│   │
│   ├── repositories/                 # 데이터 접근 계층
│   │   ├── session_repository.py
│   │   ├── project_repository.py
│   │   └── crawled_data_repository.py
│   │
│   ├── adapters/                     # 외부 API 어댑터
│   │   ├── image_backend_adapter.py  # Z-Image/Seedream/Nano Banana 어댑터
│   │   └── ai_client_adapter.py      # AI 클라이언트 추상화
│   │
│   ├── utils/                        # 유틸리티
│   │   ├── logger.py
│   │   └── encryption.py
│   │
│   ├── prompts/                      # AI 프롬프트 템플릿
│   │   ├── trend_analysis.py
│   │   ├── design_idea.py
│   │   └── image_prompt.py
│   │
│   └── db/                           # 데이터베이스
│       ├── database.py
│       └── init_db.py
│
├── crawlers/                         # 크롤러 모듈 (Cosmetic_case_gen 구조)
│   ├── base_crawler.py               # 추상 기본 클래스
│   ├── crawler_manager.py            # 크롤러 통합 관리
│   ├── fashion_news_crawler.py       # 패션 뉴스
│   ├── fashion_insta_crawler.py      # 인스타그램
│   ├── musinsa_crawler.py            # 무신사
│   ├── wgsn_crawler.py               # WGSN
│   └── pinterest_crawler.py          # Pinterest
│
├── templates/                        # Jinja2 HTML 템플릿 (신규)
│   ├── base.html                     # 기본 레이아웃
│   └── pages/
│       ├── dashboard.html            # 메인 대시보드
│       ├── new_session.html          # 세션 생성 폼
│       ├── session_detail.html       # 세션 상세/결과
│       ├── history.html              # 세션 히스토리/목록
│       ├── projects.html             # 프로젝트 관리
│       ├── settings.html             # 설정 페이지
│       └── manual_generation.html    # 수동 이미지 생성 (고급)
│
├── static/                           # 정적 파일
│   ├── css/
│   │   ├── variables.css             # 디자인 토큰 (Ad_imageGen_win)
│   │   ├── glassmorphism.css         # 글래스모피즘 (Cosmetic_case_gen)
│   │   ├── layout.css                # 레이아웃 유틸리티
│   │   └── components.css            # UI 컴포넌트
│   │
│   ├── js/
│   │   ├── i18n.js                   # 다국어 지원
│   │   ├── api.js                    # API 클라이언트
│   │   ├── app.js                    # 메인 앱 초기화
│   │   └── components/               # Alpine.js 컴포넌트
│   │
│   └── i18n/
│       ├── ko.json                   # 한국어 (완전)
│       ├── en.json                   # 영어 (완전)
│       ├── zh-CN.json                # 중국어 간체 (완전)
│       └── zh-TW.json                # 중국어 번체 (완전)
│
├── data/
│   ├── fashion_image.db              # SQLite 데이터베이스
│   ├── uploads/                      # 사용자 업로드
│   └── generated/                    # 생성된 이미지
│
├── logs/                             # 세션별 로그
├── plan/                             # 계획 문서
├── reference/                        # 레퍼런스 프로그램
│
├── server.py                         # 서버 실행 스크립트
├── requirements.txt
└── .env
```

### 2.2 자동 파이프라인 워크플로우 (7단계)
```
1. 프로젝트 생성/선택
   └─ 프로젝트명, 기본 설정, 언어/치수 시스템

2. 세션 생성
   └─ 제목, 설명, 키워드, 크롤러 선택, 고급 옵션

3. 데이터 크롤링 (자동)
   └─ 선택된 크롤러로 병렬 데이터 수집
   └─ 게시글/댓글/이미지 수집 → DB 저장

4. 트렌드 분석 (자동)
   └─ Gemini AI로 크롤링 데이터 분석
   └─ 패션 트렌드 요약, 키워드 추출, 인사이트 도출

5. 디자인 아이디어 생성 (자동)
   └─ 트렌드 분석 기반 디자인 컨셉 10개 생성
   └─ 의류 종류, 스타일, 색상, 소재, 디테일 포함

6. 이미지 생성 (자동/수동)
   └─ 각 아이디어별 패션 이미지 자동 생성
   └─ Z-Image/Seedream/Nano Banana 백엔드 활용
   └─ 일관성 검증 및 품질 체크

7. 결과 조회 및 내보내기
   └─ 대시보드에서 전체 결과 확인
   └─ PDF 리포트, 이미지 다운로드
```

### 2.2-1 블루프린트(패턴) 생성 흐름 (유지)
```
1. 디자인 설명/의류 종류 입력
2. 치수 시스템/사이즈 선택, 지시문/시접 옵션
3. 패턴 이미지/지시문/재료 목록 생성
4. 다운로드 및 세션 결과에 연결
```

### 2.3 데이터 모델 설계 (현행 SQLAlchemy 기준)
- **Project**: `app/models/project.py` 기반 유지
  - 보완: `default_language`, `size_standard`, `default_crawlers` 기본값/검증
- **Session**: `app/models/project.py`
  - 보완: `status`, `progress_percent`, `current_step`, 로그/에러 필드 추가
- **CrawlJob / RawData**: `app/models/crawler.py`
  - 소스명 표준화(`fashion_news`, `fashion_insta`, `musinsa`, `wgsn`, `pinterest`)
- **TrendAnalysis / TrendInsight**: `app/models/analysis.py`
  - 세션/프로젝트 연결 일관화, 분석 결과 구조 표준화
- **DesignConcept / PromptSpec**: `app/models/design.py`
  - `prompt_type`에 `blueprint` 포함, 다국어 프롬프트/번역 필드 유지
- **GenerationJob / ImageAsset**: `app/models/generation.py`
  - `model_used` 값: `zimage`, `seedream`, `nano_banana`
  - `generation_type`: `garment`, `model_fitting`, `blueprint`
- **PatternDraft**: `app/models/generation.py`
  - 블루프린트 결과 저장(파일 URL/사이즈/측정치)
- **세션/워크플로우 로그**: 별도 테이블 또는 JSON 로그 테이블로 지속성 확보

---

## 3. 구현 순서 (Phase별) - 재정렬

### Phase 0: 현행 정합화 (필수, 즉시)
1. [ ] API base 경로 통일(`/api/v1`) 및 settings prefix 정리
2. [ ] 프론트/백엔드 엔드포인트 매핑 표 작성 및 일괄 정합화 계획 수립
3. [ ] 워크플로우 세션 지속성 확보(싱글톤/DB/캐시) + 상태 조회 정상화
4. [ ] `AnalysisService.analyze_trends` 시그니처/반환 구조 정합화
5. [ ] 블루프린트 API 추가(`/blueprint/*`) + `PatternDraft/GenerationJob` 연동
6. [ ] 크롤러 소스명 통일(`fashion_news`, `fashion_insta`, `musinsa`, `wgsn`, `pinterest`)
7. [ ] `NotificationManager` 정리(UIManager 통합) + 설정 API 인증/경로 정합화

### Phase 1: i18n 전면 적용 + 모달/hidden CSS 정비
1. [ ] `static/index.html` 모든 텍스트/placeholder/옵션/버튼/상태에 i18n 키 적용
2. [ ] `main.js`/`ui.js`/`settings.js` 동적 문자열을 `t()`로 전환
3. [ ] 언어 전환 시 결과/상태 재렌더 규칙 정의
4. [ ] `.modal`, `.modal-content`, `.modal-actions`, `.hidden`, `.language-selector`,
       `.api-status-indicator`, `.status-dot` 스타일 추가

### Phase 2: 프론트엔드 레이아웃/디자인 정렬
1. [ ] 레퍼런스 디자인 토큰 적용 + 현행 레이아웃 유지
2. [ ] 고정폭 제거/정렬 재구성 (grid/flex)
3. [ ] 다국어 길이 대응(min/max, wrap, clamp)
4. [ ] 반응형 브레이크포인트 재정리

### Phase 3: 프로젝트/세션 기반 구조 이관 (Cosmetic_case_gen)
1. [ ] 프로젝트/세션 CRUD 및 자동 파이프라인 시작점 정의
2. [ ] SPA → 템플릿 단계적 전환 여부 결정 및 라우트 구성
3. [ ] Session 상태/로그/결과 링크 모델 보강

### Phase 4: 크롤러 시스템 연동
1. [ ] `crawler_config.py` 메타데이터 정의(현재 크롤러 기준 + 아이콘/설명)
2. [ ] `crawler_service.py` 진행률/에러 핸들링 연동
3. [ ] 크롤러 선택 UI 및 테스트/모니터링 화면 구성

### Phase 5: 자동 파이프라인 구현
1. [ ] 크롤링 → 분석 → 아이디어 생성 자동화
2. [ ] 상태/진행률 실시간 업데이트 API 구현
3. [ ] 세션 상세 페이지에 로그/단계 표시

### Phase 6: 이미지/블루프린트 생성 통합 (Z-Image/Seedream/Nano Banana)
1. [ ] 이미지 생성 서비스 통합 및 프롬프트 생성
2. [ ] 백엔드 선택 로직 + 품질/일관성 검증
3. [ ] 블루프린트 생성 로직 및 다운로드/결과 연계

### Phase 7: 테스트 및 검증
1. [ ] 4개 언어 전환 시 번역 누락 0건 확인(placeholder/옵션/알림 포함)
2. [ ] 자동 파이프라인 E2E 3회 연속 성공
3. [ ] 블루프린트 생성/다운로드 E2E 검증
4. [ ] 반응형 레이아웃 깨짐 없음 확인

---

## 4. API 설계 (정합화 후 기준)

### 4.0 공통
- **Base**: `/api/v1` 로 통일(프론트/백엔드 일치)
- **Health**: `GET /api/v1/health` (또는 `/health` 단일화)
- **응답 규격**: `{ success, message, data, error }`

### 4.1 프로젝트/세션 API
```
GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/{id}
PUT    /api/v1/projects/{id}
DELETE /api/v1/projects/{id}

GET    /api/v1/sessions
POST   /api/v1/sessions                 # 생성 + 자동 파이프라인 시작
GET    /api/v1/sessions/{id}
GET    /api/v1/sessions/{id}/status
GET    /api/v1/sessions/{id}/logs
POST   /api/v1/sessions/{id}/cancel
```

### 4.2 크롤러 API
```
GET    /api/v1/crawler/sources
POST   /api/v1/crawler/start
GET    /api/v1/crawler/status/{job_id}
GET    /api/v1/crawler/results/{job_id}
```

### 4.3 분석 API
```
POST   /api/v1/analysis/analyze-trends
GET    /api/v1/analysis/analysis-status/{session_id}
GET    /api/v1/analysis/trend-results/{session_id}
```

### 4.4 이미지 생성 API (수동/자동 공용)
```
POST   /api/v1/generation/fashion-design
GET    /api/v1/generation/generation-status/{design_id}
GET    /api/v1/generation/design-results/{design_id}
```

### 4.5 블루프린트 API (필수 유지)
```
POST   /api/v1/blueprint/generate
GET    /api/v1/blueprint/status/{draft_id}
GET    /api/v1/blueprint/results/{draft_id}
GET    /api/v1/blueprint/download/{draft_id}/{part}
```

### 4.6 설정 API
```
POST   /api/v1/settings/login
GET    /api/v1/settings/status
POST   /api/v1/settings/test-connection
GET    /api/v1/settings/system-config
POST   /api/v1/settings/system-config
POST   /api/v1/settings/export
POST   /api/v1/settings/import
```

---

## 5. 페이지 구조

### 5.0 현행 SPA 섹션 (static/index.html 기준, 유지/정렬 대상)
- 트렌드 분석: 키워드, 기간, 시작 버튼, 결과 패널
- 이미지 생성: 프롬프트, 의류/스타일/색상/소재/품질/변형, 결과 패널
- 블루프린트: 의류 종류, 디자인 설명, 치수 시스템/사이즈, 지시문/시접 옵션, 결과 탭
- 데이터 수집: 소스 선택, 키워드, 최대 수집량, 상태/결과 패널
- 설정: API 키/시스템/내보내기 탭, API 상태 표시

### 5.1 대시보드 (dashboard.html)
- 시작 가이드
- 최근 세션 목록
- 크롤러 상태 요약
- 빠른 시작 버튼

### 5.2 세션 생성 (new_session.html)
- 프로젝트 선택
- 세션 제목/설명
- 키워드 입력 (태그 형식)
- 크롤러 선택 (카테고리별 체크박스)
- 고급 옵션 (수집량, 날짜 범위)
- 실행 버튼

### 5.3 세션 상세 (session_detail.html)
- 탭 네비게이션:
  1. 입력 데이터
  2. 크롤링 데이터
  3. 트렌드 분석
  4. 디자인 아이디어
  5. 생성된 이미지
  6. 실시간 로그
- 진행률 바
- 현재 단계 표시

### 5.4 세션 히스토리 (history.html)
- 세션 목록 테이블
- 상태/날짜/프로젝트별 필터
- 정렬 기능 (최신순, 상태순)
- 세션 상세 페이지로 이동

### 5.5 프로젝트 관리 (projects.html)
- 프로젝트 그리드
- 생성/수정/삭제 기능
- 기본 설정 (언어, 치수 시스템, 기본 크롤러)

### 5.6 설정 (settings.html)
- 탭 네비게이션:
  1. AI API 키 (Gemini, GLM, Z-Image, Seedream, Nano Banana)
  2. 이미지 백엔드 (Z-Image/Seedream/Nano Banana 설정)
  3. 시스템 설정 (언어, 동시 요청 수 등)
  4. 크롤러 모니터링

### 5.7 수동 이미지 생성 (manual_generation.html)
- 고급 사용자용
- 프롬프트 직접 입력
- 백엔드 선택
- 상세 파라미터 설정

### 5.8 블루프린트 (blueprint.html 또는 세션 상세 탭)
- 패턴 생성 입력 폼
- 결과 탭(조각/레이아웃/지시문/재료)
- 다운로드/내보내기

---

## 6. i18n 키 체계
> 모든 UI 텍스트(정적/동적/placeholder/옵션/알림/상태/로딩/모달)를 키로 분리  
> JS 동적 문자열은 `t()`로 통일, 언어 전환 시 결과/상태 재렌더 규칙 포함

### 6.1 공통 (common)
```json
{
  "common": {
    "save": "저장",
    "cancel": "취소",
    "confirm": "확인",
    "delete": "삭제",
    "edit": "수정",
    "create": "생성",
    "loading": "로딩 중...",
    "error": "오류",
    "success": "성공",
    "warning": "경고"
  }
}
```

### 6.2 네비게이션 (navigation)
```json
{
  "navigation": {
    "trendAnalysis": "트렌드 분석",
    "imageGeneration": "이미지 생성",
    "blueprint": "패턴 생성",
    "crawler": "데이터 수집",
    "settings": "설정",
    "dashboard": "대시보드",
    "newSession": "새 세션",
    "projects": "프로젝트",
    "manualGeneration": "수동 생성"
  }
}
```

### 6.3 세션 (session)
```json
{
  "session": {
    "title": "세션 제목",
    "description": "설명",
    "keywords": "키워드",
    "selectCrawlers": "크롤러 선택",
    "advancedOptions": "고급 옵션",
    "startPipeline": "파이프라인 시작",
    "status": {
      "created": "생성됨",
      "crawling": "크롤링 중",
      "analyzing": "분석 중",
      "generating": "생성 중",
      "completed": "완료",
      "failed": "실패"
    }
  }
}
```

### 6.4 크롤러 (crawlers)
```json
{
  "crawlers": {
    "categories": {
      "fashionNews": "패션 뉴스",
      "shopping": "쇼핑몰",
      "socialMedia": "소셜 미디어",
      "trendReport": "트렌드 리포트"
    },
    "sources": {
      "fashion_news": "패션 뉴스",
      "fashion_insta": "인스타그램",
      "musinsa": "무신사",
      "wgsn": "WGSN",
      "pinterest": "Pinterest"
    }
  }
}
```

### 6.5 설정 (settings)
```json
{
  "settings": {
    "title": "설정",
    "tabs": {
      "apiKeys": "AI API 키",
      "imageBackend": "이미지 백엔드",
      "system": "시스템 설정",
      "crawlerMonitor": "크롤러 모니터링"
    },
    "apiKeys": {
      "gemini": "Gemini API 키",
      "glm": "GLM API 키",
      "zimage": "Z-Image API 키",
      "seedream": "Seedream API 키",
      "nanoBanana": "Nano Banana API 키",
      "testConnection": "연결 테스트"
    }
  }
}
```

### 6.6 블루프린트 (blueprint)
```json
{
  "blueprint": {
    "title": "패턴 블루프린트 생성",
    "tabs": {
      "pieces": "패턴 조각",
      "layout": "레이아웃",
      "instructions": "지시문",
      "materials": "재료 목록"
    }
  }
}
```

### 6.7 UI/상태/알림 (ui)
```json
{
  "ui": {
    "apiStatus": {
      "configured": "API 설정 완료",
      "notConfigured": "API 미설정",
      "testing": "테스트 중...",
      "success": "연결 성공",
      "failed": "테스트 실패"
    },
    "loading": "처리 중...",
    "modal": {
      "title": "제목",
      "confirm": "확인",
      "cancel": "취소"
    }
  }
}
```

---

## 7. 리스크 및 대응

### 7.1 기술적 리스크
| 리스크 | 영향 | 대응 |
|--------|------|------|
| 마이그레이션 중 기존 기능 손실 | 높음 | 단계별 테스트, 백업 |
| 이미지 백엔드 연동 실패 | 중간 | 폴백 체인 (Z-Image → Seedream → Nano Banana) |
| 크롤러 차단/제한 | 중간 | 재시도 로직, 프록시 지원 |

### 7.2 일정 리스크
| 리스크 | 영향 | 대응 |
|--------|------|------|
| Phase 간 의존성으로 지연 | 중간 | 병렬 작업 가능한 부분 식별 |
| 레퍼런스 코드 이해 부족 | 중간 | 충분한 분석 시간 확보 |

---

## 8. Open Questions 해결

### Q1: UI 기준 프로그램?
**A**: Cosmetic_case_gen의 워크플로우/구조 + Ad_imageGen_win의 디자인 토큰 조합

### Q2: 자동 파이프라인 범위?
**A**: 크롤링 → 트렌드 분석 → 디자인 아이디어 10개 → 각 아이디어별 이미지 1-3개

### Q3: 수동 기능 위치?
**A**: "수동 생성" 별도 페이지로 분리, 고급 사용자용

### Q4: 블루프린트(패턴 생성) 유지?
**A**: 유지. SPA 섹션 및 멀티페이지 탭에 포함

### Q5: 이미지 백엔드 우선순위?
**A**: Z-Image/Seedream/Nano Banana 유지 및 기본 백엔드로 통합

---

## 9. 성공 기준

1. **i18n 100%**: 4개 언어 전환 시 번역 누락 0건
2. **API 정합성**: `/api/v1` 기준 404/경로 불일치 0건
3. **자동 파이프라인 안정성**: E2E 3회 연속 성공
4. **블루프린트 기능**: 생성/다운로드 E2E 정상 동작
5. **UI 품질**: 레퍼런스 프로그램 수준의 정렬/간격/디자인
6. **응답 시간**: 페이지 로드 < 2초, 파이프라인 시작 < 3초
7. **에러 처리**: 모든 실패 상황에서 명확한 에러 메시지 표시

---

## 10. 다각도 검토 기준 (3회)
1. **정합성 관점**: API 경로, 워크플로우 세션 지속성, 서비스 시그니처 일치 여부
2. **UX/i18n 관점**: 모든 텍스트/placeholder/옵션/알림/상태 번역 누락 여부
3. **디자인/레이아웃 관점**: 기존 UI 정렬/간격 유지, 다국어 길이 대응, 반응형 깨짐 여부

## 11. 참조 문서

- Cosmetic_case_gen 분석: `/reference/Cosmetic_case_gen/`
- Ad_imageGen_win 분석: `/reference/Ad_imageGen_win/`
- 현재 프로젝트 분석: 본 문서 상단
- 현재 프론트 기준: `/static/index.html`, `/static/js/main.js`, `/static/js/ui.js`, `/static/css/style.css`
