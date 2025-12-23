# Todo 12: Seedream 4.5 + Nano Banana Base/Pro 모델 최적화

**작성일**: 2025-12-22 18:58
**관련 계획**: plan_12.md

---

## Phase 1: 모델 설정 정비
- [x] `app/core/settings_storage.py` 이미지 모델 목록/매핑 업데이트
- [x] 이미지 모델 선택 함수 추가 (Seedream/Nano Banana)

## Phase 2: Seedream 4.5 적용
- [x] `app/core/config.py` Seedream 기본 API URL 정비
- [x] `ai_clients/seedream_client.py` OpenAI 호환 이미지 생성 API로 변경
- [x] Seedream 4.5 모델 ID 매핑 적용

## Phase 3: Nano Banana base/pro 정책 적용
- [x] `ai_clients/nano_banana_client.py` base/pro 선택 로직 적용
- [x] Google GenAI 모델 ID 매핑 정비

## Phase 4: 테스트
- [ ] Seedream 4.5 실제 호출 테스트
- [x] Nano Banana base/pro 실제 호출 테스트
- [x] 파이프라인 이미지 생성 단계 테스트
