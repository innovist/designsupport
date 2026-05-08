"""
Image generation service for fashion designs
"""

# @MX:NOTE: [AUTO] Image generation service - multi-provider AI image generation orchestration
# Manages Z-Image, Seedream, and Nano Banana clients with fallback and retry logic

import asyncio
import io
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import base64
import json

from PIL import Image, ImageOps
import numpy as np

from app.core.config import get_config
from app.core.logging import get_logger
from app.core.settings_storage import get_gemini_model
from app.utils.system_detector import detect_gpu_availability
from ai_clients.zimage_client import ZImageClient, get_zimage_client
from ai_clients.seedream_client import SeedreamClient, get_seedream_client
from ai_clients.nano_banana_client import NanoBananaClient, get_nano_banana_client
from ai_clients.gemini_client import GeminiClient, get_gemini_client

logger = get_logger(__name__)
config = get_config()


@dataclass
class ImageGenerationRequest:
    """이미지 생성 요청"""
    prompt: str
    style: str = "modern"
    garment_type: str = "dress"
    color_scheme: Optional[str] = None
    fabric_type: Optional[str] = None
    reference_image: Optional[Union[str, bytes]] = None
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    num_variations: int = 1
    width: int = 1024
    height: int = 1024
    quality: str = "high"  # low, medium, high, ultra
    model_preference: Optional[str] = None  # zimage, seedream, nano_banana
    is_children_clothing: bool = False  # 아동복 여부


@dataclass
class ImageGenerationResult:
    """이미지 생성 결과"""
    images: List[bytes]
    model_used: str
    generation_time: float
    prompt: str
    metadata: Dict[str, Any]
    variations: Optional[List[bytes]] = None


class ImageGenerationService:
    """이미지 생성 서비스"""

    def __init__(self):
        """초기화"""
        self.zimage_client = get_zimage_client()
        self.seedream_client = get_seedream_client()
        self.nano_banana_client = get_nano_banana_client()
        self.gemini_client = get_gemini_client()

        # 모델 우선순위
        self.model_priority = {
            "fashion_design": ["zimage", "seedream", "nano_banana"],
            "sketch": ["nano_banana", "seedream", "zimage"],
            "pattern": ["seedream", "nano_banana", "zimage"],
            "texture": ["seedream", "zimage", "nano_banana"],
            "model_fitting": ["zimage", "seedream", "nano_banana"]
        }

        # 품질별 설정
        self.quality_settings = {
            "low": {"steps": 20, "guidance_scale": 7.0},
            "medium": {"steps": 30, "guidance_scale": 7.5},
            "high": {"steps": 40, "guidance_scale": 8.0},
            "ultra": {"steps": 50, "guidance_scale": 8.5}
        }

        self._gpu_available: Optional[bool] = None
        self._gpu_info: Optional[str] = None

    async def generate_fashion_design(
        self,
        request: ImageGenerationRequest
    ) -> ImageGenerationResult:
        """
        패션 디자인 이미지 생성

        Args:
            request: 이미지 생성 요청

        Returns:
            생성된 이미지 결과
        """
        start_time = asyncio.get_event_loop().time()

        # 프롬프트 최적화
        optimized_prompt = await self._optimize_prompt_for_fashion(
            prompt=request.prompt,
            style=request.style,
            garment_type=request.garment_type,
            color_scheme=request.color_scheme,
            fabric_type=request.fabric_type,
            is_children_clothing=request.is_children_clothing
        )

        # 모델 선택
        task_type = "model_fitting" if request.garment_type == "model_fitting" else "fashion_design"
        selected_models = self._select_models(
            task_type=task_type,
            preference=request.model_preference
        )

        # 이미지 생성 시도
        last_error = None
        for model_name in selected_models:
            try:
                logger.info(f"Attempting generation with {model_name}")

                if model_name == "zimage":
                    result = await self._generate_with_zimage(
                        optimized_prompt, request
                    )
                elif model_name == "seedream":
                    result = await self._generate_with_seedream(
                        optimized_prompt, request
                    )
                elif model_name == "nano_banana":
                    result = await self._generate_with_nano_banana(
                        optimized_prompt, request
                    )
                else:
                    continue

                generation_time = asyncio.get_event_loop().time() - start_time

                # 이미지 후처리
                processed_images = []
                for img in result.images:
                    processed = await self._post_process_image(img)
                    processed_images.append(processed)

                # 변형 생성
                variations = None
                if request.num_variations > 1:
                    variations = await self._generate_variations(
                        processed_images[0],
                        request.num_variations - 1,
                        optimized_prompt
                    )

                return ImageGenerationResult(
                    images=processed_images,
                    model_used=model_name,
                    generation_time=generation_time,
                    prompt=optimized_prompt,
                    metadata=result.metadata,
                    variations=variations
                )

            except Exception as e:
                last_error = e
                logger.warning(f"Model {model_name} failed: {str(e)}")
                continue

        # 모든 모델 실패
        raise Exception(f"All models failed. Last error: {last_error}")

    async def _optimize_prompt_for_fashion(
        self,
        prompt: str,
        style: str,
        garment_type: str,
        color_scheme: Optional[str] = None,
        fabric_type: Optional[str] = None,
        is_children_clothing: bool = False
    ) -> str:
        """패션 프롬프트 최적화"""

        # 아동복 여부에 따른 추가 지시사항
        kids_instruction = ""
        if is_children_clothing:
            kids_instruction = """
            IMPORTANT: This is for CHILDREN'S CLOTHING.
            - Specify age-appropriate child model (6-12 years old)
            - Emphasize kids' fashion proportions (smaller body, youthful features)
            - NO adult features, NO mature elements
            - Use keywords: "child model", "kids fashion", "age-appropriate"
            """

        # Gemini를 사용한 프롬프트 최적화
        optimization_prompt = f"""
        Optimize this fashion design prompt for AI image generation:

        Original Prompt: {prompt}
        Style: {style}
        Garment Type: {garment_type}
        Color Scheme: {color_scheme or 'not specified'}
        Fabric Type: {fabric_type or 'not specified'}
        {kids_instruction}

        Create an enhanced prompt that:
        1. Is specific and detailed
        2. Includes professional fashion terminology
        3. Specifies lighting and composition
        4. Mentions quality and detail level
        5. Excludes: text, letters, watermarks, logos, magazine covers

        Return only the optimized prompt without explanation.
        """

        try:
            response = await self.gemini_client.generate_content(
                optimization_prompt,
                model=get_gemini_model()
            )
            optimized = response.text.strip()
            # 아동복인 경우 추가 안전장치
            if is_children_clothing:
                safe_suffixes = [
                    "child model", "kids fashion", "age-appropriate",
                    "6-12 years old", "kids wear"
                ]
                if not any(s in optimized.lower() for s in safe_suffixes):
                    optimized += ", child model (6-12 years old), kids fashion"
            return optimized
        except Exception as e:
            logger.warning(f"Prompt optimization failed: {str(e)}")
            # 폴백으로 수동 최적화
            fallback = f"Professional fashion design of a {garment_type}, {prompt}, style: {style}, high quality, detailed, studio lighting"
            if is_children_clothing:
                fallback += ", child model (6-12 years old), kids fashion"
            return fallback

    def _is_gpu_available(self) -> bool:
        if not config.gpu_enabled:
            return False
        if self._gpu_available is None:
            self._gpu_available, self._gpu_info = detect_gpu_availability()
        return bool(self._gpu_available)

    def _is_zimage_available(self) -> bool:
        if not self.zimage_client or not self.zimage_client.api_key:
            return False
        return self._is_gpu_available()

    def _get_available_models(self, task_type: str) -> List[str]:
        candidates = list(self.model_priority.get(task_type, ["zimage", "seedream", "nano_banana"]))
        if "zimage" in candidates and not self._is_zimage_available():
            candidates = [model for model in candidates if model != "zimage"]
        return candidates

    def _select_models(
        self,
        task_type: str,
        preference: Optional[str] = None
    ) -> List[str]:
        """작업에 적합한 모델 선택"""
        available_models = self._get_available_models(task_type)
        if not available_models:
            raise ValueError("No available image models for generation")

        # 선호 모델이 지정된 경우
        if preference and preference in ["zimage", "seedream", "nano_banana"]:
            if preference in available_models:
                return [preference] + [m for m in available_models if m != preference]
            logger.warning(f"Preferred model unavailable: {preference}. Available: {available_models}")

        # 기본 우선순위 반환
        return available_models

    async def _generate_with_zimage(
        self,
        prompt: str,
        request: ImageGenerationRequest
    ) -> ImageGenerationResult:
        """Z-Image로 이미지 생성"""

        from ai_clients.zimage_client import ImageGenerationConfig

        config = ImageGenerationConfig(
            width=request.width,
            height=request.height,
            **self.quality_settings[request.quality],
            model="stable-diffusion-xl-fashion"
        )

        if request.negative_prompt:
            config.negative_prompt = request.negative_prompt
        if request.seed is not None:
            config.seed = request.seed

        response = await self.zimage_client.generate_image(
            prompt=prompt,
            config=config,
            reference_image=request.reference_image,
            controlnet_type="scribble" if request.reference_image else None
        )

        return ImageGenerationResult(
            images=response.images,
            model_used="zimage",
            generation_time=response.generation_time,
            prompt=prompt,
            metadata={
                "seed": response.seed,
                "nsfw_detected": response.nsfw_detected,
                "model": response.model
            }
        )

    async def _generate_with_seedream(
        self,
        prompt: str,
        request: ImageGenerationRequest
    ) -> ImageGenerationResult:
        """Seedream으로 이미지 생성"""

        from ai_clients.seedream_client import SeedreamGenerationConfig

        config = SeedreamGenerationConfig(
            width=request.width,
            height=request.height,
            **self.quality_settings[request.quality]
        )

        if request.negative_prompt:
            config.negative_prompt = request.negative_prompt
        if request.seed is not None:
            config.seed = request.seed

        response = await self.seedream_client.generate_image(
            prompt=prompt,
            config=config,
            reference_image=request.reference_image,
            ip_adapter_image=request.reference_image
        )

        return ImageGenerationResult(
            images=response.images,
            model_used="seedream",
            generation_time=response.generation_time,
            prompt=prompt,
            metadata={
                "seed": response.seed,
                "safety_check_passed": response.safety_check_passed,
                "model": response.model
            }
        )

    async def _generate_with_nano_banana(
        self,
        prompt: str,
        request: ImageGenerationRequest
    ) -> ImageGenerationResult:
        """Nano Banana로 이미지 생성"""

        from ai_clients.nano_banana_client import NanoBananaGenerationConfig

        config = NanoBananaGenerationConfig(
            width=request.width,
            height=request.height,
            **self.quality_settings[request.quality]
        )

        if request.negative_prompt:
            config.negative_prompt = request.negative_prompt
        if request.seed is not None:
            config.seed = request.seed

        response = await self.nano_banana_client.generate_image(
            prompt=prompt,
            config=config,
            control_image=request.reference_image,
            control_type="depth" if request.reference_image else None
        )

        return ImageGenerationResult(
            images=response.images,
            model_used="nano_banana",
            generation_time=response.generation_time,
            prompt=prompt,
            metadata={
                "seed": response.seed,
                "nsfw_score": response.nsfw_score,
                "model": response.model
            }
        )

    async def _post_process_image(self, image: bytes) -> bytes:
        """이미지 후처리"""

        try:
            # 이미지 로드
            img = Image.open(io.BytesIO(image))

            # EXIF 데이터 기반 회전 수정
            img = ImageOps.exif_transpose(img)

            # RGB로 변환
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # 최대 크기 제한
            max_size = 2048
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # 출력을 바이트로 변환
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=95, optimize=True)
            output.seek(0)

            return output.read()

        except Exception as e:
            logger.error(f"Image post-processing failed: {str(e)}")
            return image  # 원본 이미지 반환

    async def _generate_variations(
        self,
        base_image: bytes,
        num_variations: int,
        prompt: str
    ) -> List[bytes]:
        """이미지 변형 생성"""

        variations = []

        # 현재는 Nano Banana의 컬러 변형 기능 사용
        # 추후 각 모델의 특화 기능으로 확장
        color_schemes = [
            "monochrome",
            "vibrant",
            "pastel",
            "warm",
            "cool"
        ]

        for i in range(min(num_variations, len(color_schemes))):
            try:
                color_variations = await self.nano_banana_client.generate_color_variations(
                    base_image=base_image,
                    color_schemes=[color_schemes[i]]
                )

                if color_variations:
                    variations.append(color_variations[0])

            except Exception as e:
                logger.warning(f"Variation generation failed: {str(e)}")
                continue

        return variations

    async def generate_fashion_collection(
        self,
        theme: str,
        garments: List[str],
        style: str = "modern",
        color_palette: Optional[List[str]] = None,
        mood_board: Optional[Union[str, bytes]] = None
    ) -> List[ImageGenerationResult]:
        """
        패션 컬렉션 생성

        Args:
            theme: 컬렉션 테마
            garments: 의류 목록
            style: 스타일
            color_palette: 색상 팔레트
            mood_board: 무드 보드

        Returns:
            생성된 컬렉션 이미지 결과 목록
        """

        # Seedream을 사용한 컬렉션 생성
        try:
            responses = await self.seedream_client.generate_fashion_collection(
                theme=theme,
                garments=garments,
                style=style,
                color_palette=color_palette,
                mood_board=mood_board
            )

            results = []
            for i, response in enumerate(responses):
                processed_images = []
                for img in response.images:
                    processed = await self._post_process_image(img)
                    processed_images.append(processed)

                result = ImageGenerationResult(
                    images=processed_images,
                    model_used="seedream",
                    generation_time=response.generation_time,
                    prompt=response.prompt,
                    metadata={
                        "seed": response.seed,
                        "safety_check_passed": response.safety_check_passed,
                        "model": response.model,
                        "garment": garments[i],
                        "collection_theme": theme
                    }
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Collection generation failed: {str(e)}")
            # 각 의류 개별 생성으로 폴백
            results = []
            for garment in garments:
                request = ImageGenerationRequest(
                    prompt=f"{theme} {garment}",
                    style=style,
                    garment_type=garment,
                    reference_image=mood_board
                )

                try:
                    result = await self.generate_fashion_design(request)
                    result.metadata["collection_theme"] = theme
                    result.metadata["garment"] = garment
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to generate {garment}: {str(e)}")
                    continue

            return results

    async def generate_technical_sketch(
        self,
        design_description: str,
        garment_type: str,
        include_measurements: bool = False
    ) -> ImageGenerationResult:
        """
        기술적 스케치 생성

        Args:
            design_description: 디자인 설명
            garment_type: 의류 타입
            include_measurements: 치수 표시 여부

        Returns:
            생성된 스케치 결과
        """

        # Nano Banana를 사용한 스케치 생성
        response = await self.nano_banana_client.generate_fashion_sketch(
            design_description=design_description,
            sketch_style="technical",
            annotations=include_measurements
        )

        processed_images = []
        for img in response.images:
            processed = await self._post_process_image(img)
            processed_images.append(processed)

        return ImageGenerationResult(
            images=processed_images,
            model_used="nano_banana",
            generation_time=response.generation_time,
            prompt=response.prompt,
            metadata={
                "seed": response.seed,
                "nsfw_score": response.nsfw_score,
                "model": response.model,
                "garment_type": garment_type,
                "include_measurements": include_measurements
            }
        )

    async def cleanup(self):
        """리소스 정리"""
        await self.zimage_client.cleanup()
        await self.seedream_client.cleanup()
        await self.nano_banana_client.cleanup()
        await self.gemini_client.cleanup()
        logger.info("Image generation service cleaned up")


# 전역 서비스 인스턴스
_image_generation_service = None


def get_image_generation_service() -> ImageGenerationService:
    """이미지 생성 서비스 인스턴스 가져오기"""
    global _image_generation_service
    if _image_generation_service is None:
        _image_generation_service = ImageGenerationService()
    return _image_generation_service


# FastAPI 의존성 주입용
async def get_image_generation_service_dep():
    """FastAPI 의존성 주입용 이미지 생성 서비스"""
    service = get_image_generation_service()
    try:
        yield service
    finally:
        await service.cleanup()
