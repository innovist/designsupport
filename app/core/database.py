"""
SQLAlchemy engine, session factory, and FastAPI dependency for PostgreSQL.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables that do not yet exist."""
    from app.models.base import Base
    import app.models  # noqa: F401 - registers all ORM classes with metadata
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialised")


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for DB sessions used outside FastAPI (e.g. startup tasks)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# @MX:ANCHOR: [AUTO] Database session dependency for FastAPI endpoints
# @MX:REASON: High fan_in (62+ callers) - all API routes depend on this function

def get_db() -> Generator[Session, None, None]:
    """FastAPI Depends() provider for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
