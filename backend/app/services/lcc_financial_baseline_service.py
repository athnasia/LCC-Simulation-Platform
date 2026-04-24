from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.models.engineering import LccFinancialBaseline
from app.schemas.common import PageResult
from app.schemas.lcc_financial_baseline import (
    LccFinancialBaselineCreate,
    LccFinancialBaselineResponse,
    LccFinancialBaselineUpdate,
)
from app.services.master_data.base import _build_deleted_unique_value


class LccFinancialBaselineService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, baseline_id: int) -> LccFinancialBaseline:
        baseline = self.db.execute(
            select(LccFinancialBaseline).where(
                LccFinancialBaseline.id == baseline_id,
                LccFinancialBaseline.is_deleted == False,
            )
        ).scalar_one_or_none()
        if baseline is None:
            raise ResourceNotFoundError(resource="LCC 财务评估基准", identifier=baseline_id)
        return baseline

    def _assert_name_unique(self, rule_name: str) -> None:
        exists = self.db.execute(
            select(LccFinancialBaseline).where(
                LccFinancialBaseline.rule_name == rule_name,
                LccFinancialBaseline.is_deleted == False,
            )
        ).scalar_one_or_none()
        if exists is not None:
            raise BusinessRuleViolationError(
                error_code="LCC_FINANCIAL_BASELINE_NAME_DUPLICATE",
                message=f"LCC 财务评估基准名称已存在：{rule_name}",
            )

    def _validate_business_constraints(self, risk_strategy: str, risk_value) -> None:
        if risk_strategy == "PERCENTAGE" and risk_value > 100:
            raise BusinessRuleViolationError(
                error_code="LCC_FINANCIAL_BASELINE_RISK_INVALID",
                message="按 OPEX 百分比计提时，拨备数值不能超过 100",
            )

    def list(
        self,
        keyword: str | None = None,
        risk_strategy: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[LccFinancialBaselineResponse]:
        stmt = select(LccFinancialBaseline).where(LccFinancialBaseline.is_deleted == False)

        if keyword:
            stmt = stmt.where(LccFinancialBaseline.rule_name.ilike(f"%{keyword}%"))
        if risk_strategy:
            stmt = stmt.where(LccFinancialBaseline.risk_strategy == risk_strategy)
        if is_active is not None:
            stmt = stmt.where(LccFinancialBaseline.is_active == is_active)

        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
        items = self.db.execute(
            stmt.order_by(LccFinancialBaseline.id.desc()).offset((page - 1) * size).limit(size)
        ).scalars().all()

        return PageResult.build(
            items=[LccFinancialBaselineResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
        )

    def get(self, baseline_id: int) -> LccFinancialBaselineResponse:
        return LccFinancialBaselineResponse.model_validate(self._get_or_404(baseline_id))

    def create(self, payload: LccFinancialBaselineCreate, operator: str) -> LccFinancialBaselineResponse:
        self._assert_name_unique(payload.rule_name)
        self._validate_business_constraints(payload.risk_strategy, payload.risk_value)

        baseline = LccFinancialBaseline(
            **payload.model_dump(),
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(baseline)
        self.db.flush()
        return LccFinancialBaselineResponse.model_validate(baseline)

    def update(self, baseline_id: int, payload: LccFinancialBaselineUpdate, operator: str) -> LccFinancialBaselineResponse:
        baseline = self._get_or_404(baseline_id)

        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            return LccFinancialBaselineResponse.model_validate(baseline)

        if "rule_name" in update_data and update_data["rule_name"] != baseline.rule_name:
            self._assert_name_unique(update_data["rule_name"])

        risk_strategy = update_data.get("risk_strategy", baseline.risk_strategy)
        risk_value = update_data.get("risk_value", baseline.risk_value)
        self._validate_business_constraints(risk_strategy, risk_value)

        for field, value in update_data.items():
            setattr(baseline, field, value)
        baseline.updated_by = operator
        self.db.flush()
        return LccFinancialBaselineResponse.model_validate(baseline)

    def delete(self, baseline_id: int, operator: str) -> None:
        baseline = self._get_or_404(baseline_id)
        baseline.rule_name = _build_deleted_unique_value(baseline.rule_name, baseline.id, 100)
        baseline.is_deleted = True
        baseline.updated_by = operator
        self.db.flush()
