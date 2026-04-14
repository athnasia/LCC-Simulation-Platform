"""
主数据域 Pydantic Schema

包含：
  - 量纲定义（UnitDimension）的请求/响应模型
  - 单位（Unit）的请求/响应模型
  - 单位换算（UnitConversion）的请求/响应模型（含同量纲防呆校验）
"""

from datetime import datetime
from decimal import Decimal

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
