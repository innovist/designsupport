# Design Support System - Architecture Guide
**Version:** 2.0.0
**Last Updated:** 2026-05-07

---

## 1. 시스템 개요

Design Support System은 근거 기반 디자인 창작을 지원하는 SaaS 플랫폼입니다. 편집툴이나 AI 이미지 생성기가 아니라, 디자인 목적을 구조화하고 트렌드 근거로 컨셉을 결정하며, 레퍼런스를 추상화해 시각화하고, 스펙 문서로 남기는 시스템입니다.

### 1.1. 핵심 기능
- **브리프 구조화**: 자연어 목적을 구조화된 디자인 브리프로 변환
- **트렌드 근거 조사**: 출처 기반 트렌드 인사이트 수집
- **컨셉 후보 관리**: 근거 기반 컨셉 생성, 평가, 결정 기록
- **레퍼런스 검색과 추상화**: 레퍼런스를 디자인 문법으로 변환
- **사용자 스케치 지원**: 원본 보존, AI 해석, 구체화
- **이미지 생성**: 추상화 규칙 기반 스케치/변형 생성
- **스펙 문서화**: 모든 결정 근거를 포함한 문서 생성
- **관리자 시스템**: 트렌드 지식, AI 모델, 테넌트 관리

### 1.2. 기술 스택
- **Backend**: Django 5.2 LTS (Python 3.13+)
- **Frontend**: Vanilla HTML + Vanilla JS + Vanilla CSS
- **Database**: PostgreSQL 15+
- **Cache/Queue**: Redis 7
- **Container**: Docker + Docker Compose
- **Monitoring**: Prometheus + Grafana

---

## 2. 아키텍처 원칙

### 2.1. 클린 아키텍처

모든 기능은 독립 모듈로 구성하며, 4계층 레이어를 따릅니다.

| 계층 | 책임 | 규칙 |
|------|------|------|
| Domain | Entity, Value Object, Domain Service | Django ORM에 의존하지 않음 |
| Application | UseCase, DTO, Command, Query, Port | 인프라 구현체에 의존하지 않음 |
| Infrastructure | Django ORM Repository, 외부 API, 크롤러, RAG | 구체적인 기술 구현 |
| Presentation | Django View, Template, Vanilla JS, CSS | 사용자 인터페이스 |

모듈 간 직접 ORM 접근은 금지합니다. 다른 모듈 데이터가 필요하면 Application Port 또는 Query Service를 통해 접근합니다.

### 2.2. 품질 속성

| 속성 | 목표 | 구현 전략 |
|------|------|-----------|
| 확장성 | 도메인팩 추가 용이 | 공통 파이프라인 + 도메인별 템플릿 |
| 가용성 | 99.5% | 헬스 체크, Failover |
| 보안 | 테넌트 격리 | Tenant/Workspace 접근 제어, AuditLog |
| 추적성 | 모든 결정 기록 | Decision Log, 출처 연결 |

---

## 3. 시스템 구조

### 3.1. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ User Workspace  │  │ Admin Console   │                  │
│  │ Vanilla HTML/JS │  │ Vanilla HTML/JS │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  Django Views + Templates + Static Files                    │
│  REST API Endpoints                                          │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  UseCases: BriefBuilder, TrendResearcher, ConceptGenerator  │
│  ReferenceSearcher, AbstractionEngine, SketchRefiner        │
│  SpecWriter, GenerationOrchestrator                         │
│  Ports: Repository, Gateway, Indexer Interfaces             │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                            │
│  Entities: Brief, Concept, Reference, AbstractionRule       │
│  Sketch, GeneratedDesign, SpecDocument, TrendInsight        │
│  Value Objects: Decision, Score, Source, License            │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                       │
│  Django ORM Repositories │ AI Model Router                  │
│  Web Crawlers            │ File/Object Storage              │
│  RAG / Search Index      │ Background Jobs (Celery)         │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                        │
│  AI Providers (Gemini, GLM, OpenAI) │ Web Search APIs       │
│  Image Generation Models            │ Trend Source Websites  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2. 모듈 구조

```text
apps/
  accounts/         domain/ application/ infrastructure/ presentation/
  workspaces/       domain/ application/ infrastructure/ presentation/
  design_projects/  domain/ application/ infrastructure/ presentation/
  design_sessions/  domain/ application/ infrastructure/ presentation/
  conversations/    domain/ application/ infrastructure/ presentation/
  user_assets/      domain/ application/ infrastructure/ presentation/
  trend_knowledge/  domain/ application/ infrastructure/ presentation/
  references/       domain/ application/ infrastructure/ presentation/
  concepts/         domain/ application/ infrastructure/ presentation/
  abstraction/      domain/ application/ infrastructure/ presentation/
  generation/       domain/ application/ infrastructure/ presentation/
  specs/            domain/ application/ infrastructure/ presentation/
  model_catalog/    domain/ application/ infrastructure/ presentation/
  admin_console/    domain/ application/ infrastructure/ presentation/
  audit_logs/       domain/ application/ infrastructure/ presentation/
shared/
  domain/ application/ infrastructure/ presentation/
```

---

## 4. 데이터베이스 설계

### 4.1. 핵심 엔티티 관계

```
Tenant 1--* User
Tenant 1--* Workspace
Workspace 1--* DesignProject
DesignProject 1--* DesignSession
DesignSession 1--1 DesignBrief
DesignSession 1--* UserSketchAsset
UserSketchAsset 1--* SketchAnalysis
DesignSession 1--* ConceptCandidate
ConceptCandidate 1--* ConceptDecision
DesignSession 1--* ReferenceAsset
ReferenceAsset 1--* ReferenceAnalysis
DesignSession 1--* AbstractionRule
SketchAnalysis 1--* AbstractionRule
AbstractionRule 1--* GeneratedDesign
DesignSession 1--* DesignEvaluation
DesignSession 1--* SpecDocument
TrendSource 1--* TrendDocument
TrendDocument 1--* TrendInsight
ModelProvider 1--* ModelCatalog
ModelCatalog 1--* FeatureModelPolicy
DesignSession 1--* GenerationJob
User 1--* AuditLog
```

### 4.2. 주요 테이블

| 테이블 | 설명 | 주요 필드 |
|--------|------|----------|
| DesignBrief | 목적, 도메인, 타깃, 제약 | purpose, domain, target, context, constraints |
| UserSketchAsset | 사용자 원본 스케치 | file_path, sketch_type, description, uploaded_by |
| SketchAnalysis | 스케치 AI 해석 | intent, form_elements, structure, unclear_points |
| ConceptCandidate | 컨셉 후보 | name, description, score, evidence, risks, status |
| ConceptDecision | 컨셉 결정 기록 | decision, reason, decided_by, alternatives |
| ReferenceAsset | 레퍼런스 자료 | url, title, category, source_type, license |
| ReferenceAnalysis | 레퍼런스 분석 | form_grammar, structure_grammar, copyright_risk |
| AbstractionRule | 추상화 규칙 | axis, observation, application, source_refs |
| GeneratedDesign | 생성 이미지 | image_url, type, linked_rules, linked_concept |
| SpecDocument | 스펙 문서 | content, version, status, approved_by |
| TrendSource | 트렌드 출처 | name, url, domain, crawl_interval, reliability |
| TrendDocument | 트렌드 문서 | title, url, published_at, parsed_text, hash |
| TrendInsight | 트렌드 인사이트 | summary, keywords, evidence_quote, confidence |
| FeatureModelPolicy | 기능별 모델 정책 | feature_key, model, parameters, fallback_policy |

---

## 5. AI 모델 라우터

### 5.1. 기능별 모델 정책

```text
.env (Provider + API Key)
    -> ModelProvider
    -> ModelCatalog
    -> FeatureModelPolicy (관리자 설정)
    -> ModelRouter
    -> TrendResearch / ConceptChat / SketchAnalysis / ...
```

모델명은 코드에 하드코딩하지 않고, `.env`와 관리자 카탈로그를 통해 관리합니다.

### 5.2. Fallback 전략

Fallback은 거짓 결과를 반환하는 방식이 아니라 실패를 명확히 보고하고 재시도 가능한 다른 모델 정책을 사용하는 방식입니다.

---

## 6. 파이프라인 오케스트레이션

### 6.1. 17단계 파이프라인

```
 1. 목적 입력 -> 2. 브리프 구조화 -> 3. 스케치 업로드(선택)
 -> 4. 추가 질문 -> 5. 트렌드 조사 -> 6. 컨셉 후보 생성
 -> 7. 컨셉 평가 -> 8. 컨셉 결정 -> 9. 레퍼런스 검색
 -> 10. 레퍼런스 분석 -> 11. 스케치 분석 -> 12. 추상화
 -> 13. 시각화 -> 14. 대상물 적용 -> 15. 후보 비교
 -> 16. 스펙 문서 작성 -> 17. 검토/승인
```

### 6.2. 불변 조건

- 출처 없는 트렌드 주장은 컨셉 결정 근거로 사용하지 않음
- 레퍼런스 원본과 AI 생성 이미지를 엄격히 구분
- 사용자 스케치 원본을 절대 덮어쓰지 않음
- 이미지 생성은 최소 1개 이상의 브리프, 컨셉, 추상화 규칙과 연결
- 스펙 문서는 버린 대안과 선택 사유도 기록

---

## 7. SaaS 멀티테넌시

### 7.1. 데이터 격리

모든 사용자 데이터는 Tenant와 Workspace에 종속됩니다.

```text
Tenant
  -> Workspace
    -> DesignProject
      -> DesignSession (Brief, Concepts, References, ...)
```

### 7.2. 공용 데이터

- 트렌드 출처와 문서: 공개 범위와 비공개 범위 구분
- 모델 카탈로그: 관리자가 관리, 모든 테넌트 공유
- 레퍼런스 공용 라이브러리: 옵션

### 7.3. 감사 로그

관리자 작업과 AI 호출은 AuditLog에 저장합니다.

---

## 8. 도메인팩

공통 파이프라인 위에 얹히는 도메인별 입력/평가/출력 템플릿입니다.

| 도메인 | 특화 분석 | 시각화 | 스펙 필드 |
|--------|----------|--------|----------|
| 산업디자인 | 사용성, 구조, 재료, CMF | 형태/구조 스케치, 사용 장면 | 치수, 소재, 제조 방식 |
| 패션디자인 | 시즌, 실루엣, 소재, 패턴 | 무드보드, 룩 스케치, 착장 | 아이템, 소재, 컬러, 스타일링 |
| 시각디자인 | 브랜드 톤, 색, 타입, 그리드 | 키비주얼, 로고, 포스터 | 색/타입/그리드, 사용 규칙 |
| 광고디자인 | 타깃 인사이트, 메시지, 채널 | 캠페인 컷, 소셜 소재 | 메시지, 채널, 카피, CTA |

---

## 9. 배포 아키텍처

### 9.1. 컨테이너화

```dockerfile
FROM python:3.13-slim as base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

### 9.2. 오케스트레이션

```yaml
services:
  web:
    build: .
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/design_support
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=design_support
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  celery:
    build: .
    command: celery -A config worker -l info
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

volumes:
  postgres_data:
```

---

## 10. 참고 자료

- [Django 공식 문서](https://docs.djangoproject.com/)
- [PostgreSQL 문서](https://www.postgresql.org/docs/)
- [Docker 공식 문서](https://docs.docker.com/)
- [Celery 문서](https://docs.celeryq.dev/)

---

*본 문서는 시스템의 현재 상태를 기준으로 작성되었으며, 지속적으로 업데이트됩니다.*
