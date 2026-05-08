"""
AI Research Service - Orchestrates AI-powered web research
Coordinates multiple AI research clients (Gemini, Perplexity, GLM)
for comprehensive fashion trend investigation.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable

from ai_clients.research.base_research_client import BaseResearchClient, ResearchResult
from ai_clients.research.gemini_research_client import GeminiResearchClient
from ai_clients.research.perplexity_client import PerplexityClient
from ai_clients.research.glm_research_client import GLMResearchClient

from app.core.logging import get_logger
from app.core.settings_storage import (
    get_api_key,
    load_settings,
    save_settings
)

logger = get_logger(__name__)

ProgressCallback = Callable[[str, float, str], None]


class AIResearchService:
    """
    AI 직접 조사 오케스트레이터

    크롤러 데이터 수집 후 추가적으로 AI가 직접 웹 검색을 수행하여
    보다 풍부한 패션 트렌드 인사이트를 제공합니다.
    """

    def __init__(self):
        self.gemini_client = GeminiResearchClient()
        self.perplexity_client = PerplexityClient(model="sonar")
        self.glm_client = GLMResearchClient()

    async def conduct_research(
        self,
        session_data: Dict[str, Any],
        keywords: List[str],
        progress_cb: ProgressCallback
    ) -> Dict[str, Any]:
        """
        세션 데이터와 키워드를 기반으로 AI 조사 수행

        Args:
            session_data: 세션 데이터 (필터 정보 포함)
            keywords: 추출된 키워드 리스트
            progress_cb: 진행률 콜백

        Returns:
            AI 조사 결과 딕셔너리
        """
        if not self.is_enabled():
            return {"enabled": False, "results": []}

        # 맥락 쿼리 생성
        context_query = self._build_context_query(session_data, keywords)

        progress_cb(
            "ai_research",
            51,
            f"AI 조사 시작: {context_query[:50]}..."
        )

        # 활성화된 모델로 병렬 조사
        enabled_models = self._get_enabled_models()
        logger.info(f"[AI_RESEARCH] 활성화된 모델: {enabled_models}")

        tasks = []
        task_names = []

        if "gemini_search" in enabled_models:
            tasks.append(self._safe_research(
                self.gemini_client, context_query
            ))
            task_names.append("gemini")

        if "perplexity" in enabled_models:
            perplexity_model = self._get_perplexity_model()
            self.perplexity_client._model = perplexity_model
            tasks.append(self._safe_research(
                self.perplexity_client, context_query
            ))
            task_names.append(f"perplexity({perplexity_model})")

        if "glm_research" in enabled_models:
            tasks.append(self._safe_research(
                self.glm_client, context_query
            ))
            task_names.append("glm")

        logger.info(f"[AI_RESEARCH] {len(tasks)}개 모델로 조사 시작: {task_names}")

        # 병렬 실행
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            valid_results = []
            failed_models = []

            for idx, result in enumerate(results):
                model_name = task_names[idx] if idx < len(task_names) else f"model_{idx}"
                if isinstance(result, Exception):
                    logger.warning(f"[AI_RESEARCH] {model_name} 작업 실패: {result}")
                    failed_models.append(model_name)
                elif result is not None and result.content:
                    valid_results.append(result)
                else:
                    logger.warning(f"[AI_RESEARCH] {model_name} 응답 없음")
                    failed_models.append(model_name)

            success_count = len(valid_results)
            total_count = len(tasks)
            logger.info(f"[AI_RESEARCH] 조사 완료: {success_count}/{total_count} 성공, 실패: {failed_models}")

            progress_cb(
                "ai_research",
                54,
                f"AI 조사 완료: {success_count}개 모델 응답 (총 {total_count}개 중)"
            )

            return {
                "enabled": True,
                "context_query": context_query,
                "results": [r.to_dict() for r in valid_results],
                "merged_insights": self._merge_results(valid_results)
            }

        return {"enabled": False, "results": []}

    def _build_context_query(
        self,
        session_data: Dict[str, Any],
        keywords: List[str]
    ) -> str:
        """
        세션 데이터와 키워드로 맥락 기반 조사 쿼리 생성

        Args:
            session_data: 세션 데이터
            keywords: 추출된 키워드

        Returns:
            조사 쿼리 문자열
        """
        filters = session_data.get("filters") or {}
        parts = []

        # 필터 값이 리스트인 경우 처리 (문자열로 변환)
        def _to_str(value: Any) -> str:
            if isinstance(value, list):
                return " ".join(str(v) for v in value if v)
            return str(value) if value else ""

        # 시즌/연도
        if filters.get("season"):
            parts.append(_to_str(filters["season"]))

        # 타겟 연령대
        if filters.get("age_group"):
            parts.append(_to_str(filters["age_group"]))

        # 성별
        if filters.get("gender"):
            parts.append(_to_str(filters["gender"]))

        # 카테고리
        if filters.get("category"):
            parts.append(_to_str(filters["category"]))

        # 키워드 추가 (최대 3개)
        if keywords:
            parts.extend(keywords[:3])

        # 패션 트렌드 전망 접미사
        base_query = " ".join(parts)
        return f"{base_query} 패션 트렌드 전망 분석"

    async def _safe_research(
        self,
        client: BaseResearchClient,
        query: str
    ) -> Optional[ResearchResult]:
        """
        안전한 조사 실행 (에러 처리 포함)

        Args:
            client: 연구 클라이언트
            query: 조사 쿼리

        Returns:
            ResearchResult 또는 None (실패 시)
        """
        client_name = client.__class__.__name__
        source_name = client.SOURCE.value if hasattr(client, 'SOURCE') else client_name

        try:
            if not client.is_available():
                reason = "API key not configured" if not client.is_available() else "Availability check failed"
                logger.warning(f"[AI_RESEARCH] {source_name} 연결 실패: {reason}")
                return None

            logger.info(f"[AI_RESEARCH] {source_name} 조사 시작: {query[:50]}...")
            result = await client.research(query)
            logger.info(f"[AI_RESEARCH] {source_name} 조사 성공: {len(result.citations)}개 출처")
            return result

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(f"[AI_RESEARCH] {source_name} 조사 실패 [{error_type}]: {error_msg}")
            return None

    def _merge_results(self, results: List[ResearchResult]) -> Dict[str, Any]:
        """
        여러 AI 조사 결과 통합

        Args:
            results: 연구 결과 리스트

        Returns:
            통합된 인사이트
        """
        if not results:
            return {}

        all_citations = []
        all_content = []

        for r in results:
            source_label = r.source.value.upper()
            all_content.append(f"[{source_label}] {r.content}")
            all_citations.extend(r.citations)

        return {
            "combined_content": "\n\n".join(all_content),
            "all_citations": list(set(all_citations)),
            "source_count": len(results),
            "sources": [r.source.value for r in results]
        }

    def is_enabled(self) -> bool:
        """AI 조사 기능 활성화 여부 확인"""
        settings = load_settings()
        ai_research_config = settings.get("ai_research", {})
        return ai_research_config.get("enabled", False)

    def _get_enabled_models(self) -> List[str]:
        """활성화된 조사 모델 리스트 반환"""
        settings = load_settings()
        ai_research_config = settings.get("ai_research", {})
        models_config = ai_research_config.get("models", {})

        enabled = []
        for model, is_active in models_config.items():
            if is_active:
                enabled.append(model)
        return enabled

    def _get_perplexity_model(self) -> str:
        """Perplexity 모델명 반환"""
        settings = load_settings()
        ai_research_config = settings.get("ai_research", {})
        return ai_research_config.get("perplexity_model", "sonar")


# ============================================================================
# 설정 관련 함수 (settings_storage.py에서 호출됨)
# ============================================================================

def get_ai_research_config() -> Dict[str, Any]:
    """AI 조사 설정 반환"""
    settings = load_settings()
    return settings.get("ai_research", {
        "enabled": False,
        "models": {
            "gemini_search": False,
            "perplexity": False,
            "glm_research": False
        },
        "perplexity_model": "sonar",
        "research_depth": "standard"
    })


def save_ai_research_config(config: Dict[str, Any]) -> bool:
    """
    AI 조사 설정 저장

    Args:
        config: AI 조사 설정 딕셔너리

    Returns:
        저장 성공 여부
    """
    settings = load_settings()
    settings["ai_research"] = config
    return save_settings(settings)


def is_ai_research_enabled() -> bool:
    """AI 조사 활성화 여부"""
    settings = load_settings()
    return settings.get("ai_research", {}).get("enabled", False)


def get_enabled_research_models() -> List[str]:
    """활성화된 조사 모델 리스트"""
    settings = load_settings()
    models_config = settings.get("ai_research", {}).get("models", {})

    enabled = []
    for model, is_active in models_config.items():
        if is_active:
            enabled.append(model)
    return enabled


def get_perplexity_model() -> str:
    """Perplexity 모델 반환"""
    settings = load_settings()
    return settings.get("ai_research", {}).get("perplexity_model", "sonar")
