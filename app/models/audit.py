"""
Audit log model
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class ActionType(enum.Enum):
    """작업 타입"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    DOWNLOAD = "download"
    LOGIN = "login"
    LOGOUT = "logout"
    GENERATE = "generate"
    CRAWL = "crawl"
    ANALYZE = "analyze"


class ResourceType(enum.Enum):
    """리소스 타입"""
    PROJECT = "project"
    SESSION = "session"
    VERSION = "version"
    CRAWL_JOB = "crawl_job"
    RAW_DATA = "raw_data"
    TREND_ANALYSIS = "trend_analysis"
    DESIGN_CONCEPT = "design_concept"
    PROMPT_SPEC = "prompt_spec"
    GENERATION_JOB = "generation_job"
    IMAGE_ASSET = "image_asset"
    PATTERN_DRAFT = "pattern_draft"
    REPORT = "report"
    USER = "user"
    API_KEY = "api_key"


class LogLevel(enum.Enum):
    """로그 레벨"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(BaseModel):
    """감사 로그 모델"""

    __tablename__ = "audit_logs"

    # 기본 정보
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="사용자 ID"
    )

    session_id = Column(
        String(200),
        nullable=True,
        index=True,
        comment="세션 ID"
    )

    ip_address = Column(
        String(45),
        nullable=True,
        comment="IP 주소"
    )

    user_agent = Column(
        String(500),
        nullable=True,
        comment="User Agent"
    )

    # 작업 정보
    action_type = Column(
        Enum(ActionType),
        nullable=False,
        comment="작업 타입"
    )

    resource_type = Column(
        Enum(ResourceType),
        nullable=False,
        comment="리소스 타입"
    )

    resource_id = Column(
        Integer,
        nullable=True,
        comment="리소스 ID"
    )

    resource_name = Column(
        String(200),
        nullable=True,
        comment="리소스 이름"
    )

    # 상세 정보
    description = Column(
        Text,
        nullable=True,
        comment="작업 설명"
    )

    details = Column(
        Text,
        nullable=True,
        comment="상세 정보 (JSON)"
    )

    old_values = Column(
        Text,
        nullable=True,
        comment="이전 값 (JSON)"
    )

    new_values = Column(
        Text,
        nullable=True,
        comment="새 값 (JSON)"
    )

    # 로그 레벨
    log_level = Column(
        Enum(LogLevel),
        nullable=False,
        default=LogLevel.INFO,
        comment="로그 레벨"
    )

    # 결과
    success = Column(
        Integer,
        default=1,
        nullable=False,
        comment="성공 여부 (0: 실패, 1: 성공)"
    )

    error_message = Column(
        Text,
        nullable=True,
        comment="에러 메시지"
    )

    # 성능 정보
    duration_ms = Column(
        Integer,
        nullable=True,
        comment="처리 시간 (밀리초)"
    )

    # API 관련
    endpoint = Column(
        String(200),
        nullable=True,
        comment="API 엔드포인트"
    )

    method = Column(
        String(10),
        nullable=True,
        comment="HTTP 메서드"
    )

    status_code = Column(
        Integer,
        nullable=True,
        comment="HTTP 상태 코드"
    )

    # 추가 컨텍스트
    project_id = Column(
        Integer,
        nullable=True,
        index=True,
        comment="관련 프로젝트 ID"
    )

    organization_id = Column(
        Integer,
        nullable=True,
        comment="조직 ID"
    )

    tags = Column(
        Text,
        nullable=True,
        comment="태그 (JSON)"
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action_type.value}', resource='{self.resource_type.value}')>"

    def to_dict(self) -> dict:
        """감사 로그를 딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "action_type": self.action_type.value,
            "resource_type": self.resource_type.value,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "description": self.description,
            "success": bool(self.success),
            "duration_ms": self.duration_ms,
            "ip_address": self.ip_address,
        }