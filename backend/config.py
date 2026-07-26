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
    CORS_ORIGINS: str = "*"
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


settings = Settings()
