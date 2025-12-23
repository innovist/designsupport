# Plan 11: AI 클라이언트 및 데이터 영속성 수정

**작성일**: 2025-12-22 15:30
**목적**: 세션 실패 원인 해결 및 데이터 영속성 구현

---

## 1. 문제 분석 (Root Cause Analysis)

### 1.1 세션 실패 원인 (에러 로그 분석)

```
Attempt 1 failed for chat completion with gemini-2.5-flash:
'GenerateContentResponse' object has no attribute 'usage_metadata'

Mock response for GLM glm-4.7 (zhipuai not installed)
Pipeline failed: JSON 파싱 실패
```

**에러 흐름:**
1. `pipeline_orchestrator.py:179` → `gemini_client.chat_completion()` 호출
2. `gemini_client.py:330` → `response.usage_metadata.__dict__` 접근 시 AttributeError
3. GLM 폴백 시도 → `zhipuai` 미설치로 Mock 응답 반환
4. Mock 응답이 유효한 JSON 아님 → 파싱 실패

### 1.2 진짜 원인 3가지

| 원인 | 위치 | 문제 | 레퍼런스 대비 |
|------|------|------|---------------|
| **Gemini 응답 처리 오류** | `gemini_client.py:168,247,330` | `response.usage_metadata` 속성 접근 시 AttributeError | 레퍼런스는 `response.text`만 사용 |
| **GLM API 구현 오류** | `glm_client.py` 전체 | `zhipuai` 모듈 사용 (잘못된 접근) | 레퍼런스는 OpenAI SDK + Z.AI base URL 사용 |
| **데이터 영속성 없음** | `projects.py:64`, `sessions.py:12` | 메모리 딕셔너리 저장 → 서버 재시작 시 소멸 | 레퍼런스는 SQLite 사용 |

### 1.3 Z.AI API 정보 (공식 문서 확인)

- **Base URL**: `https://api.z.ai/api/paas/v4` (일반) 또는 `https://api.z.ai/api/coding/paas/v4` (코딩)
- **인증**: HTTP Bearer (`Authorization: Bearer YOUR_API_KEY`)
- **SDK**: OpenAI 호환 (zhipuai 불필요)
- **사용법**: OpenAI SDK에 base_url만 변경

```python
# 올바른 Z.AI 사용법 (레퍼런스 gemini_service.py:460-540)
from openai import OpenAI
client = OpenAI(api_key=zai_api_key, base_url="https://api.z.ai/api/paas/v4")
response = client.chat.completions.create(model="glm-4.7", messages=[...])
```

---

## 2. 수정 대상 파일

### 2.1 AI 클라이언트 수정

| 파일 | 수정 내용 |
|------|----------|
| `ai_clients/gemini_client.py` | `response.usage_metadata` 접근 제거, `response.text`만 사용 |
| `ai_clients/glm_client.py` | 전면 재작성 - OpenAI SDK + Z.AI base URL 방식 |

### 2.2 데이터 영속성 구현

| 파일 | 수정 내용 |
|------|----------|
| `app/api/projects.py` | 메모리 → SQLite 전환 |
| `app/api/sessions.py` | 메모리 → SQLite 전환 |
| `app/models/` | 프로젝트/세션 ORM 모델 추가 |
| `app/core/database.py` | SQLite 연결 설정 추가 |

### 2.3 누락 기능 추가 (선택)

| 파일 | 설명 |
|------|------|
| `app/routers/youtube_channels.py` | YouTube 채널 관리 API |
| `app/models/youtube_channel.py` | YouTube 채널 모델 |

---

## 3. 수정 상세

### 3.1 gemini_client.py 수정

**현재 코드 (오류 발생):**
```python
# Line 168, 247, 330
result = GenerationResponse(
    text=response.text,
    model=model,
    usage_metadata=response.usage_metadata.__dict__ if response.usage_metadata else None,  # ERROR!
    ...
)
```

**수정 후 (레퍼런스 방식):**
```python
result = GenerationResponse(
    text=response.text,
    model=model,
    usage_metadata=None,  # 또는 getattr(response, 'usage_metadata', None)
    ...
)
```

### 3.2 glm_client.py 전면 재작성

**현재 코드 (잘못된 접근):**
```python
import zhipuai  # 잘못됨! Z.AI는 zhipuai 아님
zhipuai.api_key = api_key
response = zhipuai.model_api.invoke(...)
```

**수정 후 (레퍼런스 방식):**
```python
from openai import OpenAI

class ZAIProvider:
    BASE_URL = "https://api.z.ai/api/paas/v4"

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)

    def generate_content(self, prompt: str, model: str = "glm-4.7") -> str:
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
```

### 3.3 데이터 영속성 구현

**현재 코드 (메모리):**
```python
_projects_db: Dict[int, Dict[str, Any]] = {}  # 서버 재시작 시 소멸
```

**수정 후 (SQLite):**
```python
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.project import Project

@router.post("/")
async def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(**data.dict())
    db.add(project)
    db.commit()
    return project
```

---

## 4. 레퍼런스 비교

| 기능 | Fashion 프로젝트 | Cosmetic 레퍼런스 |
|------|-----------------|------------------|
| Gemini 응답 처리 | `response.usage_metadata.__dict__` 접근 | `response.text`만 사용 |
| GLM 폴백 | `zhipuai` 모듈 (미설치) | OpenAI SDK + Z.AI base URL |
| 데이터 저장 | 메모리 딕셔너리 | SQLite + SQLAlchemy |
| YouTube 채널 관리 | 없음 | `youtube_channels.py` 있음 |

---

## 5. 구현 우선순위

### Phase 1: AI 클라이언트 수정 (필수, 즉시)
1. `gemini_client.py` - `usage_metadata` 접근 제거
2. `glm_client.py` - OpenAI 호환 방식으로 재작성

### Phase 2: 데이터 영속성 (필수)
1. `app/core/database.py` - SQLite 연결 설정
2. `app/models/project.py`, `app/models/session.py` - ORM 모델
3. `app/api/projects.py`, `app/api/sessions.py` - DB 연동

### Phase 3: 추가 기능 (선택)
1. YouTube 채널 관리 기능 이식

---

## 6. 검증 계획

1. **Gemini 호출 테스트**: API 호출 → 응답 텍스트 정상 반환 확인
2. **GLM 폴백 테스트**: Gemini 실패 시 → Z.AI GLM 정상 응답 확인
3. **데이터 영속성 테스트**:
   - 프로젝트 생성 → 서버 재시작 → 프로젝트 유지 확인
   - 세션 생성 → 서버 재시작 → 세션 유지 확인
4. **파이프라인 전체 테스트**: 세션 생성 → 분석 완료까지 정상 동작

---

## 7. 참고 파일

**레퍼런스 (Cosmetic_case_gen):**
- `app/services/gemini_service.py:460-540` - ZAIProvider 클래스
- `app/utils/gemini_client.py:291-294` - 응답 처리 (response.text만 사용)
- `app/models/` - SQLAlchemy ORM 모델
- `app/routers/youtube_channels.py` - YouTube 채널 관리

**Fashion 프로젝트 (수정 대상):**
- `ai_clients/gemini_client.py:168,247,330` - usage_metadata 접근 제거
- `ai_clients/glm_client.py` - 전면 재작성
- `app/api/projects.py:64` - DB 전환
- `app/api/sessions.py:12` - DB 전환
