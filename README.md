# Fashion AI Generation System

패션 트렌드 분석 및 AI 이미지 생성 통합 플랫폼

## 빠른 시작

### 1. 실행 방법
```bash
# 메인 실행 (권장)
python main.py

# 또는 개발 모드 (자동 리로드)
uvicorn main:app --reload --host 0.0.0.0 --port 14000
```

### 2. 접속 주소
- 웹 애플리케이션: http://localhost:14000
- API 문서: http://localhost:14000/docs
- API 상태 확인: http://localhost:14000/health

### 3. 서버 관리
```bash
# 서버 실행 (포트 14000)
python main.py

# 개발 모드 (자동 리로드)
uvicorn main:app --reload --host 0.0.0.0 --port 14000

# 서버 중지
# 터미널에서 Ctrl+C 누르기

# 백그라운드 실행
nohup python main.py > server.log 2>&1 &

# 백그라운드 프로세스 중지
lsof -ti:14000 | xargs kill -9
```

### 4. 초기 설정
1. 웹 접속 후 우측 상단 ⚙️ 설정 메뉴 클릭
2. API 키 탭에서 필요한 API 키 입력:
   - **Gemini API Key** (필수): https://makersuite.google.com/app/apikey
   - **GLM API Key** (필수): https://open.bigmodel.cn/
   - Z-Image, Seedream, Nano Banana (선택)
3. 저장 후 '연결 테스트'로 확인

## 주요 기능

### 🔍 트렌드 분석
- 키워드 기반 패션 트렌드 분석
- 여러 커뮤니티 데이터 수집 (FM코리아, 블라인드 등)
- AI 기반 트렌드 인사이트 생성

### 🎨 이미지 생성
- 텍스트 설명으로 패션 디자인 생성
- 참조 이미지 기반 디자인 제안
- 다양한 스타일과 품질 옵션
- 일관성 있는 시리즈 생성 (마스터 → 모델 → 도면)

### 📐 패턴 생성
- 기술 도면 자동 생성
- 치수표 (KS, GB, ASTM, ISO)
- 제작 지시문 포함

### 🕷️ 데이터 수집
- 다양한 소스에서 패션 데이터 수집
- 실시간 트렌드 모니터링
- 필터링 및 분석 기능

## 시스템 요구사항

- Python 3.8 이상
- 8GB 이상 RAM
- GPU 지원 (권장: NVIDIA CUDA 또는 Apple Silicon)

## 설치

```bash
# 1. 저장소 클론
git clone [repository-url]
cd Fashion_Image_gen

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경 설정
cp .env.template .env
# .env 파일에 API 키 설정

# 4. 실행
python main.py
```

### SearXNG 설치 (데이터 수집용)

SearXNG를 통한 웹 검색 기능을 사용하려면 추가 설정이 필요합니다:

```bash
# SearXNG 의존성 모듈 설치
pip install --user msgspec

# 또는 conda 환경 사용 시
conda install -c conda-forge msgspec
```

SearXNG는 `storage/searxng-src` 디렉토리에 포함되어 있으며, 설정 페이지에서 API URL을 `http://localhost:8913`으로 설정하면 자동으로 연동됩니다.

## API 문서

FastAPI 자동 문서: http://localhost:14000/docs

주요 엔드포인트:
- `/api/v1/settings` - 설정 관리
- `/api/v1/analysis` - 트렌드 분석
- `/api/v1/generation` - 이미지 생성
- `/api/v1/crawler` - 데이터 수집
- `/api/v1/blueprint` - 패턴 생성
- `/api/v1/projects` - 프로젝트 관리
- `/api/v1/sessions` - 세션/파이프라인 관리

## 보안

- 모든 API 키는 AES-256 암호화로 저장
- 로컬 저장소에만 보관
- 설정 파일 내보내기/가져오기 지원

## 기술 스택

- **Backend**: FastAPI, Python 3.8+
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **AI**: Google Gemini, Zhipu GLM, Custom Image Models
- **Database**: SQLite (기본), PostgreSQL (옵션)
- **Caching**: Redis (옵션)

## AI 모델 설정

### 사용 가능한 모델

**텍스트 생성 (Gemini)**
- `gemini-2.5-flash` - 기본값, 빠르고 효율적
- `gemini-2.5-flash-lite` - 경량 버전
- `gemini-2.5-pro` - 고품질 분석용

**텍스트 생성 폴백 (GLM)**
- `glm-4.7` - 기본값
- `glm-4-flash` - 빠른 응답용

**이미지 생성**
- `seedream-3.0` - Bytedance Seedream
- `nano-banana-v1` - Nano Banana

### 모델 설정 방법
1. 웹 UI의 설정 페이지에서 모델 선택
2. 설정 저장 후 자동 적용

### 개발자 참고사항
- 모델명은 절대 하드코딩하지 않음
- `app/core/settings_storage.py`의 함수 사용:
  - `get_gemini_model()` - Gemini 모델명 반환
  - `get_glm_model()` - GLM 모델명 반환
  - `get_fallback_model()` - 폴백 모델명 반환

## 라이선스

MIT License

## 지원

문의: [이메일 주소]