"""
主数据域 Pydantic Schema

包含：
  - 量纲定义（UnitDimension）的请求/响应模型
  - 单位（Unit）的请求/响应模型
  - 单位换算（UnitConversion）的请求/响应模型（含同量纲防呆校验）
  - 资源分类（ResourceCategory）的请求/响应模型
  - 属性定义（AttrDefinition）的请求/响应模型
  - 材料主数据（Material）的请求/响应模型
  - 设备主数据（Equipment）的请求/响应模型
  - 标准工艺/工时库（Process）的请求/响应模型
  - 工艺资源挂载包（ProcessResource）的请求/响应模型
  - 人员技能资质矩阵（Labor）的请求/响应模型
  - 能源单价（EnergyRate）的请求/响应模型
  - 能源日历（EnergyCalendar）的请求/响应模型
"""

import enum
from datetime import datetime, time
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, computed_field, model_validator


# ═══════════════════════════════════════════════════════════════════════════════
# 一、量纲定义（UnitDimension）
# ═══════════════════════════════════════════════════════════════════════════════

class UnitDimensionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="量纲名称")
    code: str = Field(..., min_length=1, max_length=30, pattern=r"^[A-Z][A-Z0-9_]*$", description="量纲编码（纯大写英文）")
    description: str | None = Field(None, max_length=256, description="量纲描述")
    sort_order: int = Field(0, ge=0, description="排序值")


class UnitDimensionCreate(UnitDimensionBase):
    pass


class UnitDimensionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    description: str | None = Field(None, max_length=256)
    sort_order: int | None = Field(None, ge=0)


class UnitDimensionResponse(UnitDimensionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 二、单位定义（Unit）
# ═══════════════════════════════════════════════════════════════════════════════

class UnitBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="单位名称")
    code: str = Field(..., min_length=1, max_length=20, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$", description="单位编码（英文开头）")
    symbol: str | None = Field(None, max_length=10, description="单位符号")
    dimension_id: int = Field(..., description="所属量纲 ID")
    is_base: bool = Field(False, description="是否基础单位")
    description: str | None = Field(None, max_length=256, description="单位描述")


class UnitCreate(UnitBase):
    pass


class UnitUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    symbol: str | None = Field(None, max_length=10)
    is_base: bool | None = None
    description: str | None = Field(None, max_length=256)


class UnitResponse(UnitBase):
    id: int
    dimension: UnitDimensionResponse
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


class UnitBrief(BaseModel):
    """单位简要信息（用于关联查询）"""
    id: int
    name: str
    code: str
    symbol: str | None
    dimension_id: int

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 三、单位换算（UnitConversion）
# ═══════════════════════════════════════════════════════════════════════════════

class UnitConversionBase(BaseModel):
    from_unit_id: int = Field(..., description="源单位 ID")
    to_unit_id: int = Field(..., description="目标单位 ID")
    conversion_factor: Decimal = Field(..., gt=0, description="换算因子（必须大于0）")
    offset: Decimal | None = Field(None, description="偏移量（保留字段，用于非线性换算）")
    description: str | None = Field(None, max_length=256, description="换算说明")

    @model_validator(mode="after")
    def validate_units_different(self):
        """校验源单位和目标单位不能相同"""
        if self.from_unit_id == self.to_unit_id:
            raise ValueError("源单位和目标单位不能相同")
        return self


class UnitConversionCreate(UnitConversionBase):
    @model_validator(mode="after")
    def validate_linear_only(self):
        """当前版本仅允许线性换算规则入库"""
        if self.offset is not None and self.offset != 0:
            raise ValueError("当前版本仅支持线性换算，offset 必须为 0 或为空")
        return self


class UnitConversionUpdate(BaseModel):
    conversion_factor: Decimal | None = Field(None, gt=0)
    offset: Decimal | None = None
    description: str | None = Field(None, max_length=256)

    @model_validator(mode="after")
    def validate_linear_only(self):
        """当前版本仅允许线性换算规则入库"""
        if self.offset is not None and self.offset != 0:
            raise ValueError("当前版本仅支持线性换算，offset 必须为 0 或为空")
        return self


class UnitConversionResponse(BaseModel):
    id: int
    from_unit: UnitBrief
    to_unit: UnitBrief
    conversion_factor: Decimal
    offset: Decimal | None
    description: str | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 四、换算计算请求（用于 Service 层调用）
# ═══════════════════════════════════════════════════════════════════════════════

class UnitConversionCalculateRequest(BaseModel):
    """单位换算计算请求"""
    from_unit_id: int
    to_unit_id: int
    value: Decimal = Field(..., description="待换算的数值")


class UnitConversionCalculateResponse(BaseModel):
    """单位换算计算结果"""
    from_unit: UnitBrief
    to_unit: UnitBrief
    original_value: Decimal
    converted_value: Decimal
    conversion_factor: Decimal
    offset: Decimal | None


# ═════════════════════════════════════════════════════════════════════════════
# 五、资源分类（ResourceCategory）
# ═════════════════════════════════════════════════════════════════════════════

class ResourceType(str, enum.Enum):
    MATERIAL = "MATERIAL"
    EQUIPMENT = "EQUIPMENT"
    LABOR = "LABOR"
    TOOL = "TOOL"


class ResourceCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    code: str = Field(..., min_length=1, max_length=30, pattern=r"^[A-Z][A-Z0-9_]*$", description="分类编码（纯大写英文）")
    resource_type: ResourceType = Field(..., description="资源类型")
    parent_id: int | None = Field(None, description="父分类 ID（自关联）")
    sort_order: int = Field(0, ge=0, description="排序值")
    is_active: bool = Field(True, description="是否启用")
    description: str | None = Field(None, max_length=256, description="分类描述")


    children: list["ResourceCategoryTreeResponse"] = Field(default_factory=list, description="子分类列表")


    class Config:
        from_attributes = True


class ResourceCategoryCreate(ResourceCategoryBase):
    pass


class ResourceCategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    resource_type: ResourceType | None = None
    parent_id: int | None = None
    sort_order: int | None = Field(None, ge=0)
    is_active: bool | None = None
    description: str | None = Field(None, max_length=256)


    @model_validator(mode="after")
    def validate_parent_not_self(self):
        """校验父分类不能是自己"""
        if self.parent_id == self.id:
            raise ValueError("父分类不能是自己")
        return self


class ResourceCategoryResponse(ResourceCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


class ResourceCategoryTreeResponse(ResourceCategoryBase):
    id: int
    parent_id: int | None
    children: list["ResourceCategoryTreeResponse"]
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


# ═════════════════════════════════════════════════════════════════════════════
# 六、属性定义（AttrDefinition）
# ═════════════════════════════════════════════════════════════════════════════

class DataType(str, enum.Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"
    DATE = "DATE"
    ENUM = "ENUM"


class AttrDefinitionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="属性名称")
    code: str = Field(..., min_length=1, max_length=30, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$", description="变量标识码（纯英文，供公式引擎解析）")
    data_type: DataType = Field(..., description="数据类型")
    unit_id: int | None = Field(None, description="关联单位 ID（可为空）")
    applicable_resource_types: list[ResourceType] | None = Field(None, description="适用资源类型")
    description: str | None = Field(None, max_length=256, description="属性描述")
    is_required: bool = Field(False, description="是否必填")
    default_value: str | None = Field(None, description="默认值")
    enum_values: list[str] | None = Field(None, description="枚举值列表")

    class Config:
        from_attributes = True


class AttrDefinitionCreate(AttrDefinitionBase):
    pass


class AttrDefinitionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    data_type: DataType | None = None
    unit_id: int | None = None
    applicable_resource_types: list[ResourceType] | None = None
    description: str | None = Field(None, max_length=256)
    is_required: bool | None = None
    default_value: str | None = None
    enum_values: list[str] | None = None


    @model_validator(mode="after")
    def validate_enum_values_for_enum_type(self):
        """校验枚举类型必须提供枚举值列表"""
        if self.data_type == DataType.ENUM and not self.enum_values:
            raise ValueError("枚举类型必须提供 enum_values 字段")
        return self


class AttrDefinitionResponse(AttrDefinitionBase):
    id: int
    unit: UnitBrief | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 七、材料主数据（Material）
# ═══════════════════════════════════════════════════════════════════════════════

class MaterialBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="材料名称")
    code: str = Field(..., min_length=1, max_length=50, description="材料编码")
    category_id: int | None = Field(None, description="材料分类 ID")
    pricing_unit_id: int | None = Field(None, description="计价单位 ID")
    consumption_unit_id: int | None = Field(None, description="消耗单位 ID")
    unit_price: Decimal | None = Field(None, ge=0, description="单价（元/计价单位）")
    loss_rate: Decimal | None = Field(None, ge=0, le=100, description="变动损耗率（%）")
    scrap_value: Decimal | None = Field(None, ge=0, description="废料回收残值（元/单位）")
    substitute_group: str | None = Field(None, max_length=50, description="替代料群组编码")
    substitute_priority: int | None = Field(None, ge=1, description="替代优先级")
    lcc_lifespan_months: int | None = Field(None, ge=1, description="理论疲劳寿命（月）")
    lcc_maintenance_cost: Decimal | None = Field(None, ge=0, description="单次维保预估成本（元）")
    dynamic_attributes: dict[str, Any] | None = Field(None, description="柔性属性")
    is_active: bool = Field(True, description="是否启用")
    description: str | None = Field(None, max_length=512, description="材料描述")


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    category_id: int | None = None
    pricing_unit_id: int | None = None
    consumption_unit_id: int | None = None
    unit_price: Decimal | None = Field(None, ge=0)
    loss_rate: Decimal | None = Field(None, ge=0, le=100)
    scrap_value: Decimal | None = Field(None, ge=0)
    substitute_group: str | None = Field(None, max_length=50)
    substitute_priority: int | None = Field(None, ge=1)
    lcc_lifespan_months: int | None = Field(None, ge=1)
    lcc_maintenance_cost: Decimal | None = Field(None, ge=0)
    dynamic_attributes: dict[str, Any] | None = None
    is_active: bool | None = None
    description: str | None = Field(None, max_length=512)


class MaterialResponse(MaterialBase):
    id: int
    category: ResourceCategoryResponse | None
    pricing_unit: UnitBrief | None
    consumption_unit: UnitBrief | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 八、设备主数据（Equipment）
# ═══════════════════════════════════════════════════════════════════════════════

class EquipmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="设备名称")
    code: str = Field(..., min_length=1, max_length=50, description="设备编码")
    category_id: int | None = Field(None, description="设备分类 ID")
    depreciation_rate: Decimal | None = Field(None, ge=0, description="静态折旧费率（元/小时）")
    power_consumption: Decimal | None = Field(None, ge=0, description="基础能耗系数（kW/h）")
    setup_cost: Decimal | None = Field(None, ge=0, description="换型成本（元/次）")
    oee_target: Decimal | None = Field(None, ge=0, le=100, description="目标 OEE（%）")
    mtbf_hours: Decimal | None = Field(None, ge=0, description="平均无故障时间 MTBF（小时）")
    defect_rate: Decimal | None = Field(None, ge=0, le=100, description="标准缺陷率（%）")
    dynamic_attributes: dict[str, Any] | None = Field(None, description="柔性属性")
    is_active: bool = Field(True, description="是否启用")
    description: str | None = Field(None, max_length=512, description="设备描述")


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    category_id: int | None = None
    depreciation_rate: Decimal | None = Field(None, ge=0)
    power_consumption: Decimal | None = Field(None, ge=0)
    setup_cost: Decimal | None = Field(None, ge=0)
    oee_target: Decimal | None = Field(None, ge=0, le=100)
    mtbf_hours: Decimal | None = Field(None, ge=0)
    defect_rate: Decimal | None = Field(None, ge=0, le=100)
    dynamic_attributes: dict[str, Any] | None = None
    is_active: bool | None = None
    description: str | None = Field(None, max_length=512)


class EquipmentResponse(EquipmentBase):
    id: int
    category: ResourceCategoryResponse | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 九、标准工艺/工时库（Process）
# ═══════════════════════════════════════════════════════════════════════════════

class ProcessBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="工序名称")
    code: str = Field(..., min_length=1, max_length=50, description="工序编码（变量标识）")
    category_id: int | None = Field(None, description="工序分类 ID")
    standard_time: Decimal | None = Field(None, ge=0, description="标准工时（小时）")
    setup_time: Decimal | None = Field(None, ge=0, description="换产准备时间（小时）")
    is_active: bool = Field(True, description="是否启用")
    description: str | None = Field(None, max_length=512, description="工序描述")


class ProcessCreate(ProcessBase):
    resources: list["ProcessResourceCreate"] = Field(default_factory=list, description="资源挂载列表")


class ProcessUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    category_id: int | None = None
    standard_time: Decimal | None = Field(None, ge=0)
    setup_time: Decimal | None = Field(None, ge=0)
    is_active: bool | None = None
    description: str | None = Field(None, max_length=512)


class ProcessResponse(ProcessBase):
    id: int
    category: ResourceCategoryResponse | None
    resources: list["ProcessResourceResponse"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


class ProcessBrief(BaseModel):
    """工序简要信息（用于关联查询）"""
    id: int
    name: str
    code: str
    standard_time: Decimal | None
    setup_time: Decimal | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 十、工艺资源挂载包（ProcessResource）
# ═══════════════════════════════════════════════════════════════════════════════

class ProcessResourceBase(BaseModel):
    resource_type: ResourceType = Field(..., description="资源类型（EQUIPMENT/LABOR/MATERIAL/TOOL）")
    resource_id: int = Field(..., description="资源 ID（对应各资源表主键）")
    quantity: Decimal = Field(Decimal("1"), ge=0, description="消耗数量/投入比例")
    description: str | None = Field(None, max_length=256, description="备注说明")


class ProcessResourceCreate(ProcessResourceBase):
    pass


class ProcessResourceUpdate(BaseModel):
    resource_type: ResourceType | None = None
    resource_id: int | None = None
    quantity: Decimal | None = Field(None, ge=0)
    description: str | None = Field(None, max_length=256)


class ProcessResourceResponse(ProcessResourceBase):
    id: int
    process_id: int
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 十一、人员技能资质矩阵（Labor）
# ═══════════════════════════════════════════════════════════════════════════════

class SkillLevel(str, enum.Enum):
    JUNIOR = "JUNIOR"
    INTERMEDIATE = "INTERMEDIATE"
    SENIOR = "SENIOR"
    MASTER = "MASTER"


class LaborBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="人员名称")
    code: str = Field(..., min_length=1, max_length=50, description="人员编码")
    labor_type: str | None = Field(None, max_length=50, description="工种（如：焊工、电工、装配工）")
    skill_level: SkillLevel = Field(..., description="技能等级（初/中/高/技师）")
    hourly_rate: Decimal | None = Field(None, ge=0, description="标准时薪（元/小时）")
    qualification_code: str | None = Field(None, max_length=50, description="资质编码（用于排产约束）")
    category_id: int | None = Field(None, description="人员分类 ID")
    is_active: bool = Field(True, description="是否启用")
    description: str | None = Field(None, max_length=512, description="人员描述")


class LaborCreate(LaborBase):
    pass


class LaborUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    labor_type: str | None = Field(None, max_length=50)
    skill_level: SkillLevel | None = None
    hourly_rate: Decimal | None = Field(None, ge=0)
    qualification_code: str | None = Field(None, max_length=50)
    category_id: int | None = None
    is_active: bool | None = None
    description: str | None = Field(None, max_length=512)


class LaborResponse(LaborBase):
    id: int
    category: ResourceCategoryResponse | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


class LaborBrief(BaseModel):
    """人员简要信息（用于关联查询）"""
    id: int
    name: str
    code: str
    labor_type: str | None
    skill_level: SkillLevel
    hourly_rate: Decimal | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 十二、能源单价（EnergyRate）
# ═══════════════════════════════════════════════════════════════════════════════

class EnergyType(str, enum.Enum):
    ELECTRICITY = "ELECTRICITY"
    WATER = "WATER"
    GAS = "GAS"
    STEAM = "STEAM"
    COMPRESSED_AIR = "COMPRESSED_AIR"


class EnergyRateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="能源名称")
    code: str = Field(..., min_length=1, max_length=50, description="能源编码")
    energy_type: EnergyType = Field(..., description="能源类型（电/水/气/蒸汽/压缩空气）")
    unit_price: Decimal = Field(..., ge=0, description="单价（元/单位）")
    unit_id: int | None = Field(None, description="计价单位 ID")
    is_active: bool = Field(True, description="是否启用")
    description: str | None = Field(None, max_length=256, description="能源描述")


class EnergyRateCreate(EnergyRateBase):
    calendars: list["EnergyCalendarCreateNested"] = Field(default_factory=list, description="能源日历列表")


class EnergyRateUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    energy_type: EnergyType | None = None
    unit_price: Decimal | None = Field(None, ge=0)
    unit_id: int | None = None
    is_active: bool | None = None
    description: str | None = Field(None, max_length=256)


class EnergyRateResponse(EnergyRateBase):
    id: int
    unit: UnitBrief | None
    calendars: list["EnergyCalendarResponse"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


class EnergyRateBrief(BaseModel):
    """能源单价简要信息（用于关联查询）"""
    id: int
    name: str
    code: str
    energy_type: EnergyType
    unit_price: Decimal

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 十三、能源日历（EnergyCalendar）
# ═══════════════════════════════════════════════════════════════════════════════

class EnergyCalendarBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="时段名称（如：峰时段、平时段、谷时段）")
    start_time: time = Field(..., description="开始时间（如：08:00:00，支持跨天时段如 23:00:00）")
    end_time: time = Field(..., description="结束时间（如：12:00:00，若小于开始时间则表示跨天）")
    multiplier: Decimal = Field(Decimal("1.0"), ge=0, description="费率系数（如：峰时段 1.5，谷时段 0.5）")
    is_active: bool = Field(True, description="是否启用")
    description: str | None = Field(None, max_length=256, description="时段描述")

    @computed_field(return_type=bool)
    def is_cross_day(self) -> bool:
        """判断是否为跨天时段（如 23:00 -> 次日 07:00）"""
        return self.start_time >= self.end_time


class EnergyCalendarCreate(EnergyCalendarBase):
    energy_rate_id: int = Field(..., description="能源单价 ID")


class EnergyCalendarCreateNested(EnergyCalendarBase):
    """嵌套在 EnergyRateCreate 中使用，不需要 energy_rate_id"""
    pass


class EnergyCalendarUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    start_time: time | None = None
    end_time: time | None = None
    multiplier: Decimal | None = Field(None, ge=0)
    is_active: bool | None = None
    description: str | None = Field(None, max_length=256)


class EnergyCalendarResponse(EnergyCalendarBase):
    id: int
    energy_rate_id: int
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 十四、工艺复制请求
# ═══════════════════════════════════════════════════════════════════════════════

class ProcessCloneRequest(BaseModel):
    new_name: str = Field(..., min_length=1, max_length=100, description="新工序名称")
    new_code: str = Field(..., min_length=1, max_length=50, description="新工序编码")
    copy_resources: bool = Field(True, description="是否复制资源挂载包")
