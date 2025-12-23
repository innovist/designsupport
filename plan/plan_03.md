# 차세대 패션 이미지 생성 시스템 상세 계획서 (plan_03.md)
**작성일시:** 2025-12-20
**버전:** v1.0 (Final Planning Phase)
**검토:** 3회 이상 논리적 교차 검증 완료 (기능성, 일관성, 구현 가능성)

---

## 1. 개요 및 핵심 목표 (Executive Summary)
본 프로젝트는 단순한 이미지 생성을 넘어, **"트렌드 분석 → 디자인 도출 → 가상 시착 → 설계/패턴 제작"**으로 이어지는 패션 산업의 전 공정을 AI로 자동화하는 **End-to-End 통합 솔루션**이다.

*   **Core Value:** 데이터에 기반한 논리적 디자인 제안과 생성된 디자인의 시각적 일관성(Consistency) 유지.
*   **Key Tech:** Multi-LLM Ensemble (Gemini + GLM), Multi-GenModel (Z-Image/Seedream/Nano), Crawler Orchestration.

---

## 2. 논리적 요구사항 심층 분석 (Deep Dive Analysis)

### 2.1. 인텔리전스 계층 (Analysis Engine)
*   **다중 모델 앙상블 (Ensemble Logic):** 단일 모델의 편향을 방지하기 위해 3단계 분석 구조를 채택한다.
    *   **Phase A (개별 분석):** `Gemini-2.5-flash`와 `Gemini-3-flash`, `GLM-4.7`이 수집된 Raw Data(텍스트, 메타데이터)를 독립적으로 분석한다. (속도 및 다각적 시각 확보)
    *   **Phase B (상호 검증):** 각 모델의 분석 결과(키워드, 트렌드 예측)를 비교하여 공통점과 차이점을 식별한다.
    *   **Phase C (최종 종합 - GLM-4.7):** `GLM-4.7`이 "Chief Designer" 역할을 수행. 상충되는 의견을 조율하고, 최종적인 **"Design DNA(디자인 설계서)"**를 JSON 형태로 확정한다.
*   **논리적 근거 확보:** 모든 트렌드 제안에는 `source_id`(크롤링 원본 링크)가 매핑되어야 하며, 사용자는 "왜 이 디자인이 유행할 것인가?"에 대한 근거를 확인할 수 있어야 한다.

### 2.2. 크리에이티브 계층 (Generation Engine)
*   **모델 선택권 (User Choice):** 사용자는 결과물의 스타일(실사형, 일러스트형, 예술적 등)에 따라 생성 엔진을 선택한다.
    *   `Z-Image-turbo`: 빠른 속도, 명확한 구조적 표현에 강점 (도면/기본 디자인 추천).
    *   `Seedream 4.5`: 높은 예술성과 창의적 변형에 강점 (화보/컨셉 아트 추천).
    *   `Nano Banana`: 극실사주의 및 텍스처 표현에 강점 (제품 상세/소재감 추천).
*   **일관성 파이프라인 (Consistency Pipeline) - **가장 중요한 난제 해결책****
    *   이미지 생성은 독립적 사건이 아닌 **연쇄적 흐름(Chain)**이어야 한다.
    *   **Step 1 (Master Design):** 의상 평면도(Flat Lay) 또는 마네킹 샷을 먼저 생성하여 "의상의 원형"을 고정한다.
    *   **Step 2 (Feature Extraction):** 생성된 의상의 특징(Color Code, Pattern, Shape)을 Vision Model로 역추출하여 고정 프롬프트화한다.
    *   **Step 3 (Virtual Try-On):** 모델 착장 이미지 생성 시, Step 1의 이미지를 `ControlNet(Reference/Canny)` 또는 `IP-Adapter`의 입력으로 사용하여 의상 형태를 강제한다.

### 2.3. 테크니컬 계층 (Blueprint & Dimensions)
*   **치수 표준화:** 도면은 단순 그림이 아니라 "제작 가능성"을 암시해야 한다.
    *   KS(한국), ISO(국제), ASTM(미국) 등의 표준 치수 데이터를 DB에 내장.
    *   생성된 도면 이미지 위에 AI(OCR/Vision)가 주요 측정 지점(어깨 너비, 총장 등)을 식별하고, 예상 치수를 오버레이(Overlay) 하거나 테이블로 제공한다.

---

## 3. 시스템 아키텍처 및 워크플로우 (System Architecture)

### 3.1. 모듈 구성
1.  **Collector (수집기):**
    *   Target: 패션 뉴스, SNS, 쇼핑몰 (robots.txt 준수).
    *   Tech: Python, Playwright/Selenium, BeautifulSoup.
    *   Logic: 키워드 확장(Prompt -> Related Keywords) -> 분산 수집 -> 정제(De-duplication).
2.  **Analyst (분석기):**
    *   Models: Gemini-2.5-flash / Gemini-3-flash / GLM-4.7.
    *   Output: `TrendReport` (Markdown) & `DesignSpec` (JSON - 소재, 핏, 색상코드, 디테일).
3.  **Generator (생성기):**
    *   Prompt Engineering: `DesignSpec` JSON을 각 이미지 모델(Z-Image 등)에 최적화된 프롬프트 포맷(Tag형 vs 서술형)으로 변환.
    *   Image Pipeline: Design -> Model Fitting -> Variation -> Blueprint.
4.  **Reviewer (검증기):**
    *   Logic: 생성된 이미지가 프롬프트의 핵심 요소(예: "빨간색 벨벳 소재")를 포함하는지 Vision Model로 재검증. 불일치 시 자동 재생성(Retry).

### 3.2. 데이터 흐름도 (Data Flow)
1.  **User Input:** 프롬프트, 타겟(성별/나이/시즌/지역).
2.  **Collection:** 크롤러 동작 -> Raw Data 저장.
3.  **Insight:** Gemini 분석 -> GLM 종합 -> **[Design Report]** 생성.
4.  **Concept creation:** GLM이 3가지 컨셉 도출 (예: "Neo-Retro", "Eco-Minimal", "Tech-Wear").
5.  **Visual Gen (Loop per concept):**
    *   Gen 1: 의상 단독 디자인 (Front/Back) 생성.
    *   Gen 2: (Gen 1 참조) 모델 착장 화보 생성.
    *   Gen 3: (Gen 1 참조 + 표준치수 데이터) 도면/패턴도 생성.
6.  **Final Output:** 웹 리포트 뷰어 (텍스트 + 이미지 갤러리 + 다운로드).

---

## 4. 상세 기능 명세 (Functional Specifications)

### 4.1. 트렌드 분석 및 리포트
*   **기능:** 사용자의 모호한 요청(예: "내년 봄 20대 여성 유행")을 구체적 디자인 언어로 변환.
*   **출력:** 트렌드 키워드, 예상 유행 컬러(Pantone 코드), 주요 소재(Fabric), 실루엣(Fit).

### 4.2. 프롬프트 엔지니어링 (Auto-Prompting)
*   보고서 내용을 바탕으로 "초상세 프롬프트" 자동 생성.
*   **구조:** `(Subject: 의상 상세) + (Style: 예술적 화풍) + (Environment: 조명/배경) + (Tech: 렌더링 엔진 설정)`
*   모델별 최적화: Z-Image(단어 위주), Seedream(문장 위주) 등 구분 적용.

### 4.3. 이미지 생성 및 제어
*   사용자 인터페이스에서 `모델 변경(Z-Image <-> Nano Banana)` 즉시 지원.
*   모든 생성물은 `Project_ID`와 `Design_ID`로 묶여 관리됨.
*   **도면 생성 특화:** 배경 제거(White Background), 라인 드로잉(Line Art) 스타일 적용, 치수선(Dimension Lines) 포함 프롬프트 주입.

---

## 5. 구현 로드맵 (Implementation Plan)

### Phase 1: 기반 구축 (Infrastructure)
*   프로젝트 구조 세팅 (FastAPI, React/VanillaJS).
*   DB 설계 (User, Project, TrendData, DesignConcept, ImageResult).
*   AI API 연동 모듈 (Key Management, Rate Limiting).

### Phase 2: 수집 및 분석 (Intelligence)
*   크롤러 엔진 구현 (비동기 처리).
*   Gemini/GLM 분석 파이프라인 및 JSON 출력 스키마 정의.
*   트렌드 보고서 UI 구현.

### Phase 3: 생성 엔진 고도화 (Creative)
*   이미지 생성 모델 API 연동 (Z-Image, Seedream, Nano).
*   프롬프트 번역/최적화 모듈 (Korean -> English -> Optimized Prompt).
*   **일관성 유지 로직(I2I, ControlNet 등 API 파라미터 튜닝) 구현.**

### Phase 4: 결과물 패키징 (Delivery)
*   도면 치수 매핑 로직.
*   최종 결과물(보고서+이미지+도면) PDF/Zip 다운로드.
*   전체 통합 테스트 및 UI 폴리싱.

---

## 6. 검토 의견 요약 (Review Summary)
*   **논리성:** 크롤링된 데이터를 기반으로 하므로 "환각(Hallucination)"이 아닌 "근거 있는 디자인"이 생성됨.
*   **완결성:** 디자인에서 끝나는 것이 아니라, 실제 제작을 위한 도면과 모델 핏까지 제공하여 실무 활용도 극대화.
*   **확장성:** 향후 쇼핑몰 연동이나 가상 피팅룸(Virtual Fitting Room) 서비스로 확장 용이한 구조.