"""
Settings Storage Module - Persists user settings to file
API keys and config are saved to a JSON file in storage directory
"""

# @MX:NOTE: [AUTO] Settings persistence layer - maintains 20+ configuration accessor methods
# Centralizes API keys, model configurations, and user preferences across the application

import json
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache

from app.core.logging import get_logger

logger = get_logger(__name__)

SETTINGS_DIR = Path(__file__).parent.parent.parent / "storage" / "config"
SETTINGS_FILE = SETTINGS_DIR / "user_settings.json"

# ======================================================================
# AI 모델 설정 - 절대 하드코딩 금지! 항상 이 설정에서 가져와서 사용할 것!
# Gemini: 2.5 시리즈만 사용 (2.0은 지원 종료됨)
# ======================================================================
AVAILABLE_MODELS = {
    "gemini": {
        "text": ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro"],
        "default": "gemini-2.5-flash"
    },
    "glm": {
        "text": ["glm-4.7", "glm-4-flash"],
        "default": "glm-4.7"
    },
    "image": {
        "seedream": ["seedream-4.5"],
        "nano_banana": ["nano-banana-base", "nano-banana-pro"]
    },
    "research": {
        "gemini_search": ["gemini-2.5-flash"],
        "perplexity": ["sonar", "sonar-pro"],
        "glm_research": ["glm-4.7"]
    }
}

SEEDREAM_MODEL_IDS = {
    "seedream-4.5": "seedream-4-5-251128",
    "seedream-4.0": "seedream-4-0-250828"
}

NANO_BANANA_GOOGLE_MODEL_IDS = {
    "nano-banana-base": "gemini-2.5-flash-image",
    "nano-banana-pro": "gemini-3-pro-image-preview"
}

NANO_BANANA_REST_MODEL_IDS = {
    "nano-banana-base": "nano-banana-v2",
    "nano-banana-pro": "nano-banana-pro"
}

DEFAULT_SETTINGS = {
    "api_keys": {
        "gemini": None,
        "glm": None,
        "seedream": None,
        "nano_banana": None,
        "perplexity": None
    },
    "models": {
        "gemini_text": "gemini-2.5-flash",
        "gemini_fallback": "glm-4.7",
        "glm_text": "glm-4.7",
        "seedream_image": "seedream-4.5",
        "nano_banana_image": "nano-banana-base"
    },
    "config": {
        "crawler_workers": 5,
        "crawler_timeout": 30,
        "searxng_api_url": "http://localhost:8913"
    },
    "ai_research": {
        "enabled": False,
        "models": {
            "gemini_search": False,
            "perplexity": False,
            "glm_research": False
        },
        "perplexity_model": "sonar",
        "research_depth": "standard"
    }
}


def ensure_settings_dir() -> None:
    """Create settings directory if it doesn't exist"""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> Dict[str, Any]:
    """Load settings from file"""
    ensure_settings_dir()
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.info("User settings loaded from file")
                return {**DEFAULT_SETTINGS, **data}
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load settings: {e}")
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to file"""
    ensure_settings_dir()
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        logger.info("User settings saved to file")
        return True
    except IOError as e:
        logger.error(f"Failed to save settings: {e}")
        return False


def get_api_key(service: str) -> Optional[str]:
    """Get API key for a service"""
    settings = load_settings()
    return settings.get("api_keys", {}).get(service)


def save_api_key(service: str, api_key: str) -> bool:
    """Save API key for a service"""
    settings = load_settings()
    if "api_keys" not in settings:
        settings["api_keys"] = {}
    settings["api_keys"][service] = api_key
    return save_settings(settings)


def get_config() -> Dict[str, Any]:
    """Get config settings"""
    settings = load_settings()
    return settings.get("config", DEFAULT_SETTINGS["config"])


def save_config(config: Dict[str, Any]) -> bool:
    """Save config settings"""
    settings = load_settings()
    if "config" not in settings:
        settings["config"] = {}
    settings["config"].update(config)
    return save_settings(settings)


@lru_cache()
def get_stored_settings() -> Dict[str, Any]:
    """Get cached settings (use for startup)"""
    return load_settings()


def clear_settings_cache() -> None:
    """Clear cached settings to force reload"""
    get_stored_settings.cache_clear()


# ======================================================================
# 모델명 가져오기 함수 - 코드에서 반드시 이 함수들을 사용할 것!
# 하드코딩 절대 금지!
# ======================================================================
def get_gemini_model() -> str:
    """Get configured Gemini model name"""
    settings = load_settings()
    model = settings.get("models", {}).get("gemini_text")
    if model and model in AVAILABLE_MODELS["gemini"]["text"]:
        return model
    return AVAILABLE_MODELS["gemini"]["default"]


def get_glm_model() -> str:
    """Get configured GLM model name (fallback)"""
    settings = load_settings()
    model = settings.get("models", {}).get("glm_text")
    if model and model in AVAILABLE_MODELS["glm"]["text"]:
        return model
    return AVAILABLE_MODELS["glm"]["default"]


def get_fallback_model() -> str:
    """Get fallback model when primary fails"""
    settings = load_settings()
    model = settings.get("models", {}).get("gemini_fallback")
    if model:
        return model
    return AVAILABLE_MODELS["glm"]["default"]


def get_seedream_model() -> str:
    """Get configured Seedream image model name"""
    settings = load_settings()
    model = settings.get("models", {}).get("seedream_image")
    options = AVAILABLE_MODELS.get("image", {}).get("seedream", [])
    if model and model in options:
        return model
    return options[0] if options else "seedream-4.5"


def get_seedream_model_id(model: Optional[str] = None) -> str:
    """Get Seedream API model ID for the configured model"""
    name = model or get_seedream_model()
    return SEEDREAM_MODEL_IDS.get(name, name)


def get_nano_banana_model() -> str:
    """Get configured Nano Banana image model name"""
    settings = load_settings()
    model = settings.get("models", {}).get("nano_banana_image")
    options = AVAILABLE_MODELS.get("image", {}).get("nano_banana", [])
    if model and model in options:
        return model
    return options[0] if options else "nano-banana-base"


def get_nano_banana_base_model() -> str:
    """Get Nano Banana base model name"""
    options = AVAILABLE_MODELS.get("image", {}).get("nano_banana", [])
    if "nano-banana-base" in options:
        return "nano-banana-base"
    return options[0] if options else "nano-banana-base"


def get_nano_banana_pro_model() -> str:
    """Get Nano Banana pro model name"""
    options = AVAILABLE_MODELS.get("image", {}).get("nano_banana", [])
    if "nano-banana-pro" in options:
        return "nano-banana-pro"
    return options[-1] if options else "nano-banana-pro"


def get_nano_banana_model_id(model: Optional[str] = None, provider: str = "google") -> str:
    """Get Nano Banana provider model ID (google/rest)"""
    name = model or get_nano_banana_model()
    if provider == "google":
        return NANO_BANANA_GOOGLE_MODEL_IDS.get(name, name)
    return NANO_BANANA_REST_MODEL_IDS.get(name, name)


def save_model_settings(gemini_model: str, glm_model: str) -> bool:
    """Save model settings"""
    settings = load_settings()
    if "models" not in settings:
        settings["models"] = {}
    settings["models"]["gemini_text"] = gemini_model
    settings["models"]["glm_text"] = glm_model
    settings["models"]["gemini_fallback"] = glm_model
    return save_settings(settings)


def get_available_models() -> Dict[str, Any]:
    """Get list of available models for UI"""
    return AVAILABLE_MODELS
