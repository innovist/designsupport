"""
Gemini API key manager
"""

import aiohttp
from typing import List, Dict, Any

from .base_key_manager import BaseKeyManager
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiKeyManager(BaseKeyManager):
    """Gemini API 키 관리자"""

    def __init__(
        self,
        api_keys: List[str],
        base_url: str = "https://generativelanguage.googleapis.com",
        model: str = "gemini-1.5-pro",
        **kwargs
    ):
        """
        초기화

        Args:
            api_keys: Gemini API 키 목록
            base_url: API 기본 URL
            model: 사용할 모델
            **kwargs: BaseKeyManager 인자
        """
        super().__init__(api_keys, **kwargs)
        self.base_url = base_url
        self.model = model

    async def test_key(self, api_key: str) -> bool:
        """
        Gemini API 키 유효성 테스트

        Args:
            api_key: 테스트할 API 키

        Returns:
            유효성 여부
        """
        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent"
        headers = {"Content-Type": "application/json"}
        params = {"key": api_key}

        test_payload = {
            "contents": [
                {
                    "parts": [
                        {"text": "Hello, this is a test."}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 10,
                "temperature": 0.1
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    params=params,
                    json=test_payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "candidates" in data:
                            logger.info("Gemini API key validation successful")
                            return True
                        else:
                            logger.error(f"Gemini API returned unexpected response: {data}")
                            return False
                    elif response.status == 400:
                        # API 키 형식 오류
                        error_data = await response.json()
                        logger.error(f"Gemini API key format error: {error_data}")
                        return False
                    elif response.status == 401:
                        # 인증 실패
                        logger.error("Gemini API key authentication failed")
                        return False
                    elif response.status == 403:
                        # 권한 없음 또는 할당량 초과
                        error_data = await response.json()
                        logger.error(f"Gemini API access forbidden: {error_data}")
                        return False
                    elif response.status == 429:
                        # Rate limit
                        logger.warning("Gemini API rate limited during validation")
                        return True  # Rate limit은 키가 유효하다는 의미
                    else:
                        logger.error(f"Gemini API returned status {response.status}")
                        return False

        except aiohttp.ClientError as e:
            logger.error(f"Gemini API test failed with network error: {e}")
            return False
        except Exception as e:
            logger.error(f"Gemini API test failed: {e}")
            return False

    async def get_models(self, api_key: str) -> List[str]:
        """
        사용 가능한 모델 목록 조회

        Args:
            api_key: API 키

        Returns:
            모델 목록
        """
        url = f"{self.base_url}/v1beta/models"
        params = {"key": api_key}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [
                            model["name"].split("/")[-1]
                            for model in data.get("models", [])
                            if "generateContent" in model.get("supportedGenerationMethods", [])
                        ]
                        return models
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
        # Gemini API는 직접적인 할당량 조회 엔드포인트가 없음
        # 실제 사용량은 Google Cloud Console을 통해 확인 필요
        return {
            "message": "Quota information available through Google Cloud Console",
            "url": "https://console.cloud.google.com/iam-admin/quotas"
        }

    def get_default_headers(self) -> Dict[str, str]:
        """기본 요청 헤더 반환"""
        return {
            "Content-Type": "application/json",
            "User-Agent": "Fashion-AI-Generator/1.0"
        }

    async def create_session(self) -> aiohttp.ClientSession:
        """API 세션 생성"""
        timeout = aiohttp.ClientTimeout(total=60)
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        return aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self.get_default_headers()
        )

    def build_generation_url(self, api_key: str) -> str:
        """생성 API URL构建"""
        return f"{self.base_url}/v1beta/models/{self.model}:generateContent?key={api_key}"

    def build_streaming_url(self, api_key: str) -> str:
        """스트리밍 API URL构建"""
        return f"{self.base_url}/v1beta/models/{self.model}:streamGenerateContent?key={api_key}"

    def parse_error_response(self, status_code: int, error_data: Dict) -> str:
        """
        에러 응답 파싱

        Args:
            status_code: HTTP 상태 코드
            error_data: 에러 데이터

        Returns:
            에러 타입
        """
        if status_code == 400:
            return "invalid_request"
        elif status_code == 401:
            return "authentication_failed"
        elif status_code == 403:
            error_code = error_data.get("error", {}).get("code", "")
            if error_code == 429:
                return "quota_exceeded"
            else:
                return "permission_denied"
        elif status_code == 429:
            return "rate_limit"
        elif status_code >= 500:
            return "server_error"
        else:
            return "unknown_error"