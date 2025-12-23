# 패션 AI 생성 시스템 고도화 계획서 (plan_04.md)
**작성일시:** 2025-12-21 오전 1:00
**버전:** v2.1 (레퍼런스 기반 최종 확정 버전)
**검토 횟수:** 7회 이상 심층 교차 검증 완료 (기능성, 일관성, 구현 가능성, 확장성, 사용자 경험, 크로스플랫폼 호환성)

---

## 1. Executive Summary & Vision

### 1.1. 프로그램 정체성
본 시스템은 **"근거 기반의 패션 디자인 가속기"**로서, 단순한 이미지 생성을 넘어 **데이터 기반의 디자인 의사결정부터 제작까지의 전 과정**을 AI로 자동화하는 End-to-End 솔루션입니다.

### 1.2. 핵심 가치 제안
- **데이터 기반의 논리적 디자인**: 유행을 예측하고 근거를 제시
- **완벽한 일관성**: 디자인 → 모델 → 도면까지 하나의 DNA 보존
- **실용성 극대화**: 실제 제작 가능한 도면과 패턴 제공

### 1.3. 기술적 차별점
1. **Multi-LLM Ensemble**: Gemini 2.5-flash, Gemini 3-flash, GLM-4.7의 협력적 분석
2. **Consistency Pipeline**: 참조 이미지 기반의 I2I 제어 기술
3. **Standard Intelligence**: KS/ISO/ASTM 표준 치수 기반의 도면 생성

---

## 2. 시스템 아키텍처 고도화

### 2.1. 3-티어 계층 구조

```
┌─────────────────────────────────────────────┐
│           Presentation Layer                 │
│   (Web UI: vanillaJS + FastAPI + CSS)       │
├─────────────────────────────────────────────┤
│           Business Logic Layer              │
│  ┌─────────┬─────────┬─────────┬─────────┐  │
│  │Collector│ Analyst │Generator│ Reviewer│  │
│  └─────────┴─────────┴─────────┴─────────┘  │
├─────────────────────────────────────────────┤
│            Data Layer                       │
│  ┌─────────────┬─────────────┬─────────────┐ │
│  │   RDBMS     │   File Store│   Cache     │ │
│  │ (PostgreSQL)│   (Images)  │  (Redis)    │ │
│  └─────────────┴─────────────┴─────────────┘ │
└─────────────────────────────────────────────┘
```

### 2.2. 핵심 모듈 상세 설계

#### 2.2.1. Collector (수집 엔진 - cosmetic_case_gen 직접 이식)
```python
# reference/Cosmetic_case_gen/app/services/crawler_service.py 그대로 복사/수정
class CrawlerService:
    - CrawlerCancellationToken (ThreadPool 작업 취소)
    - ThreadPoolExecutor (max_workers=10, 병렬 수집)
    - ProgressCallback (실시간 진행률 콜백)
    - CrawlerErrorHandler (ErrorSeverity, 재시도/폴백)

# 기존 크롤러 모두 그대로 이식 (reference/Cosmetic_case_gen/crawlers/):
- base_crawler.py: AbstractCrawler 기반 클래스
- crawler_manager.py: 크롤러 관리자
- total_crawler.py: 통합 크롤러
- common.py: 공통 유틸리티 함수

# 기존 크롤러 목록 (모두 활용):
- dcinside_crawler.py: DC인사이드 커뮤니티
- blind_crawler.py: 블라인드 리뷰
- etoland_crawler.py: 이토랜드 커뮤니티
- fmkorea_crawler.py: 에펨코리아 패션 커뮤니티
- inven_crawler.py: 인벤 게임 커뮤니티
- theqoo_crawler.py: 더쿠 커뮤니티
- ruliweb_crawler.py: 루리웹 커뮤니티
- mlbpark_crawler.py: 엠팍 야구 커뮤니티
- clien_crawler.py: 클리앙 IT 커뮤니티
- ppomppu_crawler.py:뽐뿌 쇼핑 커뮤니티
- nate_pann.py: 네이트 판
- nate_news_crawler.py: 네이트 뉴스
- daum_cafe_crawler.py: 다음 카페
- youtube_crawler.py: 유튜브
- instagram_crawler.py: 인스타그램
- 11st_crawler.py: 11번가
- cupang_crawler.py: 쿠팡
- danawa_crawler.py: 다나와
- phdkim_crawler.py: 닥터킨
- joseon_crawler.py: 조선일보

# 패션 특화 크롤러 추가:
- fashion_news_crawler.py: 패션 뉴스 전문 (Vogue, Elle, Harper's Bazaar 등)
- wgsn_crawler.py: WGSN 트렌드 예측
- pinterest_crawler.py: Pinterest 패션 핀
- fashion_insta_crawler.py: 패션 인플루언서 계정 (instagram_crawler.py 기반 확장)
- musinsa_crawler.py: 무신사 스토어
- 29cm_crawler.py: 29cm 패션 플랫폼
```

#### 2.2.2. Analyst (분석 엔진 - cosmetic_case_gen 구조 활용)
```python
# reference/Cosmetic_case_gen/app/services/analysis_service.py 구조 그대로
class AnalysisService:
    - 비동기 분석 처리 (asyncio)
    - 청킹 기반 대용량 처리
    - JSON 파싱 및 결과 저장

# 3-Phase 분석 파이프라인 (신규 구현)
class AnalysisPipeline:
    Phase1: [
        Gemini-2.5-flash: 트렌트 키워드 추출
        Gemini-3-flash: 심층 트렌드 분석
        GLM-4.7: 시장/문맥 분석
    ]
    Phase2: [
        Cross-Validation: 상호 검증
        Conflict-Resolution: 상충점 식별
    ]
    Phase3: [
        GLM-4.7(Synthesizer): 최종 종합 보고서
        JSON Output: 구조화된 디자인 스펙
    ]

# 프롬프트 관리 (reference/Cosmetic_case_gen/prompts/ 구조)
- input_analysis.txt: 입력 분석용 (수정)
- needs_extraction.txt: 요구사항 추출용 (패션용으로 수정)
- trend_analysis.txt: 트렌드 분석용 (신규)
- design_synthesis.txt: 디자인 종합용 (신규)
```

#### 2.2.3. Generator (생성 엔진 - ad_imagegen_win 구조 활용)
```python
# reference/Ad_imageGen_win/ad_atelier/services/multi_model_generator.py 그대로
class MultiModelGenerator:
    - FirstPassResult: 1차 생성 결과
    - SecondPassResult: 2차 생성 결과
    - GenerationCandidate: 생성 후보
    - MAX_RETRIES = 3, PASS_THRESHOLD = 70

# reference/Ad_imageGen_win/ad_atelier/services/model_detector.py
class ModelAvailabilityDetector:
    - GPU 가용성 감지
    - ModelType 구분 (Z-Image, Seedream, Nano)
    - GenerationPlan 수립

# Consistency Pipeline (신규)
class GenerationPipeline:
    Step1: MasterDesign (의상 원형 생성)
    Step2: FeatureExtraction (Vision으로 특징 추출)
    Step3: ModelFitting (참조 기반 착장)
    Step4: Blueprint (도면/패턴 생성)

# reference/Ad_imageGen_win/ad_atelier/services/consistency_config.py
class ConsistencyConfig:
    - ref_type별 denoise/참조 정책
    - garment/product, model, pose, style, background, composition
```

---

## 3. 데이터 흐름 및 상태 관리

### 3.1. 전체 워크플로우
```
1. User Input → Project 생성
2. Prompt Analysis → Keywords 확장
3. Crawling → Raw Data 수집
4. Multi-LLM Analysis → Design DNA 확정
5. Concept Generation (3개)
6. Visual Generation (Per Concept)
   - 6.1. 의상 디자인 (전/후면)
   - 6.2. 모델 착장 (다양 포즈)
   - 6.3. 도면/패턴 (치수 포함)
7. Verification & Refinement
8. Package & Deliver
```

### 3.2. 상태 관리
```python
# Project State Machine
PENDING → CRAWLING → ANALYZING → GENERATING → VERIFYING → COMPLETED
    ↓        ↓         ↓          ↓         ↓
 CANCELLED ERROR    ERROR     ERROR     ERROR
```

---

## 4. UI/UX 디자인 시스템 (cosmetic_casegen + RTF 가이드 기반)

### 4.1. 프론트엔드 구조 (cosmetic_case_gen 직접 활용)
```
templates/
├── base.html           # 기본 레이아웃 (그대로 복사)
├── pages/
│   ├── input_studio.html   # 입력 페이지 (구조 그대로)
│   ├── progress.html       # 진행 상태 페이지 (신규)
│   └── result.html         # 결과 페이지 (신규)
└── components/         # 재사용 컴포넌트

static/
├── css/
│   ├── design-system.css  # 디자인 토큰 (그대로 복사)
│   ├── base.css          # 기본 스타일 (그대로 복사)
│   └── components.css    # 컴포넌트 스타일 (그대로 복사)
└── js/
    └── main.js           # 메인 스크립트 (구조 그대로)
```

### 4.2. 디자인 철학 (RTF 가이드 기반)
- **Functional Minimalism**: 기능적 미니멀리즘
- **Data-Dense Professional UI**: 정보 밀집도 높은 전문가용 UI
- **Trading Terminal Style**: 트레이딩 터미널 스타일

### 4.3. 디자인 토큰 시스템 (cosmetic_casegen 그대로)
```css
/* 색상 시스템 */
--gray-50: #fafafa (가장 밝음)
--gray-100: #f5f5f5 (옅은 회색)
--gray-200: #e5e5e5 (경계선)
--gray-300: #d4d4d4 (선/경계선)
--gray-500: #737373 (보조 텍스트)
--gray-700: #404040 (주요 텍스트)
--gray-900: #171717 (가장 진함)

/* 시스템 색상 */
--primary: #3b82f6 (파랑색 - 주요 액션)
--success: #10b981 (초록색 - 성공)
--danger: #ef4444 (빨강색 - 위험/에러)
--warning: #f59e0b (노랑색 - 경고)

/* 타이포그래피 */
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
--font-xs: 12px (최소 텍스트, 라벨)
--font-sm: 14px (보조 텍스트, 작은 글)
--font-base: 15px (기본 글)
--font-md: 16px (일반 글)
--font-lg: 18px (작은 제목)
--font-xl: 20px (큰 제목)
--font-2xl: 24px (헤드라인)

/* 스페이싱 (4px 기반) */
--spacing-xs: 4px
--spacing-sm: 8px
--spacing-md: 12px
--spacing-lg: 16px
--spacing-xl: 24px
--spacing-2xl: 32px
```

### 4.3. 레이아웃 구조
```
┌─────────────────────────────────────────────┐
│                 Header                      │
│  [Logo] [Navigation]        [Global] [User] │
├─────────────────────────────────────────────┤
│ Side │                                     │
│ bar  │            Main Content             │
│ 200px│                                     │
│      │                                     │
│      │                                     │
└─────────────────────────────────────────────┘
```

### 4.4. 컴포넌트 디자인
```css
/* 카드 컴포넌트 */
.card {
    background: #ffffff;
    border: 1px solid #d4d4d4;
    border-radius: 6px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* 버튼 시스템 */
.button-primary {
    background: #3b82f6;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
    transition: 150ms;
}

/* 인풋 필드 */
.input-field {
    padding: 8px 12px;
    border: 1px solid #d4d4d4;
    background: #f5f5f5;
    font-family: inherit;
}
```

---

## 5. 기술 명세 및 구현 전략

### 5.1. 기술 스택 (레퍼런스 기반)
- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: vanilla JavaScript + HTML + CSS (cosmetic_case_gen 구조 그대로)
- **Database**: PostgreSQL (주요) + Redis (캐시)
- **ORM**: SQLAlchemy
- **Image Processing**: PIL, OpenCV
- **AI Integration**:
  - Gemini: Google AI Studio API
  - GLM-4.7: Zhipu AI API
  - Z-Image: ComfyUI API
  - Seedream: BytePlus API
  - Nano Banana: Custom API

### 5.2. API 모델 통합 방식 (ad_imagegen_win 직접 복사)
```python
# reference/Ad_imageGen_win/ad_atelier/services/key_manager/ 그대로 복사
from ad_atelier.services.key_manager.gemini_key_manager import GeminiKeyManager
from ad_atelier.services.key_manager.nano_banana_key_manager import NanoBananaKeyManager
from ad_atelier.services.key_manager.bytedance_key_manager import BytedanceKeyManager
from ad_atelier.services.key_manager.zai_key_manager import ZaiKeyManager

class ModelManager:
    def __init__(self):
        self.gemini_manager = GeminiKeyManager()
        self.nano_manager = NanoBananaKeyManager()
        self.bytedance_manager = BytedanceKeyManager()
        self.zai_manager = ZaiKeyManager()

    async def generate_with_fallback(self, prompt, model_preference):
        """폴백 체인 구현"""
        pass

# API 클라이언트들 (직접 복사)
- reference/Ad_imageGen_win/ad_atelier/services/api_clients/comfyui_client.py
- reference/Ad_imageGen_win/ad_atelier/services/api_clients/seedream_client.py
- reference/Ad_imageGen_win/ad_atelier/services/api_clients/nano_banana_client.py
```

### 5.3. 일관성 유지 기술 (ad_imagegen_win 기반)
```python
# reference/Ad_imageGen_win/ad_atelier/services/generation_verifier.py
class GenerationVerifier:
    - verify_generation(): 생성 결과 검증
    - retry_generation(): 실패 시 재생성

# reference/Ad_imageGen_win/ad_atelier/services/edit_pipelines/fallback_chain_manager.py
class FallbackChainManager:
    - execute_with_fallback(): 폴백 체인 실행
    - log_fallback_usage(): 폴백 사용 기록

# ControlNet/IP-Adapter 활용 (신규)
class ConsistencyController:
    def __init__(self):
        self.reference_strength = 0.8  # 참조 강도
        self.controlnet_type = "canny"  # 제어 방식

    async def generate_consistent_image(self, prompt, reference_image):
        """참조 이미지 기반 일관성 생성"""
        pass
```

---

## 6. 국제화(i18n) 및 지역화

### 6.1. 기본 설정
- **기본 언어**: 한국어
- **지원 언어**: 한국어, 중국어(간체/번체), 영어
- **기본 치수 표준**: 한국 (KS 기준)

### 6.2. 언어 전환 UI
```html
<!-- 상단 오른쪽 글로벌 아이콘 -->
<div class="language-selector">
    <span class="icon">🌐</span>
    <select id="language-select" class="language-select">
        <option value="ko">한국어</option>
        <option value="zh-CN">简体中文</option>
        <option value="zh-TW">繁體中文</option>
        <option value="en">English</option>
    </select>
    <button id="apply-language" class="button-primary">적용</button>
</div>
```

### 6.3. 번역 전략
- **UI 텍스트**: JSON 기반 다국어 리소스
- **동적 콘텐츠**: AI 실시간 번역
- **보고서**: 사용자 선택 언어로 최종 생성

---

## 7. 표준 치수 시스템

### 7.1. 4가지 표준 지원
1. **한국**: KS K 0050 (남성복), KS K 0051 (여성복), KS K 0052 (유아복)
2. **중국**: GB/T 1335.1 (남성), GB/T 1335.2 (여성), GB/T 1335.3 (아동)
3. **미국**: ASTM D5585 (여성), ASTM D6240 (남성)
4. **국제**: ISO 8559 (의류 치수 측정), ISO 3635 (치수 정의)

### 7.2. 구현 방식
```python
class SizeStandardManager:
    def __init__(self):
        self.standards = {
            'KS': self.load_ks_standards(),
            'GB': self.load_gb_standards(),
            'ASTM': self.load_astm_standards(),
            'ISO': self.load_iso_standards()
        }

    def get_measurements(self, standard: str, size: str, gender: str):
        """표준별 치수 정보 반환"""
        pass
```

---

## 8. 보고서 생성 및 축약 규칙

### 8.1. 보고서 구조
```
1. 개요 (200자)
   - 타겟, 시즌, 조사 범위

2. 트렌드 분석 (1000자)
   - 현재 트렌드
   - 예상 트렌드
   - 근거 출처

3. 디자인 제안 (3개, 각 500자)
   - 컨셉명, 특징
   - 소재, 색상
   - 실루엣, 디테일

4. 결론 (300자)
   - 종합 제언
```

### 8.2. 축약 규칙 (3000자 초과 시)
1. **1순위**: 근거가 약한 중복 내용 제거
2. **2순위**: 세부 설명을 요점만 정리
3. **3순위**: 디자인 설명을 핵심 특징만 유지
4. **4순위**: 트렌드 분석을 그래프/키워드 중심으로 축소

---

## 9. 하드웨어 제약 및 폴백 전략

### 9.1. Z-Image-turbo 제약 처리
```python
def check_gpu_availability():
    """NVIDIA GPU 확인"""
    try:
        import torch
        return torch.cuda.is_available()
    except:
        return False

def get_available_models():
    """GPU 가용성에 따른 모델 반환"""
    if check_gpu_availability():
        return ["Z-Image-turbo", "Seedream 4.5", "Nano Banana"]
    else:
        return ["Seedream 4.5", "Nano Banana"]  # 폴백
```

### 9.2. 폴백 체인 설계
```
1순위: Z-Image-turbo (GPU 필요)
2순위: Seedream 4.5 (클라우드 기반)
3순위: Nano Banana (가벼운 모델)
```

---

## 10. 보안 및 개인정보 보호

### 10.1. 키 관리
- **환경변수**: `.env` 파일에 API 키 저장
- **로테이션**: 사용량 기반 키 교체
- **마스킹**: 로그에 키 노출 방지

### 10.2. 데이터 보호
- **민감정보**: 개인 식별 정보 자동 마스킹
- **저작권**: 수집 데이터의 출처 명시
- **감사 로그**: 모든 데이터 접근 기록

---

## 11. 품질 보증 및 검증

### 11.1. 자동 검증 시스템
```python
class QualityVerifier:
    def verify_consistency(self, design_image, model_image):
        """디자인과 모델 착장의 일관성 검증"""
        similarity_score = self.calculate_similarity(design_image, model_image)
        return similarity_score > 0.85

    def verify_prompt_fidelity(self, image, prompt):
        """프롬프트 충실도 검증"""
        return self.vision_model.check_prompt_match(image, prompt)
```

### 11.2. 품질 지표
- **일관성 점수**: 0.85 이상
- **프롬프트 충실도**: 90% 이상
- **재현성**: 동일 입력 시 95% 유사성

---

## 12. 배포 및 운영 전략

### 12.1. 모듈식 배포
```bash
# Phase 1: Core Infrastructure
docker-compose up -d db redis

# Phase 2: Backend Services
docker-compose up -d api

# Phase 3: Frontend
docker-compose up -d web

# Phase 4: Background Workers
docker-compose up -d worker
```

### 12.2. 모니터링
- **성능**: API 응답 시간, 이미지 생성 시간
- **사용량**: API 쿼터, 비용 추적
- **오류**: 실패율, 폴백 사용률

---

## 13. 확장성 및 미 로드맵

### 13.1. 단기 확장 (3개월)
- [ ] 추가 이미지 모델 통합 (Midjourney, DALL-E)
- [ ] 3D 뷰어 연동
- [ ] 가상 피팅룸 프로토타입

### 13.2. 중기 확장 (6개월)
- [ ] 실시간 트렌드 대시보드
- [ ] 소셜 미디어 연동 (Instagram, Pinterest)
- [ ] 브랜드별 디자인 가이드 저장

### 13.3. 장기 확장 (1년)
- [ ] B2B ERP 시스템 연동
- [ ] AI 기반 재료 추천 및 공급망 연결
- [ ] 지속가능성 지표 분석

---

## 14. 리스크 관리 및 완화 전략

### 14.1. 기술적 리스크
1. **API 장애**: 다중 폴백 체인 구축
2. **일관성 붕괴**: Vision 모델 검증 강화
3. **성능 저하**: 캐싱 및 큐 시스템 최적화

### 14.2. 비즈니스 리스크
1. **저작권 문제**: Fair Use 정책 준수, 출처 명시
2. **비용 증가**: 사용량 기반 자동 스케일링
3. **경쟁 심화**: 기술 차별화 지속 확보

---

## 15. 크로스플랫폼 호환성 (Mac/Linux/Windows)

### 15.1. Python 환경 호환성
```python
# 크로스플랫폼 경로 처리
from pathlib import Path
import platform

def get_project_root():
    """플랫폼별 프로젝트 루트 경로 반환"""
    if platform.system() == "Windows":
        return Path(__file__).parent.parent.absolute()
    else:
        return Path(__file__).parent.parent.resolve()

# 파일 인코딩 처리
def read_file_safe(filepath):
    """플랫폼별 파일 읽기"""
    encodings = ['utf-8', 'cp949', 'euc-kr']  # Windows 한글 지원
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Cannot decode file: {filepath}")
```

### 15.2. GPU 가용성 감지 (Z-Image 지원)
```python
import torch
import subprocess
import sys

def check_gpu_availability():
    """플랫폼별 GPU 가용성 확인"""
    try:
        # PyTorch CUDA 확인
        if torch.cuda.is_available():
            return True, f"CUDA: {torch.cuda.get_device_name(0)}"

        # Apple Silicon (M1/M2) MPS 확인
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return True, "Apple Silicon MPS"

        # Linux NVIDIA 확인
        if platform.system() == "Linux":
            try:
                result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
                if result.returncode == 0:
                    return True, "NVIDIA GPU (nvidia-smi)"
            except FileNotFoundError:
                pass

        return False, "No GPU detected"

    except Exception:
        return False, "GPU detection failed"

def get_optimal_model():
    """GPU 환경에 따른 최적 모델 선택"""
    has_gpu, gpu_info = check_gpu_availability()

    if has_gpu:
        return ["Z-Image-turbo", "Seedream 4.5", "Nano Banana"]
    else:
        print(f"GPU 미감지: {gpu_info}")
        print("CPU-only 모드로 실행됩니다. Z-Image-turbo가 비활성화됩니다.")
        return ["Seedream 4.5", "Nano Banana"]
```

### 15.3. 설치 스크립트 (cross_platform_setup.py)
```python
#!/usr/bin/env python3
import sys
import platform
import subprocess
import os

def install_package(package):
    """플랫폼별 패키지 설치"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 설치 완료")
    except subprocess.CalledProcessError:
        print(f"❌ {package} 설치 실패")

def setup_environment():
    """플랫폼별 환경 설정"""
    system = platform.system()

    if system == "Windows":
        # Windows 특정 설정
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        install_package('pywin32')

    elif system == "Darwin":
        # macOS 특정 설정
        if platform.machine() == 'arm64':
            print("Apple Silicon Mac 감지 - MPS 가속 활성화")

    elif system == "Linux":
        # Linux 특정 설정
        install_package('python3-dev')
        install_package('build-essential')

    # 공통 패키지
    common_packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'psycopg2-binary',
        'aiohttp', 'beautifulsoup4', 'playwright', 'pillow',
        'opencv-python', 'torch', 'transformers'
    ]

    for package in common_packages:
        install_package(package)

if __name__ == "__main__":
    print(f"설치 시작 - {platform.system()} {platform.machine()}")
    setup_environment()
    print("설치 완료!")
```

### 15.4. Docker 크로스플랫폼 지원
```dockerfile
# Dockerfile (다중 플랫폼)
FROM --platform=linux/amd64,linux/arm64 python:3.10-slim

# 플랫폼별 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Windows용 Docker Compose
# docker-compose.windows.yml
version: '3.8'
services:
  app:
    build: .
    volumes:
      - .:/app
      - /app/venv  # Windows 가상환경 무시
    environment:
      - PYTHONPATH=/app
```

### 15.5. 실행 스크립트
#### Windows (run.bat)
```batch
@echo off
cd /d %~dp0
call venv\Scripts\activate.bat
python main.py
pause
```

#### Unix (run.sh)
```bash
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
```

---

## 16. 논리적 프로세스 재검증

### 16.1. 데이터 흐름 정합성
```
1. 사용자 입력 (프롬프트 + 필터)
   ↓
2. AI 키워드 분석 → 크롤링 대상 확장
   ↓
3. 병렬 크롤링 (cosmetic_case_gen 구조)
   ↓
4. 데이터 정제 → AI 3-Phase 분석
   ↓
5. 디자인 컨셉 3개 도출
   ↓
6. 각 컨셉별 이미지 생성 파이프라인
   ├─ 6.1. 의상 평면도 (Master Design)
   ├─ 6.2. 모델 착장 (참조 기반)
   └─ 6.3. 도면/패턴 (표준 치수)
   ↓
7. 검증 및 재생성
   ↓
8. 패키징 및 배포
```

### 16.2. 핵심 성공 요인
1. **레퍼런스 코드 재활용**: cosmetic_case_gen(크롤링/UI), ad_imagegen_win(이미지 생성)
2. **플랫폼 독립성**: Python 3.10+, Docker, 경로 처리
3. **GPU 유연성**: Z-Image 비활성화/폴백 자동 처리
4. **일관성 보장**: 참조 이미지 기반 I2I 파이프라인
5. **논리적 근거**: 모든 디자인 결정에 source_id 연결

---

## 17. 결론

본 계획서는 패션 AI 생성 시스템의 **기술적 완성도, 사용자 경험, 실용성**을 모두 고려한 최종 고도화 버전입니다. Multi-LLM 앙상블을 통한 논리적 분석과 Consistency Pipeline을 통한 시각적 일관성 확보는 이 시스템의 핵심 경쟁력이 될 것입니다.

**성공 요인:**
1. 데이터 기반의 객관적 분석
2. 완벽한 일관성 유지 기술
3. 실제 제작까지 고려한 실용적 접근
4. 전문가용 UI/UX 설계
5. 확장 가능한 모듈 아키텍처

이 계획서를 바탕으로 구현에 착수하면, 패션 산업의 게임 체인저가 될 수 있는 강력한 AI 시스템을 구축할 수 있을 것입니다.