"""
ORM 模型包

导入所有模型以便 Alembic 自动检测和迁移
"""

from app.models.base import AuditMixin, Base
from app.models.master_data import (
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
    EnergyType,
    ResourceType,
    SkillLevel,
)
from app.models.system import (
    OrgDepartment,
    SysAuditLog,
    SysPermission,
    SysRole,
    SysRolePermission,
    SysUser,
    SysUserRole,
)

__all__ = [
    "Base",
    "AuditMixin",
    # 系统管理域
    "OrgDepartment",
    "SysUser",
    "SysRole",
    "SysPermission",
    "SysUserRole",
    "SysRolePermission",
    "SysAuditLog",
    # 主数据域
    "MdUnitDimension",
    "MdUnit",
    "MdUnitConversion",
    "MdResourceCategory",
    "MdAttrDefinition",
    "MdMaterial",
    "MdEquipment",
    "MdProcess",
    "MdProcessResource",
    "MdLabor",
    "MdEnergyRate",
    "MdEnergyCalendar",
    # 枚举类型
    "ResourceType",
    "SkillLevel",
    "EnergyType",
]
