"""
Gemini extra client helpers
"""

from typing import Dict, Any

import google.generativeai as genai

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.settings_storage import get_gemini_model

logger = get_logger(__name__)
config = get_settings()


class GeminiClientExtras:
    """Extra Gemini client methods"""

    async def count_tokens(self, text: str, model: str = None) -> int:
        try:
            client = await self._get_client(model)
            response = await self._run_to_thread(client.count_tokens, text)
            return response.total_tokens
        except Exception as exc:
            logger.error(f"Failed to count tokens: {exc}")
            raise

    async def get_model_info(self, model: str = None) -> Dict[str, Any]:
        try:
            api_key = config.gemini_api_key
            if not api_key:
                return {"error": "No Gemini API key configured"}

            genai.configure(api_key=api_key)
            model_info = genai.get_model(model)
            return {
                "name": model,
                "display_name": model_info.display_name,
                "description": model_info.description,
                "input_token_limit": model_info.input_token_limit,
                "output_token_limit": model_info.output_token_limit,
                "supported_generation_methods": model_info.supported_generation_methods,
                "temperature": model_info.temperature,
                "top_p": model_info.top_p,
                "top_k": model_info.top_k
            }
        except Exception as exc:
            logger.error(f"Failed to get model info: {exc}")
            return {"error": str(exc)}

    async def validate_key(self, api_key: str) -> bool:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(get_gemini_model())
            await self._run_to_thread(model.generate_content, "test", stream=False)
            return True
        except Exception as exc:
            logger.error(f"API key validation failed: {exc}")
            return False

    async def _run_to_thread(self, func, *args, **kwargs):
        import asyncio
        return await asyncio.to_thread(func, *args, **kwargs)
