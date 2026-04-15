"""
主数据 - 设备管理路由层

提供设备主数据的 RESTful API 接口
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db, require_permission
from app.models.system import SysUser
from app.schemas.common import PageResult
from app.schemas.master_data import (
    EquipmentCreate,
    EquipmentResponse,
    EquipmentUpdate,
)
from app.services.master_data_service import EquipmentService

router = APIRouter()


@router.get(
    "",
    response_model=PageResult[EquipmentResponse],
    summary="查询设备列表",
    description="支持按关键字、分类、启用状态筛选，分页返回。",
)
def list_equipments(
    keyword: str | None = Query(None, description="设备名称或编码关键字"),
    category_id: int | None = Query(None, description="设备分类 ID"),
    is_active: bool | None = Query(None, description="是否启用"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/equipments", "read")),
) -> PageResult[EquipmentResponse]:
    return EquipmentService(db).list(
        keyword=keyword,
        category_id=category_id,
        is_active=is_active,
        page=page,
        size=size,
    )


@router.post(
    "",
    response_model=EquipmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建设备",
)
def create_equipment(
    payload: EquipmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/equipments", "write")),
) -> EquipmentResponse:
    operator = str(current_user.id)
    result = EquipmentService(db).create(payload, operator)
    return result


@router.get(
    "/{equipment_id}",
    response_model=EquipmentResponse,
    summary="获取设备详情",
)
def get_equipment(
    equipment_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/equipments", "read")),
) -> EquipmentResponse:
    return EquipmentService(db).get(equipment_id)


@router.put(
    "/{equipment_id}",
    response_model=EquipmentResponse,
    summary="更新设备",
)
def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/equipments", "write")),
) -> EquipmentResponse:
    operator = str(current_user.id)
    result = EquipmentService(db).update(equipment_id, payload, operator)
    return result


@router.delete(
    "/{equipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除设备",
)
def delete_equipment(
    equipment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/equipments", "delete")),
) -> None:
    operator = str(current_user.id)
    EquipmentService(db).delete(equipment_id, operator)
