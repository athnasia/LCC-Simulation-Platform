"""
主数据 - 材料管理路由层

提供材料主数据的 RESTful API 接口
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db, require_permission
from app.models.system import SysUser
from app.schemas.common import PageResult
from app.schemas.master_data import (
    MaterialCreate,
    MaterialResponse,
    MaterialUpdate,
)
from app.services.master_data_service import MaterialService

router = APIRouter()


@router.get(
    "",
    response_model=PageResult[MaterialResponse],
    summary="查询材料列表",
    description="支持按关键字、分类、启用状态筛选，分页返回。",
)
def list_materials(
    keyword: str | None = Query(None, description="材料名称或编码关键字"),
    category_id: int | None = Query(None, description="材料分类 ID"),
    is_active: bool | None = Query(None, description="是否启用"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/materials", "read")),
) -> PageResult[MaterialResponse]:
    return MaterialService(db).list(
        keyword=keyword,
        category_id=category_id,
        is_active=is_active,
        page=page,
        size=size,
    )


@router.post(
    "",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建材料",
)
def create_material(
    payload: MaterialCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/materials", "write")),
) -> MaterialResponse:
    operator = str(current_user.id)
    result = MaterialService(db).create(payload, operator)
    return result


@router.get(
    "/{material_id}",
    response_model=MaterialResponse,
    summary="获取材料详情",
)
def get_material(
    material_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/materials", "read")),
) -> MaterialResponse:
    return MaterialService(db).get(material_id)


@router.put(
    "/{material_id}",
    response_model=MaterialResponse,
    summary="更新材料",
)
def update_material(
    material_id: int,
    payload: MaterialUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/materials", "write")),
) -> MaterialResponse:
    operator = str(current_user.id)
    result = MaterialService(db).update(material_id, payload, operator)
    return result


@router.delete(
    "/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除材料",
)
def delete_material(
    material_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/materials", "delete")),
) -> None:
    operator = str(current_user.id)
    MaterialService(db).delete(material_id, operator)
