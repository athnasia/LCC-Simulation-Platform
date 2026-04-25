from __future__ import annotations
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.models.master_data import MdEnergyCalendar, MdEnergyRate, EnergyType
from app.schemas.common import PageResult
from app.schemas.master_data import (
    EnergyCalendarCreate,
    EnergyCalendarResponse,
    EnergyCalendarUpdate,
    EnergyRateCreate,
    EnergyRateResponse,
    EnergyRateUpdate,
)
from .base import _build_deleted_unique_value

class EnergyRateService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, rate_id: int) -> MdEnergyRate:
        rate = self.db.execute(
            select(MdEnergyRate).where(
                MdEnergyRate.id == rate_id,
                MdEnergyRate.is_deleted == False,
            )
            .options(
                selectinload(MdEnergyRate.unit),
                selectinload(MdEnergyRate.calendars),
            )
        ).scalar_one_or_none()
        if rate is None:
            raise ResourceNotFoundError(resource="能源单价", identifier=rate_id)
        return rate

    def _assert_code_unique(self, code: str, exclude_id: int | None = None) -> None:
        stmt = select(MdEnergyRate).where(
            MdEnergyRate.code == code,
            MdEnergyRate.is_deleted == False,
        )
        if exclude_id is not None:
            stmt = stmt.where(MdEnergyRate.id != exclude_id)
        exists = self.db.execute(stmt).scalar_one_or_none()
        if exists is not None:
            raise BusinessRuleViolationError(
                error_code="ENERGY_RATE_CODE_DUPLICATE",
                message=f"能源编码已存在：{code}",
            )

    def list(
        self,
        keyword: str | None = None,
        energy_type: EnergyType | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[EnergyRateResponse]:
        stmt = select(MdEnergyRate).where(MdEnergyRate.is_deleted == False)

        if keyword:
            stmt = stmt.where(
                or_(
                    MdEnergyRate.name.ilike(f"%{keyword}%"),
                    MdEnergyRate.code.ilike(f"%{keyword}%"),
                )
            )
        if energy_type:
            stmt = stmt.where(MdEnergyRate.energy_type == energy_type)
        if is_active is not None:
            stmt = stmt.where(MdEnergyRate.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.options(
            selectinload(MdEnergyRate.unit),
            selectinload(MdEnergyRate.calendars),
        )
        stmt = stmt.order_by(MdEnergyRate.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult(
            items=[EnergyRateResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    def get(self, rate_id: int) -> EnergyRateResponse:
        rate = self._get_or_404(rate_id)
        return EnergyRateResponse.model_validate(rate)

    def create(self, payload: EnergyRateCreate, operator: str) -> EnergyRateResponse:
        self._assert_code_unique(payload.code)

        calendars_data = payload.calendars
        rate_data = payload.model_dump(exclude={"calendars"})

        rate = MdEnergyRate(
            **rate_data,
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(rate)
        self.db.flush()

        for calendar_data in calendars_data:
            calendar = MdEnergyCalendar(
                energy_rate_id=rate.id,
                **calendar_data.model_dump(exclude={"energy_rate_id", "is_cross_day"}),
                created_by=operator,
                updated_by=operator,
            )
            self.db.add(calendar)
        self.db.flush()

        rate = self.db.execute(
            select(MdEnergyRate)
            .where(MdEnergyRate.id == rate.id)
            .options(
                selectinload(MdEnergyRate.unit),
                selectinload(MdEnergyRate.calendars),
            )
        ).scalar_one()
        return EnergyRateResponse.model_validate(rate)

    def update(
        self, rate_id: int, payload: EnergyRateUpdate, operator: str
    ) -> EnergyRateResponse:
        rate = self._get_or_404(rate_id)

        update_data = payload.model_dump(exclude_unset=True, exclude={"calendars"})
        for field, value in update_data.items():
            setattr(rate, field, value)
        rate.updated_by = operator
        self.db.flush()

        if payload.calendars is not None:
            self.db.query(MdEnergyCalendar).filter(MdEnergyCalendar.energy_rate_id == rate_id).delete()
            
            for calendar_data in payload.calendars:
                calendar = MdEnergyCalendar(
                    energy_rate_id=rate_id,
                    **calendar_data.model_dump(exclude={"energy_rate_id", "is_cross_day"}),
                    created_by=operator,
                    updated_by=operator,
                )
                self.db.add(calendar)
            
            self.db.flush()

        rate = self.db.execute(
            select(MdEnergyRate)
            .where(MdEnergyRate.id == rate_id)
            .options(
                selectinload(MdEnergyRate.unit),
                selectinload(MdEnergyRate.calendars),
            )
        ).scalar_one()
        return EnergyRateResponse.model_validate(rate)

    def delete(self, rate_id: int, operator: str) -> None:
        rate = self._get_or_404(rate_id)

        rate.code = _build_deleted_unique_value(rate.code, rate.id, 50)
        rate.is_deleted = True
        rate.updated_by = operator
        self.db.flush()

class EnergyCalendarService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, calendar_id: int) -> MdEnergyCalendar:
        calendar = self.db.execute(
            select(MdEnergyCalendar).where(
                MdEnergyCalendar.id == calendar_id,
            )
            .options(selectinload(MdEnergyCalendar.energy_rate))
        ).scalar_one_or_none()
        if calendar is None:
            raise ResourceNotFoundError(resource="能源日历", identifier=calendar_id)
        return calendar

    def list(
        self,
        energy_rate_id: int | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[EnergyCalendarResponse]:
        stmt = select(MdEnergyCalendar)

        if energy_rate_id is not None:
            stmt = stmt.where(MdEnergyCalendar.energy_rate_id == energy_rate_id)
        if is_active is not None:
            stmt = stmt.where(MdEnergyCalendar.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.options(selectinload(MdEnergyCalendar.energy_rate))
        stmt = stmt.order_by(MdEnergyCalendar.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult(
            items=[EnergyCalendarResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    def get(self, calendar_id: int) -> EnergyCalendarResponse:
        calendar = self._get_or_404(calendar_id)
        return EnergyCalendarResponse.model_validate(calendar)

    def create(self, payload: EnergyCalendarCreate, operator: str) -> EnergyCalendarResponse:
        rate = self.db.execute(
            select(MdEnergyRate).where(
                MdEnergyRate.id == payload.energy_rate_id,
                MdEnergyRate.is_deleted == False,
            )
        ).scalar_one_or_none()
        if rate is None:
            raise ResourceNotFoundError(resource="能源单价", identifier=payload.energy_rate_id)

        calendar = MdEnergyCalendar(
            **payload.model_dump(exclude={"is_cross_day"}),
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(calendar)
        self.db.flush()

        calendar = self.db.execute(
            select(MdEnergyCalendar)
            .where(MdEnergyCalendar.id == calendar.id)
            .options(selectinload(MdEnergyCalendar.energy_rate))
        ).scalar_one()
        return EnergyCalendarResponse.model_validate(calendar)

    def update(
        self, calendar_id: int, payload: EnergyCalendarUpdate, operator: str
    ) -> EnergyCalendarResponse:
        calendar = self._get_or_404(calendar_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(calendar, field, value)
        calendar.updated_by = operator
        self.db.flush()

        calendar = self.db.execute(
            select(MdEnergyCalendar)
            .where(MdEnergyCalendar.id == calendar_id)
            .options(selectinload(MdEnergyCalendar.energy_rate))
        ).scalar_one()
        return EnergyCalendarResponse.model_validate(calendar)

    def delete(self, calendar_id: int, operator: str) -> None:
        calendar = self._get_or_404(calendar_id)
        self.db.delete(calendar)
        self.db.flush()
