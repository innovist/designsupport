# Todo 07: Fashion AI Generation System 전면 재설계 체크리스트

**작성일**: 2025-12-21 16:00
**기준**: plan_07.md

---

## Phase 0: 기존 코드 백업 (필수)
- [x] static/ 폴더 → static_legacy/로 이동 (백업)
- [x] 기존 app/api/routes.py 백업
- [x] 기존 main.py 백업 (archive/main_phase6.py)

---

## Phase 1: 레퍼런스 파일 복사 및 텍스트 변경

### ⚠️ 핵심: 레퍼런스 복사 → 텍스트만 변경 (UI/UX 검증됨)

### 1.1 Jinja2 설정
- [x] main.py에 Jinja2Templates 설정 추가
- [x] templates/ 폴더 생성
- [x] templates/pages/ 폴더 생성

### 1.2 CSS 복사 (그대로)
- [x] reference/Cosmetic_case_gen/static/css/design-system.css → static/css/design-system.css

### 1.3 템플릿 복사 및 텍스트 변경
- [x] base.html 복사 → "화장품 용기 아이디어"→"패션 트렌드 AI" 변경
- [x] dashboard.html 복사 → 텍스트 변경
- [x] new_session.html 복사 → 텍스트 변경 + 패션 필터 추가
- [x] session_detail.html 복사 → 텍스트 변경
- [x] history.html 복사 → 텍스트 변경
- [x] settings.html 복사 → 텍스트 변경
- [x] projects.html 복사 → 텍스트 변경
- [x] project_detail.html 복사 → 텍스트 변경
- [x] new_project.html 복사 → 텍스트 변경
- [x] ideas.html 복사 → 텍스트 변경
- [x] chatbot.html 복사 → 텍스트 변경

### 1.4 텍스트 변경 목록
| 원본 | 변경 |
|-----|-----|
| 화장품 용기 아이디어 발굴 시스템 | 패션 트렌드 AI 생성 시스템 |
| 화장품 용기/케이스 | 패션 디자인 |
| AI 아이디어 발굴 | 패션 AI 생성 |
| 화장품 | 패션 |

---

## Phase 2: 패션 특화 세션 UI (new_session.html)

### 2.1 세션 정보 섹션
- [x] 세션 제목 입력 (필수)
- [x] 세션 설명 입력 (필수) - AI 분석 지시사항
- [x] 사용자 정의 키워드 (선택사항)

### 2.2 패션 분석 조건 (신규)
- [x] 성별 선택: 남성 / 여성 / 유니섹스 / 전체
- [x] 나이대 선택: 10대 / 20대 / 30대 / 40대 / 50대+ / 전체
- [x] 계절 선택: 봄/여름 / 가을/겨울 / 전체
- [x] 카테고리: 상의 / 하의 / 원피스 / 아우터 / 액세서리 / 전체

### 2.3 입력 데이터 섹션 (선택사항)
- [x] 텍스트 입력 (AI 추가 지시)
- [x] 파일 업로드 (이미지, PDF)
- [x] URL 입력 (다중)

### 2.4 크롤러 선택 섹션
- [x] 카테고리별 크롤러 체크박스 UI
- [x] 전체선택 / 전체해제 버튼
- [x] 수집 범위 설정 (날짜, 게시물 수)

---

## Phase 3: 크롤러 설정

### 3.1 crawler_config.py 작성
- [x] CRAWLER_CATEGORIES 정의 (패션 특화)
  - [x] fashion_community: 무신사, W컨셉, 29CM, 에이블리
  - [x] community: 더쿠, FM코리아, 인스티즈, 블라인드
  - [x] portal: 네이버블로그, 네이버카페, 다음카페
  - [x] media: 인스타그램, 유튜브, 핀터레스트
  - [x] news: 패션N, WGSN, 보그코리아
- [x] get_all_crawlers() 함수
- [x] get_enabled_crawlers() 함수

### 3.2 기존 크롤러 연동
- [x] 기존 크롤러 모듈 확인
- [x] crawler_config와 기존 크롤러 매핑

---

## Phase 4: 파이프라인 구현

### 4.1 pipeline_orchestrator.py 작성
- [x] FashionPipelineOrchestrator 클래스
- [x] run_complete_pipeline() 메서드
 - [x] 7단계 파이프라인 구현:
  - [x] Step 1: 입력 분석 (멀티모달)
  - [x] Step 2: 키워드 추출 (AI + 사용자 정의)
  - [x] Step 3: 데이터 수집 (크롤링)
  - [x] Step 4: 트렌드 분석 (패션 니즈 추출)
  - [x] Step 5: 디자인 아이디어 생성
  - [x] Step 6: 이미지 생성 (선택)
  - [x] Step 7: 블루프린트 생성 (선택)
- [x] get_pipeline_status() 메서드

### 4.2 세션 API 연동
- [x] POST /api/v1/sessions/ - 세션 생성
- [x] POST /api/v1/sessions/{id}/run-analysis - 분석 시작
- [x] GET /api/v1/sessions/{id}/status - 진행률 조회
- [x] GET /api/v1/sessions/{id}/results - 결과 조회

---

## Phase 5: 분석/아이디어 생성

### 5.1 트렌드 분석 서비스
- [x] 패션 필터 적용 (성별/나이대/계절/카테고리)
- [x] 크롤링 데이터에서 트렌드 추출
- [x] Gemini 기반 분석

### 5.2 디자인 아이디어 생성
- [x] 트렌드 기반 아이디어 생성
- [x] 아이디어 저장 및 표시

---

## Phase 6: 이미지 생성 통합

### 6.1 기존 이미지 서비스 연동
- [x] ImageGenerationService 세션 연동
- [x] 세션 결과에 이미지 저장

### 6.2 블루프린트 생성 (선택)
- [x] BlueprintService 세션 연동

---

## Phase 7: 테스트 및 검증

### 7.1 기능 테스트
- [x] 세션 생성 테스트
- [x] 크롤러 선택 테스트 (루트 엔드포인트 추가)
- [x] 파이프라인 실행 테스트 (구조 검증 완료)
- [x] 결과 표시 테스트

### 7.2 UI/UX 검증
- [x] 템플릿 렌더링 확인 (10개 페이지 OK)
- [x] 네비게이션 동작 확인
- [x] 반응형 레이아웃 확인

### 7.3 Python 구문 검증
- [x] 모든 .py 파일 구문 검증 (python -m py_compile)
- [x] import 구조 검증

---

## 완료 기준

- [x] 모든 Phase 체크리스트 완료
- [x] 서버 정상 실행 (python main.py)
- [x] 대시보드 접속 확인 (http://localhost:8912)
- [x] 새 세션 생성 → 분석 실행 → 결과 확인 워크플로우 성공
- [x] worksheet.md 업데이트

---

**진행 상태**: Phase 7 완료 (2025-12-22)
