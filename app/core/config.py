"""
Application configuration loaded from environment variables / .env file.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings sourced from environment variables."""

    app_name: str = "Design Creative Support"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    # @MX:NOTE: [AUTO] Server port configuration - must match project memory setting
    port: int = 14000

    # PostgreSQL connection string
    database_url: str = "postgresql://localhost/designsupport"

    # ─── AI provider API keys ─────────────────────────────────────────────────
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_api_keys: Optional[str] = None   # .env uses GEMINI_API_KEYS (plural)
    anthropic_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    alibaba_api_key: Optional[str] = None
    xiaomi_mimo_api_key: Optional[str] = None
    minimax_api_key: Optional[str] = None
    kimi_api_key: Optional[str] = None
    bytedance_seedream_api_key: Optional[str] = None

    # ─── Image search APIs ────────────────────────────────────────────────────
    unsplash_access_key: Optional[str] = None
    pexels_api_key: Optional[str] = None
    pixabay_api_key: Optional[str] = None

    # ─── File storage ─────────────────────────────────────────────────────────
    upload_dir: str = "./uploads"
    static_dir: str = "./static"
    max_file_size_mb: int = 50

    # ─── Logging ──────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # ─── Provider base URLs (optional overrides from .env) ───────────────────
    minimax_base_url: Optional[str] = None
    kimi_base_url: Optional[str] = None
    xiaomi_mimo_base_url: Optional[str] = None
    alibaba_compatible_base_url: Optional[str] = None

    # ─── SearXNG (optional) ───────────────────────────────────────────────────
    searxng_api_url: Optional[str] = None

    # ─── Search backend selection & configuration ─────────────────────────────
    search_backend: str = "none"  # none / searxng / external / crawl4ai
    web_search_crawler_api_base_url: Optional[str] = None
    web_search_crawler_api_token: Optional[str] = None
    web_search_crawler_api_poll_interval_seconds: int = 30
    crawl4ai_api_url: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    def effective_gemini_key(self) -> Optional[str]:
        """Return whichever Gemini key is set (GEMINI_API_KEY or GEMINI_API_KEYS)."""
        return self.gemini_api_key or self.gemini_api_keys

    def get_provider_api_key(self, provider: str) -> Optional[str]:
        """Return the API key for the given provider name."""
        mapping = {
            "openai": self.openai_api_key,
            "gemini": self.effective_gemini_key(),
            "anthropic": self.anthropic_api_key,
            "deepseek": self.deepseek_api_key,
            "alibaba": self.alibaba_api_key,
            "xiaomi": self.xiaomi_mimo_api_key,
            "minimax": self.minimax_api_key,
            "kimi": self.kimi_api_key,
            "seedream": self.bytedance_seedream_api_key,
        }
        return mapping.get(provider.lower())

    def available_providers(self) -> list[str]:
        """Return list of providers that have an API key configured."""
        providers = []
        if self.openai_api_key:
            providers.append("openai")
        if self.effective_gemini_key():
            providers.append("gemini")
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.deepseek_api_key:
            providers.append("deepseek")
        if self.alibaba_api_key:
            providers.append("alibaba")
        if self.xiaomi_mimo_api_key:
            providers.append("xiaomi")
        if self.minimax_api_key:
            providers.append("minimax")
        if self.kimi_api_key:
            providers.append("kimi")
        if self.bytedance_seedream_api_key:
            providers.append("seedream")
        return providers


# @MX:ANCHOR: [AUTO] Cached settings provider used across all modules
# @MX:REASON: High fan_in (6+ direct imports) - single source of truth for configuration

@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
