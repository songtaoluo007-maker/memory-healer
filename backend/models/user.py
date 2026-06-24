"""用户模型"""
from sqlalchemy import Column, Integer, String, DateTime, func
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    nickname = Column(String(50), default="")
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)
