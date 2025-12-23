# Todo 09: 2단 레이아웃 + 워크플로우 + 이미지/블루프린트 파이프라인

**작성일**: 2025-12-22 04:00
**수정일**: 2025-12-22 08:30
**기준**: plan_09.md

---

## Phase 1: 2단 레이아웃 UI ✅

- [x] dashboard.html 2단 레이아웃 구현
- [x] 왼쪽 패널: 프로젝트/세션 선택
- [x] 오른쪽 패널: 5개 탭 (개요/데이터/분석/의상/착장)
- [x] CSS 스타일 추가

---

## Phase 2: 워크플로우 정합성 ✅

- [x] 프로젝트 생성 모달
- [x] 세션 생성 폼
- [x] 분석 실행 버튼 연동
- [x] 진행률 표시
- [x] 탭별 결과 표시

---

## Phase 3: 라이브러리 페이지 ✅

- [x] library.html 생성
- [x] 이미지 그리드 표시
- [x] 필터/정렬 기능
- [x] API 엔드포인트 추가 (GET /api/v1/library)

---

## Phase 4: 이미지 생성 파이프라인 ✅

- [x] 디자인 원칙 추가 (vfx-and-life.com, KR102173900B1)
- [x] 마스터 디자인 생성 (Flat Lay)
- [x] 모델 착장 생성 (마스터 디자인 기반 일관성)
- [x] pipeline_orchestrator.py 3단계 이미지 생성 통합

---

## Phase 4.5: 블루프린트 생성 파이프라인 ✅

- [x] 스케치 생성 (Fashion Design Sketch)
- [x] 레이아웃 도면 생성 (Flat Layout Drawing)
- [x] 패턴 제도도 생성 (Technical Pattern Drawing)
- [x] BlueprintService.generate_three_blueprints() 구현
- [x] pipeline_orchestrator에 3종 블루프린트 통합

---

## Phase 5: 테스트 ✅

- [x] Python 구문 검증 완료
- [x] 모듈 import 테스트 (10개 핵심 모듈)
- [x] FastAPI 앱 로드 테스트 (86개 라우트)
- [x] API 엔드포인트 테스트 (health, projects, sessions, library, blueprint, pages)
- [x] CRUD 테스트 (프로젝트/세션 생성·조회·수정·삭제)

---

**진행 상태**: Phase 1-5 모두 완료 ✅

## 참고 자료

1. **의상 디자인 요소 및 원칙** (vfx-and-life.com)
   - 디자인 요소: 컨셉, 형태, 라인, 질감, 색상
   - 디자인 원칙: 비례/스케일, 균형, 통일감, 리듬, 초점

2. **KR102173900B1 특허**
   - 파라메트릭 패턴 생성 (신체 치수 기반)
   - 3D 드레이프 시뮬레이션
   - 패턴 수정 이력 관리 (dx = DX/W, dy = DY/H)

3. **FashionDesign411 패션 플랫 스케치**
   - 업계 표준 템플릿 (전면/후면 뷰)
   - Float 스타일 (자유 손그림 느낌)
   - CAD 최적화 (AI, SVG, PNG 벡터 형식)
   - 의류 카테고리별 템플릿 (여성/남성/아동)
