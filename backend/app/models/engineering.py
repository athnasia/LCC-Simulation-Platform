"""
工程建模域 ORM 模型

包含：
  - EngProject：项目
  - EngProduct：产品
  - EngDesignScheme：设计方案
  - EngDesignSchemeVersion：设计方案版本
  - EngBomNode：BOM 节点树
  - EngComponentProcessRoute：零件工艺路线主表
  - EngRouteStepBind：路线步骤与资源明细
  - EngModelSnapshot：模型快照

设计约定：
  1. 所有表必须继承 AuditMixin 基类，包含标准审计字段
  2. 严格支持版本号 (version) 管理，禁止直接覆盖更新
  3. 所有关键业务对象支持逻辑删除
  4. 依赖 AuditMixin 中的 is_deleted (时间戳) 实现逻辑删除唯一性
"""

from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base


# ── 项目 ───────────────────────────────────────────────────────────────────

class EngProject(AuditMixin, Base):
    __tablename__ = "eng_project"
    __table_args__ = (
        # 依赖 AuditMixin 中的 is_deleted (时间戳) 实现逻辑删除唯一性
        UniqueConstraint("code", "is_deleted", name="uq_eng_project_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="项目名称")
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="项目编码")
    description: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="项目描述")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用"
    )

    products: Mapped[list["EngProduct"]] = relationship(
        "EngProduct", back_populates="project", cascade="all, delete-orphan"
    )


# ── 产品 ───────────────────────────────────────────────────────────────────

class EngProduct(AuditMixin, Base):
    __tablename__ = "eng_product"
    __table_args__ = (
        # 依赖 AuditMixin 中的 is_deleted (时间戳) 实现逻辑删除唯一性
        UniqueConstraint("code", "is_deleted", name="uq_eng_product_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="产品名称")
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="产品编码")
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("eng_project.id"), nullable=False, comment="所属项目 ID"
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="产品描述")
    attributes: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="柔性属性（从基础字典与模板中拉取）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用"
    )

    project: Mapped["EngProject"] = relationship("EngProject", back_populates="products")
    design_schemes: Mapped[list["EngDesignScheme"]] = relationship(
        "EngDesignScheme", back_populates="product", cascade="all, delete-orphan"
    )


# ── 设计方案 ───────────────────────────────────────────────────────────────────

class EngDesignScheme(AuditMixin, Base):
    __tablename__ = "eng_design_scheme"
    __table_args__ = (
        # 依赖 AuditMixin 中的 is_deleted (时间戳) 实现逻辑删除唯一性
        UniqueConstraint("code", "is_deleted", name="uq_eng_design_scheme_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="方案名称")
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="方案编码")
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("eng_product.id"), nullable=False, comment="所属产品 ID"
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="方案描述")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用"
    )

    product: Mapped["EngProduct"] = relationship("EngProduct", back_populates="design_schemes")
    versions: Mapped[list["EngDesignSchemeVersion"]] = relationship(
        "EngDesignSchemeVersion", back_populates="scheme", cascade="all, delete-orphan"
    )


# ── 设计方案版本 ───────────────────────────────────────────────────────────────────

class EngDesignSchemeVersion(AuditMixin, Base):
    __tablename__ = "eng_design_scheme_version"
    __table_args__ = (
        # 依赖 AuditMixin 中的 is_deleted (时间戳) 实现逻辑删除唯一性
        UniqueConstraint(
            "scheme_id", "version", "is_deleted", 
            name="uq_eng_design_scheme_version_unique"
        ),
    )

    scheme_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("eng_design_scheme.id"), nullable=False, comment="所属方案 ID"
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, comment="版本号")
    status: Mapped[str] = mapped_column(
        String(20), default="DRAFT", comment="状态（DRAFT/RELEASED/ARCHIVED）"
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="版本描述")
    released_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="发布时间"
    )
    released_by: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="发布人用户 ID"
    )

    scheme: Mapped["EngDesignScheme"] = relationship("EngDesignScheme", back_populates="versions")
    bom_nodes: Mapped[list["EngBomNode"]] = relationship(
        "EngBomNode", back_populates="scheme_version", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list["EngModelSnapshot"]] = relationship(
        "EngModelSnapshot", back_populates="scheme_version", cascade="all, delete-orphan"
    )


# ── BOM 节点树 ───────────────────────────────────────────────────────────────────

class EngBomNode(AuditMixin, Base):
    __tablename__ = "eng_bom_node"
    __table_args__ = (
        # 依赖 AuditMixin 中的 is_deleted (时间戳) 实现逻辑删除唯一性
        UniqueConstraint(
            "scheme_version_id", "code", "is_deleted", 
            name="uq_eng_bom_node_code_unique"
        ),
    )

    scheme_version_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("eng_design_scheme_version.id"), 
        nullable=False, 
        comment="所属方案版本 ID"
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, 
        ForeignKey("eng_bom_node.id"), 
        nullable=True, 
        comment="父节点 ID（NULL 表示根节点）"
    )
    node_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="节点名称")
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="节点编码")
    node_type: Mapped[str] = mapped_column(
        String(20), default="PART", comment="节点类型（PART/ASSEMBLY）"
    )
    quantity: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True, comment="数量"
    )
    unit_id: Mapped[int | None] = mapped_column(
        BigInteger, 
        ForeignKey("md_unit.id"), 
        nullable=True, 
        comment="单位 ID"
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序值")
    is_configured: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", comment="是否已配置工艺路线"
    )
    attributes: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="柔性属性（从基础字典与模板中拉取）"
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="节点描述")

    scheme_version: Mapped["EngDesignSchemeVersion"] = relationship(
        "EngDesignSchemeVersion", back_populates="bom_nodes"
    )
    parent: Mapped["EngBomNode | None"] = relationship(
        "EngBomNode", remote_side="EngBomNode.id", back_populates="children"
    )
    children: Mapped[list["EngBomNode"]] = relationship(
        "EngBomNode", back_populates="parent", cascade="all, delete-orphan"
    )
    unit: Mapped["MdUnit | None"] = relationship("MdUnit")
    process_routes: Mapped[list["EngComponentProcessRoute"]] = relationship(
        "EngComponentProcessRoute", back_populates="bom_node", cascade="all, delete-orphan"
    )


# ── 零件工艺路线主表 ───────────────────────────────────────────────────────────────────

class EngComponentProcessRoute(AuditMixin, Base):
    __tablename__ = "eng_component_process_route"
    __table_args__ = (
        # 依赖 AuditMixin 中的 is_deleted (时间戳) 实现逻辑删除唯一性
        UniqueConstraint(
            "bom_node_id", "route_code", "is_deleted", 
            name="uq_eng_component_process_route_unique"
        ),
    )

    bom_node_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("eng_bom_node.id"), 
        nullable=False, 
        comment="所属 BOM 节点 ID"
    )
    route_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="路线名称")
    route_code: Mapped[str] = mapped_column(String(50), nullable=False, comment="路线编码")
    description: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="路线描述")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", comment="是否启用"
    )

    bom_node: Mapped["EngBomNode"] = relationship(
        "EngBomNode", back_populates="process_routes"
    )
    steps: Mapped[list["EngRouteStepBind"]] = relationship(
        "EngRouteStepBind", back_populates="route", cascade="all, delete-orphan"
    )


# ── 路线步骤与资源明细 ───────────────────────────────────────────────────────────────────

class EngRouteStepBind(AuditMixin, Base):
    __tablename__ = "eng_route_step_bind"
    __table_args__ = (
        # 依赖 AuditMixin 中的 is_deleted (时间戳) 实现逻辑删除唯一性
        UniqueConstraint(
            "route_id", "step_order", "is_deleted", 
            name="uq_eng_route_step_bind_unique"
        ),
    )

    route_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("eng_component_process_route.id"), 
        nullable=False, 
        comment="所属路线 ID"
    )
    process_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("md_process.id"), 
        nullable=False, 
        comment="标准工艺 ID（来自主数据域）"
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False, comment="工序顺序")
    
    process_type: Mapped[str] = mapped_column(
        String(20), default="IN_HOUSE", nullable=False, comment="加工方式（IN_HOUSE=自制，OUTSOURCED=外协）"
    )
    override_equipment_id: Mapped[int | None] = mapped_column(
        BigInteger, 
        ForeignKey("md_equipment.id"), 
        nullable=True, 
        comment="覆写设备 ID（自制时使用）"
    )
    outsource_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, comment="外协单价（外协时使用）"
    )
    
    override_t_set: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True, comment="覆写准备工时（h）"
    )
    override_t_run: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True, comment="覆写运行工时（h）"
    )
    override_mat_params: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="覆写辅材参数（如：{'M_T_001': 2.0, 'LIQUID_01': 0.5}）"
    )
    
    description: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="步骤描述")

    route: Mapped["EngComponentProcessRoute"] = relationship(
        "EngComponentProcessRoute", back_populates="steps"
    )
    process: Mapped["MdProcess"] = relationship("MdProcess")
    equipment: Mapped["MdEquipment | None"] = relationship("MdEquipment")


# ── 模型快照 ───────────────────────────────────────────────────────────────────────────

class EngModelSnapshot(AuditMixin, Base):
    __tablename__ = "eng_model_snapshot"
    __table_args__ = (
        # 依赖 AuditMixin 中的 is_deleted (时间戳) 实现逻辑删除唯一性
        UniqueConstraint(
            "scheme_version_id", "snapshot_code", "is_deleted", 
            name="uq_eng_model_snapshot_unique"
        ),
    )

    scheme_version_id: Mapped[int] = mapped_column(
        BigInteger, 
        ForeignKey("eng_design_scheme_version.id"), 
        nullable=False, 
        comment="所属方案版本 ID"
    )
    snapshot_code: Mapped[str] = mapped_column(String(50), nullable=False, comment="快照编码")
    snapshot_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="快照名称")
    snapshot_data: Mapped[dict] = mapped_column(
        JSON, nullable=False, comment="快照数据（包含 BOM 树、工艺路线、资源费率等完整信息）"
    )
    simulation_result: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="LCC 仿真结果（时间轴事件、总成本、异常信息）"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="DRAFT", comment="状态（DRAFT/READY/SIMULATING/COMPLETED/FAILED/ARCHIVED）"
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="快照描述")

    scheme_version: Mapped["EngDesignSchemeVersion"] = relationship(
        "EngDesignSchemeVersion", back_populates="snapshots"
    )
