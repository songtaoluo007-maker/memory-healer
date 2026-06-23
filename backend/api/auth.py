"""认证API - 注册/登录/JWT"""
import hashlib
import time
import json
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

# JWT密钥（生产环境应从环境变量读取）
JWT_SECRET = "mh_secret_2024_xian"
JWT_EXPIRE = 86400 * 7  # 7天


def _hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(f"mh_{password}_salt".encode()).hexdigest()


def _generate_jwt(user_id: int, username: str) -> str:
    """简单JWT生成"""
    header = json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
    import base64
    h = base64.urlsafe_b64encode(header).rstrip(b"=").decode()
    payload = json.dumps({
        "user_id": user_id,
        "username": username,
        "exp": int(time.time()) + JWT_EXPIRE,
    }).encode()
    p = base64.urlsafe_b64encode(payload).rstrip(b"=").decode()
    sig_input = f"{h}.{p}.{JWT_SECRET}"
    sig = hashlib.sha256(sig_input.encode()).hexdigest()[:32]
    return f"{h}.{p}.{sig}"


def _verify_jwt(token: str) -> dict | None:
    """验证JWT，返回payload或None"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        import base64
        # 验证签名
        sig_input = f"{parts[0]}.{parts[1]}.{JWT_SECRET}"
        expected_sig = hashlib.sha256(sig_input.encode()).hexdigest()[:32]
        if parts[2] != expected_sig:
            return None
        # 解码payload
        padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User | None:
    """从Authorization header获取当前用户"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    payload = _verify_jwt(token)
    if not payload:
        return None
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    return user


def require_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    """要求登录"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization[7:]
    payload = _verify_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="登录已过期")
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


# ── 请求模型 ──

class RegisterRequest(BaseModel):
    username: str
    password: str
    nickname: str = ""

    @validator('username')
    def validate_username(cls, v):
        v = v.strip()
        if len(v) < 2 or len(v) > 20:
            raise ValueError('用户名长度2-20')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 4 or len(v) > 50:
            raise ValueError('密码长度4-50')
        return v

    @validator('nickname')
    def validate_nickname(cls, v):
        return v.strip()[:20] if v else ""


class LoginRequest(BaseModel):
    username: str
    password: str


class UpdateProfileRequest(BaseModel):
    nickname: str = ""
    avatar_url: str = ""


# ── 接口 ──

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """注册"""
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

    token = _generate_jwt(user.id, user.username)
    return {
        "success": True,
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "created_at": str(user.created_at),
        },
    }


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """登录"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or user.password_hash != _hash_password(req.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    from datetime import datetime, timezone
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = _generate_jwt(user.id, user.username)
    return {
        "success": True,
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "created_at": str(user.created_at),
            "last_login": str(user.last_login),
        },
    }


@router.get("/me")
def get_me(user: User = Depends(require_user)):
    """获取当前用户信息"""
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "created_at": str(user.created_at),
            "last_login": str(user.last_login),
        },
    }


@router.put("/profile")
def update_profile(req: UpdateProfileRequest, user: User = Depends(require_user), db: Session = Depends(get_db)):
    """更新用户资料"""
    if req.nickname:
        user.nickname = req.nickname[:20]
    if req.avatar_url:
        user.avatar_url = req.avatar_url[:200]
    db.commit()
    return {"success": True}
