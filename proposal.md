# 근거 기반 디자인 창작 지원 시스템 구축 제안서

---

## 0. 표지

**AI 기반 디자인 창작 지원 시스템 구축 제안**

Evidence-Based Design Creation Support System

From Purpose to Specification with Evidence

2026.05

---

## 1. The Question (문제 인식)

"디자이너의 감과 경험에만 의존해 컨셉을 결정하고 계십니까? 그 결정의 근거를 팀과 클라이언트에게 설명할 수 있습니까?"

- 트렌드 정보는 폭증했지만, 의미 있는 인사이트로 연결되는 과정이 부족합니다.
- 레퍼런스는 많이 수집하지만, 복제와 참고의 경계가 모호합니다.
- 디자인 결정은 개인 머릿속에 남고, 조직의 지식 자산으로 축적되지 않습니다.
- 클라이언트와의 소통에서 "왜 이 컨셉인가"에 대한 근거 있는 설명이 어렵습니다.

---

## 2. Executive Summary (요약)

본 제안은 **디자인 목적을 구조화하고, 트렌드 근거로 컨셉을 결정하며, 레퍼런스를 추상화해 시각화하고, 스펙 문서로 남기는** 통합 디자인 창작 지원 시스템 구축을 제안합니다.

핵심 가치는 다음과 같습니다.

- **근거 기반 발상**: 출처 없는 제안을 금지하고, 모든 컨셉 결정은 트렌드와 레퍼런스에 근거
- **레퍼런스 추상화**: 레퍼런스를 모방이 아닌 디자인 문법으로 변환
- **결정 기록 보존**: 선택과 폐기의 모든 과정을 Decision Log로 관리
- **사용자 스케치 존중**: 사용자 고유의 창작물을 원본 보존하며 구체화
- **멀티 도메인 지원**: 산업/패션/시각/광고 디자인 도메인팩 제공

---

## 3. 시장 맥락 및 Pain Point

### 3.1 디자인 결정의 근거 부재

- 디자인 기획 회의에서 "왜 이 방향인가"에 대한 답이 개인 감에 머뭅니다.
- 트렌드 조사 결과가 정리되지 않아 매번 같은 조사를 반복합니다.
- 레퍼런스 수집은 많지만, 어떤 요소를 참고했는지 기록이 없습니다.

### 3.2 AI 도구의 한계

- 기존 AI 이미지 생성기는 "무엇을 만들지"는 도와주지만 "왜 만드는지"는 답하지 못합니다.
- 레퍼런스를 그대로 모방하는 AI 도구는 저작권 리스크를 가집니다.
- 사용자의 스케치를 무시하고 유행 스타일을 덮어씌우는 문제가 있습니다.

### 3.3 조직 지식의 유실

- 디자이너가 퇴사하면 왜 그 컨셉을 선택했는지 알 수 없게 됩니다.
- 폐기된 대안에 대한 기록이 없어 나중에 비슷한 논의를 반복합니다.

---

## 4. 제안 솔루션 개요

### 4.1 근거 기반 디자인 발상 시스템

본 시스템은 단순 이미지 생성 툴이 아니라, **목적 구조화부터 스펙 문서화까지 연결하는 지능형 창작 지원 에이전트**입니다.

- Brief Builder: 목적을 구조화된 브리프로 변환
- Trend Researcher: 출처 기반 트렌드 근거 조사
- Concept Generator: 근거 기반 컨셉 후보 생성과 평가
- Reference Searcher: 컨셉 기반 레퍼런스 검색과 분석
- Abstraction Engine: 레퍼런스를 디자인 문법으로 추상화
- Sketch Refiner: 사용자 스케치 해석과 구체화
- Spec Writer: 모든 결정을 스펙 문서로 구조화

---

## 5. 핵심 경쟁력 (차별점)

| 구분 | 일반 AI 이미지 생성 | 기존 디자인 도구 | 제안 시스템 |
| --- | --- | --- | --- |
| 컨셉 근거 | 없음 (프롬프트 의존) | 없음 (사용자 판단) | 트렌드/레퍼런스 출처 기반 |
| 레퍼런스 활용 | 스타일 복제 | 수동 참고 | 추상화 문법 변환 |
| 결정 기록 | 없음 | 없음 | Decision Log 전 과정 기록 |
| 사용자 스케치 | 무시 또는 덮어쓰기 | 직접 편집 | 원본 보존 + 구체화 |
| 결과물 | 이미지 | 편집 파일 | 이미지 + 스펙 문서 + 결정 이력 |
| 도메인 | 범용 | 도구 특화 | 도메인팩 (산업/패션/시각/광고) |

---

## 6. 시스템 아키텍처

### 6.1 기술 스택

- **Frontend**: Vanilla HTML + Vanilla JS + Vanilla CSS
- **Backend**: Django 5.2 LTS (Python 3.13+)
- **Database**: PostgreSQL 15+
- **Architecture**: Clean Architecture (Domain/Application/Infrastructure/Presentation)

### 6.2 클린 아키텍처 구조

모든 기능은 독립 모듈로 구성합니다.

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
```

레이어 규칙:
- Domain: Entity, Value Object, Domain Service (Django ORM 비의존)
- Application: UseCase, DTO, Command, Query, Port 인터페이스
- Infrastructure: Django ORM Repository, 외부 API, 크롤러, RAG
- Presentation: Django View, Template, Vanilla JS, CSS

### 6.3 SaaS 구조

- 사용자 워크스페이스와 관리자 프로그램 분리
- Tenant → Workspace → Project → Session 계층
- 멀티테넌시: 모든 데이터는 Tenant와 Workspace에 종속
- 관리자 작업은 AuditLog에 저장

---

## 7. 파이프라인 (17단계)

```text
 1. 목적 입력            — 자연어 목적, 도메인 선택
 2. 브리프 구조화         — 대상, 사용 맥락, 제약 추출
 3. 스케치 업로드 (선택)  — 사용자 스케치, 메모
 4. 추가 질문            — 누락 필드 판정
 5. 트렌드 조사           — RAG, 웹 검색, 문서 검색
 6. 컨셉 후보 생성        — 후보 생성, 스코어링
 7. 컨셉 후보 평가        — 근거, 리스크 평가
 8. 컨셉 결정            — 승인/보류/폐기 기록
 9. 레퍼런스 검색         — 웹/이미지/문서 검색
10. 레퍼런스 분석         — 의미/형태/구조 분석
11. 스케치 분석           — 의도/형태/구조 분석
12. 추상화               — 디자인 문법 변환
13. 시각화               — 스케치 생성/구체화/변형
14. 대상물 적용           — 대상물/매체/아이템에 적용
15. 후보 비교             — 장단점 비교, 최종 선택
16. 스펙 문서 작성        — 모든 산출물 구조화
17. 검토/승인             — 버전 관리, 승인
```

### 7.1 파이프라인 불변 조건

- 출처 없는 트렌드 주장은 컨셉 결정의 근거로 쓰지 않는다.
- 레퍼런스 원본과 AI 생성 이미지를 엄격히 구분한다.
- 사용자 업로드 스케치 원본을 절대 덮어쓰지 않는다.
- 이미지 생성은 최소 1개 이상의 브리프, 컨셉, 레퍼런스, 추상화 규칙과 연결되어야 한다.
- 스펙 문서는 버린 대안과 선택 사유도 기록한다.

---

## 8. 사용자 진행 모드

### 8.1 챗봇 협업 모드

디자이너와 AI가 함께 컨셉을 좁혀가는 기본 모드. AI 답변 옆에 근거 출처를 표시하고, 컨셉 후보 카드마다 점수와 리스크를 보여줍니다.

### 8.2 자동 진행 모드

사용자가 목적과 제약만 입력하면 시스템이 끝까지 진행. 자동 결정마다 점수, 근거, 대안, 리스크를 저장하고, 불확실성이 큰 항목은 "검토 필요"로 표시합니다.

### 8.3 사용자 스케치 기반 진행

사용자의 스케치를 업로드하여 AI가 의도를 해석하고 구체화 방향을 제시. 원본 스케치는 불변 저장하고, 구체화 결과는 별도 버전으로 관리합니다.

---

## 9. 도메인팩

| 도메인 | 특화 분석 | 시각화 | 스펙 필드 |
|---|---|---|---|
| 산업디자인 | 사용성, 구조, 재료, 생산성, CMF | 형태/구조 스케치, 사용 장면, 변형안 | 치수, 소재, 구조, 제조, 사용 시나리오 |
| 패션디자인 | 시즌, 타깃, 실루엣, 소재, 패턴 | 무드보드, 룩 스케치, 착장 이미지 | 아이템, 소재, 컬러, 패턴, 스타일링 |
| 시각디자인 | 브랜드 톤, 색, 타입, 그리드 | 키비주얼, 로고, 포스터, 그래픽 시스템 | 색/타입/그리드, 사용 규칙, 금지 규칙 |
| 광고디자인 | 타깃 인사이트, 메시지, 채널 | 캠페인 컷, 소셜 소재, 스토리보드 | 메시지, 채널, 비주얼 톤, 카피, CTA |

---

## 10. 추상화 엔진

레퍼런스를 디자인 문법으로 바꾸는 핵심 모듈입니다.

| 축 | 분석 | 산출 예 |
|---|---|---|
| 형태 | 외곽선, 비례, 반복, 곡률 | 삼각 실루엣, 긴 수평선 |
| 구조 | 하중, 결합, 지지, 접힘 | 경사 지지, 레이어 구조 |
| 표면 | 질감, 광택, 패턴 | 무광, 거친 입자 |
| 색/재료 | 색상 대비, 소재 감각 | 흙색, 반투명 소재 |
| 의미 | 상징과 감정 | 안정, 고요, 자연성 |
| 사용성 | 기능과의 연결 | 잡기 쉬움, 세워짐 |

---

## 11. 레퍼런스 검색기

디자인 컨셉을 구체화하기 위한 증거 수집과 해석 도구입니다.

검색 유형: 키워드, 이미지, 스케치 기반, 문서, 내부 자산, 확장 검색

레퍼런스 분류: Nature, Product, Architecture, Fashion, Graphic, Advertising, Material

카드 필수 정보: 썸네일, 출처 URL, 라이선스, 도메인 태그, 추상화 가능 요소, 복제 위험

---

## 12. 트렌드 지식 시스템

관리자가 트렌드 출처를 등록하고, 시스템이 문서를 수집/파싱/색인합니다.

- 패션: Vogue Business, WGSN, 패션위크 리뷰
- 산업디자인: Core77, Dezeen, DesignWanted
- 시각디자인: AIGA, It's Nice That, Brand New
- 광고디자인: Cannes Lions, Campaign, AdAge
- 범용: Adobe Trends, Pinterest Predicts, Behance

품질 기준: 발행일/수집일 분리, 다중 출처 근거 강화, 최신성 점수 관리

---

## 13. AI 모델 관리

코드에 모델명을 직접 박아 넣지 않고, 관리자 페이지에서 기능별 모델 정책을 관리합니다.

| 기능 | 모델 유형 |
|---|---|
| Trend Research | 검색/텍스트 |
| Concept Chat | 대화 |
| Sketch Analysis | 비전/멀티모달 |
| Reference Analysis | 비전/멀티모달 |
| Abstraction | 추론/텍스트 |
| Image Generation | 이미지 |
| Spec Writing | 긴 문서 |
| Verification | 텍스트/비전 |

Fallback은 거짓 결과가 아니라 실패 보고 + 대체 모델 정책입니다.

---

## 14. 위험과 대응

| 위험 | 대응 |
|---|---|
| 레퍼런스 표절 | 원본 복제 금지, 추상화 규칙 저장, 출처/라이선스 표시 |
| AI 환각 | 출처 없는 주장 금지, 근거 문서 연결 |
| UX 복잡도 | 현재 단계/다음 결정/근거만 우선 표시 |
| 자동 모드 품질 | 중간 산출물 저장, 검토 필요 항목 표시 |
| 모델 비용 | 기능별 모델 정책, 비용 제한 |
| SaaS 데이터 혼선 | Tenant/Workspace 접근 제어, 감사 로그 |

---

## 15. 추진 계획

### Phase 1: Design Session
- 프로젝트/세션/브리프
- 챗봇 협업 모드
- 사용자 스케치 업로드와 원본 보존
- 컨셉 후보와 결정 로그
- 기본 스펙 문서

### Phase 2: Trend Knowledge
- 관리자 출처 등록
- 문서 수집/파싱/색인
- 트렌드 근거 인용

### Phase 3: Reference Searcher
- 웹/이미지/문서 검색
- 레퍼런스 저장과 분석
- 출처/라이선스/위험 표시

### Phase 4: Abstraction & Generation
- 레퍼런스/스케치 분석
- 추상화 규칙 생성
- 스케치 구체화 및 변형 이미지 생성

### Phase 5: Spec Builder & Admin
- 도메인별 스펙 템플릿
- 문서 버전 관리
- 모델 카탈로그와 운영 관리

---

## 16. 기대 효과

- 디자인 결정의 근거 명확화 — "왜 이 컨셉인가"에 대한 답변 가능
- 기획 리드타임 단축 — 목적 입력에서 스펙 문서까지 자동화
- 레퍼런스 저작권 리스크 감소 — 추상화 문법으로 복제 방지
- 조직 지식 자산 축적 — 모든 결정 이력이 프로젝트 단위로 보존
- 다양한 도메인 대응 — 도메인팩으로 산업/패션/시각/광고 확장

---

## 17. 결론

"Evidence, not Guess."

본 제안 시스템은 **디자인 목적 구조화, 트렌드 근거 조사, 컨셉 결정, 레퍼런스 추상화, 시각화, 스펙 문서화**까지 하나의 파이프라인으로 연결해, **디자인 결정을 감에서 근거로 전환하는 실질적인 도구**입니다.

디자인 창작의 데이터 전환을 시작하십시오.
