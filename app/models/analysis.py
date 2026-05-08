"""
Analysis related models
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Float, Enum, Boolean
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class AnalysisStatus(enum.Enum):
    """분석 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisModel(enum.Enum):
    """분석 모델"""
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_3_FLASH = "gemini-3-flash"
    GLM_4_7 = "glm-4.7"
    ENSEMBLE = "ensemble"


class TrendAnalysis(BaseModel):
    """트렌드 분석 모델"""

    __tablename__ = "trend_analyses"

    # 기본 정보
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        comment="프로젝트 ID"
    )

    analysis_name = Column(
        String(200),
        nullable=False,
        comment="분석 이름"
    )

    # 상태
    status = Column(
        Enum(AnalysisStatus),
        nullable=False,
        default=AnalysisStatus.PENDING,
        comment="분석 상태"
    )

    # 분석 설정
    model_used = Column(
        Enum(AnalysisModel),
        nullable=False,
        comment="사용된 분석 모델"
    )

    data_sources = Column(
        Text,
        nullable=True,
        comment="사용된 데이터 소스 (JSON)"
    )

    keywords = Column(
        Text,
        nullable=True,
        comment="주요 키워드 (JSON)"
    )

    # 분석 결과
    summary = Column(
        Text,
        nullable=True,
        comment="분석 요약"
    )

    key_trends = Column(
        Text,
        nullable=True,
        comment="주요 트렌드 (JSON)"
    )

    market_insights = Column(
        Text,
        nullable=True,
        comment="시장 인사이트 (JSON)"
    )

    recommendations = Column(
        Text,
        nullable=True,
        comment="추천 사항 (JSON)"
    )

    # 신뢰도
    confidence_score = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="신뢰도 점수 (0-1)"
    )

    data_coverage = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="데이터 커버리지 (0-1)"
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
        back_populates="trend_analyses"
    )

    insights = relationship(
        "TrendInsight",
        back_populates="analysis",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TrendAnalysis(id={self.id}, model='{self.model_used.value}', status='{self.status.value}')>"

    # @MX:ANCHOR: [AUTO] Analysis job state machine - lifecycle management
    # @MX:REASON: State transition methods called from 85+ locations across analysis service and pipeline
    def start(self) -> None:
        """분석 시작"""
        self.status = AnalysisStatus.RUNNING
        self.started_at = datetime.utcnow()

    def complete(self) -> None:
        """분석 완료"""
        self.status = AnalysisStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def fail(self, error_message: str) -> None:
        """분석 실패"""
        self.status = AnalysisStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()


class TrendInsight(BaseModel):
    """트렌드 인사이트 모델"""

    __tablename__ = "trend_insights"

    # 기본 정보
    analysis_id = Column(
        Integer,
        ForeignKey("trend_analyses.id"),
        nullable=False,
        index=True,
        comment="분석 ID"
    )

    category = Column(
        String(100),
        nullable=False,
        comment="인사이트 카테고리"
    )

    title = Column(
        String(500),
        nullable=False,
        comment="인사이트 제목"
    )

    description = Column(
        Text,
        nullable=False,
        comment="인사이트 설명"
    )

    # 관련 정보
    keywords = Column(
        Text,
        nullable=True,
        comment="관련 키워드 (JSON)"
    )

    source_urls = Column(
        Text,
        nullable=True,
        comment="근거 URL 목록 (JSON)"
    )

    source_ids = Column(
        Text,
        nullable=True,
        comment="근거 데이터 ID 목록 (JSON)"
    )

    # 평가
    impact_level = Column(
        String(20),
        nullable=True,
        comment="영향력 레벨 (low/medium/high)"
    )

    trend_strength = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="트렌드 강도 (0-1)"
    )

    confidence = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="신뢰도 (0-1)"
    )

    # 타겟 정보
    target_demographics = Column(
        Text,
        nullable=True,
        comment="타겟 인구통계 (JSON)"
    )

    relevant_seasons = Column(
        Text,
        nullable=True,
        comment="관련 시즌 (JSON)"
    )

    # 관계
    analysis = relationship(
        "TrendAnalysis",
        back_populates="insights"
    )

    def __repr__(self) -> str:
        return f"<TrendInsight(id={self.id}, category='{self.category}', title='{self.title[:50]}')>"