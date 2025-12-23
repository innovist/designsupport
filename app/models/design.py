"""
Design related models
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Float, Enum, Boolean
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class DesignConcept(BaseModel):
    """디자인 컨셉 모델"""

    __tablename__ = "design_concepts"

    # 기본 정보
    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
        comment="프로젝트 ID"
    )

    concept_name = Column(
        String(200),
        nullable=False,
        comment="컨셉 이름"
    )

    concept_number = Column(
        Integer,
        nullable=False,
        comment="컨셉 번호 (1, 2, 3)"
    )

    # 컨셉 상세
    target_audience = Column(
        Text,
        nullable=True,
        comment="타겟 고객"
    )

    season = Column(
        String(50),
        nullable=True,
        comment="시즌"
    )

    silhouette = Column(
        Text,
        nullable=True,
        comment="실루엣"
    )

    materials = Column(
        Text,
        nullable=True,
        comment="주요 소재 (JSON)"
    )

    color_palette = Column(
        Text,
        nullable=True,
        comment="색상 팔레트 (JSON)"
    )

    key_features = Column(
        Text,
        nullable=True,
        comment="주요 특징 (JSON)"
    )

    details = Column(
        Text,
        nullable=True,
        comment="디테일 설명"
    )

    # 근거
    rationale = Column(
        Text,
        nullable=True,
        comment="컨셉 근거"
    )

    supporting_data = Column(
        Text,
        nullable=True,
        comment="뒷받침 데이터 (JSON)"
    )

    source_ids = Column(
        Text,
        nullable=True,
        comment="관련 소스 ID 목록 (JSON)"
    )

    # 평가
    feasibility_score = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="실현 가능성 점수 (0-1)"
    )

    market_potential = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="시장성 점수 (0-1)"
    )

    innovation_score = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="혁신성 점수 (0-1)"
    )

    # 상태
    is_selected = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="선택된 컨셉 여부"
    )

    # 관계
    project = relationship(
        "Project",
        back_populates="design_concepts"
    )

    prompt_specs = relationship(
        "PromptSpec",
        back_populates="concept",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DesignConcept(id={self.id}, name='{self.concept_name}', number={self.concept_number})>"


class PromptSpec(BaseModel):
    """프롬프트 스펙 모델"""

    __tablename__ = "prompt_specs"

    # 기본 정보
    concept_id = Column(
        Integer,
        ForeignKey("design_concepts.id"),
        nullable=False,
        index=True,
        comment="디자인 컨셉 ID"
    )

    prompt_type = Column(
        String(50),
        nullable=False,
        comment="프롬프트 타입 (garment, model_fitting, blueprint)"
    )

    model_name = Column(
        String(50),
        nullable=True,
        comment="타겟 생성 모델"
    )

    # 프롬프트 내용
    base_prompt = Column(
        Text,
        nullable=False,
        comment="기본 프롬프트"
    )

    optimized_prompt = Column(
        Text,
        nullable=True,
        comment="최적화된 프롬프트"
    )

    negative_prompt = Column(
        Text,
        nullable=True,
        comment="네거티브 프롬프트"
    )

    # 언어
    original_language = Column(
        String(10),
        default="ko",
        nullable=False,
        comment="원본 언어"
    )

    translated_prompt = Column(
        Text,
        nullable=True,
        comment="번역된 프롬프트 (영어)"
    )

    # 파라미터
    width = Column(
        Integer,
        nullable=True,
        comment="이미지 너비"
    )

    height = Column(
        Integer,
        nullable=True,
        comment="이미지 높이"
    )

    steps = Column(
        Integer,
        nullable=True,
        comment="생성 단계 수"
    )

    cfg_scale = Column(
        Float,
        nullable=True,
        comment="CFG 스케일"
    )

    seed = Column(
        Integer,
        nullable=True,
        comment="시드 값"
    )

    # 참조 이미지
    reference_image_url = Column(
        String(1000),
        nullable=True,
        comment="참조 이미지 URL"
    )

    reference_strength = Column(
        Float,
        default=0.8,
        nullable=False,
        comment="참조 이미지 강도 (0-1)"
    )

    controlnet_type = Column(
        String(50),
        nullable=True,
        comment="ControlNet 타입"
    )

    # 관계
    concept = relationship(
        "DesignConcept",
        back_populates="prompt_specs"
    )

    def __repr__(self) -> str:
        return f"<PromptSpec(id={self.id}, type='{self.prompt_type}', model='{self.model_name}')>"