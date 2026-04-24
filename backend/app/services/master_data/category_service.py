from __future__ import annotations
from datetime import datetime
from typing import TypedDict
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.models.master_data import (
    MdEquipment,
    MdLabor,
    MdMaterial,
    MdProcess,
    MdResourceCategory,
    ResourceType,
)
from app.schemas.common import PageResult
from app.schemas.master_data import (
    ResourceCategoryCreate,
    ResourceCategoryResponse,
    ResourceCategoryUpdate,
)
from .base import _build_deleted_unique_value

class ResourceCategoryTreeNode(TypedDict):
    id: int
    name: str
    code: str
    resource_type: ResourceType
    parent_id: int | None
    sort_order: int
    is_active: bool
    description: str | None
    children: list["ResourceCategoryTreeNode"]
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

class ResourceCategoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, category_id: int) -> MdResourceCategory:
        category = self.db.execute(
            select(MdResourceCategory).where(
                MdResourceCategory.id == category_id,
                MdResourceCategory.is_deleted == False,
            )
        ).scalar_one_or_none()
        if category is None:
            raise ResourceNotFoundError(resource="资源分类", identifier=category_id)
        return category

    def _assert_code_unique(self, code: str, exclude_id: int | None = None) -> None:
        stmt = select(MdResourceCategory).where(
            MdResourceCategory.code == code,
            MdResourceCategory.is_deleted == False,
        )
        if exclude_id is not None:
            stmt = stmt.where(MdResourceCategory.id != exclude_id)
        exists = self.db.execute(stmt).scalar_one_or_none()
        if exists is not None:
            raise BusinessRuleViolationError(
                error_code="RESOURCE_CATEGORY_CODE_DUPLICATE",
                message=f"资源分类编码已存在：{code}",
            )

    def _build_tree(self, categories: list[MdResourceCategory]) -> list[ResourceCategoryTreeNode]:
        category_map: dict[int, ResourceCategoryTreeNode] = {
            category.id: {
                "id": category.id,
                "name": category.name,
                "code": category.code,
                "resource_type": category.resource_type,
                "parent_id": category.parent_id,
                "sort_order": category.sort_order,
                "is_active": category.is_active,
                "description": category.description,
                "children": [],
                "created_at": category.created_at,
                "updated_at": category.updated_at,
                "created_by": category.created_by,
                "updated_by": category.updated_by,
            }
            for category in categories
        }
        root_categories: list[ResourceCategoryTreeNode] = []

        for category in categories:
            node = category_map[category.id]
            if category.parent_id is None:
                root_categories.append(node)
                continue

            parent = category_map.get(category.parent_id)
            if parent is not None:
                parent["children"].append(node)

        return root_categories

    def list(
        self,
        keyword: str | None = None,
        resource_type: str | None = None,
        parent_id: int | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[ResourceCategoryResponse]:
        stmt = select(MdResourceCategory).where(MdResourceCategory.is_deleted == False)

        if keyword:
            stmt = stmt.where(
                or_(
                    MdResourceCategory.name.ilike(f"%{keyword}%"),
                    MdResourceCategory.code.ilike(f"%{keyword}%"),
                )
            )
        if resource_type:
            stmt = stmt.where(MdResourceCategory.resource_type == resource_type)
        if parent_id is not None:
            stmt = stmt.where(MdResourceCategory.parent_id == parent_id)
        if is_active is not None:
            stmt = stmt.where(MdResourceCategory.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(MdResourceCategory.sort_order, MdResourceCategory.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult(
            items=[ResourceCategoryResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    def get_tree(
        self,
        resource_type: str | None = None,
    ) -> list[ResourceCategoryTreeNode]:
        stmt = select(MdResourceCategory).where(
            MdResourceCategory.is_deleted == False,
            MdResourceCategory.is_active == True,
        )

        if resource_type:
            stmt = stmt.where(MdResourceCategory.resource_type == resource_type)

        stmt = stmt.order_by(MdResourceCategory.sort_order, MdResourceCategory.id)
        categories = self.db.execute(stmt).scalars().all()

        return self._build_tree(categories)

    def get(self, category_id: int) -> ResourceCategoryResponse:
        category = self._get_or_404(category_id)
        return ResourceCategoryResponse.model_validate(category)

    def create(self, payload: ResourceCategoryCreate, operator: str) -> ResourceCategoryResponse:
        self._assert_code_unique(payload.code)

        if payload.parent_id is not None:
            raise BusinessRuleViolationError(
                error_code="RESOURCE_CATEGORY_FLAT_ONLY",
                message="资源分类仅支持一级结构，请直接挂到材料/设备/人员/工艺类型下",
            )

        category = MdResourceCategory(
            **payload.model_dump(),
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(category)
        self.db.flush()
        return ResourceCategoryResponse.model_validate(category)

    def update(
        self, category_id: int, payload: ResourceCategoryUpdate, operator: str
    ) -> ResourceCategoryResponse:
        category = self._get_or_404(category_id)

        if payload.code is not None:
            self._assert_code_unique(payload.code, exclude_id=category_id)

        if payload.parent_id is not None:
            raise BusinessRuleViolationError(
                error_code="RESOURCE_CATEGORY_FLAT_ONLY",
                message="资源分类仅支持一级结构，请直接挂到材料/设备/人员/工艺类型下",
            )

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        category.updated_by = operator
        self.db.flush()
        return ResourceCategoryResponse.model_validate(category)

    def delete(self, category_id: int, operator: str) -> None:
        category = self._get_or_404(category_id)

        child_count = self.db.execute(
            select(func.count()).select_from(MdResourceCategory).where(
                MdResourceCategory.parent_id == category_id,
                MdResourceCategory.is_deleted == False,
            )
        ).scalar_one()
        if child_count > 0:
            raise BusinessRuleViolationError(
                error_code="RESOURCE_CATEGORY_HAS_CHILDREN",
                message=f"分类「{category.name}」下仍有子分类，不能删除",
            )

        binding_count = 0
        if category.resource_type == ResourceType.MATERIAL:
            binding_count = self.db.execute(
                select(func.count()).select_from(MdMaterial).where(
                    MdMaterial.category_id == category_id,
                    MdMaterial.is_deleted == False,
                )
            ).scalar_one()
        elif category.resource_type == ResourceType.EQUIPMENT:
            binding_count = self.db.execute(
                select(func.count()).select_from(MdEquipment).where(
                    MdEquipment.category_id == category_id,
                    MdEquipment.is_deleted == False,
                )
            ).scalar_one()
        elif category.resource_type == ResourceType.LABOR:
            binding_count = self.db.execute(
                select(func.count()).select_from(MdLabor).where(
                    MdLabor.category_id == category_id,
                    MdLabor.is_deleted == False,
                )
            ).scalar_one()
        elif category.resource_type == ResourceType.PROCESS:
            binding_count = self.db.execute(
                select(func.count()).select_from(MdProcess).where(
                    MdProcess.category_id == category_id,
                    MdProcess.is_deleted == False,
                )
            ).scalar_one()

        if binding_count > 0:
            raise BusinessRuleViolationError(
                error_code="RESOURCE_CATEGORY_IN_USE",
                message=f"分类「{category.name}」下仍有关联数据，不能删除",
            )

        category.code = _build_deleted_unique_value(category.code, category.id, 30)
        category.is_deleted = True
        category.updated_by = operator
        self.db.flush()
