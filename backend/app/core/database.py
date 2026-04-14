"""
数据库基础设施

- 使用 SQLAlchemy 2.0 同步引擎 + pymysql 驱动
- 针对高并发 LCC 仿真场景配置连接池
- FastAPI 端点使用 `Depends(get_db)` 获取 Session（同步端点由 FastAPI 自动放入线程池）
- Celery Worker 直接调用 `SessionLocal` 上下文管理器
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# ── 引擎创建 ───────────────────────────────────────────────────────────────────
#
# 连接池参数说明（面向并发 LCC 仿真场景）：
#   pool_size=20        → 常驻连接数。并发仿真任务 + Web 请求不需要频繁创建连接。
#   max_overflow=30     → 峰值时最多再借用 30 个连接（总上限 50），超出则等待。
#   pool_timeout=30     → 等待可用连接的超时（秒），超时抛出 TimeoutError 而非无限阻塞。
#   pool_recycle=3600   → 连接存活上限 1 小时，避免 MySQL 默认 8h wait_timeout 断连。
#   pool_pre_ping=True  → 每次取连接时执行 SELECT 1 检查存活，静默替换失效连接。

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    echo=settings.APP_DEBUG,     # DEBUG 模式下打印 SQL，生产环境关闭
    future=True,                 # 强制使用 SQLAlchemy 2.0 风格
)


# ── 监听器：强制 pymysql 使用 utf8mb4 ─────────────────────────────────────────
@event.listens_for(engine, "connect")
def set_charset(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.close()


# ── Session 工厂 ───────────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,   # 避免 commit 后访问对象属性触发额外查询
)


# ── FastAPI 依赖注入 ───────────────────────────────────────────────────────────

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI 路由层依赖。
    使用方式：`db: Session = Depends(get_db)`

    注意：FastAPI 对同步生成器依赖会自动在线程池中运行，
          无需将端点声明为 async def 也能安全使用。
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── 启动预检 ───────────────────────────────────────────────────────────────────

async def init_db() -> None:
    """
    应用启动时验证数据库连通性（在 main.py lifespan 中调用）。
    仅做存活探测，不执行建表（建表由 Alembic migrate 负责）。
    """
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
