"""
Seedream (Bytedance) AI client implementation for fashion image generation
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
from app.core.settings_storage import get_seedream_model, get_seedream_model_id

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class SeedreamGenerationConfig:
    """Seedream 생성 설정"""
    width: int = 1024
    height: int = 1024
    steps: int = 30
    guidance_scale: float = 7.5
    seed: Optional[int] = None
    negative_prompt: Optional[str] = None
    num_images: int = 1
    model: str = field(default_factory=get_seedream_model)
    response_format: str = "b64_json"
    watermark: bool = False
    scheduler: str = "FlowMatch"
    ip_adapter_strength: float = 0.7
    controlnet_strength: float = 1.0


@dataclass
class SeedreamResponse:
    """Seedream 응답"""
    images: List[bytes]  # Base64 decoded images
    model: str
    generation_time: float
    prompt: str
    seed: Optional[int] = None
    safety_check_passed: Optional[bool] = None


class SeedreamClient:
    """Seedream AI 클라이언트"""

    def __init__(self):
        """초기화"""
        self.base_url = (settings.seedream_api_url or "https://ark.ap-southeast.bytepluses.com/api/v3").rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5분 타임아웃

    async def generate_image(
        self,
        prompt: str,
        config: Optional[SeedreamGenerationConfig] = None,
        reference_image: Optional[Union[str, bytes]] = None,
        ip_adapter_image: Optional[Union[str, bytes]] = None,
        controlnet_type: Optional[str] = None
    ) -> SeedreamResponse:
        """
        패션 이미지 생성

        Args:
            prompt: 생성 프롬프트
            config: 생성 설정
            reference_image: 참조 이미지 (파일 경로 또는 바이츠)
            ip_adapter_image: IP-Adapter 이미지
            controlnet_type: ControlNet 타입 (canny, depth, pose, etc.)

        Returns:
            생성된 이미지 응답
        """
        if config is None:
            config = SeedreamGenerationConfig()

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                api_key = settings.seedream_api_key
                if not api_key:
                    raise ValueError("No Seedream API key configured")

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                # 요청 데이터 구성 (BytePlus ModelArk OpenAI-compatible)
                model_id = get_seedream_model_id(config.model)
                data = {
                    "model": model_id,
                    "prompt": prompt,
                    "image_size": {"width": config.width, "height": config.height},
                    "response_format": config.response_format,
                    "watermark": config.watermark
                }

                if isinstance(config.num_images, int) and config.num_images > 1:
                    data["n"] = config.num_images

                if config.negative_prompt:
                    data["negative_prompt"] = config.negative_prompt

                if config.seed is not None:
                    data["seed"] = config.seed

                image_urls = []
                for img in [reference_image, ip_adapter_image]:
                    if img:
                        image_base64 = await self._encode_image(img)
                        image_urls.append(f"data:image/png;base64,{image_base64}")

                if image_urls:
                    data["image_urls"] = image_urls[:14]

                start_time = asyncio.get_event_loop().time()

                # API 호출
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        f"{self.base_url}/images/generations",
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
                for item in result.get("data", []):
                    if item.get("b64_json"):
                        images.append(base64.b64decode(item["b64_json"]))
                    elif item.get("url"):
                        async with aiohttp.ClientSession() as session:
                            async with session.get(item["url"]) as img_response:
                                images.append(await img_response.read())

                if not images:
                    raise Exception("No images returned from Seedream API")

                response_obj = SeedreamResponse(
                    images=images,
                    model=config.model,
                    generation_time=generation_time,
                    prompt=prompt,
                    seed=result.get("seed"),
                    safety_check_passed=None
                )

                logger.info(f"Successfully generated image with Seedream in {generation_time:.2f}s")
                return response_obj

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed for Seedream: {str(e)}")

                # API 키 오류 시 로깅만 수행
                if "quota" in str(e).lower() or "rate" in str(e).lower() or "unauthorized" in str(e).lower():
                    logger.warning(f"API quota/rate limit/unauthorized error: {str(e)}")

                # 재시도 전 대기
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # 모든 재시도 실패
        logger.error(f"All {max_retries} attempts failed for Seedream: {last_error}")
        raise last_error if last_error else Exception("All image generation attempts failed")

    async def _encode_image(self, image: Union[str, bytes]) -> str:
        """이미지를 base64로 인코딩"""
        if isinstance(image, str):
            with open(image, "rb") as f:
                image_data = f.read()
        else:
            image_data = image
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                output = io.BytesIO()
                img.save(output, format="PNG")
                image_data = output.getvalue()
        except Exception:
            pass
        return base64.b64encode(image_data).decode('utf-8')

    async def generate_fashion_collection(
        self,
        theme: str,
        garments: List[str],
        style: str = "modern",
        color_palette: Optional[List[str]] = None,
        mood_board: Optional[Union[str, bytes]] = None
    ) -> List[SeedreamResponse]:
        """
        패션 컬렉션 생성

        Args:
            theme: 컬렉션 테마
            garments: 의류 목록
            style: 스타일
            color_palette: 색상 팔레트
            mood_board: 무드 보드

        Returns:
            생성된 컬렉션 이미지 목록
        """
        responses = []

        # 공통 프롬프트 구성
        color_prompt = ""
        if color_palette:
            color_prompt = f"Color palette: {', '.join(color_palette)}"

        for garment in garments:
            prompt_parts = [
                f"High-end fashion {garment}",
                f"Collection theme: {theme}",
                f"Style: {style}",
                "Luxury fashion photography",
                "Fashion magazine quality",
                "Professional studio lighting",
                "Detailed fabric texture",
                "Clean presentation"
            ]

            if color_prompt:
                prompt_parts.append(color_prompt)

            prompt = ", ".join(prompt_parts)

            # 생성 설정
            config = SeedreamGenerationConfig(
                width=1024,
                height=1024,
                steps=40,
                guidance_scale=8.0,
                negative_prompt="ugly, blurry, low quality, distorted"
            )

            response = await self.generate_image(
                prompt=prompt,
                config=config,
                reference_image=mood_board,
                ip_adapter_image=mood_board if mood_board else None
            )

            responses.append(response)

        logger.info(f"Generated fashion collection with {len(responses)} garments")
        return responses

    async def generate_pattern_design(
        self,
        pattern_type: str,
        motifs: List[str],
        scale: str = "medium",
        repeat_type: str = "seamless",
        color_scheme: Optional[str] = None
    ) -> SeedreamResponse:
        """
        패턴 디자인 생성

        Args:
            pattern_type: 패턴 타입 (floral, geometric, abstract, etc.)
            motifs: 모티프 목록
            scale: 스케일 (small, medium, large)
            repeat_type: 반복 타입 (seamless, half-drop, brick)
            color_scheme: 색상 구성

        Returns:
            생성된 패턴 디자인
        """
        # 패턴 디자인 프롬프트
        prompt_parts = [
            f"Seamless {pattern_type} pattern design",
            f"Motifs: {', '.join(motifs)}",
            f"Scale: {scale}",
            f"Repeat: {repeat_type}",
            "Professional textile pattern",
            "High resolution",
            "Clean design",
            "Fashion industry standard"
        ]

        if color_scheme:
            prompt_parts.append(f"Color scheme: {color_scheme}")

        prompt = ", ".join(prompt_parts)

        # 생성 설정 - 정사각형을 위한 1024x1024
        config = SeedreamGenerationConfig(
            width=1024,
            height=1024,
            steps=35,
            guidance_scale=7.5,
            negative_prompt="blurry, low quality, non-seamless"
        )

        response = await self.generate_image(prompt=prompt, config=config)
        logger.info(f"Generated {pattern_type} pattern design")
        return response

    async def generate_texture_map(
        self,
        fabric_type: str,
        texture_detail: str = "high",
        color: Optional[str] = None,
        sample_size: int = 512
    ) -> SeedreamResponse:
        """
        패브릭 텍스처 맵 생성

        Args:
            fabric_type: 패브릭 타입 (denim, silk, cotton, wool, etc.)
            texture_detail: 텍스처 디테일 수준
            color: 색상
            sample_size: 샘플 크기

        Returns:
            생성된 텍스처 맵
        """
        # 텍스처 맵 프롬프트
        prompt_parts = [
            f"Photorealistic {fabric_type} fabric texture",
            f"{texture_detail} detail",
            "Seamless tileable texture",
            "Macro photography",
            "Professional textile sample",
            "Studio lighting"
        ]

        if color:
            prompt_parts.append(f"Color: {color}")

        prompt = ", ".join(prompt_parts)

        # 생성 설정
        config = SeedreamGenerationConfig(
            width=sample_size,
            height=sample_size,
            steps=30,
            guidance_scale=7.0,
            negative_prompt="blurry, low resolution, pattern, design"
        )

        response = await self.generate_image(prompt=prompt, config=config)
        logger.info(f"Generated {fabric_type} texture map")
        return response

    async def remove_background(
        self,
        image: Union[str, bytes],
        edge_refinement: bool = True
    ) -> bytes:
        """
        이미지 배경 제거

        Args:
            image: 원본 이미지
            edge_refinement: 에지 정밀화

        Returns:
            배경이 제거된 이미지
        """
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                api_key = settings.seedream_api_key
                if not api_key:
                    raise ValueError("No Seedream API key configured")

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                # 이미지를 base64로 변환
                image_base64 = await self._encode_image(image)

                data = {
                    "image": image_base64,
                    "edge_refinement": edge_refinement
                }

                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        f"{self.base_url}/remove-background",
                        headers=headers,
                        json=data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                        else:
                            error_text = await response.text()
                            raise Exception(f"API returned {response.status}: {error_text}")

                # 결과 이미지 반환
                bg_removed_image = base64.b64decode(result["image"])
                logger.info("Successfully removed background")
                return bg_removed_image

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed for background removal: {str(e)}")

                # API 키 오류 시 로깅만 수행
                if "quota" in str(e).lower() or "rate" in str(e).lower() or "unauthorized" in str(e).lower():
                    logger.warning(f"API quota/rate limit/unauthorized error: {str(e)}")

                # 재시도 전 대기
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # 모든 재시도 실패
        logger.error(f"All {max_retries} attempts failed for background removal: {last_error}")
        raise last_error if last_error else Exception("All background removal attempts failed")

    async def get_model_list(self) -> List[Dict[str, Any]]:
        """
        사용 가능한 모델 목록 조회

        Returns:
            모델 목록
        """
        try:
            api_key = settings.seedream_api_key
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
                    f"{self.base_url}/models",
                    headers=headers
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False

    async def cleanup(self):
        """리소스 정리"""
        logger.info("Seedream client cleaned up")


# 전역 클라이언트 인스턴스
_seedream_client = None


def get_seedream_client() -> SeedreamClient:
    """Seedream 클라이언트 인스턴스 가져오기"""
    global _seedream_client
    if _seedream_client is None:
        _seedream_client = SeedreamClient()
    return _seedream_client


# FastAPI 의존성 주입용
async def get_seedream_client_dep():
    """FastAPI 의존성 주입용 Seedream 클라이언트"""
    client = get_seedream_client()
    try:
        yield client
    finally:
        await client.cleanup()
