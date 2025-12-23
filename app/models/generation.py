"""
Generation related models
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Float, Enum, Boolean
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class GenerationStatus(enum.Enum):
    """생성 상태"""
    PENDING = "pending"
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GenerationJob(BaseModel):
    """이미지 생성 작업 모델"""

    __tablename__ = "generation_jobs"

    # 기본 정보
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        comment="프로젝트 ID"
    )

    concept_id = Column(
        Integer,
        ForeignKey("design_concepts.id"),
        nullable=True,
        index=True,
        comment="디자인 컨셉 ID"
    )

    job_name = Column(
        String(200),
        nullable=False,
        comment="작업 이름"
    )

    # 상태
    status = Column(
        Enum(GenerationStatus),
        nullable=False,
        default=GenerationStatus.PENDING,
        comment="생성 상태"
    )

    progress_percent = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="진행률 (0-100)"
    )

    # 생성 설정
    model_used = Column(
        String(50),
        nullable=False,
        comment="사용된 생성 모델"
    )

    generation_type = Column(
        String(50),
        nullable=False,
        comment="생성 타입 (garment, model_fitting, blueprint)"
    )

    prompt_spec_id = Column(
        Integer,
        ForeignKey("prompt_specs.id"),
        nullable=True,
        comment="프롬프트 스펙 ID"
    )

    # 파라미터
    parameters = Column(
        Text,
        nullable=True,
        comment="생성 파라미터 (JSON)"
    )

    # 결과
    total_images_generated = Column(
        Integer,
        default=0,
        nullable=False,
        comment="생성된 이미지 수"
    )

    successful_generations = Column(
        Integer,
        default=0,
        nullable=False,
        comment="성공적인 생성 수"
    )

    failed_generations = Column(
        Integer,
        default=0,
        nullable=False,
        comment="실패한 생성 수"
    )

    # 품질 평가
    average_quality_score = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="평균 품질 점수 (0-1)"
    )

    average_consistency_score = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="평균 일관성 점수 (0-1)"
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
        back_populates="generation_jobs"
    )

    concept = relationship(
        "DesignConcept"
    )

    prompt_spec = relationship(
        "PromptSpec"
    )

    image_assets = relationship(
        "ImageAsset",
        back_populates="generation_job",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GenerationJob(id={self.id}, model='{self.model_used}', status='{self.status.value}')>"

    def start(self) -> None:
        """생성 시작"""
        self.status = GenerationStatus.GENERATING
        self.started_at = datetime.utcnow()
        self.progress_percent = 0.0

    def update_progress(self, percent: float) -> None:
        """진행률 업데이트"""
        self.progress_percent = max(0.0, min(100.0, percent))

    def complete(self) -> None:
        """생성 완료"""
        self.status = GenerationStatus.COMPLETED
        self.progress_percent = 100.0
        self.completed_at = datetime.utcnow()

    def fail(self, error_message: str) -> None:
        """생성 실패"""
        self.status = GenerationStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()


class ImageAsset(BaseModel):
    """이미지 에셋 모델"""

    __tablename__ = "image_assets"

    # 기본 정보
    generation_job_id = Column(
        Integer,
        ForeignKey("generation_jobs.id"),
        nullable=False,
        index=True,
        comment="생성 작업 ID"
    )

    file_name = Column(
        String(500),
        nullable=False,
        comment="파일 이름"
    )

    file_path = Column(
        String(1000),
        nullable=False,
        comment="파일 경로"
    )

    file_url = Column(
        String(1000),
        nullable=True,
        comment="파일 URL"
    )

    # 이미지 정보
    image_type = Column(
        String(50),
        nullable=False,
        comment="이미지 타입 (garment_front, garment_back, model_fitting, blueprint)"
    )

    width = Column(
        Integer,
        nullable=False,
        comment="이미지 너비"
    )

    height = Column(
        Integer,
        nullable=False,
        comment="이미지 높이"
    )

    file_size_bytes = Column(
        Integer,
        nullable=False,
        comment="파일 크기 (bytes)"
    )

    format = Column(
        String(10),
        nullable=False,
        comment="파일 포맷"
    )

    # 생성 정보
    prompt_used = Column(
        Text,
        nullable=True,
        comment="사용된 프롬프트"
    )

    seed = Column(
        Integer,
        nullable=True,
        comment="생성 시드"
    )

    # 평가
    quality_score = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="품질 점수 (0-1)"
    )

    consistency_score = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="일관성 점수 (0-1)"
    )

    prompt_fidelity = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="프롬프트 충실도 (0-1)"
    )

    # 검증
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="검증 완료 여부"
    )

    verification_notes = Column(
        Text,
        nullable=True,
        comment="검증 노트"
    )

    # 상태
    is_selected = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="최종 선택 여부"
    )

    # 관계
    generation_job = relationship(
        "GenerationJob",
        back_populates="image_assets"
    )

    def __repr__(self) -> str:
        return f"<ImageAsset(id={self.id}, type='{self.image_type}', quality={self.quality_score})>"


class PatternDraft(BaseModel):
    """패턴 초안 모델"""

    __tablename__ = "pattern_drafts"

    # 기본 정보
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        comment="프로젝트 ID"
    )

    concept_id = Column(
        Integer,
        ForeignKey("design_concepts.id"),
        nullable=True,
        index=True,
        comment="디자인 컨셉 ID"
    )

    generation_job_id = Column(
        Integer,
        ForeignKey("generation_jobs.id"),
        nullable=True,
        index=True,
        comment="생성 작업 ID"
    )

    draft_name = Column(
        String(200),
        nullable=False,
        comment="초안 이름"
    )

    # 치수 정보
    size_standard = Column(
        String(10),
        nullable=False,
        comment="치수 표준"
    )

    size_label = Column(
        String(20),
        nullable=False,
        comment="사이즈 라벨"
    )

    measurements = Column(
        Text,
        nullable=True,
        comment="치수 정보 (JSON)"
    )

    # 파일 정보
    front_pattern_url = Column(
        String(1000),
        nullable=True,
        comment="앞면 패턴 URL"
    )

    back_pattern_url = Column(
        String(1000),
        nullable=True,
        comment="뒤면 패턴 URL"
    )

    combined_pattern_url = Column(
        String(1000),
        nullable=True,
        comment="통합 패턴 URL"
    )

    format = Column(
        String(10),
        nullable=False,
        comment="파일 포맷 (svg, pdf, png)"
    )

    # 생성 정보
    generation_notes = Column(
        Text,
        nullable=True,
        comment="생성 노트"
    )

    # 상태
    is_standardized = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="표준화 여부"
    )

    def __repr__(self) -> str:
        return f"<PatternDraft(id={self.id}, name='{self.draft_name}', size='{self.size_label}')>"