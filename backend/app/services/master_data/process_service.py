from __future__ import annotations
from collections import defaultdict
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.models.master_data import (
    MdProcess,
    MdProcessResource,
    MdMaterial,
    MdEquipment,
    MdLabor,
    ResourceType,
)
from app.schemas.common import PageResult
from app.schemas.master_data import (
    ProcessCloneRequest,
    ProcessCreate,
    ProcessResourceCreate,
    ProcessResourceResponse,
    ProcessResponse,
    ProcessUpdate,
)
from .base import _build_deleted_unique_value

class ProcessService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, process_id: int) -> MdProcess:
        process = self.db.execute(
            select(MdProcess).where(
                MdProcess.id == process_id,
                MdProcess.is_deleted == False,
            )
            .options(
                selectinload(MdProcess.category),
                selectinload(MdProcess.resources),
            )
        ).scalar_one_or_none()
        if process is None:
            raise ResourceNotFoundError(resource="标准工艺", identifier=process_id)
        return process

    def _assert_code_unique(self, code: str, exclude_id: int | None = None) -> None:
        stmt = select(MdProcess).where(
            MdProcess.code == code,
            MdProcess.is_deleted == False,
        )
        if exclude_id is not None:
            stmt = stmt.where(MdProcess.id != exclude_id)
        exists = self.db.execute(stmt).scalar_one_or_none()
        if exists is not None:
            raise BusinessRuleViolationError(
                error_code="PROCESS_CODE_DUPLICATE",
                message=f"工艺编码已存在：{code}",
            )

    def list(
        self,
        keyword: str | None = None,
        category_id: int | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[ProcessResponse]:
        stmt = select(MdProcess).where(MdProcess.is_deleted == False)

        if keyword:
            stmt = stmt.where(
                or_(
                    MdProcess.name.ilike(f"%{keyword}%"),
                    MdProcess.code.ilike(f"%{keyword}%"),
                )
            )
        if category_id is not None:
            stmt = stmt.where(MdProcess.category_id == category_id)
        if is_active is not None:
            stmt = stmt.where(MdProcess.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.options(
            selectinload(MdProcess.category),
            selectinload(MdProcess.resources),
        )
        stmt = stmt.order_by(MdProcess.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult(
            items=[ProcessResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    def get(self, process_id: int) -> ProcessResponse:
        process = self._get_or_404(process_id)
        return ProcessResponse.model_validate(process)

    def _fetch_resource_names_batch(
        self, resources: list[tuple[ResourceType, int]]
    ) -> dict[tuple[ResourceType, int], str | None]:
        """
        批量获取资源名称（优化版：避免 N+1 查询）
        
        Args:
            resources: 资源列表，每个元素为 (resource_type, resource_id)
        
        Returns:
            字典，key 为 (resource_type, resource_id)，value 为资源名称
        """
        result: dict[tuple[ResourceType, int], str | None] = {}
        
        by_type: dict[ResourceType, list[int]] = defaultdict(list)
        for resource_type, resource_id in resources:
            by_type[resource_type].append(resource_id)
        
        if ResourceType.MATERIAL in by_type:
            material_ids = by_type[ResourceType.MATERIAL]
            stmt = select(MdMaterial.id, MdMaterial.name).where(
                MdMaterial.id.in_(material_ids)
            )
            rows = self.db.execute(stmt).all()
            for row in rows:
                result[(ResourceType.MATERIAL, row[0])] = row[1]
        
        if ResourceType.EQUIPMENT in by_type:
            equipment_ids = by_type[ResourceType.EQUIPMENT]
            stmt = select(MdEquipment.id, MdEquipment.name).where(
                MdEquipment.id.in_(equipment_ids)
            )
            rows = self.db.execute(stmt).all()
            for row in rows:
                result[(ResourceType.EQUIPMENT, row[0])] = row[1]
        
        if ResourceType.LABOR in by_type:
            labor_ids = by_type[ResourceType.LABOR]
            stmt = select(MdLabor.id, MdLabor.name).where(
                MdLabor.id.in_(labor_ids)
            )
            rows = self.db.execute(stmt).all()
            for row in rows:
                result[(ResourceType.LABOR, row[0])] = row[1]
        
        for resource_type, resource_id in resources:
            if (resource_type, resource_id) not in result:
                result[(resource_type, resource_id)] = None
        
        return result

    def create(self, payload: ProcessCreate, operator: str) -> ProcessResponse:
        self._assert_code_unique(payload.code)

        if payload.category_id is None:
            raise BusinessRuleViolationError(
                error_code="PROCESS_CATEGORY_REQUIRED",
                message="工艺分类不能为空",
            )

        process = MdProcess(
            **payload.model_dump(exclude={"resources"}),
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(process)
        self.db.flush()

        if payload.resources:
            resource_keys = [
                (res.resource_type, res.resource_id)
                for res in payload.resources
            ]
            resource_names = self._fetch_resource_names_batch(resource_keys)
            
            for resource_data in payload.resources:
                resource_name = resource_names.get(
                    (resource_data.resource_type, resource_data.resource_id)
                )
                
                resource = MdProcessResource(
                    process_id=process.id,
                    **resource_data.model_dump(),
                    resource_name=resource_name,
                    created_by=operator,
                    updated_by=operator,
                )
                self.db.add(resource)
            self.db.flush()

        process = self.db.execute(
            select(MdProcess)
            .where(MdProcess.id == process.id)
            .options(
                selectinload(MdProcess.category),
                selectinload(MdProcess.resources),
            )
        ).scalar_one()
        return ProcessResponse.model_validate(process)

    def update(
        self, process_id: int, payload: ProcessUpdate, operator: str
    ) -> ProcessResponse:
        process = self._get_or_404(process_id)

        update_data = payload.model_dump(exclude_unset=True)
        if "category_id" in update_data and update_data["category_id"] is None:
            raise BusinessRuleViolationError(
                error_code="PROCESS_CATEGORY_REQUIRED",
                message="工艺分类不能为空",
            )
        for field, value in update_data.items():
            setattr(process, field, value)
        process.updated_by = operator
        self.db.flush()

        process = self.db.execute(
            select(MdProcess)
            .where(MdProcess.id == process_id)
            .options(
                selectinload(MdProcess.category),
                selectinload(MdProcess.resources),
            )
        ).scalar_one()
        return ProcessResponse.model_validate(process)

    def delete(self, process_id: int, operator: str) -> None:
        process = self._get_or_404(process_id)

        process.code = _build_deleted_unique_value(process.code, process.id, 50)
        process.is_deleted = True
        process.updated_by = operator
        self.db.flush()

    def clone(self, process_id: int, payload: ProcessCloneRequest, operator: str) -> ProcessResponse:
        """复制工序及其资源挂载包（使用批量插入优化性能）"""
        source = self._get_or_404(process_id)
        self._assert_code_unique(payload.new_code)

        new_process = MdProcess(
            name=payload.new_name,
            code=payload.new_code,
            category_id=source.category_id,
            standard_time=source.standard_time,
            setup_time=source.setup_time,
            is_active=True,
            description=source.description,
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(new_process)
        self.db.flush()

        if payload.copy_resources and source.resources:
            new_resources = []
            for resource in source.resources:
                if resource.is_deleted:
                    continue
                new_resources.append(MdProcessResource(
                    process_id=new_process.id,
                    resource_type=resource.resource_type,
                    resource_id=resource.resource_id,
                    quantity=resource.quantity,
                    resource_name=resource.resource_name,
                    description=resource.description,
                    created_by=operator,
                    updated_by=operator,
                ))
            self.db.add_all(new_resources)
            self.db.flush()

        new_process = self.db.execute(
            select(MdProcess)
            .where(MdProcess.id == new_process.id)
            .options(
                selectinload(MdProcess.category),
                selectinload(MdProcess.resources),
            )
        ).scalar_one()
        return ProcessResponse.model_validate(new_process)

    def add_resource(
        self, process_id: int, payload: ProcessResourceCreate, operator: str
    ) -> ProcessResourceResponse:
        """为工序添加资源挂载"""
        process = self._get_or_404(process_id)

        existing = self.db.execute(
            select(MdProcessResource).where(
                MdProcessResource.process_id == process_id,
                MdProcessResource.resource_type == payload.resource_type,
                MdProcessResource.resource_id == payload.resource_id,
                MdProcessResource.is_deleted == False,
            )
        ).scalar_one_or_none()

        if existing:
            raise BusinessRuleViolationError(
                error_code="PROCESS_RESOURCE_DUPLICATE",
                message=f"该工序已挂载此资源（类型：{payload.resource_type.value}，ID：{payload.resource_id}），请勿重复添加",
            )

        resource_name = self._fetch_resource_name(payload.resource_type, payload.resource_id)

        resource = MdProcessResource(
            process_id=process_id,
            **payload.model_dump(),
            resource_name=resource_name,
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(resource)
        self.db.flush()

        return ProcessResourceResponse.model_validate(resource)

    def remove_resource(self, process_id: int, resource_id: int, operator: str) -> None:
        """移除工序的资源挂载 (L-6: 改为逻辑删除)"""
        resource = self.db.execute(
            select(MdProcessResource).where(
                MdProcessResource.id == resource_id,
                MdProcessResource.process_id == process_id,
                MdProcessResource.is_deleted == False,
            )
        ).scalar_one_or_none()
        if resource is None:
            raise ResourceNotFoundError(resource="工序资源挂载", identifier=resource_id)
        
        resource.is_deleted = True
        resource.updated_by = operator
        self.db.flush()

    def _fetch_resource_name(self, resource_type: ResourceType, resource_id: int) -> str | None:
        """辅助方法：获取单个资源名称快照"""
        if resource_type == ResourceType.MATERIAL:
            stmt = select(MdMaterial.name).where(MdMaterial.id == resource_id)
        elif resource_type == ResourceType.EQUIPMENT:
            stmt = select(MdEquipment.name).where(MdEquipment.id == resource_id)
        elif resource_type == ResourceType.LABOR:
            stmt = select(MdLabor.name).where(MdLabor.id == resource_id)
        else:
            return None
        
        return self.db.execute(stmt).scalar_one_or_none()
