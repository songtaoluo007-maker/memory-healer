"""存档模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from backend.database import Base


class SaveSlot(Base):
    __tablename__ = "save_slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slot_id = Column(Integer, nullable=False, unique=True)  # 1-5
    slot_name = Column(String(100), default="")
    game_state = Column(Text, nullable=False)  # JSON
    scene_id = Column(String(50), default="")
    play_time = Column(Integer, default=0)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
