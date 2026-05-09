---
id: SPEC-05-UX-WORKSPACE
title: 사용자 워크스페이스 UX(Project Navigator + Design Studio 7-Board + Decision Panel, 스켈레톤 로딩, i18n, 접근성)
version: 0.1.0
status: draft
created: 2026-05-07
domain: ux
priority: P0
dependencies: [SPEC-01-FOUNDATION-SESSION, SPEC-02-KNOWLEDGE, SPEC-03-CREATION, SPEC-04-MODEL-ADMIN]
---

# SPEC-05-UX-WORKSPACE: 사용자 워크스페이스 UX

## 1. 개요 (Overview)

### 1.1 목적
디자이너가 17단계 파이프라인을 “지금 무엇을 판단해야 하는지” 항상 인지하면서 진행할 수 있도록 사용자 워크스페이스 UX와 프런트엔드 구현 기준을 정의한다. Project Navigator + Design Studio 7-Board + Decision Panel의 3분할 레이아웃을 표준화하고, Sketch Input Board의 3분할(원본/AI 해석/Refinement Actions), Reference Search UI(Source Clusters/Reference Grid/Analysis), Spec Builder UI(섹션별 출처·결정 로그 연결)를 명세한다. 단순 스피너를 금지하고, 단계별 스켈레톤 + 실제 작업 로그 표시 표준을 정한다. i18n(ko/en/zh-CN/zh-TW) 및 접근성(WCAG 2.1 AA)을 강제한다. 관리자 콘솔 UX는 SPEC-04가 구현 범위를 소유하되, 본 SPEC의 i18n·접근성·스켈레톤·시각 토큰 표준을 동일하게 준수한다.

### 1.2 범위 (In Scope)
- 사용자 워크스페이스 레이아웃과 라우팅 (단계별 화면 1:1 매핑)
- 7-Board: Chat / Evidence / Sketch Input / Reference / Abstraction / Generation / Decision
- Sketch Input Board (원본 / AI 해석(가설) / Refinement Actions)
- Reference Search UI (Source Clusters / Reference Grid / Analysis 패널)
- Spec Builder UI (섹션별 출처·결정 로그 인용 + 검토 가능 뷰어)
- 스켈레톤 로딩(단계별 + 실제 작업 로그) — 스피너 금지
- i18n 4언어, 접근성 WCAG 2.1 AA, 다국어 폰트/숫자/날짜 처리
- 시각 구분 규칙: 사용자 스케치 / 외부 레퍼런스 / 추상화 / 생성 이미지 (라벨·카드 색상·아이콘)
- 완전한 프런트엔드 상태: 생성/조회/수정/재실행/승인/반려/저장/삭제(tombstone)/빈 상태/오류 상태/권한 없음/네트워크 실패/비동기 진행/부분 실패/재시도 UI

### 1.3 범위 외 (Out of Scope)
- 관리자 콘솔 UI 상세 구현 소유권(SPEC-04). 단, 관리자 콘솔도 본 SPEC의 UX 표준(i18n, 접근성, 스켈레톤, 디자인 토큰, 오류 상태)을 준수한다.
- 백엔드 도메인/엔티티/모델 라우팅(SPEC-01~04)
- 결제/플랜 관리(향후 SPEC)

### 1.4 가치 제안
- 사용자가 단계·근거·다음 결정을 한눈에 본다 → 의사결정 속도와 품질 동시 향상
- 사용자 스케치/외부 레퍼런스/AI 결과의 시각 구분 → INV-02-04 / INV-01-01 UI 수준 강제
- 스켈레톤 + 작업 로그 → 자동 모드의 “블랙박스화” 방지

### 1.5 User_Needs.md 매핑
- §11(UX/UI 상세), §12(UX/UI 검증 기준), §13.1(사용자 영역), §3(원칙), §22(위험과 대응)

---

## 2. 사용자 스토리 (User Stories)

- US-05-01 (디자이너): 화면 어디서나 현재 단계, 다음 결정, 근거 출처를 즉시 확인한다.
- US-05-02 (디자이너): 사용자 스케치 카드와 외부 레퍼런스 카드의 색상/라벨/아이콘이 명확히 다르다.
- US-05-03 (디자이너): 스케치 업로드 후 원본/AI 해석/Refinement Actions가 3분할 화면에 동시에 보인다.
- US-05-04 (디자이너): 트렌드 자료 부족·라이선스 위험·모델 실패 등 모든 빈 상태/오류 상태가 의미 있게 표현된다.
- US-05-05 (디자이너): 단계 진행 중 실제 작업 로그(어떤 모델이 무엇을 하고 있는지)가 스켈레톤과 함께 표시된다.
- US-05-06 (디자이너/리드): 스펙 문서 뷰어에서 각 섹션마다 인용 출처와 결정 로그로 점프할 수 있다.
- US-05-07 (다국어 사용자): ko/en/zh-CN/zh-TW로 UI를 전환하면 라벨/플레이스홀더/오류 메시지가 모두 번역되어 표시된다.
- US-05-08 (스크린리더 사용자): 모든 결정 버튼·카드 라벨이 적절한 의미 있는 라벨과 ARIA 속성을 갖는다.

---

## 3. 요구사항 (EARS Format Requirements)

### 3.1 레이아웃과 라우팅 (REQ-05-LAYOUT)

- REQ-05-LAYOUT-001 (Ubiquitous): THE SYSTEM SHALL 사용자 워크스페이스(포트 14000)는 3분할 레이아웃을 사용한다: 좌측 Project Navigator, 중앙 Design Studio, 우측 Decision Panel. (근거: §11.2)
- REQ-05-LAYOUT-002 (Ubiquitous): THE SYSTEM SHALL 화면 라우팅은 17단계 파이프라인과 1:1로 매핑되며, 현재 단계는 상단 단계 바와 Decision Panel에서 동시 표시된다. (근거: §4, §11.1)
- REQ-05-LAYOUT-003 (Ubiquitous): THE SYSTEM SHALL Decision Panel은 항상 다음을 표시한다: 현재 단계, 브리프 점수, 컨셉 점수, 선택된 스케치, 선택된 레퍼런스, “다음 결정” 버튼과 그 이유. (근거: §11.2)
- REQ-05-LAYOUT-004 (Ubiquitous): THE SYSTEM SHALL Evidence Board와 Decision Panel은 모든 단계에서 항상 보인다(수축은 가능하나 숨김 불가). (근거: §11.1)
- REQ-05-LAYOUT-005 (Ubiquitous): THE SYSTEM SHALL 17단계 각각에 대해 주 화면, 주 보드, 가능한 액션, 빈/오류 상태, 되돌아가기 경로를 정의하고 구현한다. 화면이 없는 파이프라인 단계는 허용하지 않는다.

### 3.2 7-Board (REQ-05-BOARD)

- REQ-05-BOARD-001 (Ubiquitous): THE SYSTEM SHALL Design Studio는 7개 보드를 제공한다: Chat, Evidence, Sketch Input, Reference, Abstraction, Generation, Decision. (근거: §11.3)
- REQ-05-BOARD-002 (Ubiquitous): THE SYSTEM SHALL Chat Panel은 SPEC-01 `ChatMessage` 단위로 렌더링하며, AI 메시지에 `evidence_refs` 또는 `is_hypothesis` 표지를 시각적으로 표시한다. (근거: §3.2, SPEC-01 REQ-01-SESSION-004)
- REQ-05-BOARD-003 (Ubiquitous): THE SYSTEM SHALL Evidence Board는 SPEC-02 `TrendInsight`를 인용 카드로 표시하고, 각 카드에 출처 URL·발행일·신뢰도·최신성 점수를 노출한다. (근거: §11.3, §8.3)
- REQ-05-BOARD-004 (Ubiquitous): THE SYSTEM SHALL Generation Board는 결과 자산이 `kind`(refinement/variation/domain_application)별로 별도 섹션에 표시되고, 부모 자산(원본 스케치) 링크를 보여준다. (근거: §10.2, SPEC-03 REQ-03-GEN-003)

### 3.3 시각 구분 (REQ-05-VISUAL)

- REQ-05-VISUAL-001 (Ubiquitous): THE SYSTEM SHALL 사용자 스케치 카드, 외부 레퍼런스 카드, 추상화 규칙 카드, AI 생성 이미지 카드는 라벨, 카드 배경/테두리 색상, 아이콘이 모두 다르며, 디자인 토큰으로 정의된다. (근거: §11.1, §12.1)
- REQ-05-VISUAL-002 (Unwanted): IF UI에서 사용자 스케치가 외부 레퍼런스와 동일한 컴포넌트로 렌더링되면, THEN THE SYSTEM SHALL 컴포넌트 검증 테스트에서 실패해야 한다. (근거: §9.4, SPEC-02 INV-02-04)
- REQ-05-VISUAL-003 (Ubiquitous): THE SYSTEM SHALL AI 생성 이미지 카드에는 “AI 생성” 워터마크/라벨과 모델 정책 키를 표시한다. (근거: §11.6, NFR-04-COMP-001)

### 3.4 Sketch Input Board (REQ-05-SKETCH)

- REQ-05-SKETCH-001 (Ubiquitous): THE SYSTEM SHALL Sketch Input Board는 3분할이다: 원본 스케치(Original), AI 해석(Interpretation, 가설), Refinement Actions. (근거: §11.4)
- REQ-05-SKETCH-002 (Ubiquitous): THE SYSTEM SHALL AI 해석 영역은 의도, 형태, 구조, 미확정 요소, 사용자 확인용 질문을 분리해 표시하며 “가설(Hypothesis)” 배지를 표기한다. (근거: §5.3, §10.2)
- REQ-05-SKETCH-003 (Ubiquitous): THE SYSTEM SHALL Refinement Actions는 다음 액션을 제공한다: keep/clarify/vary/refine/expand/use_as_concept_evidence/run_sketch_search/generate_refinement. (근거: §11.4)
- REQ-05-SKETCH-004 (Unwanted): IF 사용자가 원본 스케치를 “덮어쓰기”로 수정하려 하면, THEN THE SYSTEM SHALL UI에서 동작 자체를 막고 “새 버전으로 저장” 안내를 표시한다. (근거: §22, SPEC-01 REQ-01-SKETCH-002)

### 3.5 Reference Search UI (REQ-05-REF)

- REQ-05-REF-001 (Ubiquitous): THE SYSTEM SHALL Reference Search UI는 3분할이다: Source Clusters(좌), Reference Grid(중), Analysis 패널(우). (근거: §11.5)
- REQ-05-REF-002 (Ubiquitous): THE SYSTEM SHALL Reference Grid는 7개 분류(Nature/Product/Architecture/Fashion/Graphic/Advertising/Material) 클러스터 라벨을 카드에 명시한다. (근거: §9.2)
- REQ-05-REF-003 (Ubiquitous): THE SYSTEM SHALL 라이선스 위험 카드는 시각 구분(워터마크/배지)을 가지며, “직접 스타일 적용” 버튼은 비활성화된다. (근거: §10.3, SPEC-02 REQ-02-REF-005)
- REQ-05-REF-004 (Optional): WHERE 사용자가 자신의 스케치를 입력으로 검색하면, THE SYSTEM SHALL 결과 그리드 상단에 “이 스케치 기반” 헤더와 사용자 스케치 카드(별도 타입)를 표시한다. (근거: §9, SPEC-02 REQ-02-REF-003)

### 3.6 Spec Builder UI (REQ-05-SPEC)

- REQ-05-SPEC-001 (Ubiquitous): THE SYSTEM SHALL Spec Builder UI는 SPEC-03 `SpecDocument.sections`을 좌측 목차/우측 본문으로 표시하고, 각 섹션은 출처·결정 로그·생성 작업으로 점프 가능한 인용 링크를 보여준다. (근거: §11.6, §12.1)
- REQ-05-SPEC-002 (Ubiquitous): THE SYSTEM SHALL Spec Builder는 “편집기”가 아닌 “결정 기록 뷰어 + 메모”다. 본문 텍스트 직접 편집은 메모/주석 영역에서만 허용한다. (근거: §11.6)
- REQ-05-SPEC-003 (Ubiquitous): THE SYSTEM SHALL Spec Builder는 폐기/보류 컨셉 섹션을 펼침 가능한 영역으로 항상 노출한다. (근거: §4.2)

### 3.7 로딩·진행률·작업 로그 (REQ-05-LOADING)

- REQ-05-LOADING-001 (Unwanted): IF 데이터 로딩에 단순 스피너만 사용된 화면이 발견되면, THEN THE SYSTEM SHALL UI 검증 테스트에서 실패해야 한다. (근거: §11.1)
- REQ-05-LOADING-002 (Ubiquitous): THE SYSTEM SHALL 모든 비동기 단계는 단계별 스켈레톤(콘텐츠 모양과 일치) + 실제 작업 로그(현재 단계, 모델 정책 키, 진행률)를 동시에 보여준다. (근거: §5.2, §11.1)
- REQ-05-LOADING-003 (Ubiquitous): THE SYSTEM SHALL 자동 모드 상태(`queued`~`failed`)는 상단 단계 바·Decision Panel·Workspace 알림 3곳에서 동기화 표시된다. (근거: §5.2)

### 3.8 빈 상태/오류 상태 (REQ-05-EMPTY)

- REQ-05-EMPTY-001 (Ubiquitous): THE SYSTEM SHALL §12.2의 6가지 상황에 대해 의미 있는 상태 메시지·다음 액션 제안을 제공한다: 트렌드 자료 부족, 레퍼런스 없음, 라이선스 위험, 모델 실패, 자동 모드 불확실성, 문서 파싱 실패. (근거: §12.2)
- REQ-05-EMPTY-002 (Unwanted): IF 시스템 오류 메시지가 사용자에게 직접 노출되면, THEN THE SYSTEM SHALL 사용자 친화적 메시지 + “자세히 보기” 토글로 변환되어야 한다.

### 3.9 i18n / 접근성 (REQ-05-I18N)

- REQ-05-I18N-001 (Ubiquitous): THE SYSTEM SHALL 4개 언어(ko, en, zh-CN, zh-TW)를 지원하고, 기존 `static/i18n/{ko,en,zh-CN,zh-TW}.json` 자산을 1차 소스로 활용한다. (근거: 작성자 지침, 프로젝트 자산)
- REQ-05-I18N-002 (Ubiquitous): THE SYSTEM SHALL 모든 UI 라벨/플레이스홀더/오류 메시지는 i18n 키를 통해서만 출력되며, 하드코딩된 자연어를 금지한다. (근거: 작성자 지침)
- REQ-05-I18N-003 (Ubiquitous): THE SYSTEM SHALL WCAG 2.1 AA를 준수한다: 키보드 탐색, 명도 대비, 포커스 인디케이터, ARIA 라벨, 스크린리더 호환. (근거: §11.1)
- REQ-05-I18N-004 (Ubiquitous): THE SYSTEM SHALL 자동 모드 진행 표시는 시각 외에도 스크린리더 접근 가능한 라이브 영역(`aria-live`)으로 알린다.

### 3.10 데이터 계약 (REQ-05-API)

- REQ-05-API-001 (Ubiquitous): THE SYSTEM SHALL 모든 API 응답은 `current_step`, `mode`, `evidence_refs`, `is_hypothesis`, `decision_required`, `next_actions` 메타를 표준 포함한다. (근거: SPEC-01 NFR-01-A11Y-001)
- REQ-05-API-002 (Ubiquitous): THE SYSTEM SHALL UI는 메타에 따라 단계 바, Decision Panel, 가설 배지, 다음 액션 버튼을 자동 렌더링한다.
- REQ-05-API-003 (Ubiquitous): THE SYSTEM SHALL UI 액션은 서버가 반환한 `next_actions`에 없는 동작을 임의로 노출하지 않는다. 버튼 숨김/비활성 상태는 권한·상태·불변 조건의 실제 API 결과와 일치해야 한다.
- REQ-05-API-004 (Ubiquitous): THE SYSTEM SHALL 네트워크 실패, 401/403/404/409/422/429/5xx, Celery 작업 실패, quota 초과, 근거 부족, 라이선스 차단을 서로 다른 사용자 상태로 표시하고 각각 복구 액션을 제공한다.

### 3.11 프런트엔드 완전성 / 논리 검증 (REQ-05-COMPLETE)

- REQ-05-COMPLETE-001 (Ubiquitous): THE SYSTEM SHALL 사용자 워크스페이스의 모든 주요 유스케이스(새 세션, guided 대화, auto 실행, 스케치 업로드/승인, 레퍼런스 검색/선택, 컨셉 결정, 추상화, 생성, 비교, 스펙 승인, 단계 재실행)를 프런트엔드에서 끝까지 수행 가능하게 한다.
- REQ-05-COMPLETE-002 (Ubiquitous): THE SYSTEM SHALL 각 화면의 디자인 토큰, 카드 타입, 액션 라벨, 데이터 필드가 해당 도메인 불변 조건과 일치해야 한다. 예: Tier 3 레퍼런스는 직접 스타일 적용 액션이 없어야 하고, 사용자 스케치 원본은 덮어쓰기 액션이 없어야 한다.
- REQ-05-COMPLETE-003 (Unwanted): IF UI가 백엔드 실패를 성공 상태처럼 표시하거나 placeholder/mock 데이터로 빈 결과를 채우면, THEN THE SYSTEM SHALL UI 검증 테스트에서 실패해야 한다.
- REQ-05-COMPLETE-004 (Ubiquitous): THE SYSTEM SHALL 사용자 워크스페이스와 관리자 콘솔에 공통 UI 검증 게이트를 적용한다: i18n 키 누락 0, 하드코딩 자연어 0, 단순 스피너-only 0, 주요 액션 접근성 라벨 100%, 상태별 API contract snapshot 통과.

---

## 4. 인수 기준 (Acceptance Criteria)

- AC-05-L-001: Given 워크스페이스가 로드되었을 때, When 사용자가 임의 단계에 머무르면, Then 화면 상단 단계 바에 현재 단계가 강조 표시되고, Decision Panel에 “다음 결정” 버튼·이유가 1초 이내 표시된다. (REQ-05-LAYOUT-002, REQ-05-LAYOUT-003)
- AC-05-V-002: Given 같은 화면에 사용자 스케치 1개와 외부 레퍼런스 1개가 표시될 때, When DOM 스냅샷 테스트가 실행되면, Then 두 카드는 서로 다른 컴포넌트 타입과 시각 토큰을 사용함이 검증된다. (REQ-05-VISUAL-001, REQ-05-VISUAL-002)
- AC-05-K-003: Given Sketch Input Board가 열렸을 때, When 사용자가 원본 영역에서 “덮어쓰기”를 시도하면, Then UI는 “새 버전으로 저장” 모달을 띄우고 원본 자산 ID는 변하지 않는다. (REQ-05-SKETCH-004)
- AC-05-R-004: Given 라이선스 `high` 레퍼런스 카드일 때, When 사용자가 “직접 스타일 적용” 버튼을 보면, Then 버튼은 disabled이고 hover 시 사유가 표시된다. (REQ-05-REF-003)
- AC-05-L-005: Given 자동 모드에서 `concepting` 단계 진행 중일 때, When 화면을 보면, Then 단계별 스켈레톤(컨셉 카드 모양)과 작업 로그(`feature_key=ConceptChat`, 현재 시도 횟수, 진행률)가 동시에 표시된다. (REQ-05-LOADING-002)
- AC-05-E-006: Given 트렌드 자료가 부족한 상태에서, When 컨셉 후보 화면이 열리면, Then “근거 부족” 빈 상태와 추가 검색/도메인 전환 제안 버튼이 표시된다. (REQ-05-EMPTY-001)
- AC-05-S-007: Given Spec Builder가 열린 세션에서, When 사용자가 “컨셉 후보와 평가” 섹션의 인용을 클릭하면, Then Evidence Board의 해당 인사이트로 점프하고 하이라이트된다. (REQ-05-SPEC-001)
- AC-05-I-008: Given 언어를 zh-TW로 전환했을 때, When 화면을 새로고침하면, Then 모든 라벨/오류/빈 상태 메시지가 zh-TW JSON 키로 표시되며, 하드코딩 텍스트가 0개로 검증된다. (REQ-05-I18N-001, REQ-05-I18N-002)
- AC-05-A-009: Given 스크린리더(VoiceOver/NVDA)가 활성화된 상태에서, When 자동 모드가 단계 전이를 알리면, Then `aria-live` 영역으로 “현재 단계: …” 메시지가 발화된다. (REQ-05-I18N-004)
- AC-05-C-010: Given 신규 사용자가 guided 모드로 세션을 시작했을 때, When 목적 입력부터 스펙 문서 승인까지 진행하면, Then 17단계 모두에서 화면/액션/근거/결정/되돌아가기 경로가 표시되고 중간 단계 누락이 없다. (REQ-05-LAYOUT-005, REQ-05-COMPLETE-001)
- AC-05-C-011: Given API가 429 quota 초과와 `insufficient_evidence`를 각각 반환할 때, When Reference UI가 렌더링되면, Then 두 상태는 서로 다른 메시지·원인·다음 액션으로 표시되고 mock 결과로 채워지지 않는다. (REQ-05-API-004, REQ-05-COMPLETE-003)
- AC-05-C-012: Given 사용자 워크스페이스와 관리자 콘솔 UI 검증이 실행될 때, When i18n/접근성/스켈레톤/contract snapshot을 점검하면, Then 두 영역 모두 하드코딩 자연어 0, 단순 스피너-only 0, 주요 액션 ARIA 라벨 100%를 만족한다. (REQ-05-COMPLETE-004, SPEC-04 REQ-04-ADMIN-009)

---

## 5. 도메인 모델 (Domain Model)

본 SPEC은 UI/Presentation 중심이므로 신규 도메인 엔티티는 정의하지 않으며, 다음 백엔드 응답 메타 표준만 정의한다.

```text
SessionViewModel {
  session_id, mode, current_step, status,
  brief_score, concept_scores[], selected_sketch_id?, selected_reference_ids[],
  next_actions[], decision_required, evidence_refs[], is_hypothesis_flags[]
}

Card kinds (UI):
  UserSketchCard, ReferenceCard, AbstractionRuleCard, GeneratedDesignCard, TrendInsightCard
```

### 5.1 화면 ↔ 17단계 파이프라인 매핑

| 단계 | 주 화면 | 주 보드 |
|---|---|---|
| 1 목적 입력 | Onboarding | Chat |
| 2 브리프 구조화 | Brief Builder | Chat + Decision |
| 3 사용자 스케치/참고 이미지 업로드(선택) | Sketch Input Board | Sketch Input |
| 4 추가 질문과 제약 확인 | Clarifying Chat | Chat + Decision |
| 5 트렌드/시장/사용자/도메인 근거 조사 | Evidence Board | Evidence |
| 6 컨셉 후보 생성 | Concept Cards | Chat + Evidence |
| 7 컨셉 후보 평가 | Concept Evaluation | Decision + Evidence |
| 8 컨셉 결정 | Concept Decision | Decision |
| 9 레퍼런스 검색과 수집 | Reference Search | Reference |
| 10 레퍼런스 클러스터링과 적합성 분석 | Reference Analysis | Reference |
| 11 사용자 스케치와 레퍼런스 분석 | Sketch + Reference Analysis | Sketch Input + Reference |
| 12 레퍼런스/스케치 추상화 | Abstraction Board | Abstraction |
| 13 추상화 스케치 생성 또는 사용자 스케치 구체화 | Generation Board(refinement) | Generation |
| 14 대상물/매체/아이템 적용 디자인 변형 생성 | Generation Board(domain) | Generation |
| 15 후보 비교와 최종 방향 선택 | Comparison View | Generation + Decision |
| 16 스펙 문서 작성 | Spec Builder | Spec Viewer |
| 17 검토·승인·버전 관리 | Spec Approval | Decision |

---

## 6. 아키텍처 결정 (Architecture Decisions)

### 6.1 라이브러리 채택/보류

| 후보 | 판정 | 사유 |
|---|---|---|
| Vanilla HTML/JS/CSS (작성자 고정) | 채택 | 스택 제약 |
| 디자인 토큰(CSS Custom Properties) | 채택 | 시각 구분/다크모드 대응 |
| 기존 `static/i18n/{ko,en,zh-CN,zh-TW}.json` | 채택 | 자산 재활용 |
| ui-ux-pro-max-skill / web-design-guidelines (참고) | 채택(참조) | 보드 UX 가이드 자료, 코드 의존 없음 |
| React/Vue/Svelte | 거부 | 작성자 스택 제약 위반 |

### 6.2 모듈 경계
- `apps/*/presentation/templates,static`: 사용자 화면 SSR 템플릿 + Vanilla JS 모듈
- `static/js/pages/...`: 페이지별 진입점, 상태 관리 모듈은 단일 store 패턴(Vanilla)
- 백엔드와의 데이터 계약은 SPEC-01~04의 API; UI는 REQ-05-API-001 메타에만 의존

### 6.3 포트 사용 (SPEC-01 §6.2)
- 14000 = 사용자 워크스페이스 (Django Web)
- 14051 = Spec Builder 미리보기 서버(개발용; 운영은 14000 라우트 안)

### 6.4 Clean Architecture 4-layer 매핑
- presentation 레이어에 한정. 다른 레이어 변경은 본 SPEC 범위 밖
- 데이터 페치는 Application UseCase가 노출하는 JSON API만 사용 (모듈 간 직접 ORM 접근 금지)
- 관리자 콘솔은 SPEC-04가 소유하지만, 공통 i18n/접근성/스켈레톤/디자인 토큰 검증은 본 SPEC의 presentation 표준을 재사용한다.

---

## 7. 비기능 요구사항 (NFR)

- NFR-05-PERF-001: 워크스페이스 첫 인터랙션 가능 시간(TTI) p95 ≤ 2.0s.
- NFR-05-PERF-002: 보드 전환·단계 전환 시 스크롤 점프 없음, 컨텐츠 시프트(CLS) ≤ 0.1.
- NFR-05-A11Y-001: 모든 인터랙티브 요소 키보드 도달 가능, 포커스 인디케이터 표준화, 색상 의존 정보는 텍스트/아이콘 보조.
- NFR-05-I18N-001: 4개 언어 빌드 검증, 누락 키 발생 시 빌드 실패.
- NFR-05-SEC-001: XSS 방지를 위해 모든 사용자 콘텐츠는 출력 시 escape, AI 출력은 마크다운 화이트리스트 렌더러로 처리.
- NFR-05-LIC-001: AI 사용 고지를 화면 푸터/문서 카드에 표준 렌더.
- NFR-05-OBS-001: 클라이언트 오류는 백엔드로 보고(SSRF 안전), 단계 전환 이벤트를 측정.

---

## 8. 불변 조건 (Invariants)

- INV-05-01: 사용자 스케치/외부 레퍼런스/추상화/생성 이미지는 항상 시각적으로 구분된다. (User_Needs §11.1, §12.1)
- INV-05-02: 단순 스피너만 사용하는 로딩 화면은 존재하지 않는다. (§11.1)
- INV-05-03: AI 메시지는 인용 출처 또는 “가설” 배지 중 하나를 반드시 가진다. (§3.2; SPEC-01 INV-01-03)
- INV-05-04: Decision Panel과 Evidence Board는 모든 단계에서 노출된다. (§11.1)
- INV-05-05: UI 라벨/메시지는 i18n 키로만 출력된다. (작성자 지침)
- INV-05-06: UI는 실제 API/도메인 상태를 숨기거나 성공처럼 꾸미지 않는다. mock, placeholder, 표시용 fallback으로 작업 성공을 가장하지 않는다.
- INV-05-07: 사용자 워크스페이스와 관리자 콘솔은 같은 UX 검증 게이트(i18n, 접근성, 스켈레톤, 상태별 contract)를 통과해야 한다.

---

## 9. 위험과 대응 (Risks)

| 위험 (User_Needs §22) | 대응 |
|---|---|
| UX 복잡도 | 단계 바 + Decision Panel + 7-Board 표준화 |
| 자동 모드 블랙박스화 | 단계 스켈레톤 + 작업 로그 + aria-live |
| 사용자 스케치 손실 오해 | UI 차원의 “덮어쓰기 차단 + 새 버전 저장” 모달 |
| 라이선스 위험 무인지 | 카드 배지 + 비활성 액션 + 사유 표시 |
| 다국어 누락 | i18n 키 누락 시 CI 실패 |
| 접근성 회귀 | axe-core 등 자동 점검 (CI) |
| 화면 단계 누락 | 17단계 화면 매핑 + 단계별 contract snapshot + E2E 시나리오 |
| UI와 도메인 불변 조건 불일치 | `next_actions` 기반 액션 렌더링 + 상태별 검증 테스트 |

---

## 10. 의존성 (Dependencies)

- SPEC-01: SessionViewModel 메타 표준, ChatMessage/UserSketchAsset 필드
- SPEC-02: TrendInsight, ReferenceAsset, ReferenceAnalysis, UserSketchCard/ReferenceCard 분리
- SPEC-03: ConceptCandidate/Decision, AbstractionRule, GeneratedDesign, SpecDocument
- SPEC-04: 모델 정책 키 표시(생성 카드의 model_policy_key), AI 사용 고지 메타

---

## 11. 범위 외 (Out of Scope)

- 관리자 콘솔 UI 상세 소유권(SPEC-04 §6.4). 단, 공통 i18n/접근성/스켈레톤/디자인 토큰/상태 검증 표준은 본 SPEC을 따른다.
- 외부 디자인 툴(Figma 등) 임포트/익스포트
- 결제/플랜 화면

---

## 12. 추적 매트릭스 (Traceability)

| REQ ID | User_Needs 매핑 | 인수 기준 |
|---|---|---|
| REQ-05-LAYOUT-001~004 | §11.1, §11.2 | AC-05-L-001 |
| REQ-05-BOARD-002 | §3.2, §11.3 | (Chat 인용 표지) |
| REQ-05-VISUAL-001~002 | §11.1, §12.1 | AC-05-V-002 |
| REQ-05-SKETCH-001~003 | §11.4 | (3분할 검증) |
| REQ-05-SKETCH-004 | §22 | AC-05-K-003 |
| REQ-05-REF-001~003 | §11.5, §10.3 | AC-05-R-004 |
| REQ-05-SPEC-001~003 | §11.6 | AC-05-S-007 |
| REQ-05-LOADING-001~002 | §11.1 | AC-05-L-005 |
| REQ-05-EMPTY-001 | §12.2 | AC-05-E-006 |
| REQ-05-I18N-001~004 | 작성자 지침, §11 | AC-05-I-008, AC-05-A-009 |
| REQ-05-API-001 | SPEC-01 NFR-01-A11Y-001 | (메타 검증) |
| REQ-05-API-003~004 | §12.2, 사용자 추가 지시 | AC-05-C-011 |
| REQ-05-COMPLETE-001~004 | §11, §12, 사용자 추가 지시 | AC-05-C-010, AC-05-C-012 |

---

문서 종료. 본 SPEC은 SPEC-01~04의 산출물을 사용자에게 어떻게 노출할지에 대한 단일 기준이며, 모든 보드/패널은 단계 표시·근거·결정·시각 구분의 4대 원칙을 공통으로 따른다.
