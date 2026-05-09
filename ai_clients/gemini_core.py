"""
Gemini core client implementation
"""

import asyncio
from typing import Dict, List, Optional, Any

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.settings_storage import get_gemini_model
from ai_clients.gemini_types import GenerationConfig, GenerationResponse

logger = get_logger(__name__)
config = get_settings()
TEXT_TIMEOUT_SECONDS = config.analysis_timeout_seconds
IMAGE_TIMEOUT_SECONDS = config.generation_timeout_seconds


def _get_default_model() -> str:
    return get_gemini_model()


def _safe_safety_ratings(response: Any) -> Optional[List[Dict[str, str]]]:
    try:
        candidate = response.candidates[0] if response.candidates else None
        ratings = candidate.safety_ratings if candidate else None
        if not ratings:
            return None
        return [
            {category.name: rating.name}
            for category, rating in ratings.items()
        ]
    except Exception:
        return None


class GeminiClientCore:
    """Core Gemini client"""
    # @MX:ANCHOR: [AUTO] Core Gemini API client with caching and retry logic. Used by all Gemini image generation endpoints.
    # @MX:REASON: High fan_in (3+ Gemini client variants). Client caching, timeout handling, and safety rating extraction shared across Gemini operations.

    def __init__(self):
        self._client_cache: Dict[str, Any] = {}
        self._last_init_time: Dict[str, float] = {}
        self.cache_ttl = 3600

    async def _get_client(self, model: Optional[str] = None):
        if model is None:
            model = _get_default_model()

        current_time = asyncio.get_event_loop().time()
        if model in self._client_cache:
            cache_time = self._last_init_time.get(model, 0)
            if current_time - cache_time < self.cache_ttl:
                return self._client_cache[model]

        api_key = config.gemini_api_key
        if not api_key:
            raise ValueError("No Gemini API key configured")

        genai.configure(api_key=api_key)
        client = genai.GenerativeModel(
            model_name=model,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 8192,
                "candidate_count": 1,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )

        self._client_cache[model] = client
        self._last_init_time[model] = current_time
        logger.info(f"Created new Gemini client for model: {model}")
        return client

    @staticmethod
    def _apply_generation_config(client: Any, generation_config: Optional[GenerationConfig]) -> None:
        if not generation_config:
            return
        client._generation_config = {
            "temperature": generation_config.temperature,
            "top_p": generation_config.top_p,
            "top_k": generation_config.top_k,
            "max_output_tokens": generation_config.max_output_tokens,
            "candidate_count": generation_config.candidate_count,
        }

    async def generate_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None,
        system_instruction: Optional[str] = None
    ) -> GenerationResponse:
        # @MX:WARN: [AUTO] Retry loop with exponential backoff (2^attempt seconds). Quota/rate limit errors break early without retry.
        # @MX:REASON: Handles transient API failures with 3 retry attempts. Rate limit errors detected via string matching on error messages.
        max_retries = 3
        last_error = None
        for attempt in range(max_retries):
            try:
                client = await self._get_client(model)
                self._apply_generation_config(client, generation_config)
                if system_instruction:
                    if hasattr(client, "set_system_instruction"):
                        client.set_system_instruction(system_instruction)
                    else:
                        prompt = f"{system_instruction}\n\n{prompt}"

                response = await asyncio.wait_for(
                    asyncio.to_thread(client.generate_content, prompt, stream=False),
                    timeout=TEXT_TIMEOUT_SECONDS
                )

                result = GenerationResponse(
                    text=response.text,
                    model=model,
                    usage_metadata=None,
                    finish_reason=response.candidates[0].finish_reason.name if response.candidates else None,
                    safety_ratings=_safe_safety_ratings(response)
                )
                logger.info(f"Successfully generated content with {model}")
                return result
            except Exception as exc:
                last_error = exc
                logger.warning(f"Attempt {attempt + 1} failed for {model}: {exc}")
                if "quota" in str(exc).lower() or "rate" in str(exc).lower():
                    logger.warning(f"API quota/rate limit error: {exc}")
                    break
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        logger.error(f"All {max_retries} attempts failed for {model}: {last_error}")
        raise last_error if last_error else Exception("All generation attempts failed")

    async def generate_with_image(
        self,
        prompt: str,
        image_path: str,
        model: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None
    ) -> GenerationResponse:
        from PIL import Image

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                client = await self._get_client(model)
                image = Image.open(image_path)
                self._apply_generation_config(client, generation_config)
                response = await asyncio.wait_for(
                    asyncio.to_thread(client.generate_content, [prompt, image], stream=False),
                    timeout=IMAGE_TIMEOUT_SECONDS
                )

                result = GenerationResponse(
                    text=response.text,
                    model=model,
                    usage_metadata=None,
                    finish_reason=response.candidates[0].finish_reason.name if response.candidates else None,
                    safety_ratings=_safe_safety_ratings(response)
                )
                logger.info(f"Successfully generated content with image using {model}")
                return result
            except Exception as exc:
                last_error = exc
                logger.warning(f"Attempt {attempt + 1} failed for {model} with image: {exc}")
                if "quota" in str(exc).lower() or "rate" in str(exc).lower():
                    logger.warning(f"API quota/rate limit error: {exc}")
                    break
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        logger.error(f"All {max_retries} attempts failed for {model} with image: {last_error}")
        raise last_error if last_error else Exception("All generation attempts failed with image")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None
    ) -> GenerationResponse:
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                client = await self._get_client(model)
                self._apply_generation_config(client, generation_config)
                chat = client.start_chat(history=[])
                response = None
                for message in messages:
                    role = message.get("role", "user")
                    content = message.get("content", "")
                    if role == "user":
                        response = await asyncio.wait_for(
                            asyncio.to_thread(chat.send_message, content, stream=False),
                            timeout=TEXT_TIMEOUT_SECONDS
                        )
                    else:
                        continue

                if response is None:
                    raise ValueError("No chat response from Gemini")

                result = GenerationResponse(
                    text=response.text,
                    model=model,
                    usage_metadata=None,
                    finish_reason=response.candidates[0].finish_reason.name if response.candidates else None,
                    safety_ratings=_safe_safety_ratings(response)
                )
                logger.info(f"Successfully completed chat with {model}")
                return result
            except Exception as exc:
                last_error = exc
                logger.warning(f"Attempt {attempt + 1} failed for chat completion with {model}: {exc}")
                if "quota" in str(exc).lower() or "rate" in str(exc).lower():
                    logger.warning(f"API quota/rate limit error: {exc}")
                    break
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        logger.error(f"All {max_retries} attempts failed for chat completion with {model}: {last_error}")
        raise last_error if last_error else Exception("All chat completion attempts failed")

    async def cleanup(self):
        self._client_cache.clear()
        self._last_init_time.clear()
        logger.info("Gemini client cleaned up")
