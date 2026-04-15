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
from app.models.system_dictionary import SysDictItem, SysDictType


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
    {
        "name": "数据字典查看",
        "code": "SYSTEM_DICTIONARIES_READ",
        "resource": "/system/dictionaries",
        "action": "read",
        "description": "查看系统级数据字典与缓存聚合结果",
    },
    {
        "name": "数据字典维护",
        "code": "SYSTEM_DICTIONARIES_WRITE",
        "resource": "/system/dictionaries",
        "action": "write",
        "description": "新建和编辑系统级数据字典",
    },
    {
        "name": "数据字典删除",
        "code": "SYSTEM_DICTIONARIES_DELETE",
        "resource": "/system/dictionaries",
        "action": "delete",
        "description": "删除系统级数据字典",
    },
    {
        "name": "人员工时查看",
        "code": "MASTER_DATA_LABOR_READ",
        "resource": "/master-data/labor",
        "action": "read",
        "description": "查看人员工时台账",
    },
    {
        "name": "人员工时维护",
        "code": "MASTER_DATA_LABOR_WRITE",
        "resource": "/master-data/labor",
        "action": "write",
        "description": "新建和编辑人员工时与属性",
    },
    {
        "name": "人员工时删除",
        "code": "MASTER_DATA_LABOR_DELETE",
        "resource": "/master-data/labor",
        "action": "delete",
        "description": "删除人员工时台账记录",
    },
    {
        "name": "能源日历查看",
        "code": "MASTER_DATA_ENERGY_READ",
        "resource": "/master-data/energy",
        "action": "read",
        "description": "查看能源日历与费率",
    },
    {
        "name": "能源日历维护",
        "code": "MASTER_DATA_ENERGY_WRITE",
        "resource": "/master-data/energy",
        "action": "write",
        "description": "新建和编辑能源单价及时段",
    },
    {
        "name": "能源日历删除",
        "code": "MASTER_DATA_ENERGY_DELETE",
        "resource": "/master-data/energy",
        "action": "delete",
        "description": "删除能源日历配置",
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
    "SYSTEM_DICTIONARIES_READ": "数据字典查看",
    "SYSTEM_DICTIONARIES_WRITE": "数据字典维护",
    "SYSTEM_DICTIONARIES_DELETE": "数据字典删除",
    "MASTER_DATA_LABOR_READ": "人员工时查看",
    "MASTER_DATA_LABOR_WRITE": "人员工时维护",
    "MASTER_DATA_LABOR_DELETE": "人员工时删除",
    "MASTER_DATA_ENERGY_READ": "能源日历查看",
    "MASTER_DATA_ENERGY_WRITE": "能源日历维护",
    "MASTER_DATA_ENERGY_DELETE": "能源日历删除",
}

_PERMISSION_DESCRIPTION_BY_CODE = {
    "MATERIAL_READ": "允许查询材料主数据列表和详情",
    "EQUIP_WRITE": "允许新增、编辑设备主数据",
    "TEST_PERM": "系统管理联调用测试权限",
    "TEST_PERM_001": "系统管理联调用测试权限001",
    "SYSTEM_DICTIONARIES_READ": "允许查看系统级数据字典",
    "SYSTEM_DICTIONARIES_WRITE": "允许维护系统级数据字典",
    "SYSTEM_DICTIONARIES_DELETE": "允许删除系统级数据字典",
    "MASTER_DATA_LABOR_READ": "允许查询人员工时与技能列表",
    "MASTER_DATA_LABOR_WRITE": "允许新增、编辑人员工时信息",
    "MASTER_DATA_LABOR_DELETE": "允许删除人员工时信息",
    "MASTER_DATA_ENERGY_READ": "允许查询能源日历与单位费率",
    "MASTER_DATA_ENERGY_WRITE": "允许新增、编辑能源日历时间段与费率",
    "MASTER_DATA_ENERGY_DELETE": "允许删除能源配置项",
}

_SYSTEM_DICT_TYPE_SEEDS = [
    {"name": "属性数据类型", "code": "ATTR_DATA_TYPE", "description": "属性模板数据类型显示字典", "sort_order": 1, "is_active": True},
    {"name": "适用资源类型", "code": "RESOURCE_TYPE", "description": "主数据资源类型显示字典", "sort_order": 2, "is_active": True},
    {"name": "单位类型", "code": "UNIT_KIND", "description": "基准单位与转换单位显示字典", "sort_order": 3, "is_active": True},
    {"name": "权限动作", "code": "PERMISSION_ACTION", "description": "系统权限动作显示字典", "sort_order": 4, "is_active": True},
    {"name": "审计动作", "code": "AUDIT_ACTION", "description": "审计日志动作显示字典", "sort_order": 5, "is_active": True},
    {"name": "审计资源类型", "code": "AUDIT_RESOURCE_TYPE", "description": "审计日志资源类型显示字典", "sort_order": 6, "is_active": True},
    {"name": "工序资源类型", "code": "PROCESS_RESOURCE_TYPE", "description": "工序资源挂载类型显示字典", "sort_order": 7, "is_active": True},
]

_SYSTEM_DICT_ITEM_SEEDS = {
    "ATTR_DATA_TYPE": [
        {"value": "STRING", "label": "字符串", "sort_order": 1, "extra_json": {"input_hint": "文本"}},
        {"value": "NUMBER", "label": "数值", "sort_order": 2, "extra_json": {"input_hint": "数字"}},
        {"value": "BOOLEAN", "label": "布尔值", "sort_order": 3, "extra_json": {"input_hint": "true / false"}},
        {"value": "JSON", "label": "JSON 对象", "sort_order": 4, "extra_json": {"input_hint": "JSON 格式"}},
        {"value": "DATE", "label": "日期", "sort_order": 5, "extra_json": {"input_hint": "日期 (YYYY-MM-DD)"}},
        {"value": "ENUM", "label": "枚举", "sort_order": 6, "extra_json": {"input_hint": "枚举值"}},
    ],
    "RESOURCE_TYPE": [
        {"value": "MATERIAL", "label": "材料", "sort_order": 1},
        {"value": "EQUIPMENT", "label": "设备", "sort_order": 2},
        {"value": "LABOR", "label": "人员", "sort_order": 3},
        {"value": "TOOL", "label": "工具", "sort_order": 4},
    ],
    "UNIT_KIND": [
        {"value": "BASE", "label": "基准单位", "sort_order": 1},
        {"value": "CONVERTED", "label": "转换单位", "sort_order": 2},
    ],
    "PERMISSION_ACTION": [
        {"value": "read", "label": "读取", "sort_order": 1, "extra_json": {"tag_type": "success"}},
        {"value": "write", "label": "维护", "sort_order": 2, "extra_json": {"tag_type": ""}},
        {"value": "delete", "label": "删除", "sort_order": 3, "extra_json": {"tag_type": "danger"}},
        {"value": "admin", "label": "管理", "sort_order": 4, "extra_json": {"tag_type": "warning"}},
    ],
    "AUDIT_ACTION": [
        {"value": "CREATE", "label": "创建", "sort_order": 1, "extra_json": {"tag_type": "success"}},
        {"value": "UPDATE", "label": "更新", "sort_order": 2, "extra_json": {"tag_type": ""}},
        {"value": "DELETE", "label": "删除", "sort_order": 3, "extra_json": {"tag_type": "danger"}},
        {"value": "RESET_PASSWORD", "label": "重置密码", "sort_order": 4, "extra_json": {"tag_type": "warning"}},
        {"value": "CHANGE_PASSWORD", "label": "修改密码", "sort_order": 5, "extra_json": {"tag_type": "warning"}},
    ],
    "AUDIT_RESOURCE_TYPE": [
        {"value": "OrgDepartment", "label": "部门", "sort_order": 1},
        {"value": "SysPermission", "label": "权限", "sort_order": 2},
        {"value": "SysRole", "label": "角色", "sort_order": 3},
        {"value": "SysUser", "label": "用户", "sort_order": 4},
        {"value": "SysDictType", "label": "字典类型", "sort_order": 5},
        {"value": "SysDictItem", "label": "字典项", "sort_order": 6},
    ],
    "PROCESS_RESOURCE_TYPE": [
        {"value": "MATERIAL", "label": "材料", "sort_order": 1},
        {"value": "EQUIPMENT", "label": "设备", "sort_order": 2},
        {"value": "LABOR", "label": "人员", "sort_order": 3},
        {"value": "TOOL", "label": "工具", "sort_order": 4},
    ],
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


# ── 资源分类种子数据 ───────────────────────────────────────────────────────────

_RESOURCE_CATEGORY_SEEDS = [
    {"name": "材料", "code": "MATERIAL", "resource_type": "MATERIAL", "parent_code": None, "sort_order": 1, "description": "材料分类"},
    {"name": "金属", "code": "MATERIAL_METAL", "resource_type": "MATERIAL", "parent_code": "MATERIAL", "sort_order": 1, "description": "金属材料"},
    {"name": "黑色金属", "code": "MATERIAL_METAL_FERROUS", "resource_type": "MATERIAL", "parent_code": "MATERIAL_METAL", "sort_order": 1, "description": "黑色金属"},
    {"name": "碳钢", "code": "MATERIAL_METAL_FERROUS_CARBON_STEEL", "resource_type": "MATERIAL", "parent_code": "MATERIAL_METAL_FERROUS", "sort_order": 1, "description": "碳钢"},
    {"name": "合金钢", "code": "MATERIAL_METAL_FERROUS_ALLOY_STEEL", "resource_type": "MATERIAL", "parent_code": "MATERIAL_METAL_FERROUS", "sort_order": 2, "description": "合金钢"},
    {"name": "有色金属", "code": "MATERIAL_METAL_NON_FERROUS", "resource_type": "MATERIAL", "parent_code": "MATERIAL_METAL", "sort_order": 2, "description": "有色金属"},
    {"name": "铜及铜合金", "code": "MATERIAL_METAL_NON_FERROUS_COPPER", "resource_type": "MATERIAL", "parent_code": "MATERIAL_METAL_NON_FERROUS", "sort_order": 1, "description": "铜及铜合金"},
    {"name": "铝及铝合金", "code": "MATERIAL_METAL_NON_FERROUS_ALUMINUM", "resource_type": "MATERIAL", "parent_code": "MATERIAL_METAL_NON_FERROUS", "sort_order": 2, "description": "铝及铝合金"},
    {"name": "非金属", "code": "MATERIAL_NON_METAL", "resource_type": "MATERIAL", "parent_code": "MATERIAL", "sort_order": 2, "description": "非金属材料"},
    {"name": "塑料", "code": "MATERIAL_NON_METAL_PLASTIC", "resource_type": "MATERIAL", "parent_code": "MATERIAL_NON_METAL", "sort_order": 1, "description": "塑料"},
    {"name": "橡胶", "code": "MATERIAL_NON_METAL_RUBBER", "resource_type": "MATERIAL", "parent_code": "MATERIAL_NON_METAL", "sort_order": 2, "description": "橡胶"},
    {"name": "复合材料", "code": "MATERIAL_COMPOSITE", "resource_type": "MATERIAL", "parent_code": "MATERIAL", "sort_order": 3, "description": "复合材料"},
    {"name": "设备", "code": "EQUIPMENT", "resource_type": "EQUIPMENT", "parent_code": None, "sort_order": 2, "description": "设备分类"},
    {"name": "加工设备", "code": "EQUIPMENT_PROCESSING", "resource_type": "EQUIPMENT", "parent_code": "EQUIPMENT", "sort_order": 1, "description": "加工设备"},
    {"name": "数控机床", "code": "EQUIPMENT_PROCESSING_CNC", "resource_type": "EQUIPMENT", "parent_code": "EQUIPMENT_PROCESSING", "sort_order": 1, "description": "数控机床"},
    {"name": "普通机床", "code": "EQUIPMENT_PROCESSING_CONVENTIONAL", "resource_type": "EQUIPMENT", "parent_code": "EQUIPMENT_PROCESSING", "sort_order": 2, "description": "普通机床"},
    {"name": "检测设备", "code": "EQUIPMENT_INSPECTION", "resource_type": "EQUIPMENT", "parent_code": "EQUIPMENT", "sort_order": 2, "description": "检测设备"},
    {"name": "人员", "code": "LABOR", "resource_type": "LABOR", "parent_code": None, "sort_order": 3, "description": "人员分类"},
    {"name": "焊工", "code": "LABOR_WELDER", "resource_type": "LABOR", "parent_code": "LABOR", "sort_order": 1, "description": "焊工"},
    {"name": "电工", "code": "LABOR_ELECTRICIAN", "resource_type": "LABOR", "parent_code": "LABOR", "sort_order": 2, "description": "电工"},
    {"name": "工具", "code": "TOOL", "resource_type": "TOOL", "parent_code": None, "sort_order": 4, "description": "工具分类"},
    {"name": "刀具", "code": "TOOL_CUTTING", "resource_type": "TOOL", "parent_code": "TOOL", "sort_order": 1, "description": "刀具"},
    {"name": "夹具", "code": "TOOL_FIXTURE", "resource_type": "TOOL", "parent_code": "TOOL", "sort_order": 2, "description": "夹具"},
]


# ── 属性定义种子数据 ───────────────────────────────────────────────────────────

_ATTR_DEFINITION_SEEDS = [
    {"name": "密度", "code": "density", "data_type": "NUMBER", "unit_code": "kg/m3", "applicable_resource_types": ["MATERIAL"], "description": "材料密度", "is_required": False},
    {"name": "硬度", "code": "hardness", "data_type": "NUMBER", "unit_code": None, "applicable_resource_types": ["MATERIAL"], "description": "材料硬度（HRC）", "is_required": False},
    {"name": "抗拉强度", "code": "tensile_strength", "data_type": "NUMBER", "unit_code": "MPa", "applicable_resource_types": ["MATERIAL"], "description": "材料抗拉强度", "is_required": False},
    {"name": "屈服强度", "code": "yield_strength", "data_type": "NUMBER", "unit_code": "MPa", "applicable_resource_types": ["MATERIAL"], "description": "材料屈服强度", "is_required": False},
    {"name": "额定功率", "code": "rated_power", "data_type": "NUMBER", "unit_code": "kW", "applicable_resource_types": ["EQUIPMENT"], "description": "设备额定功率", "is_required": False},
    {"name": "主轴转速", "code": "spindle_speed", "data_type": "NUMBER", "unit_code": "r/min", "applicable_resource_types": ["EQUIPMENT"], "description": "设备主轴转速", "is_required": False},
    {"name": "工作台尺寸", "code": "worktable_size", "data_type": "STRING", "unit_code": None, "applicable_resource_types": ["EQUIPMENT"], "description": "设备工作台尺寸", "is_required": False},
    {"name": "加工精度", "code": "machining_precision", "data_type": "NUMBER", "unit_code": "mm", "applicable_resource_types": ["EQUIPMENT"], "description": "设备加工精度", "is_required": False},
    {"name": "能效比", "code": "efficiency_ratio", "data_type": "NUMBER", "unit_code": None, "applicable_resource_types": ["EQUIPMENT"], "description": "设备能效比", "is_required": False},
    {"name": "表面处理", "code": "surface_treatment", "data_type": "ENUM", "unit_code": None, "applicable_resource_types": ["MATERIAL"], "description": "表面处理工艺", "is_required": False, "enum_values": ["镀锌", "喷塑", "发黑", "阳极氧化", "电镀"]},
    {"name": "材料状态", "code": "material_status", "data_type": "ENUM", "unit_code": None, "applicable_resource_types": ["MATERIAL"], "description": "材料状态", "is_required": False, "enum_values": ["热轧", "冷轧", "退火", "正火", "淬火"]},
]


# ── 标准工序种子数据 ───────────────────────────────────────────────────────────

_PROCESS_SEEDS = [
    {"name": "车削", "code": "PROC_TURNING", "standard_time": Decimal("0.5"), "setup_time": Decimal("0.25"), "description": "车削加工工序"},
    {"name": "铣削", "code": "PROC_MILLING", "standard_time": Decimal("0.75"), "setup_time": Decimal("0.5"), "description": "铣削加工工序"},
    {"name": "钻孔", "code": "PROC_DRILLING", "standard_time": Decimal("0.25"), "setup_time": Decimal("0.15"), "description": "钻孔加工工序"},
    {"name": "磨削", "code": "PROC_GRINDING", "standard_time": Decimal("1.0"), "setup_time": Decimal("0.5"), "description": "磨削加工工序"},
    {"name": "焊接", "code": "PROC_WELDING", "standard_time": Decimal("0.5"), "setup_time": Decimal("0.3"), "description": "焊接工序"},
    {"name": "装配", "code": "PROC_ASSEMBLY", "standard_time": Decimal("1.5"), "setup_time": Decimal("0.5"), "description": "装配工序"},
    {"name": "热处理", "code": "PROC_HEAT_TREATMENT", "standard_time": Decimal("2.0"), "setup_time": Decimal("1.0"), "description": "热处理工序"},
    {"name": "表面处理", "code": "PROC_SURFACE_TREATMENT", "standard_time": Decimal("0.5"), "setup_time": Decimal("0.25"), "description": "表面处理工序"},
]


# ── 能源单价种子数据 ───────────────────────────────────────────────────────────

_ENERGY_RATE_SEEDS = [
    {"name": "工业用电", "code": "ELEC_INDUSTRIAL", "energy_type": "ELECTRICITY", "unit_price": Decimal("0.85"), "unit_code": "kWh", "description": "工业用电基准单价"},
    {"name": "工业用水", "code": "WATER_INDUSTRIAL", "energy_type": "WATER", "unit_price": Decimal("4.5"), "unit_code": "L", "description": "工业用水基准单价"},
    {"name": "天然气", "code": "GAS_NATURAL", "energy_type": "GAS", "unit_price": Decimal("3.5"), "unit_code": "m3", "description": "天然气基准单价"},
    {"name": "蒸汽", "code": "STEAM_INDUSTRIAL", "energy_type": "STEAM", "unit_price": Decimal("250.0"), "unit_code": "t", "description": "工业蒸汽基准单价"},
    {"name": "压缩空气", "code": "AIR_COMPRESSED", "energy_type": "COMPRESSED_AIR", "unit_price": Decimal("0.15"), "unit_code": "m3", "description": "压缩空气基准单价"},
]


# ── 能源日历种子数据（峰平谷电价）─────────────────────────────────────────────

_ENERGY_CALENDAR_SEEDS = [
    {"energy_rate_code": "ELEC_INDUSTRIAL", "name": "峰时段", "start_time": "08:00:00", "end_time": "12:00:00", "multiplier": Decimal("1.5"), "description": "早高峰电价"},
    {"energy_rate_code": "ELEC_INDUSTRIAL", "name": "平时段", "start_time": "12:00:00", "end_time": "18:00:00", "multiplier": Decimal("1.0"), "description": "正常电价"},
    {"energy_rate_code": "ELEC_INDUSTRIAL", "name": "峰时段", "start_time": "18:00:00", "end_time": "22:00:00", "multiplier": Decimal("1.5"), "description": "晚高峰电价"},
    {"energy_rate_code": "ELEC_INDUSTRIAL", "name": "谷时段", "start_time": "22:00:00", "end_time": "08:00:00", "multiplier": Decimal("0.5"), "description": "低谷电价"},
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


def _ensure_dict_type(db: Session, seed: dict) -> SysDictType:
    dict_type = db.execute(
        select(SysDictType).where(
            SysDictType.code == seed["code"],
            SysDictType.is_deleted == False,
        )
    ).scalar_one_or_none()

    if dict_type is None:
        dict_type = SysDictType(**seed, created_by="system", updated_by="system")
        db.add(dict_type)
        db.flush()
        print(f"  [+] 创建字典类型：{dict_type.name}（{dict_type.code}）")
        return dict_type

    changed = False
    for field in ("name", "description", "sort_order", "is_active"):
        if field in seed and getattr(dict_type, field) != seed[field]:
            setattr(dict_type, field, seed[field])
            changed = True
    if changed:
        dict_type.updated_by = "system"
        db.flush()
        print(f"  [~] 更新字典类型：{dict_type.name}（{dict_type.code}）")
    else:
        print(f"  [=] 字典类型已存在，跳过：{dict_type.name}（{dict_type.code}）")

    return dict_type


def _ensure_dict_types(db: Session) -> dict[str, SysDictType]:
    dict_types: dict[str, SysDictType] = {}
    for seed in _SYSTEM_DICT_TYPE_SEEDS:
        dict_type = _ensure_dict_type(db, seed)
        dict_types[dict_type.code] = dict_type
    return dict_types


def _ensure_dict_item(db: Session, dict_type: SysDictType, seed: dict) -> SysDictItem:
    item = db.execute(
        select(SysDictItem).where(
            SysDictItem.dict_type_id == dict_type.id,
            SysDictItem.value == seed["value"],
            SysDictItem.is_deleted == False,
        )
    ).scalar_one_or_none()

    if item is None:
        item = SysDictItem(
            dict_type_id=dict_type.id,
            value=seed["value"],
            label=seed["label"],
            description=seed.get("description"),
            sort_order=seed.get("sort_order", 0),
            is_active=seed.get("is_active", True),
            extra_json=seed.get("extra_json"),
            created_by="system",
            updated_by="system",
        )
        db.add(item)
        db.flush()
        print(f"  [+] 创建字典项：{dict_type.code}.{item.value}")
        return item

    changed = False
    for field in ("label", "description", "sort_order", "is_active", "extra_json"):
        new_val = seed.get(field)
        if field == "is_active" and new_val is None:
            new_val = True
        elif field == "sort_order" and new_val is None:
            new_val = 0
            
        if getattr(item, field) != new_val:
            setattr(item, field, new_val)
            changed = True
    if changed:
        item.updated_by = "system"
        db.flush()
        print(f"  [~] 更新字典项：{dict_type.code}.{item.value}")
    else:
        print(f"  [=] 字典项已存在，跳过：{dict_type.code}.{item.value}")

    return item


def _ensure_dict_items(db: Session, dict_types: dict[str, SysDictType]) -> None:
    for dict_code, items in _SYSTEM_DICT_ITEM_SEEDS.items():
        dict_type = dict_types[dict_code]
        for seed in items:
            _ensure_dict_item(db, dict_type, seed)


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


# ── 资源分类初始化函数 ─────────────────────────────────────────────────────────

def _ensure_resource_category(db: Session, seed: dict, parent_map: dict[str, int]) -> MdResourceCategory:
    category = db.execute(
        select(MdResourceCategory).where(
            MdResourceCategory.code == seed["code"],
            MdResourceCategory.is_deleted == False,
        )
    ).scalar_one_or_none()

    parent_id = None
    if seed.get("parent_code"):
        parent_id = parent_map.get(seed["parent_code"])

    if category is None:
        category = MdResourceCategory(
            name=seed["name"],
            code=seed["code"],
            resource_type=seed["resource_type"],
            parent_id=parent_id,
            sort_order=seed.get("sort_order", 0),
            is_active=seed.get("is_active", True),
            description=seed.get("description"),
            created_by="system",
            updated_by="system",
        )
        db.add(category)
        db.flush()
        parent_map[category.code] = category.id
        print(f"  [+] 创建分类：{category.name}（{category.code}）")
        return category

    changed = False
    if category.name != seed["name"]:
        category.name = seed["name"]
        changed = True
    if category.resource_type != seed["resource_type"]:
        category.resource_type = seed["resource_type"]
        changed = True
    if category.parent_id != parent_id:
        category.parent_id = parent_id
        changed = True
    if seed.get("sort_order") and category.sort_order != seed["sort_order"]:
        category.sort_order = seed["sort_order"]
        changed = True
    if seed.get("is_active") is not None and category.is_active != seed["is_active"]:
        category.is_active = seed["is_active"]
        changed = True
    if seed.get("description") and category.description != seed["description"]:
        category.description = seed["description"]
        changed = True

    parent_map[category.code] = category.id

    if changed:
        category.updated_by = "system"
        db.flush()
        print(f"  [~] 更新分类：{category.name}（{category.code}）")
    else:
        print(f"  [=] 分类已存在，跳过：{category.name}（{category.code}）")

    return category


def _ensure_resource_categories(db: Session) -> dict[str, MdResourceCategory]:
    parent_map: dict[str, int] = {}
    categories: dict[str, MdResourceCategory] = {}

    for seed in _RESOURCE_CATEGORY_SEEDS:
        category = _ensure_resource_category(db, seed, parent_map)
        categories[category.code] = category

    return categories


# ── 属性定义初始化函数 ─────────────────────────────────────────────────────────

def _ensure_attr_definition(
    db: Session,
    seed: dict,
    units: dict[str, MdUnit],
) -> MdAttrDefinition:
    attr = db.execute(
        select(MdAttrDefinition).where(
            MdAttrDefinition.code == seed["code"],
            MdAttrDefinition.is_deleted == False,
        )
    ).scalar_one_or_none()

    unit_id = None
    if seed.get("unit_code"):
        unit = units.get(seed["unit_code"])
        if unit:
            unit_id = unit.id

    if attr is None:
        attr = MdAttrDefinition(
            name=seed["name"],
            code=seed["code"],
            data_type=seed["data_type"],
            unit_id=unit_id,
            applicable_resource_types=seed.get("applicable_resource_types"),
            description=seed.get("description"),
            is_required=seed.get("is_required", False),
            default_value=seed.get("default_value"),
            enum_values=seed.get("enum_values"),
            created_by="system",
            updated_by="system",
        )
        db.add(attr)
        db.flush()
        print(f"  [+] 创建属性：{attr.name}（{attr.code}）")
        return attr

    changed = False
    if attr.name != seed["name"]:
        attr.name = seed["name"]
        changed = True
    if attr.data_type != seed["data_type"]:
        attr.data_type = seed["data_type"]
        changed = True
    if attr.unit_id != unit_id:
        attr.unit_id = unit_id
        changed = True
    if seed.get("applicable_resource_types") and attr.applicable_resource_types != seed["applicable_resource_types"]:
        attr.applicable_resource_types = seed["applicable_resource_types"]
        changed = True
    if seed.get("description") and attr.description != seed["description"]:
        attr.description = seed["description"]
        changed = True
    if seed.get("is_required") is not None and attr.is_required != seed["is_required"]:
        attr.is_required = seed["is_required"]
        changed = True
    if seed.get("default_value") and attr.default_value != seed["default_value"]:
        attr.default_value = seed["default_value"]
        changed = True
    if seed.get("enum_values") and attr.enum_values != seed["enum_values"]:
        attr.enum_values = seed["enum_values"]
        changed = True

    if changed:
        attr.updated_by = "system"
        db.flush()
        print(f"  [~] 更新属性：{attr.name}（{attr.code}）")
    else:
        print(f"  [=] 属性已存在，跳过：{attr.name}（{attr.code}）")

    return attr


def _ensure_attr_definitions(db: Session, units: dict[str, MdUnit]) -> None:
    for seed in _ATTR_DEFINITION_SEEDS:
        _ensure_attr_definition(db, seed, units)


def _ensure_resource_category(
    db: Session,
    seed: dict,
    parent_by_code: dict[str, "MdResourceCategory"],
) -> MdResourceCategory:
    category = db.execute(
        select(MdResourceCategory).where(
            MdResourceCategory.code == seed["code"],
            MdResourceCategory.is_deleted == False,
        )
    ).scalar_one_or_none()

    parent_id = None
    if seed.get("parent_code"):
        parent = parent_by_code.get(seed["parent_code"])
        if parent:
            parent_id = parent.id

    if category is None:
        category = MdResourceCategory(
            name=seed["name"],
            code=seed["code"],
            resource_type=seed["resource_type"],
            parent_id=parent_id,
            sort_order=seed.get("sort_order", 0),
            is_active=True,
            description=seed.get("description"),
            created_by="system",
            updated_by="system",
        )
        db.add(category)
        db.flush()
        print(f"  [+] 创建资源分类：{category.name}（{category.code}）")
        return category

    changed = False
    for field in ("name", "sort_order", "is_active", "description"):
        if field in seed and getattr(category, field) != seed.get(field):
            setattr(category, field, seed.get(field))
            changed = True
    if category.parent_id != parent_id:
        category.parent_id = parent_id
        changed = True
    if category.resource_type != seed["resource_type"]:
        category.resource_type = seed["resource_type"]
        changed = True
    if changed:
        category.updated_by = "system"
        db.flush()
        print(f"  [~] 更新资源分类：{category.name}（{category.code}）")
    else:
        print(f"  [=] 资源分类已存在，跳过：{category.name}（{category.code}）")

    return category


def _ensure_resource_categories(db: Session) -> dict[str, MdResourceCategory]:
    categories: dict[str, MdResourceCategory] = {}
    for seed in _RESOURCE_CATEGORY_SEEDS:
        category = _ensure_resource_category(db, seed, categories)
        categories[category.code] = category
    return categories


def _ensure_attr_definition(
    db: Session,
    seed: dict,
    units: dict[str, MdUnit],
) -> MdAttrDefinition:
    attr = db.execute(
        select(MdAttrDefinition).where(
            MdAttrDefinition.code == seed["code"],
            MdAttrDefinition.is_deleted == False,
        )
    ).scalar_one_or_none()

    unit_id = None
    if seed.get("unit_code"):
        unit = units.get(seed["unit_code"])
        if unit:
            unit_id = unit.id

    if attr is None:
        attr = MdAttrDefinition(
            name=seed["name"],
            code=seed["code"],
            data_type=seed["data_type"],
            unit_id=unit_id,
            applicable_resource_types=seed.get("applicable_resource_types"),
            description=seed.get("description"),
            is_required=seed.get("is_required", False),
            default_value=seed.get("default_value"),
            enum_values=seed.get("enum_values"),
            created_by="system",
            updated_by="system",
        )
        db.add(attr)
        db.flush()
        print(f"  [+] 创建属性定义：{attr.name}（{attr.code}）")
        return attr

    changed = False
    for field in ("name", "description", "is_required", "default_value"):
        if field in seed and getattr(attr, field) != seed.get(field):
            setattr(attr, field, seed.get(field))
            changed = True
    if attr.unit_id != unit_id:
        attr.unit_id = unit_id
        changed = True
    if attr.data_type != seed["data_type"]:
        attr.data_type = seed["data_type"]
        changed = True
    if seed.get("applicable_resource_types") and attr.applicable_resource_types != seed["applicable_resource_types"]:
        attr.applicable_resource_types = seed["applicable_resource_types"]
        changed = True
    if seed.get("enum_values") and attr.enum_values != seed["enum_values"]:
        attr.enum_values = seed["enum_values"]
        changed = True
    if changed:
        attr.updated_by = "system"
        db.flush()
        print(f"  [~] 更新属性定义：{attr.name}（{attr.code}）")
    else:
        print(f"  [=] 属性定义已存在，跳过：{attr.name}（{attr.code}）")

    return attr


def _ensure_attr_definitions(db: Session, units: dict[str, MdUnit]) -> None:
    for seed in _ATTR_DEFINITION_SEEDS:
        _ensure_attr_definition(db, seed, units)


# ── 主入口 ─────────────────────────────────────────────────────────────────────

def run_seed() -> None:
    print("\n======================================")
    print("  LCC 平台 — 初始数据填充（幂等模式）")
    print("======================================\n")

    db: Session = SessionLocal()
    try:
        print("[Step 1] 初始化根部门...")
        dept = _ensure_root_department(db)
        db.commit()
        print("  [OK] 已提交")

        print("\n[Step 2] 初始化模块六权限点...")
        permissions = _ensure_system_permissions(db)
        db.commit()
        print("  [OK] 已提交")

        print("\n[Step 3] 初始化内置角色...")
        roles = _ensure_builtin_roles(db)
        db.commit()
        print("  [OK] 已提交")

        print("\n[Step 4] 绑定内置角色与权限...")
        _ensure_builtin_role_permissions(db, roles, permissions)
        db.commit()
        print("  [OK] 已提交")

        print("\n[Step 5] 初始化管理员账号...")
        user = _ensure_admin_user(db, dept)
        db.commit()
        print("  [OK] 已提交")

        print("\n[Step 6] 绑定用户与角色...")
        _ensure_user_role_binding(db, user, roles["SUPER_ADMIN"])
        db.commit()
        print("  [OK] 已提交")

        print("\n[Step 7] 初始化量纲定义...")
        dimensions = _ensure_unit_dimensions(db)
        db.commit()
        print("  [OK] 已提交")

        print("\n[Step 8] 初始化单位定义...")
        units = _ensure_units(db, dimensions)
        db.commit()
        print("  [OK] 已提交")

        print("\n[Step 9] 初始化单位换算...")
        _ensure_unit_conversions(db, units)
        db.commit()
        print("  [OK] 已提交")

        print("\n[Step 10] 初始化资源分类...")
        categories = _ensure_resource_categories(db)
        db.commit()
        print("  [OK] 已提交")

        print("\n[Step 11] 初始化属性定义...")
        _ensure_attr_definitions(db, units)
        db.commit()
        print("  [OK] 已提交")

        print("\n[Step 12] 初始化系统级字典类型...")
        dict_types = _ensure_dict_types(db)
        db.commit()
        print("  [OK] 已提交")

        print("\n[Step 13] 初始化系统级字典项...")
        _ensure_dict_items(db, dict_types)
        db.commit()
        print("  [OK] 已提交")

        print("\n[Done] 初始化完成，所有数据已提交。\n")

    except Exception as e:
        db.rollback()
        print(f"\n[Error] 初始化失败，已回滚：{e}\n")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
