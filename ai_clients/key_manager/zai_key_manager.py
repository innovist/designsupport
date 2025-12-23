"""
ZAI (Z-Image) API key manager
"""

import aiohttp
from typing import List, Dict, Any
import json
import asyncio

from .base_key_manager import BaseKeyManager
from app.core.logging import get_logger

logger = get_logger(__name__)


class ZaiKeyManager(BaseKeyManager):
    """ZAI (Z-Image) API 키 관리자"""

    def __init__(
        self,
        api_keys: List[str],
        base_url: str = "http://localhost:8188",
        workflow_path: str = "/api/prompt",
        model: str = "Z-Image-turbo",
        **kwargs
    ):
        """
        초기화

        Args:
            api_keys: ZAI API 키 목록
            base_url: ComfyUI API 기본 URL
            workflow_path: 워크플로우 API 경로
            model: 사용할 모델
            **kwargs: BaseKeyManager 인자
        """
        super().__init__(api_keys, **kwargs)
        self.base_url = base_url
        self.workflow_path = workflow_path
        self.model = model
        self.client_id = None  # ComfyUI WebSocket용 클라이언트 ID

    async def test_key(self, api_key: str) -> bool:
        """
        ZAI API 키 유효성 테스트

        Args:
            api_key: 테스트할 API 키

        Returns:
            유효성 여부
        """
        # ComfyUI는 전통적인 API 키 대신 WebSocket 연결을 사용
        # 여기서는 서버 연결성 확인
        url = f"{self.base_url}/system_stats"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "system" in data:
                            logger.info("ZAI server connection successful")
                            return True
                        else:
                            logger.error(f"ZAI server returned unexpected response: {data}")
                            return False
                    else:
                        logger.error(f"ZAI server returned status {response.status}")
                        return False

        except aiohttp.ClientError as e:
            logger.error(f"ZAI server test failed with network error: {e}")
            return False
        except Exception as e:
            logger.error(f"ZAI server test failed: {e}")
            return False

    async def get_models(self, api_key: str) -> List[str]:
        """
        사용 가능한 모델 목록 조회

        Args:
            api_key: API 키

        Returns:
            모델 목록
        """
        url = f"{self.base_url}/object_info"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = []
                        for node_id, node_info in data.items():
                            # KSampler 노드에서 모델 정보 추출
                            if node_info.get("class_type") == "KSampler":
                                model_input = node_info.get("inputs", {}).get("model", [])
                                if model_input and len(model_input) > 0:
                                    models.append(model_input[0])
                        return list(set(models))  # 중복 제거
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
        # ComfyUI는 할당량 개념이 없음 (로컬 실행)
        return {
            "message": "Local ComfyUI instance - no quota limits",
            "gpu_info": await self._get_gpu_info()
        }

    async def _get_gpu_info(self) -> Dict[str, Any]:
        """GPU 정보 조회"""
        url = f"{self.base_url}/system_stats"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("system", {}).get("devices", {})
        except Exception:
            pass

        return {}

    def get_default_headers(self) -> Dict[str, str]:
        """기본 요청 헤더 반환"""
        return {
            "Content-Type": "application/json",
            "User-Agent": "Fashion-AI-Generator/1.0"
        }

    async def create_session(self) -> aiohttp.ClientSession:
        """API 세션 생성"""
        timeout = aiohttp.ClientTimeout(total=300)  # 이미지 생성은 긴 타임아웃
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        return aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self.get_default_headers()
        )

    def build_generation_url(self) -> str:
        """생성 API URL构建"""
        return f"{self.base_url}{self.workflow_path}"

    def build_websocket_url(self) -> str:
        """WebSocket URL构建"""
        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        return f"{ws_url}/ws?clientId={self.client_id}"

    async def generate_client_id(self) -> str:
        """고유 클라이언트 ID 생성"""
        import uuid
        self.client_id = str(uuid.uuid4())
        return self.client_id

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
            return "permission_denied"
        elif status_code == 404:
            return "not_found"
        elif status_code == 429:
            return "rate_limit"
        elif status_code == 500:
            return "server_error"
        elif status_code == 503:
            return "service_unavailable"
        else:
            return "unknown_error"

    def build_workflow_payload(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg_scale: float = 7.5,
        seed: int = None,
        negative_prompt: str = None,
        reference_image: str = None,
        controlnet_type: str = None
    ) -> Dict[str, Any]:
        """
        ComfyUI 워크플로우 페이로드 빌드

        Args:
            prompt: 생성 프롬프트
            width: 이미지 너비
            height: 이미지 높이
            steps: 생성 단계 수
            cfg_scale: CFG 스케일
            seed: 시드 값
            negative_prompt: 네거티브 프롬프트
            reference_image: 참조 이미지
            controlnet_type: ControlNet 타입

        Returns:
            워크플로우 페이로드
        """
        # 기본 노드 ID 생성
        checkpoint_loader_id = "1"
        clip_id = "2"
        clip_text_encode_id = "3"
        clip_text_encode_neg_id = "4"
        empty_latent_id = "5"
        ksampler_id = "6"
        vaedecode_id = "7"
        save_image_id = "8"

        workflow = {
            "1": {
                "inputs": {
                    "ckpt_name": f"{self.model}.safetensors"
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "2": {
                "inputs": {
                    "text": prompt,
                    "clip": [checkpoint_loader_id, 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "5": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "6": {
                "inputs": {
                    "seed": seed or -1,
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "denoise": 1.0,
                    "model": [checkpoint_loader_id, 0],
                    "positive": [clip_text_encode_id, 0],
                    "negative": [clip_text_encode_neg_id, 0] if negative_prompt else [clip_text_encode_id, 0],
                    "latent_image": [empty_latent_id, 0]
                },
                "class_type": "KSampler"
            },
            "7": {
                "inputs": {
                    "samples": [ksampler_id, 0],
                    "vae": [checkpoint_loader_id, 2]
                },
                "class_type": "VAEDecode"
            },
            "8": {
                "inputs": {
                    "filename_prefix": "fashion_ai",
                    "images": [vaedecode_id, 0]
                },
                "class_type": "SaveImage"
            }
        }

        # 네거티브 프롬프트 추가
        if negative_prompt:
            workflow["3"] = workflow.pop("2")
            workflow["4"] = {
                "inputs": {
                    "text": negative_prompt,
                    "clip": [checkpoint_loader_id, 1]
                },
                "class_type": "CLIPTextEncode"
            }

        # 참조 이미지 및 ControlNet 추가
        if reference_image and controlnet_type:
            # ControlNet 적용을 위한 노드 추가
            controlnet_loader_id = "9"
            controlnet_apply_id = "10"
            image_load_id = "11"

            workflow["9"] = {
                "inputs": {
                    "control_net_name": f"control_{controlnet_type}.safetensors"
                },
                "class_type": "ControlNetLoader"
            }

            workflow["10"] = {
                "inputs": {
                    "strength": 0.8,
                    "conditioning": [clip_text_encode_id, 0],
                    "control_net": [controlnet_loader_id, 0],
                    "image": [image_load_id, 0]
                },
                "class_type": "ControlNetApply"
            }

            workflow["11"] = {
                "inputs": {
                    "image": reference_image,
                    "upload": "image"
                },
                "class_type": "LoadImage"
            }

            # KSampler 업데이트
            workflow["6"]["inputs"]["positive"] = [controlnet_apply_id, 0]

        return workflow