"""
人员技能资质矩阵 API 路由
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db, require_permission
from app.schemas.common import PageResult
from app.schemas.master_data import (
    LaborCreate,
    LaborResponse,
    LaborUpdate,
    SkillLevel,
)
from app.services.master_data_service import LaborService
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
    _: SysUser = Depends(get_current_active_user),
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
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/labor", "write")),
):
    result = LaborService(db).create(payload, current_user.username)
    return result


@router.get("/{labor_id}", response_model=LaborResponse)
def get_labor(
    labor_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_active_user),
):
    return LaborService(db).get(labor_id)


@router.put("/{labor_id}", response_model=LaborResponse)
def update_labor(
    labor_id: int,
    payload: LaborUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/labor", "write")),
):
    result = LaborService(db).update(labor_id, payload, current_user.username)
    return result


@router.delete("/{labor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_labor(
    labor_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/labor", "delete")),
):
    LaborService(db).delete(labor_id, current_user.username)
