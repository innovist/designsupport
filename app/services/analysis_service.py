"""
Analysis service for fashion trend analysis using multiple AI models
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import logging

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.settings_storage import get_gemini_model, get_glm_model, AVAILABLE_MODELS
from app.models.crawler import RawData
from app.models.analysis import TrendAnalysis, TrendInsight
from app.models.design import DesignConcept
from app.services.pipeline_utils import parse_json
from ai_clients.gemini_client import GeminiClient
from ai_clients.glm_client import GLMClient
from .prompt_service import PromptService
from app.services.comment_insight_service import CommentInsightService

logger = get_logger(__name__)


class AnalysisPhase(Enum):
    """분석 단계"""
    INDIVIDUAL_ANALYSIS = "individual_analysis"
    CROSS_VALIDATION = "cross_validation"
    FINAL_SYNTHESIS = "final_synthesis"


class AnalysisService:
    """분석 서비스"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        초기화

        Args:
            config: 서비스 설정
        """
        self.config = config or {}

        # AI 클라이언트 초기화
        self.gemini_client = GeminiClient()
        self.glm_client = GLMClient()

        # 프롬프트 서비스
        self.prompt_service = PromptService()
        self.comment_insight_service = CommentInsightService()

        # 분석 프롬프트 로드
        self.prompts = self._load_analysis_prompts()

    def _load_analysis_prompts(self) -> Dict[str, Dict[str, str]]:
        """분석 프롬프트 로드"""
        return {
            "trend_extraction": {
                "gemini_2_5": """
                As a professional fashion trend analyst, extract key fashion trends from the provided data. Focus on:

                1. Emerging patterns and styles
                2. Color trends and palettes
                3. Material preferences
                4. Silhouette evolutions
                5. Target demographic shifts
                6. Community sentiment and hidden needs (comments/transcripts)

                Data: {data}

                Provide output in JSON format:
                {{
                    "trends": [
                        {{
                            "trend_name": "Trend Name",
                            "category": "color/material/style/silhouette",
                            "description": "Detailed description",
                            "emergence_stage": "emerging/growing/mature/declining",
                            "confidence": 0.0
                        }}
                    ],
                    "confidence_score": 0.0
                }}
                """,
                "gemini_3": """
                Analyze the following fashion data for emerging trends with deep insight. Consider cultural, seasonal, and economic factors.

                Data: {data}

                Output requirements:
                - Identify subtle trend indicators
                - Analyze global fashion movements
                - Include community sentiment and latent needs
                - Consider social and environmental influences
                - Assess commercial viability

                JSON format:
                {{
                    "trends": [
                        {{
                            "trend_name": "Trend Name",
                            "category": "Category",
                            "description": "Comprehensive analysis",
                            "global_relevance": "High/Medium/Low",
                            "market_potential": "High/Medium/Low",
                            "confidence": 0.0,
                            "supporting_evidence": ["evidence1", "evidence2"]
                        }}
                    ],
                    "overall_confidence": 0.0
                }}
                """,
                "glm_4_6": """
                As a senior fashion market analyst with 15+ years of experience, conduct a comprehensive trend analysis of the provided data.

                Data source: {data}

                Analytical framework:
                1. Macro trend identification
                2. Micro trend extraction
                3. Cross-cultural comparison
                4. Community sentiment and latent needs
                5. Commercial viability assessment
                6. Future projection methodology

                Required output in strict JSON format:
                {{
                    "trends": [
                        {{
                            "trend_name": "Trend Name",
                            "category": "primary_category",
                            "sub_category": "specific_category",
                            "description": "Detailed analytical description",
                            "time_horizon": "short_term/medium_term/long_term",
                            "regional_spread": ["region1", "region2"],
                            "market_impact": "high/medium/low",
                            "consumer_adoption": "rapid/moderate/slow",
                            "confidence": 0.0,
                            "key_indicators": ["indicator1", "indicator2"],
                            "competitive_landscape": "competitive/emerging/saturated",
                            "supporting_data": ["data_point1", "data_point2"]
                        }}
                    ],
                    "methodology": {{
                        "analysis_approach": "Quantitative and qualitative analysis",
                        "data_weighting": "Multiple source triangulation",
                        "validation_method": "Expert consensus and market data",
                        "confidence_calculations": "Statistical significance testing"
                    }},
                    "overall_confidence": 0.0
                }}
                """
            },
            "concept_synthesis": {
                "glm_4_6": """
                As the Chief Design Director for a leading fashion house, synthesize the trend analyses into actionable design concepts.

                Trend Analyses: {analyses}

                Synthesis requirements:
                1. Identify consensus and contradictions
                2. Prioritize trends by market opportunity
                3. Bridge gaps between analysis results
                4. Ensure commercial viability
                5. Balance creativity with market trends

                Create exactly 3 distinct design concepts in JSON format:
                {{
                    "synthesis_summary": "Overview of trend alignment",
                    "consensus_points": ["point1", "point2"],
                    "contradictions": ["contradiction1", "contradiction2"],
                    "recommendations": ["recommendation1", "recommendation2"],
                    "concepts": [
                        {{
                            "concept_name": "Concept Name",
                            "trend_alignment": "High/Medium/Low",
                            "market_opportunity": "High/Medium/Low",
                            "design_approach": "Approach description",
                            "key_elements": ["element1", "element2"],
                            "differentiators": ["differentiator1", "differentiator2"],
                            "commercial_feasibility": "High/Medium/Low"
                        }}
                    ]
                }}
                """
            }
        }

    async def analyze_trends(
        self,
        raw_data: Any = None,
        filters: Dict[str, Any] = None,
        user_input: str = "",
        project_id: int = None,
        crawl_job_id: int = None
    ) -> Dict[str, Any]:
        """
        트렌드 분석 실행

        Args:
            raw_data: 원본 데이터 목록 (List[RawData] 또는 List[Dict])
            filters: 분석 필터
            user_input: 사용자 입력 프롬프트
            project_id: 프로젝트 ID (선택)
            crawl_job_id: 크롤링 작업 ID (선택)

        Returns:
            트렌드 분석 결과 딕셔너리
        """
        raw_data = raw_data or []
        filters = filters or {}
        data_count = len(raw_data) if isinstance(raw_data, list) else 0

        logger.info(f"Starting trend analysis: {data_count} items, filters={filters}")

        # 데이터 전처리
        comment_insights = await self.comment_insight_service.summarize(raw_data, filters, user_input)
        processed_data = await self._preprocess_data_flexible(raw_data, filters, user_input, comment_insights)

        # Phase 1: 개별 모델 분석
        individual_analyses = await self._perform_individual_analysis(processed_data)

        # Phase 2: 상호 검증
        cross_validation = await self._perform_cross_validation(individual_analyses)

        # Phase 3: 최종 종합
        synthesis = await self._perform_final_synthesis(
            individual_analyses, cross_validation
        )

        # 분석 결과 구성
        result = {
            "analysis_name": f"Trend Analysis - {datetime.utcnow().strftime('%Y-%m-%d')}",
            "model_used": "ensemble",
            "keywords": self._extract_keywords(processed_data),
            "summary": synthesis.get('synthesis_summary', ''),
            "key_trends": synthesis.get('consensus_points', []),
            "market_insights": cross_validation.get('market_insights', []),
            "recommendations": synthesis.get('recommendations', []),
            "confidence_score": float(synthesis.get('overall_confidence', 0.0)),
            "comment_insights": comment_insights,
            "individual_analyses": individual_analyses,
            "cross_validation": cross_validation,
            "synthesis": synthesis,
            "completed_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Trend analysis completed with confidence: {result['confidence_score']}")
        return result

    async def _preprocess_data_flexible(
        self,
        raw_data: Any,
        filters: Dict[str, Any],
        user_input: str,
        comment_insights: Optional[Dict[str, Any]] = None
    ) -> str:
        """유연한 데이터 전처리 - 다양한 입력 형식 지원"""
        filtered_data = []

        # raw_data 타입에 따른 처리
        if isinstance(raw_data, list):
            for item in raw_data:
                # Dict 형식
                if isinstance(item, dict):
                    content = item.get('content', item.get('text', ''))
                    if len(content) < 50:
                        continue
                    filtered_data.append({
                        'title': item.get('title', ''),
                        'content': self._clean_text(content),
                        'source': item.get('source', ''),
                        'date': item.get('date', item.get('published_at', '')),
                        'tags': item.get('tags', item.get('keywords', []))
                    })
                # RawData 객체
                elif hasattr(item, 'content'):
                    if hasattr(item, 'quality_score') and item.quality_score < 0.3:
                        continue
                    content = self._clean_text(item.content)
                    if len(content) < 50:
                        continue
                    filtered_data.append({
                        'title': getattr(item, 'title', ''),
                        'content': content,
                        'source': getattr(item, 'source', ''),
                        'date': str(getattr(item, 'published_date', '')),
                        'tags': getattr(item, 'metadata', {}).get('fashion_tags', []) if hasattr(item, 'metadata') else []
                    })

        # 필터와 user_input 추가
        if not filtered_data:
            raise ValueError("No valid data available for trend analysis")

        context = {
            'user_query': user_input,
            'filters': filters,
            'data': filtered_data
        }
        if comment_insights:
            context['comment_insights'] = comment_insights

        return json.dumps(context, ensure_ascii=False, default=str)

    async def _preprocess_data(self, raw_data: List[RawData]) -> str:
        """데이터 전처리 (레거시 호환용)"""
        # 데이터 필터링 및 정제
        filtered_data = []

        for data in raw_data:
            # 품질 점수 필터링
            if data.quality_score < 0.3:
                continue

            # 관련성 점수 필터링
            if data.relevance_score < 0.3:
                continue

            # 데이터 정제
            content = self._clean_text(data.content)
            if len(content) < 50:
                continue

            filtered_data.append({
                'title': data.title,
                'content': content,
                'source': data.source,
                'date': data.published_date,
                'author': data.author,
                'views': data.view_count,
                'likes': data.like_count,
                'tags': data.metadata.get('fashion_tags', []) if data.metadata else []
            })

        # JSON 형태로 변환
        return json.dumps(filtered_data, ensure_ascii=False, default=str)

    def _clean_text(self, text: str) -> str:
        """텍스트 정제"""
        if not text:
            return ""

        # HTML 태그 제거
        import re
        text = re.sub(r'<[^>]+>', '', text)

        # 여러 공백 제거
        text = re.sub(r'\s+', ' ', text)

        # 특수문자 정리
        text = re.sub(r'[^\w\s\u3131-\u3163\uac00-\ud7a3.,!?~\-]', '', text)

        return text.strip()

    def _extract_keywords(self, processed_data: str) -> List[str]:
        """키워드 추출"""
        # 데이터에서 키워드 추출
        import re

        # 태그 및 해시태그 추출
        data = json.loads(processed_data)
        items = data.get('data', []) if isinstance(data, dict) else data
        if not isinstance(items, list):
            return []

        all_text = " ".join(
            item.get('title', '') + " " + item.get('content', '')
            for item in items
            if isinstance(item, dict)
        )

        # 패션 관련 키워드
        fashion_keywords = set()

        # 기본 키워드 목록
        base_keywords = [
            'fashion', 'trend', 'style', 'design', 'collection',
            'clothing', 'outfit', 'apparel', 'garment', 'textile',
            'color', 'palette', 'material', 'fabric', 'silhouette'
        ]

        for keyword in base_keywords:
            if keyword in all_text.lower():
                fashion_keywords.add(keyword)

        # 태그에서 키워드 추출
        for item in items:
            tags = item.get('tags', []) if isinstance(item, dict) else []
            if isinstance(tags, str):
                tags = [tags]
            for tag in tags:
                if tag:
                    fashion_keywords.add(str(tag).lower())

        return list(fashion_keywords)

    async def _perform_individual_analysis(self, data: str) -> Dict[str, Any]:
        """개별 모델 분석"""
        tasks = {
            "gemini_2_5": self._analyze_with_gemini_2_5(data),
            "gemini_3": self._analyze_with_gemini_3(data),
            "glm_4_6": self._analyze_with_glm_4_6(data)
        }

        results: Dict[str, Any] = {}
        gathered = await asyncio.gather(*tasks.values(), return_exceptions=True)

        for model_name, result in zip(tasks.keys(), gathered):
            if isinstance(result, Exception):
                logger.error(f"Analysis failed with {model_name}: {result}")
                results[model_name] = {"error": str(result), "success": False}
                continue

            results[model_name] = result
            logger.info(f"Analysis completed with {model_name}")

        return results

    async def _analyze_with_gemini_2_5(self, data: str) -> Dict[str, Any]:
        """Gemini 2.5 Flash로 분석"""
        try:
            response = await self._call_gemini_api(
                prompt=self.prompts['trend_extraction']['gemini_2_5'].format(data=data),
                model="gemini-2.5-flash"
            )

            return {
                "model": "gemini-2.5-flash",
                "result": response,
                "success": True
            }

        except Exception as e:
            logger.error(f"Gemini 2.5 analysis failed: {e}")
            return {
                "model": "gemini-2.5-flash",
                "error": str(e),
                "success": False
            }

    async def _analyze_with_gemini_3(self, data: str) -> Dict[str, Any]:
        """Gemini 3 Flash로 분석"""
        try:
            response = await self._call_gemini_api(
                prompt=self.prompts['trend_extraction']['gemini_3'].format(data=data),
                model="gemini-2.5-pro"
            )

            return {
                "model": "gemini-2.5-pro",
                "result": response,
                "success": True
            }

        except Exception as e:
            logger.error(f"Gemini 3 analysis failed: {e}")
            return {
                "model": "gemini-2.5-pro",
                "error": str(e),
                "success": False
            }

    async def _analyze_with_glm_4_6(self, data: str) -> Dict[str, Any]:
        """GLM 4.7으로 분석"""
        try:
            response = await self._call_glm_api(
                prompt=self.prompts['trend_extraction']['glm_4_6'].format(data=data),
                model="glm-4.7"
            )

            return {
                "model": "glm-4.7",
                "result": response,
                "success": True
            }

        except Exception as e:
            logger.error(f"GLM 4.7 analysis failed: {e}")
            return {
                "model": "glm-4.7",
                "error": str(e),
                "success": False
            }

    async def _perform_cross_validation(
        self,
        analyses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """상호 검증"""
        logger.info("Performing cross-validation between analysis results")

        # 각 모델 결과 파싱
        parsed_results = {}
        for model_name, result in analyses.items():
            if not result.get('success'):
                continue

            raw_result = result.get('result')
            try:
                if isinstance(raw_result, dict):
                    parsed = raw_result
                elif isinstance(raw_result, str):
                    try:
                        parsed = json.loads(raw_result)
                    except json.JSONDecodeError:
                        json_start = raw_result.find("{")
                        json_end = raw_result.rfind("}")
                        if json_start == -1 or json_end == -1 or json_end <= json_start:
                            raise
                        parsed = json.loads(raw_result[json_start:json_end + 1])
                else:
                    raise ValueError("Unsupported analysis result format")

                parsed_results[model_name] = parsed
            except Exception as e:
                logger.error(f"Failed to parse {model_name} result: {e}")

        # 트렌드 비교
        consensus_trends = []
        all_trends = set()
        trend_counts = {}

        for model_name, result in parsed_results.items():
            if 'trends' in result:
                for trend in result['trends']:
                    trend_name = trend.get('trend_name', '')
                    if trend_name:
                        all_trends.add(trend_name)
                        trend_counts[trend_name] = trend_counts.get(trend_name, 0) + 1

        # 공통 트렌드 식별 (2개 이상 모델에서 등장)
        for trend_name, count in trend_counts.items():
            if count >= 2:
                # 각 모델 결과에서 정보 수집
                trend_info = {}
                for model_name, result in parsed_results.items():
                    if 'trends' in result:
                        for trend in result['trends']:
                            if trend.get('trend_name') == trend_name:
                                trend_info[model_name] = trend
                                break

                consensus_trends.append({
                    'trend_name': trend_name,
                    'agreement_count': count,
                    'sources': list(trend_info.keys()),
                    'combined_data': trend_info
                })

        # 상충된 인사이트 생성
        market_insights = []

        # 예시 마켓 인사이트
        if consensus_trends:
            market_insights.append({
                "insight_type": "consensus_trends",
                "description": f"Identified {len(consensus_trends)} trends with multi-model consensus",
                "confidence": "high"
            })

        return {
            "consensus_trends": consensus_trends,
            "market_insights": market_insights,
            "total_trends_identified": len(all_trends),
            "consensus_rate": len(consensus_trends) / len(all_trends) if all_trends else 0
        }

    async def _perform_final_synthesis(
        self,
        analyses: Dict[str, Any],
        cross_validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """최종 종합"""
        logger.info("Performing final synthesis with GLM-4.7")

        # 분석 결과 준비
        analysis_data = {
            "analyses": analyses,
            "cross_validation": cross_validation
        }

        # GLM-4.7에 종합 요청
        try:
            synthesis_prompt = self.prompts['concept_synthesis']['glm_4_6'].format(
                analyses=json.dumps(analyses, indent=2)
            )

            response = await self._call_glm_api(
                prompt=synthesis_prompt,
                model="glm-4.7"
            )

            return parse_json(response)

        except Exception as e:
            logger.error(f"Final synthesis failed: {e}")
            raise

    async def _save_trend_insights(
        self,
        analysis: TrendAnalysis,
        analyses: Dict[str, Any]
    ) -> List[TrendInsight]:
        """트렌드 인사이트 저장"""
        insights = []

        # 개별 모델 분석에서 인사이트 추출
        for model_name, analysis_result in analyses.items():
            if not analysis_result.get('success'):
                continue

            try:
                parsed = json.loads(analysis_result['result'])

                if 'trends' in parsed:
                    for trend in parsed['trends']:
                        insight = TrendInsight(
                            analysis_id=analysis.id if hasattr(analysis, 'id') else None,
                            category=trend.get('category', 'general'),
                            title=trend.get('trend_name', ''),
                            description=trend.get('description', ''),
                            keywords=json.dumps(self._extract_keywords_from_trend(trend)),
                            source_urls=json.dumps([trend.get('source_id', '')]),
                            confidence=float(trend.get('confidence', 0.0)),
                            impact_level=self._determine_impact_level(trend),
                            trend_strength=float(trend.get('market_potential', 0.0)),
                            target_demographics=json.dumps(trend.get('target_demographics', [])),
                            relevant_seasons=json.dumps(trend.get('time_horizon', [])),
                            metadata={
                                'model': model_name,
                                'raw_analysis': json.dumps(trend)
                            }
                        )
                        insights.append(insight)

            except Exception as e:
                logger.error(f"Failed to save insights from {model_name}: {e}")

        # 저장
        # 실제 구현 시 DB 저장

        return insights

    def _extract_keywords_from_trend(self, trend: Dict[str, Any]) -> List[str]:
        """트렌드에서 키워드 추출"""
        keywords = []

        # 기본 정보에서 추출
        if 'trend_name' in trend:
            keywords.append(trend['trend_name'])

        if 'description' in trend:
            # 설명에서 키워드 추출
            import re
            words = re.findall(r'\b\w+\b', trend['description'].lower())
            keywords.extend([word for word in words if len(word) > 2])

        return list(set(keywords))

    def _determine_impact_level(self, trend: Dict[str, Any]) -> str:
        """영향력 레벨 결정"""
        market_potential = trend.get('market_impact', 'low')

        if market_potential.lower() == 'high':
            return "high"
        elif market_potential.lower() == 'medium':
            return "medium"
        else:
            return "low"

    async def _call_gemini_api(self, prompt: str, model: str) -> str:
        """Gemini API 호출"""
        logger.info(f"Calling Gemini API with model: {model}")
        response = await self.gemini_client.generate_content(prompt=prompt, model=model)
        return response.text

    async def _call_glm_api(self, prompt: str, model: str) -> str:
        """GLM API 호출"""
        logger.info(f"Calling GLM API with model: {model}")
        response = await self.glm_client.generate_content(prompt=prompt, model=model)
        return response.text

    async def generate_design_concepts(
        self,
        analysis_result: Any = None,
        analysis: Any = None,
        num_concepts: int = 3
    ) -> List[Dict[str, Any]]:
        """디자인 컨셉 생성

        Args:
            analysis_result: 분석 결과 딕셔너리 (새 API)
            analysis: TrendAnalysis 객체 (레거시 호환)
            num_concepts: 생성할 컨셉 수

        Returns:
            디자인 컨셉 목록
        """
        logger.info(f"Generating {num_concepts} design concepts")

        concepts = []

        # 분석 결과 처리 - 새 형식 또는 레거시 형식
        try:
            if analysis_result and isinstance(analysis_result, dict):
                synthesis_data = analysis_result.get('synthesis', {})
            elif analysis and hasattr(analysis, 'recommendations'):
                synthesis_data = json.loads(analysis.recommendations or '{}')
            else:
                synthesis_data = {}

            if 'concepts' in synthesis_data:
                for i, concept_data in enumerate(synthesis_data['concepts'][:num_concepts]):
                    concept = {
                        "id": f"concept_{i + 1}",
                        "concept_number": i + 1,
                        "concept_name": concept_data.get('concept_name', f'Concept {i + 1}'),
                        "target_audience": concept_data.get('target_audience', ''),
                        "season": concept_data.get('season', ''),
                        "silhouette": concept_data.get('design_approach', ''),
                        "materials": concept_data.get('key_elements', []),
                        "color_palette": concept_data.get('color_palette', []),
                        "details": concept_data.get('differentiators', ''),
                        "rationale": concept_data.get('commercial_feasibility', ''),
                        "feasibility_score": self._calculate_feasibility_score(concept_data),
                        "market_potential": self._calculate_market_potential(concept_data),
                        "innovation_score": self._calculate_innovation_score(concept_data),
                        "prompt": f"Fashion design: {concept_data.get('concept_name', 'modern design')}, "
                                  f"style: {concept_data.get('design_approach', 'contemporary')}, "
                                  f"materials: {', '.join(concept_data.get('key_elements', []))}"
                    }
                    concepts.append(concept)

        except Exception as e:
            logger.error(f"Failed to generate concepts: {e}")

        if not concepts:
            raise ValueError("No design concepts generated from analysis result")

        return concepts

    def _map_level_score(self, value: Any) -> float:
        """High/Medium/Low 또는 숫자 기반 점수 변환"""
        if isinstance(value, (int, float)):
            return max(0.0, min(1.0, float(value)))
        if not value:
            return 0.0
        mapping = {
            "high": 0.9,
            "medium": 0.6,
            "low": 0.3
        }
        return mapping.get(str(value).strip().lower(), 0.0)

    def _calculate_feasibility_score(self, concept_data: Dict[str, Any]) -> float:
        """실현 가능성 점수 계산"""
        return self._map_level_score(concept_data.get('commercial_feasibility'))

    def _calculate_market_potential(self, concept_data: Dict[str, Any]) -> float:
        """시장성 점수 계산"""
        return self._map_level_score(concept_data.get('market_opportunity'))

    def _calculate_innovation_score(self, concept_data: Dict[str, Any]) -> float:
        """혁신성 점수 계산"""
        differentiators = concept_data.get('differentiators') or []
        if isinstance(differentiators, str):
            differentiators = [d.strip() for d in differentiators.split(',') if d.strip()]
        if not isinstance(differentiators, list):
            differentiators = []

        return min(1.0, 0.3 + (0.15 * len(differentiators)))

    async def get_analysis_stats(self) -> Dict[str, Any]:
        """분석 통계 정보 반환"""
        settings = get_settings()
        return {
            "gemini_configured": bool(settings.gemini_api_key and settings.gemini_api_key != "test-gemini-key"),
            "glm_configured": bool(settings.glm_api_key and settings.glm_api_key != "test-glm-key"),
            "available_models": [
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "glm-4.7"
            ]
        }
