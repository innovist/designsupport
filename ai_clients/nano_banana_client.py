"""
Nano Banana AI client implementation for fashion image generation
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import base64
import io

import aiohttp
from PIL import Image

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.settings_storage import (
    get_nano_banana_base_model,
    get_nano_banana_model,
    get_nano_banana_model_id,
    get_nano_banana_pro_model
)

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class NanoBananaGenerationConfig:
    """Nano Banana 생성 설정"""
    width: int = 1024
    height: int = 1024
    steps: int = 30
    guidance_scale: float = 7.5
    seed: Optional[int] = None
    negative_prompt: Optional[str] = None
    num_images: int = 1
    model: str = field(default_factory=get_nano_banana_model)
    purpose: str = "general"
    sampler: str = "DPM++ 2M Karras"
    cfg_scale: float = 7.5


@dataclass
class NanoBananaResponse:
    """Nano Banana 응답"""
    images: List[bytes]  # Base64 decoded images
    model: str
    generation_time: float
    prompt: str
    seed: Optional[int] = None
    nsfw_score: Optional[float] = None


class NanoBananaClient:
    """Nano Banana AI 클라이언트"""

    def __init__(self):
        """초기화"""
        self.base_url = settings.nano_banana_api_url or "https://api.nano-banana.ai/v1"
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5분 타임아웃

    @staticmethod
    def _is_google_key(api_key: str) -> bool:
        return api_key.startswith("AIza")

    @staticmethod
    def _resolve_variant(
        config: NanoBananaGenerationConfig,
        control_image: Optional[Union[str, bytes]]
    ) -> str:
        model_name = (config.model or "").strip().lower()
        base_aliases = {
            "nano-banana-base",
            "nano-banana-v1",
            "nano-banana-v2",
            "nano-banana-v2-sketch",
            "nano-banana-v2-product",
            "nano-banana-v2-fabric"
        }
        pro_aliases = {"nano-banana-pro", "nano-banana-v2-pro"}
        if model_name in pro_aliases:
            return get_nano_banana_pro_model()
        if config.purpose in {"sketch", "layout", "pattern", "variation"}:
            return get_nano_banana_base_model()
        if model_name in base_aliases:
            if config.steps >= 40 or control_image:
                return get_nano_banana_pro_model()
            return get_nano_banana_base_model()
        if "pro" in model_name:
            return get_nano_banana_pro_model()
        if config.steps >= 40 or control_image:
            return get_nano_banana_pro_model()
        return get_nano_banana_base_model()

    @staticmethod
    def _select_google_model(
        config: NanoBananaGenerationConfig,
        control_image: Optional[Union[str, bytes]]
    ) -> str:
        variant = NanoBananaClient._resolve_variant(config, control_image)
        return get_nano_banana_model_id(variant, provider="google")

    @staticmethod
    def _normalize_image_bytes(image: Union[str, bytes]) -> bytes:
        if isinstance(image, str):
            with open(image, "rb") as f:
                image = f.read()
        if not image:
            return b""
        try:
            with Image.open(io.BytesIO(image)) as img:
                output = io.BytesIO()
                img.save(output, format="PNG")
                return output.getvalue()
        except Exception:
            return image

    @staticmethod
    def _extract_google_images(response: Any) -> List[bytes]:
        images: List[bytes] = []
        for cand in getattr(response, "candidates", []) or []:
            content = getattr(cand, "content", None)
            for part in getattr(content, "parts", []) or []:
                inline = getattr(part, "inline_data", None)
                data = getattr(inline, "data", None)
                if isinstance(data, (bytes, bytearray)) and data:
                    images.append(bytes(data))
        return images

    def _sync_google_generate(
        self,
        api_key: str,
        model_id: str,
        prompt: str,
        seed: Optional[int],
        control_image: Optional[Union[str, bytes]]
    ) -> List[bytes]:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        contents = []
        if control_image:
            safe_bytes = self._normalize_image_bytes(control_image)
            contents.append(types.Part.from_bytes(data=safe_bytes, mime_type="image/png"))
        contents.append(prompt)

        gen_config = types.GenerateContentConfig(response_modalities=["IMAGE"])
        if isinstance(seed, int):
            gen_config.seed = seed

        response = client.models.generate_content(model=model_id, contents=contents, config=gen_config)
        return self._extract_google_images(response)

    async def _generate_with_google(
        self,
        api_key: str,
        prompt: str,
        config: NanoBananaGenerationConfig,
        control_image: Optional[Union[str, bytes]]
    ) -> NanoBananaResponse:
        model_id = self._select_google_model(config, control_image)
        start_time = asyncio.get_event_loop().time()
        images = await asyncio.to_thread(
            self._sync_google_generate,
            api_key,
            model_id,
            prompt,
            config.seed,
            control_image
        )
        if not images:
            raise ValueError("No images returned from Google GenAI")
        generation_time = asyncio.get_event_loop().time() - start_time
        return NanoBananaResponse(
            images=images,
            model=model_id,
            generation_time=generation_time,
            prompt=prompt,
            seed=config.seed,
            nsfw_score=None
        )

    async def generate_image(
        self,
        prompt: str,
        config: Optional[NanoBananaGenerationConfig] = None,
        control_image: Optional[Union[str, bytes]] = None,
        control_type: Optional[str] = None,
        lora_path: Optional[str] = None
    ) -> NanoBananaResponse:
        """
        패션 이미지 생성

        Args:
            prompt: 생성 프롬프트
            config: 생성 설정
            control_image: 컨트롤 이미지
            control_type: 컨트롤 타입 (canny, depth, pose, etc.)
            lora_path: LoRA 모델 경로

        Returns:
            생성된 이미지 응답
        """
        if config is None:
            config = NanoBananaGenerationConfig()

        api_key = settings.nano_banana_api_key
        if not api_key:
            raise ValueError("No Nano Banana API key configured")

        config.model = self._resolve_variant(config, control_image)

        last_error = None
        if self._is_google_key(api_key):
            try:
                return await self._generate_with_google(api_key, prompt, config, control_image)
            except Exception as exc:
                last_error = exc
                logger.warning(f"Google GenAI generation failed, falling back to REST API: {exc}")

        max_retries = 3

        for attempt in range(max_retries):
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                # 요청 데이터 구성
                rest_model = get_nano_banana_model_id(config.model, provider="rest")
                data = {
                    "prompt": prompt,
                    "model": rest_model,
                    "width": config.width,
                    "height": config.height,
                    "steps": config.steps,
                    "cfg_scale": config.cfg_scale,
                    "num_images": config.num_images,
                    "sampler": config.sampler
                }

                if config.negative_prompt:
                    data["negative_prompt"] = config.negative_prompt

                if config.seed:
                    data["seed"] = config.seed

                # 컨트롤 이미지 처리
                if control_image and control_type:
                    image_base64 = await self._encode_image(control_image)
                    data["control"] = {
                        "image": image_base64,
                        "type": control_type
                    }

                # LoRA 모델 적용
                if lora_path:
                    data["lora"] = {
                        "path": lora_path,
                        "weight": 0.8
                    }

                start_time = asyncio.get_event_loop().time()

                # API 호출
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        f"{self.base_url}/generate",
                        headers=headers,
                        json=data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                        else:
                            error_text = await response.text()
                            raise Exception(f"API returned {response.status}: {error_text}")

                generation_time = asyncio.get_event_loop().time() - start_time

                # 응답 처리
                images = []
                for image_data in result.get("images", []):
                    if isinstance(image_data, str):
                        # Base64 encoded
                        images.append(base64.b64decode(image_data))
                    else:
                        # URL
                        async with aiohttp.ClientSession() as session:
                            async with session.get(image_data) as img_response:
                                images.append(await img_response.read())

                response_obj = NanoBananaResponse(
                    images=images,
                    model=rest_model,
                    generation_time=generation_time,
                    prompt=prompt,
                    seed=result.get("seed"),
                    nsfw_score=result.get("nsfw_score")
                )

                logger.info(f"Successfully generated image with Nano Banana in {generation_time:.2f}s")
                return response_obj

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed for Nano Banana: {str(e)}")

                # API 키 오류 시 로깅만 수행
                if "quota" in str(e).lower() or "rate" in str(e).lower() or "unauthorized" in str(e).lower():
                    logger.warning(f"API quota/rate limit/unauthorized error: {str(e)}")

                # 재시도 전 대기
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # 모든 재시도 실패
        logger.error(f"All {max_retries} attempts failed for Nano Banana: {last_error}")
        raise last_error if last_error else Exception("All image generation attempts failed")

    async def _encode_image(self, image: Union[str, bytes]) -> str:
        """이미지를 base64로 인코딩"""
        if isinstance(image, str):
            with open(image, "rb") as f:
                image_data = f.read()
        else:
            image_data = image
        return base64.b64encode(image_data).decode('utf-8')

    async def generate_fashion_sketch(
        self,
        design_description: Optional[str] = None,
        sketch_style: str = "technical",
        line_weight: str = "medium",
        annotations: bool = False,
        description: Optional[str] = None
    ) -> NanoBananaResponse:
        """
        패션 스케치 생성

        Args:
            design_description: 디자인 설명
            sketch_style: 스케치 스타일 (technical, artistic, minimal)
            line_weight: 선 두께 (light, medium, heavy)
            annotations: 주석 포함 여부

        Returns:
            생성된 패션 스케치
        """
        if not design_description:
            design_description = description or ""
        if not design_description:
            raise ValueError("Design description is required for sketch generation")
        # 패션 스케치 프롬프트
        prompt_parts = [
            f"Fashion sketch of {design_description}",
            f"Style: {sketch_style} sketch",
            f"Line weight: {line_weight}",
            "Black and white line drawing",
            "Clean lines",
            "Professional fashion illustration",
            "Technical drawing"
        ]

        if annotations:
            prompt_parts.append("Design annotations and measurements")

        prompt = ", ".join(prompt_parts)

        # 네거티브 프롬프트
        negative_prompt = (
            "color, shading, texture, background, person, model, "
            "blurry, messy, unfinished"
        )

        # 생성 설정
        config = NanoBananaGenerationConfig(
            width=1024,
            height=1024,
            steps=25,
            cfg_scale=9.0,  # Higher for more precise control
            negative_prompt=negative_prompt,
            purpose="sketch"
        )

        response = await self.generate_image(prompt=prompt, config=config)
        logger.info(f"Generated fashion sketch: {design_description}")
        return response

    async def generate_flat_lay(
        self,
        garment_type: str,
        design_features: List[str],
        view_angle: str = "top",
        lighting: str = "studio"
    ) -> NanoBananaResponse:
        """
        평면 레이아웃 이미지 생성

        Args:
            garment_type: 의류 타입
            design_features: 디자인 특징 목록
            view_angle: 뷰 각도 (top, angled, 45-degree)
            lighting: 조명 (studio, natural, dramatic)

        Returns:
            생성된 평면 레이아웃 이미지
        """
        # 평면 레이아웃 프롬프트
        prompt_parts = [
            f"Flat lay photography of {garment_type}",
            f"Design features: {', '.join(design_features)}",
            f"View angle: {view_angle}",
            f"Lighting: {lighting}",
            "Clean white background",
            "Product photography",
            "E-commerce style",
            "Professional lighting",
            "Detailed garment construction visible"
        ]

        prompt = ", ".join(prompt_parts)

        # 네거티브 프롬프트
        negative_prompt = (
            "person, mannequin, hanger, wrinkle, dirty, "
            "blurry, low quality, bad lighting"
        )

        # 생성 설정
        config = NanoBananaGenerationConfig(
            width=1024,
            height=1024,
            steps=30,
            cfg_scale=7.5,
            negative_prompt=negative_prompt,
            purpose="layout"
        )

        response = await self.generate_image(prompt=prompt, config=config)
        logger.info(f"Generated flat lay for {garment_type}")
        return response

    async def generate_color_variations(
        self,
        base_image: Union[str, bytes],
        color_schemes: List[str],
        preserve_shadows: bool = True
    ) -> List[bytes]:
        """
        색상 변형 생성

        Args:
            base_image: 기본 이미지
            color_schemes: 색상 구성 목록
            preserve_shadows: 그림자 보존 여부

        Returns:
            생성된 색상 변형 이미지 목록
        """
        variations = []

        api_key = settings.nano_banana_api_key
        if api_key and self._is_google_key(api_key):
            base_variant = get_nano_banana_base_model()
            model_id = get_nano_banana_model_id(base_variant, provider="google")
            for color_scheme in color_schemes:
                instruction = (
                    f"Recolor this garment with a {color_scheme} palette. "
                    "Preserve texture, fabric detail, and shadows."
                    if preserve_shadows
                    else f"Recolor this garment with a {color_scheme} palette."
                )
                try:
                    images = await asyncio.to_thread(
                        self._sync_google_generate,
                        api_key,
                        model_id,
                        instruction,
                        None,
                        base_image
                    )
                    if images:
                        variations.append(images[0])
                except Exception as e:
                    logger.warning(f"Google GenAI color variation failed: {e}")
            return variations

        for color_scheme in color_schemes:
            max_retries = 3
            last_error = None

            for attempt in range(max_retries):
                try:
                    api_key = settings.nano_banana_api_key
                    if not api_key:
                        raise ValueError("No Nano Banana API key configured")

                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }

                    # 이미지를 base64로 변환
                    image_base64 = await self._encode_image(base_image)

                    data = {
                        "image": image_base64,
                        "color_scheme": color_scheme,
                        "preserve_shadows": preserve_shadows
                    }

                    async with aiohttp.ClientSession(timeout=self.timeout) as session:
                        async with session.post(
                            f"{self.base_url}/colorize",
                            headers=headers,
                            json=data
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                colored_image = base64.b64decode(result["image"])
                                variations.append(colored_image)
                                break
                            else:
                                error_text = await response.text()
                                raise Exception(f"API returned {response.status}: {error_text}")

                except Exception as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt + 1} failed for color variation: {str(e)}")

                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)

        logger.info(f"Generated {len(variations)} color variations")
        return variations

    async def generate_fabric_simulation(
        self,
        fabric_type: str,
        garment_pattern: Optional[Union[str, bytes]] = None,
        drape_style: str = "natural",
        environment: str = "studio"
    ) -> NanoBananaResponse:
        """
        패브릭 시뮬레이션 생성

        Args:
            fabric_type: 패브릭 타입
            garment_pattern: 의류 패턴
            drape_style: 드레이프 스타일
            environment: 환경

        Returns:
            생성된 패브릭 시뮬레이션
        """
        # 패브릭 시뮬레이션 프롬프트
        prompt_parts = [
            f"Realistic {fabric_type} fabric simulation",
            f"Drape style: {drape_style}",
            f"Environment: {environment}",
            "Photorealistic fabric rendering",
            "Accurate physics simulation",
            "Natural fabric behavior",
            "High resolution texture"
        ]

        prompt = ", ".join(prompt_parts)

        # 생성 설정
        config = NanoBananaGenerationConfig(
            width=1024,
            height=1024,
            steps=40,
            cfg_scale=7.0,
            purpose="fabric"
        )

        response = await self.generate_image(
            prompt=prompt,
            config=config,
            control_image=garment_pattern,
            control_type="depth"
        )

        logger.info(f"Generated fabric simulation for {fabric_type}")
        return response

    async def get_model_list(self) -> List[Dict[str, Any]]:
        """
        사용 가능한 모델 목록 조회

        Returns:
            모델 목록
        """
        try:
            api_key = settings.nano_banana_api_key
            if not api_key:
                return []

            headers = {
                "Authorization": f"Bearer {api_key}"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Failed to get model list: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Failed to get model list: {str(e)}")
            return []

    async def validate_key(self, api_key: str) -> bool:
        """
        API 키 유효성 검사

        Args:
            api_key: 검사할 API 키

        Returns:
            유효성 여부
        """
        try:
            headers = {
                "Authorization": f"Bearer {api_key}"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/status",
                    headers=headers
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False

    async def cleanup(self):
        """리소스 정리"""
        logger.info("Nano Banana client cleaned up")


# 전역 클라이언트 인스턴스
_nano_banana_client = None


def get_nano_banana_client() -> NanoBananaClient:
    """Nano Banana 클라이언트 인스턴스 가져오기"""
    global _nano_banana_client
    if _nano_banana_client is None:
        _nano_banana_client = NanoBananaClient()
    return _nano_banana_client


# FastAPI 의존성 주입용
async def get_nano_banana_client_dep():
    """FastAPI 의존성 주입용 Nano Banana 클라이언트"""
    client = get_nano_banana_client()
    try:
        yield client
    finally:
        await client.cleanup()
