"""
主数据域业务服务层

包含：
  - UnitDimensionService   量纲 CRUD（编码唯一性）
  - UnitService            单位 CRUD（编码唯一性、量纲关联）
  - UnitConversionService  单位换算 CRUD（同量纲校验、换算计算）
  - ResourceCategoryService 资源分类 CRUD（树形结构组装）
  - AttrDefinitionService  属性定义 CRUD（变量标识码唯一性）
  - MaterialService        材料主数据 CRUD（分类类型校验）
  - EquipmentService       设备主数据 CRUD（分类类型校验）
  - ProcessService         标准工艺/工时库 CRUD（含复制功能）
  - LaborService           人员技能资质矩阵 CRUD
  - EnergyRateService      能源单价 CRUD
  - EnergyCalendarService  能源日历 CRUD

设计约定：
    1. 所有服务接收 Session 并在此层管理数据库操作，路由层只负责 I/O 转换
    2. 逻辑删除统一通过 is_deleted=True 实现，禁止物理 DELETE
    3. 写操作由路由层统一 commit，Service 内仅负责 add/flush
    4. 单位换算创建时强制校验源单位和目标单位属于同一量纲
    5. 材料/设备创建时强制校验分类类型匹配
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TypedDict

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.models.master_data import (
    EnergyType,
    MdAttrDefinition,
    MdEnergyCalendar,
    MdEnergyRate,
    MdEquipment,
    MdLabor,
    MdMaterial,
    MdProcess,
    MdProcessResource,
    MdResourceCategory,
    MdUnit,
    MdUnitConversion,
    MdUnitDimension,
    ResourceType,
    SkillLevel,
)
from app.schemas.common import PageResult
from app.schemas.master_data import (
    AttrDefinitionCreate,
    AttrDefinitionResponse,
    AttrDefinitionUpdate,
    EnergyCalendarCreate,
    EnergyCalendarResponse,
    EnergyCalendarUpdate,
    EnergyRateCreate,
    EnergyRateResponse,
    EnergyRateUpdate,
    EquipmentCreate,
    EquipmentResponse,
    EquipmentUpdate,
    LaborCreate,
    LaborResponse,
    LaborUpdate,
    MaterialCreate,
    MaterialResponse,
    MaterialUpdate,
    ProcessCloneRequest,
    ProcessCreate,
    ProcessResourceCreate,
    ProcessResourceResponse,
    ProcessResponse,
    ProcessUpdate,
    ResourceCategoryCreate,
    ResourceCategoryResponse,
    ResourceCategoryUpdate,
    SkillLevel as SkillLevelSchema,
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


def _build_deleted_unique_value(value: str | None, record_id: int, max_length: int) -> str | None:
    """构建逻辑删除后的唯一字段墓碑值"""
    if not value:
        return value

    suffix = f"__deleted__{record_id}"
    keep_length = max_length - len(suffix)
    if keep_length <= 0:
        return suffix[-max_length:]
    return f"{value[:keep_length]}{suffix}"


def _check_process_resource_reference(
    db: Session, resource_type: ResourceType, resource_id: int, resource_name: str
) -> None:
    """检查资源是否被工序引用，若被引用则抛出异常"""
    from app.models.master_data import MdProcessResource

    references = db.execute(
        select(MdProcessResource).where(
            MdProcessResource.resource_type == resource_type,
            MdProcessResource.resource_id == resource_id,
            MdProcessResource.is_deleted == False,
        )
        .limit(5)
    ).scalars().all()

    if references:
        process_names = [f"工序ID={ref.process_id}" for ref in references[:3]]
        extra = f"等 {len(references)} 个工序" if len(references) > 3 else ""
        raise BusinessRuleViolationError(
            error_code="RESOURCE_REFERENCED_BY_PROCESS",
            message=f"{resource_name} 已被工序引用（{', '.join(process_names)}{extra}），无法删除。请先解除工序中的资源挂载。",
        )


# ══════════════════════════════════════════════════════════════════════════════
# 一、量纲服务
# ══════════════════════════════════════════════════════════════════════════════

class UnitDimensionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, dimension_id: int) -> MdUnitDimension:
        dimension = self.db.execute(
            select(MdUnitDimension).where(
                MdUnitDimension.id == dimension_id,
                MdUnitDimension.is_deleted == False,
            )
        ).scalar_one_or_none()
        if dimension is None:
            raise ResourceNotFoundError(resource="量纲", identifier=dimension_id)
        return dimension

    def _assert_code_unique(self, code: str, exclude_id: int | None = None) -> None:
        stmt = select(MdUnitDimension).where(
            MdUnitDimension.code == code,
            MdUnitDimension.is_deleted == False,
        )
        if exclude_id is not None:
            stmt = stmt.where(MdUnitDimension.id != exclude_id)
        exists = self.db.execute(stmt).scalar_one_or_none()
        if exists is not None:
            raise BusinessRuleViolationError(
                error_code="DIMENSION_CODE_DUPLICATE",
                message=f"量纲编码已存在：{code}",
            )

    def list(
        self,
        keyword: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[UnitDimensionResponse]:
        stmt = select(MdUnitDimension).where(MdUnitDimension.is_deleted == False)

        if keyword:
            stmt = stmt.where(
                or_(
                    MdUnitDimension.name.ilike(f"%{keyword}%"),
                    MdUnitDimension.code.ilike(f"%{keyword}%"),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.order_by(MdUnitDimension.sort_order, MdUnitDimension.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult(
            items=[UnitDimensionResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    def get(self, dimension_id: int) -> UnitDimensionResponse:
        dimension = self._get_or_404(dimension_id)
        return UnitDimensionResponse.model_validate(dimension)

    def create(self, payload: UnitDimensionCreate, operator: str) -> UnitDimensionResponse:
        self._assert_code_unique(payload.code)

        dimension = MdUnitDimension(
            **payload.model_dump(),
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(dimension)
        self.db.flush()
        return UnitDimensionResponse.model_validate(dimension)

    def update(
        self, dimension_id: int, payload: UnitDimensionUpdate, operator: str
    ) -> UnitDimensionResponse:
        dimension = self._get_or_404(dimension_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dimension, field, value)
        dimension.updated_by = operator
        self.db.flush()
        return UnitDimensionResponse.model_validate(dimension)

    def delete(self, dimension_id: int, operator: str) -> None:
        dimension = self._get_or_404(dimension_id)

        dimension.code = _build_deleted_unique_value(dimension.code, dimension.id, 30)
        dimension.is_deleted = True
        dimension.updated_by = operator
        self.db.flush()


# ══════════════════════════════════════════════════════════════════════════════
# 二、单位服务
# ══════════════════════════════════════════════════════════════════════════════

class UnitService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, unit_id: int) -> MdUnit:
        unit = self.db.execute(
            select(MdUnit).where(
                MdUnit.id == unit_id,
                MdUnit.is_deleted == False,
            )
        ).scalar_one_or_none()
        if unit is None:
            raise ResourceNotFoundError(resource="单位", identifier=unit_id)
        return unit

    def _assert_code_unique(self, code: str, exclude_id: int | None = None) -> None:
        stmt = select(MdUnit).where(
            MdUnit.code == code,
            MdUnit.is_deleted == False,
        )
        if exclude_id is not None:
            stmt = stmt.where(MdUnit.id != exclude_id)
        exists = self.db.execute(stmt).scalar_one_or_none()
        if exists is not None:
            raise BusinessRuleViolationError(
                error_code="UNIT_CODE_DUPLICATE",
                message=f"单位编码已存在：{code}",
            )

    def list(
        self,
        keyword: str | None = None,
        dimension_id: int | None = None,
        is_base: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[UnitResponse]:
        stmt = select(MdUnit).where(MdUnit.is_deleted == False)

        if keyword:
            stmt = stmt.where(
                or_(
                    MdUnit.name.ilike(f"%{keyword}%"),
                    MdUnit.code.ilike(f"%{keyword}%"),
                )
            )
        if dimension_id is not None:
            stmt = stmt.where(MdUnit.dimension_id == dimension_id)
        if is_base is not None:
            stmt = stmt.where(MdUnit.is_base == is_base)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.options(selectinload(MdUnit.dimension))
        stmt = stmt.order_by(MdUnit.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult(
            items=[UnitResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    def get(self, unit_id: int) -> UnitResponse:
        unit = self._get_or_404(unit_id)
        unit = self.db.execute(
            select(MdUnit)
            .where(MdUnit.id == unit_id)
            .options(selectinload(MdUnit.dimension))
        ).scalar_one()
        return UnitResponse.model_validate(unit)

    def create(self, payload: UnitCreate, operator: str) -> UnitResponse:
        self._assert_code_unique(payload.code)

        dimension = self.db.execute(
            select(MdUnitDimension).where(
                MdUnitDimension.id == payload.dimension_id,
                MdUnitDimension.is_deleted == False,
            )
        ).scalar_one_or_none()
        if dimension is None:
            raise ResourceNotFoundError(resource="量纲", identifier=payload.dimension_id)

        unit = MdUnit(
            **payload.model_dump(),
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(unit)
        self.db.flush()

        unit = self.db.execute(
            select(MdUnit)
            .where(MdUnit.id == unit.id)
            .options(selectinload(MdUnit.dimension))
        ).scalar_one()
        return UnitResponse.model_validate(unit)

    def update(self, unit_id: int, payload: UnitUpdate, operator: str) -> UnitResponse:
        unit = self._get_or_404(unit_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(unit, field, value)
        unit.updated_by = operator
        self.db.flush()

        unit = self.db.execute(
            select(MdUnit)
            .where(MdUnit.id == unit_id)
            .options(selectinload(MdUnit.dimension))
        ).scalar_one()
        return UnitResponse.model_validate(unit)

    def delete(self, unit_id: int, operator: str) -> None:
        unit = self._get_or_404(unit_id)

        unit.code = _build_deleted_unique_value(unit.code, unit.id, 20)
        unit.is_deleted = True
        unit.updated_by = operator
        self.db.flush()


# ══════════════════════════════════════════════════════════════════════════════
# 三、单位换算服务
# ══════════════════════════════════════════════════════════════════════════════

class UnitConversionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, conversion_id: int) -> MdUnitConversion:
        conversion = self.db.execute(
            select(MdUnitConversion).where(
                MdUnitConversion.id == conversion_id,
                MdUnitConversion.is_deleted == False,
            )
        ).scalar_one_or_none()
        if conversion is None:
            raise ResourceNotFoundError(resource="单位换算", identifier=conversion_id)
        return conversion

    def _assert_same_dimension(self, from_unit_id: int, to_unit_id: int) -> None:
        """校验源单位和目标单位必须属于同一量纲"""
        from_unit = self.db.execute(
            select(MdUnit).where(MdUnit.id == from_unit_id, MdUnit.is_deleted == False)
        ).scalar_one_or_none()
        to_unit = self.db.execute(
            select(MdUnit).where(MdUnit.id == to_unit_id, MdUnit.is_deleted == False)
        ).scalar_one_or_none()

        if from_unit is None:
            raise ResourceNotFoundError(resource="源单位", identifier=from_unit_id)
        if to_unit is None:
            raise ResourceNotFoundError(resource="目标单位", identifier=to_unit_id)

        if from_unit.dimension_id != to_unit.dimension_id:
            raise BusinessRuleViolationError(
                error_code="UNIT_CONVERSION_DIFFERENT_DIMENSION",
                message=f"单位换算失败：源单位（{from_unit.name}）和目标单位（{to_unit.name}）不属于同一量纲",
                detail={
                    "from_unit_dimension": from_unit.dimension_id,
                    "to_unit_dimension": to_unit.dimension_id,
                },
            )

    def list(
        self,
        from_unit_id: int | None = None,
        to_unit_id: int | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[UnitConversionResponse]:
        stmt = select(MdUnitConversion).where(MdUnitConversion.is_deleted == False)

        if from_unit_id is not None:
            stmt = stmt.where(MdUnitConversion.from_unit_id == from_unit_id)
        if to_unit_id is not None:
            stmt = stmt.where(MdUnitConversion.to_unit_id == to_unit_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.options(
            selectinload(MdUnitConversion.from_unit).selectinload(MdUnit.dimension),
            selectinload(MdUnitConversion.to_unit).selectinload(MdUnit.dimension),
        )
        stmt = stmt.order_by(MdUnitConversion.id)
        stmt = stmt.offset((page - 1) * size).limit(size)
        items = self.db.execute(stmt).scalars().all()

        return PageResult(
            items=[UnitConversionResponse.model_validate(item) for item in items],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size,
        )

    def get(self, conversion_id: int) -> UnitConversionResponse:
        conversion = self._get_or_404(conversion_id)
        conversion = self.db.execute(
            select(MdUnitConversion)
            .where(MdUnitConversion.id == conversion_id)
            .options(
                selectinload(MdUnitConversion.from_unit).selectinload(MdUnit.dimension),
                selectinload(MdUnitConversion.to_unit).selectinload(MdUnit.dimension),
            )
        ).scalar_one()
        return UnitConversionResponse.model_validate(conversion)

    def create(
        self, payload: UnitConversionCreate, operator: str
    ) -> UnitConversionResponse:
        self._assert_same_dimension(payload.from_unit_id, payload.to_unit_id)

        conversion = MdUnitConversion(
            **payload.model_dump(),
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(conversion)
        self.db.flush()

        conversion = self.db.execute(
            select(MdUnitConversion)
            .where(MdUnitConversion.id == conversion.id)
            .options(
                selectinload(MdUnitConversion.from_unit).selectinload(MdUnit.dimension),
                selectinload(MdUnitConversion.to_unit).selectinload(MdUnit.dimension),
            )
        ).scalar_one()
        return UnitConversionResponse.model_validate(conversion)

    def update(
        self, conversion_id: int, payload: UnitConversionUpdate, operator: str
    ) -> UnitConversionResponse:
        conversion = self._get_or_404(conversion_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conversion, field, value)
        conversion.updated_by = operator
        self.db.flush()

        conversion = self.db.execute(
            select(MdUnitConversion)
            .where(MdUnitConversion.id == conversion_id)
            .options(
                selectinload(MdUnitConversion.from_unit).selectinload(MdUnit.dimension),
                selectinload(MdUnitConversion.to_unit).selectinload(MdUnit.dimension),
            )
        ).scalar_one()
        return UnitConversionResponse.model_validate(conversion)

    def delete(self, conversion_id: int, operator: str) -> None:
        conversion = self._get_or_404(conversion_id)
        conversion.is_deleted = True
        conversion.updated_by = operator
        self.db.flush()

    def calculate(
        self, payload: UnitConversionCalculateRequest
    ) -> UnitConversionCalculateResponse:
        """
        执行单位换算计算（目前仅支持线性换算）
        
        支持自动反向换算：
        - 优先查找正向规则（from_unit → to_unit）
        - 若无正向规则，自动查找反向规则（to_unit → from_unit）并取倒数
        """
        conversion = self.db.execute(
            select(MdUnitConversion).where(
                MdUnitConversion.from_unit_id == payload.from_unit_id,
                MdUnitConversion.to_unit_id == payload.to_unit_id,
                MdUnitConversion.is_deleted == False,
            )
            .options(
                selectinload(MdUnitConversion.from_unit).selectinload(MdUnit.dimension),
                selectinload(MdUnitConversion.to_unit).selectinload(MdUnit.dimension),
            )
        ).scalar_one_or_none()

        if conversion is None:
            reverse_conversion = self.db.execute(
                select(MdUnitConversion).where(
                    MdUnitConversion.from_unit_id == payload.to_unit_id,
                    MdUnitConversion.to_unit_id == payload.from_unit_id,
                    MdUnitConversion.is_deleted == False,
                )
                .options(
                    selectinload(MdUnitConversion.from_unit).selectinload(MdUnit.dimension),
                    selectinload(MdUnitConversion.to_unit).selectinload(MdUnit.dimension),
                )
            ).scalar_one_or_none()

            if reverse_conversion is not None:
                reverse_factor = Decimal("1") / reverse_conversion.conversion_factor
                converted_value = payload.value * reverse_factor

                return UnitConversionCalculateResponse(
                    from_unit=reverse_conversion.to_unit,
                    to_unit=reverse_conversion.from_unit,
                    original_value=payload.value,
                    converted_value=converted_value,
                    conversion_factor=reverse_factor,
                    offset=reverse_conversion.offset,
                )

            raise BusinessRuleViolationError(
                error_code="UNIT_CONVERSION_NOT_FOUND",
                message="未找到对应的单位换算规则（正向或反向）",
                detail={
                    "from_unit_id": payload.from_unit_id,
                    "to_unit_id": payload.to_unit_id,
                },
            )

        converted_value = payload.value * conversion.conversion_factor

        return UnitConversionCalculateResponse(
            from_unit=conversion.from_unit,
            to_unit=conversion.to_unit,
            original_value=payload.value,
            converted_value=converted_value,
            conversion_factor=conversion.conversion_factor,
            offset=conversion.offset,
        )


# ══════════════════════════════════════════════════════════════════════════════
# 四、资源分类服务
# ══════════════════════════════════════════════════════════════════════════════

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
        """将扁平列表组装成纯字典树结构，避免向 ORM 关系集合写入非模型对象。"""
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
        """获取树状结构的分类列表"""
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
            parent = self.db.execute(
                select(MdResourceCategory).where(
                    MdResourceCategory.id == payload.parent_id,
                    MdResourceCategory.is_deleted == False,
                )
            ).scalar_one_or_none()
            if parent is None:
                raise ResourceNotFoundError(resource="父分类", identifier=payload.parent_id)

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
            if payload.parent_id == category_id:
                raise BusinessRuleViolationError(
                    error_code="RESOURCE_CATEGORY_PARENT_SELF",
                    message="父分类不能是自己",
                )
            parent = self.db.execute(
                select(MdResourceCategory).where(
                    MdResourceCategory.id == payload.parent_id,
                    MdResourceCategory.is_deleted == False,
                )
            ).scalar_one_or_none()
            if parent is None:
                raise ResourceNotFoundError(resource="父分类", identifier=payload.parent_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        category.updated_by = operator
        self.db.flush()
        return ResourceCategoryResponse.model_validate(category)

    def delete(self, category_id: int, operator: str) -> None:
        category = self._get_or_404(category_id)

        category.code = _build_deleted_unique_value(category.code, category.id, 30)
        category.is_deleted = True
        category.updated_by = operator
        self.db.flush()


# ══════════════════════════════════════════════════════════════════════════════
# 五、属性定义服务
# ══════════════════════════════════════════════════════════════════════════════

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
                error_code="ATTR_DEFINITION_CODE_DUPLICATE",
                message=f"属性定义编码已存在：{code}",
            )

    def list(
        self,
        keyword: str | None = None,
        data_type: str | None = None,
        resource_type: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[AttrDefinitionResponse]:
        stmt = select(MdAttrDefinition).where(MdAttrDefinition.is_deleted == False)

        if keyword:
            stmt = stmt.where(
                or_(
                    MdAttrDefinition.name.ilike(f"%{keyword}%"),
                    MdAttrDefinition.code.ilike(f"%{keyword}%"),
                )
            )
        if data_type:
            stmt = stmt.where(MdAttrDefinition.data_type == data_type)
        if resource_type:
            stmt = stmt.where(
                MdAttrDefinition.applicable_resource_types.contains(resource_type)
            )

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

        if payload.unit_id is not None:
            unit = self.db.execute(
                select(MdUnit).where(
                    MdUnit.id == payload.unit_id,
                    MdUnit.is_deleted == False,
                )
            ).scalar_one_or_none()
            if unit is None:
                raise ResourceNotFoundError(resource="单位", identifier=payload.unit_id)

        attr = MdAttrDefinition(
            **payload.model_dump(),
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(attr)
        self.db.flush()

        attr = self.db.execute(
            select(MdAttrDefinition)
            .where(MdAttrDefinition.id == attr.id)
            .options(selectinload(MdAttrDefinition.unit))
        ).scalar_one()
        return AttrDefinitionResponse.model_validate(attr)

    def update(
        self, attr_id: int, payload: AttrDefinitionUpdate, operator: str
    ) -> AttrDefinitionResponse:
        attr = self._get_or_404(attr_id)

        if payload.code is not None:
            self._assert_code_unique(payload.code, exclude_id=attr_id)

        if payload.unit_id is not None:
            unit = self.db.execute(
                select(MdUnit).where(
                    MdUnit.id == payload.unit_id,
                    MdUnit.is_deleted == False,
                )
            ).scalar_one_or_none()
            if unit is None:
                raise ResourceNotFoundError(resource="单位", identifier=payload.unit_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(attr, field, value)
        attr.updated_by = operator
        self.db.flush()

        attr = self.db.execute(
            select(MdAttrDefinition)
            .where(MdAttrDefinition.id == attr_id)
            .options(selectinload(MdAttrDefinition.unit))
        ).scalar_one()
        return AttrDefinitionResponse.model_validate(attr)

    def delete(self, attr_id: int, operator: str) -> None:
        attr = self._get_or_404(attr_id)

        attr.code = _build_deleted_unique_value(attr.code, attr.id, 30)
        attr.is_deleted = True
        attr.updated_by = operator
        self.db.flush()


# ══════════════════════════════════════════════════════════════════════════════
# 六、材料主数据服务
# ══════════════════════════════════════════════════════════════════════════════

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
        """校验分类类型必须为 MATERIAL"""
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
                detail={
                    "category_id": category_id,
                    "expected_type": "MATERIAL",
                    "actual_type": category.resource_type,
                },
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

        if payload.pricing_unit_id is not None:
            unit = self.db.execute(
                select(MdUnit).where(
                    MdUnit.id == payload.pricing_unit_id,
                    MdUnit.is_deleted == False,
                )
            ).scalar_one_or_none()
            if unit is None:
                raise ResourceNotFoundError(resource="计价单位", identifier=payload.pricing_unit_id)

        if payload.consumption_unit_id is not None:
            unit = self.db.execute(
                select(MdUnit).where(
                    MdUnit.id == payload.consumption_unit_id,
                    MdUnit.is_deleted == False,
                )
            ).scalar_one_or_none()
            if unit is None:
                raise ResourceNotFoundError(resource="消耗单位", identifier=payload.consumption_unit_id)

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

        if payload.pricing_unit_id is not None:
            unit = self.db.execute(
                select(MdUnit).where(
                    MdUnit.id == payload.pricing_unit_id,
                    MdUnit.is_deleted == False,
                )
            ).scalar_one_or_none()
            if unit is None:
                raise ResourceNotFoundError(resource="计价单位", identifier=payload.pricing_unit_id)

        if payload.consumption_unit_id is not None:
            unit = self.db.execute(
                select(MdUnit).where(
                    MdUnit.id == payload.consumption_unit_id,
                    MdUnit.is_deleted == False,
                )
            ).scalar_one_or_none()
            if unit is None:
                raise ResourceNotFoundError(resource="消耗单位", identifier=payload.consumption_unit_id)

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


# ══════════════════════════════════════════════════════════════════════════════
# 七、设备主数据服务
# ══════════════════════════════════════════════════════════════════════════════

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
        """校验分类类型必须为 EQUIPMENT"""
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
                detail={
                    "category_id": category_id,
                    "expected_type": "EQUIPMENT",
                    "actual_type": category.resource_type,
                },
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


# ══════════════════════════════════════════════════════════════════════════════
# 八、标准工艺/工时库服务
# ══════════════════════════════════════════════════════════════════════════════

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
            raise ResourceNotFoundError(resource="工序", identifier=process_id)
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
                message=f"工序编码已存在：{code}",
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

    def create(self, payload: ProcessCreate, operator: str) -> ProcessResponse:
        self._assert_code_unique(payload.code)

        resources_data = payload.resources
        process_data = payload.model_dump(exclude={"resources"})

        process = MdProcess(
            **process_data,
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(process)
        self.db.flush()

        for resource_data in resources_data:
            resource = MdProcessResource(
                process_id=process.id,
                **resource_data.model_dump(),
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

        if payload.code is not None:
            self._assert_code_unique(payload.code, exclude_id=process_id)

        update_data = payload.model_dump(exclude_unset=True)
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
            new_resources = [
                MdProcessResource(
                    process_id=new_process.id,
                    resource_type=resource.resource_type,
                    resource_id=resource.resource_id,
                    quantity=resource.quantity,
                    description=resource.description,
                    created_by=operator,
                    updated_by=operator,
                )
                for resource in source.resources
            ]
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
        from sqlalchemy.exc import IntegrityError

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

        resource = MdProcessResource(
            process_id=process_id,
            **payload.model_dump(),
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(resource)
        self.db.flush()

        return ProcessResourceResponse.model_validate(resource)

    def remove_resource(self, process_id: int, resource_id: int, operator: str) -> None:
        """移除工序的资源挂载"""
        resource = self.db.execute(
            select(MdProcessResource).where(
                MdProcessResource.id == resource_id,
                MdProcessResource.process_id == process_id,
            )
        ).scalar_one_or_none()
        if resource is None:
            raise ResourceNotFoundError(resource="工序资源挂载", identifier=resource_id)
        self.db.delete(resource)
        self.db.flush()


# ══════════════════════════════════════════════════════════════════════════════
# 九、人员技能资质矩阵服务
# ══════════════════════════════════════════════════════════════════════════════

class LaborService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, labor_id: int) -> MdLabor:
        labor = self.db.execute(
            select(MdLabor).where(
                MdLabor.id == labor_id,
                MdLabor.is_deleted == False,
            )
            .options(selectinload(MdLabor.category))
        ).scalar_one_or_none()
        if labor is None:
            raise ResourceNotFoundError(resource="人员", identifier=labor_id)
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
                message=f"人员编码已存在：{code}",
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
            raise ResourceNotFoundError(resource="人员分类", identifier=category_id)
        if category.resource_type != ResourceType.LABOR:
            raise BusinessRuleViolationError(
                error_code="LABOR_CATEGORY_TYPE_MISMATCH",
                message=f"人员分类类型不匹配：期望 LABOR，实际为 {category.resource_type}",
            )

    def list(
        self,
        keyword: str | None = None,
        labor_type: str | None = None,
        skill_level: SkillLevelSchema | None = None,
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
        if labor_type:
            stmt = stmt.where(MdLabor.labor_type == labor_type)
        if skill_level:
            stmt = stmt.where(MdLabor.skill_level == skill_level)
        if is_active is not None:
            stmt = stmt.where(MdLabor.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = stmt.options(selectinload(MdLabor.category))
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
        self._validate_category_type(payload.category_id)

        labor = MdLabor(
            **payload.model_dump(),
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(labor)
        self.db.flush()

        labor = self.db.execute(
            select(MdLabor)
            .where(MdLabor.id == labor.id)
            .options(selectinload(MdLabor.category))
        ).scalar_one()
        return LaborResponse.model_validate(labor)

    def update(
        self, labor_id: int, payload: LaborUpdate, operator: str
    ) -> LaborResponse:
        labor = self._get_or_404(labor_id)

        if payload.code is not None:
            self._assert_code_unique(payload.code, exclude_id=labor_id)

        if payload.category_id is not None:
            self._validate_category_type(payload.category_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(labor, field, value)
        labor.updated_by = operator
        self.db.flush()

        labor = self.db.execute(
            select(MdLabor)
            .where(MdLabor.id == labor_id)
            .options(selectinload(MdLabor.category))
        ).scalar_one()
        return LaborResponse.model_validate(labor)

    def delete(self, labor_id: int, operator: str) -> None:
        labor = self._get_or_404(labor_id)

        _check_process_resource_reference(
            self.db, ResourceType.LABOR, labor_id, f"人员【{labor.name}】"
        )

        labor.code = _build_deleted_unique_value(labor.code, labor.id, 50)
        labor.is_deleted = True
        labor.updated_by = operator
        self.db.flush()


# ══════════════════════════════════════════════════════════════════════════════
# 十、能源单价服务
# ══════════════════════════════════════════════════════════════════════════════

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

        if payload.code is not None:
            self._assert_code_unique(payload.code, exclude_id=rate_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rate, field, value)
        rate.updated_by = operator
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


# ══════════════════════════════════════════════════════════════════════════════
# 十一、能源日历服务
# ══════════════════════════════════════════════════════════════════════════════

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
