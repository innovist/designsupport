"""
Prompt engineering service for AI generation
"""

# @MX:NOTE: [AUTO] Prompt engineering service - manages AI model interactions and prompt templates
# Maintains 29 specialized prompt methods for different AI models and generation types

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import json
import logging

from app.core.logging import get_logger
from app.core.config import get_local_now
from app.models.design import DesignConcept, PromptSpec

logger = get_logger(__name__)


class PromptType(Enum):
    """프롬프트 타입"""
    GARMENT = "garment"
    MODEL_FITTING = "model_fitting"
    BLUEPRINT = "blueprint"
    TREND_ANALYSIS = "trend_analysis"
    CONCEPT_GENERATION = "concept_generation"


class AIModel(Enum):
    """AI 모델"""
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_3_FLASH = "gemini-3-flash"
    GLM_4_7 = "glm-4.7"
    Z_IMAGE_TURBO = "z-image-turbo"
    SEEDREAM_4_5 = "seedream-4.5"
    NANO_BANANA = "nano-banana"


class PromptTemplate:
    """프롬프트 템플릿"""

    # 모델별 기본 설정
    MODEL_CONFIGS = {
        AIModel.GEMINI_2_5_FLASH: {
            "style": "concise",
            "max_tokens": 4000,
            "temperature": 0.7,
            "tag_style": "minimal"
        },
        AIModel.GEMINI_3_FLASH: {
            "style": "descriptive",
            "max_tokens": 4000,
            "temperature": 0.8,
            "tag_style": "detailed"
        },
        AIModel.GLM_4_7: {
            "style": "comprehensive",
            "max_tokens": 4000,
            "temperature": 0.6,
            "tag_style": "structured"
        },
        AIModel.Z_IMAGE_TURBO: {
            "style": "tag-based",
            "max_tokens": 200,
            "temperature": 0.1,
            "tag_style": "art-focused"
        },
        AIModel.SEEDREAM_4_5: {
            "style": "descriptive",
            "max_tokens": 300,
            "temperature": 0.8,
            "tag_style": "photography"
        },
        AIModel.NANO_BANANA: {
            "style": "hyper-realistic",
            "max_tokens": 300,
            "temperature": 0.7,
            "tag_style": "detailed"
        }
    }

    @classmethod
    def get_config(cls, model: AIModel) -> Dict[str, Any]:
        """모델별 설정 반환"""
        return cls.MODEL_CONFIGS.get(model, cls.MODEL_CONFIGS[AIModel.GLM_4_7])


class PromptService:
    """프롬프트 엔지니어링 서비스"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        초기화

        Args:
            config: 서비스 설정
        """
        self.config = config or {}

        # 프롬프트 템플릿 로드
        self.templates = self._load_templates()

        # 번역기 초기화
        self.translator = PromptTranslator()

    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """프롬프트 템플릿 로드"""
        return {
            "trend_analysis": {
                "gemini": """
                You are a professional fashion trend analyst. Analyze the following fashion data and provide comprehensive insights.

                Data: {data}

                Provide analysis in the following JSON format:
                {{
                    "key_trends": ["trend1", "trend2"],
                    "emerging_colors": ["color1", "color2"],
                    "popular_materials": ["material1", "material2"],
                    "style_directions": ["direction1", "direction2"],
                    "target_demographics": ["demographic1", "demographic2"],
                    "confidence_score": 0.0
                }}
                """,
                "glm": """
                As an expert fashion analyst with deep knowledge of global trends, analyze the provided fashion data.

                Data to analyze: {data}

                Requirements:
                1. Identify key fashion trends
                2. Extract emerging color palettes
                3. Note popular materials
                4. Determine style directions
                5. Define target demographics

                Output must be valid JSON:
                {{
                    "key_trends": ["trend1", "trend2"],
                    "emerging_colors": ["color1", "color2"],
                    "popular_materials": ["material1", "material2"],
                    "style_directions": ["direction1", "direction2"],
                    "target_demographics": ["demographic1", "demographic2"],
                    "confidence_score": 0.0
                }}
                """
            },
            "concept_generation": {
                "gemini": """
                Based on the trend analysis, generate 3 distinct fashion concepts.

                Trend Analysis: {analysis}

                For each concept, provide:
                - Concept name
                - Target audience
                - Season
                - Silhouette description
                - Key materials
                - Color palette
                - Unique details
                - Supporting rationale

                Output format:
                [
                    {{
                        "concept_name": "Concept Name",
                        "target_audience": "Target Description",
                        "season": "Season",
                        "silhouette": "Silhouette Description",
                        "materials": ["material1", "material2"],
                        "color_palette": ["color1", "color2"],
                        "details": "Detail description",
                        "rationale": "Supporting rationale"
                    }},
                    ...
                ]
                """,
                "glm": """
                As a creative fashion designer, develop 3 innovative fashion concepts based on the trend analysis.

                Trend Analysis: {analysis}

                For each concept, create:
                1. A memorable concept name
                2. Clear target audience definition
                3. Seasonal appropriateness
                4. Detailed silhouette description
                5. Material selection rationale
                6. Color palette justification
                7. Unique design details
                8. Supporting trend rationale

                Generate exactly 3 distinct concepts in JSON array format.
                """
            },
            "image_generation": {
                "z_image": {
                    "template": """
                    fashion photography, {style_description}, {materials}, {colors}, clean studio lighting, white background, professional lighting, 8k, high detail, sharp focus
                    """,
                    "negative": """
                    low quality, blurry, ugly, bad anatomy, deformed, disfigured, poor lighting, noisy, text, watermark, signature, cartoon, drawing, painting
                    """
                },
                "seedream": {
                    "template": """
                    Create a professional fashion photograph featuring {style_description}. The design should showcase {materials} in a palette dominated by {colors}. The lighting should be soft and flattering, creating depth and texture in the fabrics. Professional studio setting with clean background. Photorealistic style with exceptional detail and clarity.
                    """,
                    "negative": """
                    amateur photography, smartphone photo, blurry image, poor lighting, cluttered background, flash photography, harsh shadows, oversaturated colors, cartoon style, illustration, digital art
                    """
                },
                "nano_banana": {
                    "template": """
                    Hyperrealistic fashion photography of {style_description}. Premium {materials} fabric displayed in sophisticated {colors} color scheme. Professional studio lighting setup creating soft shadows and highlights that accentuate texture. Clean minimalist background. Ultra-high resolution, 8k quality, lifelike detail. Commercial fashion photography style.
                    """,
                    "negative": """
                    Low resolution, grainy, pixelated, artificial lighting, flat lighting, shadows, harsh contrast, overexposed, underexposed, amateur photography, snapshot style, unprofessional setting, digital art, 3D render
                    """
                }
            },
            "blueprint_generation": {
                "template": """
                    Fashion technical drawing blueprint, {style_description}, flat lay illustration, clean line art, technical fashion sketch, measurements included, side by side front and back views, professional drafting style, white background, black ink lines, precision drawing
                    """,
                    "negative": """
                    Photography, color image, shading, background, photo, 3d render, painting, artistic illustration, sketch drawing without measurements, informal style
                    """
                }
        }

    async def generate_prompt(
        self,
        concept: DesignConcept,
        prompt_type: PromptType,
        model: AIModel,
        width: Optional[int] = None,
        height: Optional[int] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> PromptSpec:
        """
        프롬프트 생성

        Args:
            concept: 디자인 컨셉
            prompt_type: 프롬프트 타입
            model: AI 모델
            width: 이미지 너비
            height: 이미지 높이
            additional_context: 추가 컨텍스트

        Returns:
            생성된 프롬프트 스펙
        """
        # 기본 프롬프트 생성
        base_prompt = await self._generate_base_prompt(
            concept, prompt_type, model, additional_context
        )

        # 모델별 최적화
        optimized_prompt = await self._optimize_for_model(
            base_prompt, model, prompt_type
        )

        # 네거티브 프롬프트
        negative_prompt = self._generate_negative_prompt(model, prompt_type)

        # PromptSpec 생성
        prompt_spec = PromptSpec(
            concept_id=concept.id if hasattr(concept, 'id') else None,
            prompt_type=prompt_type.value,
            model_name=model.value,
            base_prompt=base_prompt,
            optimized_prompt=optimized_prompt,
            negative_prompt=negative_prompt,
            original_language="ko",
            width=width or self._get_default_width(model, prompt_type),
            height=height or self._get_default_height(model, prompt_type),
            steps=self._get_default_steps(model),
            cfg_scale=self._get_default_cfg(model),
            metadata={
                'generation_date': get_local_now().isoformat(),
                'concept_name': concept.concept_name,
                'style_options': self._extract_style_options(concept)
            }
        )

        return prompt_spec

    async def _generate_base_prompt(
        self,
        concept: DesignConcept,
        prompt_type: PromptType,
        model: AIModel,
        additional_context: Optional[Dict[str, Any]]
    ) -> str:
        """기본 프롬프트 생성"""
        context_data = {
            'concept': concept,
            'type': prompt_type.value,
            'model': model.value
        }

        if additional_context:
            context_data.update(additional_context)

        # 컨셉 정보를 텍스트로 변환
        concept_text = f"""
        Concept: {concept.concept_name}
        Target: {concept.target_audience}
        Season: {concept.season}
        Silhouette: {concept.silhouette}
        Materials: {', '.join(concept.materials or [])}
        Colors: {', '.join(concept.color_palette or [])}
        Details: {concept.details or ''}
        Rationale: {concept.rationale or ''}
        """

        # 타입별 프롬프트 생성
        if prompt_type == PromptType.GARMENT:
            prompt = self._create_garment_prompt(concept_text, concept_text)
        elif prompt_type == PromptType.MODEL_FITTING:
            prompt = self._create_model_fitting_prompt(concept_text, concept_text)
        elif prompt_type == PromptType.BLUEPRINT:
            prompt = self._create_blueprint_prompt(concept_text, concept_text)
        else:
            prompt = concept_text

        return prompt

    def _create_garment_prompt(self, context: str, concept_text: str) -> str:
        """의상 프롬프트 생성"""
        return f"""
        Fashion garment design based on:
        {concept_text}

        Design specifications:
        - Front and back views
        - High detail fabric texture
        - Professional studio lighting
        - Clean white background
        - Photorealistic rendering
        """

    def _create_model_fitting_prompt(self, context: str, concept_text: str) -> str:
        """모델 착용 프롬프트 생성"""
        return f"""
        Fashion model wearing the design:
        {concept_text}

        Photography requirements:
        - Full body shot
        - Natural pose
        - Studio lighting
        - Fashion photography style
        - High resolution detail
        """

    def _create_blueprint_prompt(self, context: str, concept_text: str) -> str:
        """도면 프롬프트 생성"""
        return f"""
        Technical fashion blueprint based on:
        {concept_text}

        Drawing requirements:
        - Technical line art
        - Front and back views
        - Measurements and specifications
        - Professional drafting style
        - Clean white background
        """

    async def _optimize_for_model(
        self,
        prompt: str,
        model: AIModel,
        prompt_type: PromptType
    ) -> str:
        """모델별 프롬프트 최적화"""
        # 프롬프트 길이 조정
        config = PromptTemplate.get_config(model)
        max_length = config['max_tokens'] // 4  # 토큰당 4바이트 가정

        if len(prompt) > max_length:
            prompt = prompt[:max_length] + "..."

        # 모델별 스타일 적용
        if config['tag_style'] == 'tag-based':
            prompt = self._convert_to_tags(prompt, config)
        elif config['tag_style'] == 'detailed':
            prompt = self._add_descriptive_elements(prompt, prompt_type)
        elif config['tag_style'] == 'structured':
            prompt = self._add_structure(prompt, prompt_type)

        return prompt

    def _convert_to_tags(self, prompt: str, config: Dict[str, Any]) -> str:
        """태그 기반으로 변환"""
        # 핵심 키워드 추출
        keywords = self._extract_keywords(prompt)

        # 카테고리별 태그 추가
        tags = []

        if 'garment' in prompt.lower():
            tags.extend(['fashion', 'design', 'clothing'])

        if 'model' in prompt.lower():
            tags.extend(['fashion model', 'photography', 'pose'])

        if 'blueprint' in prompt.lower():
            tags.extend(['technical drawing', 'sketch', 'pattern'])

        # 키워드와 조합
        if keywords:
            tags.extend(keywords[:20])  # 최대 20개 키워드

        if tags:
            return f"{' '.join(tags)}, {prompt}"

        return prompt

    def _add_descriptive_elements(self, prompt: str, prompt_type: PromptType) -> str:
        """설명적 요소 추가"""
        if prompt_type == PromptType.GARMENT:
            descriptive = "detailed fashion design with intricate fabric patterns, professional photography"
        elif prompt_type == PromptType.MODEL_FITTING:
            descriptive = "professional fashion photography with model, dynamic pose, high-end lighting"
        elif prompt_type == PromptType.BLUEPRINT:
            descriptive = "technical fashion blueprint with precise measurements, professional drafting"
        else:
            descriptive = "professional fashion creation"

        return f"{prompt}, {descriptive}"

    def _add_structure(self, prompt: str, prompt_type: PromptType) -> str:
        """구조화된 형식 추가"""
        if prompt_type == PromptType.BLUEPRINT:
            return f"[FRONT VIEW] [BACK VIEW] [MEASUREMENTS] {prompt}"
        else:
            return f"[PROFESSIONAL] [HIGH QUALITY] {prompt}"

    def _generate_negative_prompt(self, model: AIModel, prompt_type: PromptType) -> str:
        """네거티브 프롬프트 생성"""
        # 모델별 템플릿 참조
        templates = self.templates.get('image_generation', {})
        model_map = {
            AIModel.Z_IMAGE_TURBO: "z_image",
            AIModel.SEEDREAM_4_5: "seedream",
            AIModel.NANO_BANANA: "nano_banana"
        }
        template_key = model_map.get(model)
        model_templates = templates.get(template_key, templates.get('nano_banana', {}))

        return model_templates.get('negative', '')

    def _get_default_width(self, model: AIModel, prompt_type: PromptType) -> int:
        """기본 너비 반환"""
        if prompt_type == PromptType.BLUEPRINT:
            return 1024
        elif model == AIModel.Z_IMAGE_TURBO:
            return 1024
        else:
            return 1024

    def _get_default_height(self, model: AIModel, prompt_type: PromptType) -> int:
        """기본 높이 반환"""
        if prompt_type == PromptType.BLUEPRINT:
            return 1024
        elif model == AIModel.Z_IMAGE_TURBO:
            return 1024
        else:
            return 1024

    def _get_default_steps(self, model: AIModel) -> int:
        """기본 단계 수 반환"""
        if model == AIModel.Z_IMAGE_TURBO:
            return 20
        elif model == AIModel.SEEDREAM_4_5:
            return 30
        elif model == AIModel.NANO_BANANA:
            return 25
        else:
            return 20

    def _get_default_cfg(self, model: AIModel) -> float:
        """기본 CFG 스케일 반환"""
        if model == AIModel.Z_IMAGE_TURBO:
            return 7.5
        elif model == AIModel.SEEDREAM_4_5:
            return 8.0
        elif model == AIModel.NANO_BANANA:
            return 7.0
        else:
            return 7.5

    def _extract_keywords(self, text: str) -> List[str]:
        """키워드 추출"""
        # 간단한 단어 필터링
        stop_words = {'the', 'of', 'and', 'in', 'to', 'a', 'is', 'it', 'that', 'for'}

        words = []
        current_word = []
        for char in text.lower():
            if char.isalnum() or char == "'":
                current_word.append(char)
            else:
                if current_word:
                    word = ''.join(current_word)
                    if len(word) > 2 and word not in stop_words:
                        words.append(word)
                    current_word = []

        if current_word:
            word = ''.join(current_word)
            if len(word) > 2 and word not in stop_words:
                words.append(word)

        return words

    def _extract_style_options(self, concept: DesignConcept) -> Dict[str, Any]:
        """스타일 옵션 추출"""
        return {
            'target_audience': concept.target_audience,
            'season': concept.season,
            'silhouette': concept.silhouette,
            'materials': concept.materials,
            'colors': concept.color_palette,
            'has_images': bool(concept.image_urls),
            'has_details': bool(concept.details)
        }

    async def batch_generate_prompts(
        self,
        concepts: List[DesignConcept],
        prompt_types: List[PromptType],
        model: AIModel
    ) -> List[PromptSpec]:
        """일괄 프롬프트 생성"""
        prompt_specs = []

        for concept in concepts:
            for prompt_type in prompt_types:
                prompt_spec = asyncio.create_task(
                    self.generate_prompt(concept, prompt_type, model)
                )
                prompt_specs.append(prompt_spec)

        # 태스크 실행 및 결과 수집
        return [await task for task in asyncio.as_completed(prompt_specs)]

    async def analyze_prompt_performance(
        self,
        prompt_spec: PromptSpec,
        generation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """프롬프트 성능 분석"""
        analysis = {
            'prompt_spec_id': prompt_spec.id,
            'generation_success': generation_result.get('success', False),
            'generation_time': generation_result.get('time', 0),
            'quality_metrics': {}
        }

        if generation_result.get('success'):
            # 품질 메트릭 계산
            analysis['quality_metrics'] = self._calculate_quality_metrics(
                prompt_spec, generation_result
            )

        return analysis

    def _calculate_quality_metrics(
        self,
        prompt_spec: PromptSpec,
        result: Dict[str, Any]
    ) -> Dict[str, float]:
        """품질 메트릭스 계산"""
        metrics = {}

        # 프롬프트 충실도 (시뮬레이션용)
        metrics['prompt_fidelity'] = self._calculate_prompt_fidelity(prompt_spec, result)

        # 모델별 최적화도
        metrics['model_optimization'] = self._calculate_model_optimization(prompt_spec)

        # 예측 가능성
        metrics['predictability'] = self._calculate_predictability(prompt_spec)

        return metrics

    def _calculate_prompt_fidelity(self, prompt_spec: PromptSpec, result: Dict[str, Any]) -> float:
        """프롬프트 충실도 계산"""
        # 구현 시 실제 생성 결과와 프롬프트 비교
        return 0.85  # 예시 값

    def _calculate_model_optimization(self, prompt_spec: PromptSpec) -> float:
        """모델별 최적화도 계산"""
        # 구현 시 프롬프트가 모델 특성에 맞게 최적화되었는지 평가
        return 0.90  # 예시 값

    def _calculate_predictability(self, prompt_spec: PromptSpec) -> float:
        """예측 가능성 계산"""
        # 구현 시 프롬프트의 구체성과 예측 가능성 평가
        return 0.88  # 예시 값


class PromptTranslator:
    """프롬프트 번역기"""

    def __init__(self):
        """초기화"""
        self.translation_service = None  # 실제로는 번역 API 연동

    async def translate_to_english(self, text: str) -> str:
        """영어로 번역"""
        # 실제 구현 시 AI 번역 API 사용
        # 여기서는 간단한 구현
        return text

    async def translate_to_korean(self, text: str) -> str:
        """한국어로 번역"""
        # 실제 구현 시 AI 번역 API 사용
        # 여기서는 간단한 구현
        return text

    def detect_language(self, text: str) -> str:
        """언어 감지"""
        # 실제 구현시 언어 감지 라이브러리 사용
        return "ko" if any('\u3131' <= char <= '\u3163' or '\uac00' <= char <= '\ud7a3' for char in text) else "en"
