"""
유튜브 채널 관리 모델
- 등록된 채널 목록 저장
- 채널별 크롤링 이력 관리
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.sql import func
from .base import Base, TimestampMixin


class YoutubeChannel(Base, TimestampMixin):
    """유튜브 채널 등록 정보"""
    __tablename__ = "youtube_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 채널 기본 정보
    channel_id = Column(String(100), unique=True, index=True, nullable=False)
    channel_handle = Column(String(100), nullable=True)  # @handle 형식
    channel_name = Column(String(200), nullable=False)
    channel_url = Column(String(500), nullable=True)

    # 채널 메타 정보
    description = Column(Text, nullable=True)
    subscriber_count = Column(Integer, nullable=True)
    video_count = Column(Integer, nullable=True)

    # 관리 정보
    is_active = Column(Boolean, default=True, nullable=False)
    category = Column(String(50), nullable=True)  # 패션, 뷰티 등
    memo = Column(Text, nullable=True)

    # 크롤링 이력
    last_crawled_at = Column(DateTime(timezone=True), nullable=True)
    total_videos_crawled = Column(Integer, default=0)
    total_comments_crawled = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "channel_handle": self.channel_handle,
            "channel_name": self.channel_name,
            "channel_url": self.channel_url,
            "description": self.description,
            "category": self.category,
            "memo": self.memo,
            "is_active": self.is_active,
            "last_crawled_at": self.last_crawled_at.isoformat() if self.last_crawled_at else None,
            "total_videos_crawled": self.total_videos_crawled,
            "total_comments_crawled": self.total_comments_crawled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
