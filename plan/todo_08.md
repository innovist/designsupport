# Todo 08: 핵심 기능 완성 체크리스트

**작성일**: 2025-12-22 03:00
**기준**: plan_08.md

---

## Phase 1: 크롤러 전면 활성화 (최우선) ✅ 완료

### 1.1 레퍼런스 크롤러 복사
- [x] naver_blog_crawler.py
- [x] naver_cafe_crawler.py
- [x] daum_cafe_crawler.py
- [x] youtube_crawler.py
- [x] theqoo_crawler.py
- [x] fmkorea_crawler.py
- [x] clien_crawler.py
- [x] ppomppu_crawler.py
- [x] ruliweb_crawler.py
- [x] mlbpark_crawler.py

### 1.2 레거시 크롤러 이동
- [x] dcinside_crawler.py
- [x] blind_crawler.py
- [x] etoland_crawler.py
- [x] inven_crawler.py

### 1.3 crawler_config.py 전면 수정
- [x] 모든 크롤러 enabled: True (20개)
- [x] module/class 매핑 완료

---

## Phase 2: 파이프라인 검증 (긴급) ✅ 완료

### 2.1 API 엔드포인트 확인
- [x] POST /api/v1/projects/ 동작 (200)
- [x] POST /api/v1/sessions/ 동작 (200)
- [x] POST /api/v1/sessions/{id}/run-analysis 동작 (200)
- [x] GET /api/v1/sessions/{id} 동작 (200)

### 2.2 파이프라인 단계별 검증
- [x] 프로젝트 생성
- [x] 세션 생성
- [x] 파이프라인 시작 (run-analysis)
- [ ] 실제 크롤링 실행 (API 키 필요)
- [ ] 트렌드 분석 (API 키 필요)
- [ ] 이미지 생성 (API 키 필요)

---

## Phase 3: 이미지 생성 검증 (중요)

- [x] 이미지 모델 API 동작 확인
- [ ] 실제 이미지 생성 테스트 (API 키 필요)

---

## Phase 4: 프론트엔드 (보통)

- [x] 크롤러 목록 API 동작
- [ ] 크롤러 선택 UI 확인
- [ ] 결과 표시 확인

---

**진행 상태**: Phase 2 완료, API 키 설정 필요
**활성 크롤러**: 20개 (전체 활성화)
