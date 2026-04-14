"""
全局配置管理

通过 pydantic-settings 从 .env 文件或环境变量中读取配置。
所有模块通过 `from app.core.config import settings` 获取单例。
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py 位于 backend/app/core/config.py，向上三层即 backend/
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",          # 忽略 .env 中多余的字段，避免启动报错
        case_sensitive=False,
    )

    # ── 应用基础 ────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"          # development | production
    APP_DEBUG: bool = True
    APP_VERSION: str = "0.1.0"

    # ── MySQL ───────────────────────────────────────────────────────────────────
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 33306
    DB_USER: str = "lcc_user"
    DB_PASSWORD: str = "lcc_password"
    DB_NAME: str = "lcc"
    DB_CHARSET: str = "utf8mb4"

    # 连接池（见 database.py）
    DB_POOL_SIZE: int = 20               # 常驻连接数，覆盖并发核算请求
    DB_MAX_OVERFLOW: int = 30            # 峰值时允许额外创建的连接数
    DB_POOL_TIMEOUT: int = 30            # 等待可用连接的超时秒数
    DB_POOL_RECYCLE: int = 3600          # 连接最长存活时间（防 MySQL wait_timeout 断连）

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset={self.DB_CHARSET}"
        )

    # ── Redis ───────────────────────────────────────────────────────────────────
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 63799
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    @property
    def REDIS_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ── Celery ──────────────────────────────────────────────────────────────────
    CELERY_BROKER_DB: int = 1            # 与业务 Redis DB 隔离
    CELERY_RESULT_DB: int = 2

    @property
    def CELERY_BROKER_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.CELERY_BROKER_DB}"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.CELERY_RESULT_DB}"

    # ── JWT 认证 ────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-this-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8    # 8 小时
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ────────────────────────────────────────────────────────────────────
    # .env 中使用 JSON 数组格式：CORS_ORIGINS=["http://localhost:5173"]
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # ── 文件存储 ────────────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./storage/uploads"
    REPORT_DIR: str = "./storage/reports"
    MAX_UPLOAD_SIZE_MB: int = 50


@lru_cache
def get_settings() -> Settings:
    """
    使用 lru_cache 保证全局单例，避免重复读取 .env 文件。
    测试时可通过 get_settings.cache_clear() 重置缓存以注入不同配置。
    """
    return Settings()


settings: Settings = get_settings()
