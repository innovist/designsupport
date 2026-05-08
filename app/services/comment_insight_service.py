"""
Comment insight summarization service
"""

from typing import Any, Dict, List, Optional
import json

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.settings_storage import get_gemini_model, get_glm_model
from app.services.pipeline_utils import parse_json
from ai_clients.gemini_client import get_gemini_client
from ai_clients.glm_client import GLMClient

logger = get_logger(__name__)
settings = get_settings()

LANGUAGE_LABELS = {
    "ko": "Korean",
    "en": "English",
    "zh-CN": "Simplified Chinese",
    "zh-TW": "Traditional Chinese",
}

MAX_COMMENTS = 200
MAX_COMMENT_LENGTH = 300
MAX_TOTAL_CHARS = 20000


def _language_label(language: str) -> str:
    return LANGUAGE_LABELS.get(language, language)


def _trim_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "..."


class CommentInsightService:
    """Summarize comment insights from crawled data."""

    def __init__(self) -> None:
        self.client = get_gemini_client()
        self.glm_client = GLMClient()

    def _extract_comment_texts(self, raw_data: Any) -> List[str]:
        if not isinstance(raw_data, list):
            return []

        collected: List[str] = []
        total_chars = 0

        for item in raw_data:
            if not isinstance(item, dict):
                continue
            metadata = item.get("metadata") or {}
            comments = metadata.get("comments") or []
            if not isinstance(comments, list):
                continue

            source = item.get("source") or item.get("platform") or ""
            title = item.get("title") or ""

            for comment in comments:
                if not isinstance(comment, dict):
                    continue
                content = comment.get("content") or ""
                if not isinstance(content, str):
                    continue
                content = content.strip()
                if not content:
                    continue

                prefix = f"[{source}] {title}".strip()
                text = _trim_text(content, MAX_COMMENT_LENGTH)
                line = f"{prefix}: {text}" if prefix else text

                total_chars += len(line)
                if total_chars > MAX_TOTAL_CHARS:
                    return collected

                collected.append(line)
                if len(collected) >= MAX_COMMENTS:
                    return collected

        return collected

    async def summarize(
        self,
        raw_data: Any,
        filters: Dict[str, Any],
        user_input: str
    ) -> Optional[Dict[str, Any]]:
        comments = self._extract_comment_texts(raw_data)
        if not comments:
            return None

        language = _language_label(settings.default_language)
        payload = {
            "filters": filters or {},
            "user_input": user_input or "",
            "comments": comments
        }
        system_instruction = (
            "You are a fashion trend research analyst. Summarize real user comments and reveal"
            " hidden opinions and latent needs. Only use the provided comments. "
            f"Respond in {language}. Output strict JSON with keys: "
            "summary, dominant_opinions, hidden_needs, sentiment, unexpected_signals, representative_quotes."
        )
        prompt = json.dumps(payload, ensure_ascii=False)

        try:
            response = await self.client.generate_content(
                prompt=prompt,
                model=get_gemini_model(),
                system_instruction=system_instruction
            )
        except Exception as exc:
            logger.warning(f"Gemini comment insights failed, falling back to GLM: {exc}")
            response = await self.glm_client.generate_content(
                prompt=prompt,
                model=get_glm_model(),
                system_prompt=system_instruction
            )
        if not response or not hasattr(response, 'text') or not response.text:
            raise ValueError("Comment insight response is empty")

        data = parse_json(response.text)
        if not isinstance(data, dict):
            raise ValueError("Comment insight is not a JSON object")

        required_keys = {
            "summary",
            "dominant_opinions",
            "hidden_needs",
            "sentiment",
            "unexpected_signals",
            "representative_quotes",
        }
        missing = required_keys - set(data.keys())
        if missing:
            raise ValueError(f"Missing comment insight keys: {sorted(missing)}")

        logger.info("Comment insights summarized")
        return data
