"""
能源单价与日历 API 路由
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_permission
from app.schemas.common import PageResult
from app.schemas.master_data import (
    EnergyCalendarCreate,
    EnergyCalendarResponse,
    EnergyCalendarUpdate,
    EnergyRateCreate,
    EnergyRateResponse,
    EnergyRateUpdate,
    EnergyType,
)
from app.services.master_data.energy_service import EnergyRateService, EnergyCalendarService
from app.services.system_service import AuditLogService
from app.models.system import SysUser

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# 能源单价接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/rates", response_model=PageResult[EnergyRateResponse])
def list_energy_rates(
    keyword: str | None = None,
    energy_type: EnergyType | None = None,
    is_active: bool | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/energy", "read")),
):
    return EnergyRateService(db).list(
        keyword=keyword,
        energy_type=energy_type,
        is_active=is_active,
        page=page,
        size=size,
    )


@router.post("/rates", response_model=EnergyRateResponse, status_code=status.HTTP_201_CREATED)
def create_energy_rate(
    payload: EnergyRateCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/energy", "write")),
):
    result = EnergyRateService(db).create(payload, current_user.username)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="MdEnergyRate",
        resource_id=result.id,
        detail={"name": result.name, "code": result.code, "energy_type": result.energy_type},
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/rates/{rate_id}", response_model=EnergyRateResponse)
def get_energy_rate(
    rate_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/energy", "read")),
):
    return EnergyRateService(db).get(rate_id)


@router.put("/rates/{rate_id}", response_model=EnergyRateResponse)
def update_energy_rate(
    rate_id: int,
    payload: EnergyRateUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/energy", "write")),
):
    result = EnergyRateService(db).update(rate_id, payload, current_user.username)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="MdEnergyRate",
        resource_id=rate_id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.delete("/rates/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_energy_rate(
    rate_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/energy", "delete")),
):
    EnergyRateService(db).delete(rate_id, current_user.username)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="MdEnergyRate",
        resource_id=rate_id,
        ip_address=request.client.host if request.client else None,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 能源日历接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/calendars", response_model=PageResult[EnergyCalendarResponse])
def list_energy_calendars(
    energy_rate_id: int | None = None,
    is_active: bool | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/energy", "read")),
):
    return EnergyCalendarService(db).list(
        energy_rate_id=energy_rate_id,
        is_active=is_active,
        page=page,
        size=size,
    )


@router.post("/calendars", response_model=EnergyCalendarResponse, status_code=status.HTTP_201_CREATED)
def create_energy_calendar(
    payload: EnergyCalendarCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/energy", "write")),
):
    result = EnergyCalendarService(db).create(payload, current_user.username)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="MdEnergyCalendar",
        resource_id=result.id,
        detail={"name": result.name, "energy_rate_id": result.energy_rate_id},
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/calendars/{calendar_id}", response_model=EnergyCalendarResponse)
def get_energy_calendar(
    calendar_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/energy", "read")),
):
    return EnergyCalendarService(db).get(calendar_id)


@router.put("/calendars/{calendar_id}", response_model=EnergyCalendarResponse)
def update_energy_calendar(
    calendar_id: int,
    payload: EnergyCalendarUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/energy", "write")),
):
    result = EnergyCalendarService(db).update(calendar_id, payload, current_user.username)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="MdEnergyCalendar",
        resource_id=calendar_id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.delete("/calendars/{calendar_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_energy_calendar(
    calendar_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/energy", "delete")),
):
    EnergyCalendarService(db).delete(calendar_id, current_user.username)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="MdEnergyCalendar",
        resource_id=calendar_id,
        ip_address=request.client.host if request.client else None,
    )
