"""
工程建模域业务逻辑服务

包含：
  - 项目、产品、设计方案、版本管理
  - BOM 树管理（树形结构查询、柔性属性处理）
  - 工艺路线与资源覆写管理（工序重排、参数覆写）
  - 模型快照生成（核心算力枢纽）

设计约定：
  1. 所有方法必须在事务边界内执行
  2. 快照生成必须跨域拉取主数据并硬拷贝固化
  3. 所有业务规则校验必须在 Service 层完成
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select, and_
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.models.engineering import (
    EngBomNode,
    EngComponentProcessRoute,
    EngDesignScheme,
    EngDesignSchemeVersion,
    EngModelSnapshot,
    EngProduct,
    EngProject,
    EngRouteStepBind,
)
from app.models.master_data import MdEquipment, MdLabor, MdMaterial, MdProcess
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


# ═══════════════════════════════════════════════════════════════════════════════
# 一、项目管理服务
# ═══════════════════════════════════════════════════════════════════════════════

class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, project_id: int) -> EngProject:
        project = self.db.execute(
            select(EngProject).where(
                EngProject.id == project_id,
                EngProject.is_deleted == False,
            )
        ).scalar_one_or_none()
        if project is None:
            raise ResourceNotFoundError(resource="项目", identifier=project_id)
        return project

    def list(
        self,
        keyword: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[ProjectResponse]:
        stmt = select(EngProject).where(EngProject.is_deleted == False)

        if keyword:
            stmt = stmt.where(
                or_(
                    EngProject.name.ilike(f"%{keyword}%"),
                    EngProject.code.ilike(f"%{keyword}%"),
                )
            )
        
        if is_active is not None:
            stmt = stmt.where(EngProject.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(EngProject.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult(
            items=[ProjectResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=max(1, (total + size - 1) // size) if total > 0 else 1,
        )

    def create(self, payload: ProjectCreate, operator: str) -> ProjectResponse:
        project = EngProject(**payload.model_dump(), created_by=operator, updated_by=operator)
        self.db.add(project)
        self.db.flush()
        return ProjectResponse.model_validate(project)

    def detail(self, project_id: int) -> ProjectResponse:
        project = self._get_or_404(project_id)
        return ProjectResponse.model_validate(project)

    def update(self, project_id: int, payload: ProjectUpdate, operator: str) -> ProjectResponse:
        project = self._get_or_404(project_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        project.updated_by = operator
        self.db.flush()
        return ProjectResponse.model_validate(project)

    def delete(self, project_id: int, operator: str) -> None:
        project = self._get_or_404(project_id)
        project.is_deleted = int(datetime.now().timestamp())
        project.updated_by = operator
        self.db.flush()


# ═══════════════════════════════════════════════════════════════════════════════
# 二、产品管理服务
# ═══════════════════════════════════════════════════════════════════════════════

class ProductService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, product_id: int) -> EngProduct:
        product = self.db.execute(
            select(EngProduct).where(
                EngProduct.id == product_id,
                EngProduct.is_deleted == False,
            )
        ).scalar_one_or_none()
        if product is None:
            raise ResourceNotFoundError(resource="产品", identifier=product_id)
        return product

    def list(
        self,
        keyword: str | None = None,
        project_id: int | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[ProductResponse]:
        stmt = select(EngProduct).where(EngProduct.is_deleted == False)

        if keyword:
            stmt = stmt.where(
                or_(
                    EngProduct.name.ilike(f"%{keyword}%"),
                    EngProduct.code.ilike(f"%{keyword}%"),
                )
            )
        
        if project_id:
            stmt = stmt.where(EngProduct.project_id == project_id)
        
        if is_active is not None:
            stmt = stmt.where(EngProduct.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(EngProduct.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult.build(
            items=[ProductResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
        )

    def create(self, payload: ProductCreate, operator: str) -> ProductResponse:
        product = EngProduct(**payload.model_dump(), created_by=operator, updated_by=operator)
        self.db.add(product)
        self.db.flush()
        return ProductResponse.model_validate(product)

    def detail(self, product_id: int) -> ProductResponse:
        product = self._get_or_404(product_id)
        return ProductResponse.model_validate(product)

    def update(self, product_id: int, payload: ProductUpdate, operator: str) -> ProductResponse:
        product = self._get_or_404(product_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        product.updated_by = operator
        self.db.flush()
        return ProductResponse.model_validate(product)

    def delete(self, product_id: int, operator: str) -> None:
        product = self._get_or_404(product_id)
        product.is_deleted = int(datetime.now().timestamp())
        product.updated_by = operator
        self.db.flush()


# ═══════════════════════════════════════════════════════════════════════════════
# 三、设计方案管理服务
# ═══════════════════════════════════════════════════════════════════════════════

class DesignSchemeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, scheme_id: int) -> EngDesignScheme:
        scheme = self.db.execute(
            select(EngDesignScheme).where(
                EngDesignScheme.id == scheme_id,
                EngDesignScheme.is_deleted == False,
            )
        ).scalar_one_or_none()
        if scheme is None:
            raise ResourceNotFoundError(resource="设计方案", identifier=scheme_id)
        return scheme

    def list(
        self,
        keyword: str | None = None,
        product_id: int | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[DesignSchemeResponse]:
        stmt = select(EngDesignScheme).where(EngDesignScheme.is_deleted == False)

        if keyword:
            stmt = stmt.where(
                or_(
                    EngDesignScheme.name.ilike(f"%{keyword}%"),
                    EngDesignScheme.code.ilike(f"%{keyword}%"),
                )
            )
        
        if product_id:
            stmt = stmt.where(EngDesignScheme.product_id == product_id)
        
        if is_active is not None:
            stmt = stmt.where(EngDesignScheme.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(EngDesignScheme.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult.build(
            items=[DesignSchemeResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
        )

    def create(self, payload: DesignSchemeCreate, operator: str) -> DesignSchemeResponse:
        scheme = EngDesignScheme(**payload.model_dump(), created_by=operator, updated_by=operator)
        self.db.add(scheme)
        self.db.flush()
        return DesignSchemeResponse.model_validate(scheme)

    def detail(self, scheme_id: int) -> DesignSchemeResponse:
        scheme = self._get_or_404(scheme_id)
        return DesignSchemeResponse.model_validate(scheme)

    def update(self, scheme_id: int, payload: DesignSchemeUpdate, operator: str) -> DesignSchemeResponse:
        scheme = self._get_or_404(scheme_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(scheme, field, value)
        scheme.updated_by = operator
        self.db.flush()
        return DesignSchemeResponse.model_validate(scheme)

    def delete(self, scheme_id: int, operator: str) -> None:
        scheme = self._get_or_404(scheme_id)
        scheme.is_deleted = int(datetime.now().timestamp())
        scheme.updated_by = operator
        self.db.flush()


# ═══════════════════════════════════════════════════════════════════════════════
# 四、设计方案版本管理服务
# ═══════════════════════════════════════════════════════════════════════════════

class DesignSchemeVersionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, version_id: int) -> EngDesignSchemeVersion:
        version = self.db.execute(
            select(EngDesignSchemeVersion).where(
                EngDesignSchemeVersion.id == version_id,
                EngDesignSchemeVersion.is_deleted == False,
            )
        ).scalar_one_or_none()
        if version is None:
            raise ResourceNotFoundError(resource="设计方案版本", identifier=version_id)
        return version

    def list(
        self,
        keyword: str | None = None,
        scheme_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[DesignSchemeVersionResponse]:
        stmt = select(EngDesignSchemeVersion).where(EngDesignSchemeVersion.is_deleted == False)

        if scheme_id:
            stmt = stmt.where(EngDesignSchemeVersion.scheme_id == scheme_id)
        
        if status:
            stmt = stmt.where(EngDesignSchemeVersion.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(EngDesignSchemeVersion.version.desc())
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult.build(
            items=[DesignSchemeVersionResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
        )

    def create(self, payload: DesignSchemeVersionCreate, operator: str) -> DesignSchemeVersionResponse:
        clone_from_id = payload.clone_from_version_id
        version_data = payload.model_dump(exclude={'clone_from_version_id'})
        
        new_version = EngDesignSchemeVersion(**version_data, created_by=operator, updated_by=operator)
        self.db.add(new_version)
        self.db.flush()
        
        if clone_from_id:
            self._clone_version_data(clone_from_id, new_version.id, operator)
        
        return DesignSchemeVersionResponse.model_validate(new_version)
    
    def _clone_version_data(self, source_version_id: int, target_version_id: int, operator: str) -> None:
        """深拷贝版本数据：BOM 树 -> 工艺路线 -> 工序步骤"""
        from sqlalchemy import case
        
        source_nodes = self.db.execute(
            select(EngBomNode)
            .where(EngBomNode.scheme_version_id == source_version_id)
            .where(EngBomNode.is_deleted.is_(False))
            .order_by(
                case((EngBomNode.parent_id.is_(None), 0), else_=1),
                EngBomNode.parent_id.asc()
            )
        ).scalars().all()
        
        node_id_mapping: dict[int, int] = {}
        
        for source_node in source_nodes:
            attrs_copy = None
            if source_node.attributes:
                attrs_copy = json.loads(json.dumps(source_node.attributes))
            
            new_node = EngBomNode(
                scheme_version_id=target_version_id,
                parent_id=node_id_mapping.get(source_node.parent_id) if source_node.parent_id else None,
                node_name=source_node.node_name,
                code=source_node.code,
                node_type=source_node.node_type,
                quantity=source_node.quantity,
                unit_id=source_node.unit_id,
                sort_order=source_node.sort_order,
                is_configured=source_node.is_configured,
                attributes=attrs_copy,
                description=source_node.description,
                created_by=operator,
                updated_by=operator,
            )
            self.db.add(new_node)
            self.db.flush()
            node_id_mapping[source_node.id] = new_node.id
            
            self._clone_process_routes(source_node.id, new_node.id, operator)
    
    def _clone_process_routes(self, source_bom_node_id: int, target_bom_node_id: int, operator: str) -> None:
        """深拷贝工艺路线及其步骤"""
        source_routes = self.db.execute(
            select(EngComponentProcessRoute)
            .where(EngComponentProcessRoute.bom_node_id == source_bom_node_id)
            .where(EngComponentProcessRoute.is_deleted.is_(False))
        ).scalars().all()
        
        for source_route in source_routes:
            new_route = EngComponentProcessRoute(
                bom_node_id=target_bom_node_id,
                route_name=source_route.route_name,
                route_code=source_route.route_code,
                description=source_route.description,
                is_active=source_route.is_active,
                created_by=operator,
                updated_by=operator,
            )
            self.db.add(new_route)
            self.db.flush()
            
            self._clone_route_steps(source_route.id, new_route.id, operator)
    
    def _clone_route_steps(self, source_route_id: int, target_route_id: int, operator: str) -> None:
        """深拷贝工艺步骤"""
        source_steps = self.db.execute(
            select(EngRouteStepBind)
            .where(EngRouteStepBind.route_id == source_route_id)
            .where(EngRouteStepBind.is_deleted.is_(False))
            .order_by(EngRouteStepBind.step_order)
        ).scalars().all()
        
        for source_step in source_steps:
            mat_params_copy = None
            if source_step.override_mat_params:
                mat_params_copy = json.loads(json.dumps(source_step.override_mat_params))
            
            new_step = EngRouteStepBind(
                route_id=target_route_id,
                process_id=source_step.process_id,
                step_order=source_step.step_order,
                process_type=source_step.process_type,
                override_equipment_id=source_step.override_equipment_id,
                outsource_price=source_step.outsource_price,
                override_t_set=source_step.override_t_set,
                override_t_run=source_step.override_t_run,
                override_mat_params=mat_params_copy,
                description=source_step.description,
                created_by=operator,
                updated_by=operator,
            )
            self.db.add(new_step)
        
        self.db.flush()

    def detail(self, version_id: int) -> DesignSchemeVersionResponse:
        version = self._get_or_404(version_id)
        return DesignSchemeVersionResponse.model_validate(version)

    def update(self, version_id: int, payload: DesignSchemeVersionUpdate, operator: str) -> DesignSchemeVersionResponse:
        version = self._get_or_404(version_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(version, field, value)
        version.updated_by = operator
        self.db.flush()
        return DesignSchemeVersionResponse.model_validate(version)

    def delete(self, version_id: int, operator: str) -> None:
        version = self._get_or_404(version_id)
        version.is_deleted = int(datetime.now().timestamp())
        version.updated_by = operator
        self.db.flush()

    def release(self, version_id: int, operator: str) -> DesignSchemeVersionResponse:
        """发布版本"""
        version = self._get_or_404(version_id)
        version.status = "RELEASED"
        version.released_at = datetime.now()
        version.released_by = operator
        version.updated_by = operator
        self.db.flush()
        return DesignSchemeVersionResponse.model_validate(version)


# ═══════════════════════════════════════════════════════════════════════════════
# 五、BOM 节点管理服务（核心）
# ═══════════════════════════════════════════════════════════════════════════════

class BomNodeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, node_id: int) -> EngBomNode:
        node = self.db.execute(
            select(EngBomNode).where(
                EngBomNode.id == node_id,
                EngBomNode.is_deleted == False,
            )
        ).scalar_one_or_none()
        if node is None:
            raise ResourceNotFoundError(resource="BOM 节点", identifier=node_id)
        return node

    def _build_tree(self, nodes: list[EngBomNode]) -> list[BomNodeTreeResponse]:
        """构建 BOM 树形结构"""
        # 构建节点映射
        node_map: dict[int, BomNodeTreeResponse] = {}
        for node in nodes:
            node_map[node.id] = BomNodeTreeResponse.model_validate(node)
            node_map[node.id].children = []
        
        # 构建树形结构
        root_nodes = []
        for node in nodes:
            if node.parent_id is None:
                root_nodes.append(node_map[node.id])
            else:
                parent = node_map.get(node.parent_id)
                if parent:
                    parent.children.append(node_map[node.id])
        
        return root_nodes

    def list(
        self,
        scheme_version_id: int | None = None,
        parent_id: int | None = None,
        node_type: str | None = None,
        is_configured: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[BomNodeResponse]:
        stmt = select(EngBomNode).where(EngBomNode.is_deleted == False)

        if scheme_version_id:
            stmt = stmt.where(EngBomNode.scheme_version_id == scheme_version_id)
        
        if parent_id is not None:
            stmt = stmt.where(EngBomNode.parent_id == parent_id)
        
        if node_type:
            stmt = stmt.where(EngBomNode.node_type == node_type)
        
        if is_configured is not None:
            stmt = stmt.where(EngBomNode.is_configured == is_configured)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(EngBomNode.sort_order, EngBomNode.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult.build(
            items=[BomNodeResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
        )

    def get_tree(self, scheme_version_id: int) -> list[BomNodeTreeResponse]:
        """获取完整的 BOM 树形结构"""
        nodes = self.db.execute(
            select(EngBomNode)
            .where(
                EngBomNode.scheme_version_id == scheme_version_id,
                EngBomNode.is_deleted == False,
            )
            .order_by(EngBomNode.sort_order, EngBomNode.id)
        ).scalars().all()
        
        return self._build_tree(nodes)

    def create(self, payload: BomNodeCreate, operator: str) -> BomNodeResponse:
        node = EngBomNode(**payload.model_dump(), created_by=operator, updated_by=operator)
        self.db.add(node)
        self.db.flush()
        return BomNodeResponse.model_validate(node)

    def detail(self, node_id: int) -> BomNodeResponse:
        node = self._get_or_404(node_id)
        return BomNodeResponse.model_validate(node)

    def update(self, node_id: int, payload: BomNodeUpdate, operator: str) -> BomNodeResponse:
        node = self._get_or_404(node_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(node, field, value)
        node.updated_by = operator
        self.db.flush()
        return BomNodeResponse.model_validate(node)

    def delete(self, node_id: int, operator: str) -> None:
        node = self._get_or_404(node_id)
        node.is_deleted = int(datetime.now().timestamp())
        node.updated_by = operator
        self.db.flush()


# ═══════════════════════════════════════════════════════════════════════════════
# 六、工艺路线管理服务
# ═══════════════════════════════════════════════════════════════════════════════

class ComponentProcessRouteService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, route_id: int) -> EngComponentProcessRoute:
        route = self.db.execute(
            select(EngComponentProcessRoute).where(
                EngComponentProcessRoute.id == route_id,
                EngComponentProcessRoute.is_deleted == False,
            )
        ).scalar_one_or_none()
        if route is None:
            raise ResourceNotFoundError(resource="工艺路线", identifier=route_id)
        return route

    def list(
        self,
        bom_node_id: int | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[ComponentProcessRouteResponse]:
        stmt = select(EngComponentProcessRoute).where(EngComponentProcessRoute.is_deleted == False)

        if bom_node_id:
            stmt = stmt.where(EngComponentProcessRoute.bom_node_id == bom_node_id)
        
        if is_active is not None:
            stmt = stmt.where(EngComponentProcessRoute.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(EngComponentProcessRoute.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult.build(
            items=[ComponentProcessRouteResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
        )

    def create(self, payload: ComponentProcessRouteCreate, operator: str) -> ComponentProcessRouteResponse:
        route = EngComponentProcessRoute(**payload.model_dump(), created_by=operator, updated_by=operator)
        self.db.add(route)
        self.db.flush()
        return ComponentProcessRouteResponse.model_validate(route)

    def detail(self, route_id: int) -> ComponentProcessRouteResponse:
        route = self._get_or_404(route_id)
        return ComponentProcessRouteResponse.model_validate(route)

    def update(self, route_id: int, payload: ComponentProcessRouteUpdate, operator: str) -> ComponentProcessRouteResponse:
        route = self._get_or_404(route_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(route, field, value)
        route.updated_by = operator
        self.db.flush()
        return ComponentProcessRouteResponse.model_validate(route)

    def delete(self, route_id: int, operator: str) -> None:
        route = self._get_or_404(route_id)
        route.is_deleted = int(datetime.now().timestamp())
        route.updated_by = operator
        self.db.flush()


# ═══════════════════════════════════════════════════════════════════════════════
# 七、路线步骤管理服务（核心：工序重排与参数覆写）
# ═══════════════════════════════════════════════════════════════════════════════

class RouteStepBindService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, step_id: int) -> EngRouteStepBind:
        step = self.db.execute(
            select(EngRouteStepBind).where(
                EngRouteStepBind.id == step_id,
                EngRouteStepBind.is_deleted == False,
            )
            .options(selectinload(EngRouteStepBind.process))
        ).scalar_one_or_none()
        if step is None:
            raise ResourceNotFoundError(resource="路线步骤", identifier=step_id)
        return step

    def list(
        self,
        route_id: int | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[RouteStepBindResponse]:
        stmt = select(EngRouteStepBind).where(EngRouteStepBind.is_deleted == False)

        if route_id:
            stmt = stmt.where(EngRouteStepBind.route_id == route_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(EngRouteStepBind.step_order, EngRouteStepBind.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult.build(
            items=[RouteStepBindResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
        )

    def list_with_process(self, route_id: int) -> list[RouteStepBindWithProcessResponse]:
        """获取路线步骤列表（包含标准工艺信息）"""
        steps = self.db.execute(
            select(EngRouteStepBind)
            .where(
                EngRouteStepBind.route_id == route_id,
                EngRouteStepBind.is_deleted == False,
            )
            .options(selectinload(EngRouteStepBind.process))
            .order_by(EngRouteStepBind.step_order, EngRouteStepBind.id)
        ).scalars().all()
        
        return [
            RouteStepBindWithProcessResponse(
                **RouteStepBindResponse.model_validate(step).model_dump(),
                process={
                    "id": step.process.id,
                    "name": step.process.name,
                    "code": step.process.code,
                    "setup_time": float(step.process.setup_time) if step.process.setup_time else None,
                    "standard_time": float(step.process.standard_time) if step.process.standard_time else None,
                }
            )
            for step in steps
        ]

    def create(self, payload: RouteStepBindCreate, operator: str) -> RouteStepBindResponse:
        step = EngRouteStepBind(**payload.model_dump(), created_by=operator, updated_by=operator)
        self.db.add(step)
        self.db.flush()
        return RouteStepBindResponse.model_validate(step)

    def detail(self, step_id: int) -> RouteStepBindResponse:
        step = self._get_or_404(step_id)
        return RouteStepBindResponse.model_validate(step)

    def update(self, step_id: int, payload: RouteStepBindUpdate, operator: str) -> RouteStepBindResponse:
        """更新路线步骤（参数覆写）"""
        step = self._get_or_404(step_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(step, field, value)
        step.updated_by = operator
        self.db.flush()
        return RouteStepBindResponse.model_validate(step)

    def delete(self, step_id: int, operator: str) -> None:
        step = self._get_or_404(step_id)
        step.is_deleted = int(datetime.now().timestamp())
        step.updated_by = operator
        self.db.flush()

    def reorder(self, route_id: int, step_ids: list[int], operator: str) -> None:
        """重新排序路线步骤"""
        # 验证所有步骤都属于该路线
        steps = self.db.execute(
            select(EngRouteStepBind)
            .where(
                EngRouteStepBind.id.in_(step_ids),
                EngRouteStepBind.route_id == route_id,
                EngRouteStepBind.is_deleted == False,
            )
        ).scalars().all()
        
        if len(steps) != len(step_ids):
            raise BusinessRuleViolationError(
                error_code="INVALID_STEP_IDS",
                message="部分步骤不存在或不属于该路线",
            )
        
        # 批量更新顺序
        step_map = {step.id: step for step in steps}
        for index, step_id in enumerate(step_ids, start=1):
            step = step_map.get(step_id)
            if step:
                step.step_order = index
                step.updated_by = operator
        
        self.db.flush()


# ═══════════════════════════════════════════════════════════════════════════════
# 八、模型快照管理服务（核心算力枢纽）
# ═══════════════════════════════════════════════════════════════════════════════

class ModelSnapshotService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, snapshot_id: int) -> EngModelSnapshot:
        snapshot = self.db.execute(
            select(EngModelSnapshot).where(
                EngModelSnapshot.id == snapshot_id,
                EngModelSnapshot.is_deleted == False,
            )
        ).scalar_one_or_none()
        if snapshot is None:
            raise ResourceNotFoundError(resource="模型快照", identifier=snapshot_id)
        return snapshot

    def _check_all_leaf_nodes_configured(self, scheme_version_id: int) -> tuple[bool, list[str]]:
        """
        递归校验所有叶子节点是否已配置工艺路线
        
        Returns:
            tuple[bool, list[str]]: (是否全部配置, 未配置的节点名称列表)
        """
        # 获取所有 BOM 节点
        nodes = self.db.execute(
            select(EngBomNode).where(
                EngBomNode.scheme_version_id == scheme_version_id,
                EngBomNode.is_deleted == False,
            )
        ).scalars().all()
        
        # 构建父子关系映射
        children_map: dict[int | None, list[EngBomNode]] = {}
        for node in nodes:
            parent_id = node.parent_id
            if parent_id not in children_map:
                children_map[parent_id] = []
            children_map[parent_id].append(node)
        
        # 递归查找叶子节点
        unconfigured_nodes = []
        
        def find_leaf_nodes(parent_id: int | None):
            children = children_map.get(parent_id, [])
            for node in children:
                if node.id not in children_map or len(children_map[node.id]) == 0:
                    # 叶子节点
                    if not node.is_configured:
                        unconfigured_nodes.append(node.node_name)
                else:
                    # 装配节点，递归查找
                    find_leaf_nodes(node.id)
        
        find_leaf_nodes(None)
        
        return len(unconfigured_nodes) == 0, unconfigured_nodes

    def _fetch_master_data_rates(self) -> dict[str, Any]:
        """
        跨域拉取主数据费率（模拟）
        
        实际实现中，应该调用主数据域的服务：
        - 设备折旧费率
        - 人员等级费率
        - 材料最新单价
        - 能源价格
        
        Returns:
            dict: 主数据费率快照
        """
        # TODO: 实际实现中应该调用主数据域的服务
        # 这里返回模拟数据
        return {
            "equipment_rates": {
                # 设备编码 -> 折旧费率（元/h）
                "EQ_001": 50.0,
                "EQ_002": 80.0,
            },
            "labor_rates": {
                # 工种等级 -> 费率（元/h）
                "WELDER_SENIOR": 100.0,
                "WELDER_JUNIOR": 60.0,
                "ASSEMBLER_SENIOR": 80.0,
            },
            "material_prices": {
                # 材料编码 -> 单价（元/单位）
                "MAT_STEEL_PLATE": 5.0,
                "MAT_COPPER_INGOT": 50.0,
                "MAT_CUTTING_FLUID": 20.0,
            },
            "energy_prices": {
                # 能源类型 -> 单价
                "ELECTRICITY_PEAK": 1.2,
                "ELECTRICITY_VALLEY": 0.4,
            },
            "snapshot_time": datetime.now().isoformat(),
        }

    def _build_snapshot_data(self, scheme_version_id: int) -> dict[str, Any]:
        """
        构建快照数据（优化版：避免 N+1 查询）
        
        包含：
        - BOM 树结构
        - 所有工艺路线和步骤
        - 工程师覆写的参数
        - 主数据费率快照
        """
        # 1. 获取所有 BOM 节点
        bom_nodes = self.db.execute(
            select(EngBomNode).where(
                EngBomNode.scheme_version_id == scheme_version_id,
                EngBomNode.is_deleted == False,
            )
        ).scalars().all()
        
        if not bom_nodes:
            return {
                "bom_tree": [],
                "routes": [],
                "master_data_rates": self._fetch_master_data_rates(),
            }
        
        # 2. 提取所有 BOM 节点 ID
        bom_node_ids = [node.id for node in bom_nodes]
        bom_node_map = {node.id: node for node in bom_nodes}
        
        # 3. 一次性查询所有工艺路线
        routes = self.db.execute(
            select(EngComponentProcessRoute).where(
                EngComponentProcessRoute.bom_node_id.in_(bom_node_ids),
                EngComponentProcessRoute.is_deleted == False,
            )
        ).scalars().all()
        
        if not routes:
            return {
                "bom_tree": [BomNodeResponse.model_validate(node).model_dump(mode='json') for node in bom_nodes],
                "routes": [],
                "master_data_rates": self._fetch_master_data_rates(),
            }
        
        # 4. 提取所有路线 ID
        route_ids = [route.id for route in routes]
        route_map = {route.id: route for route in routes}
        
        # 5. 一次性查询所有路线步骤（包含标准工艺信息）
        steps = self.db.execute(
            select(EngRouteStepBind)
            .where(
                EngRouteStepBind.route_id.in_(route_ids),
                EngRouteStepBind.is_deleted == False,
            )
            .options(selectinload(EngRouteStepBind.process))
            .order_by(EngRouteStepBind.route_id, EngRouteStepBind.step_order)
        ).scalars().all()
        
        # 6. 在内存中构建步骤映射（route_id -> steps）
        steps_by_route: dict[int, list[EngRouteStepBind]] = {}
        for step in steps:
            if step.route_id not in steps_by_route:
                steps_by_route[step.route_id] = []
            steps_by_route[step.route_id].append(step)
        
        # 7. 在内存中构建路线映射（bom_node_id -> routes）
        routes_by_node: dict[int, list[EngComponentProcessRoute]] = {}
        for route in routes:
            if route.bom_node_id not in routes_by_node:
                routes_by_node[route.bom_node_id] = []
            routes_by_node[route.bom_node_id].append(route)
        
        # 8. 组装快照数据
        routes_data = []
        for node_id, node_routes in routes_by_node.items():
            node = bom_node_map[node_id]
            for route in node_routes:
                route_steps = steps_by_route.get(route.id, [])
                steps_data = [
                    {
                        **RouteStepBindResponse.model_validate(step).model_dump(mode='json'),
                        "process": {
                            "id": step.process.id,
                            "name": step.process.name,
                            "code": step.process.code,
                            "setup_time": float(step.process.setup_time) if step.process.setup_time else None,
                            "standard_time": float(step.process.standard_time) if step.process.standard_time else None,
                        }
                    }
                    for step in route_steps
                ]
                routes_data.append({
                    "bom_node_id": node.id,
                    "bom_node_name": node.node_name,
                    "route_id": route.id,
                    "route_name": route.route_name,
                    "steps": steps_data,
                })
        
        # 9. 跨域拉取主数据费率
        master_data_rates = self._fetch_master_data_rates()
        
        return {
            "bom_tree": [BomNodeResponse.model_validate(node).model_dump(mode='json') for node in bom_nodes],
            "routes": routes_data,
            "master_data_rates": master_data_rates,
        }

    def generate(self, payload: GenerateSnapshotRequest, operator: str) -> GenerateSnapshotResponse:
        """
        生成可计算快照（核心算力枢纽）
        
        步骤：
        1. 前置防呆校验：递归校验所有叶子节点是否已配置工艺路线
        2. 创建快照记录
        3. 构建快照数据（BOM 树、工艺路线、参数覆写、主数据费率）
        4. 硬拷贝固化
        """
        # 1. 前置防呆校验
        all_configured, unconfigured_nodes = self._check_all_leaf_nodes_configured(payload.scheme_version_id)
        
        if not all_configured:
            raise BusinessRuleViolationError(
                error_code="INCOMPLETE_CONFIGURATION",
                message=f"以下叶子节点未配置工艺路线：{', '.join(unconfigured_nodes)}",
            )
        
        # 2. 生成快照编码
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        snapshot_code = f"S_{timestamp}"
        
        # 3. 构建快照数据
        snapshot_data = self._build_snapshot_data(payload.scheme_version_id)
        
        # 4. 创建快照记录
        snapshot = EngModelSnapshot(
            scheme_version_id=payload.scheme_version_id,
            snapshot_code=snapshot_code,
            snapshot_name=payload.snapshot_name,
            snapshot_data=snapshot_data,
            status="READY",
            description=payload.description,
            created_by=operator,
            updated_by=operator,
        )
        
        self.db.add(snapshot)
        self.db.flush()
        
        return GenerateSnapshotResponse(
            snapshot_id=snapshot.id,
            snapshot_code=snapshot.snapshot_code,
            snapshot_name=snapshot.snapshot_name,
            status=snapshot.status,
            created_at=snapshot.created_at,
        )

    def list(
        self,
        scheme_version_id: int | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[ModelSnapshotResponse]:
        stmt = select(EngModelSnapshot).where(EngModelSnapshot.is_deleted == False)

        if scheme_version_id:
            stmt = stmt.where(EngModelSnapshot.scheme_version_id == scheme_version_id)
        
        if status:
            stmt = stmt.where(EngModelSnapshot.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(EngModelSnapshot.id.desc())
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult.build(
            items=[ModelSnapshotResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
        )

    def detail(self, snapshot_id: int) -> ModelSnapshotResponse:
        snapshot = self._get_or_404(snapshot_id)
        return ModelSnapshotResponse.model_validate(snapshot)

    def update(self, snapshot_id: int, payload: ModelSnapshotUpdate, operator: str) -> ModelSnapshotResponse:
        snapshot = self._get_or_404(snapshot_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(snapshot, field, value)
        snapshot.updated_by = operator
        self.db.flush()
        return ModelSnapshotResponse.model_validate(snapshot)

    def delete(self, snapshot_id: int, operator: str) -> None:
        snapshot = self._get_or_404(snapshot_id)
        snapshot.is_deleted = int(datetime.now().timestamp())
        snapshot.updated_by = operator
        self.db.flush()
