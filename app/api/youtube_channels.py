"""유튜브 채널 관리 API 라우터"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.youtube_channel import YoutubeChannel

router = APIRouter()


# ========== Request/Response 스키마 ==========

class ChannelCreate(BaseModel):
    """채널 등록 요청"""
    channel_id: str
    channel_handle: Optional[str] = None
    channel_name: str
    channel_url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    memo: Optional[str] = None


class ChannelUpdate(BaseModel):
    """채널 수정 요청"""
    channel_name: Optional[str] = None
    channel_handle: Optional[str] = None
    channel_url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    memo: Optional[str] = None
    is_active: Optional[bool] = None


class ChannelRead(BaseModel):
    """채널 응답"""
    id: int
    channel_id: str
    channel_handle: Optional[str]
    channel_name: str
    channel_url: Optional[str]
    description: Optional[str]
    category: Optional[str]
    memo: Optional[str]
    is_active: bool
    last_crawled_at: Optional[datetime]
    total_videos_crawled: int
    total_comments_crawled: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ========== API 엔드포인트 ==========

@router.get("/", response_model=List[ChannelRead])
async def list_channels(
    active_only: bool = False,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """등록된 유튜브 채널 목록 조회"""
    query = db.query(YoutubeChannel)

    if active_only:
        query = query.filter(YoutubeChannel.is_active == True)

    if category:
        query = query.filter(YoutubeChannel.category == category)

    channels = query.order_by(YoutubeChannel.created_at.desc()).all()
    return channels


@router.get("/{channel_db_id}", response_model=ChannelRead)
async def get_channel(channel_db_id: int, db: Session = Depends(get_db)):
    """특정 채널 조회 (DB ID)"""
    channel = db.query(YoutubeChannel).filter(YoutubeChannel.id == channel_db_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다")
    return channel


@router.post("/", response_model=ChannelRead)
async def create_channel(data: ChannelCreate, db: Session = Depends(get_db)):
    """새 유튜브 채널 등록"""
    # 중복 체크
    existing = db.query(YoutubeChannel).filter(
        YoutubeChannel.channel_id == data.channel_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail=f"이미 등록된 채널입니다: {data.channel_id}")

    channel = YoutubeChannel(
        channel_id=data.channel_id,
        channel_handle=data.channel_handle,
        channel_name=data.channel_name,
        channel_url=data.channel_url,
        description=data.description,
        category=data.category,
        memo=data.memo
    )

    db.add(channel)
    db.commit()
    db.refresh(channel)

    return channel


@router.patch("/{channel_db_id}", response_model=ChannelRead)
async def update_channel(
    channel_db_id: int,
    data: ChannelUpdate,
    db: Session = Depends(get_db)
):
    """채널 정보 수정"""
    channel = db.query(YoutubeChannel).filter(YoutubeChannel.id == channel_db_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(channel, key, value)

    db.commit()
    db.refresh(channel)

    return channel


@router.delete("/{channel_db_id}")
async def delete_channel(channel_db_id: int, db: Session = Depends(get_db)):
    """채널 삭제"""
    channel = db.query(YoutubeChannel).filter(YoutubeChannel.id == channel_db_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다")

    channel_name = channel.channel_name
    db.delete(channel)
    db.commit()

    return {"message": f"채널이 삭제되었습니다: {channel_name}"}


@router.post("/{channel_db_id}/toggle-active")
async def toggle_channel_active(channel_db_id: int, db: Session = Depends(get_db)):
    """채널 활성/비활성 토글"""
    channel = db.query(YoutubeChannel).filter(YoutubeChannel.id == channel_db_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="채널을 찾을 수 없습니다")

    channel.is_active = not channel.is_active
    db.commit()
    db.refresh(channel)

    status = "활성화" if channel.is_active else "비활성화"
    return {"message": f"채널이 {status}되었습니다", "is_active": channel.is_active}
