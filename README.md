# Design Support System

근거 기반 디자인 창작 지원 플랫폼

## 빠른 시작

### 1. 실행 방법
```bash
# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션
python manage.py migrate

# 관리자 계정 생성
python manage.py createsuperuser

# 개발 서버 실행
python manage.py runserver 0.0.0.0:8000
```

### 2. 접속 주소
- 웹 애플리케이션: http://localhost:8000
- 관리자 콘솔: http://localhost:8000/admin/

### 3. 서버 관리
```bash
# 개발 서버 실행
python manage.py runserver 0.0.0.0:8000

# 백그라운드 실행
nohup python manage.py runserver 0.0.0.0:8000 > server.log 2>&1 &

# 백그라운드 프로세스 중지
lsof -ti:8000 | xargs kill -9
```

### 4. 초기 설정
1. 관리자 콘솔 접속 (`/admin/`)
2. Model Catalog에서 AI Provider 및 모델 등록
3. Trend Knowledge에서 트렌드 출처 등록
4. `.env` 파일에 API 키 설정

## 제품 정의

편집툴이나 AI 이미지 생성기가 아닙니다. 이 시스템은 **근거 기반 디자인 발상 시스템**입니다.

- 어떤 디자인 목적이 있는가.
- 이 목적에 적합한 컨셉은 무엇인가.
- 그 컨셉은 어떤 트렌드와 실제 자료에 근거하는가.
- 레퍼런스를 어떤 디자인 문법으로 추상화할 수 있는가.
- 사용자 스케치를 어떻게 구체화할 수 있는가.
- 그 과정을 어떤 스펙 문서로 남길 것인가.

## 주요 기능

### 목적 → 브리프 → 컨셉
- 자연어 목적 입력으로 구조화된 디자인 브리프 생성
- 트렌드 근거 기반 컨셉 후보 생성 및 평가
- 컨셉별 점수, 근거, 리스크 표시

### 사용자 스케치 지원
- 러프/구조/스타일 스케치 업로드
- AI 스케치 의도 해석 (사용자 승인 필요)
- 원본 보존형 구체화 및 변형 생성

### 레퍼런스 검색과 추상화
- 키워드/이미지/스케치/문서 기반 검색
- 출처, 라이선스, 저작권 위험 관리
- 레퍼런스를 형태/구조/재질/상징/사용성 규칙으로 추상화

### 스펙 문서화
- 브리프, 근거, 결정, 레퍼런스, 추상화, 최종안을 포함한 스펙 문서
- 버전 관리와 승인 워크플로우

### 챗봇 협업 / 자동 진행
- 챗봇 협업 모드: 디자이너와 AI가 단계별로 컨셉을 좁혀가는 모드
- 자동 진행 모드: 목적과 제약만 입력하면 시스템이 끝까지 진행

### 도메인팩
- 산업디자인, 패션디자인, 시각디자인, 광고디자인 지원
- 도메인별 특화 분석, 시각화, 스펙 필드

### 관리자 시스템
- 기능별 AI 모델 정책 관리
- 트렌드 출처 등록 및 문서 수집 관리
- 테넌트/사용자/권한 관리
- 감사 로그

## 시스템 요구사항

- Python 3.13 이상
- PostgreSQL 15+
- 8GB 이상 RAM

## 설치

```bash
# 1. 저장소 클론
git clone [repository-url]
cd DesignSupport

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 설정
cp .env.template .env
# .env 파일에 API 키, DB 설정

# 5. 데이터베이스 마이그레이션
python manage.py migrate

# 6. 관리자 계정 생성
python manage.py createsuperuser

# 7. 실행
python manage.py runserver 0.0.0.0:8000
```

## 기술 스택

- **Backend**: Django 5.2 LTS, Python 3.13+
- **Frontend**: Vanilla HTML, Vanilla JS, Vanilla CSS
- **Database**: PostgreSQL 15+
- **AI**: 기능별 모델 정책 (관리자 페이지에서 관리)
- **Architecture**: Clean Architecture (Domain/Application/Infrastructure/Presentation)

## 제품 원칙

1. **편집보다 창작 지원이 우선** — 캔버스 편집, 레이어 조작, 세밀한 이미지 보정은 핵심 범위가 아님
2. **근거 없는 제안 금지** — 출처가 없으면 "아이디어 가설"로 표시
3. **레퍼런스 복제 금지** — 레퍼런스는 분석 대상, 모방 대상이 아님
4. **디자이너의 판단 보존** — 모든 결정을 Decision Log로 남김
5. **사용자 스케치 존중** — 원본 덮어쓰기 금지, AI 해석은 가설로 표시
6. **자동화는 옵션** — 챗봇 협업 또는 자동 진행 선택 가능
7. **도메인팩 기반 확장** — 공통 파이프라인 + 도메인별 템플릿
8. **관리 가능한 AI 시스템** — 모델명/API 키 하드코딩 금지

## 라이선스

MIT License
