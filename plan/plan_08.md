# Plan 08: 핵심 기능 완성 및 크롤러 전면 활성화

**작성일**: 2025-12-22 03:00
**목표**: 핵심 파이프라인 완성, 모든 크롤러 활성화, 이미지 생성 검증

---

## 현재 상황 분석

### 문제점
1. **크롤러 대부분 비활성화**: 레퍼런스에 있는 크롤러들이 복사되지 않음
2. **핵심 파이프라인 미검증**: 실제 동작 여부 확인 안됨
3. **이미지 생성 미검증**: 서비스 존재하나 연동 상태 불명
4. **불필요한 작업에 시간 낭비**: i18n, 네비게이션 등 부차적 작업에 집중

### 현재 크롤러 상태
- **현재 프로젝트 크롤러** (crawlers/):
  - fashion_news_crawler.py ✅
  - fashion_insta_crawler.py ✅
  - musinsa_crawler.py ✅
  - wgsn_crawler.py ✅
  - pinterest_crawler.py ✅
  - nate_news_crawler.py ✅

- **레거시 크롤러** (crawlers/legacy/):
  - dcinside_crawler.py
  - blind_crawler.py
  - etoland_crawler.py
  - inven_crawler.py

- **레퍼런스에 있으나 미복사**:
  - naver_blog_crawler.py
  - naver_cafe_crawler.py
  - daum_cafe_crawler.py
  - youtube_crawler.py
  - theqoo_crawler.py
  - fmkorea_crawler.py
  - clien_crawler.py
  - ruliweb_crawler.py
  - ppomppu_crawler.py
  - mlbpark_crawler.py

---

## Phase 1: 크롤러 전면 복사 및 활성화

### 1.1 레퍼런스에서 크롤러 복사
- [ ] naver_blog_crawler.py 복사 및 import 수정
- [ ] naver_cafe_crawler.py 복사 및 import 수정
- [ ] daum_cafe_crawler.py 복사 및 import 수정
- [ ] youtube_crawler.py 복사 및 import 수정
- [ ] theqoo_crawler.py 복사 및 import 수정
- [ ] fmkorea_crawler.py 복사 및 import 수정
- [ ] clien_crawler.py 복사 및 import 수정

### 1.2 레거시 크롤러 메인으로 이동
- [ ] dcinside_crawler.py → crawlers/ 이동
- [ ] blind_crawler.py → crawlers/ 이동
- [ ] etoland_crawler.py → crawlers/ 이동
- [ ] inven_crawler.py → crawlers/ 이동

### 1.3 crawler_config.py 전면 수정
- [ ] 모든 크롤러 enabled: True 설정
- [ ] module/class 정확히 매핑
- [ ] 카테고리 정리

---

## Phase 2: 핵심 파이프라인 검증

### 2.1 세션 생성 → 파이프라인 실행 흐름
1. POST /api/v1/sessions/ - 세션 생성
2. POST /api/v1/sessions/{id}/run-analysis - 파이프라인 시작
3. GET /api/v1/sessions/{id}/status - 진행률 조회
4. GET /api/v1/sessions/{id}/results - 결과 조회

### 2.2 파이프라인 7단계 검증
- [ ] Step 1: 입력 분석 (멀티모달)
- [ ] Step 2: 키워드 추출 (AI)
- [ ] Step 3: 데이터 수집 (크롤링)
- [ ] Step 4: 트렌드 분석
- [ ] Step 5: 디자인 아이디어 생성
- [ ] Step 6: 이미지 생성
- [ ] Step 7: 블루프린트 생성

### 2.3 크롤러-파이프라인 연동 확인
- [ ] CrawlerService.start_crawl() 동작 확인
- [ ] 크롤러별 run() 메서드 호출 확인
- [ ] 수집 데이터 형식 검증

---

## Phase 3: 이미지 생성 검증

### 3.1 ImageGenerationService 연동
- [ ] Gemini API 연결 확인
- [ ] GLM API 연결 확인
- [ ] Seedream API 연결 확인
- [ ] Nano Banana API 연결 확인

### 3.2 이미지 생성 API 테스트
- [ ] POST /api/v1/generation/image 테스트
- [ ] 생성된 이미지 저장 경로 확인
- [ ] 세션에 이미지 연결 확인

---

## Phase 4: 프론트엔드 정합성

### 4.1 세션 페이지
- [ ] new_session.html - 크롤러 선택 UI
- [ ] session_detail.html - 결과 표시
- [ ] history.html - 세션 목록

### 4.2 대시보드
- [ ] 크롤러 상태 표시
- [ ] 최근 세션 표시
- [ ] 통계 표시

---

## 우선순위

1. **최우선**: 크롤러 전면 활성화 (Phase 1)
2. **긴급**: 파이프라인 동작 검증 (Phase 2)
3. **중요**: 이미지 생성 검증 (Phase 3)
4. **보통**: 프론트엔드 정합성 (Phase 4)

---

## 완료 기준

- [ ] 모든 크롤러 enabled: True
- [ ] 파이프라인 전체 흐름 테스트 통과
- [ ] 이미지 생성 API 동작 확인
- [ ] 세션 생성 → 분석 → 결과 확인 워크플로우 성공
