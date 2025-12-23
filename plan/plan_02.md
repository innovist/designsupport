# 계획서 (plan_02.md)
작성일시: 2025-12-20 23:27:06 KST
버전: v0.2

## 목표/범위
- 패션 트렌드 수집→AI 분석/집계→3개 콘셉트/보고서→프롬프트→이미지/도면 생성까지의 통합 파이프라인 설계.
- FastAPI + vanillaJS/vanillaCSS/HTML, ORM, 모듈/클래스 구조를 전제로 설계한다.

## 전제/제약
- 코드 작성 없이 문서 단계만 수행한다.
- 크롤러/오케스트레이션/AI 호출 방식은 레퍼런스 로직을 그대로 복사해 적용한다.
- 예외를 숨기지 않고 명시적으로 실패를 노출한다.

## 핵심 구성 요소 점검
- 입력/세션: 프롬프트+필터+참고 이미지 입력, 세션/버전 관리.
- 수집: 크롤러, 취소 토큰, 진행률, 에러 핸들러.
- 분석: gemini-2.5-flash/3-flash 분석 + glm-4.7 집계.
- 콘셉트/보고서: 3개 콘셉트, 근거 포함 보고서.
- 프롬프트: 모델별 프롬프트 템플릿/번역/네거티브.
- 이미지 생성: Z-Image/Seedream/Nano Banana 선택, 1차/2차 생성.
- 일관성: 디자인 ID, 참조 이미지, 스타일 토큰.
- 도면/패턴: 표준 치수 기반 초안.
- UI/UX: 입력→비교→선택→생성→다운로드.
- 운영: 알럿, 쿼터, 로그, 감사.

## 파이프라인/워크플로우 (상세)
1) 입력 분석: `input_service.py` 구조로 키워드/필터 추출.
2) 수집: `crawler_service.py` 구조로 다중 크롤러 실행/취소/진행률.
3) 정제: AI 기반 품질/관련성 분류로 필터링.
4) 분석: Gemini 2종 분석 후 GLM 4.7이 최종 집계/보고서.
5) 콘셉트: 3개 디자인 콘셉트 + 상세안 도출.
6) 프롬프트: 모델별 초상세 프롬프트 생성.
7) 이미지 생성: 1차 후보 생성 → 검증 → 2차 고품질 재생성.
8) 도면 생성: 표준 치수 기반 패턴 초안 산출.
9) 검토/선택: 사용자가 결과 선택 및 수정.
10) 저장/다운로드: 버전 묶음 저장 및 패키지 제공.

## 데이터 모델/스키마(요약)
- Project, Session, CrawlJob, RawItem, Comment, TrendInsight, Concept, PromptSpec,
  GenerationJob, ImageAsset, PatternDraft, Report, Version, ApiKey, AuditLog.

## 레퍼런스 복사/참고 상세
- 크롤링 오케스트레이션: `Cosmetic_case_gen/app/services/crawler_service.py` 구조 그대로 복사.
- 크롤러 유틸/래퍼: `Cosmetic_case_gen/crawlers/common.py`, `crawler_manager.py`, `total_crawler.py` 로직 복사.
- 파이프라인 단계 구성: `Cosmetic_case_gen/app/services/pipeline_orchestrator.py` 단계 흐름 참고.
- 입력 분석: `Cosmetic_case_gen/app/services/input_service.py`, `prompts/input_analysis.txt` 구조 복사 후 패션 도메인화.
- 니즈 추출: `prompts/needs_extraction.txt` 형식 유지, 패션 도메인으로 재작성.
- 프롬프트 최적화: `Ad_imageGen_win/ad_atelier/services/prompt/ai_prompt_optimizer.py` 그대로 적용.
- 모델 가용성: `Ad_imageGen_win/ad_atelier/services/model_detector.py` 구조 그대로 적용.
- 멀티모델 생성: `Ad_imageGen_win/ad_atelier/services/multi_model_generator.py` 1차/2차 구조 복사.
- 일관성 정책: `Ad_imageGen_win/ad_atelier/services/consistency_config.py` ref_type 정책 복사.
- 검증/개선: `Ad_imageGen_win/ad_atelier/services/generation_verifier.py` 검증 루프 복사.
- API 클라이언트: `comfyui_client.py`, `seedream_client.py`, `nano_banana_client.py` 엔드포인트/페이로드 그대로 적용.
- 키 관리: `gemini_key_manager.py`, `nano_banana_key_manager.py`, `bytedance_key_manager.py`, `zai_key_manager.py` 로직 복사.
- 폴백/알럿: `fallback_chain_manager.py`, `alert_service.py`, `response_ai.md` 흐름 반영.
- UI/UX 토큰: `static/css/design-system.css`, `templates/pages/input_studio.html` 레이아웃 참고.

## 상세 구현 계획 (Action Items)
[ ] 1) 프로젝트/세션/버전 모델과 저장 구조 확정(ORM 설계).
[ ] 2) 입력 분석 파이프라인 설계 및 키워드 출력 스키마 확정.
[ ] 3) 크롤러 오케스트레이션 로직을 레퍼런스 그대로 이식.
[ ] 4) 크롤러별 수집 메타/저장 규칙 통일 및 원문 보존.
[ ] 5) AI 기반 품질/관련성 필터링 로직 설계(규칙 기반 제거).
[ ] 6) Gemini 2종 분석 결과 포맷과 GLM 집계 스키마 정의.
[ ] 7) 보고서/콘셉트/프롬프트 생성 규칙을 패션 도메인으로 확정.
[ ] 8) 이미지 생성 파이프라인(모델 선택, 1차/2차, 검증 루프) 설계.
[ ] 9) 일관성 유지 전략(디자인 ID, 참조 이미지, 스타일 토큰) 확정.
[ ] 10) 도면/패턴 초안 규칙 및 표준 치수 테이블 확정.
[ ] 11) API/UX 플로우 설계(입력→분석→비교→다운로드).
[ ] 12) 폴백 체인/알럿/쿼터 표시 정책 확정.
[ ] 13) 감사 로그/버전 관리/다운로드 패키징 규칙 확정.
[ ] 14) 테스트 계획 수립(크롤링/분석/생성/일관성/성능).

## 테스트/검증 계획
- 크롤러 기능 테스트: 실제 수집/정제 결과 로그 확인.
- 모델 분석 테스트: 각 모델 출력 구조 일치성, 집계 결과 일관성 확인.
- 일관성 테스트: 동일 디자인의 전/후면/착장/도면 일치 검증.
- 성능 테스트: 크롤링/분석/생성 시간 측정 및 병목 분석.

## 품질/운영/보안
- 데이터 무결성 검증(해시/버전), 접근 제어, 감사 로그.
- API 비용/쿼터 모니터링 및 명시적 알럿.
- 에러는 숨기지 않고 원인 기반으로 처리.

## 리스크/엣지 케이스
- 데이터 부족/편향, 모델 간 의견 상충, 이미지 일관성 실패.
- 모델 API 실패/쿼터 초과, 표준 치수와 디자인 충돌.

## 결정 필요/오픈 질문
- 크롤링 대상 사이트 목록 및 우선순위는?
- 표준 치수 기준은 무엇으로 할 것인가?
- 결과 언어/보고서 포맷은 어떻게 할 것인가?
- 모델별 사용 우선순위/기본값은 무엇인가?

## 다음 단계 제안
- 핵심 크롤링 채널/치수 기준/언어 포맷을 먼저 결정.
- 모델 호출 방식/키 정책을 레퍼런스 기준으로 확정.
- UX 플로우(비교/선택/다운로드)를 와이어프레임으로 고정.

## 3회 이상 검토 기록
- 1차(구성요소 관점): 입력/수집/분석/생성/도면/UX 구성 누락 여부 점검.
- 2차(레퍼런스 관점): 복사/참고 대상 파일 매핑 정확성 검토.
- 3차(운영 관점): 알럿/쿼터/로그/버전 관리 흐름 보강.
- 4차(일관성 관점): 디자인 ID/참조 이미지/검증 루프 연결 보강.
