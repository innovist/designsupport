# Plan 12: Seedream 4.5 + Nano Banana Base/Pro 모델 최적화

**작성일**: 2025-12-22 18:58
**목적**: Seedream 4.5(BytePlus ModelArk)로 통일하고 Nano Banana는 목적/품질에 따라 base/pro를 선택하도록 정책과 구현을 정비한다.

---

## 1. 문제 분석

### 1.1 Seedream API 불일치
- 현재 seedream_client는 /generate 기반의 비공식 엔드포인트 사용
- BytePlus ModelArk 문서 기준 OpenAI 호환 `images/generations` 경로 필요
- Seedream 4.5 모델 ID(공식) 사용 필요

### 1.2 Nano Banana 모델 정책 부재
- nano_banana_client에 스케치/제품/패브릭 모델 하드코딩 존재
- Google GenAI 기준 base/pro 모델 구분 규칙 없음
- 목적/품질 기반 선택 정책 부재

---

## 2. 설계 방향

1) **Seedream 4.5 고정**
- 기본 모델: seedream-4.5 (공식 모델 ID 매핑)
- BytePlus ModelArk OpenAI-compatible API 적용

2) **Nano Banana base/pro 정책**
- 기본: base(비용 최소)
- 고품질/참조 이미지/최종 이미지: pro
- 스케치/레이아웃/패턴 등 단순 출력은 base 유지

3) **모델명 하드코딩 제거**
- settings_storage.py에 이미지 모델 목록/매핑 정의
- 코드에서는 설정 함수 호출로 모델 결정

---

## 3. 수정 대상

- `app/core/settings_storage.py`
  - 이미지 모델 목록 업데이트
  - Seedream/Nano Banana 모델명/ID 매핑 함수 추가
- `app/core/config.py`
  - Seedream 기본 API URL을 BytePlus ModelArk 기준으로 정렬
- `ai_clients/seedream_client.py`
  - OpenAI 호환 이미지 생성 API로 변경
  - Seedream 4.5 모델 ID 매핑 적용
- `ai_clients/nano_banana_client.py`
  - base/pro 모델 선택 로직 적용
  - Google GenAI 모델 ID 매핑 정비

---

## 4. 테스트 계획

1) Seedream 4.5 이미지 생성 호출
   - 실제 API 호출 확인
   - 이미지 bytes 반환 확인
2) Nano Banana base/pro 호출
   - base(Flash)와 pro(3 Pro Image) 모델 선택 로그 확인
   - 실제 이미지 생성 확인
3) 파이프라인 이미지 생성 단계 확인
   - 모델 선택 정책 적용 확인

---

## 5. 리스크

- BytePlus API 엔드포인트 지역(서울/싱가포르) 불일치 가능
- Nano Banana Pro 모델명과 비용 정책 불일치 시 호출 실패 가능

---

## 6. 완료 기준

- Seedream 4.5 정상 호출 성공
- Nano Banana base/pro 정책이 목적/품질에 따라 선택됨
- 파이프라인 이미지 생성 성공 및 로그 증빙
