"""
Nano Banana API key manager
"""

import aiohttp
from typing import List, Dict, Any
import json

from .base_key_manager import BaseKeyManager
from app.core.logging import get_logger

logger = get_logger(__name__)


class NanoBananaKeyManager(BaseKeyManager):
    """Nano Banana API 키 관리자"""

    def __init__(
        self,
        api_keys: List[str],
        base_url: str = "https://api.nano-banana.com",
        model: str = "nano-banana-v1",
        **kwargs
    ):
        """
        초기화

        Args:
            api_keys: Nano Banana API 키 목록
            base_url: API 기본 URL
            model: 사용할 모델
            **kwargs: BaseKeyManager 인자
        """
        super().__init__(api_keys, **kwargs)
        self.base_url = base_url
        self.model = model

    async def test_key(self, api_key: str) -> bool:
        """
        Nano Banana API 키 유효성 테스트

        Args:
            api_key: 테스트할 API 키

        Returns:
            유효성 여부
        """
        url = f"{self.base_url}/v1/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "data" in data and isinstance(data["data"], list):
                            logger.info("Nano Banana API key validation successful")
                            return True
                        else:
                            logger.error(f"Nano Banana API returned unexpected response: {data}")
                            return False
                    elif response.status == 401:
                        # 인증 실패
                        error_data = await response.json() if response.content_type == "application/json" else {}
                        logger.error(f"Nano Banana API authentication failed: {error_data}")
                        return False
                    elif response.status == 403:
                        # 권한 없음
                        error_data = await response.json() if response.content_type == "application/json" else {}
                        logger.error(f"Nano Banana API access forbidden: {error_data}")
                        return False
                    elif response.status == 429:
                        # Rate limit
                        logger.warning("Nano Banana API rate limited during validation")
                        return True  # Rate limit은 키가 유효하다는 의미
                    else:
                        logger.error(f"Nano Banana API returned status {response.status}")
                        return False

        except aiohttp.ClientError as e:
            logger.error(f"Nano Banana API test failed with network error: {e}")
            return False
        except Exception as e:
            logger.error(f"Nano Banana API test failed: {e}")
            return False

    async def get_models(self, api_key: str) -> List[str]:
        """
        사용 가능한 모델 목록 조회

        Args:
            api_key: API 키

        Returns:
            모델 목록
        """
        url = f"{self.base_url}/v1/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [
                            model.get("id", "")
                            for model in data.get("data", [])
                            if model.get("object") == "model"
                        ]
                        return [m for m in models if m]  # 빈 문자열 제거
                    else:
                        logger.error(f"Failed to get models: status {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []

    async def get_quota_info(self, api_key: str) -> Dict[str, Any]:
        """
        할당량 정보 조회

        Args:
            api_key: API 키

        Returns:
            할당량 정보
        """
        url = f"{self.base_url}/v1/usage"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "current_usage": data.get("current_usage", 0),
                            "limit": data.get("limit", 0),
                            "reset_time": data.get("reset_time"),
                            "remaining": data.get("remaining", 0)
                        }
                    else:
                        logger.error(f"Failed to get quota info: status {response.status}")
                        return {}

        except Exception as e:
            logger.error(f"Failed to get quota info: {e}")
            return {}

    def get_default_headers(self, api_key: str) -> Dict[str, str]:
        """기본 요청 헤더 반환"""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Fashion-AI-Generator/1.0"
        }

    async def create_session(self, api_key: str) -> aiohttp.ClientSession:
        """API 세션 생성"""
        timeout = aiohttp.ClientTimeout(total=120)  # 이미지 생성은 더 긴 타임아웃
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
        return aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self.get_default_headers(api_key)
        )

    def build_generation_url(self) -> str:
        """생성 API URL构建"""
        return f"{self.base_url}/v1/images/generations"

    def build_edit_url(self) -> str:
        """이미지 편집 API URL构建"""
        return f"{self.base_url}/v1/images/edits"

    def build_variation_url(self) -> str:
        """이미지 변형 API URL构建"""
        return f"{self.base_url}/v1/images/variations"

    def parse_error_response(self, status_code: int, error_data: Dict) -> str:
        """
        에러 응답 파싱

        Args:
            status_code: HTTP 상태 코드
            error_data: 에러 데이터

        Returns:
            에러 타입
        """
        error = error_data.get("error", {})
        error_type = error.get("type", "")
        error_code = error.get("code", "")

        if status_code == 400:
            return "invalid_request"
        elif status_code == 401:
            return "authentication_failed"
        elif status_code == 403:
            if error_code == "insufficient_quota":
                return "quota_exceeded"
            else:
                return "permission_denied"
        elif status_code == 429:
            return "rate_limit"
        elif status_code == 500:
            return "server_error"
        elif status_code == 503:
            return "service_unavailable"
        else:
            return "unknown_error"

    def build_generation_payload(
        self,
        prompt: str,
        model: str = None,
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg_scale: float = 7.5,
        seed: int = None,
        negative_prompt: str = None
    ) -> Dict[str, Any]:
        """
        이미지 생성 요청 페이로드 빌드

        Args:
            prompt: 생성 프롬프트
            model: 모델 이름
            width: 이미지 너비
            height: 이미지 높이
            steps: 생성 단계 수
            cfg_scale: CFG 스케일
            seed: 시드 값
            negative_prompt: 네거티브 프롬프트

        Returns:
            요청 페이로드
        """
        payload = {
            "model": model or self.model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "response_format": "url"
        }

        if seed is not None:
            payload["seed"] = seed

        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        return payload