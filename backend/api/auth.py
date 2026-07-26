"""Cookie-only authentication API."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.domain.errors import DomainError
from backend.persistence.models import User
from backend.persistence.repositories import SessionRepository
from backend.security import DUMMY_PASSWORD_HASH, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str
    nickname: str = ""

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()
        if not 3 <= len(value) <= 20:
            raise ValueError("用户名长度需在3-20之间")
        if not value.isalnum():
            raise ValueError("用户名只能包含字母和数字")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8 or len(value) > 128:
            raise ValueError("密码长度需在8-128之间")
        return value

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, value: str) -> str:
        value = value.strip()
        if len(value) > 50:
            raise ValueError("昵称长度不能超过50")
        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str


class AuthResponse(BaseModel):
    user_id: int
    username: str
    nickname: str


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(
        user_id=user.id,
        username=user.username,
        nickname=user.nickname or user.username,
    )


def _set_session_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=raw_token,
        max_age=settings.SESSION_TTL_SECONDS,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    raw_token = request.cookies.get(settings.SESSION_COOKIE_NAME, "")
    user = SessionRepository(db).resolve(raw_token)
    if user is None:
        raise DomainError("AUTH_REQUIRED", "请先登录")
    return user


@router.post("/register", response_model=AuthResponse)
def register(
    req: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        nickname=req.nickname or req.username,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DomainError("USERNAME_TAKEN", "用户名已存在") from exc
    db.refresh(user)

    raw_token, _session = SessionRepository(db).create(
        user.id,
        ttl_seconds=settings.SESSION_TTL_SECONDS,
    )
    _set_session_cookie(response, raw_token)
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
def login(
    req: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    user = db.scalar(select(User).where(User.username == req.username.strip()))
    password_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    if not verify_password(password_hash, req.password) or user is None:
        raise DomainError("INVALID_CREDENTIALS", "用户名或密码错误")

    user.last_login = datetime.now(timezone.utc)
    db.commit()
    raw_token, _session = SessionRepository(db).create(
        user.id,
        ttl_seconds=settings.SESSION_TTL_SECONDS,
    )
    _set_session_cookie(response, raw_token)
    return _auth_response(user)


@router.get("/me", response_model=AuthResponse)
def me(user: User = Depends(get_current_user)) -> AuthResponse:
    return _auth_response(user)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    raw_token = request.cookies.get(settings.SESSION_COOKIE_NAME, "")
    SessionRepository(db).revoke(raw_token)
    _clear_session_cookie(response)
    return {"status": "ok"}
