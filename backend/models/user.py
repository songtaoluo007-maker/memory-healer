"""用户模型"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    password_hash = Column(String(128), nullable=False)
    nickname = Column(String(50), default="")
    avatar_url = Column(String(200), default="")
    created_at = Column(DateTime, default=_utcnow)
    last_login = Column(DateTime, default=_utcnow)
