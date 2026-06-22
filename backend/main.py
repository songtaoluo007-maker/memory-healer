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
    description="""## 拾忆 · Memory Healer

AI驱动的记忆修复叙事游戏后端 API

### 功能特性
- 🎭 **NPC对话**: 与AI驱动的NPC进行深度对话
- 🦋 **蝴蝶效应**: 选择影响后续剧情发展
- 💾 **存档系统**: 多槽位存档/读档
- 🎬 **场景管理**: 5个时代场景切换
- 🧩 **碎片收集**: 17个记忆碎片探索

### 技术栈
- **后端**: FastAPI + SQLAlchemy + SQLite
- **AI**: DeepSeek API (可选)
- **前端**: Vue 3 + TypeScript + Vite
""",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "dialogue",
            "description": "NPC对话相关接口",
        },
        {
            "name": "scene",
            "description": "场景管理接口",
        },
        {
            "name": "save",
            "description": "存档系统接口",
        },
        {
            "name": "health",
            "description": "健康检查接口",
        },
    ],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda req, exc: JSONResponse(
    status_code=429,
    content={"error": "请求过于频繁，请稍后再试", "retry_after": exc.detail},
))

# ── CORS（从配置读取）──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


# ── 请求日志中间件 ──
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志（DEBUG模式）+ 静态资源缓存头 + 安全头"""
    if settings.DEBUG:
        logger.debug("{} {}", request.method, request.url.path)
    response = await call_next(request)
    # 静态资源缓存（7天）
    if request.url.path.startswith("/assets/"):
        response.headers["Cache-Control"] = "public, max-age=604800, immutable"
    # 安全响应头
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

app.include_router(dialogue_router)
app.include_router(scene_router)
app.include_router(save_router)


@app.get("/api/health", tags=["health"])
def health():
    """健康检查（含诊断信息）"""
    from backend.database import get_db
    from sqlalchemy import text
    
    db_ok = True
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    
    return {
        "status": "ok" if db_ok else "degraded",
        "game": "拾忆",
        "version": "1.0.0",
        "has_ai_key": bool(settings.DEEPSEEK_API_KEY and "your_" not in settings.DEEPSEEK_API_KEY),
        "database": "ok" if db_ok else "error",
        "debug": settings.DEBUG,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=True)
