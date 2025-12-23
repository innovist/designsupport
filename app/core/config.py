import os
from functools import lru_cache
from typing import List, Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import BaseModel, Field, field_validator


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 애플리케이션 기본 설정
    app_name: str = "Fashion AI Generator"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8912
    workers: int = 4

    # 데이터베이스 설정
    database_url: str = "sqlite:///./storage/fashion.db"
    redis_url: str = "redis://localhost:6379/0"

    # 보안 설정
    secret_key: str = "test-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API 키
    gemini_api_key: str = "test-gemini-key"
    glm_api_key: str = "test-glm-key"
    z_image_api_key: Optional[str] = None
    seedream_api_key: Optional[str] = None
    nano_banana_api_key: Optional[str] = None

    # 언어 및 지역화
    default_language: str = "ko"
    default_size_standard: str = "KS"
    supported_languages: List[str] = ["ko", "zh-CN", "zh-TW", "en"]

    @field_validator("supported_languages", mode="before")
    @classmethod
    def parse_languages(cls, v):
        if isinstance(v, str):
            return [lang.strip() for lang in v.split(",")]
        return v

    # 크롤러 설정
    max_crawl_pages: int = 100
    crawl_delay_seconds: int = 1
    max_concurrent_crawls: int = 10
    crawler_timeout_seconds: int = 30

    # AI 모델 설정
    max_prompt_length: int = 4000
    analysis_timeout_seconds: int = 300
    generation_timeout_seconds: int = 600
    max_retries: int = 3

    # 품질 임계값
    consistency_threshold: float = 0.85
    prompt_fidelity_threshold: float = 0.90
    reproduction_threshold: float = 0.95

    @field_validator("consistency_threshold", "prompt_fidelity_threshold", "reproduction_threshold")
    @classmethod
    def validate_thresholds(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        return v

    # 파일 저장 설정
    upload_dir: str = "./uploads"
    static_dir: str = "./static"
    max_file_size_mb: int = 10

    # 로깅 설정
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_rotation: str = "daily"
    log_retention_days: int = 30

    # 레이트 limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # 캐시 설정
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 1000

    # GPU 설정
    gpu_enabled: bool = True
    cuda_visible_devices: str = "0"

    # 외부 서비스 URL
    comfyui_api_url: str = "http://localhost:8188"
    seedream_api_url: str = "https://ark.ap-southeast.bytepluses.com/api/v3"
    nano_banana_api_url: str = "https://api.nano-banana.com/v1"
    searxng_api_url: Optional[str] = None

    # 모니터링
    enable_metrics: bool = False
    metrics_port: int = 9090
    health_check_interval: int = 30

    # 기능 플래그
    enable_crawling: bool = True
    enable_analysis: bool = True
    enable_generation: bool = True
    enable_blueprint: bool = True
    enable_i18n: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields in .env

    @property
    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.environment.lower() == "development"

    @property
    def cors_origins(self) -> List[str]:
        """CORS 허용 오리진"""
        if self.is_development:
            return ["http://localhost:3000", "http://localhost:8000"]
        else:
            return []  # 프로덕션에서는 명시적으로 설정 필요

    @property
    def database_config(self) -> dict:
        """데이터베이스 연결 설정"""
        return {
            "url": self.database_url,
            "echo": self.debug,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }

    @property
    def redis_config(self) -> dict:
        """Redis 연결 설정"""
        return {
            "url": self.redis_url,
            "decode_responses": True,
            "health_check_interval": 30,
        }

    def get_available_models(self) -> List[str]:
        """GPU 가용성에 따른 사용 가능한 모델 목록"""
        if self.gpu_enabled and self.z_image_api_key:
            return ["Z-Image-turbo", "Seedream 4.5", "Nano Banana"]
        else:
            return ["Seedream 4.5", "Nano Banana"]

    def get_size_standards(self) -> List[str]:
        """지원하는 치수 표준 목록"""
        return ["KS", "GB", "ASTM", "ISO"]

    def validate_language(self, language: str) -> bool:
        """지원하는 언어인지 확인"""
        return language in self.supported_languages

    def validate_size_standard(self, standard: str) -> bool:
        """지원하는 치수 표준인지 확인"""
        return standard in self.get_size_standards()


@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스 반환 (캐시된)"""
    settings_obj = Settings()

    # Load stored API keys from file
    try:
        from app.core.settings_storage import load_settings
        stored = load_settings()
        api_keys = stored.get("api_keys", {})

        if api_keys.get("gemini"):
            settings_obj.gemini_api_key = api_keys["gemini"]
        if api_keys.get("glm"):
            settings_obj.glm_api_key = api_keys["glm"]
        if api_keys.get("seedream"):
            settings_obj.seedream_api_key = api_keys["seedream"]
        if api_keys.get("nano_banana"):
            settings_obj.nano_banana_api_key = api_keys["nano_banana"]

        # Load config
        config = stored.get("config", {})
        if config.get("crawler_workers"):
            settings_obj.max_concurrent_crawls = config["crawler_workers"]
        if config.get("crawler_timeout"):
            settings_obj.crawler_timeout_seconds = config["crawler_timeout"]
        searxng_url = config.get("searxng_api_url")
        if isinstance(searxng_url, str) and searxng_url.strip():
            settings_obj.searxng_api_url = searxng_url.strip()
    except Exception:
        pass  # On first run, storage may not exist yet

    return settings_obj


# 전역 설정 인스턴스
settings = get_settings()


def get_config() -> Settings:
    """레거시 호환: get_settings alias"""
    return get_settings()
