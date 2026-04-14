"""
主数据 - 字典与模板路由层

包含：
  - 量纲定义（UnitDimension）CRUD 接口
  - 单位（Unit）CRUD 接口
  - 单位换算（UnitConversion）CRUD 接口 + 换算计算接口

路由层职责边界：
  - 接收并校验请求参数（Pydantic 自动完成）
  - 调用 Service 执行业务逻辑
  - 封装响应对象返回给调用方
  - 严禁在此处编写 SQL、ORM 操作或业务规则
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db, require_permission
from app.models.system import SysUser
from app.schemas.common import PageResult
from app.schemas.master_data import (
    UnitConversionCalculateRequest,
    UnitConversionCalculateResponse,
    UnitConversionCreate,
    UnitConversionResponse,
    UnitConversionUpdate,
    UnitCreate,
    UnitDimensionCreate,
    UnitDimensionResponse,
    UnitDimensionUpdate,
    UnitResponse,
    UnitUpdate,
)
from app.services.master_data_service import (
    UnitConversionService,
    UnitDimensionService,
    UnitService,
)

router = APIRouter()


def _commit_write(db: Session) -> None:
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# 一、量纲定义接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/dimensions",
    response_model=PageResult[UnitDimensionResponse],
    summary="查询量纲列表",
    description="支持按关键字搜索，分页返回。",
)
def list_dimensions(
    keyword: str | None = Query(None, description="量纲名称或编码关键字"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/dict-templates", "read")),
) -> PageResult[UnitDimensionResponse]:
    return UnitDimensionService(db).list(keyword=keyword, page=page, size=size)


@router.post(
    "/dimensions",
    response_model=UnitDimensionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建量纲",
)
def create_dimension(
    payload: UnitDimensionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "write")),
) -> UnitDimensionResponse:
    operator = str(current_user.id)
    result = UnitDimensionService(db).create(payload, operator)
    _commit_write(db)
    return result


@router.get(
    "/dimensions/{dimension_id}",
    response_model=UnitDimensionResponse,
    summary="获取量纲详情",
)
def get_dimension(
    dimension_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/dict-templates", "read")),
) -> UnitDimensionResponse:
    return UnitDimensionService(db).get(dimension_id)


@router.put(
    "/dimensions/{dimension_id}",
    response_model=UnitDimensionResponse,
    summary="更新量纲",
)
def update_dimension(
    dimension_id: int,
    payload: UnitDimensionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "write")),
) -> UnitDimensionResponse:
    operator = str(current_user.id)
    result = UnitDimensionService(db).update(dimension_id, payload, operator)
    _commit_write(db)
    return result


@router.delete(
    "/dimensions/{dimension_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除量纲",
)
def delete_dimension(
    dimension_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "delete")),
) -> None:
    operator = str(current_user.id)
    UnitDimensionService(db).delete(dimension_id, operator)
    _commit_write(db)


# ═══════════════════════════════════════════════════════════════════════════════
# 二、单位接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/units",
    response_model=PageResult[UnitResponse],
    summary="查询单位列表",
    description="支持按关键字、量纲、是否基础单位筛选，分页返回。",
)
def list_units(
    keyword: str | None = Query(None, description="单位名称或编码关键字"),
    dimension_id: int | None = Query(None, description="量纲 ID"),
    is_base: bool | None = Query(None, description="是否基础单位"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/dict-templates", "read")),
) -> PageResult[UnitResponse]:
    return UnitService(db).list(
        keyword=keyword, dimension_id=dimension_id, is_base=is_base, page=page, size=size
    )


@router.post(
    "/units",
    response_model=UnitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建单位",
)
def create_unit(
    payload: UnitCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "write")),
) -> UnitResponse:
    operator = str(current_user.id)
    result = UnitService(db).create(payload, operator)
    _commit_write(db)
    return result


@router.get(
    "/units/{unit_id}",
    response_model=UnitResponse,
    summary="获取单位详情",
)
def get_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/dict-templates", "read")),
) -> UnitResponse:
    return UnitService(db).get(unit_id)


@router.put(
    "/units/{unit_id}",
    response_model=UnitResponse,
    summary="更新单位",
)
def update_unit(
    unit_id: int,
    payload: UnitUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "write")),
) -> UnitResponse:
    operator = str(current_user.id)
    result = UnitService(db).update(unit_id, payload, operator)
    _commit_write(db)
    return result


@router.delete(
    "/units/{unit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除单位",
)
def delete_unit(
    unit_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "delete")),
) -> None:
    operator = str(current_user.id)
    UnitService(db).delete(unit_id, operator)
    _commit_write(db)


# ═══════════════════════════════════════════════════════════════════════════════
# 三、单位换算接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/conversions",
    response_model=PageResult[UnitConversionResponse],
    summary="查询单位换算列表",
    description="支持按源单位、目标单位筛选，分页返回。",
)
def list_conversions(
    from_unit_id: int | None = Query(None, description="源单位 ID"),
    to_unit_id: int | None = Query(None, description="目标单位 ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/dict-templates", "read")),
) -> PageResult[UnitConversionResponse]:
    return UnitConversionService(db).list(
        from_unit_id=from_unit_id, to_unit_id=to_unit_id, page=page, size=size
    )


@router.post(
    "/conversions",
    response_model=UnitConversionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建单位换算",
    description="源单位和目标单位必须属于同一量纲，否则返回 422 错误。",
)
def create_conversion(
    payload: UnitConversionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "write")),
) -> UnitConversionResponse:
    operator = str(current_user.id)
    result = UnitConversionService(db).create(payload, operator)
    _commit_write(db)
    return result


@router.get(
    "/conversions/{conversion_id}",
    response_model=UnitConversionResponse,
    summary="获取单位换算详情",
)
def get_conversion(
    conversion_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/dict-templates", "read")),
) -> UnitConversionResponse:
    return UnitConversionService(db).get(conversion_id)


@router.put(
    "/conversions/{conversion_id}",
    response_model=UnitConversionResponse,
    summary="更新单位换算",
)
def update_conversion(
    conversion_id: int,
    payload: UnitConversionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "write")),
) -> UnitConversionResponse:
    operator = str(current_user.id)
    result = UnitConversionService(db).update(conversion_id, payload, operator)
    _commit_write(db)
    return result


@router.delete(
    "/conversions/{conversion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除单位换算",
)
def delete_conversion(
    conversion_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "delete")),
) -> None:
    operator = str(current_user.id)
    UnitConversionService(db).delete(conversion_id, operator)
    _commit_write(db)


@router.post(
    "/conversions/calculate",
    response_model=UnitConversionCalculateResponse,
    summary="单位换算计算",
    description="根据换算规则计算数值转换结果。当前版本仅支持线性换算（乘除法）。",
)
def calculate_conversion(
    payload: UnitConversionCalculateRequest,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/dict-templates", "read")),
) -> UnitConversionCalculateResponse:
    return UnitConversionService(db).calculate(payload)
