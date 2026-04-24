"""LCC 财务评估基准 Schema。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


RiskStrategy = Literal["FIXED", "PERCENTAGE"]


class LccFinancialBaselineBase(BaseModel):
    rule_name: str = Field(..., min_length=1, max_length=100, description="规则名称")
    lifecycle_years: int = Field(15, ge=1, description="生命周期设定（年）")
    discount_rate: Decimal = Field(Decimal("10.0000"), decimal_places=4, description="资金折现率/WACC（%）")
    corrosion_rate: Decimal = Field(Decimal("4.0000"), decimal_places=4, description="维保年度递增率（%）")
    risk_strategy: RiskStrategy = Field("FIXED", description="风险拨备策略")
    risk_value: Decimal = Field(Decimal("0.0000"), ge=0, decimal_places=4, description="风险拨备数值")
    eol_salvage_rate: Decimal = Field(Decimal("0.0000"), decimal_places=4, description="期末处置残值率（%）")
    is_active: bool = Field(True, description="是否启用")

    @model_validator(mode="after")
    def validate_financial_values(self) -> "LccFinancialBaselineBase":
        if self.discount_rate < Decimal("0"):
            raise ValueError("折现率不能为负数")
        if self.corrosion_rate < Decimal("0"):
            raise ValueError("设备维保递增率不能为负数")
        if self.risk_strategy == "PERCENTAGE" and self.risk_value > Decimal("100"):
            raise ValueError("按 OPEX 百分比计提时，拨备数值不能超过 100")
        return self


class LccFinancialBaselineCreate(LccFinancialBaselineBase):
    pass


class LccFinancialBaselineUpdate(BaseModel):
    rule_name: str | None = Field(None, min_length=1, max_length=100)
    lifecycle_years: int | None = Field(None, ge=1)
    discount_rate: Decimal | None = Field(None, decimal_places=4)
    corrosion_rate: Decimal | None = Field(None, decimal_places=4)
    risk_strategy: RiskStrategy | None = None
    risk_value: Decimal | None = Field(None, ge=0, decimal_places=4)
    eol_salvage_rate: Decimal | None = Field(None, decimal_places=4)
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_financial_values(self) -> "LccFinancialBaselineUpdate":
        if self.discount_rate is not None and self.discount_rate < Decimal("0"):
            raise ValueError("折现率不能为负数")
        if self.corrosion_rate is not None and self.corrosion_rate < Decimal("0"):
            raise ValueError("设备维保递增率不能为负数")
        if self.risk_strategy == "PERCENTAGE" and self.risk_value is not None and self.risk_value > Decimal("100"):
            raise ValueError("按 OPEX 百分比计提时，拨备数值不能超过 100")
        return self


class LccFinancialBaselineResponse(LccFinancialBaselineBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True
