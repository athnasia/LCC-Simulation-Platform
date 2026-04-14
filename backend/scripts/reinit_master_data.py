"""重新初始化主数据种子数据（修复乱码）

执行方式：在 backend 目录下运行
    .\.venv\Scripts\python.exe scripts\reinit_master_data.py
"""
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from datetime import time

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.master_data import (
    MdAttrDefinition,
    MdEnergyCalendar,
    MdEnergyRate,
    MdProcess,
    MdResourceCategory,
    MdUnit,
    MdUnitConversion,
    MdUnitDimension,
    EnergyType,
    ResourceType,
    SkillLevel,
)


def clear_master_data(db: Session) -> None:
    """清理主数据表（保留量纲和单位）"""
    print("清理主数据表...")

    from app.models.master_data import MdProcessResource, MdMaterial, MdEquipment, MdLabor

    # 清理能源日历
    db.execute(delete(MdEnergyCalendar))
    # 清理能源单价
    db.execute(delete(MdEnergyRate))
    # 清理工序资源挂载
    db.execute(delete(MdProcessResource))
    # 清理工序
    db.execute(delete(MdProcess))
    # 清理材料（引用资源分类）
    db.execute(delete(MdMaterial))
    # 清理设备（引用资源分类）
    db.execute(delete(MdEquipment))
    # 清理人员（引用资源分类）
    db.execute(delete(MdLabor))
    # 清理属性定义
    db.execute(delete(MdAttrDefinition))
    # 清理资源分类
    db.execute(delete(MdResourceCategory))

    db.commit()
    print("清理完成")


def init_resource_categories(db: Session) -> dict[str, int]:
    """初始化资源分类"""
    print("初始化资源分类...")

    categories = [
        {"name": "金属材料", "code": "CAT_METAL", "resource_type": ResourceType.MATERIAL, "description": "金属材料分类"},
        {"name": "非金属材料", "code": "CAT_NON_METAL", "resource_type": ResourceType.MATERIAL, "description": "非金属材料分类"},
        {"name": "加工设备", "code": "CAT_MACHINING", "resource_type": ResourceType.EQUIPMENT, "description": "加工设备分类"},
        {"name": "检测设备", "code": "CAT_INSPECTION", "resource_type": ResourceType.EQUIPMENT, "description": "检测设备分类"},
        {"name": "焊接工", "code": "CAT_WELDER", "resource_type": ResourceType.LABOR, "description": "焊接工种"},
        {"name": "装配工", "code": "CAT_ASSEMBLER", "resource_type": ResourceType.LABOR, "description": "装配工种"},
    ]

    category_ids = {}
    for cat_data in categories:
        cat = MdResourceCategory(
            name=cat_data["name"],
            code=cat_data["code"],
            resource_type=cat_data["resource_type"],
            description=cat_data.get("description"),
            created_by="system",
            updated_by="system",
        )
        db.add(cat)
        db.flush()
        category_ids[cat_data["code"]] = cat.id

    db.commit()
    print(f"已创建 {len(categories)} 个资源分类")
    return category_ids


def init_attr_definitions(db: Session) -> None:
    """初始化属性定义"""
    print("初始化属性定义...")

    attrs = [
        {"name": "密度", "code": "density", "data_type": "NUMBER", "unit_code": "kg/m3", "applicable_resource_types": ["MATERIAL"], "description": "材料密度", "is_required": False},
        {"name": "硬度", "code": "hardness", "data_type": "NUMBER", "unit_code": None, "applicable_resource_types": ["MATERIAL"], "description": "材料硬度（HRC）", "is_required": False},
        {"name": "抗拉强度", "code": "tensile_strength", "data_type": "NUMBER", "unit_code": "MPa", "applicable_resource_types": ["MATERIAL"], "description": "材料抗拉强度", "is_required": False},
        {"name": "屈服强度", "code": "yield_strength", "data_type": "NUMBER", "unit_code": "MPa", "applicable_resource_types": ["MATERIAL"], "description": "材料屈服强度", "is_required": False},
        {"name": "额定功率", "code": "rated_power", "data_type": "NUMBER", "unit_code": "kW", "applicable_resource_types": ["EQUIPMENT"], "description": "设备额定功率", "is_required": False},
        {"name": "主轴转速", "code": "spindle_speed", "data_type": "NUMBER", "unit_code": "r/min", "applicable_resource_types": ["EQUIPMENT"], "description": "设备主轴转速", "is_required": False},
        {"name": "工作台尺寸", "code": "worktable_size", "data_type": "STRING", "unit_code": None, "applicable_resource_types": ["EQUIPMENT"], "description": "设备工作台尺寸", "is_required": False},
        {"name": "加工精度", "code": "machining_precision", "data_type": "NUMBER", "unit_code": "mm", "applicable_resource_types": ["EQUIPMENT"], "description": "设备加工精度", "is_required": False},
        {"name": "能效比", "code": "efficiency_ratio", "data_type": "NUMBER", "unit_code": None, "applicable_resource_types": ["EQUIPMENT"], "description": "设备能效比", "is_required": False},
    ]

    for attr_data in attrs:
        unit = None
        if attr_data.get("unit_code"):
            unit = db.execute(
                select(MdUnit).where(MdUnit.code == attr_data["unit_code"])
            ).scalar_one_or_none()

        attr = MdAttrDefinition(
            name=attr_data["name"],
            code=attr_data["code"],
            data_type=attr_data["data_type"],
            unit_id=unit.id if unit else None,
            applicable_resource_types=attr_data["applicable_resource_types"],
            description=attr_data.get("description"),
            is_required=attr_data.get("is_required", False),
            enum_values=attr_data.get("enum_values"),
            created_by="system",
            updated_by="system",
        )
        db.add(attr)

    db.commit()
    print(f"已创建 {len(attrs)} 个属性定义")


def init_processes(db: Session) -> None:
    """初始化标准工序"""
    print("初始化标准工序...")

    processes = [
        {"name": "车削", "code": "PROC_TURNING", "standard_time": Decimal("0.5"), "setup_time": Decimal("0.25"), "description": "车削加工工序"},
        {"name": "铣削", "code": "PROC_MILLING", "standard_time": Decimal("0.75"), "setup_time": Decimal("0.5"), "description": "铣削加工工序"},
        {"name": "钻孔", "code": "PROC_DRILLING", "standard_time": Decimal("0.25"), "setup_time": Decimal("0.15"), "description": "钻孔加工工序"},
        {"name": "磨削", "code": "PROC_GRINDING", "standard_time": Decimal("1.0"), "setup_time": Decimal("0.5"), "description": "磨削加工工序"},
        {"name": "焊接", "code": "PROC_WELDING", "standard_time": Decimal("0.5"), "setup_time": Decimal("0.3"), "description": "焊接工序"},
        {"name": "装配", "code": "PROC_ASSEMBLY", "standard_time": Decimal("1.5"), "setup_time": Decimal("0.5"), "description": "装配工序"},
        {"name": "热处理", "code": "PROC_HEAT_TREATMENT", "standard_time": Decimal("2.0"), "setup_time": Decimal("1.0"), "description": "热处理工序"},
        {"name": "表面处理", "code": "PROC_SURFACE_TREATMENT", "standard_time": Decimal("0.5"), "setup_time": Decimal("0.25"), "description": "表面处理工序"},
    ]

    for proc_data in processes:
        proc = MdProcess(
            name=proc_data["name"],
            code=proc_data["code"],
            standard_time=proc_data["standard_time"],
            setup_time=proc_data["setup_time"],
            description=proc_data.get("description"),
            created_by="system",
            updated_by="system",
        )
        db.add(proc)

    db.commit()
    print(f"已创建 {len(processes)} 个标准工序")


def init_energy_rates(db: Session) -> None:
    """初始化能源单价和日历"""
    print("初始化能源单价...")

    # 获取单位
    kwh_unit = db.execute(select(MdUnit).where(MdUnit.code == "kWh")).scalar_one_or_none()
    l_unit = db.execute(select(MdUnit).where(MdUnit.code == "L")).scalar_one_or_none()
    m3_unit = db.execute(select(MdUnit).where(MdUnit.code == "m3")).scalar_one_or_none()
    t_unit = db.execute(select(MdUnit).where(MdUnit.code == "t")).scalar_one_or_none()

    rates = [
        {"name": "工业用电", "code": "ELEC_INDUSTRIAL", "energy_type": EnergyType.ELECTRICITY, "unit_price": Decimal("0.85"), "unit_id": kwh_unit.id if kwh_unit else None, "description": "工业用电基准单价"},
        {"name": "工业用水", "code": "WATER_INDUSTRIAL", "energy_type": EnergyType.WATER, "unit_price": Decimal("4.5"), "unit_id": l_unit.id if l_unit else None, "description": "工业用水基准单价"},
        {"name": "天然气", "code": "GAS_NATURAL", "energy_type": EnergyType.GAS, "unit_price": Decimal("3.5"), "unit_id": m3_unit.id if m3_unit else None, "description": "天然气基准单价"},
        {"name": "蒸汽", "code": "STEAM_INDUSTRIAL", "energy_type": EnergyType.STEAM, "unit_price": Decimal("250.0"), "unit_id": t_unit.id if t_unit else None, "description": "工业蒸汽基准单价"},
        {"name": "压缩空气", "code": "AIR_COMPRESSED", "energy_type": EnergyType.COMPRESSED_AIR, "unit_price": Decimal("0.15"), "unit_id": m3_unit.id if m3_unit else None, "description": "压缩空气基准单价"},
    ]

    for rate_data in rates:
        rate = MdEnergyRate(
            name=rate_data["name"],
            code=rate_data["code"],
            energy_type=rate_data["energy_type"],
            unit_price=rate_data["unit_price"],
            unit_id=rate_data["unit_id"],
            description=rate_data.get("description"),
            created_by="system",
            updated_by="system",
        )
        db.add(rate)
        db.flush()

        # 为电力添加峰平谷日历
        if rate_data["code"] == "ELEC_INDUSTRIAL":
            calendars = [
                {"name": "早高峰", "start_time": time(8, 0, 0), "end_time": time(12, 0, 0), "multiplier": Decimal("1.5"), "description": "早高峰电价"},
                {"name": "平时段", "start_time": time(12, 0, 0), "end_time": time(18, 0, 0), "multiplier": Decimal("1.0"), "description": "正常电价"},
                {"name": "晚高峰", "start_time": time(18, 0, 0), "end_time": time(22, 0, 0), "multiplier": Decimal("1.5"), "description": "晚高峰电价"},
                {"name": "谷时段", "start_time": time(22, 0, 0), "end_time": time(23, 59, 59), "multiplier": Decimal("0.5"), "description": "低谷电价"},
            ]
            for cal_data in calendars:
                cal = MdEnergyCalendar(
                    energy_rate_id=rate.id,
                    name=cal_data["name"],
                    start_time=cal_data["start_time"],
                    end_time=cal_data["end_time"],
                    multiplier=cal_data["multiplier"],
                    description=cal_data.get("description"),
                    created_by="system",
                    updated_by="system",
                )
                db.add(cal)

    db.commit()
    print(f"已创建 {len(rates)} 个能源单价")


def main():
    print("=" * 60)
    print("重新初始化主数据种子数据")
    print("=" * 60)

    db = SessionLocal()
    try:
        clear_master_data(db)
        init_resource_categories(db)
        init_attr_definitions(db)
        init_processes(db)
        init_energy_rates(db)
        print("\n主数据种子数据初始化完成！")
    except Exception as e:
        print(f"初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
