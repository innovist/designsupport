# Plan 07: Fashion AI Generation System 전면 재설계

**작성일**: 2025-12-21 16:00
**기준**: Cosmetic_case_gen 프로젝트 구조 완전 복제 후 패션 특화 수정

---

## 🚨 현재 문제점 (사용자 피드백)

1. **키워드 필수 오류**: 트렌드 분석이 키워드 필수로 설계됨 → 성별/나이대/계절 선택으로 변경 필요
2. **크롤러 선택 UI 부재**: 어떤 크롤러를 사용할지 선택하는 UI가 없음
3. **프로젝트 설정 부재**: Cosmetic_case_gen처럼 프로젝트/세션 기반 관리 필요
4. **시각화 구조 오류**: Jinja2 템플릿 기반이 아닌 단일 페이지 구조로 잘못 구현
5. **파이프라인 구조 부재**: 10단계 자동 파이프라인 없음

---

## ✅ 목표 아키텍처 (Cosmetic_case_gen 기반)

### 1. 템플릿 구조 (templates/pages/)
```
templates/
├── base.html                 # 공통 레이아웃
└── pages/
    ├── dashboard.html        # 대시보드 (통계, 최근 세션)
    ├── new_session.html      # 새 세션 생성 (크롤러 선택 + 패션 필터)
    ├── session_detail.html   # 세션 상세 (진행률, 결과)
    ├── history.html          # 세션 히스토리
    ├── projects.html         # 프로젝트 목록
    ├── project_detail.html   # 프로젝트 상세
    ├── ideas.html            # 디자인 아이디어 목록
    ├── settings.html         # 설정 (API 키 등)
    └── chatbot.html          # AI 챗봇 대화
```

### 2. 패션 특화 세션 필터 (new_session.html)
Cosmetic_case_gen은 "화장품 용기/케이스"에 집중하지만, 우리는 **패션 트렌드 분석**이므로:

```
[패션 분석 조건] (모두 선택사항)
├── 성별: 남성 / 여성 / 유니섹스 / 전체
├── 나이대: 10대 / 20대 / 30대 / 40대 / 50대+ / 전체
├── 계절: 봄/여름 / 가을/겨울 / 전체
├── 카테고리: 상의 / 하의 / 원피스 / 아우터 / 액세서리 / 전체
└── 사용자 키워드: (선택사항) 예: 미니멀, 오버핏, 레트로
```

### 3. 크롤러 카테고리 (패션 특화)
```python
CRAWLER_CATEGORIES = {
    "fashion_community": {
        "name": "패션 커뮤니티",
        "crawlers": ["무신사", "W컨셉", "29CM", "에이블리"]
    },
    "community": {
        "name": "일반 커뮤니티",
        "crawlers": ["더쿠", "FM코리아", "인스티즈", "블라인드"]
    },
    "portal": {
        "name": "포털/블로그",
        "crawlers": ["네이버블로그", "네이버카페", "다음카페"]
    },
    "media": {
        "name": "미디어",
        "crawlers": ["인스타그램", "유튜브", "핀터레스트"]
    },
    "news": {
        "name": "패션 뉴스",
        "crawlers": ["패션N", "WGSN", "보그코리아"]
    }
}
```

### 4. 파이프라인 (7단계)
```
1. 입력 분석 (멀티모달: 텍스트/파일/URL/이미지)
2. 키워드 추출 (AI 기반 + 사용자 정의)
3. 데이터 수집 (선택된 크롤러 실행)
4. 트렌드 분석 (패션 니즈/불만/요구사항 추출)
5. 디자인 아이디어 생성 (Gemini 기반)
6. 이미지 생성 (선택: Z-Image/Seedream/NanoBanana)
7. 블루프린트/패턴 생성 (선택)
```

---

## 📁 파일 구조 변경

### 기존 static/ → templates/ 전환
```
# 기존 (삭제 예정)
static/
├── index.html          # 단일 페이지 (문제)
├── css/style.css
└── js/main.js, api.js, ui.js

# 신규 (Jinja2 템플릿)
templates/
├── base.html
└── pages/
    ├── dashboard.html
    ├── new_session.html
    ├── session_detail.html
    ├── history.html
    └── settings.html
static/
├── css/
│   ├── variables.css   # CSS 변수
│   └── main.css        # 공통 스타일
└── js/
    ├── api.js          # API 클라이언트
    └── common.js       # 공통 유틸리티
```

### 백엔드 구조 (Cosmetic_case_gen 동일)
```
app/
├── api/v1/endpoints/
│   ├── sessions.py     # 세션 CRUD + 파이프라인
│   ├── projects.py     # 프로젝트 CRUD
│   ├── crawlers.py     # 크롤러 실행/상태
│   ├── analysis.py     # 트렌드 분석
│   ├── ideas.py        # 아이디어 생성
│   └── settings.py     # 설정 관리
├── services/
│   ├── pipeline_orchestrator.py  # 7단계 파이프라인
│   ├── crawler_service.py
│   ├── analysis_service.py
│   ├── idea_service.py
│   └── image_generation_service.py
├── models/
│   ├── analysis_session.py
│   ├── project.py
│   ├── crawled_data.py
│   ├── fashion_trend.py    # 패션 특화 모델
│   └── design_idea.py
├── repositories/
│   └── (Repository 패턴)
└── crawler_config.py       # 크롤러 카테고리 정의
```

---

## 🔄 마이그레이션 전략 (레퍼런스 복사 방식)

### ⚠️ 핵심 원칙: 레퍼런스 파일 복사 → 도메인만 변경
- CSS/HTML 구조는 Cosmetic_case_gen에서 **그대로 복사**
- "화장품 용기" → "패션 트렌드" 텍스트만 변경
- 검증된 UI/UX 재사용으로 오류 최소화

### 복사 대상 및 변경 범위
| 구분 | 복사 대상 | 변경 내용 |
|-----|----------|----------|
| **CSS** | design-system.css | 그대로 사용 (변경 없음) |
| **템플릿** | base.html, dashboard.html 등 | 텍스트만 변경 (화장품→패션) |
| **파이프라인** | pipeline_orchestrator.py | 구조 복사 → 패션 분석 로직으로 변경 |
| **API 라우터** | sessions.py, projects.py 등 | 구조 복사 → 기존 서비스 연결 |
| **백엔드 서비스** | 기존 Fashion_Image_gen 유지 | 파이프라인에 연결만 추가 |

### Phase 0: 기존 코드 백업 (필수)
- static/ → static_legacy/
- 기존 라우터/서비스 백업

### Phase 1: 레퍼런스 파일 복사 및 텍스트 변경
**복사할 파일 목록:**
```
# CSS (그대로 복사)
reference/Cosmetic_case_gen/static/css/design-system.css → static/css/design-system.css

# 템플릿 (복사 후 텍스트 변경)
reference/Cosmetic_case_gen/templates/base.html → templates/base.html
reference/Cosmetic_case_gen/templates/pages/dashboard.html → templates/pages/dashboard.html
reference/Cosmetic_case_gen/templates/pages/new_session.html → templates/pages/new_session.html
reference/Cosmetic_case_gen/templates/pages/session_detail.html → templates/pages/session_detail.html
reference/Cosmetic_case_gen/templates/pages/history.html → templates/pages/history.html
reference/Cosmetic_case_gen/templates/pages/settings.html → templates/pages/settings.html
```

**텍스트 변경 예시:**
| 원본 (화장품) | 변경 (패션) |
|--------------|------------|
| 화장품 용기 아이디어 발굴 시스템 | 패션 트렌드 AI 생성 시스템 |
| 화장품 용기/케이스 | 패션 디자인 |
| AI 아이디어 발굴 | 패션 AI 생성 |

### Phase 2: 패션 특화 세션 UI
- new_session.html에 패션 필터 추가 (성별/나이대/계절/카테고리)
- 크롤러 카테고리 선택 UI
- 사용자 키워드 입력 (선택사항)

### Phase 3: 크롤러 설정
- crawler_config.py 작성 (패션 크롤러 카테고리)
- 기존 크롤러 연동 (무신사, 핀터레스트, WGSN 등)

### Phase 4: 파이프라인 구현
- pipeline_orchestrator.py 작성 (7단계)
- 세션 기반 파이프라인 실행

### Phase 5: 분석/아이디어 생성
- 트렌드 분석 서비스 연동
- 디자인 아이디어 생성 로직

### Phase 6: 이미지 생성 통합
- 기존 이미지 생성 서비스 연동
- 세션 결과에 이미지 저장

### Phase 7: 테스트 및 검증
- 전체 파이프라인 테스트
- UI/UX 검증

---

## 📌 핵심 변경사항 요약

| 항목 | 기존 (잘못됨) | 신규 (Cosmetic_case_gen 기반) |
|------|--------------|------------------------------|
| UI 구조 | 단일 index.html | Jinja2 템플릿 (7개 페이지) |
| 트렌드 필터 | 키워드 필수 | 성별/나이대/계절/카테고리 (선택) |
| 크롤러 선택 | 없음 | 카테고리별 체크박스 UI |
| 세션 관리 | 없음 | 프로젝트/세션 기반 |
| 파이프라인 | 수동 API 호출 | 7단계 자동 파이프라인 |
| 진행률 표시 | 없음 | 실시간 진행률 + 상태 표시 |

---

## ⚠️ 주의사항

1. **Cosmetic_case_gen 구조 100% 복제**: 단순 참고가 아니라 베이스로 사용
2. **패션 특화 수정만**: 화장품 용기 → 패션 트렌드로 도메인만 변경
3. **기존 이미지 생성 서비스 유지**: Z-Image, Seedream, NanoBanana 연동
4. **i18n 유지**: 기존 다국어 지원 구조 유지

---

**다음 단계**: todo_07.md 체크리스트 작성 후 Phase 0부터 순차 진행
