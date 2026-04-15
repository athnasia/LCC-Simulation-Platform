"""
系统级数据字典 ORM 模型

包含：
  - SysDictType 数据字典类型表
  - SysDictItem 数据字典项表

设计目标：
  - 数据库存储原始值（如 STRING / MATERIAL / BASE）
  - 展示标签使用可配置中文 label
  - 通过系统管理模块维护，供前端统一缓存消费
"""

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base


class SysDictType(AuditMixin, Base):
    __tablename__ = "sys_dict_type"
    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uq_sys_dict_type_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="字典类型名称")
    code: Mapped[str] = mapped_column(String(64), nullable=False, comment="字典类型编码")
    description: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="字典类型描述")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序值，升序")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", nullable=False, comment="是否启用"
    )

    items: Mapped[list["SysDictItem"]] = relationship(
        "SysDictItem",
        back_populates="dict_type",
        cascade="all, delete-orphan",
        order_by="SysDictItem.sort_order, SysDictItem.id",
    )


class SysDictItem(AuditMixin, Base):
    __tablename__ = "sys_dict_item"
    __table_args__ = (
        UniqueConstraint("dict_type_id", "value", "is_deleted", name="uq_sys_dict_item_type_value_deleted"),
    )

    dict_type_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sys_dict_type.id"), nullable=False, comment="所属字典类型 ID"
    )
    value: Mapped[str] = mapped_column(String(100), nullable=False, comment="存储值，保持原始枚举或编码")
    label: Mapped[str] = mapped_column(String(100), nullable=False, comment="展示标签")
    description: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="字典项描述")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序值，升序")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", nullable=False, comment="是否启用"
    )
    extra_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="扩展元数据")

    dict_type: Mapped["SysDictType"] = relationship("SysDictType", back_populates="items")