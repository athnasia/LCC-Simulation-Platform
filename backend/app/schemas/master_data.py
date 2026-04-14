"""
主数据域 Pydantic Schema

包含：
  - 量纲定义（UnitDimension）的请求/响应模型
  - 单位（Unit）的请求/响应模型
  - 单位换算（UnitConversion）的请求/响应模型（含同量纲防呆校验）
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator


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
    pass


class UnitConversionUpdate(BaseModel):
    conversion_factor: Decimal | None = Field(None, gt=0)
    offset: Decimal | None = None
    description: str | None = Field(None, max_length=256)


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
    depreciation_rate: Decimal | None = Field(None, description="静态折旧费率")
    power_consumption: Decimal | None = Field(None, description="基础能耗系数")
    dynamic_attributes: dict[str, Any] | None = Field(None, description="柔性属性")
    is_active: bool = Field(True, description="是否启用")
    description: str | None = Field(None, max_length=512, description="设备描述")


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    category_id: int | None = None
    depreciation_rate: Decimal | None = None
    power_consumption: Decimal | None = None
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
