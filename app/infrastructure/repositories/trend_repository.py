"""
Repository for TrendSource, TrendDocument, TrendInsight.
"""

from sqlalchemy.orm import Session

from app.models.trends import TrendDocument, TrendInsight, TrendSource


class TrendRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_document_by_hash(self, content_hash: str) -> TrendDocument | None:
        return self.db.query(TrendDocument).filter_by(content_hash=content_hash).first()

    def list_active_sources(self) -> list[TrendSource]:
        return self.db.query(TrendSource).filter_by(is_active=True).all()

    def create_source(self, name: str, url: str | None = None, domain: str | None = None) -> TrendSource:
        source = TrendSource(name=name, url=url, domain=domain)
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def list_all_sources(self) -> list[TrendSource]:
        return self.db.query(TrendSource).order_by(TrendSource.created_at.desc()).all()
