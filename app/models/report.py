"""
Report model
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Float, Enum
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class ReportStatus(enum.Enum):
    """보고서 상태"""
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportFormat(enum.Enum):
    """보고서 포맷"""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"


class Report(BaseModel):
    """보고서 모델"""

    __tablename__ = "reports"

    # 기본 정보
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        comment="프로젝트 ID"
    )

    report_name = Column(
        String(200),
        nullable=False,
        comment="보고서 이름"
    )

    report_type = Column(
        String(50),
        nullable=False,
        comment="보고서 타입 (trend_analysis, design_proposal)"
    )

    # 상태
    status = Column(
        Enum(ReportStatus),
        nullable=False,
        default=ReportStatus.DRAFT,
        comment="보고서 상태"
    )

    # 내용
    language = Column(
        String(10),
        default="ko",
        nullable=False,
        comment="보고서 언어"
    )

    title = Column(
        String(500),
        nullable=True,
        comment="보고서 제목"
    )

    executive_summary = Column(
        Text,
        nullable=True,
        comment="요약"
    )

    target_audience = Column(
        Text,
        nullable=True,
        comment="타겟 고객"
    )

    research_scope = Column(
        Text,
        nullable=True,
        comment="조사 범위"
    )

    # 섹션
    market_analysis = Column(
        Text,
        nullable=True,
        comment="시장 분석"
    )

    trend_analysis = Column(
        Text,
        nullable=True,
        comment="트렌드 분석"
    )

    competitor_analysis = Column(
        Text,
        nullable=True,
        comment="경쟁사 분석"
    )

    design_proposals = Column(
        Text,
        nullable=True,
        comment="디자인 제안 (JSON)"
    )

    recommendations = Column(
        Text,
        nullable=True,
        comment="추천 사항"
    )

    conclusion = Column(
        Text,
        nullable=True,
        comment="결론"
    )

    # 메타데이터
    word_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="단어 수"
    )

    character_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="문자 수"
    )

    # 파일 정보
    file_path = Column(
        String(1000),
        nullable=True,
        comment="파일 경로"
    )

    file_url = Column(
        String(1000),
        nullable=True,
        comment="파일 URL"
    )

    format = Column(
        Enum(ReportFormat),
        nullable=False,
        default=ReportFormat.MARKDOWN,
        comment="파일 포맷"
    )

    # 타임스탬프
    generated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="생성 시각"
    )

    # 관계
    project = relationship(
        "Project",
        back_populates="reports"
    )

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, name='{self.report_name}', type='{self.report_type}')>"

    # @MX:ANCHOR: [AUTO] Report generation state machine - lifecycle management
    # @MX:REASON: State transition methods called from 85+ locations across report service and pipeline
    def generate(self) -> None:
        """보고서 생성"""
        self.status = ReportStatus.GENERATING

    def complete(self) -> None:
        """보고서 완료"""
        self.status = ReportStatus.COMPLETED
        self.generated_at = datetime.utcnow()

    def fail(self) -> None:
        """보고서 실패"""
        self.status = ReportStatus.FAILED

    def update_counts(self) -> None:
        """단어 수 및 문자 수 업데이트"""
        content = " ".join(filter(None, [
            self.executive_summary or "",
            self.market_analysis or "",
            self.trend_analysis or "",
            self.competitor_analysis or "",
            self.recommendations or "",
            self.conclusion or ""
        ]))

        self.character_count = len(content)
        self.word_count = len(content.split())