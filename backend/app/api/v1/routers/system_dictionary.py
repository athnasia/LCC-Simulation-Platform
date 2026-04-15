"""
系统级数据字典路由层

职责：
  - 提供系统管理数据字典类型与字典项 CRUD 接口
  - 提供前端字典缓存聚合只读接口
  - 统一复用系统管理权限模型和审计日志能力
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db, require_permission
from app.models.system import SysUser
from app.schemas.common import PageResult
from app.schemas.system_dictionary import (
    SysDictCacheResponse,
    SysDictItemCreate,
    SysDictItemResponse,
    SysDictItemUpdate,
    SysDictTypeCreate,
    SysDictTypeResponse,
    SysDictTypeUpdate,
)
from app.services.system_dictionary_service import (
    SystemDictionaryCacheService,
    SystemDictionaryItemService,
    SystemDictionaryTypeService,
)
from app.services.system_service import AuditLogService

router = APIRouter()


@router.get(
    "/types",
    response_model=PageResult[SysDictTypeResponse],
    summary="查询字典类型列表",
)
def list_dict_types(
    keyword: str | None = Query(None, description="字典类型名称或编码关键字"),
    is_active: bool | None = Query(None, description="是否启用"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/system/dictionaries", "read")),
) -> PageResult[SysDictTypeResponse]:
    return SystemDictionaryTypeService(db).list(keyword=keyword, is_active=is_active, page=page, size=size)


@router.post(
    "/types",
    response_model=SysDictTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建字典类型",
)
def create_dict_type(
    payload: SysDictTypeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/dictionaries", "write")),
) -> SysDictTypeResponse:
    operator = str(current_user.id)
    result = SystemDictionaryTypeService(db).create(payload, operator)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="SysDictType",
        resource_id=result.id,
        detail={"code": result.code, "name": result.name},
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get(
    "/types/{dict_type_id}",
    response_model=SysDictTypeResponse,
    summary="获取字典类型详情",
)
def get_dict_type(
    dict_type_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/system/dictionaries", "read")),
) -> SysDictTypeResponse:
    return SystemDictionaryTypeService(db).get(dict_type_id)


@router.put(
    "/types/{dict_type_id}",
    response_model=SysDictTypeResponse,
    summary="更新字典类型",
)
def update_dict_type(
    dict_type_id: int,
    payload: SysDictTypeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/dictionaries", "write")),
) -> SysDictTypeResponse:
    operator = str(current_user.id)
    result = SystemDictionaryTypeService(db).update(dict_type_id, payload, operator)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="SysDictType",
        resource_id=dict_type_id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.delete(
    "/types/{dict_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除字典类型",
)
def delete_dict_type(
    dict_type_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/dictionaries", "delete")),
) -> None:
    SystemDictionaryTypeService(db).delete(dict_type_id, str(current_user.id))
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="SysDictType",
        resource_id=dict_type_id,
        ip_address=request.client.host if request.client else None,
    )


@router.get(
    "/items",
    response_model=PageResult[SysDictItemResponse],
    summary="查询字典项列表",
)
def list_dict_items(
    dict_type_id: int | None = Query(None, description="字典类型 ID"),
    dict_type_code: str | None = Query(None, description="字典类型编码"),
    keyword: str | None = Query(None, description="字典值或展示标签关键字"),
    is_active: bool | None = Query(None, description="是否启用"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/system/dictionaries", "read")),
) -> PageResult[SysDictItemResponse]:
    return SystemDictionaryItemService(db).list(
        dict_type_id=dict_type_id,
        dict_type_code=dict_type_code,
        keyword=keyword,
        is_active=is_active,
        page=page,
        size=size,
    )


@router.post(
    "/items",
    response_model=SysDictItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建字典项",
)
def create_dict_item(
    payload: SysDictItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/dictionaries", "write")),
) -> SysDictItemResponse:
    operator = str(current_user.id)
    result = SystemDictionaryItemService(db).create(payload, operator)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="SysDictItem",
        resource_id=result.id,
        detail={"dict_type_id": result.dict_type_id, "value": result.value, "label": result.label},
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get(
    "/items/{item_id}",
    response_model=SysDictItemResponse,
    summary="获取字典项详情",
)
def get_dict_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/system/dictionaries", "read")),
) -> SysDictItemResponse:
    return SystemDictionaryItemService(db).get(item_id)


@router.put(
    "/items/{item_id}",
    response_model=SysDictItemResponse,
    summary="更新字典项",
)
def update_dict_item(
    item_id: int,
    payload: SysDictItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/dictionaries", "write")),
) -> SysDictItemResponse:
    operator = str(current_user.id)
    result = SystemDictionaryItemService(db).update(item_id, payload, operator)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="SysDictItem",
        resource_id=item_id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除字典项",
)
def delete_dict_item(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/dictionaries", "delete")),
) -> None:
    SystemDictionaryItemService(db).delete(item_id, str(current_user.id))
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="SysDictItem",
        resource_id=item_id,
        ip_address=request.client.host if request.client else None,
    )


@router.get(
    "/cache",
    response_model=SysDictCacheResponse,
    summary="获取前端字典缓存聚合结果",
)
def get_dict_cache(
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_active_user),
) -> SysDictCacheResponse:
    return SystemDictionaryCacheService(db).get_active_cache()