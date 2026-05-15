"""拾忆 - AI驱动记忆修复叙事游戏 · 后端主入口"""
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.database import init_db
from backend.api.dialogue import router as dialogue_router
from backend.api.scene import router as scene_router
from backend.api.save import router as save_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("正在初始化数据库...")
    init_db()
    logger.info("拾忆 · 后端启动完成")
    yield
    logger.info("拾忆 · 后端已关闭")


app = FastAPI(
    title="拾忆 - AI叙事游戏",
    description="AI驱动的记忆修复叙事游戏后端",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dialogue_router)
app.include_router(scene_router)
app.include_router(save_router)


@app.get("/api/health")
def health():
    from backend.config import settings
    return {
        "status": "ok",
        "game": "拾忆",
        "has_ai_key": bool(settings.DEEPSEEK_API_KEY and "your_" not in settings.DEEPSEEK_API_KEY),
    }


if __name__ == "__main__":
    import uvicorn
    from backend.config import settings
    uvicorn.run("backend.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=True)
