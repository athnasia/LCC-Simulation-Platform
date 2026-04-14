"""
SQLAlchemy ORM 基础层

提供：
  - Base：所有 ORM 模型的声明基类
  - AuditMixin：通用审计字段（id、时间戳、操作人、逻辑删除）
  - 所有业务模型通过 `class MyModel(AuditMixin, Base)` 继承获得完整审计能力
"""

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, mapped_column


# ── 声明基类 ───────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """
    所有 ORM 模型共享的声明基类（SQLAlchemy 2.0 风格）。
    不包含任何业务字段，仅作为元数据注册中心。
    """
    pass


# ── 审计字段 Mixin ─────────────────────────────────────────────────────────────

class AuditMixin:
    """
    通用审计基类，所有核心业务表必须继承。

    字段说明：
        id          — 自增主键，BigInteger 为未来分库分表预留空间
        created_at  — 记录创建时间，由数据库服务端自动填充（server_default）
        updated_at  — 最后更新时间，每次 UPDATE 自动刷新（onupdate）
        created_by  — 创建人用户 ID（字符串，兼容后续 SSO/外部系统用户编码）
        updated_by  — 最后操作人用户 ID
        is_deleted  — 逻辑删除标志（True = 已删除），禁止物理删除核心业务数据

    查询约定：
        所有业务查询必须附加 `.filter(Model.is_deleted == False)` 条件。
        repositories/base.py 的通用 CRUD 基类已封装此过滤，勿在路由层手动拼接。
    """

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主键 ID",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="最后更新时间",
    )

    created_by: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="创建人用户 ID",
    )

    updated_by: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="最后操作人用户 ID",
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        nullable=False,
        index=True,           # 几乎所有查询都携带此过滤条件，建索引降低扫描量
        comment="逻辑删除标志（1=已删除）",
    )
