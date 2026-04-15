"""
系统级数据字典业务服务层

包含：
  - SystemDictionaryTypeService 字典类型 CRUD
  - SystemDictionaryItemService 字典项 CRUD
  - SystemDictionaryCacheService 前端缓存聚合读取
"""

from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.models.system_dictionary import SysDictItem, SysDictType
from app.schemas.common import PageResult
from app.schemas.system_dictionary import (
    SysDictCacheItemResponse,
    SysDictCacheResponse,
    SysDictCacheTypeResponse,
    SysDictItemCreate,
    SysDictItemResponse,
    SysDictItemUpdate,
    SysDictTypeCreate,
    SysDictTypeResponse,
    SysDictTypeUpdate,
)


def _build_deleted_unique_value(value: str | None, record_id: int, max_length: int) -> str | None:
    if not value:
        return value

    suffix = f"__deleted__{record_id}"
    keep_length = max_length - len(suffix)
    if keep_length <= 0:
        return suffix[-max_length:]
    return f"{value[:keep_length]}{suffix}"


class SystemDictionaryTypeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, dict_type_id: int) -> SysDictType:
        dict_type = self.db.execute(
            select(SysDictType).where(
                SysDictType.id == dict_type_id,
                SysDictType.is_deleted == False,
            )
        ).scalar_one_or_none()
        if dict_type is None:
            raise ResourceNotFoundError(resource="字典类型", identifier=dict_type_id)
        return dict_type

    def _assert_code_unique(self, code: str, exclude_id: int | None = None) -> None:
        stmt = select(SysDictType).where(
            SysDictType.code == code,
            SysDictType.is_deleted == False,
        )
        if exclude_id is not None:
            stmt = stmt.where(SysDictType.id != exclude_id)
        if self.db.execute(stmt).scalar_one_or_none() is not None:
            raise BusinessRuleViolationError(message=f"字典类型编码「{code}」已存在")

    def list(
        self,
        *,
        keyword: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[SysDictTypeResponse]:
        stmt = select(SysDictType).where(SysDictType.is_deleted == False)
        if keyword:
            stmt = stmt.where(
                or_(
                    SysDictType.name.ilike(f"%{keyword}%"),
                    SysDictType.code.ilike(f"%{keyword}%"),
                )
            )
        if is_active is not None:
            stmt = stmt.where(SysDictType.is_active == is_active)

        total: int = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
        rows = self.db.execute(
            stmt.order_by(SysDictType.sort_order, SysDictType.id)
            .offset((page - 1) * size)
            .limit(size)
        ).scalars().all()

        return PageResult.build(
            items=[SysDictTypeResponse.model_validate(row) for row in rows],
            total=total,
            page=page,
            size=size,
        )

    def get(self, dict_type_id: int) -> SysDictTypeResponse:
        return SysDictTypeResponse.model_validate(self._get_or_404(dict_type_id))

    def create(self, payload: SysDictTypeCreate, operator: str) -> SysDictTypeResponse:
        self._assert_code_unique(payload.code)
        dict_type = SysDictType(
            name=payload.name,
            code=payload.code,
            description=payload.description,
            sort_order=payload.sort_order,
            is_active=payload.is_active,
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(dict_type)
        self.db.flush()
        return SysDictTypeResponse.model_validate(dict_type)

    def update(self, dict_type_id: int, payload: SysDictTypeUpdate, operator: str) -> SysDictTypeResponse:
        dict_type = self._get_or_404(dict_type_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dict_type, field, value)
        dict_type.updated_by = operator
        self.db.flush()
        return SysDictTypeResponse.model_validate(dict_type)

    def delete(self, dict_type_id: int, operator: str) -> None:
        dict_type = self._get_or_404(dict_type_id)
        item_count: int = self.db.execute(
            select(func.count()).select_from(SysDictItem).where(
                SysDictItem.dict_type_id == dict_type_id,
                SysDictItem.is_deleted == False,
            )
        ).scalar_one()
        if item_count > 0:
            raise BusinessRuleViolationError(message="该字典类型下仍存在字典项，请先删除字典项后再删除类型")

        dict_type.code = _build_deleted_unique_value(dict_type.code, dict_type.id, 64)
        dict_type.is_deleted = True
        dict_type.updated_by = operator
        self.db.flush()


class SystemDictionaryItemService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_type_or_404(self, dict_type_id: int) -> SysDictType:
        dict_type = self.db.execute(
            select(SysDictType).where(
                SysDictType.id == dict_type_id,
                SysDictType.is_deleted == False,
            )
        ).scalar_one_or_none()
        if dict_type is None:
            raise ResourceNotFoundError(resource="字典类型", identifier=dict_type_id)
        return dict_type

    def _get_or_404(self, item_id: int) -> SysDictItem:
        item = self.db.execute(
            select(SysDictItem)
            .where(SysDictItem.id == item_id, SysDictItem.is_deleted == False)
            .options(selectinload(SysDictItem.dict_type))
        ).scalar_one_or_none()
        if item is None:
            raise ResourceNotFoundError(resource="字典项", identifier=item_id)
        return item

    def _assert_value_unique(self, dict_type_id: int, value: str, exclude_id: int | None = None) -> None:
        stmt = select(SysDictItem).where(
            SysDictItem.dict_type_id == dict_type_id,
            SysDictItem.value == value,
            SysDictItem.is_deleted == False,
        )
        if exclude_id is not None:
            stmt = stmt.where(SysDictItem.id != exclude_id)
        if self.db.execute(stmt).scalar_one_or_none() is not None:
            raise BusinessRuleViolationError(message=f"该字典类型下的字典值「{value}」已存在")

    def list(
        self,
        *,
        dict_type_id: int | None = None,
        dict_type_code: str | None = None,
        keyword: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[SysDictItemResponse]:
        stmt = (
            select(SysDictItem)
            .join(SysDictType, SysDictItem.dict_type_id == SysDictType.id)
            .where(SysDictItem.is_deleted == False, SysDictType.is_deleted == False)
        )
        if dict_type_id is not None:
            stmt = stmt.where(SysDictItem.dict_type_id == dict_type_id)
        if dict_type_code is not None:
            stmt = stmt.where(SysDictType.code == dict_type_code)
        if keyword:
            stmt = stmt.where(
                or_(
                    SysDictItem.value.ilike(f"%{keyword}%"),
                    SysDictItem.label.ilike(f"%{keyword}%"),
                )
            )
        if is_active is not None:
            stmt = stmt.where(SysDictItem.is_active == is_active)

        total: int = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
        rows = self.db.execute(
            stmt.options(selectinload(SysDictItem.dict_type))
            .order_by(SysDictType.sort_order, SysDictItem.sort_order, SysDictItem.id)
            .offset((page - 1) * size)
            .limit(size)
        ).scalars().all()

        return PageResult.build(
            items=[SysDictItemResponse.model_validate(row) for row in rows],
            total=total,
            page=page,
            size=size,
        )

    def get(self, item_id: int) -> SysDictItemResponse:
        return SysDictItemResponse.model_validate(self._get_or_404(item_id))

    def create(self, payload: SysDictItemCreate, operator: str) -> SysDictItemResponse:
        self._get_type_or_404(payload.dict_type_id)
        self._assert_value_unique(payload.dict_type_id, payload.value)

        item = SysDictItem(
            dict_type_id=payload.dict_type_id,
            value=payload.value,
            label=payload.label,
            description=payload.description,
            sort_order=payload.sort_order,
            is_active=payload.is_active,
            extra_json=payload.extra_json,
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(item)
        self.db.flush()

        item = self.db.execute(
            select(SysDictItem)
            .where(SysDictItem.id == item.id)
            .options(selectinload(SysDictItem.dict_type))
        ).scalar_one()
        return SysDictItemResponse.model_validate(item)

    def update(self, item_id: int, payload: SysDictItemUpdate, operator: str) -> SysDictItemResponse:
        item = self._get_or_404(item_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        item.updated_by = operator
        self.db.flush()

        item = self.db.execute(
            select(SysDictItem)
            .where(SysDictItem.id == item_id)
            .options(selectinload(SysDictItem.dict_type))
        ).scalar_one()
        return SysDictItemResponse.model_validate(item)

    def delete(self, item_id: int, operator: str) -> None:
        item = self._get_or_404(item_id)
        item.value = _build_deleted_unique_value(item.value, item.id, 100)
        item.is_deleted = True
        item.updated_by = operator
        self.db.flush()


class SystemDictionaryCacheService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active_cache(self) -> SysDictCacheResponse:
        dict_types = self.db.execute(
            select(SysDictType)
            .where(
                SysDictType.is_deleted == False,
                SysDictType.is_active == True,
            )
            .options(selectinload(SysDictType.items))
            .order_by(SysDictType.sort_order, SysDictType.id)
        ).scalars().all()

        dictionaries: list[SysDictCacheTypeResponse] = []
        for dict_type in dict_types:
            active_items = [
                SysDictCacheItemResponse(
                    value=item.value,
                    label=item.label,
                    sort_order=item.sort_order,
                    extra_json=item.extra_json,
                )
                for item in dict_type.items
                if item.is_deleted == False and item.is_active == True
            ]
            dictionaries.append(
                SysDictCacheTypeResponse(
                    name=dict_type.name,
                    code=dict_type.code,
                    items=active_items,
                )
            )

        return SysDictCacheResponse(dictionaries=dictionaries)