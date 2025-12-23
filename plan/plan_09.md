# Plan 09: 2단 레이아웃 + 논리적 워크플로우 + 이미지 생성 파이프라인

**작성일**: 2025-12-22 04:00
**목표**: UX 중심 논리적 워크플로우 재설계, 이미지 일관성 파이프라인 구축

---

## 1. 현재 문제점 분석

### 1.1 UX/워크플로우 문제
- 프로젝트 → 세션 흐름이 직관적이지 않음
- 대시보드에서 프로젝트 생성/관리 불가
- 결과 확인 UI 분산됨 (탭 구조 없음)
- 챗봇 영역이 불필요하게 존재

### 1.2 이미지 생성 파이프라인 문제
- 의상 디자인 → 모델 착장 일관성 미보장
- 참조 이미지 기반 생성 로직 미완성
- 프롬프트 최적화 부족

### 1.3 API 키 저장 문제
- 저장 후 사라지는 현상 (확인 필요)

---

## 2. 목표 아키텍처

### 2.1 UI 레이아웃 (2단 구조)

```
┌─────────────────────────────────────────────────────────────┐
│                        헤더 (네비게이션)                      │
├───────────────┬─────────────────────────────────────────────┤
│               │                                             │
│   프로젝트/   │              보고서 영역                      │
│   세션 선택   │  ┌─────┬─────┬─────┬─────┬─────┐            │
│   (왼쪽 패널) │  │개요 │데이터│분석 │의상 │착장 │            │
│               │  ├─────┴─────┴─────┴─────┴─────┤            │
│   - 프로젝트  │  │                              │            │
│     목록      │  │      탭 콘텐츠               │            │
│   - + 추가    │  │                              │            │
│   - 세션 목록 │  │                              │            │
│   - + 추가    │  │                              │            │
│               │  │                              │            │
├───────────────┼──┴──────────────────────────────┴────────────┤
│ 너비: 280px   │              너비: 나머지                      │
└───────────────┴─────────────────────────────────────────────┘
```

### 2.2 네비게이션 구조

| 메뉴 | 설명 | 경로 |
|------|------|------|
| 대시보드 | 프로젝트/세션/분석/결과 통합 화면 | / |
| 라이브러리 | 생성된 이미지 조회/필터 | /library |
| 설정 | API 키, 언어 설정 | /settings |

### 2.3 보고서 탭 구조

| 탭 | 내용 |
|----|------|
| 개요 | 세션 요약, 진행률, 주요 지표 |
| 수집 데이터 | 크롤링 결과, 게시물/댓글 목록 |
| 분석 보고서 | 트렌드 분석, 키워드, 인사이트 |
| 의상 이미지 | 생성된 의상 디자인 + 블루프린트 |
| 착장 이미지 | 모델 착장 이미지 갤러리 |

---

## 3. 논리적 워크플로우 (Use Case)

### 3.1 사용자 플로우

```
[1. 프로젝트 생성]
    ↓
[2. 세션 생성]
    - 세션 이름 입력
    - 분석 필터 설정 (성별, 계절, 카테고리)
    - 크롤러 선택
    ↓
[3. 분석 시작]
    ↓
[4. 파이프라인 자동 실행]
    4.1 키워드 추출 (AI)
    4.2 크롤링 실행
    4.3 트렌드 분석
    4.4 디자인 아이디어 생성
    4.5 의상 이미지 생성
    4.6 모델 착장 이미지 생성
    4.7 블루프린트 생성
    ↓
[5. 결과 확인 (탭)]
    - 개요: 요약
    - 수집 데이터: 크롤링 결과
    - 분석 보고서: 트렌드/키워드
    - 의상 이미지: 디자인 + 블루프린트
    - 착장 이미지: 모델 이미지
```

### 3.2 API 엔드포인트 흐름

```
POST /api/v1/projects/                    # 프로젝트 생성
POST /api/v1/sessions/                    # 세션 생성
POST /api/v1/sessions/{id}/run-analysis   # 파이프라인 시작
GET  /api/v1/sessions/{id}/status         # 진행률 조회
GET  /api/v1/sessions/{id}/results        # 전체 결과
GET  /api/v1/sessions/{id}/crawled-data   # 수집 데이터
GET  /api/v1/sessions/{id}/analysis       # 분석 결과
GET  /api/v1/sessions/{id}/images         # 생성 이미지
```

---

## 4. 이미지 생성 파이프라인 (핵심)

### 4.1 일관성 유지 원칙

**문제**: 의상 디자인과 착장 이미지가 일치하지 않음
**해결**: Multi-Reference Image Generation 적용

### 4.2 3단계 이미지 생성 프로세스

```
┌──────────────────────────────────────────────────────────────┐
│ Step 1: 의상 디자인 상세 프롬프트 생성 (Gemini)               │
│   Input:  트렌드 분석 결과, 키워드, 스타일 지정               │
│   Output: 초상세 영문 디자인 프롬프트                         │
│   - 색상, 소재, 실루엣, 디테일, 장식 등 구체적 묘사           │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ Step 2: 의상 디자인 이미지 생성 (Seedream/Nano Banana)       │
│   Input:  Step 1 프롬프트                                    │
│   Output: Flat Lay 의상 디자인 이미지 (마스터 디자인)         │
│   - 배경: 흰색/단색                                          │
│   - 시점: 정면, 평면 배치                                    │
│   - 고해상도: 1024x1024 이상                                 │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
                    [마스터 디자인 저장]
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ Step 3: 모델 착장 이미지 생성 (IP-Adapter + ControlNet)      │
│   Input:  마스터 디자인 이미지 + 모델 포즈 참조               │
│   Output: 모델이 의상을 착용한 패션 화보 이미지               │
│   - 마스터 디자인 일관성 유지 (IP-Adapter)                   │
│   - 포즈/구도 제어 (ControlNet)                              │
│   - 다양한 포즈로 3-5장 생성                                 │
└──────────────────────────────────────────────────────────────┘
```

### 4.3 디자인 요소 및 원칙 (참고: vfx-and-life.com, KR102173900B1)

#### 4.3.1 핵심 디자인 요소

| 요소 | 설명 | 프롬프트 반영 |
|------|------|---------------|
| **컨셉** | 디자인의 핵심 아이디어 | 트렌드 키워드로 표현 |
| **형태(Form)** | 원형(여성적), 예각(에너지), 유기적(역동) | 실루엣 지정 |
| **라인** | 직선/곡선, 세로/가로선 | seam lines, design lines |
| **질감** | 금속, 벨벳, 가죽, 시폰 등 | fabric texture |
| **색상** | 전체 조화, 대비 | color palette |

#### 4.3.2 디자인 원칙

| 원칙 | 설명 | 적용 방법 |
|------|------|-----------|
| **비례/스케일** | 요소 간 상대적 크기 | 패턴 제도시 신체 비율 반영 |
| **균형** | 대칭/비대칭 안정감 | 전면/후면 레이아웃 |
| **통일감** | 형태, 패턴, 색상 조화 | 마스터 디자인 → 착장 일관성 |
| **리듬** | 요소 반복으로 움직임 | 패턴 반복, 주름 |
| **초점** | 대조로 우위성 확보 | 포인트 디테일 강조 |

#### 4.3.3 파라메트릭 패턴 생성 원칙 (KR102173900B1)

```python
# 신체 치수 기반 패턴 자동 생성
pattern_params = {
    "base_measurements": ["bust", "waist", "hip", "shoulder"],
    "derived_points": "f(base_point, relationship_formula)",
    "modification_tracking": {
        "dx": "DX / pattern_width",   # 상대적 이동량
        "dy": "DY / pattern_height"
    }
}
```

### 4.4 프롬프트 작성 전략

**Step 1 프롬프트 생성 지침 (Gemini 사용)**:
```
당신은 패션 디자인 전문가입니다.
다음 트렌드 분석 결과를 바탕으로 AI 이미지 생성을 위한
초상세 영문 프롬프트를 작성하세요.

트렌드 키워드: {keywords}
스타일: {style}
의류 종류: {garment_type}
계절: {season}
성별: {gender}

프롬프트는 다음을 반드시 포함:
1. 의류 타입 (dress, coat, pants, etc.)
2. 색상 (구체적: "dusty rose pink", "navy blue")
3. 소재 (silk, cotton, wool, leather, etc.)
4. 실루엣 (A-line, fitted, oversized, etc.)
5. 디테일 (pleats, buttons, zippers, embroidery)
6. 장식 (lace trim, metallic hardware, etc.)
7. 품질 지시어 (high fashion, editorial, professional)
8. 형태 원칙 (균형, 비례, 리듬, 초점 등)

출력 형식: 영문 1단락, 150-200 단어
```

**Step 2 이미지 생성 프롬프트 구조**:
```
Professional fashion design flat lay photography.
{Step 1 생성 프롬프트}
Clean white background, centered composition,
soft studio lighting, high detail, 8k quality,
fashion catalog style, no model, garment only.
```

**Step 3 모델 착장 프롬프트 구조**:
```
Professional fashion photography, high-end editorial.
Fashion model wearing {의류 설명}.
{Step 1 핵심 디자인 요소 유지}
Full body shot, studio lighting, clean background,
fashion magazine quality, 8k, sharp focus.
```

### 4.4 IP-Adapter + ControlNet 파라미터

```python
# 일관성 파라미터
consistency_params = {
    "ip_adapter_scale": 0.8,        # 마스터 디자인 반영 강도
    "controlnet_conditioning_scale": 0.7,
    "guidance_scale": 7.5,
    "reference_strength": 0.85,     # 참조 이미지 가중치
}
```

### 4.5 모델 선택 전략

| 작업 | 1순위 | 2순위 | 3순위 |
|------|-------|-------|-------|
| 의상 디자인 | Seedream | Nano Banana | - |
| 모델 착장 | Nano Banana (IP-Adapter) | Seedream | - |
| 블루프린트 | Gemini (imagen-3) | Seedream | - |

---

## 5. 블루프린트 생성 파이프라인 (신규)

### 5.1 블루프린트 타입 정의

의상 디자인당 3종류의 블루프린트를 생성:

| 타입 | 설명 | 용도 |
|------|------|------|
| **스케치 (Sketch)** | 패션 디자인 스케치 | 디자이너 아이디어 시각화, 초기 컨셉 전달 |
| **레이아웃 도면 (Layout)** | 평면 전개도/레이아웃 | 의상 구조 파악, 원단 배치 계획 |
| **패턴 제도도 (Pattern)** | 실제 제작용 패턴 도면 | 봉제 공장 전달, 실제 제작 |

### 5.2 블루프린트 생성 프로세스

```
┌──────────────────────────────────────────────────────────────┐
│ Step B1: 스케치 생성 (Fashion Design Sketch)                 │
│   Input:  마스터 디자인 이미지 + 디자인 프롬프트              │
│   Output: 패션 일러스트레이션 스타일 스케치                    │
│   - 연필/마커 스타일                                          │
│   - 디자인 의도 강조                                          │
│   - 컬러 & 흑백 버전                                          │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ Step B2: 레이아웃 도면 생성 (Flat Layout Drawing)            │
│   Input:  마스터 디자인 이미지 + 의상 구조 분석               │
│   Output: 평면 전개도 (Flat Pattern Layout)                   │
│   - 전면/후면 분리 도면                                       │
│   - 부분별 명칭 라벨링                                        │
│   - 치수 기준선 표시                                          │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ Step B3: 패턴 제도도 생성 (Technical Pattern Drawing)        │
│   Input:  레이아웃 도면 + 표준 치수 시스템 (KS/GB/ASTM/ISO)  │
│   Output: 봉제용 패턴 제도도                                  │
│   - 실물 크기 패턴 조각                                       │
│   - 시접/봉제선 표시                                          │
│   - 원단 결/방향 표시                                         │
│   - 제작 지시문 포함                                          │
└──────────────────────────────────────────────────────────────┘
```

### 5.3 패션 플랫 스케치 표준 (참고: FashionDesign411)

#### 업계 표준 특징
- **전면/후면 구성**: 양면 뷰 (Front & Back views)
- **Float 스타일**: 비정형 자유 손그림 느낌 스케치
- **CAD 최적화**: 벡터 형식 지원 (AI, SVG, PNG)
- **쉬운 수정**: 색상 변형, 디테일 추가/제거 용이

#### 의류 카테고리별 템플릿
| 대분류 | 상세 |
|--------|------|
| 여성용 | 상의, 바지, 드레스, 재킷, 언더웨어 |
| 남성용 | 셔츠, 바지, 자켓, 스웨터 |
| 아동용 | 상의, 바지, 드레스, 외투 |

### 5.4 블루프린트 프롬프트 전략

**스케치 생성 프롬프트**:
```
Fashion design sketch illustration.
{의상 디자인 설명}
Hand-drawn style, fashion illustration,
pencil and marker technique, dynamic pose hint,
fabric texture indication, professional fashion sketch,
white background, clean lines.
```

**레이아웃 도면 프롬프트**:
```
Technical flat pattern layout drawing.
{의상 구조: 전면, 후면, 소매, 칼라 등}
Flat lay technical drawing, front and back views,
labeled parts, seam lines indicated,
professional pattern drafting style,
clean white background, CAD-like precision.
```

**패턴 제도도 프롬프트**:
```
Sewing pattern technical draft.
{패턴 조각: 앞판, 뒷판, 소매 등}
Pattern pieces with seam allowance,
grain line arrows, notches marked,
size {size} ({size_system} standard),
measurement annotations, cutting instructions,
professional pattern maker style.
```

### 5.4 블루프린트 출력 형식

```python
blueprint_output = {
    "sketch": {
        "type": "sketch",
        "url": "/storage/blueprints/sketch_001.png",
        "format": "PNG",
        "resolution": "1024x1024"
    },
    "layout": {
        "type": "layout",
        "url": "/storage/blueprints/layout_001.png",
        "views": ["front", "back"],
        "format": "PNG",
        "resolution": "1024x1024"
    },
    "pattern": {
        "type": "pattern",
        "url": "/storage/blueprints/pattern_001.png",
        "size_system": "KS",
        "size": "M",
        "pieces": ["front_bodice", "back_bodice", "sleeve"],
        "format": "PNG",
        "resolution": "2048x2048"  # 고해상도 필요
    }
}
```

---

## 6. 라이브러리 페이지

### 6.1 기능 요구사항

- 생성된 모든 이미지 그리드 표시
- 필터: 프로젝트, 세션, 이미지 타입, 날짜
- 정렬: 최신순, 이름순
- 이미지 상세 모달
- 다운로드 기능

### 6.2 필터 옵션

```javascript
filters = {
    project_id: null,        // 프로젝트 필터
    session_id: null,        // 세션 필터
    image_type: null,        // 'design' | 'model' | 'blueprint'
    date_from: null,         // 시작일
    date_to: null,           // 종료일
    sort_by: 'created_at',   // 정렬 기준
    sort_order: 'desc'       // 정렬 방향
}
```

---

## 7. 구현 Phase

### Phase 1: 2단 레이아웃 구현 ✅
- [x] dashboard.html 2단 레이아웃 재구성
- [x] 왼쪽 패널: 프로젝트/세션 선택 UI
- [x] 오른쪽 패널: 5개 탭 구조
- [x] CSS 스타일링 (design-system.css 확장)

### Phase 2: 워크플로우 정합성 ✅
- [x] 프로젝트 생성 모달
- [x] 세션 생성 폼 (필터, 크롤러 선택)
- [x] 세션 실행 버튼 → run-analysis 연동
- [x] 진행률 표시 (Polling)
- [x] 결과 탭별 데이터 바인딩

### Phase 3: 라이브러리 페이지 ✅
- [x] library.html 생성
- [x] 필터/정렬 UI
- [x] 이미지 그리드
- [x] 상세 모달
- [x] API 엔드포인트: GET /api/v1/library

### Phase 4: 이미지 생성 파이프라인
- [ ] Step 1: 프롬프트 생성 서비스 (Gemini)
- [ ] Step 2: 마스터 디자인 생성 (Seedream)
- [ ] Step 3: 모델 착장 생성 (IP-Adapter)
- [ ] ConsistencyPipeline 클래스 완성
- [ ] 세션 파이프라인에 통합

### Phase 4.5: 블루프린트 생성 파이프라인
- [ ] 스케치 생성 (Fashion Design Sketch)
- [ ] 레이아웃 도면 생성 (Flat Layout Drawing)
- [ ] 패턴 제도도 생성 (Technical Pattern Drawing)
- [ ] BlueprintService 클래스 업데이트
- [ ] 의상 이미지 탭에 3종 블루프린트 표시

### Phase 5: 테스트
- [ ] API 엔드포인트 테스트
- [ ] 워크플로우 E2E 테스트
- [ ] 이미지 생성 테스트 (API 키 필요)
- [ ] 블루프린트 3종 생성 테스트

---

## 8. 검토 기록

### 1차 검토 (논리성)
- 워크플로우: 프로젝트→세션→분석→결과 논리적 흐름 확인 ✓
- 탭 구조: 5개 탭이 분석 파이프라인 7단계 결과를 커버 ✓
- 이미지 일관성: 3단계 파이프라인으로 마스터 디자인 기반 생성 ✓

### 2차 검토 (사용성)
- 2단 레이아웃: 레퍼런스 3단에서 챗봇 제거, 보고서 확대 ✓
- 라이브러리: 생성 이미지 관리 페이지 추가 ✓
- 필터 기능: 프로젝트/세션/타입/날짜 필터 ✓

### 3차 검토 (기술적 타당성)
- Gemini API: 프롬프트 생성에 적합 (텍스트 생성 특화)
- Seedream/Nano Banana: 이미지 생성에 적합
- IP-Adapter: 참조 이미지 기반 일관성 유지 가능 ✓
- 기존 서비스 재사용: consistency_pipeline.py, image_generation_service.py ✓

### 4차 검토 (비용 효율성)
- Gemini 2.5 Flash: 프롬프트 생성 (저비용)
- Seedream: 의상 디자인 (중비용)
- Nano Banana: 모델 착장 (중비용)
- 총 이미지당: 의상 1장 + 착장 3-5장 = 4-6장

---

## 9. 완료 기준

- [x] 2단 레이아웃 정상 표시
- [x] 프로젝트/세션 CRUD 동작
- [ ] 세션 실행 → 파이프라인 완료
- [ ] 5개 탭에 결과 표시
- [x] 라이브러리 페이지 동작
- [ ] 이미지 생성 일관성 확인
- [ ] 블루프린트 3종 생성 (스케치/레이아웃/패턴)
