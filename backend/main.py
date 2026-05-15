"""拾忆 - AI驱动记忆修复叙事游戏 · 后端主入口"""
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.database import init_db
from backend.api.dialogue import router as dialogue_router
from backend.api.scene import router as scene_router
from backend.api.save import router as save_router
from backend.config import settings


# ── 日志配置 ──
logger.remove()
logger.add(
    sys.stderr,
    level=settings.LOG_LEVEL,
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}",
)

# ── 速率限制 ──
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("正在初始化数据库...")
    init_db()
    logger.info("拾忆 · 后端启动完成 (log_level={})", settings.LOG_LEVEL)
    yield
    logger.info("拾忆 · 后端已关闭")


app = FastAPI(
    title="拾忆 - AI叙事游戏",
    description="AI驱动的记忆修复叙事游戏后端",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda req, exc: JSONResponse(
    status_code=429,
    content={"error": "请求过于频繁，请稍后再试", "retry_after": exc.detail},
))

# ── CORS（生产环境收紧）──
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(dialogue_router)
app.include_router(scene_router)
app.include_router(save_router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "game": "拾忆",
        "has_ai_key": bool(settings.DEEPSEEK_API_KEY and "your_" not in settings.DEEPSEEK_API_KEY),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=True)
