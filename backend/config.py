"""游戏配置"""

from pathlib import Path
from typing import List

from pydantic import Field, model_validator
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
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = f"sqlite:///{(ROOT_DIR / 'data' / 'game.db').as_posix()}"
    CORS_ORIGINS: str = "http://127.0.0.1:5173,http://localhost:5173"
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production
    SESSION_COOKIE_NAME: str = "memory_session"
    SESSION_TTL_SECONDS: int = Field(default=2_592_000, ge=300, le=31_536_000)
    COOKIE_SECURE: bool | None = None
    TTS_CACHE_DIR: Path = ROOT_DIR / "data" / "tts_cache"
    TTS_MAX_TEXT_LENGTH: int = Field(default=500, ge=1, le=2_000)
    TTS_MAX_CONCURRENCY: int = Field(default=2, ge=1, le=16)
    TTS_MAX_CACHE_FILES: int = Field(default=500, ge=1, le=10_000)
    TTS_MAX_CACHE_BYTES: int = Field(
        default=256 * 1024 * 1024,
        ge=1024,
        le=10 * 1024 * 1024 * 1024,
    )
    VOICE_PUBLIC_DIR: Path = ROOT_DIR / "data" / "voice_public"
    VOICE_SEED_DIR: Path = ROOT_DIR / "data" / "voice_seeds"
    VOICE_PRIMARY_ENABLED: bool = False
    VOICE_GENERATION_MAX_CONCURRENCY: int = Field(default=1, ge=1, le=4)
    VOICE_CACHE_MAX_FILES: int = Field(default=500, ge=1, le=10000)
    VOICE_CACHE_MAX_BYTES: int = Field(default=2_147_483_648, ge=1_048_576)
    COSYVOICE_BASE_URL: str = "http://127.0.0.1:50000"
    COSYVOICE_BRIDGE_TOKEN: str = ""
    COSYVOICE_CONNECT_TIMEOUT_SECONDS: float = Field(default=0.5, ge=0.1, le=10)
    COSYVOICE_TOTAL_TIMEOUT_SECONDS: float = Field(default=2.5, ge=0.5, le=30)
    COSYVOICE_FAILURE_THRESHOLD: int = Field(default=3, ge=1, le=20)
    COSYVOICE_COOLDOWN_SECONDS: float = Field(default=30, ge=1, le=600)
    COSYVOICE_MODEL_REVISION: str = "Fun-CosyVoice3-0.5B-2512"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cookie_secure(self) -> bool:
        if self.COOKIE_SECURE is not None:
            return self.COOKIE_SECURE
        return self.is_production

    @model_validator(mode="after")
    def validate_cookie_transport(self) -> "Settings":
        if "*" in self.cors_origins_list:
            raise ValueError(
                "CORS_ORIGINS cannot contain '*' when Cookie authentication is enabled"
            )
        if self.is_production and not self.cors_origins_list:
            raise ValueError("CORS_ORIGINS must be explicit in production")
        return self

    @model_validator(mode="after")
    def create_voice_directories(self) -> "Settings":
        (self.VOICE_PUBLIC_DIR / "cache").mkdir(parents=True, exist_ok=True)
        (self.VOICE_PUBLIC_DIR / "fixed").mkdir(parents=True, exist_ok=True)
        self.VOICE_SEED_DIR.mkdir(parents=True, exist_ok=True)
        return self


settings = Settings()
