"""
Project model
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class ProjectStatus(enum.Enum):
    """프로젝트 상태"""
    DRAFT = "draft"
    ACTIVE = "active"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Gender(enum.Enum):
    """성별"""
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"


class Season(enum.Enum):
    """시즌"""
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"
    ALL_SEASON = "all_season"


class Project(BaseModel):
    """프로젝트 모델"""

    __tablename__ = "projects"

    # 기본 정보
    title = Column(
        String(200),
        nullable=False,
        comment="프로젝트 제목"
    )

    description = Column(
        Text,
        nullable=True,
        comment="프로젝트 설명"
    )

    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="소유자 ID"
    )

    # 상태
    status = Column(
        Enum(ProjectStatus),
        nullable=False,
        default=ProjectStatus.DRAFT,
        comment="프로젝트 상태"
    )

    progress_percent = Column(
        Integer,
        default=0,
        nullable=False,
        comment="진행률 (0-100)"
    )

    # 입력 파라미터
    prompt = Column(
        Text,
        nullable=False,
        comment="사용자 입력 프롬프트"
    )

    gender = Column(
        Enum(Gender),
        nullable=True,
        comment="성별"
    )

    age_group = Column(
        String(50),
        nullable=True,
        comment="연령대"
    )

    season = Column(
        Enum(Season),
        nullable=True,
        comment="시즌"
    )

    region = Column(
        String(100),
        nullable=True,
        comment="지역"
    )

    target_audience = Column(
        Text,
        nullable=True,
        comment="타겟 고객"
    )

    # 설정
    language = Column(
        String(10),
        default="ko",
        nullable=False,
        comment="결과물 언어"
    )

    size_standard = Column(
        String(10),
        default="KS",
        nullable=False,
        comment="치수 표준"
    )

    # 크롤링 설정
    crawl_sources = Column(
        Text,
        nullable=True,
        comment="크롤링 소스 (JSON)"
    )

    crawl_keywords = Column(
        Text,
        nullable=True,
        comment="크롤링 키워드 (JSON)"
    )

    max_crawl_pages = Column(
        Integer,
        default=100,
        nullable=False,
        comment="최대 크롤링 페이지 수"
    )

    # 결과물 설정
    preferred_image_model = Column(
        String(50),
        nullable=True,
        comment="선호 이미지 생성 모델"
    )

    # 타임스탬프
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="시작 시각"
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="완료 시각"
    )

    # 관계
    owner = relationship(
        "User",
        back_populates="projects"
    )

    sessions = relationship(
        "Session",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    versions = relationship(
        "Version",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    crawl_jobs = relationship(
        "CrawlJob",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    trend_analyses = relationship(
        "TrendAnalysis",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    design_concepts = relationship(
        "DesignConcept",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    generation_jobs = relationship(
        "GenerationJob",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    reports = relationship(
        "Report",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, title='{self.title}', status='{self.status.value}')>"

    def start(self) -> None:
        """프로젝트 시작"""
        self.status = ProjectStatus.ACTIVE
        self.started_at = datetime.utcnow()
        self.progress_percent = 0

    def update_progress(self, percent: int) -> None:
        """진행률 업데이트"""
        self.progress_percent = max(0, min(100, percent))
        if percent > 0 and self.status == ProjectStatus.ACTIVE:
            if percent < 40:
                self.status = ProjectStatus.ANALYZING
            elif percent < 80:
                self.status = ProjectStatus.GENERATING
            else:
                self.status = ProjectStatus.COMPLETED
                self.completed_at = datetime.utcnow()

    def complete(self) -> None:
        """프로젝트 완료"""
        self.status = ProjectStatus.COMPLETED
        self.progress_percent = 100
        self.completed_at = datetime.utcnow()

    def fail(self, error_message: str = None) -> None:
        """프로젝트 실패"""
        self.status = ProjectStatus.FAILED
        if error_message:
            self.update_metadata(error_message=error_message)

    def cancel(self) -> None:
        """프로젝트 취소"""
        self.status = ProjectStatus.CANCELLED


from .session import Session
from .version import Version
