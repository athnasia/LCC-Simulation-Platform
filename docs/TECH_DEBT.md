# 技术债务清单（Technical Debt）

本文档记录系统中存在的技术债务，包括问题描述、影响范围、优先级和解决方案。

---

## 📋 技术债务列表

### TD-001: 单位换算链路图算法缺失

**状态**: 🔴 待实施  
**优先级**: 中等  
**创建时间**: 2026-04-15  
**影响模块**: 成本核算引擎  
**相关文件**: 
- `backend/app/services/master_data_service.py` (UnitConversionService.calculate 方法)

#### 问题描述

当前单位换算只支持"直连"换算，即必须存在直接的换算规则（A→B）。无法处理间接换算场景。

**示例场景**：
- 数据库中存在：`1t = 1000kg` 和 `1kg = 1000g`
- 用户请求：`1t = ?g`
- 当前行为：抛出异常"未找到对应的单位换算规则"
- 期望行为：自动计算 `1t = 1000kg × 1000g/kg = 1000000g`

#### 影响范围

- 成本核算引擎中的材料消耗计算
- 多级单位换算场景
- 用户手动录入换算规则的工作量

#### 解决方案

引入图搜索算法（BFS 或 Dijkstra）：

```python
# 伪代码示例
def find_conversion_path(from_unit_id: int, to_unit_id: int) -> ConversionPath:
    """
    使用 BFS 找到最短换算路径
    
    Returns:
        ConversionPath: 包含路径节点和累积换算因子
    """
    # 1. 构建单位换算图（邻接表）
    # 2. BFS 搜索 from_unit → to_unit 的最短路径
    # 3. 计算累积换算因子（路径上所有因子的乘积）
    # 4. 缓存结果避免重复计算
```

#### 实施建议

1. **数据结构优化**：
   - 在 Redis 中缓存单位换算图
   - 使用邻接表存储换算关系

2. **算法选择**：
   - 初期：BFS（广度优先搜索）- 找到最短路径即可
   - 后期：Dijkstra - 支持加权路径（如换算精度权重）

3. **性能优化**：
   - 缓存常用换算路径
   - 预计算高频换算对的结果

#### 验收标准

- [ ] 支持多级单位换算（A→B→C）
- [ ] 换算路径查询性能 < 100ms
- [ ] 单元测试覆盖率 > 90%
- [ ] API 文档更新

---

### TD-002: 权限资源路径魔法字符串

**状态**: 🔴 待实施  
**优先级**: 低  
**创建时间**: 2026-04-15  
**影响模块**: 全局权限控制  
**相关文件**:
- `backend/app/api/v1/routers/*.py` (所有路由文件)
- `backend/app/core/dependencies.py` (require_permission 函数)

#### 问题描述

权限校验中大量使用硬编码字符串，如：
```python
require_permission("/master-data/dict-templates", "write")
require_permission("/system/users", "read")
```

**存在的问题**：
1. URL 变更时需要全局搜索替换，容易遗漏
2. 拼写错误难以发现（如 `/system/user` vs `/system/users`）
3. 无法通过 IDE 重构工具自动更新
4. 缺乏类型检查和自动补全

#### 影响范围

- 所有路由文件的权限校验
- 权限管理模块的权限定义
- 前端路由守卫的权限判断

#### 解决方案

创建权限常量枚举：

```python
# backend/app/core/constants.py
from enum import Enum

class PermissionResource(str, Enum):
    """权限资源路径常量"""
    # 系统管理
    SYSTEM_DEPARTMENTS = "/system/departments"
    SYSTEM_PERMISSIONS = "/system/permissions"
    SYSTEM_ROLES = "/system/roles"
    SYSTEM_USERS = "/system/users"
    SYSTEM_AUDIT_LOGS = "/system/audit-logs"
    
    # 主数据
    MASTER_DATA_DICT_TEMPLATES = "/master-data/dict-templates"
    MASTER_DATA_MATERIALS = "/master-data/materials"
    MASTER_DATA_EQUIPMENTS = "/master-data/equipments"
    # ... 其他资源

class PermissionAction(str, Enum):
    """权限操作类型常量"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

# 使用示例
from app.core.constants import PermissionResource, PermissionAction

@router.post("/units")
def create_unit(
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(
        require_permission(PermissionResource.MASTER_DATA_DICT_TEMPLATES, PermissionAction.WRITE)
    ),
) -> UnitResponse:
    # ...
```

#### 实施建议

1. **创建常量文件**：
   - 新建 `backend/app/core/constants.py`
   - 定义 `PermissionResource` 和 `PermissionAction` 枚举

2. **批量重构**：
   - 使用 IDE 的重构工具批量替换硬编码字符串
   - 或编写脚本自动替换

3. **类型检查**：
   - 修改 `require_permission` 函数签名，接受枚举类型
   - 添加类型检查确保传入正确的枚举值

4. **文档更新**：
   - 更新 API 文档
   - 更新开发者指南

#### 验收标准

- [ ] 创建 `constants.py` 并定义所有权限常量
- [ ] 所有路由文件使用常量替代硬编码
- [ ] 类型检查通过（mypy）
- [ ] 单元测试通过
- [ ] API 文档更新

---

## 📊 技术债务统计

| ID | 状态 | 优先级 | 预计工作量 | 计划实施时间 |
|----|------|--------|-----------|-------------|
| TD-001 | 🔴 待实施 | 中等 | 3-5人日 | 成本核算引擎开发时 |
| TD-002 | 🔴 待实施 | 低 | 2-3人日 | 权限体系重构时 |

---

## 🔄 更新日志

### 2026-04-15
- 创建技术债务清单
- 记录 TD-001: 单位换算链路图算法缺失
- 记录 TD-002: 权限资源路径魔法字符串

---

## 📝 备注

技术债务不是"坏代码"，而是为了快速交付 MVP 而做出的合理取舍。关键在于：
1. **明确记录**：让团队知道存在哪些技术债务
2. **评估影响**：了解每个债务的风险和影响范围
3. **计划偿还**：在合适的时机进行重构

**原则**：先交付价值，再优化架构。
