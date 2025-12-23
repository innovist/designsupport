# TODO (todo_02.md)
작성일시: 2025-12-20 23:27:06 KST
버전: v0.2

## 0. 결정/전제 확정
- [ ] 크롤링 대상 사이트 목록과 우선순위를 확정한다.
- [ ] 표준 치수 기준(S/M/L 또는 국제 표준)을 확정한다.
- [ ] 결과 언어(한/영) 및 보고서 포맷을 확정한다.
- [ ] 이미지 생성 우선순위(의상 단품 vs 착장)를 확정한다.

## 1. 데이터 모델/저장소
- [ ] Project/Session/Version 스키마를 정의한다.
- [ ] RawItem/Comment/TrendInsight/Concept/PromptSpec 스키마를 정의한다.
- [ ] GenerationJob/ImageAsset/PatternDraft/Report 스키마를 정의한다.
- [ ] ApiKey/AuditLog 스키마를 정의한다.

## 2. 입력/키워드 분석
- [ ] `reference/Cosmetic_case_gen/app/services/input_service.py` 구조를 복사해 InputService를 설계한다.
- [ ] `reference/Cosmetic_case_gen/prompts/input_analysis.txt`를 패션 도메인으로 재작성한다.
- [ ] 입력 분석 결과 JSON 스키마(키워드/우선순위)를 확정한다.

## 3. 크롤링 파이프라인(레퍼런스 그대로 이식)
- [ ] `reference/Cosmetic_case_gen/app/services/crawler_service.py`의 ThreadPool+취소 토큰 구조를 그대로 복사한다.
- [ ] `reference/Cosmetic_case_gen/crawlers/*` 사이트 크롤러를 그대로 이식한다.
- [ ] `reference/Cosmetic_case_gen/crawlers/common.py` 날짜/유틸 함수를 그대로 복사한다.
- [ ] `reference/Cosmetic_case_gen/crawlers/crawler_manager.py` 관리 로직을 그대로 복사한다.
- [ ] `reference/Cosmetic_case_gen/crawlers/total_crawler.py` 함수 래핑 패턴을 그대로 복사한다.
- [ ] 수집 메타(게시글/댓글/조회수/좋아요/작성일/키워드)를 저장한다.
- [ ] 진행률/취소/에러 로그가 UI로 전달되도록 설계한다.

## 4. 정제/분석/집계
- [ ] 규칙 기반 필터 대신 AI 기반 품질/관련성 분류 흐름을 설계한다.
- [ ] `reference/Cosmetic_case_gen/app/services/analysis_service.py` 비동기 분석 흐름을 복사한다.
- [ ] gemini-2.5-flash 분석 출력 포맷(JSON)을 정의한다.
- [ ] gemini-3-flash 분석 출력 포맷(JSON)을 정의한다.
- [ ] glm-4.7 집계 규칙(상충/합의/근거)을 정의한다.
- [ ] `reference/Cosmetic_case_gen/prompts/needs_extraction.txt`를 패션 도메인으로 재작성한다.

## 5. 콘셉트/보고서/프롬프트
- [ ] 3개 콘셉트 필드(컨셉명/타겟/시즌/실루엣/소재/색/디테일/근거)를 고정한다.
- [ ] 보고서 섹션(요약/근거/트렌드/리스크/대안)을 고정한다.
- [ ] 콘셉트별 프롬프트 템플릿을 정의한다.
- [ ] `reference/Ad_imageGen_win/ad_atelier/services/prompt/ai_prompt_optimizer.py` 로직을 그대로 복사한다.

## 6. 이미지 생성/일관성
- [ ] `reference/Ad_imageGen_win/ad_atelier/services/model_detector.py` 가용성 점검 로직을 복사한다.
- [ ] `reference/Ad_imageGen_win/ad_atelier/services/multi_model_generator.py` 1차/2차 생성 구조를 복사한다.
- [ ] `reference/Ad_imageGen_win/ad_atelier/services/consistency_config.py` ref_type 정책을 복사한다.
- [ ] 디자인 ID/참조 이미지/스타일 토큰 저장 규칙을 정의한다.
- [ ] `reference/Ad_imageGen_win/ad_atelier/services/api_clients/comfyui_client.py` 호출 방식 그대로 적용한다.
- [ ] `reference/Ad_imageGen_win/ad_atelier/services/api_clients/seedream_client.py` 호출 방식 그대로 적용한다.
- [ ] `reference/Ad_imageGen_win/ad_atelier/services/api_clients/nano_banana_client.py` 호출 방식 그대로 적용한다.
- [ ] 전/후면 의상 → 착장 모델 → 배경/포즈 순서로 참조 연계를 정의한다.

## 7. 검증/폴백/알럿
- [ ] `reference/Ad_imageGen_win/ad_atelier/services/generation_verifier.py` 검증 루프를 복사한다.
- [ ] `reference/Ad_imageGen_win/ad_atelier/services/edit_pipelines/fallback_chain_manager.py` 폴백 체인을 복사한다.
- [ ] `reference/Ad_imageGen_win/ad_atelier/services/alert_service.py` 알럿 기록 로직을 복사한다.
- [ ] `reference/Ad_imageGen_win/response_ai.md`의 알럿/폴백 UX 흐름을 UI에 반영한다.

## 8. 키 관리/설정
- [ ] `reference/Ad_imageGen_win/ad_atelier/services/key_manager/gemini_key_manager.py` 로직을 복사한다.
- [ ] `reference/Ad_imageGen_win/ad_atelier/services/key_manager/nano_banana_key_manager.py` 로직을 복사한다.
- [ ] `reference/Ad_imageGen_win/ad_atelier/services/key_manager/bytedance_key_manager.py` 로직을 복사한다.
- [ ] `reference/Ad_imageGen_win/ad_atelier/services/key_manager/zai_key_manager.py` 로직을 복사한다.
- [ ] 키 로테이션/마스킹/쿼터 표시 UX를 설계한다.

## 9. 도면/패턴
- [ ] 표준 치수 테이블과 기준점을 확정한다.
- [ ] 앞/뒤 패턴 초안 출력 포맷(SVG/PNG/PDF)을 정의한다.
- [ ] 도면 라벨/치수 표시 규칙을 정의한다.

## 10. API/백엔드 플로우
- [ ] 프로젝트/세션 생성 API를 정의한다.
- [ ] 크롤링 시작/중지/진행률 API를 정의한다.
- [ ] 분석/보고서/콘셉트 조회 API를 정의한다.
- [ ] 이미지/도면 생성 요청 및 상태 조회 API를 정의한다.
- [ ] 다운로드 패키징 API를 정의한다.
- [ ] 장시간 작업용 큐/이벤트 흐름을 정의한다.

## 11. UI/UX 구현 계획
- [ ] `reference/Cosmetic_case_gen/static/css/design-system.css` 토큰을 그대로 복사한다.
- [ ] `reference/Cosmetic_case_gen/templates/pages/input_studio.html` 입력 흐름을 참고해 화면 구성한다.
- [ ] 진행률/에러/폴백/알럿/쿼터 UI 패널을 설계한다.
- [ ] 콘셉트 비교/선택/재생성 UI를 설계한다.
- [ ] 모바일 1열 레이아웃 및 터치 영역 기준을 반영한다.

## 12. 보안/감사/운영
- [ ] 민감정보 마스킹 정책을 정의한다.
- [ ] AuditLog 기록 기준(입력/생성/다운로드)을 정의한다.
- [ ] 실패/예외는 사용자에게 명확히 노출하도록 설계한다.

## 13. 테스트/검증
- [ ] 크롤러 실제 수집 테스트 시나리오를 작성한다.
- [ ] Gemini/GLM 분석 결과 스키마 검증 테스트를 작성한다.
- [ ] 이미지 생성 1차/2차/검증 루프 테스트를 작성한다.
- [ ] 전/후면/착장/도면 일관성 검증 테스트를 작성한다.
- [ ] 성능/병목 측정 테스트를 작성한다.

## 14. 문서/검토
- [ ] 요구사항 문서와 계획/할일 문서 동기화를 확인한다.
- [ ] 1차 논리 검토 기록을 남긴다.
- [ ] 2차 레퍼런스 매핑 검토 기록을 남긴다.
- [ ] 3차 UX/운영 검토 기록을 남긴다.
