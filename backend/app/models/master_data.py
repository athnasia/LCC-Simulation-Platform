"""
主数据域 ORM 模型

包含：
  - MdUnitDimension      量纲定义表（长度、质量、体积、时间、能耗、力、压强、货币）
  - MdUnit               单位表（mm、m、kg、t、h、kwh、CNY等）
  - MdUnitConversion     单位换算表（同量纲单位间的换算关系）
  - MdResourceCategory   资源分类表（材料、设备、人员、工具的树形分类）
  - MdAttrDefinition     属性定义表（材料/设备的动态属性定义）
  - MdMaterial           材料主数据表（柔性建模）
  - MdEquipment          设备主数据表（数字孪生）
  - MdProcess            标准工艺/工时库
  - MdProcessResource    工艺资源挂载包（多对多容器）
  - MdLabor              人员技能资质矩阵
  - MdEnergyRate         能源单价表
  - MdEnergyCalendar     能源日历（峰平谷时间段）
"""

import enum
from decimal import Decimal
from datetime import time

from sqlalchemy import BigInteger, Boolean, Enum, ForeignKey, Integer, Numeric, String, Text, Time, UniqueConstraint
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base


class ResourceType(str, enum.Enum):
    MATERIAL = "MATERIAL"
    EQUIPMENT = "EQUIPMENT"
    LABOR = "LABOR"
    TOOL = "TOOL"
    PROCESS = "PROCESS"


class DataType(str, enum.Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"
    DATE = "DATE"
    ENUM = "ENUM"


class SkillLevel(str, enum.Enum):
    JUNIOR = "JUNIOR"
    INTERMEDIATE = "INTERMEDIATE"
    SENIOR = "SENIOR"
    MASTER = "MASTER"


class EnergyType(str, enum.Enum):
    ELECTRICITY = "ELECTRICITY"
    WATER = "WATER"
    GAS = "GAS"
    STEAM = "STEAM"
    COMPRESSED_AIR = "COMPRESSED_AIR"


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
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="分类编码")
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


# ── 材料主数据（柔性建模）──────────────────────────────────────────────────────

class MdMaterial(AuditMixin, Base):
    __tablename__ = "md_material"
    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uq_md_material_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="材料名称")
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="材料编码（业务唯一标识）")
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("md_resource_category.id"), nullable=True, comment="材料分类 ID"
    )
    pricing_unit_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("md_unit.id"), nullable=True, comment="计价单位 ID"
    )
    consumption_unit_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("md_unit.id"), nullable=True, comment="消耗单位 ID"
    )
    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True, comment="单价（元/计价单位）"
    )
    loss_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="变动损耗率（%，如：5.5 表示 5.5%）"
    )
    scrap_value: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True, comment="废料回收残值（元/单位）"
    )
    substitute_group: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="替代料群组编码（同组材料可互换）"
    )
    substitute_priority: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="替代优先级（数字越小优先级越高）"
    )
    lcc_lifespan_months: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="理论疲劳寿命（月）"
    )
    lcc_maintenance_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="单次维保预估成本（元）"
    )
    dynamic_attributes: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="柔性属性（JSON 对象，如：{\"density\": 7.85, \"surface_treatment\": \"镀锌\"}）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用"
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="材料描述")

    category: Mapped["MdResourceCategory | None"] = relationship(
        "MdResourceCategory", foreign_keys=[category_id]
    )
    pricing_unit: Mapped["MdUnit | None"] = relationship(
        "MdUnit", foreign_keys=[pricing_unit_id]
    )
    consumption_unit: Mapped["MdUnit | None"] = relationship(
        "MdUnit", foreign_keys=[consumption_unit_id]
    )


# ── 设备主数据（数字孪生）──────────────────────────────────────────────────────

class MdEquipment(AuditMixin, Base):
    __tablename__ = "md_equipment"
    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uq_md_equipment_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="设备名称")
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="设备编码（业务唯一标识）")
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("md_resource_category.id"), nullable=True, comment="设备分类 ID"
    )
    depreciation_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True, comment="静态折旧费率（元/小时）"
    )
    power_consumption: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True, comment="基础能耗系数（kW/h）"
    )
    setup_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="换型成本（元/次）"
    )
    oee_target: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="目标 OEE（%，如：85.5）"
    )
    mtbf_hours: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="平均无故障时间 MTBF（小时）"
    )
    defect_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="标准缺陷率（%，如：0.5 表示 0.5%）"
    )
    dynamic_attributes: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="柔性属性（JSON 对象，如：{\"rated_power\": 15.0, \"spindle_speed\": 3000}）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用"
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="设备描述")

    category: Mapped["MdResourceCategory | None"] = relationship(
        "MdResourceCategory", foreign_keys=[category_id]
    )


# ── 标准工艺/工时库 ───────────────────────────────────────────────────────────

class MdProcess(AuditMixin, Base):
    __tablename__ = "md_process"
    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uq_md_process_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="工序名称")
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="工序编码（变量标识）")
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("md_resource_category.id"), nullable=True, comment="工序分类 ID"
    )
    standard_time: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True, comment="标准工时（小时）"
    )
    setup_time: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True, comment="换产准备时间（小时）"
    )
    dynamic_attributes: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="柔性属性（JSON 对象）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用"
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="工序描述")

    category: Mapped["MdResourceCategory | None"] = relationship(
        "MdResourceCategory", foreign_keys=[category_id]
    )
    resources: Mapped[list["MdProcessResource"]] = relationship(
        "MdProcessResource", back_populates="process", cascade="all, delete-orphan"
    )


# ── 工艺资源挂载包（多对多容器）────────────────────────────────────────────────

class MdProcessResource(AuditMixin, Base):
    __tablename__ = "md_process_resource"
    __table_args__ = (
        UniqueConstraint(
            "process_id", "resource_type", "resource_id", "is_deleted",
            name="uq_md_process_resource_unique"
        ),
    )

    process_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("md_process.id"), nullable=False, comment="工序 ID"
    )
    resource_type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType), nullable=False, comment="资源类型（EQUIPMENT/LABOR/MATERIAL/TOOL）"
    )
    resource_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="资源 ID（对应各资源表主键）"
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=1, comment="消耗数量/投入比例"
    )
    resource_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="资源名称快照")
    description: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="备注说明")

    process: Mapped["MdProcess"] = relationship("MdProcess", back_populates="resources")


# ── 人员技能资质矩阵 ───────────────────────────────────────────────────────────

class MdLabor(AuditMixin, Base):
    __tablename__ = "md_labor"
    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uq_md_labor_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="人员名称")
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="人员编码")
    labor_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="工种（如：焊工、电工、装配工）"
    )
    skill_level: Mapped[SkillLevel] = mapped_column(
        Enum(SkillLevel), nullable=False, comment="技能等级（初/中/高/技师）"
    )
    hourly_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="标准时薪（元/小时）"
    )
    qualification_code: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="资质编码（用于排产约束）"
    )
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("md_resource_category.id"), nullable=True, comment="人员分类 ID"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用"
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="人员描述")

    category: Mapped["MdResourceCategory | None"] = relationship(
        "MdResourceCategory", foreign_keys=[category_id]
    )


# ── 能源单价表 ─────────────────────────────────────────────────────────────────

class MdEnergyRate(AuditMixin, Base):
    __tablename__ = "md_energy_rate"
    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uq_md_energy_rate_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="能源名称")
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="能源编码")
    energy_type: Mapped[EnergyType] = mapped_column(
        Enum(EnergyType), nullable=False, comment="能源类型（电/水/气/蒸汽/压缩空气）"
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), nullable=False, comment="单价（元/单位）"
    )
    unit_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("md_unit.id"), nullable=True, comment="计价单位 ID"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用"
    )
    description: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="能源描述")

    unit: Mapped["MdUnit | None"] = relationship("MdUnit")
    calendars: Mapped[list["MdEnergyCalendar"]] = relationship(
        "MdEnergyCalendar", back_populates="energy_rate"
    )


# ── 能源日历（峰平谷时间段）────────────────────────────────────────────────────

class MdEnergyCalendar(AuditMixin, Base):
    __tablename__ = "md_energy_calendar"
    __table_args__ = (
        UniqueConstraint("energy_rate_id", "name", "is_deleted", name="uq_md_energy_calendar_rate_name_deleted"),
    )

    energy_rate_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("md_energy_rate.id"), nullable=False, comment="能源单价 ID"
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="时段名称（如：峰时段、平时段、谷时段）")
    start_time: Mapped[time] = mapped_column(
        Time, nullable=False, comment="开始时间（如：08:00:00）"
    )
    end_time: Mapped[time] = mapped_column(
        Time, nullable=False, comment="结束时间（如：12:00:00）"
    )
    multiplier: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=1.0, comment="费率系数（如：峰时段 1.5，谷时段 0.5）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用"
    )
    description: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="时段描述")

    energy_rate: Mapped["MdEnergyRate"] = relationship("MdEnergyRate", back_populates="calendars")
