"""
Alembic 迁移环境配置

关键设计：
  1. 从 app.core.config.settings 动态读取 DATABASE_URL，
     无需在 alembic.ini 中硬编码连接字符串。
  2. 导入所有 ORM 模型，使 autogenerate 能感知到所有表结构变化。
"""

import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── 将 backend 目录加入 sys.path（保险措施）────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 加载项目配置（必须在 model 导入之前）──────────────────────────────────────
from app.core.config import settings  # noqa: E402

# ── 导入所有 ORM 模型，供 autogenerate 扫描 ────────────────────────────────────
# 每新增一个 models/*.py 文件，必须在此处 import，否则 autogenerate 不会感知
from app.models.base import Base      # noqa: E402
from app.models import system         # noqa: E402, F401

# 后续新增模型时，在此追加（示例）：
# from app.models import master_data   # noqa: F401
# from app.models import engineering   # noqa: F401
# from app.models import costing       # noqa: F401
# from app.models import simulation    # noqa: F401
# from app.models import iot           # noqa: F401

# ── Alembic 标准配置 ───────────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# autogenerate 扫描 Base 下注册的所有 metadata
target_metadata = Base.metadata

# 将 settings.DATABASE_URL 注入 alembic（覆盖 ini 中的空值）
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """离线模式：生成 SQL 脚本而不连接数据库。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式：连接数据库并直接执行迁移。"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
