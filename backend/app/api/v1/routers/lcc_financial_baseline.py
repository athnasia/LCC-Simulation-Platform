"""LCC 财务评估基准 API 路由。"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_permission
from app.models.system import SysUser
from app.schemas.common import PageResult
from app.schemas.lcc_financial_baseline import (
    LccFinancialBaselineCreate,
    LccFinancialBaselineResponse,
    LccFinancialBaselineUpdate,
)
from app.services.lcc_financial_baseline_service import LccFinancialBaselineService
from app.services.system_service import AuditLogService

router = APIRouter()


@router.get("", response_model=PageResult[LccFinancialBaselineResponse])
def list_lcc_financial_baselines(
    keyword: str | None = None,
    risk_strategy: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/costing/lcc-financial-baselines", "read")),
):
    return LccFinancialBaselineService(db).list(
        keyword=keyword,
        risk_strategy=risk_strategy,
        is_active=is_active,
        page=page,
        size=size,
    )


@router.post("", response_model=LccFinancialBaselineResponse, status_code=status.HTTP_201_CREATED)
def create_lcc_financial_baseline(
    payload: LccFinancialBaselineCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/costing/lcc-financial-baselines", "write")),
):
    result = LccFinancialBaselineService(db).create(payload, current_user.username)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="LccFinancialBaseline",
        resource_id=result.id,
        detail=payload.model_dump(mode="json"),
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/{baseline_id}", response_model=LccFinancialBaselineResponse)
def get_lcc_financial_baseline(
    baseline_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/costing/lcc-financial-baselines", "read")),
):
    return LccFinancialBaselineService(db).get(baseline_id)


@router.put("/{baseline_id}", response_model=LccFinancialBaselineResponse)
def update_lcc_financial_baseline(
    baseline_id: int,
    payload: LccFinancialBaselineUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/costing/lcc-financial-baselines", "write")),
):
    result = LccFinancialBaselineService(db).update(baseline_id, payload, current_user.username)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="LccFinancialBaseline",
        resource_id=baseline_id,
        detail=payload.model_dump(exclude_unset=True, mode="json"),
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.delete("/{baseline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lcc_financial_baseline(
    baseline_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/costing/lcc-financial-baselines", "delete")),
):
    LccFinancialBaselineService(db).delete(baseline_id, current_user.username)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="LccFinancialBaseline",
        resource_id=baseline_id,
        ip_address=request.client.host if request.client else None,
    )
