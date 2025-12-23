"""
GLM (Z.AI) client implementation - OpenAI compatible
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from openai import OpenAI

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.settings_storage import get_glm_model, AVAILABLE_MODELS

logger = get_logger(__name__)
config = get_settings()
THINKING_DISABLED = {"thinking": {"type": "disabled"}}
JSON_MARKERS = ("json", "JSON")
TEXT_TIMEOUT_SECONDS = config.analysis_timeout_seconds


def _expects_json(messages: List[Dict[str, str]]) -> bool:
    combined = " ".join(message.get("content", "") for message in messages)
    return any(marker in combined for marker in JSON_MARKERS)


def _extract_json_text(text: str) -> str:
    if not text:
        return text
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return text
    return text[start:end + 1]


@dataclass
class GLMGenerationConfig:
    """GLM generation settings"""
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 8192
    stream: bool = False
    model: str = field(default_factory=get_glm_model)


@dataclass
class GLMResponse:
    """GLM response"""
    text: str
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    created: Optional[int] = None
    id: Optional[str] = None


class ZAIProvider:
    """Z.AI OpenAI-compatible provider"""
    BASE_URL = "https://api.z.ai/api/coding/paas/v4"

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)


class GLMClient:
    """GLM client"""

    def __init__(self):
        self._client_cache: Dict[str, ZAIProvider] = {}
        self._last_init_time: Dict[str, float] = {}
        self.cache_ttl = 3600

    async def _get_client(self) -> ZAIProvider:
        current_time = asyncio.get_event_loop().time()
        if "glm_client" in self._client_cache:
            cache_time = self._last_init_time.get("glm_client", 0)
            if current_time - cache_time < self.cache_ttl:
                return self._client_cache["glm_client"]

        api_key = config.glm_api_key
        if not api_key:
            raise ValueError("No GLM API key configured")

        client = ZAIProvider(api_key=api_key)
        self._client_cache["glm_client"] = client
        self._last_init_time["glm_client"] = current_time
        logger.info("Created new GLM client")
        return client

    @staticmethod
    def _build_messages(prompt: str, system_prompt: Optional[str]) -> List[Dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    @staticmethod
    def _parse_usage(response: Any) -> Optional[Dict[str, int]]:
        usage = getattr(response, "usage", None)
        if not usage:
            return None
        return {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0),
            "completion_tokens": getattr(usage, "completion_tokens", 0),
            "total_tokens": getattr(usage, "total_tokens", 0)
        }

    def _sync_chat_completion(
        self,
        provider: ZAIProvider,
        model: str,
        messages: List[Dict[str, str]],
        config: GLMGenerationConfig
    ) -> GLMResponse:
        response = provider.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=config.temperature,
            top_p=config.top_p,
            max_tokens=config.max_tokens,
            stream=config.stream,
            extra_body=THINKING_DISABLED
        )

        if config.stream:
            content = ""
            for chunk in response:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    content += delta
            return GLMResponse(text=content, model=model)

        content = response.choices[0].message.content if response.choices else ""
        if _expects_json(messages):
            content = _extract_json_text(content)
        return GLMResponse(
            text=content,
            model=model,
            usage=self._parse_usage(response),
            finish_reason=response.choices[0].finish_reason if response.choices else None,
            created=getattr(response, "created", None),
            id=getattr(response, "id", None)
        )

    async def generate_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        generation_config: Optional[GLMGenerationConfig] = None,
        system_prompt: Optional[str] = None
    ) -> GLMResponse:
        max_retries = 3
        last_error = None

        model = model or get_glm_model()
        generation_config = generation_config or GLMGenerationConfig(model=model)
        messages = self._build_messages(prompt, system_prompt)

        for attempt in range(max_retries):
            try:
                provider = await self._get_client()
                return await asyncio.wait_for(
                    asyncio.to_thread(
                        self._sync_chat_completion,
                        provider,
                        model,
                        messages,
                        generation_config
                    ),
                    timeout=TEXT_TIMEOUT_SECONDS
                )
            except Exception as exc:
                last_error = exc
                logger.warning(f"Attempt {attempt + 1} failed for GLM {model}: {exc}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        logger.error(f"All {max_retries} attempts failed for GLM {model}: {last_error}")
        raise last_error if last_error else Exception("All generation attempts failed")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        generation_config: Optional[GLMGenerationConfig] = None
    ) -> GLMResponse:
        max_retries = 3
        last_error = None

        model = model or get_glm_model()
        generation_config = generation_config or GLMGenerationConfig(model=model)

        for attempt in range(max_retries):
            try:
                provider = await self._get_client()
                return await asyncio.wait_for(
                    asyncio.to_thread(
                        self._sync_chat_completion,
                        provider,
                        model,
                        messages,
                        generation_config
                    ),
                    timeout=TEXT_TIMEOUT_SECONDS
                )
            except Exception as exc:
                last_error = exc
                logger.warning(f"Attempt {attempt + 1} failed for chat completion with GLM {model}: {exc}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        logger.error(f"All {max_retries} attempts failed for chat completion with GLM {model}: {last_error}")
        raise last_error if last_error else Exception("All chat completion attempts failed")

    async def embed_text(self, text: str, model: Optional[str] = None) -> List[float]:
        if not model:
            raise ValueError("Embedding model is not configured")
        provider = await self._get_client()
        response = await asyncio.to_thread(
            provider.client.embeddings.create,
            model=model,
            input=text
        )
        return response.data[0].embedding

    async def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        provider = await self._get_client()
        response = await asyncio.to_thread(
            provider.client.chat.completions.create,
            model=model or get_glm_model(),
            messages=[{"role": "user", "content": text}],
            max_tokens=1,
            extra_body=THINKING_DISABLED
        )
        usage = self._parse_usage(response)
        if not usage:
            raise ValueError("Token usage not available in GLM response")
        return usage["prompt_tokens"]

    async def get_model_list(self) -> List[str]:
        return AVAILABLE_MODELS.get("glm", {}).get("text", [])

    async def validate_key(self, api_key: str) -> bool:
        try:
            provider = ZAIProvider(api_key=api_key)
            response = await asyncio.to_thread(
                provider.client.chat.completions.create,
                model=get_glm_model(),
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10,
                extra_body=THINKING_DISABLED
            )
            return bool(response.choices)
        except Exception as exc:
            logger.error(f"API key validation failed: {exc}")
            return False

    async def cleanup(self):
        self._client_cache.clear()
        self._last_init_time.clear()
        logger.info("GLM client cleaned up")


_glm_client: Optional[GLMClient] = None


def get_glm_client() -> GLMClient:
    global _glm_client
    if _glm_client is None:
        _glm_client = GLMClient()
    return _glm_client


async def get_glm_client_dep():
    client = get_glm_client()
    try:
        yield client
    finally:
        await client.cleanup()
