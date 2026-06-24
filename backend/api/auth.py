"""认证API"""
import hashlib
import time
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 会话token存储（内存级，重启清除）
_active_sessions: dict[str, dict] = {}


def _hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_token(user_id: int) -> str:
    """生成会话token"""
    raw = f"mh_{user_id}_{time.time()}"
    return hashlib.md5(raw.encode()).hexdigest()


class RegisterRequest(BaseModel):
    username: str
    password: str
    nickname: str = ""

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 20:
            raise ValueError('用户名长度需在3-20之间')
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('密码长度不能少于6')
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: int
    username: str
    nickname: str


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """注册新用户"""
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建用户
    user = User(
        username=req.username,
        password_hash=_hash_password(req.password),
        nickname=req.nickname or req.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 生成token
    token = _generate_token(user.id)
    _active_sessions[token] = {
        "user_id": user.id,
        "username": user.username,
        "created_at": time.time(),
    }

    return AuthResponse(
        token=token,
        user_id=user.id,
        username=user.username,
        nickname=user.nickname or user.username,
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or user.password_hash != _hash_password(req.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 更新最后登录时间
    user.last_login = func.now()
    db.commit()

    # 生成token
    token = _generate_token(user.id)
    _active_sessions[token] = {
        "user_id": user.id,
        "username": user.username,
        "created_at": time.time(),
    }

    return AuthResponse(
        token=token,
        user_id=user.id,
        username=user.username,
        nickname=user.nickname or user.username,
    )


@router.get("/me")
def get_current_user(token: str, db: Session = Depends(get_db)):
    """获取当前用户信息"""
    session = _active_sessions.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="未登录或token无效")

    user = db.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "user_id": user.id,
        "username": user.username,
        "nickname": user.nickname or user.username,
    }


@router.post("/logout")
def logout(token: str):
    """登出"""
    if token in _active_sessions:
        del _active_sessions[token]
    return {"status": "ok"}
