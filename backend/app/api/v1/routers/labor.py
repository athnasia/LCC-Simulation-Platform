"""
人员技能资质矩阵 API 路由
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_permission
from app.schemas.common import PageResult
from app.schemas.master_data import (
    LaborCreate,
    LaborResponse,
    LaborUpdate,
    SkillLevel,
)
from app.services.master_data.labor_service import LaborService
from app.services.system_service import AuditLogService
from app.models.system import SysUser

router = APIRouter()


@router.get("", response_model=PageResult[LaborResponse])
def list_labor(
    keyword: str | None = None,
    labor_type: str | None = None,
    skill_level: SkillLevel | None = None,
    is_active: bool | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/labor", "read")),
):
    return LaborService(db).list(
        keyword=keyword,
        labor_type=labor_type,
        skill_level=skill_level,
        is_active=is_active,
        page=page,
        size=size,
    )


@router.post("", response_model=LaborResponse, status_code=status.HTTP_201_CREATED)
def create_labor(
    payload: LaborCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/labor", "write")),
):
    result = LaborService(db).create(payload, current_user.username)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="MdLabor",
        resource_id=result.id,
        detail={"name": result.name, "code": result.code},
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/{labor_id}", response_model=LaborResponse)
def get_labor(
    labor_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/labor", "read")),
):
    return LaborService(db).get(labor_id)


@router.put("/{labor_id}", response_model=LaborResponse)
def update_labor(
    labor_id: int,
    payload: LaborUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/labor", "write")),
):
    result = LaborService(db).update(labor_id, payload, current_user.username)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="MdLabor",
        resource_id=labor_id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.delete("/{labor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_labor(
    labor_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/labor", "delete")),
):
    LaborService(db).delete(labor_id, current_user.username)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="MdLabor",
        resource_id=labor_id,
        ip_address=request.client.host if request.client else None,
    )
