"""
Z-Image AI client implementation for fashion image generation
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import base64
import io

import aiohttp
from PIL import Image

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
config = get_settings()


@dataclass
class ImageGenerationConfig:
    """이미지 생성 설정"""
    width: int = 1024
    height: int = 1024
    steps: int = 30
    guidance_scale: float = 7.5
    seed: Optional[int] = None
    negative_prompt: Optional[str] = None
    num_images: int = 1
    model: str = "stable-diffusion-xl"
    scheduler: str = "DPM++ 2M Karras"
    controlnet_strength: float = 1.0


@dataclass
class ImageResponse:
    """이미지 생성 응답"""
    images: List[bytes]  # Base64 encoded images
    model: str
    generation_time: float
    prompt: str
    seed: Optional[int] = None
    nsfw_detected: Optional[bool] = None


class ZImageClient:
    """Z-Image AI 클라이언트"""

    def __init__(self):
        """초기화"""
        self.api_key = config.z_image_api_key
        self.base_url = config.comfyui_api_url if config.comfyui_api_url else "http://localhost:8188"
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5분 타임아웃

    async def generate_image(
        self,
        prompt: str,
        config: Optional[ImageGenerationConfig] = None,
        reference_image: Optional[Union[str, bytes]] = None,
        controlnet_type: Optional[str] = None
    ) -> ImageResponse:
        """
        패션 이미지 생성

        Args:
            prompt: 생성 프롬프트
            config: 생성 설정
            reference_image: 참조 이미지 (파일 경로 또는 바이츠)
            controlnet_type: ControlNet 타입 (canny, depth, pose, etc.)

        Returns:
            생성된 이미지 응답
        """
        if config is None:
            config = ImageGenerationConfig()

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                api_key = self.api_key
                if not api_key:
                    raise ValueError("No Z-Image API key configured")

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                # 요청 데이터 구성
                data = {
                    "prompt": prompt,
                    "model": config.model,
                    "width": config.width,
                    "height": config.height,
                    "steps": config.steps,
                    "guidance_scale": config.guidance_scale,
                    "num_images": config.num_images,
                    "scheduler": config.scheduler
                }

                if config.negative_prompt:
                    data["negative_prompt"] = config.negative_prompt

                if config.seed:
                    data["seed"] = config.seed

                # 참조 이미지가 있는 경우
                if reference_image:
                    # 이미지를 base64로 변환
                    if isinstance(reference_image, str):
                        # 파일 경로인 경우
                        with open(reference_image, "rb") as f:
                            image_data = f.read()
                    else:
                        # 바이츠인 경우
                        image_data = reference_image

                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                    data["reference_image"] = image_base64

                    if controlnet_type:
                        data["controlnet"] = {
                            "type": controlnet_type,
                            "strength": config.controlnet_strength
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

                response_obj = ImageResponse(
                    images=images,
                    model=config.model,
                    generation_time=generation_time,
                    prompt=prompt,
                    seed=result.get("seed"),
                    nsfw_detected=result.get("nsfw_detected")
                )

                logger.info(f"Successfully generated image with Z-Image in {generation_time:.2f}s")
                return response_obj

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed for Z-Image: {str(e)}")

                # API 키 오류 시 로깅만 수행
                if "quota" in str(e).lower() or "rate" in str(e).lower() or "unauthorized" in str(e).lower():
                    logger.warning(f"API quota/rate limit/unauthorized error: {str(e)}")

                # 재시도 전 대기
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # 모든 재시도 실패
        logger.error(f"All {max_retries} attempts failed for Z-Image: {last_error}")
        raise last_error if last_error else Exception("All image generation attempts failed")

    async def generate_fashion_design(
        self,
        design_description: str,
        style: str = "modern",
        garment_type: str = "dress",
        color_scheme: Optional[str] = None,
        fabric_type: Optional[str] = None,
        reference_sketch: Optional[Union[str, bytes]] = None
    ) -> ImageResponse:
        """
        패션 디자인 이미지 생성 (특화된 프롬프트)

        Args:
            design_description: 디자인 설명
            style: 스타일 (modern, vintage, minimalist, etc.)
            garment_type: 의류 타입 (dress, shirt, pants, etc.)
            color_scheme: 색상 구성
            fabric_type: 패브릭 타입
            reference_sketch: 참조 스케치

        Returns:
            생성된 패션 디자인 이미지
        """
        # 패션 디자인 특화 프롬프트 구성
        prompt_parts = [
            f"Professional fashion design of a {garment_type}",
            f"Style: {style}",
            f"Description: {design_description}",
            "High quality fashion illustration",
            "Clean white background",
            "Professional fashion photography style",
            "Detailed fabric texture",
            "Perfect lighting"
        ]

        if color_scheme:
            prompt_parts.append(f"Color scheme: {color_scheme}")

        if fabric_type:
            prompt_parts.append(f"Fabric: {fabric_type}")

        prompt = ", ".join(prompt_parts)

        # 네거티브 프롬프트
        negative_prompt = (
            "person, human, model, mannequin, ugly, blurry, "
            "low quality, distorted, bad anatomy, extra limbs"
        )

        # 생성 설정
        config = ImageGenerationConfig(
            width=1024,
            height=1024,
            steps=40,
            guidance_scale=8.0,
            negative_prompt=negative_prompt,
            model="stable-diffusion-xl-fashion"  # 전문 패션 모델
        )

        return await self.generate_image(
            prompt=prompt,
            config=config,
            reference_image=reference_sketch,
            controlnet_type="scribble" if reference_sketch else None
        )

    async def generate_model_fitting(
        self,
        design_image: Union[str, bytes],
        model_type: str = "female",
        pose: str = "standing",
        background: str = "studio"
    ) -> ImageResponse:
        """
        의류 모델 피팅 이미지 생성

        Args:
            design_image: 디자인 이미지
            model_type: 모델 타입 (female, male, diverse)
            pose: 포즈 (standing, sitting, walking)
            background: 배경 (studio, street, runway)

        Returns:
            모델 피팅 이미지
        """
        # 모델 피팅 프롬프트
        prompt_parts = [
            f"Professional fashion model ({model_type})",
            f"Wearing the provided garment design",
            f"Pose: {pose}",
            f"Background: {background}",
            "High fashion photography",
            "Professional lighting",
            "Detailed garment fit",
            "Fashion magazine quality"
        ]

        prompt = ", ".join(prompt_parts)

        # 생성 설정
        config = ImageGenerationConfig(
            width=1024,
            height=1536,  # 2:3 ratio for fashion
            steps=40,
            guidance_scale=8.0,
            negative_prompt="ugly, blurry, bad lighting, distorted",
            model="stable-diffusion-xl-fashion"
        )

        return await self.generate_image(
            prompt=prompt,
            config=config,
            reference_image=design_image,
            controlnet_type="openpose"
        )

    async def upscale_image(
        self,
        image: Union[str, bytes],
        scale_factor: int = 2,
        enhance_fabric_texture: bool = True
    ) -> bytes:
        """
        이미지 고화질화

        Args:
            image: 원본 이미지
            scale_factor: 확대 비율
            enhance_fabric_texture: 패브릭 질감 향상 여부

        Returns:
            고화질화된 이미지
        """
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                api_key = self.api_key
                if not api_key:
                    raise ValueError("No Z-Image API key configured")

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                # 이미지를 base64로 변환
                if isinstance(image, str):
                    with open(image, "rb") as f:
                        image_data = f.read()
                else:
                    image_data = image

                image_base64 = base64.b64encode(image_data).decode('utf-8')

                data = {
                    "image": image_base64,
                    "scale_factor": scale_factor,
                    "model": "esrgan-x4",
                    "enhance_details": enhance_fabric_texture
                }

                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        f"{self.base_url}/upscale",
                        headers=headers,
                        json=data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                        else:
                            error_text = await response.text()
                            raise Exception(f"API returned {response.status}: {error_text}")

                # 결과 이미지 반환
                upscaled_image = base64.b64decode(result["image"])
                logger.info(f"Successfully upscaled image by factor {scale_factor}")
                return upscaled_image

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed for upscaling: {str(e)}")

                # API 키 오류 시 로깅만 수행
                if "quota" in str(e).lower() or "rate" in str(e).lower() or "unauthorized" in str(e).lower():
                    logger.warning(f"API quota/rate limit/unauthorized error: {str(e)}")

                # 재시도 전 대기
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # 모든 재시도 실패
        logger.error(f"All {max_retries} attempts failed for upscaling: {last_error}")
        raise last_error if last_error else Exception("All upscaling attempts failed")

    async def get_model_list(self) -> List[Dict[str, Any]]:
        """
        사용 가능한 모델 목록 조회

        Returns:
            모델 목록
        """
        try:
            api_key = self.api_key
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
        logger.info("Z-Image client cleaned up")


# 전역 클라이언트 인스턴스
_zimage_client = None


def get_zimage_client() -> ZImageClient:
    """Z-Image 클라이언트 인스턴스 가져오기"""
    global _zimage_client
    if _zimage_client is None:
        _zimage_client = ZImageClient()
    return _zimage_client


# FastAPI 의존성 주입용
async def get_zimage_client_dep():
    """FastAPI 의존성 주입용 Z-Image 클라이언트"""
    client = get_zimage_client()
    try:
        yield client
    finally:
        await client.cleanup()