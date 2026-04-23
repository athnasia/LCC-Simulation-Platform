"""
工程建模域 Pydantic Schema

包含：
  - 项目（Project）的请求/响应模型
  - 产品（Product）的请求/响应模型
  - 设计方案（DesignScheme）的请求/响应模型
  - 设计方案版本（DesignSchemeVersion）的请求/响应模型
  - BOM 节点（BomNode）的请求/响应模型
  - 零件工艺路线（ComponentProcessRoute）的请求/响应模型
  - 路线步骤（RouteStepBind）的请求/响应模型
  - 模型快照（ModelSnapshot）的请求/响应模型

设计约定：
  1. 所有响应模型必须包含 id 和审计字段
  2. 所有创建/更新模型必须包含字段验证规则
  3. Decimal 类型字段必须设置精度约束
  4. 注意：is_deleted 字段为时间戳类型（BigInteger），不是 Boolean
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator


# ═══════════════════════════════════════════════════════════════════════════════
# 一、项目（Project）
# ═══════════════════════════════════════════════════════════════════════════════

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    code: str = Field(..., min_length=1, max_length=50, description="项目编码")
    description: str | None = Field(None, max_length=512, description="项目描述")
    is_active: bool = Field(True, description="是否启用")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=512)
    is_active: bool | None = None


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 二、产品（Product）
# ═══════════════════════════════════════════════════════════════════════════════

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="产品名称")
    code: str = Field(..., min_length=1, max_length=50, description="产品编码")
    project_id: int = Field(..., description="所属项目 ID")
    description: str | None = Field(None, max_length=512, description="产品描述")
    attributes: dict[str, Any] | None = Field(None, description="柔性属性（从基础字典与模板中拉取）")
    is_active: bool = Field(True, description="是否启用")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=512)
    attributes: dict[str, Any] | None = None
    is_active: bool | None = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 三、设计方案（DesignScheme）
# ═══════════════════════════════════════════════════════════════════════════════

class DesignSchemeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="方案名称")
    code: str = Field(..., min_length=1, max_length=50, description="方案编码")
    product_id: int = Field(..., description="所属产品 ID")
    description: str | None = Field(None, max_length=512, description="方案描述")
    is_active: bool = Field(True, description="是否启用")


class DesignSchemeCreate(DesignSchemeBase):
    pass


class DesignSchemeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=512)
    is_active: bool | None = None


class DesignSchemeResponse(DesignSchemeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 四、设计方案版本（DesignSchemeVersion）
# ═══════════════════════════════════════════════════════════════════════════════

class DesignSchemeVersionBase(BaseModel):
    scheme_id: int = Field(..., description="所属方案 ID")
    version: int = Field(..., ge=1, description="版本号")
    status: str = Field("DRAFT", description="状态（DRAFT/RELEASED/ARCHIVED）")
    description: str | None = Field(None, max_length=512, description="版本描述")


class DesignSchemeVersionCreate(DesignSchemeVersionBase):
    clone_from_version_id: int | None = Field(None, description="克隆源版本 ID（用于派生新版本）")


class DesignSchemeVersionUpdate(BaseModel):
    status: str | None = None
    description: str | None = Field(None, max_length=512)


class DesignSchemeVersionResponse(DesignSchemeVersionBase):
    id: int
    released_at: datetime | None
    released_by: str | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 五、BOM 节点（BomNode）
# ═══════════════════════════════════════════════════════════════════════════════

class BomNodeUnitBrief(BaseModel):
    """BOM 节点单位简要信息"""
    id: int
    name: str
    code: str
    symbol: str | None

    class Config:
        from_attributes = True


class BomNodeBase(BaseModel):
    scheme_version_id: int = Field(..., description="所属方案版本 ID")
    parent_id: int | None = Field(None, description="父节点 ID")
    node_name: str = Field(..., min_length=1, max_length=100, description="节点名称")
    code: str = Field(..., min_length=1, max_length=50, description="节点编码")
    node_type: str = Field("PART", description="节点类型（PART/ASSEMBLY）")
    quantity: Decimal | None = Field(None, ge=0, description="数量")
    unit_id: int | None = Field(None, description="单位 ID")
    sort_order: int = Field(0, ge=0, description="排序值")
    is_configured: bool = Field(False, description="是否已配置工艺路线")
    attributes: dict[str, Any] | None = Field(None, description="柔性属性（从基础字典与模板中拉取）")
    description: str | None = Field(None, max_length=512, description="节点描述")


class BomNodeCreate(BomNodeBase):
    pass


class BomNodeUpdate(BaseModel):
    node_name: str | None = Field(None, min_length=1, max_length=100)
    node_type: str | None = None
    quantity: Decimal | None = Field(None, ge=0)
    unit_id: int | None = None
    sort_order: int | None = Field(None, ge=0)
    is_configured: bool | None = None
    attributes: dict[str, Any] | None = None
    description: str | None = Field(None, max_length=512)


class BomNodeResponse(BomNodeBase):
    id: int
    unit: BomNodeUnitBrief | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


class BomNodeTreeResponse(BomNodeResponse):
    """BOM 节点树形响应模型"""
    children: list["BomNodeTreeResponse"] = Field(default_factory=list, description="子节点列表")


# ═══════════════════════════════════════════════════════════════════════════════
# 六、零件工艺路线（ComponentProcessRoute）
# ═══════════════════════════════════════════════════════════════════════════════

class ComponentProcessRouteBase(BaseModel):
    bom_node_id: int = Field(..., description="所属 BOM 节点 ID")
    route_name: str = Field(..., min_length=1, max_length=100, description="路线名称")
    route_code: str = Field(..., min_length=1, max_length=50, description="路线编码")
    description: str | None = Field(None, max_length=512, description="路线描述")
    is_active: bool = Field(True, description="是否启用")


class ComponentProcessRouteCreate(ComponentProcessRouteBase):
    pass


class ComponentProcessRouteUpdate(BaseModel):
    route_name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=512)
    is_active: bool | None = None


class ComponentProcessRouteResponse(ComponentProcessRouteBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 七、路线步骤（RouteStepBind）
# ═══════════════════════════════════════════════════════════════════════════════

class RouteStepBindBase(BaseModel):
    route_id: int = Field(..., description="所属路线 ID")
    process_id: int = Field(..., description="标准工艺 ID")
    step_order: int = Field(..., ge=1, description="工序顺序")
    process_type: str = Field("IN_HOUSE", description="加工方式（IN_HOUSE=自制，OUTSOURCED=外协）")
    override_equipment_id: int | None = Field(None, description="覆写设备 ID（自制时使用）")
    outsource_price: Decimal | None = Field(None, ge=0, description="外协单价（外协时使用）")
    override_t_set: Decimal | None = Field(None, ge=0, description="覆写准备工时（h）")
    override_t_run: Decimal | None = Field(None, ge=0, description="覆写运行工时（h）")
    override_mat_params: dict[str, Any] | None = Field(
        None, 
        description="覆写辅材参数（如：{'M_T_001': 2.0, 'LIQUID_01': 0.5}）"
    )
    description: str | None = Field(None, max_length=512, description="步骤描述")


class RouteStepBindCreate(RouteStepBindBase):
    pass


class RouteStepBindUpdate(BaseModel):
    step_order: int | None = Field(None, ge=1)
    process_type: str | None = None
    override_equipment_id: int | None = None
    outsource_price: Decimal | None = Field(None, ge=0)
    override_t_set: Decimal | None = Field(None, ge=0)
    override_t_run: Decimal | None = Field(None, ge=0)
    override_mat_params: dict[str, Any] | None = None
    description: str | None = Field(None, max_length=512)


class RouteStepBindResponse(RouteStepBindBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


class RouteStepBindWithProcessResponse(RouteStepBindResponse):
    """路线步骤响应模型（包含标准工艺信息）"""
    process: dict[str, Any] = Field(default_factory=dict, description="标准工艺信息")


# ═══════════════════════════════════════════════════════════════════════════════
# 八、模型快照（ModelSnapshot）
# ═══════════════════════════════════════════════════════════════════════════════

class ModelSnapshotBase(BaseModel):
    scheme_version_id: int = Field(..., description="所属方案版本 ID")
    snapshot_code: str = Field(..., min_length=1, max_length=50, description="快照编码")
    snapshot_name: str = Field(..., min_length=1, max_length=100, description="快照名称")
    snapshot_data: dict[str, Any] = Field(..., description="快照数据")
    simulation_result: dict[str, Any] | None = Field(None, description="LCC 仿真结果")
    status: str = Field("DRAFT", description="状态（DRAFT/READY/SIMULATING/COMPLETED/FAILED/ARCHIVED）")
    description: str | None = Field(None, max_length=512, description="快照描述")


class ModelSnapshotCreate(BaseModel):
    """快照创建请求模型（不包含 snapshot_data，由后端生成）"""
    scheme_version_id: int = Field(..., description="所属方案版本 ID")
    snapshot_code: str = Field(..., min_length=1, max_length=50, description="快照编码")
    snapshot_name: str = Field(..., min_length=1, max_length=100, description="快照名称")
    description: str | None = Field(None, max_length=512, description="快照描述")


class ModelSnapshotUpdate(BaseModel):
    snapshot_name: str | None = Field(None, min_length=1, max_length=100)
    status: str | None = None
    description: str | None = Field(None, max_length=512)


class ModelSnapshotResponse(ModelSnapshotBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# 九、快照生成请求/响应
# ═══════════════════════════════════════════════════════════════════════════════

class GenerateSnapshotRequest(BaseModel):
    """生成快照请求模型"""
    scheme_version_id: int = Field(..., description="方案版本 ID")
    snapshot_name: str = Field(..., min_length=1, max_length=100, description="快照名称")
    description: str | None = Field(None, max_length=512, description="快照描述")


class GenerateSnapshotResponse(BaseModel):
    """生成快照响应模型"""
    snapshot_id: int = Field(..., description="快照 ID")
    snapshot_code: str = Field(..., description="快照编码")
    snapshot_name: str = Field(..., description="快照名称")
    status: str = Field(..., description="快照状态")
    created_at: datetime = Field(..., description="创建时间")
