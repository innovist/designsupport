"""
Bytedance (Seedream) API key manager
"""

import aiohttp
from typing import List, Dict, Any
import json
import hashlib
import time

from .base_key_manager import BaseKeyManager
from app.core.logging import get_logger

logger = get_logger(__name__)


class BytedanceKeyManager(BaseKeyManager):
    """Bytedance (Seedream) API 키 관리자"""

    def __init__(
        self,
        api_keys: List[str],
        access_keys: List[str] = None,  # BytePlus에서 필요한 access key
        secret_keys: List[str] = None,  # BytePlus에서 필요한 secret key
        base_url: str = "https://ark.cn-beijing.volces.com",
        model: str = "seedream-4.5",
        region: str = "cn-beijing",
        service: str = "ark",
        **kwargs
    ):
        """
        초기화

        Args:
            api_keys: Seedream API 키 목록
            access_keys: BytePlus Access Key 목록
            secret_keys: BytePlus Secret Key 목록
            base_url: API 기본 URL
            model: 사용할 모델
            region: AWS 리전
            service: AWS 서비스명
            **kwargs: BaseKeyManager 인자
        """
        super().__init__(api_keys, **kwargs)
        self.base_url = base_url
        self.model = model
        self.region = region
        self.service = service

        # Access Key와 Secret Key 쌍 매핑
        self.credentials = []
        if access_keys and secret_keys:
            for access_key, secret_key in zip(access_keys, secret_keys):
                self.credentials.append({
                    "access_key": access_key,
                    "secret_key": secret_key
                })

    async def test_key(self, api_key: str) -> bool:
        """
        Seedream API 키 유효성 테스트

        Args:
            api_key: 테스트할 API 키

        Returns:
            유효성 여부
        """
        url = f"{self.base_url}/api/v3/model/list"
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
                        if "data" in data and "result" in data["data"]:
                            logger.info("Seedream API key validation successful")
                            return True
                        else:
                            logger.error(f"Seedream API returned unexpected response: {data}")
                            return False
                    elif response.status == 401:
                        # 인증 실패
                        error_data = await response.json() if response.content_type == "application/json" else {}
                        logger.error(f"Seedream API authentication failed: {error_data}")
                        return False
                    elif response.status == 403:
                        # 권한 없음
                        error_data = await response.json() if response.content_type == "application/json" else {}
                        logger.error(f"Seedream API access forbidden: {error_data}")
                        return False
                    elif response.status == 429:
                        # Rate limit
                        logger.warning("Seedream API rate limited during validation")
                        return True  # Rate limit은 키가 유효하다는 의미
                    else:
                        logger.error(f"Seedream API returned status {response.status}")
                        return False

        except aiohttp.ClientError as e:
            logger.error(f"Seedream API test failed with network error: {e}")
            return False
        except Exception as e:
            logger.error(f"Seedream API test failed: {e}")
            return False

    def _generate_signature(
        self,
        method: str,
        uri: str,
        query_params: Dict[str, str],
        headers: Dict[str, str],
        payload: str,
        access_key: str,
        secret_key: str
    ) -> str:
        """
        AWS Signature V4 생성

        Args:
            method: HTTP 메서드
            uri: 요청 URI
            query_params: 쿼리 파라미터
            headers: 요청 헤더
            payload: 요청 본문
            access_key: Access Key
            secret_key: Secret Key

        Returns:
            서명
        """
        # 날짜 및 타임스탬프
        now = time.gmtime()
        amz_date = time.strftime("%Y%m%dT%H%M%SZ", now)
        date_stamp = time.strftime("%Y%m%d", now)

        # 캐노니컬 요청 생성
        canonical_uri = uri
        canonical_querystring = "&".join(
            f"{k}={v}" for k, v in sorted(query_params.items())
        )
        canonical_headers = "\n".join(
            f"{k.lower()}:{v}" for k, v in sorted(headers.items())
        )
        signed_headers = ";".join(sorted(headers.keys()))

        payload_hash = hashlib.sha256(payload.encode()).hexdigest()

        canonical_request = f"{method}\n{canonical_uri}\n{canonical_querystring}\n"
        canonical_request += f"{canonical_headers}\n\n{signed_headers}\n{payload_hash}"

        # 서명 문자열 생성
        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self.region}/{self.service}/aws4_request"
        string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n"
        string_to_sign += hashlib.sha256(canonical_request.encode()).hexdigest()

        # 서명 계산
        def sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode(), hashlib.sha256).digest()

        import hmac
        k_date = sign(f"AWS4{secret_key}".encode(), date_stamp)
        k_region = sign(k_date, self.region)
        k_service = sign(k_region, self.service)
        k_signing = sign(k_service, "aws4_request")

        signature = hmac.new(
            k_signing,
            string_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()

        # 인증 헤더 생성
        authorization_header = (
            f"{algorithm} Credential={access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        return authorization_header, amz_date

    async def get_models(self, api_key: str) -> List[str]:
        """
        사용 가능한 모델 목록 조회

        Args:
            api_key: API 키

        Returns:
            모델 목록
        """
        url = f"{self.base_url}/api/v3/model/list"
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
                        models = []
                        for model_info in data.get("data", {}).get("result", []):
                            model_name = model_info.get("model_name", "")
                            if model_name:
                                models.append(model_name)
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
        url = f"{self.base_url}/api/v3/quota/info"
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
                        quota_info = data.get("data", {})
                        return {
                            "current_usage": quota_info.get("used", 0),
                            "limit": quota_info.get("total", 0),
                            "remaining": quota_info.get("remaining", 0)
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

    def build_generation_url(self, model_id: str) -> str:
        """생성 API URL构建"""
        return f"{self.base_url}/api/v3/inference/text2image"

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
        error_code = error.get("code", "")
        error_message = error.get("message", "")

        if status_code == 400:
            return "invalid_request"
        elif status_code == 401:
            return "authentication_failed"
        elif status_code == 403:
            if "quota" in error_message.lower():
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
        model_id: str,
        width: int = 1024,
        height: int = 1024,
        steps: int = 50,
        seed: int = None,
        negative_prompt: str = None
    ) -> Dict[str, Any]:
        """
        이미지 생성 요청 페이로드 빌드

        Args:
            prompt: 생성 프롬프트
            model_id: 모델 ID
            width: 이미지 너비
            height: 이미지 높이
            steps: 생성 단계 수
            seed: 시드 값
            negative_prompt: 네거티브 프롬프트

        Returns:
            요청 페이로드
        """
        payload = {
            "model_id": model_id,
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "return_url": True
        }

        if seed is not None:
            payload["seed"] = seed

        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        return payload