"""
Fashion pipeline orchestrator
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Callable

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.settings_storage import get_gemini_model, get_fallback_model
from app.crawler_config import get_enabled_crawlers
from app.services.analysis_service import AnalysisService
from app.services.image_generation_service import ImageGenerationService
from app.services.blueprint_service import get_blueprint_service
from app.services.report_generation_service import ReportGenerationService
from app.services.pipeline_utils import (
    fetch_url_texts,
    extract_file_texts,
    parse_json
)
from app.services.pipeline_crawl_utils import (
    format_filters,
    build_crawl_plan,
    build_source_counts_text,
    compute_crawl_progress,
    estimate_expected_items,
    apply_crawler_config,
    serialize_crawled_items,
    build_crawl_start_message,
    format_crawler_errors
)
from app.services.pipeline_generation_steps import generate_images, generate_blueprints
from ai_clients.gemini_client import GeminiClient
from crawlers.crawler_service import CrawlerService
from crawlers.searxng_crawler import SearxngCrawler

logger = get_logger(__name__)

ProgressCallback = Callable[[str, float, str], None]
StateCallback = Callable[[Dict[str, Any]], None]


class FashionPipelineOrchestrator:
    """7단계 패션 분석 파이프라인 오케스트레이터"""

    def __init__(self):
        settings = get_settings()
        self.crawler_service = CrawlerService(max_workers=settings.max_concurrent_crawls)
        self.analysis_service = AnalysisService()
        self.image_service = ImageGenerationService()
        self.blueprint_service = get_blueprint_service()
        self.report_service = ReportGenerationService()
        self.gemini_client = GeminiClient()
        if "searxng" not in self.crawler_service.crawlers:
            self.crawler_service.register_crawler("searxng", SearxngCrawler())

    async def run_complete_pipeline(
        self,
        session_data: Dict[str, Any],
        progress_cb: ProgressCallback,
        state_cb: Optional[StateCallback] = None
    ) -> Dict[str, Any]:
        input_context = await self._build_input_context(session_data, progress_cb)
        keywords = await self._extract_keywords(session_data, input_context, progress_cb, state_cb)
        crawled = await self._collect_data(session_data, keywords, progress_cb, state_cb)
        analysis = await self._analyze_trends(session_data, crawled, keywords, progress_cb)
        ideas = await self._generate_ideas(analysis, progress_cb)
        report_context = {
            "session_data": session_data,
            "crawled": crawled,
            "analysis": analysis,
            "ideas": ideas,
            "keywords": keywords
        }
        report_payload = await self._generate_report_payload(report_context, progress_cb)
        images = await self._generate_images(session_data, ideas, progress_cb)
        blueprints = await self._generate_blueprints(session_data, ideas, progress_cb)

        return {
            "input_context": input_context,
            "keywords": keywords,
            "crawled_data": crawled,
            "analysis": analysis,
            "trends": analysis.get("key_trends", []) if isinstance(analysis, dict) else [],
            "summary": analysis.get("summary") if isinstance(analysis, dict) else None,
            "design_ideas": ideas,
            "report_payload": report_payload,
            "generated_images": images,
            "blueprints": blueprints,
            "completed_at": datetime.utcnow().isoformat()
        }

    def get_pipeline_status(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": session_data.get("status", "unknown"),
            "progress_percent": session_data.get("progress_percent", 0.0),
            "current_step": session_data.get("current_step"),
            "started_at": session_data.get("started_at"),
            "completed_at": session_data.get("completed_at"),
            "error_message": session_data.get("error_message")
        }

    async def _build_input_context(self, session_data: Dict[str, Any], progress_cb: ProgressCallback) -> str:
        progress_cb("input_analysis", 5, "입력 분석 시작")
        parts: List[str] = []

        description = session_data.get("description")
        if description:
            parts.append(f"세션 설명: {description}")

        input_text = session_data.get("input_text")
        if input_text:
            parts.append(f"추가 입력: {input_text}")

        url_texts = await fetch_url_texts(session_data.get("input_urls", []))
        for item in url_texts:
            parts.append(f"URL({item['url']}) 요약: {item['text'][:1500]}")

        file_texts = await extract_file_texts(session_data.get("input_files", []), self._describe_image)
        for item in file_texts:
            if item.get("type") == "image":
                parts.append(f"이미지 설명: {item['text']}")
            elif item.get("type") == "pdf":
                parts.append(f"PDF 내용: {item['text'][:1500]}")

        if not parts:
            raise ValueError("입력 데이터가 없습니다. 세션 설명을 확인하세요.")

        progress_cb("input_analysis", 10, "입력 분석 완료")
        return "\n\n".join(parts)

    async def _describe_image(self, image_path: str) -> Optional[str]:
        prompt = "이 이미지의 패션 요소(스타일, 실루엣, 소재, 컬러)를 간단히 요약해 주세요."
        response = await self.gemini_client.generate_with_image(prompt=prompt, image_path=image_path, model=get_gemini_model())
        return response.text.strip() if response else None

    async def _try_gemini_keywords(self, system_prompt: str, user_content: str) -> tuple[Optional[str], Optional[Exception]]:
        try:
            response = await self.gemini_client.chat_completion(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}],
                model=get_gemini_model()
            )
            logger.info(f"Keyword extraction succeeded with Gemini ({get_gemini_model()})")
            return response.text, None
        except Exception as exc:
            logger.warning(f"Gemini failed for keyword extraction: {exc}")
            return None, exc

    @staticmethod
    def _parse_keywords_json(response_text: Optional[str]) -> Optional[Dict[str, Any]]:
        if not response_text:
            return None
        return parse_json(response_text)

    async def _glm_keyword_fallback(self, system_prompt: str, user_content: str) -> Dict[str, Any]:
        from ai_clients.glm_client import GLMClient
        glm_client = GLMClient()
        response = await glm_client.generate_content(
            prompt=user_content,
            model=get_fallback_model(),
            system_prompt=system_prompt
        )
        return parse_json(response.text)

    async def _extract_keywords(
        self,
        session_data: Dict[str, Any],
        context: str,
        progress_cb: ProgressCallback,
        state_cb: Optional[StateCallback]
    ) -> List[str]:
        progress_cb("keyword_extraction", 15, "키워드 추출 시작")
        system_prompt = ("당신은 패션 트렌드 리서치 키워드 생성기입니다. 입력과 필터를 바탕으로 실제 검색에 사용할 키워드/검색어를 5~12개 생성하세요. "
                         "세션 제목/설명/입력의 핵심 명사(예: 여성복, 2026 SS, 캐주얼 등)를 모든 키워드에 반드시 포함하고, "
                         "패션/의류/스타일/코디/소재/실루엣/컬러 중 하나 이상을 반드시 포함하세요. "
                         "입력에 미래 연도가 포함되면, 동일 주제의 최근 시즌/일반 트렌드 키워드 2~3개를 포함해 실제 데이터 확보를 보장하세요. "
                         "연도/시즌/성별/카테고리 정보가 있으면 일부 키워드(60% 이상)에 반영하고, 나머지는 연도 제거한 현재/최근 트렌드 키워드로 생성합니다. "
                         "일반 뉴스/이벤트로 확장되는 표현은 금지합니다. "
                         "키워드는 한국어 중심의 2~6단어 검색어로 중복 없이 작성하세요. JSON 형식만 응답: {\"keywords\": [\"...\"]}")
        filter_summary = format_filters(session_data.get("filters") or {})
        user_content = (f"세션 제목: {session_data.get('session_title')}\n"
                        f"입력 내용: {context}\n"
                        f"필터 요약: {filter_summary}\n"
                        f"사용자 키워드: {session_data.get('user_keywords')}")
        response_text, gemini_error = await self._try_gemini_keywords(system_prompt, user_content)
        try:
            data = self._parse_keywords_json(response_text)
        except Exception as exc:
            gemini_error = exc
            data = None
            logger.warning("Gemini keyword extraction returned invalid JSON, trying GLM fallback")

        if not data or not data.get("keywords"):
            try:
                data = await self._glm_keyword_fallback(system_prompt, user_content)
                logger.info(f"Keyword extraction succeeded with GLM fallback ({get_fallback_model()})")
            except Exception as glm_e:
                logger.error(f"GLM fallback also failed: {glm_e}")
                gemini_message = str(gemini_error) if gemini_error else "Gemini failure"
                raise ValueError(
                    f"키워드 추출 실패: Gemini JSON 파싱 실패 또는 응답 없음. Gemini: {gemini_message}, GLM: {glm_e}"
                )
        keywords = data.get("keywords") if isinstance(data, dict) else []
        if not keywords:
            raise ValueError("키워드 추출 실패: 결과가 비어 있습니다")

        keywords = list(dict.fromkeys([k.strip() for k in keywords if k]))
        session_data["extracted_keywords"] = keywords
        if state_cb:
            state_cb({"extracted_keywords": keywords, "crawl_total_keywords": len(keywords)})
        preview = ", ".join(keywords[:8])
        preview = f"{preview} ...(+{len(keywords) - 8})" if len(keywords) > 8 else preview
        progress_cb("keyword_extraction", 20, f"키워드 추출 완료: {preview}")
        return keywords

    async def _collect_data(
        self,
        session_data: Dict[str, Any],
        keywords: List[str],
        progress_cb: ProgressCallback,
        state_cb: Optional[StateCallback]
    ) -> List[Dict[str, Any]]:
        crawler_config = session_data.get("crawler_config") or {}
        sources, max_items, youtube_config, start_date, end_date = build_crawl_plan(crawler_config, [c["id"] for c in get_enabled_crawlers()])
        if not sources:
            raise ValueError("활성화된 크롤러가 없습니다")
        if "searxng" in sources and not get_settings().searxng_api_url:
            raise ValueError("SearXNG API URL이 설정되어 있지 않습니다. 설정 페이지에서 입력하세요.")
        apply_crawler_config(self.crawler_service, sources, max_items, youtube_config)
        total_keywords = len(keywords)
        expected_items = estimate_expected_items(sources, total_keywords, max_items, youtube_config)
        progress_cb("crawling", 25, build_crawl_start_message(
            sources,
            total_keywords,
            expected_items,
            start_date,
            end_date,
            max_items,
            youtube_config
        ))
        if state_cb:
            state_cb({"crawl_expected_items": expected_items, "crawl_collected_items": 0, "crawl_completed_keywords": 0, "crawl_total_keywords": total_keywords})
        all_results: List[Dict[str, Any]] = []
        for index, keyword in enumerate(keywords, start=1):
            start_progress = compute_crawl_progress(len(all_results), expected_items, index - 1, total_keywords)
            progress_cb("crawling", start_progress, f"키워드 {index}/{total_keywords} 수집 시작: {keyword}")
            items = await self.crawler_service.crawl_all(keyword=keyword, start_date=start_date, end_date=end_date, enabled_crawlers=sources)
            count_text = build_source_counts_text(items, sources)
            serialized = serialize_crawled_items(items)
            all_results.extend(serialized)
            if state_cb:
                state_cb({"crawl_collected_items": len(all_results), "crawl_completed_keywords": index})
            progress = compute_crawl_progress(len(all_results), expected_items, index, total_keywords)
            errors = self.crawler_service.get_last_errors()
            error_text = format_crawler_errors(errors)
            progress_cb(
                "crawling",
                progress,
                f"키워드 {index}/{total_keywords} 완료: {len(serialized)}개 ({count_text}){error_text}"
            )
        if not all_results:
            raise ValueError(f"크롤링 결과가 없습니다 (키워드 {total_keywords}개, 소스 {len(sources)}개)")
        progress_cb("crawling", 50, f"데이터 수집 완료: {len(all_results)}개")
        return all_results

    async def _analyze_trends(self, session_data: Dict[str, Any], crawled: List[Dict[str, Any]], keywords: List[str], progress_cb: ProgressCallback) -> Dict[str, Any]:
        progress_cb("trend_analysis", 55, "트렌드 분석 시작")
        analysis = await self.analysis_service.analyze_trends(
            raw_data=crawled,
            filters=session_data.get("filters") or {},
            user_input=" ".join(keywords)
        )
        progress_cb("trend_analysis", 65, "트렌드 분석 완료")
        return analysis

    async def _generate_ideas(self, analysis: Dict[str, Any], progress_cb: ProgressCallback) -> List[Dict[str, Any]]:
        progress_cb("idea_generation", 70, "디자인 아이디어 생성")
        ideas = await self.analysis_service.generate_design_concepts(analysis_result=analysis, num_concepts=5)
        progress_cb("idea_generation", 80, f"아이디어 {len(ideas)}개 생성 완료")
        return ideas

    async def _generate_report_payload(
        self,
        context: Dict[str, Any],
        progress_cb: ProgressCallback
    ) -> Dict[str, Any]:
        progress_cb("report_generation", 81, "보고서 생성 시작")
        payload = await self.report_service.generate_payload(
            session_data=context.get("session_data") or {},
            crawled=context.get("crawled") or [],
            analysis=context.get("analysis") or {},
            ideas=context.get("ideas") or [],
            keywords=context.get("keywords") or []
        )
        progress_cb("report_generation", 82, "보고서 생성 완료")
        return payload

    async def _generate_images(
        self,
        session_data: Dict[str, Any],
        ideas: List[Dict[str, Any]],
        progress_cb: ProgressCallback
    ) -> List[Dict[str, Any]]:
        return await generate_images(session_data, ideas, self.image_service, progress_cb)

    async def _generate_blueprints(
        self,
        session_data: Dict[str, Any],
        ideas: List[Dict[str, Any]],
        progress_cb: ProgressCallback
    ) -> List[Dict[str, Any]]:
        return await generate_blueprints(session_data, ideas, self.blueprint_service, progress_cb)
