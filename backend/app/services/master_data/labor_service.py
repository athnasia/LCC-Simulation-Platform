from __future__ import annotations
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.models.master_data import MdLabor, ResourceType
from app.schemas.common import PageResult
from app.schemas.master_data import (
    LaborCreate,
    LaborResponse,
    LaborUpdate,
)
from .base import _build_deleted_unique_value, _check_process_resource_reference

class LaborService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, labor_id: int) -> MdLabor:
        labor = self.db.execute(
            select(MdLabor).where(
                MdLabor.id == labor_id,
                MdLabor.is_deleted == False,
            )
        ).scalar_one_or_none()
        if labor is None:
            raise ResourceNotFoundError(resource="人员/工种", identifier=labor_id)
        return labor

    def _assert_code_unique(self, code: str, exclude_id: int | None = None) -> None:
        stmt = select(MdLabor).where(
            MdLabor.code == code,
            MdLabor.is_deleted == False,
        )
        if exclude_id is not None:
            stmt = stmt.where(MdLabor.id != exclude_id)
        exists = self.db.execute(stmt).scalar_one_or_none()
        if exists is not None:
            raise BusinessRuleViolationError(
                error_code="LABOR_CODE_DUPLICATE",
                message=f"人员/工种编码已存在：{code}",
            )

    def list(
        self,
        keyword: str | None = None,
        skill_level: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[LaborResponse]:
        stmt = select(MdLabor).where(MdLabor.is_deleted == False)

        if keyword:
            stmt = stmt.where(
                or_(
                    MdLabor.name.ilike(f"%{keyword}%"),
                    MdLabor.code.ilike(f"%{keyword}%"),
                )
            )
        if skill_level:
            stmt = stmt.where(MdLabor.skill_level == skill_level)
        if is_active is not None:
            stmt = stmt.where(MdLabor.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(MdLabor.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult(
            items=[LaborResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    def get(self, labor_id: int) -> LaborResponse:
        labor = self._get_or_404(labor_id)
        return LaborResponse.model_validate(labor)

    def create(self, payload: LaborCreate, operator: str) -> LaborResponse:
        self._assert_code_unique(payload.code)

        labor = MdLabor(
            **payload.model_dump(),
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(labor)
        self.db.flush()
        return LaborResponse.model_validate(labor)

    def update(
        self, labor_id: int, payload: LaborUpdate, operator: str
    ) -> LaborResponse:
        labor = self._get_or_404(labor_id)

        if payload.code is not None:
            self._assert_code_unique(payload.code, exclude_id=labor_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(labor, field, value)
        labor.updated_by = operator
        self.db.flush()
        return LaborResponse.model_validate(labor)

    def delete(self, labor_id: int, operator: str) -> None:
        labor = self._get_or_404(labor_id)

        _check_process_resource_reference(
            self.db, ResourceType.LABOR, labor_id, f"人员/工种【{labor.name}】"
        )

        labor.code = _build_deleted_unique_value(labor.code, labor.id, 50)
        labor.is_deleted = True
        labor.updated_by = operator
        self.db.flush()
