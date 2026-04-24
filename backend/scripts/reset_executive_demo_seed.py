r"""高管演示用核心种子数据重置脚本。

执行方式：
    cd E:\code\lcc-app\backend
    .\.venv\Scripts\python.exe scripts\reset_executive_demo_seed.py

脚本行为：
1. 保留现有 sys_permission 基线，不触碰权限点定义。
2. 清空部门、用户、角色及其关联，重建唯一超级管理员账号。
3. 清空材料、设备、人工、能源、LCC 财务评估基准等演示业务数据。
4. 注入一套“年产万吨级聚碳酸酯(PC)”场景主数据。

说明：
- 当前仓库未定义 sys_menu ORM / 表结构，本脚本不会处理不存在的 sys_menu。
- 当前 LCC 财务评估基准模型无独立 code 字段，因此将编码并入 rule_name。
"""

from __future__ import annotations

from decimal import Decimal
import os
import sys

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.engineering import LccFinancialBaseline
from app.models.master_data import (
    EnergyType,
    MdEnergyCalendar,
    MdEnergyRate,
    MdEquipment,
    MdLabor,
    MdMaterial,
    MdResourceCategory,
    MdUnit,
    ResourceType,
    SkillLevel,
)
from app.models.system import (
    OrgDepartment,
    SysPermission,
    SysRole,
    SysRolePermission,
    SysUser,
    SysUserRole,
)


def get_unit(db: Session, code: str) -> MdUnit:
    unit = db.execute(
        select(MdUnit).where(MdUnit.code == code, MdUnit.is_deleted == False)
    ).scalar_one_or_none()
    if unit is None:
        raise ValueError(f"未找到单位：{code}")
    return unit


def get_or_create_category(
    db: Session,
    *,
    code: str,
    name: str,
    resource_type: ResourceType,
    parent_code: str | None = None,
    description: str | None = None,
    sort_order: int = 0,
) -> MdResourceCategory:
    category = db.execute(
        select(MdResourceCategory).where(
            MdResourceCategory.code == code,
            MdResourceCategory.is_deleted == False,
        )
    ).scalar_one_or_none()

    parent_id = None
    if parent_code:
      parent = db.execute(
          select(MdResourceCategory).where(
              MdResourceCategory.code == parent_code,
              MdResourceCategory.is_deleted == False,
          )
      ).scalar_one_or_none()
      if parent is None:
          raise ValueError(f"未找到父分类：{parent_code}")
      parent_id = parent.id

    if category is None:
        category = MdResourceCategory(
            code=code,
            name=name,
            resource_type=resource_type,
            parent_id=parent_id,
            description=description,
            sort_order=sort_order,
            is_active=True,
            created_by="seed",
            updated_by="seed",
        )
        db.add(category)
        db.flush()
        print(f"[+] 创建资源分类：{name} ({code})")
        return category

    changed = False
    if category.name != name:
        category.name = name
        changed = True
    if category.resource_type != resource_type:
        category.resource_type = resource_type
        changed = True
    if category.parent_id != parent_id:
        category.parent_id = parent_id
        changed = True
    if category.description != description:
        category.description = description
        changed = True
    if category.sort_order != sort_order:
        category.sort_order = sort_order
        changed = True
    if not category.is_active:
        category.is_active = True
        changed = True

    if changed:
        category.updated_by = "seed"
        db.flush()
        print(f"[~] 更新资源分类：{name} ({code})")

    return category


def reset_system_security_data(db: Session) -> None:
    print("[Step 1] 重置系统用户/角色/部门数据...")

    permission_ids = db.execute(
        select(SysPermission.id).where(SysPermission.is_deleted == False)
    ).scalars().all()
    if not permission_ids:
        raise ValueError("未找到任何权限点，无法创建 SUPER_ADMIN")

    db.execute(delete(SysUserRole))
    db.execute(delete(SysRolePermission))
    db.execute(delete(SysUser))
    db.execute(delete(SysRole))
    db.execute(update(OrgDepartment).values(parent_id=None))
    db.execute(delete(OrgDepartment))

    super_admin_role = SysRole(
        name="超级管理员",
        code="SUPER_ADMIN",
        description="高管演示环境唯一超级管理员，持有全部权限点",
        is_active=True,
        created_by="seed",
        updated_by="seed",
    )
    db.add(super_admin_role)
    db.flush()

    db.add_all(
        [
            SysRolePermission(
                role_id=super_admin_role.id,
                permission_id=permission_id,
                created_by="seed",
                updated_by="seed",
            )
            for permission_id in permission_ids
        ]
    )

    admin_user = SysUser(
        username="admin",
        hashed_password=hash_password("123456"),
        real_name="超级管理员",
        email=None,
        phone=None,
        is_active=True,
        department_id=None,
        created_by="seed",
        updated_by="seed",
    )
    db.add(admin_user)
    db.flush()

    db.add(
        SysUserRole(
            user_id=admin_user.id,
            role_id=super_admin_role.id,
            created_by="seed",
            updated_by="seed",
        )
    )

    print(f"    - 已重建用户：admin (id={admin_user.id})")
    print(f"    - 已重建角色：SUPER_ADMIN (id={super_admin_role.id})")
    print(f"    - 已绑定权限点：{len(permission_ids)} 条")


def reset_master_data(db: Session) -> None:
    print("[Step 2] 清理演示业务主数据...")
    db.execute(delete(MdEnergyCalendar))
    db.execute(delete(MdEnergyRate))
    db.execute(delete(MdLabor))
    db.execute(delete(MdEquipment))
    db.execute(delete(MdMaterial))
    db.execute(delete(LccFinancialBaseline))

    print("[Step 3] 准备注入演示分类与单位映射...")
    ton = get_unit(db, "t")
    meter = get_unit(db, "m")
    hour = get_unit(db, "h")
    kwh = get_unit(db, "kWh")

    material_raw = get_or_create_category(
        db,
        code="DEMO_PC_MATERIAL_RAW",
        name="PC 原料",
        resource_type=ResourceType.MATERIAL,
        parent_code="MATERIAL",
        description="聚碳酸酯装置原料",
        sort_order=101,
    )
    material_aux = get_or_create_category(
        db,
        code="DEMO_PC_MATERIAL_AUX",
        name="PC 辅料",
        resource_type=ResourceType.MATERIAL,
        parent_code="MATERIAL",
        description="聚碳酸酯装置辅料",
        sort_order=102,
    )
    material_spare = get_or_create_category(
        db,
        code="DEMO_PC_MATERIAL_SPARE",
        name="PC 关键备件",
        resource_type=ResourceType.MATERIAL,
        parent_code="MATERIAL",
        description="聚碳酸酯装置关键耐蚀备件",
        sort_order=103,
    )
    equipment_reaction = get_or_create_category(
        db,
        code="DEMO_PC_EQUIP_REACTION",
        name="PC 聚合反应设备",
        resource_type=ResourceType.EQUIPMENT,
        parent_code="EQUIPMENT_PROCESSING",
        description="聚碳酸酯聚合核心反应设备",
        sort_order=101,
    )
    equipment_post = get_or_create_category(
        db,
        code="DEMO_PC_EQUIP_POST",
        name="PC 后处理设备",
        resource_type=ResourceType.EQUIPMENT,
        parent_code="EQUIPMENT_PROCESSING",
        description="聚碳酸酯离心与后处理设备",
        sort_order=102,
    )
    labor_operation = get_or_create_category(
        db,
        code="DEMO_PC_LABOR_OPERATION",
        name="PC 生产操作岗",
        resource_type=ResourceType.LABOR,
        parent_code="LABOR",
        description="聚碳酸酯装置操作岗位",
        sort_order=101,
    )
    labor_maint = get_or_create_category(
        db,
        code="DEMO_PC_LABOR_MAINT",
        name="PC 设备维保岗",
        resource_type=ResourceType.LABOR,
        parent_code="LABOR",
        description="聚碳酸酯装置设备维保岗位",
        sort_order=102,
    )

    print("[Step 4] 注入物料与材料台账...")
    material_rows = [
        MdMaterial(
            code="RM-001",
            name="双酚A (BPA)",
            category_id=material_raw.id,
            pricing_unit_id=ton.id,
            consumption_unit_id=ton.id,
            unit_price=Decimal("12500.0000"),
            dynamic_attributes={
                "material_type": "原料",
                "specification": "工业级 >=99.5%",
                "industry_scene": "聚碳酸酯界面缩聚",
            },
            is_active=True,
            description="PC 核心原料，纯度要求高，直接影响分子量与色相",
            created_by="seed",
            updated_by="seed",
        ),
        MdMaterial(
            code="RM-002",
            name="光气 (Phosgene)",
            category_id=material_raw.id,
            pricing_unit_id=ton.id,
            consumption_unit_id=ton.id,
            unit_price=Decimal("4200.0000"),
            dynamic_attributes={
                "material_type": "原料",
                "specification": "剧毒/自制",
                "safety_level": "HIGH_RISK",
            },
            is_active=True,
            description="PC 界面缩聚关键原料，剧毒且通常园区内配套自制",
            created_by="seed",
            updated_by="seed",
        ),
        MdMaterial(
            code="RM-003",
            name="氢氧化钠 (NaOH)",
            category_id=material_aux.id,
            pricing_unit_id=ton.id,
            consumption_unit_id=ton.id,
            unit_price=Decimal("900.0000"),
            dynamic_attributes={
                "material_type": "辅料",
                "specification": "32% 液碱",
            },
            is_active=True,
            description="界面缩聚体系常用碱液辅料，用于中和与工艺稳定",
            created_by="seed",
            updated_by="seed",
        ),
        MdMaterial(
            code="SP-001",
            name="304 不锈钢管材",
            category_id=material_spare.id,
            pricing_unit_id=meter.id,
            consumption_unit_id=meter.id,
            unit_price=Decimal("150.0000"),
            dynamic_attributes={
                "material_type": "备件",
                "specification": "Φ108×4",
                "material_grade": "304",
            },
            is_active=True,
            description="普通耐蚀等级备件，适合低腐蚀工段但寿命有限",
            created_by="seed",
            updated_by="seed",
        ),
        MdMaterial(
            code="SP-002",
            name="哈氏合金 C276",
            category_id=material_spare.id,
            pricing_unit_id=meter.id,
            consumption_unit_id=meter.id,
            unit_price=Decimal("1800.0000"),
            dynamic_attributes={
                "material_type": "备件",
                "specification": "Φ108×4",
                "material_grade": "Hastelloy C276",
            },
            is_active=True,
            description="高耐蚀关键备件，用于强腐蚀反应段的长寿命方案",
            created_by="seed",
            updated_by="seed",
        ),
    ]
    db.add_all(material_rows)

    print("[Step 5] 注入设备资产台账...")
    equipment_rows = [
        MdEquipment(
            code="EQ-R001",
            name="普通聚合反应釜",
            category_id=equipment_reaction.id,
            depreciation_rate=Decimal("380.0000"),
            power_consumption=Decimal("250.0000"),
            dynamic_attributes={
                "purchase_value": 5000000,
                "rated_power_kw": 250,
                "annual_maintenance_base": 200000,
                "vessel_material": "304 不锈钢",
            },
            is_active=True,
            description="304材质，易腐蚀需频修，适用于常规投资方案演示",
            created_by="seed",
            updated_by="seed",
        ),
        MdEquipment(
            code="EQ-R002",
            name="特材聚合反应釜",
            category_id=equipment_reaction.id,
            depreciation_rate=Decimal("910.0000"),
            power_consumption=Decimal("220.0000"),
            dynamic_attributes={
                "purchase_value": 12000000,
                "rated_power_kw": 220,
                "annual_maintenance_base": 50000,
                "vessel_material": "哈氏合金内衬",
            },
            is_active=True,
            description="哈氏合金内衬，导热更好且显著降低腐蚀性维保负担",
            created_by="seed",
            updated_by="seed",
        ),
        MdEquipment(
            code="EQ-C001",
            name="离心分离机",
            category_id=equipment_post.id,
            depreciation_rate=Decimal("120.0000"),
            power_consumption=Decimal("180.0000"),
            dynamic_attributes={
                "purchase_value": 1500000,
                "rated_power_kw": 180,
                "annual_maintenance_base": 80000,
            },
            is_active=True,
            description="通用后处理设备，用于聚合后固液分离与产品后处理",
            created_by="seed",
            updated_by="seed",
        ),
    ]
    db.add_all(equipment_rows)

    print("[Step 6] 注入能源与人工费率...")
    labor_rows = [
        MdLabor(
            code="LB-OP",
            name="中级主操工",
            labor_type="主操工",
            skill_level=SkillLevel.INTERMEDIATE,
            hourly_rate=Decimal("65.00"),
            qualification_code="PC-OP-INT",
            category_id=labor_operation.id,
            is_active=True,
            description="负责聚碳酸酯装置中控与现场联动操作",
            created_by="seed",
            updated_by="seed",
        ),
        MdLabor(
            code="LB-ENG",
            name="高级设备管工",
            labor_type="设备管工",
            skill_level=SkillLevel.SENIOR,
            hourly_rate=Decimal("150.00"),
            qualification_code="PC-MAINT-SR",
            category_id=labor_maint.id,
            is_active=True,
            description="负责强腐蚀工况下的检修、焊补与更换作业",
            created_by="seed",
            updated_by="seed",
        ),
    ]
    db.add_all(labor_rows)

    energy_rows = [
        MdEnergyRate(
            code="EN-ELEC",
            name="工业用电",
            energy_type=EnergyType.ELECTRICITY,
            unit_price=Decimal("0.7500"),
            unit_id=kwh.id,
            is_active=True,
            description="PC 装置工业用电基准单价",
            created_by="seed",
            updated_by="seed",
        ),
        MdEnergyRate(
            code="EN-STM",
            name="工业蒸汽",
            energy_type=EnergyType.STEAM,
            unit_price=Decimal("280.0000"),
            unit_id=ton.id,
            is_active=True,
            description="PC 装置蒸汽热源基准单价",
            created_by="seed",
            updated_by="seed",
        ),
    ]
    db.add_all(energy_rows)

    print("[Step 7] 注入 LCC 财务评估基准...")
    baseline_rows = [
        LccFinancialBaseline(
            rule_name="BS-NORM | 常规强腐蚀评估",
            lifecycle_years=15,
            discount_rate=Decimal("8.0000"),
            corrosion_rate=Decimal("6.5000"),
            risk_strategy="FIXED",
            risk_value=Decimal("50000.0000"),
            eol_salvage_rate=Decimal("2.0000"),
            is_active=True,
            created_by="seed",
            updated_by="seed",
        ),
        LccFinancialBaseline(
            rule_name="BS-HIGH | 特材免维护评估",
            lifecycle_years=15,
            discount_rate=Decimal("8.0000"),
            corrosion_rate=Decimal("1.5000"),
            risk_strategy="FIXED",
            risk_value=Decimal("10000.0000"),
            eol_salvage_rate=Decimal("8.0000"),
            is_active=True,
            created_by="seed",
            updated_by="seed",
        ),
    ]
    db.add_all(baseline_rows)

    print("    - 物料 5 条")
    print("    - 设备 3 条")
    print("    - 人工 2 条")
    print("    - 能源 2 条")
    print("    - 财务基准 2 条")
    print(f"    - 参考单位：吨({ton.code}) / 米({meter.code}) / 小时({hour.code}) / 千瓦时({kwh.code})")


def main() -> None:
    db = SessionLocal()
    try:
        reset_system_security_data(db)
        reset_master_data(db)
        db.commit()
        print("[Done] 演示种子数据已提交。")
    except Exception as exc:
        db.rollback()
        print(f"[Rollback] 演示种子数据初始化失败，已回滚：{exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()