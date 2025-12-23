# Fashion AI Generator - Architecture Guide
**Version:** 1.0.0
**Last Updated:** 2025-12-21

---

## 1. 시스템 개요

Fashion AI Generator는 AI 기반 패션 트렌드 분석 및 이미지 생성을 위한 통합 플랫폼입니다. 마이크로서비스 아키텍처 기반으로 구축되어 확장성과 안정성을 확보했습니다.

### 1.1. 핵심 기능
- **데이터 수집**: 다양한 패션 소스에서 실시간 데이터 수집
- **트렌드 분석**: AI 기반 패션 트렌드 예측 및 인사이트 도출
- **디자인 생성**: 텍스트/이미지 기반 패션 디자인 생성
- **패턴 생성**: 디자인을 실제 제작용 패턴으로 변환
- **다국어 지원**: 4개 국어(한국어, 영어, 중국어 간체/번체) 지원

### 1.2. 기술 스택
- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: Vanilla JavaScript + CSS3
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Container**: Docker + Docker Compose
- **Monitoring**: Prometheus + Grafana
- **Logging**: Elasticsearch + Kibana
- **Proxy**: Nginx

---

## 2. 아키텍처 원칙

### 2.1. 설계 원칙

#### 2.1.1. 마이크로서비스 아키텍처
- 각 서비스는 독립적으로 배포 및 확장 가능
- API Gateway를 통한 통신 관리
- 서비스 디스커버리 및 로드 밸런싱

#### 2.1.2. 이벤트 기반 아키텍처
- 비동기 메시지 큐를 통한 느슨한 결합
- 이벤트 소싱 패턴 적용
- CQRS (Command Query Responsibility Segregation)

#### 2.1.3. 도메인 기반 설계
- 명확한 경계 컨텍스트 정의
- 비즈니스 로직과 인프라 분리
- 포트와 어댑터 패턴 적용

### 2.2. 품질 속성

| 속성 | 목표 | 구현 전략 |
|------|------|-----------|
| 확장성 | 1000+ 동시 사용자 | 수평적 확장, 로드 밸런싱 |
| 가용성 | 99.5% | 재해 복구, 헬스 체크 |
| 성능 | 응답시간 < 3초 | 캐싱, 최적화 |
| 보안 | 데이터 보호 | 암호화, 인증/인가 |

---

## 3. 시스템 구조

### 3.1. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Web Browser │  │ Mobile App  │  │ Third Party │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (Nginx)                     │
│  - SSL Termination                                         │
│  - Rate Limiting                                          │
│  - Load Balancing                                         │
│  - Static File Serving                                    │
└─────────────────────────────────────────────────────────────┘
                               │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Web Service │    │ API Service │    │ Admin Panel │
│   (UI)      │    │   (Core)    │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
        │                     │
        ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Crawler   │ │  Analysis   │ │ Generation  │           │
│  │   Service   │ │   Service   │ │   Service   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Blueprint │ │   User Mgmt │ │  Notific.   │           │
│  │   Service   │ │   Service   │ │   Service   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ PostgreSQL  │ │    Redis    │ │ File Storage│           │
│  │(Primary DB) │ │   (Cache)   │ │   (Images)  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               External Services                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  AI Models  │ │  Social API │ │ Payment API │           │
│  │ (Gemini,..) │ │ (Instagram) │ │   (Stripe)  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### 3.2. 서비스 상세 설계

#### 3.2.1. Web Service (UI)
- 역할: 정적 파일 서빙, SSR (Server-Side Rendering)
- 기술: FastAPI + Jinja2
- 특징:
  - CDN 통합
  - 압축 및 캐싱
  - i18n 지원

#### 3.2.2. API Service (Core)
- 역할: 비즈니스 로직 처리, API 엔드포인트 제공
- 기술: FastAPI + Pydantic
- 특징:
  - 자동 API 문서화 (Swagger)
  - 요청/응답 검증
  - 인증/인가 미들웨어

#### 3.2.3. Crawler Service
- 역할: 패션 데이터 수집
- 기술: Playwright + BeautifulSoup
- 특징:
  - 다중 소스 지원
  - 실시간 크롤링
  - 중복 제거

#### 3.2.4. Analysis Service
- 역할: 트렌드 분석 및 인사이트 도출
- 기술: Gemini 2.5 + GLM-4.7
- 특징:
  - 병렬 처리
  - 결과 캐싱
  - 실시간 분석

#### 3.2.5. Generation Service
- 역할: 이미지 및 패턴 생성
- 기술: Z-Image, Seedream, Nano Banana
- 특징:
  - 다중 모델 지원
  - 큐 기반 처리
  - 진행률 추적

---

## 4. 데이터베이스 설계

### 4.1. 데이터베이스 스키마

```sql
-- Users 테이블
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects 테이블
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CrawlJobs 테이블
CREATE TABLE crawl_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    sources JSONB NOT NULL,
    keywords TEXT[],
    status VARCHAR(20) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RawData 테이블
CREATE TABLE raw_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES crawl_jobs(id),
    source VARCHAR(50) NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TrendAnalysis 테이블
CREATE TABLE trend_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    keywords TEXT[],
    time_range VARCHAR(10),
    analysis_result JSONB,
    trend_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ImageAssets 테이블
CREATE TABLE image_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    generation_id VARCHAR(255),
    image_url TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PatternDrafts 테이블
CREATE TABLE pattern_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    garment_type VARCHAR(50),
    size_system VARCHAR(10),
    size VARCHAR(10),
    pattern_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2. 인덱스 전략

```sql
-- 검색 최적화 인덱스
CREATE INDEX idx_raw_data_source ON raw_data(source);
CREATE INDEX idx_raw_data_created_at ON raw_data(created_at);
CREATE INDEX idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX idx_trend_analyses_keywords ON trend_analyses USING GIN(keywords);

--全文検索 인덱스 (PostgreSQL)
CREATE INDEX idx_raw_data_content_gin ON raw_data USING GIN(to_tsvector('korean', content));
```

### 4.3. 파티셔닝

```sql
-- 시계열 데이터 파티셔닝
CREATE TABLE raw_data_partitioned (
    LIKE raw_data INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- 월별 파티션 생성
CREATE TABLE raw_data_2025_01 PARTITION OF raw_data_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

---

## 5. API 설계

### 5.1. API 아키텍처 패턴

#### 5.1.1. RESTful API
- 자원 기반 URI 설계
- HTTP 메서드 적절한 사용
- 일관된 응답 형식

#### 5.1.2. GraphQL (향후 지원)
- 유연한 데이터 조회
- 단일 엔드포인트
- 타입 시스템

### 5.2. API 버전 관리
- URL 경로 기반 버전: `/api/v1/`
- 하위 호환성 보장
- 디프리케이션 정책

### 5.3. 보안
- JWT 기반 인증
- OAuth 2.0 지원
- Rate Limiting
- HTTPS 강제

---

## 6. 메시징 시스템

### 6.1. 비동기 처리

```python
# Celery 기반 태스크 큐
from celery import Celery

app = Celery('fashion_ai')

@app.task
def process_image_generation(generation_request):
    # 이미지 생성 비동기 처리
    pass

@app.task
def crawl_fashion_data(sources, keywords):
    # 데이터 크롤링 비동기 처리
    pass
```

### 6.2. 이벤트 버스

```python
# 이벤트 발행
from app.events import EventBus

event_bus = EventBus()

async def publish_generation_completed(event):
    await event_bus.publish("generation.completed", event)

# 이벤트 구독
@event_bus.subscribe("trend.analyzed")
async def handle_trend_analyzed(event):
    # 트렌드 분석 완료 처리
    pass
```

---

## 7. 캐싱 전략

### 7.1. 다단계 캐싱

```python
# L1: 인메모리 캐시 (Python)
from functools import lru_cache

@lru_cache(maxsize=1024)
def get_trend_data(keywords_hash):
    # 자주 조회되는 트렌드 데이터
    pass

# L2: Redis 캐시
import redis

redis_client = redis.Redis(host='redis', port=6379)

async def get_cached_analysis(analysis_id):
    cached = redis_client.get(f"analysis:{analysis_id}")
    if cached:
        return json.loads(cached)
    return None
```

### 7.2. CDN 캐싱
- 정적 자원 CDN 배포
- 이미지 최적화
- 글로벌 엣지 로케이션

---

## 8. 모니터링

### 8.1. 메트릭 수집

```python
# Prometheus 메트릭
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Request latency')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active connections')

# 미들웨어 적용
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_LATENCY.observe(duration)

    return response
```

### 8.2. 로깅

```python
# 구조화 로깅
import structlog

logger = structlog.get_logger()

async def process_generation(request):
    logger.info(
        "generation_started",
        request_id=request.id,
        user_id=request.user_id,
        prompt=request.prompt[:50]
    )

    try:
        result = await generate_image(request)
        logger.info(
            "generation_completed",
            request_id=request.id,
            image_urls=result.urls
        )
        return result
    except Exception as e:
        logger.error(
            "generation_failed",
            request_id=request.id,
            error=str(e),
            exc_info=True
        )
        raise
```

### 8.3. 헬스 체크

```python
from fastapi import HTTPException
from app.dependencies import get_db, get_redis

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # DB 연결 확인
        db.execute("SELECT 1")

        # Redis 연결 확인
        redis = get_redis()
        redis.ping()

        # 외부 API 연결 확인
        # ...

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "checks": {
                "database": "ok",
                "redis": "ok",
                "external_apis": "ok"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service unavailable")
```

---

## 9. 배포 아키텍처

### 9.1. 컨테이너화

```dockerfile
# Dockerfile
FROM python:3.10-slim as base

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 실행 사용자 생성
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 9.2. 오케스트레이션

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/fashion_ai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=fashion_ai
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
```

### 9.3. CI/CD 파이프라인

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest
      - name: Run tests
        run: pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # 배포 스크립트
          docker-compose -f docker-compose.prod.yml up -d
```

---

## 10. 성능 최적화

### 10.1. 데이터베이스 최적화

```python
# 쿼리 최적화
from sqlalchemy.orm import selectinload, joinedload

# N+1 문제 해결
projects = session.query(Project)\
    .options(selectinload(Project.analyses))\
    .options(joinedload(Project.user))\
    .all()

# 배치 처리
def bulk_insert_raw_data(data_list):
    session.bulk_insert_mappings(RawData, data_list)
    session.commit()
```

### 10.2. API 최적화

```python
# 응답 압축
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 비동기 처리
import asyncio
import aiohttp

async def fetch_multiple_sources(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_source(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    return results
```

---

## 11. 보안 아키텍처

### 11.1. 인증/인가

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = decode_jwt(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
```

### 11.2. 데이터 암호화

```python
from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

---

## 12. 재해 복구

### 12.1. 백업 전략
- 데이터베이스: 매일 자동 백업
- 파일 스토리지: 3중 복제
- 구성: 버전 관리

### 12.2. Failover
- Active-Active 구성
- 자동 장애 전환
- 데이터 일관성 보장

---

## 13. 향후 개선 방향

### 13.1. 기술적 개선
- GraphQL 도입
- gRPC 도입
- 서비스 메시 (Istio)
- 이벤트소싱

### 13.2. 기능적 개선
- 실시간 협업
- 3D 뷰어
- VR/AR 지원
- AI 추천 시스템

---

## 14. 참고 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [PostgreSQL 문서](https://www.postgresql.org/docs/)
- [Docker 공식 문서](https://docs.docker.com/)
- [Kubernetes 공식 문서](https://kubernetes.io/docs/)
- [Nginx 공식 문서](https://nginx.org/en/docs/)

---

*본 문서는 시스템의 현재 상태를 기준으로 작성되었으며, 지속적으로 업데이트됩니다.*