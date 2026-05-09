"""
SQLAlchemy declarative base and common mixins.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, MappedColumn, mapped_column


class Base(DeclarativeBase):
    """Project-wide SQLAlchemy declarative base."""
    pass


class TimestampMixin:
    """Adds created_at / updated_at columns to any model."""

    # @MX:ANCHOR: [AUTO] TimestampMixin is used by all 17 ORM models
    # @MX:REASON: Any change to column defaults propagates across the entire schema

    created_at: MappedColumn[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: MappedColumn[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
