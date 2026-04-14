"""
主数据 - 字典与模板路由层

包含：
  - 量纲定义（UnitDimension）CRUD 接口
  - 单位（Unit）CRUD 接口
  - 单位换算（UnitConversion）CRUD 接口 + 换算计算接口
  - 资源分类（ResourceCategory）CRUD 接口 + 树形查询接口
  - 属性定义（AttrDefinition）CRUD 接口

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
    AttrDefinitionCreate,
    AttrDefinitionResponse,
    AttrDefinitionUpdate,
    ResourceCategoryCreate,
    ResourceCategoryResponse,
    ResourceCategoryTreeResponse,
    ResourceCategoryUpdate,
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
    AttrDefinitionService,
    ResourceCategoryService,
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


# ═══════════════════════════════════════════════════════════════════════════════
# 四、资源分类接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/categories",
    response_model=PageResult[ResourceCategoryResponse],
    summary="查询资源分类列表",
    description="支持按关键字、资源类型、父分类、是否启用筛选，分页返回。",
)
def list_categories(
    keyword: str | None = Query(None, description="分类名称或编码关键字"),
    resource_type: str | None = Query(None, description="资源类型"),
    parent_id: int | None = Query(None, description="父分类 ID"),
    is_active: bool | None = Query(None, description="是否启用"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/dict-templates", "read")),
) -> PageResult[ResourceCategoryResponse]:
    return ResourceCategoryService(db).list(
        keyword=keyword,
        resource_type=resource_type,
        parent_id=parent_id,
        is_active=is_active,
        page=page,
        size=size,
    )


@router.get(
    "/categories/tree",
    response_model=list[ResourceCategoryTreeResponse],
    summary="获取资源分类树",
    description="返回树状结构的分类列表，供前端级联选择器使用。",
)
def get_category_tree(
    resource_type: str | None = Query(None, description="资源类型"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/dict-templates", "read")),
) -> list[ResourceCategoryTreeResponse]:
    tree_data = ResourceCategoryService(db).get_tree(resource_type=resource_type)
    return [ResourceCategoryTreeResponse(**node) for node in tree_data]


@router.post(
    "/categories",
    response_model=ResourceCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建资源分类",
)
def create_category(
    payload: ResourceCategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "write")),
) -> ResourceCategoryResponse:
    operator = str(current_user.id)
    result = ResourceCategoryService(db).create(payload, operator)
    _commit_write(db)
    return result


@router.get(
    "/categories/{category_id}",
    response_model=ResourceCategoryResponse,
    summary="获取资源分类详情",
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/dict-templates", "read")),
) -> ResourceCategoryResponse:
    return ResourceCategoryService(db).get(category_id)


@router.put(
    "/categories/{category_id}",
    response_model=ResourceCategoryResponse,
    summary="更新资源分类",
)
def update_category(
    category_id: int,
    payload: ResourceCategoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "write")),
) -> ResourceCategoryResponse:
    operator = str(current_user.id)
    result = ResourceCategoryService(db).update(category_id, payload, operator)
    _commit_write(db)
    return result


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除资源分类",
)
def delete_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "delete")),
) -> None:
    operator = str(current_user.id)
    ResourceCategoryService(db).delete(category_id, operator)
    _commit_write(db)


# ═══════════════════════════════════════════════════════════════════════════════
# 五、属性定义接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/attributes",
    response_model=PageResult[AttrDefinitionResponse],
    summary="查询属性定义列表",
    description="支持按关键字、数据类型、适用资源类型筛选，分页返回。",
)
def list_attributes(
    keyword: str | None = Query(None, description="属性名称或编码关键字"),
    data_type: str | None = Query(None, description="数据类型"),
    resource_type: str | None = Query(None, description="适用资源类型"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/dict-templates", "read")),
) -> PageResult[AttrDefinitionResponse]:
    return AttrDefinitionService(db).list(
        keyword=keyword,
        data_type=data_type,
        resource_type=resource_type,
        page=page,
        size=size,
    )


@router.post(
    "/attributes",
    response_model=AttrDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建属性定义",
)
def create_attribute(
    payload: AttrDefinitionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "write")),
) -> AttrDefinitionResponse:
    operator = str(current_user.id)
    result = AttrDefinitionService(db).create(payload, operator)
    _commit_write(db)
    return result


@router.get(
    "/attributes/{attr_id}",
    response_model=AttrDefinitionResponse,
    summary="获取属性定义详情",
)
def get_attribute(
    attr_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/master-data/dict-templates", "read")),
) -> AttrDefinitionResponse:
    return AttrDefinitionService(db).get(attr_id)


@router.put(
    "/attributes/{attr_id}",
    response_model=AttrDefinitionResponse,
    summary="更新属性定义",
)
def update_attribute(
    attr_id: int,
    payload: AttrDefinitionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "write")),
) -> AttrDefinitionResponse:
    operator = str(current_user.id)
    result = AttrDefinitionService(db).update(attr_id, payload, operator)
    _commit_write(db)
    return result


@router.delete(
    "/attributes/{attr_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除属性定义",
)
def delete_attribute(
    attr_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/dict-templates", "delete")),
) -> None:
    operator = str(current_user.id)
    AttrDefinitionService(db).delete(attr_id, operator)
    _commit_write(db)
