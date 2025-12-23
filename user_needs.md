# 요구사항 분석서 (user_needs.md)
작성일시: 2025-12-20 23:52:38 KST
버전: v0.4

## 1. 목적/범위
- 패션 트렌드 데이터 수집 → AI 분석/집계 → 3개 디자인 콘셉트/보고서 → 초상세 프롬프트 → 이미지/도면 생성까지 end-to-end 파이프라인 구현.
- 의상 디자인, 모델 착장 이미지, 도면/패턴 초안을 하나의 디자인 ID로 일관성 있게 묶어 제공.
- 웹/앱 확장 가능한 모듈화 구조, ORM 기반 데이터 모델, FastAPI + vanillaJS/vanillaCSS/HTML 전제.

## 2. 사용자/이해관계자
- 기획자: 트렌드 근거가 포함된 보고서/콘셉트 비교 자료 필요.
- 디자이너: 재현 가능한 프롬프트, 소재/색/실루엣/디테일 설명 필요.
- 제작자: 기본 치수/도면 초안과 제작 참고 정보 필요.
- 운영자: 비용/쿼터/로그/품질 지표 및 재생성 이력 관리 필요.

## 3. 핵심 유스케이스 흐름
1) 프로젝트/세션 생성, 입력(프롬프트 + 성별/계절/연령/지역 + 참고 이미지).
2) 입력 분석 → 크롤링 키워드 생성 → 수집 채널/기간/수량 설정.
3) 크롤러로 데이터 수집 → 정제/중복 제거/품질 점수화 → 저장.
4) gemini-2.5-flash/3-flash/glm-4.7 분석 → glm-4.7 최종 집계 보고서 생성.
5) 3개 디자인 콘셉트 + 상세안 + 근거 제시.
6) 콘셉트별 초상세 프롬프트 생성(영어 변환 포함).
7) 이미지 생성(전/후면, 착장, 배경/포즈) + AI 검증 + 개선 재생성.
8) 도면/패턴 초안 생성(표준 치수 기준) → 결과 묶음/버전 저장.
9) 사용자 선택/수정 → 재생성.
10) 결과물 다운로드 및 외부 연동 API 제공.

## 4. 기능 요구사항 (FR)
FR-01. 프로젝트/세션 단위로 입력과 결과를 관리한다.
FR-02. 프롬프트와 기본 필터(성별/계절/연령/지역) 및 참고 이미지를 입력받는다.
FR-03. 입력 분석으로 크롤링 키워드를 AI가 생성한다.
FR-04. 사용자가 크롤러/기간/수집량/채널을 선택할 수 있어야 한다.
FR-05. 크롤러 오케스트레이션/스레딩/취소/진행률 로직은 reference와 동일 구조로 구현한다.
FR-06. 수집 데이터는 게시글/댓글/메타데이터를 포함해 저장한다.
FR-07. 중복 제거/노이즈 필터/품질 점수화는 AI 기반으로 수행한다.
FR-08. gemini-2.5-flash와 gemini-3-flash와 glm-4.7이 독립 분석 결과를 생성한다.
FR-09. 이후 glm-4.7이 상충점/합의점/근거를 포함해 최종 집계 보고서를 생성한다.
FR-10. 의상 종류/컨셉/색상/소재/실루엣/디테일을 포함한 3개 콘셉트를 제안한다.
FR-11. 트렌드 흐름과 근거(source_id)를 포함한 보고서를 제공한다.
FR-12. 콘셉트별 초상세 이미지/도면 프롬프트를 생성한다.
FR-13. 이미지 생성 모델(Z-Image-turbo, Seedream 4.5, Nano Banana)을 사용자가 선택한다.
FR-14. 디자인 ID/참조 이미지/스타일 토큰으로 일관성을 유지한다.
FR-15. 1차 후보 생성 → AI 검증 → 최적 선택 → 2차 고품질 재생성 흐름을 제공한다.
FR-16. 생성 결과 검증은 Gemini Vision + GLM 폴백 구조를 사용한다.
FR-17. 표준 인체 치수 기반 도면/패턴 초안을 생성한다.
FR-18. 보고서/프롬프트/이미지/도면을 버전 관리한다.
FR-19. 사용자 피드백에 따른 수정/재생성을 지원한다.
FR-20. Gemini/GLM/Nano Banana/Seedream 키 관리와 로테이션을 지원한다.
FR-21. 폴백 체인을 적용하고 사용 사실을 UI에 명시한다.
FR-22. 결과물 다운로드(보고서/이미지/도면/프롬프트)를 제공한다.
FR-23. 진행률, 작업 상태, 비용/쿼터 현황을 UI에 표시한다.
FR-24. 외부 시스템 연동을 위한 표준 API 엔드포인트를 제공한다.
FR-25. 표준 치수 기준은 한국/중국/미국/국제 4종을 지원한다.
FR-26. 이미지 생성 모델에 전달되는 모든 프롬프트는 영어로 변환한다.
FR-27. 결과 언어(보고서/요약/라벨)는 사용자 선택(한국어/중국어 간체/중국어 번체/영어)로 제공한다.
FR-28. UI 상단 오른쪽에 글로벌 아이콘, 언어 콤보박스, 적용 버튼을 제공하며 적용 즉시 전체 렌더링을 갱신한다.

## 5. 비기능 요구사항 (NFR)
NFR-01. 정확성: 근거 기반 분석, 출처/근거 식별 가능.
NFR-02. 효율성: 크롤링/분석/생성 병렬화 및 캐싱 고려.
NFR-03. 안정성: 실패 지점 분리, 재시도/롤백 가능.
NFR-04. 일관성: 동일 디자인의 시각/치수 요소 유지.
NFR-05. 완결성: 보고서-프롬프트-이미지-도면 연결 일관.
NFR-06. 무결성: 데이터 해시/버전 관리, 감사 로그.
NFR-07. 보안성: 키 관리, 접근 제어, 민감정보 마스킹.
NFR-08. 확장성: 웹/앱 확장 가능한 모듈 구조.
NFR-09. 성능: 대량 데이터 처리 시 타임아웃/큐 관리.
NFR-10. 호환성: 다양한 이미지 모델/해상도/비율 지원.
NFR-11. 사용성: 초급 사용자도 단계별로 이해 가능한 UX.
NFR-12. 논리성: 모든 단계의 입력/출력 연결이 추적 가능.
NFR-13. 국제화: 다국어 UI/보고서/라벨 제공 및 즉시 전환.

## 6. 데이터 수집(크롤링) 요구사항
- reference `reference/Cosmetic_case_gen/app/services/crawler_service.py`의 구조/동작을 그대로 이식.
- `CrawlerCancellationToken`, `ThreadPoolExecutor`, 진행률 콜백, 에러 핸들러 패턴 유지.
- `reference/Cosmetic_case_gen/crawlers/common.py`, `reference/Cosmetic_case_gen/crawlers/crawler_manager.py`, `reference/Cosmetic_case_gen/crawlers/total_crawler.py`의 함수 래핑 구조 유지.
- 수집 메타: platform, url, published_date, view/like, keyword, region/season 등 저장.
- 댓글/본문 구분 저장 및 원문 보존.

## 7. 분석/인사이트 생성 요구사항
- reference `reference/Cosmetic_case_gen/app/services/analysis_service.py`의 비동기 분석 흐름과 JSON 파싱 구조 적용.
- reference `reference/Cosmetic_case_gen/app/services/input_service.py`, `reference/Cosmetic_case_gen/prompts/input_analysis.txt`의 키워드 추출 형식 유지.
- reference `reference/Cosmetic_case_gen/prompts/needs_extraction.txt` 형식을 패션 도메인으로 재작성.
- 규칙 기반 분류 대신 AI 기반 텍스트 분류/요약으로 품질 점수화.
- 청킹 기준은 토큰/길이 기반으로 설정하고 설정값으로 관리.

## 8. 디자인 콘셉트/보고서 요구사항
- 콘셉트 3개: 컨셉명, 타겟, 시즌, 실루엣, 소재, 색 팔레트, 디테일, 근거 포함.
- 보고서: 표준화된 형식으로 3000자 내외로 요약한다.
- 보고서 섹션: 타겟, 조사 범위, 요약, 현재 트렌드, 전망, 제안 디자인, 디자인 설명, 근거(이유).

## 9. 프롬프트 생성 규칙
- reference `reference/Ad_imageGen_win/ad_atelier/services/prompt/ai_prompt_optimizer.py` 모델별 가이드라인 적용.
- 입력 언어는 자동 감지하고, 이미지 생성용 프롬프트는 항상 영어로 생성한다.
- Z-Image: concise 스타일 + 품질 태그.
- Seedream/Nano Banana: 자연어 서술형 + 카메라/조명/구도 포함.
- 네거티브 프롬프트는 모델별 기본 템플릿 사용.

## 10. 이미지 생성/일관성 요구사항
- reference `reference/Ad_imageGen_win/ad_atelier/services/multi_model_generator.py`의 1차/2차 생성 구조 적용.
- reference `reference/Ad_imageGen_win/ad_atelier/services/model_detector.py`의 가용성 점검과 생성 계획 수립 방식 적용.
- reference `reference/Ad_imageGen_win/ad_atelier/services/consistency_config.py`의 ref_type별 denoise/참조 정책 적용.
- ref_type: garment/product, model, pose, style, background, composition.
- Z-Image는 ComfyUI IP-Adapter/ControlNet 기반 참조 사용.
- Seedream/Nano Banana는 참조 이미지 + 분석 텍스트 결합 방식 사용.
- reference `reference/Ad_imageGen_win/ad_atelier/services/generation_verifier.py` 방식으로 이미지 검증 및 개선 루프 적용.

## 11. 도면/패턴 초안 요구사항
- 표준 인체 치수(기준 사이즈)와 단위/기준점을 명시.
- 앞/뒤 패턴, 주요 봉제선, 치수 라벨 포함.
- 출력: SVG/PNG/PDF 초안 + 치수 테이블.

## 12. 표준 치수 기준(4종) 정리
- 한국: KS 의복 치수 표준(예: KS K 0050 남성복, KS K 0051 여성복, KS K 0052 유아복 등).
- 중국: GB/T 1335 계열(GB/T 1335.1 남성, 1335.2 여성, 1335.3 아동).
- 미국: ASTM 의복 치수 표준(예: ASTM D5585 여성, ASTM D6240 남성).
- 국제: ISO 의복 치수 표준(예: ISO 8559 시리즈, ISO 3635).
- 구현 방식: 표준별 치수 테이블을 데이터셋으로 보유하고, 프로젝트/세션 단위로 적용 표준을 선택한다.
- 표준 문서의 상세 치수표는 구현 단계에서 공식 문서로 재검증하여 반영한다.

## 13. 데이터 모델(요약)
- Project, Session, CrawlJob, RawItem, Comment, TrendInsight, Concept, PromptSpec,
  GenerationJob, ImageAsset, PatternDraft, Report, Version, ApiKey, AuditLog,
  SizeStandard, SizeTable, LocaleSetting.

## 14. UI/UX 요구사항
- 입력 → 분석 진행 → 콘셉트 비교 → 선택 → 이미지/도면 → 다운로드 흐름.
- 텍스트 크기: 본문 14px, 소제목 16~18px, 제목 20px 내외.
- 간격: 8/16/24/32px 스케일, 카드형 레이아웃.
- reference `reference/Cosmetic_case_gen/static/css/design-system.css` 토큰/레이아웃 패턴 복사.
- reference `reference/Cosmetic_case_gen/templates/pages/input_studio.html`의 입력 흐름/레이아웃 참고.
- 상단 오른쪽 글로벌 아이콘 + 언어 콤보박스 + 적용 버튼 제공.
- 적용 버튼 클릭 시 전체 화면이 즉시 재렌더링되어 언어 변경을 반영.
- 모바일: 1열 그리드, 버튼/입력 터치 영역 44px 이상.
- 상태 표시: 진행률, 실패 사유, 폴백 사용 여부, 비용/쿼터.

## 15. 클라우드 AI 호출 방식 준수(레퍼런스 매핑)
- Gemini 프롬프트/분석: `reference/Ad_imageGen_win/ad_atelier/services/prompt/ai_prompt_optimizer.py` 호출 방식 적용.
- 검증: `reference/Ad_imageGen_win/ad_atelier/services/generation_verifier.py`의 Gemini → GLM 폴백 구조 적용.
- Z-Image(ComfyUI): `reference/Ad_imageGen_win/ad_atelier/services/api_clients/comfyui_client.py` 엔드포인트/워크플로우 적용.
- Seedream 4.5: `reference/Ad_imageGen_win/ad_atelier/services/api_clients/seedream_client.py` BytePlus 호출 적용.
- Nano Banana: `reference/Ad_imageGen_win/ad_atelier/services/api_clients/nano_banana_client.py` 호출 적용.
- 키 관리: `reference/Ad_imageGen_win/ad_atelier/services/key_manager/gemini_key_manager.py`, `reference/Ad_imageGen_win/ad_atelier/services/key_manager/nano_banana_key_manager.py`, `reference/Ad_imageGen_win/ad_atelier/services/key_manager/bytedance_key_manager.py`, `reference/Ad_imageGen_win/ad_atelier/services/key_manager/zai_key_manager.py` 복사.
- 폴백 체인: `reference/Ad_imageGen_win/ad_atelier/services/edit_pipelines/fallback_chain_manager.py`, 알럿 기록은 `reference/Ad_imageGen_win/ad_atelier/services/alert_service.py` 방식 적용.
- 알럿/경고 UX는 `reference/Ad_imageGen_win/response_ai.md`의 흐름 참고.

## 16. 운영/알럿/폴백
- 폴백 체인 사용 시 모델/사유/티어를 사용자에게 노출.
- 할당량/429 발생 시 알럿 저장 및 UI 표시.
- 실패는 숨기지 않고 원인과 재시도 옵션을 제공.

## 17. 보안/법/윤리
- 개인정보/실존 인물 처리 기준 명시, 익명화/동의 절차 준비.
- 저작권/사용권 정책 및 결과물 이용 범위 명시.
- 키/로그는 민감정보 마스킹 필수.

## 18. 품질/검증 기준
- 트렌드 타당성: 교차 출처 비율/근거 수.
- 일관성: 전/후면/착장/도면 요소 일치율.
- 프롬프트 충실도: 보고서 요소 반영률.
- 재현성: 동일 시드/참조 입력 시 유사 결과.
- 언어 정확성: 선택 언어로의 번역 품질/용어 일관성.

## 19. 엣지 케이스
- 특정 지역/시즌 데이터 부족.
- 모델 간 상충된 분석 결과.
- 선택 모델 API 실패/쿼터 초과.
- 일관성 붕괴(참조 이미지와 결과 불일치).
- 표준 치수와 디자인 구조 충돌.
- 언어 전환 시 일부 UI 문구 미번역.

## 20. 결정 필요 사항/다음 단계 제안
- 기본 언어/기본 표준 치수의 초기값 확정.
- 보고서 길이(3000자 내외) 초과 시 축약 규칙 확정.
- 이미지 생성 우선순위(의상 단품 vs 착장 우선) 결정.

## 21. 레퍼런스 활용 상세 매핑
- 크롤링: `reference/Cosmetic_case_gen/app/services/crawler_service.py` 구조 복사, `reference/Cosmetic_case_gen/crawlers/*` 모듈 직접 이식.
- 크롤러 유틸: `reference/Cosmetic_case_gen/crawlers/common.py`, `reference/Cosmetic_case_gen/crawlers/crawler_manager.py`, `reference/Cosmetic_case_gen/crawlers/total_crawler.py`의 함수 래핑 구조 유지.
- 파이프라인: `reference/Cosmetic_case_gen/app/services/pipeline_orchestrator.py` 단계 구성 참고(입력→수집→분석→보고서→저장).
- 분석/보고서: `reference/Cosmetic_case_gen/app/services/analysis_service.py`, `reference/Cosmetic_case_gen/app/services/input_service.py`, `reference/Cosmetic_case_gen/prompts/input_analysis.txt`, `reference/Cosmetic_case_gen/prompts/needs_extraction.txt` 구조 재사용.
- 프롬프트: `reference/Ad_imageGen_win/ad_atelier/services/prompt/ai_prompt_optimizer.py` 모델별 템플릿/폴백 로직 적용.
- 이미지 생성: `reference/Ad_imageGen_win/ad_atelier/services/multi_model_generator.py`, `reference/Ad_imageGen_win/ad_atelier/services/model_detector.py`, `reference/Ad_imageGen_win/ad_atelier/services/consistency_config.py` 그대로 적용.
- 검증/폴백/알럿: `reference/Ad_imageGen_win/ad_atelier/services/generation_verifier.py`, `reference/Ad_imageGen_win/ad_atelier/services/edit_pipelines/fallback_chain_manager.py`, `reference/Ad_imageGen_win/ad_atelier/services/alert_service.py`, `reference/Ad_imageGen_win/response_ai.md` 참고.
- UI/디자인: `reference/Cosmetic_case_gen/static/css/design-system.css`, `reference/Cosmetic_case_gen/templates/pages/input_studio.html`의 토큰/레이아웃 복사.

## 22. 3회 이상 검토 기록
- 1차(파이프라인 관점): 수집→분석→콘셉트→프롬프트→이미지→도면 흐름 정합성 보강.
- 2차(레퍼런스 관점): 크롤러/오케스트레이터/모델 호출/키 로테이션 매핑 보강.
- 3차(UX/운영 관점): 진행률/폴백/다운로드/이력 관리 요구사항 구체화.
- 4차(일관성 관점): 디자인 ID/참조 이미지/검증 루프 연결 고리 강화.
- 5차(언어/치수/보고서 관점): 영어 프롬프트, 다국어 결과, 표준 치수 4종, 보고서 형식 추가.
