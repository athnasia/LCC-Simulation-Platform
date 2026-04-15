from __future__ import annotations
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.models.master_data import MdEquipment, MdResourceCategory, ResourceType
from app.schemas.common import PageResult
from app.schemas.master_data import (
    EquipmentCreate,
    EquipmentResponse,
    EquipmentUpdate,
)
from .base import _build_deleted_unique_value, _check_process_resource_reference

class EquipmentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, equipment_id: int) -> MdEquipment:
        equipment = self.db.execute(
            select(MdEquipment).where(
                MdEquipment.id == equipment_id,
                MdEquipment.is_deleted == False,
            )
            .options(selectinload(MdEquipment.category))
        ).scalar_one_or_none()
        if equipment is None:
            raise ResourceNotFoundError(resource="设备", identifier=equipment_id)
        return equipment

    def _assert_code_unique(self, code: str, exclude_id: int | None = None) -> None:
        stmt = select(MdEquipment).where(
            MdEquipment.code == code,
            MdEquipment.is_deleted == False,
        )
        if exclude_id is not None:
            stmt = stmt.where(MdEquipment.id != exclude_id)
        exists = self.db.execute(stmt).scalar_one_or_none()
        if exists is not None:
            raise BusinessRuleViolationError(
                error_code="EQUIPMENT_CODE_DUPLICATE",
                message=f"设备编码已存在：{code}",
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
            raise ResourceNotFoundError(resource="设备分类", identifier=category_id)

        if category.resource_type != ResourceType.EQUIPMENT:
            raise BusinessRuleViolationError(
                error_code="EQUIPMENT_CATEGORY_TYPE_MISMATCH",
                message=f"设备分类类型不匹配：期望 EQUIPMENT，实际为 {category.resource_type}",
            )

    def list(
        self,
        keyword: str | None = None,
        category_id: int | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[EquipmentResponse]:
        stmt = select(MdEquipment).where(MdEquipment.is_deleted == False)

        if keyword:
            stmt = stmt.where(
                or_(
                    MdEquipment.name.ilike(f"%{keyword}%"),
                    MdEquipment.code.ilike(f"%{keyword}%"),
                )
            )
        if category_id is not None:
            stmt = stmt.where(MdEquipment.category_id == category_id)
        if is_active is not None:
            stmt = stmt.where(MdEquipment.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.options(selectinload(MdEquipment.category))
        stmt = stmt.order_by(MdEquipment.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult(
            items=[EquipmentResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    def get(self, equipment_id: int) -> EquipmentResponse:
        equipment = self._get_or_404(equipment_id)
        return EquipmentResponse.model_validate(equipment)

    def create(self, payload: EquipmentCreate, operator: str) -> EquipmentResponse:
        self._assert_code_unique(payload.code)
        self._validate_category_type(payload.category_id)

        equipment = MdEquipment(
            **payload.model_dump(),
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(equipment)
        self.db.flush()

        equipment = self.db.execute(
            select(MdEquipment)
            .where(MdEquipment.id == equipment.id)
            .options(selectinload(MdEquipment.category))
        ).scalar_one()
        return EquipmentResponse.model_validate(equipment)

    def update(
        self, equipment_id: int, payload: EquipmentUpdate, operator: str
    ) -> EquipmentResponse:
        equipment = self._get_or_404(equipment_id)

        if payload.code is not None:
            self._assert_code_unique(payload.code, exclude_id=equipment_id)

        if payload.category_id is not None:
            self._validate_category_type(payload.category_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(equipment, field, value)
        equipment.updated_by = operator
        self.db.flush()

        equipment = self.db.execute(
            select(MdEquipment)
            .where(MdEquipment.id == equipment_id)
            .options(selectinload(MdEquipment.category))
        ).scalar_one()
        return EquipmentResponse.model_validate(equipment)

    def delete(self, equipment_id: int, operator: str) -> None:
        equipment = self._get_or_404(equipment_id)

        _check_process_resource_reference(
            self.db, ResourceType.EQUIPMENT, equipment_id, f"设备【{equipment.name}】"
        )

        equipment.code = _build_deleted_unique_value(equipment.code, equipment.id, 50)
        equipment.is_deleted = True
        equipment.updated_by = operator
        self.db.flush()
