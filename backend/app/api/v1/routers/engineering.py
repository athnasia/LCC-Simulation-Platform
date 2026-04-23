"""
工程建模域 REST API 路由

包含：
  - 项目管理接口
  - 产品管理接口
  - 设计方案管理接口
  - 设计方案版本管理接口
  - BOM 节点管理接口
  - 工艺路线管理接口
  - 路线步骤管理接口
  - 模型快照管理接口

设计约定：
  1. 严格遵循 RESTful API 设计风格
  2. 使用 Pydantic Schemas 进行进出参校验
  3. 统一使用 Depends(get_db) 注入数据库 Session
  4. 增删改操作必须在末尾调用 db.commit()
  5. 异常处理必须转化为合适的 HTTP 状态码
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db, require_permission
from app.models.system import SysUser
from app.schemas.common import PageResult
from app.schemas.engineering import (
    BomNodeCreate,
    BomNodeResponse,
    BomNodeTreeResponse,
    BomNodeUpdate,
    ComponentProcessRouteCreate,
    ComponentProcessRouteResponse,
    ComponentProcessRouteUpdate,
    DesignSchemeCreate,
    DesignSchemeResponse,
    DesignSchemeUpdate,
    DesignSchemeVersionCreate,
    DesignSchemeVersionResponse,
    DesignSchemeVersionUpdate,
    GenerateSnapshotRequest,
    GenerateSnapshotResponse,
    ModelSnapshotCreate,
    ModelSnapshotResponse,
    ModelSnapshotUpdate,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    RouteStepBindCreate,
    RouteStepBindResponse,
    RouteStepBindUpdate,
    RouteStepBindWithProcessResponse,
)
from app.services.engineering_service import (
    BomNodeService,
    ComponentProcessRouteService,
    DesignSchemeService,
    DesignSchemeVersionService,
    ModelSnapshotService,
    ProductService,
    ProjectService,
    RouteStepBindService,
)
from app.services.system_service import AuditLogService

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# 一、项目管理接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/projects", response_model=PageResult[ProjectResponse])
def list_projects(
    keyword: str | None = Query(None, description="关键字搜索"),
    is_active: bool | None = Query(None, description="是否启用"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/projects", "read")),
) -> PageResult[ProjectResponse]:
    """获取项目列表"""
    return ProjectService(db).list(
        keyword=keyword,
        is_active=is_active,
        page=page,
        size=size,
    )


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/projects", "write")),
) -> ProjectResponse:
    """创建项目"""
    project = ProjectService(db).create(payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="PROJECT",
        resource_id=project.id,
        detail={"name": project.name, "code": project.code},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return project


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/projects", "read")),
) -> ProjectResponse:
    """获取项目详情"""
    return ProjectService(db).detail(project_id)


@router.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/projects", "write")),
) -> ProjectResponse:
    """更新项目"""
    project = ProjectService(db).update(project_id, payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="PROJECT",
        resource_id=project.id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/projects", "delete")),
) -> None:
    """删除项目"""
    ProjectService(db).delete(project_id, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="PROJECT",
        resource_id=project_id,
        detail={},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# 二、产品管理接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/products", response_model=PageResult[ProductResponse])
def list_products(
    keyword: str | None = Query(None, description="关键字搜索"),
    project_id: int | None = Query(None, description="项目 ID"),
    is_active: bool | None = Query(None, description="是否启用"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/products", "read")),
) -> PageResult[ProductResponse]:
    """获取产品列表"""
    return ProductService(db).list(
        keyword=keyword,
        project_id=project_id,
        is_active=is_active,
        page=page,
        size=size,
    )


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/products", "write")),
) -> ProductResponse:
    """创建产品"""
    product = ProductService(db).create(payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="PRODUCT",
        resource_id=product.id,
        detail={"name": product.name, "code": product.code},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return product


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/products", "read")),
) -> ProductResponse:
    """获取产品详情"""
    return ProductService(db).detail(product_id)


@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/products", "write")),
) -> ProductResponse:
    """更新产品"""
    product = ProductService(db).update(product_id, payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="PRODUCT",
        resource_id=product.id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/products", "delete")),
) -> None:
    """删除产品"""
    ProductService(db).delete(product_id, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="PRODUCT",
        resource_id=product_id,
        detail={},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# 三、设计方案管理接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/schemes", response_model=PageResult[DesignSchemeResponse])
def list_schemes(
    keyword: str | None = Query(None, description="关键字搜索"),
    product_id: int | None = Query(None, description="产品 ID"),
    is_active: bool | None = Query(None, description="是否启用"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/schemes", "read")),
) -> PageResult[DesignSchemeResponse]:
    """获取设计方案列表"""
    return DesignSchemeService(db).list(
        keyword=keyword,
        product_id=product_id,
        is_active=is_active,
        page=page,
        size=size,
    )


@router.post("/schemes", response_model=DesignSchemeResponse, status_code=status.HTTP_201_CREATED)
def create_scheme(
    payload: DesignSchemeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/schemes", "write")),
) -> DesignSchemeResponse:
    """创建设计方案"""
    scheme = DesignSchemeService(db).create(payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="DESIGN_SCHEME",
        resource_id=scheme.id,
        detail={"name": scheme.name, "code": scheme.code},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return scheme


@router.get("/schemes/{scheme_id}", response_model=DesignSchemeResponse)
def get_scheme(
    scheme_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/schemes", "read")),
) -> DesignSchemeResponse:
    """获取设计方案详情"""
    return DesignSchemeService(db).detail(scheme_id)


@router.put("/schemes/{scheme_id}", response_model=DesignSchemeResponse)
def update_scheme(
    scheme_id: int,
    payload: DesignSchemeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/schemes", "write")),
) -> DesignSchemeResponse:
    """更新设计方案"""
    scheme = DesignSchemeService(db).update(scheme_id, payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="DESIGN_SCHEME",
        resource_id=scheme.id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return scheme


@router.delete("/schemes/{scheme_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheme(
    scheme_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/schemes", "delete")),
) -> None:
    """删除设计方案"""
    DesignSchemeService(db).delete(scheme_id, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="DESIGN_SCHEME",
        resource_id=scheme_id,
        detail={},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# 四、设计方案版本管理接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/scheme-versions", response_model=PageResult[DesignSchemeVersionResponse])
def list_scheme_versions(
    keyword: str | None = Query(None, description="关键字搜索"),
    scheme_id: int | None = Query(None, description="方案 ID"),
    status: str | None = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/scheme-versions", "read")),
) -> PageResult[DesignSchemeVersionResponse]:
    """获取设计方案版本列表"""
    return DesignSchemeVersionService(db).list(
        keyword=keyword,
        scheme_id=scheme_id,
        status=status,
        page=page,
        size=size,
    )


@router.post("/scheme-versions", response_model=DesignSchemeVersionResponse, status_code=status.HTTP_201_CREATED)
def create_scheme_version(
    payload: DesignSchemeVersionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/scheme-versions", "write")),
) -> DesignSchemeVersionResponse:
    """创建设计方案版本"""
    version = DesignSchemeVersionService(db).create(payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="DESIGN_SCHEME_VERSION",
        resource_id=version.id,
        detail={"version": version.version, "scheme_id": version.scheme_id},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return version


@router.get("/scheme-versions/{version_id}", response_model=DesignSchemeVersionResponse)
def get_scheme_version(
    version_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/scheme-versions", "read")),
) -> DesignSchemeVersionResponse:
    """获取设计方案版本详情"""
    return DesignSchemeVersionService(db).detail(version_id)


@router.put("/scheme-versions/{version_id}", response_model=DesignSchemeVersionResponse)
def update_scheme_version(
    version_id: int,
    payload: DesignSchemeVersionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/scheme-versions", "write")),
) -> DesignSchemeVersionResponse:
    """更新设计方案版本"""
    version = DesignSchemeVersionService(db).update(version_id, payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="DESIGN_SCHEME_VERSION",
        resource_id=version.id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return version


@router.delete("/scheme-versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheme_version(
    version_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/scheme-versions", "delete")),
) -> None:
    """删除设计方案版本"""
    DesignSchemeVersionService(db).delete(version_id, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="DESIGN_SCHEME_VERSION",
        resource_id=version_id,
        detail={},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()


@router.post("/scheme-versions/{version_id}/release", response_model=DesignSchemeVersionResponse)
def release_scheme_version(
    version_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/scheme-versions", "write")),
) -> DesignSchemeVersionResponse:
    """发布设计方案版本"""
    version = DesignSchemeVersionService(db).release(version_id, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="RELEASE",
        resource_type="DESIGN_SCHEME_VERSION",
        resource_id=version.id,
        detail={"version": version.version},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return version


# ═══════════════════════════════════════════════════════════════════════════════
# 五、BOM 节点管理接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/bom-nodes", response_model=PageResult[BomNodeResponse])
def list_bom_nodes(
    scheme_version_id: int | None = Query(None, description="方案版本 ID"),
    parent_id: int | None = Query(None, description="父节点 ID"),
    node_type: str | None = Query(None, description="节点类型"),
    is_configured: bool | None = Query(None, description="是否已配置"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/bom-nodes", "read")),
) -> PageResult[BomNodeResponse]:
    """获取 BOM 节点列表"""
    return BomNodeService(db).list(
        scheme_version_id=scheme_version_id,
        parent_id=parent_id,
        node_type=node_type,
        is_configured=is_configured,
        page=page,
        size=size,
    )


@router.get("/bom-nodes/tree", response_model=list[BomNodeTreeResponse])
def get_bom_tree(
    scheme_version_id: int = Query(..., description="方案版本 ID"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/bom-nodes", "read")),
) -> list[BomNodeTreeResponse]:
    """获取 BOM 树形结构"""
    return BomNodeService(db).get_tree(scheme_version_id)


@router.post("/bom-nodes", response_model=BomNodeResponse, status_code=status.HTTP_201_CREATED)
def create_bom_node(
    payload: BomNodeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/bom-nodes", "write")),
) -> BomNodeResponse:
    """创建 BOM 节点"""
    node = BomNodeService(db).create(payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="BOM_NODE",
        resource_id=node.id,
        detail={"name": node.node_name, "code": node.code},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return node


@router.get("/bom-nodes/{node_id}", response_model=BomNodeResponse)
def get_bom_node(
    node_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/bom-nodes", "read")),
) -> BomNodeResponse:
    """获取 BOM 节点详情"""
    return BomNodeService(db).detail(node_id)


@router.put("/bom-nodes/{node_id}", response_model=BomNodeResponse)
def update_bom_node(
    node_id: int,
    payload: BomNodeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/bom-nodes", "write")),
) -> BomNodeResponse:
    """更新 BOM 节点"""
    node = BomNodeService(db).update(node_id, payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="BOM_NODE",
        resource_id=node.id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return node


@router.delete("/bom-nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bom_node(
    node_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/bom-nodes", "delete")),
) -> None:
    """删除 BOM 节点"""
    BomNodeService(db).delete(node_id, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="BOM_NODE",
        resource_id=node_id,
        detail={},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# 六、工艺路线管理接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/process-routes", response_model=PageResult[ComponentProcessRouteResponse])
def list_process_routes(
    bom_node_id: int | None = Query(None, description="BOM 节点 ID"),
    is_active: bool | None = Query(None, description="是否启用"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/process-routes", "read")),
) -> PageResult[ComponentProcessRouteResponse]:
    """获取工艺路线列表"""
    return ComponentProcessRouteService(db).list(
        bom_node_id=bom_node_id,
        is_active=is_active,
        page=page,
        size=size,
    )


@router.post("/process-routes", response_model=ComponentProcessRouteResponse, status_code=status.HTTP_201_CREATED)
def create_process_route(
    payload: ComponentProcessRouteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/process-routes", "write")),
) -> ComponentProcessRouteResponse:
    """创建工艺路线"""
    route = ComponentProcessRouteService(db).create(payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="PROCESS_ROUTE",
        resource_id=route.id,
        detail={"name": route.route_name, "code": route.route_code},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return route


@router.get("/process-routes/{route_id}", response_model=ComponentProcessRouteResponse)
def get_process_route(
    route_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/process-routes", "read")),
) -> ComponentProcessRouteResponse:
    """获取工艺路线详情"""
    return ComponentProcessRouteService(db).detail(route_id)


@router.put("/process-routes/{route_id}", response_model=ComponentProcessRouteResponse)
def update_process_route(
    route_id: int,
    payload: ComponentProcessRouteUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/process-routes", "write")),
) -> ComponentProcessRouteResponse:
    """更新工艺路线"""
    route = ComponentProcessRouteService(db).update(route_id, payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="PROCESS_ROUTE",
        resource_id=route.id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return route


@router.delete("/process-routes/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_process_route(
    route_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/process-routes", "delete")),
) -> None:
    """删除工艺路线"""
    ComponentProcessRouteService(db).delete(route_id, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="PROCESS_ROUTE",
        resource_id=route_id,
        detail={},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# 七、路线步骤管理接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/route-steps", response_model=PageResult[RouteStepBindResponse])
def list_route_steps(
    route_id: int | None = Query(None, description="路线 ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/route-steps", "read")),
) -> PageResult[RouteStepBindResponse]:
    """获取路线步骤列表"""
    return RouteStepBindService(db).list(
        route_id=route_id,
        page=page,
        size=size,
    )


@router.get("/route-steps/with-process/{route_id}", response_model=list[RouteStepBindWithProcessResponse])
def list_route_steps_with_process(
    route_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/route-steps", "read")),
) -> list[RouteStepBindWithProcessResponse]:
    """获取路线步骤列表（包含标准工艺信息）"""
    return RouteStepBindService(db).list_with_process(route_id)


@router.post("/route-steps", response_model=RouteStepBindResponse, status_code=status.HTTP_201_CREATED)
def create_route_step(
    payload: RouteStepBindCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/route-steps", "write")),
) -> RouteStepBindResponse:
    """创建路线步骤"""
    step = RouteStepBindService(db).create(payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="ROUTE_STEP",
        resource_id=step.id,
        detail={"route_id": step.route_id, "process_id": step.process_id, "step_order": step.step_order},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return step


@router.get("/route-steps/{step_id}", response_model=RouteStepBindResponse)
def get_route_step(
    step_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/route-steps", "read")),
) -> RouteStepBindResponse:
    """获取路线步骤详情"""
    return RouteStepBindService(db).detail(step_id)


@router.put("/route-steps/{step_id}", response_model=RouteStepBindResponse)
def update_route_step(
    step_id: int,
    payload: RouteStepBindUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/route-steps", "write")),
) -> RouteStepBindResponse:
    """更新路线步骤（参数覆写）"""
    step = RouteStepBindService(db).update(step_id, payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="ROUTE_STEP",
        resource_id=step.id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return step


@router.delete("/route-steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route_step(
    step_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/route-steps", "delete")),
) -> None:
    """删除路线步骤"""
    RouteStepBindService(db).delete(step_id, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="ROUTE_STEP",
        resource_id=step_id,
        detail={},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()


@router.post("/route-steps/reorder", status_code=status.HTTP_204_NO_CONTENT)
def reorder_route_steps(
    route_id: int = Query(..., description="路线 ID"),
    step_ids: list[int] = Query(..., description="步骤 ID 列表（按新顺序）"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/route-steps", "write")),
) -> None:
    """重新排序路线步骤"""
    RouteStepBindService(db).reorder(route_id, step_ids, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="REORDER",
        resource_type="ROUTE_STEPS",
        resource_id=route_id,
        detail={"step_ids": step_ids},
        ip_address=request.client.host if request else None,
    )
    
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# 八、模型快照管理接口
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/snapshots", response_model=PageResult[ModelSnapshotResponse])
def list_snapshots(
    scheme_version_id: int | None = Query(None, description="方案版本 ID"),
    status: str | None = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=500, description="每页数量"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/snapshots", "read")),
) -> PageResult[ModelSnapshotResponse]:
    """获取模型快照列表"""
    return ModelSnapshotService(db).list(
        scheme_version_id=scheme_version_id,
        status=status,
        page=page,
        size=size,
    )


@router.post("/snapshots", response_model=ModelSnapshotResponse, status_code=status.HTTP_201_CREATED)
def create_snapshot(
    payload: ModelSnapshotCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/snapshots", "write")),
) -> ModelSnapshotResponse:
    """创建模型快照"""
    snapshot = ModelSnapshotService(db).create(payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="MODEL_SNAPSHOT",
        resource_id=snapshot.id,
        detail={"name": snapshot.snapshot_name, "code": snapshot.snapshot_code},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return snapshot


@router.post("/snapshots/generate", response_model=GenerateSnapshotResponse, status_code=status.HTTP_201_CREATED)
def generate_snapshot(
    payload: GenerateSnapshotRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/snapshots", "write")),
) -> GenerateSnapshotResponse:
    """生成可计算快照（核心算力枢纽）"""
    snapshot = ModelSnapshotService(db).generate(payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="GENERATE_SNAPSHOT",
        resource_type="MODEL_SNAPSHOT",
        resource_id=snapshot.snapshot_id,
        detail={
            "snapshot_code": snapshot.snapshot_code,
            "snapshot_name": snapshot.snapshot_name,
            "scheme_version_id": payload.scheme_version_id,
        },
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return snapshot


@router.get("/snapshots/{snapshot_id}", response_model=ModelSnapshotResponse)
def get_snapshot(
    snapshot_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/snapshots", "read")),
) -> ModelSnapshotResponse:
    """获取模型快照详情"""
    return ModelSnapshotService(db).detail(snapshot_id)


@router.put("/snapshots/{snapshot_id}", response_model=ModelSnapshotResponse)
def update_snapshot(
    snapshot_id: int,
    payload: ModelSnapshotUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/snapshots", "write")),
) -> ModelSnapshotResponse:
    """更新模型快照"""
    snapshot = ModelSnapshotService(db).update(snapshot_id, payload, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="MODEL_SNAPSHOT",
        resource_id=snapshot.id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    return snapshot


@router.delete("/snapshots/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_snapshot(
    snapshot_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/snapshots", "delete")),
) -> None:
    """删除模型快照"""
    ModelSnapshotService(db).delete(snapshot_id, current_user.username)
    
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="MODEL_SNAPSHOT",
        resource_id=snapshot_id,
        detail={},
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
