"""
主数据域 ORM 模型

包含：
  - MdUnitDimension      量纲定义表（长度、质量、体积、时间、能耗、力、压强、货币）
  - MdUnit               单位表（mm、m、kg、t、h、kwh、CNY等）
  - MdUnitConversion     单位换算表（同量纲单位间的换算关系）
"""

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base


# ── 量纲定义 ───────────────────────────────────────────────────────────────────

class MdUnitDimension(AuditMixin, Base):
    __tablename__ = "md_unit_dimension"
    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uq_md_unit_dimension_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="量纲名称（如：长度、质量）")
    code: Mapped[str] = mapped_column(String(30), nullable=False, comment="量纲编码（如：LENGTH, MASS）")
    description: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="量纲描述")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序值，升序")

    units: Mapped[list["MdUnit"]] = relationship("MdUnit", back_populates="dimension")


# ── 单位定义 ───────────────────────────────────────────────────────────────────

class MdUnit(AuditMixin, Base):
    __tablename__ = "md_unit"
    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uq_md_unit_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="单位名称（如：毫米、千克）")
    code: Mapped[str] = mapped_column(String(20), nullable=False, comment="单位编码（如：mm, kg）")
    symbol: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="单位符号（如：mm, kg）")
    dimension_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("md_unit_dimension.id"), nullable=False, comment="所属量纲 ID"
    )
    is_base: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否基础单位（如：米是长度的基础单位）"
    )
    description: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="单位描述")

    dimension: Mapped["MdUnitDimension"] = relationship("MdUnitDimension", back_populates="units")
    from_conversions: Mapped[list["MdUnitConversion"]] = relationship(
        "MdUnitConversion", foreign_keys="MdUnitConversion.from_unit_id", back_populates="from_unit"
    )
    to_conversions: Mapped[list["MdUnitConversion"]] = relationship(
        "MdUnitConversion", foreign_keys="MdUnitConversion.to_unit_id", back_populates="to_unit"
    )


# ── 单位换算 ───────────────────────────────────────────────────────────────────

class MdUnitConversion(AuditMixin, Base):
    __tablename__ = "md_unit_conversion"
    __table_args__ = (
        UniqueConstraint("from_unit_id", "to_unit_id", "is_deleted", name="uq_md_unit_conversion_pair_deleted"),
    )

    from_unit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("md_unit.id"), nullable=False, comment="源单位 ID"
    )
    to_unit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("md_unit.id"), nullable=False, comment="目标单位 ID"
    )
    conversion_factor: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), nullable=False, comment="换算因子（如：1吨 = 1000千克，因子为1000）"
    )
    offset: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 10), nullable=True, comment="偏移量（用于温度等非线性换算，保留字段）"
    )
    description: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="换算说明")

    from_unit: Mapped["MdUnit"] = relationship(
        "MdUnit", foreign_keys=[from_unit_id], back_populates="from_conversions"
    )
    to_unit: Mapped["MdUnit"] = relationship(
        "MdUnit", foreign_keys=[to_unit_id], back_populates="to_conversions"
    )
