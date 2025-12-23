"""
Database engine and session management
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.base import Base

logger = get_logger(__name__)
settings = get_settings()


def _ensure_sqlite_path(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    db_path = database_url.replace("sqlite:///", "")
    if not db_path or db_path == ":memory:":
        return
    Path(db_path).expanduser().parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_path(settings.database_url)

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite:///") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables"""
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for DB sessions outside FastAPI dependencies"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for DB sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
