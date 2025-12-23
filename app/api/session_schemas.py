"""
Session schemas for API
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CrawlerConfig(BaseModel):
    """Crawler settings"""
    crawlers: List[str] = Field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_items_per_source: int = 100
    youtube_channel_urls: List[str] = Field(default_factory=list)
    youtube_keyword_count: Optional[int] = None
    youtube_channel_max: Optional[int] = None
    youtube_parallel: Optional[int] = None
    youtube_enable_stt: Optional[bool] = None


class SessionCreate(BaseModel):
    project_id: int
    session_title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    user_keywords: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    input_text: Optional[str] = None
    input_urls: Optional[List[str]] = None
    crawler_config: Optional[CrawlerConfig] = None
    auto_start: bool = True
    generate_images: bool = True
    generate_blueprints: bool = False
    blueprint_size_system: str = "KS"
    blueprint_size: str = "M"


class SessionUpdate(BaseModel):
    session_title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    project_id: int
    session_title: str
    description: str
    user_keywords: List[str]
    extracted_keywords: List[str] = Field(default_factory=list)
    filters: Dict[str, Any]
    crawler_config: Dict[str, Any]
    status: str
    progress_percent: float
    current_step: Optional[str]
    error_message: Optional[str] = None
    crawl_expected_items: int = 0
    crawl_collected_items: int = 0
    crawl_completed_keywords: int = 0
    crawl_total_keywords: int = 0
    needs_count: int
    ideas_count: int
    draft_count: int
    crawled_count: int
    keyword_count: int
    design_count: int
    model_image_count: int
    blueprint_count: int
    created_at: str
    updated_at: Optional[str]
    pipeline_results: Optional[Dict[str, Any]] = None
