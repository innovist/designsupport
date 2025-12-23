# Todo 11: AI 클라이언트 및 데이터 영속성 수정

**작성일**: 2025-12-22 15:30
**관련 계획**: plan_11.md

---

## Phase 1: AI 클라이언트 수정 (필수, 즉시)

### 1.1 Gemini 클라이언트 수정
- [x] `ai_clients/gemini_client.py:168` - `usage_metadata` 접근 제거
- [x] `ai_clients/gemini_client.py:247` - `usage_metadata` 접근 제거
- [x] `ai_clients/gemini_client.py:330` - `usage_metadata` 접근 제거
- [x] `safety_ratings` 접근도 안전하게 처리 (hasattr 또는 try-except)
- [x] 레퍼런스 방식으로 단순화: `response.text`만 사용
- [x] 문법 검증 실행

### 1.2 GLM 클라이언트 재작성
- [x] `ai_clients/glm_client.py` - zhipuai 의존성 제거
- [x] `ZAIProvider` 클래스 구현 (OpenAI SDK + Z.AI base URL)
  - Base URL: `https://api.z.ai/api/paas/v4`
  - 인증: HTTP Bearer
  - 모델: glm-4.7, glm-4-flash
- [x] `generate_content()` 메서드 구현
- [x] `chat_completion()` 메서드 구현
- [x] 에러 핸들링 및 재시도 로직
- [x] 문법 검증 실행

### 1.3 파이프라인 오케스트레이터 수정
- [x] `app/services/pipeline_orchestrator.py:186-198` - GLM 폴백 로직 업데이트
- [x] ZAIProvider 사용하도록 변경
- [x] 문법 검증 실행

### 1.4 Phase 1 검증
- [x] Gemini 단독 호출 테스트
- [x] GLM 단독 호출 테스트
- [x] Gemini 실패 → GLM 폴백 테스트
- [x] 파이프라인 키워드 추출 테스트

---

## Phase 2: 데이터 영속성 (필수)

### 2.1 데이터베이스 설정
- [x] `app/core/database.py` 생성 (SQLite 연결 설정)
- [x] SQLAlchemy 세션 관리 함수 추가
- [x] 데이터베이스 파일 경로 설정 (storage/fashion.db)

### 2.2 ORM 모델 생성
- [x] `app/models/project.py` - Project 모델
- [x] `app/models/session.py` - Session 모델
- [x] `app/models/__init__.py` 업데이트
- [ ] Alembic 마이그레이션 설정 (선택)

### 2.3 프로젝트 API 수정
- [x] `app/api/projects.py` - 메모리 저장소 제거
- [x] SQLAlchemy 세션 의존성 주입 추가
- [x] CRUD 함수 DB 연동으로 변경
- [x] 기존 응답 스키마 유지

### 2.4 세션 API 수정
- [x] `app/api/sessions.py` - 메모리 저장소 제거
- [x] SQLAlchemy 세션 의존성 주입 추가
- [x] CRUD 함수 DB 연동으로 변경
- [x] 파이프라인 결과 저장 로직 추가

### 2.5 Phase 2 검증
- [x] 프로젝트 CRUD 테스트 (test_fashion.db)
- [x] 세션 CRUD 테스트 (test_fashion.db)
- [ ] 서버 재시작 후 데이터 유지 확인
- [ ] 파이프라인 결과 저장 확인

---

## Phase 3: 추가 기능 (선택)

### 3.1 YouTube 채널 관리
- [ ] `app/models/youtube_channel.py` 복사 (레퍼런스에서)
- [ ] `app/routers/youtube_channels.py` 복사 (레퍼런스에서)
- [ ] `app/api/routes.py`에 라우터 등록
- [ ] 프론트엔드 UI 추가

---

## 검증 체크리스트

### AI 클라이언트 검증
- [x] `python -m py_compile ai_clients/gemini_client.py` 통과
- [x] `python -m py_compile ai_clients/glm_client.py` 통과
- [x] Gemini API 호출 → 응답 텍스트 정상
- [x] Z.AI GLM API 호출 → 응답 텍스트 정상
- [x] 폴백 로직 정상 동작

### 데이터 영속성 검증
- [x] `python -m py_compile app/core/database.py` 통과
- [x] `python -m py_compile app/api/projects.py` 통과
- [x] `python -m py_compile app/api/sessions.py` 통과
- [ ] 프로젝트 생성 → 서버 재시작 → 데이터 유지
- [ ] 세션 생성 → 서버 재시작 → 데이터 유지

### 전체 파이프라인 검증
- [ ] 프로젝트 생성
- [ ] 세션 생성 + 자동 시작
- [x] 키워드 추출 성공
- [x] 데이터 수집 성공
- [x] 분석 완료
- [ ] 결과 저장 및 조회

---

## 우선순위 요약

1. **즉시**: Phase 1.1, 1.2 (AI 클라이언트 수정) - 세션 실패 해결
2. **중요**: Phase 2 (데이터 영속성) - 데이터 소멸 방지
3. **선택**: Phase 3 (YouTube 채널) - 기능 확장

---

## 참고

**레퍼런스 파일 위치:**
- Gemini 응답 처리: `reference/Cosmetic_case_gen/app/utils/gemini_client.py:291-294`
- ZAIProvider: `reference/Cosmetic_case_gen/app/services/gemini_service.py:460-540`
- DB 설정: `reference/Cosmetic_case_gen/app/core/database.py`
- ORM 모델: `reference/Cosmetic_case_gen/app/models/`
