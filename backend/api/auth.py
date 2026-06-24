"""认证API"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.models.token import Token

router = APIRouter(prefix="/api/auth", tags=["auth"])

TOKEN_EXPIRE_DAYS = 30  # token有效期30天


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_token() -> str:
    return secrets.token_hex(32)


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """鉴权依赖：从Authorization header解析token，返回User对象"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")

    token = authorization[7:]  # 去掉 "Bearer "
    token_row = db.query(Token).filter(Token.token == token).first()
    if not token_row:
        raise HTTPException(status_code=401, detail="token无效或已过期")

    # 检查过期
    if token_row.expires_at and token_row.expires_at < datetime.now(timezone.utc):
        db.delete(token_row)
        db.commit()
        raise HTTPException(status_code=401, detail="token已过期，请重新登录")

    user = db.query(User).filter(User.id == token_row.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return user


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


def _create_token(db: Session, user_id: int) -> str:
    """创建持久化token"""
    token = _generate_token()
    expires = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRE_DAYS)
    db.add(Token(token=token, user_id=user_id, expires_at=expires))
    db.commit()
    return token


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=req.username,
        password_hash=_hash_password(req.password),
        nickname=req.nickname or req.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = _create_token(db, user.id)

    return AuthResponse(
        token=token,
        user_id=user.id,
        username=user.username,
        nickname=user.nickname or user.username,
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or user.password_hash != _hash_password(req.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = _create_token(db, user.id)

    return AuthResponse(
        token=token,
        user_id=user.id,
        username=user.username,
        nickname=user.nickname or user.username,
    )


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "user_id": user.id,
        "username": user.username,
        "nickname": user.nickname or user.username,
    }


@router.post("/logout")
def logout(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        db.query(Token).filter(Token.token == token).delete()
        db.commit()
    return {"status": "ok"}
