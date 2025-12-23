"""
User model
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class UserRole(enum.Enum):
    """사용자 역할"""
    ADMIN = "admin"
    DESIGNER = "designer"
    ANALYST = "analyst"
    VIEWER = "viewer"


class User(BaseModel):
    """사용자 모델"""

    __tablename__ = "users"

    # 기본 정보
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="이메일 (로그인 ID)"
    )

    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="사용자명"
    )

    password_hash = Column(
        String(255),
        nullable=False,
        comment="비밀번호 해시"
    )

    full_name = Column(
        String(100),
        nullable=True,
        comment="전체 이름"
    )

    # 상태
    role = Column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.DESIGNER,
        comment="사용자 역할"
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="활성 상태"
    )

    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="이메일 인증 여부"
    )

    # 설정
    language = Column(
        String(10),
        default="ko",
        nullable=False,
        comment="선호 언어"
    )

    size_standard = Column(
        String(10),
        default="KS",
        nullable=False,
        comment="선호 치수 표준"
    )

    timezone = Column(
        String(50),
        default="Asia/Seoul",
        nullable=False,
        comment="타임존"
    )

    # 제한
    api_quota_daily = Column(
        Integer,
        default=100,
        nullable=False,
        comment="일일 API 쿼터"
    )

    api_quota_monthly = Column(
        Integer,
        default=1000,
        nullable=False,
        comment="월간 API 쿼터"
    )

    # 타임스탬프
    last_login_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="마지막 로그인 시각"
    )

    password_changed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="비밀번호 변경 시각"
    )

    # 관계
    projects = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"

    @property
    def is_admin(self) -> bool:
        """관리자 여부"""
        return self.role == UserRole.ADMIN

    @property
    def display_name(self) -> str:
        """표시 이름"""
        return self.full_name or self.username

    def update_last_login(self) -> None:
        """마지막 로그인 시각 업데이트"""
        self.last_login_at = datetime.utcnow()

    def can_create_project(self) -> bool:
        """프로젝트 생성 가능 여부"""
        return self.is_active and self.is_verified

    def get_quota_remaining(self, used_daily: int, used_monthly: int) -> dict:
        """남은 쿼터 계산"""
        return {
            "daily_remaining": max(0, self.api_quota_daily - used_daily),
            "monthly_remaining": max(0, self.api_quota_monthly - used_monthly),
            "daily_usage_percent": min(100, (used_daily / self.api_quota_daily) * 100),
            "monthly_usage_percent": min(100, (used_monthly / self.api_quota_monthly) * 100)
        }