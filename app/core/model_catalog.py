"""
Central model catalog — single source of truth for all provider/model definitions.

Used by:
  - API route: /api/workspace/available-models
  - WorkspaceRepository: DEFAULT_FEATURE_MODELS & stale-model migration
"""

from typing import Any

MODEL_CATALOG: dict[str, dict[str, Any]] = {
    "openai": {
        "label": "OpenAI",
        "models": [
            {"id": "gpt-5.4",       "label": "GPT-5.4",       "types": ["text", "multimodal"]},
            {"id": "gpt-5.4-mini",  "label": "GPT-5.4 mini",  "types": ["text", "multimodal"]},
            {"id": "gpt-5.4-nano",  "label": "GPT-5.4 nano",  "types": ["text", "multimodal"]},
            {"id": "gpt-image-1",   "label": "GPT Image-1",   "types": ["image"]},
        ],
    },
    "gemini": {
        "label": "Google Gemini",
        "models": [
            {"id": "gemini-3.1-pro-preview",        "label": "Gemini 3.1 Pro",         "types": ["text", "multimodal"]},
            {"id": "gemini-3-flash-preview",         "label": "Gemini 3 Flash",          "types": ["text", "multimodal"]},
            {"id": "gemini-3.1-flash-lite",          "label": "Gemini 3.1 Flash Lite",   "types": ["text", "multimodal"]},
            {"id": "gemini-3.1-flash-image-preview", "label": "Gemini 3.1 Flash Image",  "types": ["image"]},
            {"id": "gemini-3-pro-image-preview",     "label": "Gemini 3 Pro Image",      "types": ["image"]},
            {"id": "gemini-2.5-flash-image",         "label": "Gemini 2.5 Flash Image",  "types": ["image"]},
        ],
    },
    "deepseek": {
        "label": "DeepSeek",
        "models": [
            {"id": "deepseek-chat",     "label": "DeepSeek v3.2 Chat",  "types": ["text"]},
            {"id": "deepseek-v4-pro",   "label": "DeepSeek V4 Pro",     "types": ["text"]},
            {"id": "deepseek-v4-flash", "label": "DeepSeek V4 Flash",   "types": ["text"]},
        ],
    },
    "alibaba": {
        "label": "Alibaba (Qwen)",
        "models": [
            {"id": "qwen3.6-flash",       "label": "Qwen 3.6 Flash",              "types": ["text", "multimodal"]},
            {"id": "qwen3.6-Flash-non",   "label": "Qwen 3.6 Flash (no think)",   "types": ["text", "multimodal"]},
            {"id": "qwen3.6-max-preview", "label": "Qwen 3.6 Max",                "types": ["text", "multimodal"]},
            {"id": "qwen3.6-Max-non",     "label": "Qwen 3.6 Max (no think)",     "types": ["text", "multimodal"]},
            {"id": "qwen3.6-plus",        "label": "Qwen 3.6 Plus",               "types": ["text", "multimodal"]},
            {"id": "qwen3.6-Plus-Non",    "label": "Qwen 3.6 Plus (no think)",    "types": ["text", "multimodal"]},
            {"id": "qwen-plus",           "label": "Qwen 3.5 Plus",               "types": ["text", "multimodal"]},
            {"id": "qwen3.5-flash",       "label": "Qwen 3.5 Flash",              "types": ["text", "multimodal"]},
            {"id": "z-image-turbo",       "label": "Z Image Turbo",               "types": ["image"]},
            {"id": "z-image-turbo-think", "label": "Z Image Turbo (Think)",       "types": ["image"]},
        ],
    },
    "xiaomi": {
        "label": "Xiaomi Mimo",
        "models": [
            {"id": "mimo-v2.5-pro",     "label": "Mimo v2.5 Pro",            "types": ["text"]},
            {"id": "mimo-v2.5-pro-non", "label": "Mimo v2.5 Pro (no think)", "types": ["text"]},
            {"id": "mimo-v2.5",         "label": "Mimo v2.5",                "types": ["text", "multimodal"]},
            {"id": "mimo-v2.5-non",     "label": "Mimo v2.5 (no think)",     "types": ["text", "multimodal"]},
            {"id": "mimo-v2-pro",       "label": "Mimo v2 Pro",              "types": ["text"]},
            {"id": "mimo-v2-omni",      "label": "Mimo v2 Omni",             "types": ["text", "multimodal"]},
            {"id": "mimo-v2-flash",     "label": "Mimo v2 Flash",            "types": ["text"]},
        ],
    },
    "minimax": {
        "label": "Minimax",
        "models": [
            {"id": "MiniMax-M2.7",           "label": "MiniMax M2.7",           "types": ["text"]},
            {"id": "MiniMax-M2.7-highspeed", "label": "MiniMax M2.7 Highspeed", "types": ["text"]},
        ],
    },
    "kimi": {
        "label": "Kimi (Moonshot)",
        "models": [
            {"id": "kimi-k2.6",     "label": "Kimi K2.6",            "types": ["text", "multimodal"]},
            {"id": "kimi-k2.6-non", "label": "Kimi K2.6 (no think)", "types": ["text", "multimodal"]},
            {"id": "kimi-k2.5",     "label": "Kimi K2.5",            "types": ["text", "multimodal"]},
            {"id": "kimi-k2.5-non", "label": "Kimi K2.5 (no think)", "types": ["text", "multimodal"]},
        ],
    },
    "seedream": {
        "label": "Seedream (ByteDance)",
        "models": [
            {"id": "seedream-5-0-260128", "label": "Seedream 5.0", "types": ["image"]},
            {"id": "seedream-4-5-251128", "label": "Seedream 4.5", "types": ["image"]},
            {"id": "seedream-4-0-250828", "label": "Seedream 4.0", "types": ["image"]},
        ],
    },
}

# Flat set of (provider, model_id) pairs for fast lookup
VALID_PROVIDER_MODELS: frozenset[tuple[str, str]] = frozenset(
    (provider, m["id"])
    for provider, info in MODEL_CATALOG.items()
    for m in info["models"]
)


def is_valid_model(provider: str, model_id: str) -> bool:
    return (provider, model_id) in VALID_PROVIDER_MODELS
