"""
主数据域 ORM 模型

包含：
  - MdUnitDimension      量纲定义表（长度、质量、体积、时间、能耗、力、压强、货币）
  - MdUnit               单位表（mm、m、kg、t、h、kwh、CNY等）
  - MdUnitConversion     单位换算表（同量纲单位间的换算关系）
  - MdResourceCategory   资源分类表（材料、设备、人员、工具的树形分类）
  - MdAttrDefinition     属性定义表（材料/设备的动态属性定义）
"""

import enum
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base


class ResourceType(str, enum.Enum):
    MATERIAL = "MATERIAL"
    EQUIPMENT = "EQUIPMENT"
    LABOR = "LABOR"
    TOOL = "TOOL"


class DataType(str, enum.Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"
    DATE = "DATE"
    ENUM = "ENUM"


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
        BigInteger, ForeignKey("md_unit_dimension.id"), nullable=False, comment="所属量纲 ID"
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
        BigInteger, ForeignKey("md_unit.id"), nullable=False, comment="源单位 ID"
    )
    to_unit_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("md_unit.id"), nullable=False, comment="目标单位 ID"
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


# ── 资源分类（树形结构）────────────────────────────────────────────────────────

class MdResourceCategory(AuditMixin, Base):
    __tablename__ = "md_resource_category"
    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uq_md_resource_category_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="分类名称")
    code: Mapped[str] = mapped_column(String(30), nullable=False, comment="分类编码")
    resource_type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType), nullable=False, comment="资源类型（MATERIAL/EQUIPMENT/LABOR/TOOL）"
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("md_resource_category.id"), nullable=True, comment="父分类 ID（自关联）"
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序值，升序")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用"
    )
    description: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="分类描述")

    parent: Mapped["MdResourceCategory | None"] = relationship(
        "MdResourceCategory", remote_side="MdResourceCategory.id", back_populates="children"
    )
    children: Mapped[list["MdResourceCategory"]] = relationship(
        "MdResourceCategory", back_populates="parent"
    )


# ── 属性定义（柔性建模）────────────────────────────────────────────────────────

class MdAttrDefinition(AuditMixin, Base):
    __tablename__ = "md_attr_definition"
    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uq_md_attr_definition_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="属性名称")
    code: Mapped[str] = mapped_column(String(30), nullable=False, comment="变量标识码（纯英文，供公式引擎解析）")
    data_type: Mapped[DataType] = mapped_column(
        Enum(DataType), nullable=False, comment="数据类型（STRING/NUMBER/BOOLEAN/JSON/DATE/ENUM）"
    )
    unit_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("md_unit.id"), nullable=True, comment="关联单位 ID（可为空）"
    )
    applicable_resource_types: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="适用资源类型（JSON 数组，如：[\"MATERIAL\", \"EQUIPMENT\"]）"
    )
    description: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="属性描述")
    is_required: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否必填"
    )
    default_value: Mapped[str | None] = mapped_column(Text, nullable=True, comment="默认值")
    enum_values: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="枚举值列表（JSON 数组，如：[\"镀锌\", \"喷塑\", \"发黑\"]）"
    )

    unit: Mapped["MdUnit | None"] = relationship("MdUnit")
