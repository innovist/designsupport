# Design Support System - API Documentation
**Version:** 2.0.0
**Base URL:** `https://api.design-support.com`

---

## 1. 개요

Design Support System은 근거 기반 디자인 창작 지원을 위한 RESTful API를 제공합니다. 목적 구조화, 트렌드 근거 조사, 컨셉 결정, 레퍼런스 추상화, 시각화, 스펙 문서화 파이프라인을 지원합니다.

### 1.1. 주요 기능
- **프로젝트/세션 관리**: 디자인 프로젝트와 세션의 전체 수명 주기 관리
- **브리프 구조화**: 자연어 목적을 구조화된 디자인 브리프로 변환
- **트렌드 조사**: 출처 기반 트렌드 근거 수집과 인사이트 생성
- **컨셉 관리**: 컨셉 후보 생성, 평가, 결정 기록
- **레퍼런스 검색**: 웹/이미지/문서 기반 레퍼런스 검색과 분석
- **사용자 스케치**: 스케치 업로드, AI 해석, 구체화
- **추상화 엔진**: 레퍼런스를 디자인 문법(형태/구조/재질/상징)으로 변환
- **이미지 생성**: 추상화 규칙 기반 스케치/변형 이미지 생성
- **스펙 문서**: 모든 결정 근거를 포함한 스펙 문서 생성

### 1.2. 인증
```http
Authorization: Bearer {access_token}
```

### 1.3. API 버전
- 현재 버전: v1
- URL 형식: `/api/v1/{resource}`

---

## 2. 공통 응답 형식

### 2.1. 성공 응답
```json
{
  "success": true,
  "data": {},
  "metadata": {
    "timestamp": "2026-05-07T12:00:00Z",
    "request_id": "req_123456789"
  }
}
```

### 2.2. 에러 응답
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {}
  }
}
```

### 2.3. HTTP 상태 코드
| 코드 | 의미 | 설명 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 201 | Created | 리소스 생성 성공 |
| 400 | Bad Request | 잘못된 요청 |
| 401 | Unauthorized | 인증 실패 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 429 | Too Many Requests | 요청 초과 |
| 500 | Internal Server Error | 서버 오류 |

---

## 3. 프로젝트 API

### 3.1. 프로젝트 생성
**POST** `/api/v1/projects/`

```json
{
  "name": "2026 S/S 여성복 컬렉션",
  "domain": "fashion",
  "description": "지속가능성을 주제로 한 봄여름 컬렉션",
  "workspace_id": "ws_123456"
}
```

### 3.2. 프로젝트 목록
**GET** `/api/v1/projects/?workspace_id={id}&status={status}`

### 3.3. 프로젝트 상세
**GET** `/api/v1/projects/{project_id}/`

---

## 4. 세션 API

### 4.1. 세션 생성
**POST** `/api/v1/sessions/`

```json
{
  "project_id": "proj_123456",
  "mode": "collaborative",
  "purpose": "2026 S/S 여성복 컬렉션의 핵심 무드와 룩 방향 탐색"
}
```

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| project_id | string | O | 프로젝트 ID |
| mode | string | O | collaborative / auto |
| purpose | string | O | 디자인 목적 (자연어) |

### 4.2. 세션 상태 조회
**GET** `/api/v1/sessions/{session_id}/`

```json
{
  "success": true,
  "data": {
    "session_id": "sess_123456",
    "mode": "collaborative",
    "current_stage": "concepting",
    "progress": {
      "brief": "completed",
      "trend_research": "completed",
      "concept_candidates": "in_progress",
      "reference_search": "pending",
      "abstraction": "pending",
      "generation": "pending",
      "spec_document": "pending"
    },
    "created_at": "2026-05-07T10:00:00Z"
  }
}
```

---

## 5. 브리프 API

### 5.1. 브리프 생성
**POST** `/api/v1/sessions/{session_id}/brief/`

```json
{
  "purpose": "휴대폰 거치대를 자연물 컨셉으로 디자인",
  "domain": "industrial",
  "target": "직장인, 프리미엄 사용자",
  "context": "사무실 책상 위 오브젝트",
  "constraints": ["자연적인 느낌", "책상 위 오브젝트처럼"]
}
```

### 5.2. 추가 질문 생성
**GET** `/api/v1/sessions/{session_id}/brief/questions/`

AI가 브리프의 누락 필드를 분석해 질문을 생성합니다.

### 5.3. 추가 질문 답변
**POST** `/api/v1/sessions/{session_id}/brief/answers/`

```json
{
  "answers": [
    {"question_id": "q_001", "answer": "사무실"},
    {"question_id": "q_002", "answer": "세라믹, 3D 프린팅"},
    {"question_id": "q_003", "answer": "세로 거치, 충전 케이블 통과"}
  ]
}
```

---

## 6. 사용자 스케치 API

### 6.1. 스케치 업로드
**POST** `/api/v1/sessions/{session_id}/sketches/`

(multipart/form-data)

```
file: [스케치 파일]
sketch_type: rough | structure | style | mixed
description: "휴대폰 거치대 러프 스케치 - 삼각형 실루엣"
```

원본 파일은 불변 저장되며, 분석 결과는 별도로 생성됩니다.

### 6.2. 스케치 분석 조회
**GET** `/api/v1/sessions/{session_id}/sketches/{sketch_id}/analysis/`

```json
{
  "success": true,
  "data": {
    "sketch_id": "sketch_001",
    "analysis": {
      "intent": "삼각형 실루엣의 휴대폰 거치대",
      "form_elements": ["삼각형 실루엣", "경사면", "받침 각도"],
      "structure": "후면 지지대 경사 구조",
      "unclear_points": ["정확한 받침 각도", "케이블 통과 방식"],
      "refinement_directions": [
        "능선 라인을 후면 지지대로 구체화",
        "산맥 중첩을 단차로 변형"
      ]
    },
    "status": "pending_user_confirmation"
  }
}
```

### 6.3. 스케치 분석 승인
**POST** `/api/v1/sessions/{session_id}/sketches/{sketch_id}/confirm/`

---

## 7. 트렌드 조사 API

### 7.1. 트렌드 조사 시작
**POST** `/api/v1/sessions/{session_id}/trend-research/`

```json
{
  "domain": "industrial",
  "keywords": ["자연물 오브젝트", "산 컨셉 제품", "미니멀 거치대"],
  "sources": ["core77", "dezeen", "behance"]
}
```

모든 결과는 출처 URL, 발행일, 수집일과 함께 저장됩니다.

### 7.2. 트렌드 인사이트 조회
**GET** `/api/v1/sessions/{session_id}/trend-research/insights/`

```json
{
  "success": true,
  "data": {
    "insights": [
      {
        "id": "insight_001",
        "summary": "자연물 형태를 차용한 데스크 오브젝트 트렌드 확산",
        "keywords": ["바이오필릭 디자인", "자연물 오브젝트"],
        "evidence": [
          {
            "source": "Core77",
            "url": "https://...",
            "published_at": "2026-04-15",
            "quote": "..."
          }
        ],
        "confidence": 0.85,
        "freshness_score": 0.92
      }
    ]
  }
}
```

---

## 8. 컨셉 API

### 8.1. 컨셉 후보 생성
**POST** `/api/v1/sessions/{session_id}/concepts/generate/`

```json
{
  "count": 4,
  "based_on": "brief_and_trends"
}
```

### 8.2. 컨셉 후보 목록
**GET** `/api/v1/sessions/{session_id}/concepts/`

```json
{
  "success": true,
  "data": {
    "concepts": [
      {
        "id": "concept_001",
        "name": "산",
        "description": "안정감, 자연, 능선, 높이",
        "score": 0.88,
        "evidence": ["바이오필릭 트렌드 근거", "지지 구조 연관성"],
        "risks": ["장식적으로 흐를 위험"],
        "status": "pending"
      }
    ]
  }
}
```

### 8.3. 컨셉 결정
**POST** `/api/v1/sessions/{session_id}/concepts/{concept_id}/decide/`

```json
{
  "decision": "adopted",
  "reason": "지지 구조와 잘 연결되고 바이오필릭 트렌드와 부합"
}
```

decision: adopted | deferred | rejected | explore_more

---

## 9. 레퍼런스 API

### 9.1. 레퍼런스 검색
**POST** `/api/v1/sessions/{session_id}/references/search/`

```json
{
  "query": "산 능선 제품 오브젝트",
  "categories": ["Nature", "Product", "Architecture"],
  "max_results": 30
}
```

### 9.2. 레퍼런스 저장
**POST** `/api/v1/sessions/{session_id}/references/`

```json
{
  "url": "https://...",
  "title": "산을 형상화한 데스크 오브젝트",
  "category": "Product",
  "source_type": "web"
}
```

### 9.3. 레퍼런스 분석
**GET** `/api/v1/sessions/{session_id}/references/{ref_id}/analysis/`

```json
{
  "success": true,
  "data": {
    "relevance_score": 0.82,
    "form_grammar": "삼각 실루엣, 경사 라인",
    "structure_grammar": "경사 지지, 레이어 중첩",
    "material_grammar": "무광 표면, 자연 소재",
    "symbolism": "안정감, 고요함, 자연",
    "copyright_risk": "low",
    "abstraction_potential": "high"
  }
}
```

---

## 10. 추상화 API

### 10.1. 추상화 규칙 생성
**POST** `/api/v1/sessions/{session_id}/abstraction/generate/`

```json
{
  "reference_ids": ["ref_001", "ref_002"],
  "sketch_id": "sketch_001",
  "axes": ["form", "structure", "surface", "meaning"]
}
```

### 10.2. 추상화 규칙 조회
**GET** `/api/v1/sessions/{session_id}/abstraction/`

```json
{
  "success": true,
  "data": {
    "rules": [
      {
        "id": "rule_001",
        "axis": "form",
        "observation": "삼각 실루엣, 능선 라인",
        "application": "후면 지지대의 경사 실루엣",
        "source_refs": ["ref_001", "ref_003"]
      },
      {
        "id": "rule_002",
        "axis": "structure",
        "observation": "하중을 받는 경사면",
        "application": "휴대폰 무게를 받는 받침 각도",
        "source_refs": ["ref_001"]
      }
    ]
  }
}
```

---

## 11. 이미지 생성 API

### 11.1. 스케치/변형 이미지 생성
**POST** `/api/v1/sessions/{session_id}/generation/generate/`

```json
{
  "type": "abstraction_sketch",
  "abstraction_rule_ids": ["rule_001", "rule_002"],
  "sketch_id": "sketch_001",
  "variations": 3,
  "model_policy": "image_generation"
}
```

type: abstraction_sketch | refinement | variation | domain_application

모든 생성은 최소 1개 이상의 브리프, 컨셉, 추상화 규칙과 연결되어야 합니다.

### 11.2. 생성 결과 조회
**GET** `/api/v1/sessions/{session_id}/generation/`

```json
{
  "success": true,
  "data": {
    "designs": [
      {
        "id": "design_001",
        "type": "abstraction_sketch",
        "image_url": "https://...",
        "linked_rules": ["rule_001", "rule_002"],
        "linked_sketch": "sketch_001",
        "linked_concept": "concept_001",
        "model_used": "gemini-2.5-flash",
        "created_at": "2026-05-07T14:00:00Z"
      }
    ]
  }
}
```

---

## 12. 스펙 문서 API

### 12.1. 스펙 문서 생성
**POST** `/api/v1/sessions/{session_id}/spec/`

```json
{
  "include_sections": [
    "brief", "trend_evidence", "concept_candidates",
    "concept_decision", "user_sketches", "reference_board",
    "abstraction_rules", "designs", "final_comparison",
    "domain_spec", "sources_and_licenses"
  ]
}
```

### 12.2. 스펙 문서 조회
**GET** `/api/v1/sessions/{session_id}/spec/`

### 12.3. 스펙 문서 버전 관리
**GET** `/api/v1/sessions/{session_id}/spec/versions/`

### 12.4. 스펙 문서 승인
**POST** `/api/v1/sessions/{session_id}/spec/{version}/approve/`

---

## 13. 관리자 API

### 13.1. 트렌드 출처 관리
- **GET** `/api/v1/admin/trend-sources/`
- **POST** `/api/v1/admin/trend-sources/`
- **PATCH** `/api/v1/admin/trend-sources/{source_id}/`

### 13.2. 모델 카탈로그 관리
- **GET** `/api/v1/admin/model-providers/`
- **POST** `/api/v1/admin/model-providers/`
- **GET** `/api/v1/admin/model-catalog/`
- **POST** `/api/v1/admin/feature-model-policies/`

### 13.3. 감사 로그
- **GET** `/api/v1/admin/audit-logs/?user={id}&action={type}&from={date}&to={date}`

---

## 14. Decision Log

모든 컨셉 선택, 레퍼런스 승인/제외, 변형안 선택은 Decision Log에 자동 기록됩니다.

**GET** `/api/v1/sessions/{session_id}/decisions/`

```json
{
  "success": true,
  "data": {
    "decisions": [
      {
        "id": "dec_001",
        "stage": "concept",
        "decision_type": "adopted",
        "target_id": "concept_001",
        "decided_by": "user",
        "reason": "지지 구조와 잘 연결",
        "evidence": ["insight_001", "insight_003"],
        "alternatives": ["concept_002", "concept_003"],
        "created_at": "2026-05-07T11:30:00Z"
      }
    ]
  }
}
```

---

## 15. 에러 코드

| 코드 | 의미 | 해결 방법 |
|------|------|----------|
| AUTH_001 | 잘못된 API 키 | 유효한 API 키 사용 |
| AUTH_002 | 만료된 토큰 | 토큰 갱신 |
| AUTH_003 | 워크스페이스 권한 없음 | 권한 확인 |
| RATE_001 | 요청 초과 | 요청 간격 조정 |
| SESSION_001 | 세션 없음 | 세션 ID 확인 |
| CONCEPT_001 | 컨셉 후보 없음 | 브리프/트렌드 확인 |
| REF_001 | 레퍼런스 출처 없음 | URL 확인 |
| REF_002 | 라이선스 위험 | 추상화 전용으로 처리 |
| GEN_001 | 생성 실패 | 파라미터 확인 후 재시도 |
| GEN_002 | 모델 사용 불가 | 관리자 모델 정책 확인 |
| SKETCH_001 | 스케치 분석 실패 | 파일 형식 확인 |
| SPEC_001 | 스펙 생성 불가 | 필수 단계 완료 여부 확인 |

---

*본 문서는 시스템 변경사항에 따라 지속적으로 업데이트됩니다.*
