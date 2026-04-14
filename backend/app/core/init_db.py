"""
数据库初始数据填充脚本（幂等）

执行方式：
    cd e:\\code\\lcc-app\\backend
    .venv\\Scripts\\python.exe -m app.core.init_db

幂等保证：
    脚本在执行每步操作前先查询是否已存在，存在则跳过，
    可重复执行而不会产生重复数据或报错。

初始化内容：
    1. 根部门       — 集团总部（ROOT）
    2. 模块六权限点   — 系统管理全部资源操作权限
    3. 内置角色      — 超级管理员 / 系统管理员 / 系统审计员
    4. 管理员账号    — admin / 123456
    5. 关系绑定      — admin 归属集团总部，拥有 SUPER_ADMIN 角色
"""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from decimal import Decimal

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.master_data import MdUnit, MdUnitConversion, MdUnitDimension
from app.models.system import (
    OrgDepartment,
    SysAuditLog,
    SysPermission,
    SysRole,
    SysRolePermission,
    SysUser,
    SysUserRole,
)


# ── 种子数据常量 ───────────────────────────────────────────────────────────────

_ROOT_DEPT = {
    "name": "集团总部",
    "code": "ROOT",
    "sort_order": 0,
    "is_active": True,
}

_SUPER_ADMIN_ROLE = {
    "name": "超级管理员",
    "code": "SUPER_ADMIN",
    "description": "系统内置超级管理员角色，拥有所有操作权限",
    "is_active": True,
}

_SYSTEM_ADMIN_ROLE = {
    "name": "系统管理员",
    "code": "SYSTEM_ADMIN",
    "description": "模块六内置管理员角色，可管理组织、权限、角色、用户与审计日志",
    "is_active": True,
}

_SYSTEM_AUDITOR_ROLE = {
    "name": "系统审计员",
    "code": "SYSTEM_AUDITOR",
    "description": "模块六内置审计角色，默认只读访问审计日志",
    "is_active": True,
}

_ADMIN_USER = {
    "username": "admin",
    "password": "123456",
    "real_name": "系统管理员",
}

_SYSTEM_PERMISSION_SEEDS = [
    {
        "name": "部门查看",
        "code": "SYSTEM_DEPARTMENTS_READ",
        "resource": "/system/departments",
        "action": "read",
        "description": "查看系统部门列表与详情",
    },
    {
        "name": "部门维护",
        "code": "SYSTEM_DEPARTMENTS_WRITE",
        "resource": "/system/departments",
        "action": "write",
        "description": "新建和编辑系统部门",
    },
    {
        "name": "部门删除",
        "code": "SYSTEM_DEPARTMENTS_DELETE",
        "resource": "/system/departments",
        "action": "delete",
        "description": "删除系统部门",
    },
    {
        "name": "权限查看",
        "code": "SYSTEM_PERMISSIONS_READ",
        "resource": "/system/permissions",
        "action": "read",
        "description": "查看权限点列表与详情",
    },
    {
        "name": "权限维护",
        "code": "SYSTEM_PERMISSIONS_WRITE",
        "resource": "/system/permissions",
        "action": "write",
        "description": "新建和编辑权限点",
    },
    {
        "name": "权限删除",
        "code": "SYSTEM_PERMISSIONS_DELETE",
        "resource": "/system/permissions",
        "action": "delete",
        "description": "删除权限点",
    },
    {
        "name": "角色查看",
        "code": "SYSTEM_ROLES_READ",
        "resource": "/system/roles",
        "action": "read",
        "description": "查看角色列表与详情",
    },
    {
        "name": "角色维护",
        "code": "SYSTEM_ROLES_WRITE",
        "resource": "/system/roles",
        "action": "write",
        "description": "新建和编辑角色",
    },
    {
        "name": "角色删除",
        "code": "SYSTEM_ROLES_DELETE",
        "resource": "/system/roles",
        "action": "delete",
        "description": "删除角色",
    },
    {
        "name": "用户查看",
        "code": "SYSTEM_USERS_READ",
        "resource": "/system/users",
        "action": "read",
        "description": "查看用户列表与详情",
    },
    {
        "name": "用户维护",
        "code": "SYSTEM_USERS_WRITE",
        "resource": "/system/users",
        "action": "write",
        "description": "新建和编辑用户",
    },
    {
        "name": "用户删除",
        "code": "SYSTEM_USERS_DELETE",
        "resource": "/system/users",
        "action": "delete",
        "description": "删除用户",
    },
    {
        "name": "用户管理",
        "code": "SYSTEM_USERS_ADMIN",
        "resource": "/system/users",
        "action": "admin",
        "description": "重置用户密码等高级管理操作",
    },
    {
        "name": "审计日志查看",
        "code": "SYSTEM_AUDIT_LOGS_READ",
        "resource": "/system/audit-logs",
        "action": "read",
        "description": "查看系统审计日志",
    },
]

_BUILTIN_ROLE_PERMISSIONS = {
    "SYSTEM_ADMIN": [permission["code"] for permission in _SYSTEM_PERMISSION_SEEDS],
    "SYSTEM_AUDITOR": ["SYSTEM_AUDIT_LOGS_READ"],
}

_DEPARTMENT_NAME_BY_CODE = {
    "ROOT": "集团总部",
    "RD": "研发中心",
    "MFG": "制造中心",
    "TEST_DEPT": "测试部门",
    "TEST_DEPT_001": "测试部门001",
    "TDEPT_X01": "测试部门X01",
}

_ROLE_NAME_BY_CODE = {
    "SUPER_ADMIN": "超级管理员",
    "PROCESS_ENG": "工艺工程师",
    "TEST_ROLE": "测试角色",
    "SYSTEM_ADMIN": "系统管理员",
    "SYSTEM_AUDITOR": "系统审计员",
}

_ROLE_DESCRIPTION_BY_CODE = {
    "PROCESS_ENG": "负责工艺路线创建与设备指派",
    "SYSTEM_ADMIN": "模块六内置管理员角色，可管理组织、权限、角色、用户与审计日志",
    "SYSTEM_AUDITOR": "模块六内置审计角色，默认只读访问审计日志",
}

_PERMISSION_NAME_BY_CODE = {
    "MATERIAL_READ": "材料主数据读取",
    "EQUIP_WRITE": "设备写入",
    "TEST_PERM": "测试权限",
    "TEST_PERM_001": "测试权限001",
    "SYSTEM_DEPARTMENTS_READ": "部门查看",
    "SYSTEM_DEPARTMENTS_WRITE": "部门维护",
    "SYSTEM_DEPARTMENTS_DELETE": "部门删除",
    "SYSTEM_PERMISSIONS_READ": "权限查看",
    "SYSTEM_PERMISSIONS_WRITE": "权限维护",
    "SYSTEM_PERMISSIONS_DELETE": "权限删除",
    "SYSTEM_ROLES_READ": "角色查看",
    "SYSTEM_ROLES_WRITE": "角色维护",
    "SYSTEM_ROLES_DELETE": "角色删除",
    "SYSTEM_USERS_READ": "用户查看",
    "SYSTEM_USERS_WRITE": "用户维护",
    "SYSTEM_USERS_DELETE": "用户删除",
    "SYSTEM_USERS_ADMIN": "用户管理",
    "SYSTEM_AUDIT_LOGS_READ": "审计日志查看",
}

_PERMISSION_DESCRIPTION_BY_CODE = {
    "MATERIAL_READ": "允许查询材料主数据列表和详情",
    "EQUIP_WRITE": "允许新增、编辑设备主数据",
    "TEST_PERM": "系统管理联调用测试权限",
    "TEST_PERM_001": "系统管理联调用测试权限001",
}

_USER_REAL_NAME_BY_USERNAME = {
    "admin": "系统管理员",
    "zhangsan": "张三",
    "testfe01": "前端测试01",
    "testuser_fe01": "前端测试用户01",
}


# ── 主数据域种子数据 ───────────────────────────────────────────────────────────

_UNIT_DIMENSION_SEEDS = [
    {"name": "长度", "code": "LENGTH", "description": "长度量纲", "sort_order": 1},
    {"name": "质量", "code": "MASS", "description": "质量量纲", "sort_order": 2},
    {"name": "体积", "code": "VOLUME", "description": "体积量纲", "sort_order": 3},
    {"name": "时间", "code": "TIME", "description": "时间量纲", "sort_order": 4},
    {"name": "能耗", "code": "ENERGY", "description": "能耗量纲", "sort_order": 5},
    {"name": "力", "code": "FORCE", "description": "力量纲", "sort_order": 6},
    {"name": "压强", "code": "PRESSURE", "description": "压强量纲", "sort_order": 7},
    {"name": "货币", "code": "CURRENCY", "description": "货币量纲", "sort_order": 8},
]

_UNIT_SEEDS = [
    {"name": "毫米", "code": "mm", "symbol": "mm", "dimension_code": "LENGTH", "is_base": False, "description": "毫米"},
    {"name": "厘米", "code": "cm", "symbol": "cm", "dimension_code": "LENGTH", "is_base": False, "description": "厘米"},
    {"name": "米", "code": "m", "symbol": "m", "dimension_code": "LENGTH", "is_base": True, "description": "米（基础单位）"},
    {"name": "千米", "code": "km", "symbol": "km", "dimension_code": "LENGTH", "is_base": False, "description": "千米"},
    {"name": "克", "code": "g", "symbol": "g", "dimension_code": "MASS", "is_base": False, "description": "克"},
    {"name": "千克", "code": "kg", "symbol": "kg", "dimension_code": "MASS", "is_base": True, "description": "千克（基础单位）"},
    {"name": "吨", "code": "t", "symbol": "t", "dimension_code": "MASS", "is_base": False, "description": "吨"},
    {"name": "毫升", "code": "mL", "symbol": "mL", "dimension_code": "VOLUME", "is_base": False, "description": "毫升"},
    {"name": "升", "code": "L", "symbol": "L", "dimension_code": "VOLUME", "is_base": True, "description": "升（基础单位）"},
    {"name": "立方米", "code": "m3", "symbol": "m³", "dimension_code": "VOLUME", "is_base": False, "description": "立方米"},
    {"name": "秒", "code": "s", "symbol": "s", "dimension_code": "TIME", "is_base": True, "description": "秒（基础单位）"},
    {"name": "分钟", "code": "min", "symbol": "min", "dimension_code": "TIME", "is_base": False, "description": "分钟"},
    {"name": "小时", "code": "h", "symbol": "h", "dimension_code": "TIME", "is_base": False, "description": "小时"},
    {"name": "焦耳", "code": "J", "symbol": "J", "dimension_code": "ENERGY", "is_base": True, "description": "焦耳（基础单位）"},
    {"name": "千焦", "code": "kJ", "symbol": "kJ", "dimension_code": "ENERGY", "is_base": False, "description": "千焦"},
    {"name": "千瓦时", "code": "kWh", "symbol": "kWh", "dimension_code": "ENERGY", "is_base": False, "description": "千瓦时（度）"},
    {"name": "牛顿", "code": "N", "symbol": "N", "dimension_code": "FORCE", "is_base": True, "description": "牛顿（基础单位）"},
    {"name": "千牛", "code": "kN", "symbol": "kN", "dimension_code": "FORCE", "is_base": False, "description": "千牛"},
    {"name": "帕斯卡", "code": "Pa", "symbol": "Pa", "dimension_code": "PRESSURE", "is_base": True, "description": "帕斯卡（基础单位）"},
    {"name": "千帕", "code": "kPa", "symbol": "kPa", "dimension_code": "PRESSURE", "is_base": False, "description": "千帕"},
    {"name": "兆帕", "code": "MPa", "symbol": "MPa", "dimension_code": "PRESSURE", "is_base": False, "description": "兆帕"},
    {"name": "元", "code": "CNY", "symbol": "¥", "dimension_code": "CURRENCY", "is_base": True, "description": "人民币元（基础单位）"},
    {"name": "万元", "code": "wan_yuan", "symbol": "万元", "dimension_code": "CURRENCY", "is_base": False, "description": "万元"},
]

_UNIT_CONVERSION_SEEDS = [
    {"from_unit_code": "mm", "to_unit_code": "m", "conversion_factor": Decimal("0.001"), "description": "1mm = 0.001m"},
    {"from_unit_code": "cm", "to_unit_code": "m", "conversion_factor": Decimal("0.01"), "description": "1cm = 0.01m"},
    {"from_unit_code": "km", "to_unit_code": "m", "conversion_factor": Decimal("1000"), "description": "1km = 1000m"},
    {"from_unit_code": "g", "to_unit_code": "kg", "conversion_factor": Decimal("0.001"), "description": "1g = 0.001kg"},
    {"from_unit_code": "t", "to_unit_code": "kg", "conversion_factor": Decimal("1000"), "description": "1t = 1000kg"},
    {"from_unit_code": "mL", "to_unit_code": "L", "conversion_factor": Decimal("0.001"), "description": "1mL = 0.001L"},
    {"from_unit_code": "m3", "to_unit_code": "L", "conversion_factor": Decimal("1000"), "description": "1m³ = 1000L"},
    {"from_unit_code": "min", "to_unit_code": "s", "conversion_factor": Decimal("60"), "description": "1min = 60s"},
    {"from_unit_code": "h", "to_unit_code": "s", "conversion_factor": Decimal("3600"), "description": "1h = 3600s"},
    {"from_unit_code": "h", "to_unit_code": "min", "conversion_factor": Decimal("60"), "description": "1h = 60min"},
    {"from_unit_code": "kJ", "to_unit_code": "J", "conversion_factor": Decimal("1000"), "description": "1kJ = 1000J"},
    {"from_unit_code": "kWh", "to_unit_code": "J", "conversion_factor": Decimal("3600000"), "description": "1kWh = 3600000J"},
    {"from_unit_code": "kWh", "to_unit_code": "kJ", "conversion_factor": Decimal("3600"), "description": "1kWh = 3600kJ"},
    {"from_unit_code": "kN", "to_unit_code": "N", "conversion_factor": Decimal("1000"), "description": "1kN = 1000N"},
    {"from_unit_code": "kPa", "to_unit_code": "Pa", "conversion_factor": Decimal("1000"), "description": "1kPa = 1000Pa"},
    {"from_unit_code": "MPa", "to_unit_code": "Pa", "conversion_factor": Decimal("1000000"), "description": "1MPa = 1000000Pa"},
    {"from_unit_code": "MPa", "to_unit_code": "kPa", "conversion_factor": Decimal("1000"), "description": "1MPa = 1000kPa"},
    {"from_unit_code": "wan_yuan", "to_unit_code": "CNY", "conversion_factor": Decimal("10000"), "description": "1万元 = 10000元"},
]


# ── 幂等初始化步骤 ─────────────────────────────────────────────────────────────

def _ensure_root_department(db: Session) -> OrgDepartment:
    dept = db.execute(
        select(OrgDepartment).where(
            OrgDepartment.code == _ROOT_DEPT["code"],
            OrgDepartment.is_deleted == False,
        )
    ).scalar_one_or_none()

    if dept is None:
        dept = OrgDepartment(**_ROOT_DEPT, created_by="system", updated_by="system")
        db.add(dept)
        db.flush()  # 立即写入以获取 id，尚未 commit
        print(f"  [+] 创建部门：{dept.name}（{dept.code}）")
    else:
        print(f"  [=] 部门已存在，跳过：{dept.name}（{dept.code}）")

    return dept


def _ensure_permission(db: Session, seed: dict[str, str]) -> SysPermission:
    permission = db.execute(
        select(SysPermission).where(
            SysPermission.code == seed["code"],
            SysPermission.is_deleted == False,
        )
    ).scalar_one_or_none()

    if permission is None:
        permission = SysPermission(
            **seed,
            created_by="system",
            updated_by="system",
        )
        db.add(permission)
        db.flush()
        print(f"  [+] 创建权限：{permission.code}")
        return permission

    changed = False
    for field in ("name", "resource", "action", "description"):
        if getattr(permission, field) != seed[field]:
            setattr(permission, field, seed[field])
            changed = True
    if changed:
        permission.updated_by = "system"
        db.flush()
        print(f"  [~] 更新权限：{permission.code}")
    else:
        print(f"  [=] 权限已存在，跳过：{permission.code}")

    return permission


def _ensure_system_permissions(db: Session) -> dict[str, SysPermission]:
    permissions: dict[str, SysPermission] = {}
    for seed in _SYSTEM_PERMISSION_SEEDS:
        permission = _ensure_permission(db, seed)
        permissions[permission.code] = permission
    return permissions


def _ensure_role(db: Session, seed: dict[str, str | bool]) -> SysRole:
    role = db.execute(
        select(SysRole).where(
            SysRole.code == seed["code"],
            SysRole.is_deleted == False,
        )
    ).scalar_one_or_none()

    if role is None:
        role = SysRole(**seed, created_by="system", updated_by="system")
        db.add(role)
        db.flush()
        print(f"  [+] 创建角色：{role.name}（{role.code}）")
    else:
        changed = False
        for field in ("name", "description", "is_active"):
            if getattr(role, field) != seed[field]:
                setattr(role, field, seed[field])
                changed = True
        if changed:
            role.updated_by = "system"
            db.flush()
            print(f"  [~] 更新角色：{role.name}（{role.code}）")
        else:
            print(f"  [=] 角色已存在，跳过：{role.name}（{role.code}）")

    return role


def _ensure_builtin_roles(db: Session) -> dict[str, SysRole]:
    roles = {
        "SUPER_ADMIN": _ensure_role(db, _SUPER_ADMIN_ROLE),
        "SYSTEM_ADMIN": _ensure_role(db, _SYSTEM_ADMIN_ROLE),
        "SYSTEM_AUDITOR": _ensure_role(db, _SYSTEM_AUDITOR_ROLE),
    }
    return roles


def _ensure_admin_user(db: Session, dept: OrgDepartment) -> SysUser:
    user = db.execute(
        select(SysUser).where(
            SysUser.username == _ADMIN_USER["username"],
            SysUser.is_deleted == False,
        )
    ).scalar_one_or_none()

    if user is None:
        user = SysUser(
            username=_ADMIN_USER["username"],
            hashed_password=hash_password(_ADMIN_USER["password"]),
            real_name=_ADMIN_USER["real_name"],
            is_active=True,
            department_id=dept.id,
            created_by="system",
            updated_by="system",
        )
        db.add(user)
        db.flush()
        print(f"  [+] 创建用户：{user.username}（{user.real_name}）")
    else:
        print(f"  [=] 用户已存在，跳过：{user.username}")

    return user


def _ensure_user_role_binding(db: Session, user: SysUser, role: SysRole) -> None:
    binding = db.execute(
        select(SysUserRole).where(
            SysUserRole.user_id == user.id,
            SysUserRole.role_id == role.id,
        )
    ).scalar_one_or_none()

    if binding is None:
        binding = SysUserRole(
            user_id=user.id,
            role_id=role.id,
            created_by="system",
            updated_by="system",
        )
        db.add(binding)
        db.flush()
        print(f"  [+] 绑定角色：{user.username} → {role.code}")
    else:
        print(f"  [=] 角色绑定已存在，跳过：{user.username} → {role.code}")


def _ensure_role_permission_binding(db: Session, role: SysRole, permission: SysPermission) -> None:
    binding = db.execute(
        select(SysRolePermission).where(
            SysRolePermission.role_id == role.id,
            SysRolePermission.permission_id == permission.id,
        )
    ).scalar_one_or_none()

    if binding is None:
        binding = SysRolePermission(
            role_id=role.id,
            permission_id=permission.id,
            created_by="system",
            updated_by="system",
        )
        db.add(binding)
        db.flush()
        print(f"  [+] 绑定权限：{role.code} → {permission.code}")
    else:
        print(f"  [=] 权限绑定已存在，跳过：{role.code} → {permission.code}")


def _ensure_builtin_role_permissions(
    db: Session,
    roles: dict[str, SysRole],
    permissions: dict[str, SysPermission],
) -> None:
    for role_code, permission_codes in _BUILTIN_ROLE_PERMISSIONS.items():
        role = roles[role_code]
        for permission_code in permission_codes:
            _ensure_role_permission_binding(db, role, permissions[permission_code])


# ── 主数据域初始化函数 ─────────────────────────────────────────────────────────

def _ensure_unit_dimension(db: Session, seed: dict) -> MdUnitDimension:
    dimension = db.execute(
        select(MdUnitDimension).where(
            MdUnitDimension.code == seed["code"],
            MdUnitDimension.is_deleted == False,
        )
    ).scalar_one_or_none()

    if dimension is None:
        dimension = MdUnitDimension(**seed, created_by="system", updated_by="system")
        db.add(dimension)
        db.flush()
        print(f"  [+] 创建量纲：{dimension.name}（{dimension.code}）")
        return dimension

    changed = False
    for field in ("name", "description", "sort_order"):
        if field in seed and getattr(dimension, field) != seed[field]:
            setattr(dimension, field, seed[field])
            changed = True
    if changed:
        dimension.updated_by = "system"
        db.flush()
        print(f"  [~] 更新量纲：{dimension.name}（{dimension.code}）")
    else:
        print(f"  [=] 量纲已存在，跳过：{dimension.name}（{dimension.code}）")

    return dimension


def _ensure_unit_dimensions(db: Session) -> dict[str, MdUnitDimension]:
    dimensions: dict[str, MdUnitDimension] = {}
    for seed in _UNIT_DIMENSION_SEEDS:
        dimension = _ensure_unit_dimension(db, seed)
        dimensions[dimension.code] = dimension
    return dimensions


def _ensure_unit(db: Session, seed: dict, dimensions: dict[str, MdUnitDimension]) -> MdUnit:
    unit = db.execute(
        select(MdUnit).where(
            MdUnit.code == seed["code"],
            MdUnit.is_deleted == False,
        )
    ).scalar_one_or_none()

    dimension = dimensions[seed["dimension_code"]]

    if unit is None:
        unit = MdUnit(
            name=seed["name"],
            code=seed["code"],
            symbol=seed.get("symbol"),
            dimension_id=dimension.id,
            is_base=seed.get("is_base", False),
            description=seed.get("description"),
            created_by="system",
            updated_by="system",
        )
        db.add(unit)
        db.flush()
        print(f"  [+] 创建单位：{unit.name}（{unit.code}）")
        return unit

    changed = False
    for field in ("name", "symbol", "is_base", "description"):
        if field in seed and getattr(unit, field) != seed[field]:
            setattr(unit, field, seed[field])
            changed = True
    if unit.dimension_id != dimension.id:
        unit.dimension_id = dimension.id
        changed = True
    if changed:
        unit.updated_by = "system"
        db.flush()
        print(f"  [~] 更新单位：{unit.name}（{unit.code}）")
    else:
        print(f"  [=] 单位已存在，跳过：{unit.name}（{unit.code}）")

    return unit


def _ensure_units(db: Session, dimensions: dict[str, MdUnitDimension]) -> dict[str, MdUnit]:
    units: dict[str, MdUnit] = {}
    for seed in _UNIT_SEEDS:
        unit = _ensure_unit(db, seed, dimensions)
        units[unit.code] = unit
    return units


def _ensure_unit_conversion(
    db: Session,
    seed: dict,
    units: dict[str, MdUnit],
) -> MdUnitConversion:
    from_unit = units[seed["from_unit_code"]]
    to_unit = units[seed["to_unit_code"]]

    conversion = db.execute(
        select(MdUnitConversion).where(
            MdUnitConversion.from_unit_id == from_unit.id,
            MdUnitConversion.to_unit_id == to_unit.id,
            MdUnitConversion.is_deleted == False,
        )
    ).scalar_one_or_none()

    if conversion is None:
        conversion = MdUnitConversion(
            from_unit_id=from_unit.id,
            to_unit_id=to_unit.id,
            conversion_factor=seed["conversion_factor"],
            description=seed.get("description"),
            created_by="system",
            updated_by="system",
        )
        db.add(conversion)
        db.flush()
        print(f"  [+] 创建换算：{from_unit.code} → {to_unit.code}（{seed['conversion_factor']}）")
        return conversion

    changed = False
    if conversion.conversion_factor != seed["conversion_factor"]:
        conversion.conversion_factor = seed["conversion_factor"]
        changed = True
    if seed.get("description") and conversion.description != seed["description"]:
        conversion.description = seed["description"]
        changed = True
    if changed:
        conversion.updated_by = "system"
        db.flush()
        print(f"  [~] 更新换算：{from_unit.code} → {to_unit.code}")
    else:
        print(f"  [=] 换算已存在，跳过：{from_unit.code} → {to_unit.code}")

    return conversion


def _ensure_unit_conversions(db: Session, units: dict[str, MdUnit]) -> None:
    for seed in _UNIT_CONVERSION_SEEDS:
        _ensure_unit_conversion(db, seed, units)


# ── 主入口 ─────────────────────────────────────────────────────────────────────

def run_seed() -> None:
    print("\n======================================")
    print("  LCC 平台 — 初始数据填充（幂等模式）")
    print("======================================\n")

    db: Session = SessionLocal()
    try:
        print("[Step 1] 初始化根部门...")
        dept = _ensure_root_department(db)

        print("\n[Step 2] 初始化模块六权限点...")
        permissions = _ensure_system_permissions(db)

        print("\n[Step 3] 初始化内置角色...")
        roles = _ensure_builtin_roles(db)

        print("\n[Step 4] 绑定内置角色与权限...")
        _ensure_builtin_role_permissions(db, roles, permissions)

        print("\n[Step 5] 初始化管理员账号...")
        user = _ensure_admin_user(db, dept)

        print("\n[Step 6] 绑定用户与角色...")
        _ensure_user_role_binding(db, user, roles["SUPER_ADMIN"])

        print("\n[Step 7] 初始化量纲定义...")
        dimensions = _ensure_unit_dimensions(db)

        print("\n[Step 8] 初始化单位定义...")
        units = _ensure_units(db, dimensions)

        print("\n[Step 9] 初始化单位换算...")
        _ensure_unit_conversions(db, units)

        db.commit()
        print("\n[Done] 初始化完成，所有数据已提交。\n")

    except Exception as e:
        db.rollback()
        print(f"\n[Error] 初始化失败，已回滚：{e}\n")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
