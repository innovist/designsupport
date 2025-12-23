"""
Size standard models
"""

from sqlalchemy import Column, String, Integer, Text, Float, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class SizeStandard(BaseModel):
    """치수 표준 모델"""

    __tablename__ = "size_standards"

    # 기본 정보
    standard_name = Column(
        String(10),
        nullable=False,
        unique=True,
        comment="표준 이름 (KS, GB, ASTM, ISO)"
    )

    standard_title = Column(
        String(200),
        nullable=False,
        comment="표준 제목"
    )

    description = Column(
        Text,
        nullable=True,
        comment="표준 설명"
    )

    country = Column(
        String(50),
        nullable=False,
        comment="국가/지역"
    )

    # 버전
    version = Column(
        String(50),
        nullable=True,
        comment="표준 버전"
    )

    # 단위
    measurement_unit = Column(
        String(10),
        default="cm",
        nullable=False,
        comment="측정 단위"
    )

    # 상태
    is_active = Column(
        Integer,
        default=1,
        nullable=False,
        comment="활성 상태 (0: 비활성, 1: 활성)"
    )

    # 관계
    size_tables = relationship(
        "SizeTable",
        back_populates="standard",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SizeStandard(id={self.id}, name='{self.standard_name}', country='{self.country}')>"


class Gender(enum.Enum):
    """성별"""
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"
    CHILDREN = "children"


class SizeTable(BaseModel):
    """치수표 모델"""

    __tablename__ = "size_tables"

    # 기본 정보
    standard_id = Column(
        Integer,
        ForeignKey("size_standards.id"),
        nullable=False,
        index=True,
        comment="표준 ID"
    )

    gender = Column(
        Enum(Gender),
        nullable=False,
        comment="성별"
    )

    age_group = Column(
        String(50),
        nullable=True,
        comment="연령대"
    )

    size_label = Column(
        String(20),
        nullable=False,
        comment="사이즈 라벨 (S, M, L, 90, 95 등)"
    )

    # 기본 치수
    height = Column(
        Float,
        nullable=True,
        comment="키"
    )

    weight = Column(
        Float,
        nullable=True,
        comment="몸무게"
    )

    # 상의 치수
    chest_girth = Column(
        Float,
        nullable=True,
        comment="가슴 둘레"
    )

    waist_girth = Column(
        Float,
        nullable=True,
        comment="허리 둘레"
    )

    hip_girth = Column(
        Float,
        nullable=True,
        comment="엉덩이 둘레"
    )

    shoulder_width = Column(
        Float,
        nullable=True,
        comment="어깨 너비"
    )

    sleeve_length = Column(
        Float,
        nullable=True,
        comment="소매 길이"
    )

    armhole_depth = Column(
        Float,
        nullable=True,
        comment="암홀 깊이"
    )

    back_length = Column(
        Float,
        nullable=True,
        comment="등 길이"
    )

    # 하의 치수
    waist_height = Column(
        Float,
        nullable=True,
        comment="허리 높이"
    )

    hip_height = Column(
        Float,
        nullable=True,
        comment="엉덩이 높이"
    )

    thigh_girth = Column(
        Float,
        nullable=True,
        comment="허벅지 둘레"
    )

    inseam_length = Column(
        Float,
        nullable=True,
        comment="인심 길이"
    )

    outseam_length = Column(
        Float,
        nullable=True,
        comment="아웃심 길이"
    )

    # 기타
    neck_girth = Column(
        Float,
        nullable=True,
        comment="목 둘레"
    )

    bust_girth = Column(
        Float,
        nullable=True,
        comment="가슴 둘레 (여성)"
    )

    underbust_girth = Column(
        Float,
        nullable=True,
        comment="밑가슴 둘레 (여성)"
    )

    # 추가 측정 지점
    additional_measurements = Column(
        Text,
        nullable=True,
        comment="추가 측정 지점 (JSON)"
    )

    # 주의사항
    notes = Column(
        Text,
        nullable=True,
        comment="주의사항"
    )

    # 관계
    standard = relationship(
        "SizeStandard",
        back_populates="size_tables"
    )

    def __repr__(self) -> str:
        return f"<SizeTable(id={self.id}, size='{self.size_label}', gender='{self.gender.value}')>"

    def to_dict(self) -> dict:
        """치수 정보를 딕셔너리로 변환"""
        return {
            "size_label": self.size_label,
            "height": self.height,
            "weight": self.weight,
            "chest_girth": self.chest_girth,
            "waist_girth": self.waist_girth,
            "hip_girth": self.hip_girth,
            "shoulder_width": self.shoulder_width,
            "sleeve_length": self.sleeve_length,
            "armhole_depth": self.armhole_depth,
            "back_length": self.back_length,
            "waist_height": self.waist_height,
            "hip_height": self.hip_height,
            "thigh_girth": self.thigh_girth,
            "inseam_length": self.inseam_length,
            "outseam_length": self.outseam_length,
            "neck_girth": self.neck_girth,
            "bust_girth": self.bust_girth,
            "underbust_girth": self.underbust_girth,
        }