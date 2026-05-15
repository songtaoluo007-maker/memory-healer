"""存档模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime, timezone
from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SaveSlot(Base):
    __tablename__ = "save_slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slot_id = Column(Integer, nullable=False, unique=True)  # 1-5
    slot_name = Column(String(100), default="")
    game_state = Column(Text, nullable=False)  # JSON
    scene_id = Column(String(50), default="")
    play_time = Column(Integer, default=0)  # seconds
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
