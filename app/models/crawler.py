"""
Crawler related models
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Float, Enum, Boolean
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class CrawlStatus(enum.Enum):
    """크롤링 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlJob(BaseModel):
    """크롤링 작업 모델"""

    __tablename__ = "crawl_jobs"

    # 기본 정보
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        comment="프로젝트 ID"
    )

    job_name = Column(
        String(200),
        nullable=False,
        comment="작업 이름"
    )

    # 상태
    status = Column(
        Enum(CrawlStatus),
        nullable=False,
        default=CrawlStatus.PENDING,
        comment="크롤링 상태"
    )

    progress_percent = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="진행률 (0-100)"
    )

    # 크롤링 설정
    crawler_type = Column(
        String(50),
        nullable=False,
        comment="크롤러 타입"
    )

    target_urls = Column(
        Text,
        nullable=True,
        comment="대상 URL 목록 (JSON)"
    )

    keywords = Column(
        Text,
        nullable=True,
        comment="검색 키워드 (JSON)"
    )

    max_pages = Column(
        Integer,
        default=100,
        nullable=False,
        comment="최대 페이지 수"
    )

    delay_seconds = Column(
        Integer,
        default=1,
        nullable=False,
        comment="요청 간격 (초)"
    )

    # 결과
    total_pages_found = Column(
        Integer,
        default=0,
        nullable=False,
        comment="발견된 페이지 수"
    )

    total_pages_crawled = Column(
        Integer,
        default=0,
        nullable=False,
        comment="크롤링된 페이지 수"
    )

    total_items_found = Column(
        Integer,
        default=0,
        nullable=False,
        comment="발견된 아이템 수"
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

    # 에러 정보
    error_message = Column(
        Text,
        nullable=True,
        comment="에러 메시지"
    )

    # 관계
    project = relationship(
        "Project",
        back_populates="crawl_jobs"
    )

    raw_data_items = relationship(
        "RawData",
        back_populates="crawl_job",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CrawlJob(id={self.id}, status='{self.status.value}', progress={self.progress_percent})>"

    # @MX:ANCHOR: [AUTO] Crawl job state machine - lifecycle management
    # @MX:REASON: State transition methods called from 85+ locations across crawler service and pipeline
    def start(self) -> None:
        """크롤링 시작"""
        self.status = CrawlStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.progress_percent = 0.0

    def update_progress(self, crawled: int, total: int) -> None:
        """진행률 업데이트"""
        self.total_pages_crawled = crawled
        if total > 0:
            self.progress_percent = round((crawled / total) * 100, 2)

    def complete(self) -> None:
        """크롤링 완료"""
        self.status = CrawlStatus.COMPLETED
        self.progress_percent = 100.0
        self.completed_at = datetime.utcnow()

    def fail(self, error_message: str) -> None:
        """크롤링 실패"""
        self.status = CrawlStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    def cancel(self) -> None:
        """크롤링 취소"""
        self.status = CrawlStatus.CANCELLED
        self.completed_at = datetime.utcnow()


class RawData(BaseModel):
    """수집된 원본 데이터 모델"""

    __tablename__ = "raw_data"

    # 기본 정보
    crawl_job_id = Column(
        Integer,
        ForeignKey("crawl_jobs.id"),
        nullable=False,
        index=True,
        comment="크롤링 작업 ID"
    )

    source = Column(
        String(100),
        nullable=False,
        comment="데이터 소스"
    )

    source_id = Column(
        String(200),
        nullable=True,
        comment="소스별 ID"
    )

    url = Column(
        String(1000),
        nullable=False,
        comment="원본 URL"
    )

    title = Column(
        String(500),
        nullable=True,
        comment="제목"
    )

    content = Column(
        Text,
        nullable=False,
        comment="본문 내용"
    )

    # 메타데이터
    author = Column(
        String(200),
        nullable=True,
        comment="작성자"
    )

    published_date = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="발행일"
    )

    view_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="조회수"
    )

    like_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="좋아요 수"
    )

    comment_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="댓글 수"
    )

    # 품질 평가
    quality_score = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="품질 점수 (0-1)"
    )

    relevance_score = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="관련성 점수 (0-1)"
    )

    # 처리 상태
    is_processed = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="처리 여부"
    )

    is_duplicate = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="중복 여부"
    )

    content_hash = Column(
        String(64),
        nullable=True,
        comment="내용 해시 (중복 검사용)"
    )

    # 관계
    crawl_job = relationship(
        "CrawlJob",
        back_populates="raw_data_items"
    )

    comments = relationship(
        "Comment",
        back_populates="raw_data",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<RawData(id={self.id}, source='{self.source}', title='{self.title[:50]}')>"


class Comment(BaseModel):
    """댓글 모델"""

    __tablename__ = "comments"

    # 기본 정보
    raw_data_id = Column(
        Integer,
        ForeignKey("raw_data.id"),
        nullable=False,
        index=True,
        comment="원본 데이터 ID"
    )

    comment_id = Column(
        String(200),
        nullable=True,
        comment="댓글 ID (소스별)"
    )

    author = Column(
        String(200),
        nullable=True,
        comment="작성자"
    )

    content = Column(
        Text,
        nullable=False,
        comment="댓글 내용"
    )

    # 메타데이터
    published_date = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="작성일"
    )

    like_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="좋아요 수"
    )

    # 분석 관련
    sentiment_score = Column(
        Float,
        nullable=True,
        comment="감성 분석 점수 (-1 to 1)"
    )

    is_relevant = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="관련성 여부"
    )

    # 관계
    raw_data = relationship(
        "RawData",
        back_populates="comments"
    )

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, author='{self.author}', content='{self.content[:50]}')>"