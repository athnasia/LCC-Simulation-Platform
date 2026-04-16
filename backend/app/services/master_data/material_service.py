from __future__ import annotations
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.models.master_data import DataType, MdAttrDefinition, MdMaterial, MdResourceCategory, ResourceType
from app.schemas.common import PageResult
from app.schemas.master_data import (
    AttrDefinitionCreate,
    AttrDefinitionResponse,
    AttrDefinitionUpdate,
    MaterialCreate,
    MaterialResponse,
    MaterialUpdate,
)
from .base import _build_deleted_unique_value, _check_process_resource_reference

class AttrDefinitionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, attr_id: int) -> MdAttrDefinition:
        attr = self.db.execute(
            select(MdAttrDefinition).where(
                MdAttrDefinition.id == attr_id,
                MdAttrDefinition.is_deleted == False,
            )
            .options(selectinload(MdAttrDefinition.unit))
        ).scalar_one_or_none()
        if attr is None:
            raise ResourceNotFoundError(resource="属性定义", identifier=attr_id)
        return attr

    def _assert_code_unique(self, code: str, exclude_id: int | None = None) -> None:
        stmt = select(MdAttrDefinition).where(
            MdAttrDefinition.code == code,
            MdAttrDefinition.is_deleted == False,
        )
        if exclude_id is not None:
            stmt = stmt.where(MdAttrDefinition.id != exclude_id)
        exists = self.db.execute(stmt).scalar_one_or_none()
        if exists is not None:
            raise BusinessRuleViolationError(
                error_code="ATTR_CODE_DUPLICATE",
                message=f"属性变量标识码已存在：{code}",
            )

    def list(
        self,
        keyword: str | None = None,
        data_type: DataType | None = None,
        resource_type: ResourceType | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[AttrDefinitionResponse]:
        stmt = select(MdAttrDefinition).where(MdAttrDefinition.is_deleted == False)

        if keyword:
            stmt = stmt.where(MdAttrDefinition.name.ilike(f"%{keyword}%"))
        
        if data_type:
            stmt = stmt.where(MdAttrDefinition.data_type == data_type)
        
        # JSON 包含查询：检查 resource_type 是否在 applicable_resource_types 数组中
        if resource_type:
            stmt = stmt.where(func.json_contains(MdAttrDefinition.applicable_resource_types, func.json_quote(resource_type.value)))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.options(selectinload(MdAttrDefinition.unit))
        stmt = stmt.order_by(MdAttrDefinition.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult(
            items=[AttrDefinitionResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    def get(self, attr_id: int) -> AttrDefinitionResponse:
        attr = self._get_or_404(attr_id)
        return AttrDefinitionResponse.model_validate(attr)

    def create(self, payload: AttrDefinitionCreate, operator: str) -> AttrDefinitionResponse:
        self._assert_code_unique(payload.code)

        attr = MdAttrDefinition(
            **payload.model_dump(),
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(attr)
        self.db.flush()
        
        attr = self.db.execute(
            select(MdAttrDefinition).where(MdAttrDefinition.id == attr.id).options(selectinload(MdAttrDefinition.unit))
        ).scalar_one()
        return AttrDefinitionResponse.model_validate(attr)

    def update(
        self, attr_id: int, payload: AttrDefinitionUpdate, operator: str
    ) -> AttrDefinitionResponse:
        attr = self._get_or_404(attr_id)

        if payload.code is not None:
            self._assert_code_unique(payload.code, exclude_id=attr_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(attr, field, value)
        attr.updated_by = operator
        self.db.flush()
        
        attr = self.db.execute(
            select(MdAttrDefinition).where(MdAttrDefinition.id == attr_id).options(selectinload(MdAttrDefinition.unit))
        ).scalar_one()
        return AttrDefinitionResponse.model_validate(attr)

    def delete(self, attr_id: int, operator: str) -> None:
        attr = self._get_or_404(attr_id)

        attr.code = _build_deleted_unique_value(attr.code, attr.id, 30)
        attr.is_deleted = True
        attr.updated_by = operator
        self.db.flush()

class MaterialService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, material_id: int) -> MdMaterial:
        material = self.db.execute(
            select(MdMaterial).where(
                MdMaterial.id == material_id,
                MdMaterial.is_deleted == False,
            )
            .options(
                selectinload(MdMaterial.category),
                selectinload(MdMaterial.pricing_unit),
                selectinload(MdMaterial.consumption_unit),
            )
        ).scalar_one_or_none()
        if material is None:
            raise ResourceNotFoundError(resource="材料", identifier=material_id)
        return material

    def _assert_code_unique(self, code: str, exclude_id: int | None = None) -> None:
        stmt = select(MdMaterial).where(
            MdMaterial.code == code,
            MdMaterial.is_deleted == False,
        )
        if exclude_id is not None:
            stmt = stmt.where(MdMaterial.id != exclude_id)
        exists = self.db.execute(stmt).scalar_one_or_none()
        if exists is not None:
            raise BusinessRuleViolationError(
                error_code="MATERIAL_CODE_DUPLICATE",
                message=f"材料编码已存在：{code}",
            )

    def _validate_category_type(self, category_id: int | None) -> None:
        if category_id is None:
            return

        category = self.db.execute(
            select(MdResourceCategory).where(
                MdResourceCategory.id == category_id,
                MdResourceCategory.is_deleted == False,
            )
        ).scalar_one_or_none()

        if category is None:
            raise ResourceNotFoundError(resource="材料分类", identifier=category_id)

        if category.resource_type != ResourceType.MATERIAL:
            raise BusinessRuleViolationError(
                error_code="MATERIAL_CATEGORY_TYPE_MISMATCH",
                message=f"材料分类类型不匹配：期望 MATERIAL，实际为 {category.resource_type}",
            )

    def list(
        self,
        keyword: str | None = None,
        category_id: int | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[MaterialResponse]:
        stmt = select(MdMaterial).where(MdMaterial.is_deleted == False)

        if keyword:
            stmt = stmt.where(
                or_(
                    MdMaterial.name.ilike(f"%{keyword}%"),
                    MdMaterial.code.ilike(f"%{keyword}%"),
                )
            )
        if category_id is not None:
            stmt = stmt.where(MdMaterial.category_id == category_id)
        if is_active is not None:
            stmt = stmt.where(MdMaterial.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.options(
            selectinload(MdMaterial.category),
            selectinload(MdMaterial.pricing_unit),
            selectinload(MdMaterial.consumption_unit),
        )
        stmt = stmt.order_by(MdMaterial.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult(
            items=[MaterialResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    def get(self, material_id: int) -> MaterialResponse:
        material = self._get_or_404(material_id)
        return MaterialResponse.model_validate(material)

    def create(self, payload: MaterialCreate, operator: str) -> MaterialResponse:
        self._assert_code_unique(payload.code)
        self._validate_category_type(payload.category_id)

        material = MdMaterial(
            **payload.model_dump(),
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(material)
        self.db.flush()

        material = self.db.execute(
            select(MdMaterial)
            .where(MdMaterial.id == material.id)
            .options(
                selectinload(MdMaterial.category),
                selectinload(MdMaterial.pricing_unit),
                selectinload(MdMaterial.consumption_unit),
            )
        ).scalar_one()
        return MaterialResponse.model_validate(material)

    def update(
        self, material_id: int, payload: MaterialUpdate, operator: str
    ) -> MaterialResponse:
        material = self._get_or_404(material_id)

        if payload.code is not None:
            self._assert_code_unique(payload.code, exclude_id=material_id)

        if payload.category_id is not None:
            self._validate_category_type(payload.category_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(material, field, value)
        material.updated_by = operator
        self.db.flush()

        material = self.db.execute(
            select(MdMaterial)
            .where(MdMaterial.id == material_id)
            .options(
                selectinload(MdMaterial.category),
                selectinload(MdMaterial.pricing_unit),
                selectinload(MdMaterial.consumption_unit),
            )
        ).scalar_one()
        return MaterialResponse.model_validate(material)

    def delete(self, material_id: int, operator: str) -> None:
        material = self._get_or_404(material_id)

        _check_process_resource_reference(
            self.db, ResourceType.MATERIAL, material_id, f"材料【{material.name}】"
        )

        material.code = _build_deleted_unique_value(material.code, material.id, 50)
        material.is_deleted = True
        material.updated_by = operator
        self.db.flush()
