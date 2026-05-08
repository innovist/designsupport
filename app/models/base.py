"""
Base database model with common fields
"""

from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Column, Integer, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func


Base = declarative_base()


class TimestampMixin:
    """타임스탬프 공통 믹스인"""

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성 시각"
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정 시각"
    )


class SoftDeleteMixin:
    """소프트 삭제 공통 믹스인"""

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="삭제 시각"
    )

    is_deleted = Column(
        Integer,
        default=0,
        nullable=False,
        comment="삭제 여부 (0: 활성, 1: 삭제)"
    )


class BaseModel(Base, TimestampMixin):
    """기본 모델 클래스"""

    __abstract__ = True

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="고유 ID"
    )

    metadata_json = Column(
        JSON,
        nullable=True,
        comment="추가 메타데이터"
    )

    notes = Column(
        Text,
        nullable=True,
        comment="비고"
    )

    # @MX:ANCHOR: [AUTO] Core model serialization method used across all API responses
    # @MX:REASON: Called from 10+ locations across the codebase as the primary model-to-dict converter
    def to_dict(self) -> Dict[str, Any]:
        """모델을 딕셔너리로 변환"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result

    def update_metadata(self, **kwargs) -> None:
        """메타데이터 업데이트"""
        if self.metadata_json is None:
            self.metadata_json = {}
        self.metadata_json.update(kwargs)

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """메타데이터 값 조회"""
        if self.metadata_json is None:
            return default
        return self.metadata_json.get(key, default)