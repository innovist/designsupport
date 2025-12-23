"""
Project schemas for API
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Project create schema"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    prompt: str = Field(..., min_length=1)
    gender: Optional[str] = None
    age_group: Optional[str] = None
    season: Optional[str] = None
    region: Optional[str] = None
    target_audience: Optional[str] = None
    language: str = "ko"
    size_standard: str = "KS"
    crawl_sources: Optional[List[str]] = None
    crawl_keywords: Optional[List[str]] = None
    max_crawl_pages: int = 100
    preferred_image_model: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Project update schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    gender: Optional[str] = None
    age_group: Optional[str] = None
    season: Optional[str] = None
    language: Optional[str] = None
    size_standard: Optional[str] = None
    crawl_sources: Optional[List[str]] = None
    crawl_keywords: Optional[List[str]] = None
    preferred_image_model: Optional[str] = None


class ProjectResponse(BaseModel):
    """Project response schema"""
    id: int
    title: str
    description: Optional[str]
    status: str
    progress_percent: int
    language: str
    size_standard: str
    preferred_image_model: Optional[str] = None
    session_count: int = 0
    created_at: str
    updated_at: Optional[str]
