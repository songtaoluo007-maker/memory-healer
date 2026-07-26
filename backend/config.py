"""游戏配置"""

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"
    DEEPSEEK_CONNECT_TIMEOUT_SECONDS: float = Field(default=5, gt=0, le=30)
    DEEPSEEK_TOTAL_TIMEOUT_SECONDS: float = Field(default=30, gt=0, le=120)
    DEEPSEEK_MAX_RETRIES: int = Field(default=2, ge=0, le=5)
    DEEPSEEK_FAILURE_THRESHOLD: int = Field(default=5, ge=1, le=20)
    DEEPSEEK_COOLDOWN_SECONDS: float = Field(default=30, ge=1, le=300)
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = f"sqlite:///{(ROOT_DIR / 'data' / 'game.db').as_posix()}"
    CORS_ORIGINS: str = "http://127.0.0.1:5173,http://localhost:5173"
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production
    SESSION_COOKIE_NAME: str = "memory_session"
    SESSION_TTL_SECONDS: int = Field(default=2_592_000, ge=300, le=31_536_000)
    COOKIE_SECURE: bool = False
    TTS_CACHE_DIR: Path = ROOT_DIR / "data" / "tts_cache"
    TTS_MAX_TEXT_LENGTH: int = Field(default=500, ge=1, le=2_000)
    TTS_MAX_CONCURRENCY: int = Field(default=2, ge=1, le=16)
    TTS_MAX_CACHE_FILES: int = Field(default=500, ge=1, le=10_000)
    TTS_MAX_CACHE_BYTES: int = Field(
        default=256 * 1024 * 1024,
        ge=1024,
        le=10 * 1024 * 1024 * 1024,
    )

    @property
    def cors_origins_list(self) -> List[str]:
        origins = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        if "*" in origins:
            raise ValueError("CORS_ORIGINS cannot contain '*' when Cookie auth is enabled")
        return origins

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


settings = Settings()
