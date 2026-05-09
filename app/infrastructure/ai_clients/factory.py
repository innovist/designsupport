"""
AI client factory: resolves FeatureModelSetting -> provider -> client instance.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.ports.ai_client import AIClient
from app.core.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.repositories.workspace_repository import WorkspaceRepository

logger = get_logger(__name__)
settings = get_settings()

# @MX:NOTE: [AUTO] Model ID mappings for API compatibility - display names to (actual_model_id, extra_body)
# Qwen display model_id → (actual API model_id, extra_body or None)
# "-non" variants call the same API model with thinking disabled.
_QWEN_MODEL_MAP: dict[str, tuple[str, dict | None]] = {
    "qwen3.6-flash":       ("qwen3.6-flash",       None),
    "qwen3.6-Flash-non":   ("qwen3.6-flash",       {"enable_thinking": False}),
    "qwen3.6-max-preview":  ("qwen3.6-max-preview",  None),
    "qwen3.6-Max-non":     ("qwen3.6-max-preview",  {"enable_thinking": False}),
    "qwen3.6-plus":        ("qwen3.6-plus",          None),
    "qwen3.6-Plus-Non":    ("qwen3.6-plus",          {"enable_thinking": False}),
    "qwen-plus":           ("qwen-plus",              None),
    "qwen3.5-flash":       ("qwen3.5-flash",          None),
}

# Mimo display model_id → (actual API model_id, extra_body or None)
_MIMO_MODEL_MAP: dict[str, tuple[str, dict | None]] = {
    "mimo-v2.5-pro":     ("mimo-v2.5-pro",  None),
    "mimo-v2.5-pro-non": ("mimo-v2.5-pro",  {"thinking": {"type": "disabled"}}),
    "mimo-v2.5":         ("mimo-v2.5",       None),
    "mimo-v2.5-non":     ("mimo-v2.5",       {"thinking": {"type": "disabled"}}),
    "mimo-v2-pro":       ("mimo-v2-pro",     None),
    "mimo-v2-omni":      ("mimo-v2-omni",    None),
    "mimo-v2-flash":     ("mimo-v2-flash",   None),
}

# Gemini models that use IMAGE response modality (not text completion).
_GEMINI_IMAGE_MODELS: frozenset[str] = frozenset({
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
})

# Kimi always requires explicit thinking flag via extra_body.
_KIMI_MODEL_MAP: dict[str, tuple[str, dict]] = {
    "kimi-k2.6":     ("kimi-k2.6",  {"thinking": {"type": "enabled"}}),
    "kimi-k2.6-non": ("kimi-k2.6",  {"thinking": {"type": "disabled"}}),
    "kimi-k2.5":     ("kimi-k2.5",  {"thinking": {"type": "enabled"}}),
    "kimi-k2.5-non": ("kimi-k2.5",  {"thinking": {"type": "disabled"}}),
}


class SettingsRequiredError(Exception):
    """Raised when a required FeatureModelSetting is missing."""

    def __init__(self, feature_key: str) -> None:
        super().__init__(
            f"No model configured for feature '{feature_key}'. "
            "Please set it in the workspace Settings page."
        )
        self.feature_key = feature_key
        self.action_required = "settings"


# @MX:ANCHOR: [AUTO] get_ai_client is called by every AI use-case
# @MX:REASON: Single point for provider resolution; failure here cascades to all AI features

async def get_ai_client(db: Session, feature_key: str) -> AIClient:
    """
    Look up the FeatureModelSetting for feature_key and return the matching client.
    Raises SettingsRequiredError if not configured.
    """
    repo = WorkspaceRepository(db)
    workspace = repo.ensure_default_workspace()
    setting = repo.get_feature_model(workspace.id, feature_key)

    if not setting:
        raise SettingsRequiredError(feature_key)

    return _build_client(setting.provider, setting.model, setting.temperature, setting.max_tokens)


def _build_client(
    provider: str, model: str, temperature: float, max_tokens: int
) -> AIClient:
    """Instantiate an AI client for the given provider/model."""
    from app.infrastructure.ai_clients.openai_client import OpenAIClient

    provider_lower = provider.lower()

    if provider_lower == "openai":
        api_key = settings.openai_api_key
        if not api_key:
            raise SettingsRequiredError("openai_api_key")
        # gpt-image-1 and dall-e-* use images.generate(), all others use chat.completions
        return OpenAIClient(api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens)

    if provider_lower == "gemini":
        api_key = settings.effective_gemini_key()
        if not api_key:
            raise SettingsRequiredError("gemini_api_key")
        if model in _GEMINI_IMAGE_MODELS:
            from app.infrastructure.ai_clients.gemini_image_client import GeminiImageClient
            return GeminiImageClient(api_key=api_key, model=model)
        from app.infrastructure.ai_clients.gemini_client import GeminiClient
        return GeminiClient(api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens)

    if provider_lower == "anthropic":
        api_key = settings.anthropic_api_key
        if not api_key:
            raise SettingsRequiredError("anthropic_api_key")
        from app.infrastructure.ai_clients.anthropic_client import AnthropicClient
        return AnthropicClient(api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens)

    if provider_lower == "seedream":
        api_key = settings.bytedance_seedream_api_key
        if not api_key:
            raise SettingsRequiredError("bytedance_seedream_api_key")
        return OpenAIClient(
            api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens,
            base_url="https://ark.ap-southeast.bytepluses.com/api/v3",
        )

    if provider_lower == "deepseek":
        api_key = settings.deepseek_api_key
        if not api_key:
            raise SettingsRequiredError("deepseek_api_key")
        return OpenAIClient(
            api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens,
            base_url="https://api.deepseek.com/v1",
        )

    if provider_lower == "alibaba":
        api_key = settings.alibaba_api_key
        if not api_key:
            raise SettingsRequiredError("alibaba_api_key")
        # z-image-turbo uses DashScope multimodal API (not OpenAI-compatible)
        if model in ("z-image-turbo", "z-image-turbo-think"):
            from app.infrastructure.ai_clients.zimage_client import ZImageTurboClient
            return ZImageTurboClient(api_key=api_key, prompt_extend=(model == "z-image-turbo-think"))
        base_url = settings.alibaba_compatible_base_url or "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        api_model_id, extra_body = _QWEN_MODEL_MAP.get(model, (model, None))
        extra: dict = {}
        if extra_body is not None:
            extra["extra_body"] = extra_body
        return OpenAIClient(
            api_key=api_key, model=api_model_id, temperature=temperature, max_tokens=max_tokens,
            base_url=base_url, **extra,
        )

    if provider_lower == "xiaomi":
        api_key = settings.xiaomi_mimo_api_key
        if not api_key:
            raise SettingsRequiredError("xiaomi_mimo_api_key")
        base_url = settings.xiaomi_mimo_base_url or "https://api.xiaomimimo.com/v1"
        api_model_id, extra_body = _MIMO_MODEL_MAP.get(model, (model, None))
        extra = {}
        if extra_body is not None:
            extra["extra_body"] = extra_body
        return OpenAIClient(
            api_key=api_key, model=api_model_id, temperature=temperature, max_tokens=max_tokens,
            base_url=base_url, **extra,
        )

    if provider_lower == "minimax":
        api_key = settings.minimax_api_key
        if not api_key:
            raise SettingsRequiredError("minimax_api_key")
        base_url = settings.minimax_base_url or "https://api.minimax.io/v1"
        # Minimax rejects temperature=0.0; clamp to 0.01 for deterministic calls.
        return OpenAIClient(
            api_key=api_key, model=model, temperature=max(0.01, temperature), max_tokens=max_tokens,
            base_url=base_url,
        )

    if provider_lower == "kimi":
        api_key = settings.kimi_api_key
        if not api_key:
            raise SettingsRequiredError("kimi_api_key")
        base_url = settings.kimi_base_url or "https://api.moonshot.ai/v1"
        api_model_id, extra_body = _KIMI_MODEL_MAP.get(
            model, (model, {"thinking": {"type": "enabled"}})
        )
        return OpenAIClient(
            api_key=api_key, model=api_model_id, temperature=temperature, max_tokens=max_tokens,
            base_url=base_url, extra_body=extra_body,
        )

    raise ValueError(
        f"Unknown AI provider '{provider}'. "
        "Supported: openai, gemini, anthropic, deepseek, alibaba, xiaomi, minimax, kimi, seedream."
    )
