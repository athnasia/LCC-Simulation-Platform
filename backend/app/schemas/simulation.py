from decimal import Decimal, ROUND_HALF_UP

from pydantic import BaseModel, Field, model_validator


WAN_TO_YUAN = Decimal("10000")
YUAN_QUANTIZER = Decimal("0.01")


class SimulationStartRequest(BaseModel):
    snapshot_id: int = Field(..., ge=1, description="模型快照 ID")
    baseline_id: int | None = Field(None, ge=1, description="LCC 财务评估基准 ID")
    capex: Decimal | None = Field(None, gt=0, description="初始总投资 CAPEX（万元）")
    base_mc: Decimal | None = Field(None, gt=0, description="首年维保基准费（万元）")
    annual_hours: Decimal = Field(Decimal("8000"), gt=0, description="年运行小时数")

    @model_validator(mode="after")
    def validate_chemical_payload(self) -> "SimulationStartRequest":
        chemical_values = [self.baseline_id, self.capex, self.base_mc]
        provided_count = sum(value is not None for value in chemical_values)
        if provided_count not in {0, len(chemical_values)}:
            raise ValueError("baseline_id、capex、base_mc 必须同时提供")
        return self

    def to_simulation_payload(self) -> dict[str, int | str]:
        payload: dict[str, int | str] = {
            "snapshot_id": self.snapshot_id,
            "annual_hours": self._decimal_to_string(self.annual_hours),
        }
        if self.baseline_id is not None:
            payload.update(
                {
                    "baseline_id": self.baseline_id,
                    "capex": self._decimal_to_string(self.capex * WAN_TO_YUAN),
                    "base_mc": self._decimal_to_string(self.base_mc * WAN_TO_YUAN),
                }
            )
        return payload

    @staticmethod
    def _decimal_to_string(value: Decimal) -> str:
        return format(value.quantize(YUAN_QUANTIZER, rounding=ROUND_HALF_UP), "f")