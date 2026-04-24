# 菜单、路由与权限矩阵

本文档用于统一前端菜单、前端路由、后端权限资源和数据库授权表的口径。

## 1. 菜单树

### 1.1 首页

| 菜单 | 页面标题 | 前端路由 | 路由读权限 |
| --- | --- | --- | --- |
| 首页 | 首页 | /dashboard | 无独立 scope，登录后可见 |

### 1.2 主数据中心

| 菜单 | 页面标题 | 前端路由 | 路由读权限 | 后端资源权限 |
| --- | --- | --- | --- | --- |
| 业务字典 | 基础字典与模板 | /master-data/dictionaries | /master-data/dict-templates:read | /master-data/dict-templates |
| 物料与材料台账 | 材料台账 | /master-data/materials | /master-data/materials:read | /master-data/materials |
| 设备资产台账 | 设备能力库 | /master-data/equipments | /master-data/equipments:read | /master-data/equipments |
| 工艺字典 | 工艺工时库 | /master-data/processes | /master-data/processes:read | /master-data/processes |
| 人员岗位与费率 | 人员技能矩阵 | /master-data/labor | /master-data/labor:read | /master-data/labor |
| 能源与日历中心 | 能源日历 | /master-data/energy | /master-data/energy:read | /master-data/energy |

### 1.3 工程建模中心

| 菜单 | 页面标题 | 前端路由 | 路由读权限 | 后端资源权限 |
| --- | --- | --- | --- | --- |
| 产品方案池 | 产品方案池 | /engineering/projects | /engineering/projects:read | /engineering/projects, /engineering/products, /engineering/schemes, /engineering/scheme-versions |
| 设计要素编排 | 设计要素编排 | /engineering/workbench | /engineering/bom-nodes:read | /engineering/bom-nodes, /engineering/process-routes, /engineering/route-steps |

### 1.4 成本仿真与决策

| 菜单 | 页面标题 | 前端路由 | 路由读权限 | 后端资源权限 |
| --- | --- | --- | --- | --- |
| 财务评估标准 | LCC财务评估标准 | /costing/lcc-financial-baselines | /costing/lcc-financial-baselines:read | /costing/lcc-financial-baselines |
| 产品快照中心 | 全景快照中心 | /costing/snapshot-center | /engineering/snapshots:read | /engineering/snapshots |
| 仿真结果优选与决策 | 全景快照中心 | /costing/decision-center | /engineering/snapshots:read | /engineering/snapshots |

### 1.5 系统管理

| 菜单 | 页面标题 | 前端路由 | 路由读权限 | 后端资源权限 |
| --- | --- | --- | --- | --- |
| 数据字典 | 数据字典 | /system/dictionaries | /system/dictionaries:read | /system/dictionaries |
| 用户管理 | 用户管理 | /system/users | /system/users:read | /system/users |
| 菜单权限 | 菜单权限 | /system/permissions | /system/permissions:read | /system/permissions |
| 角色权限 | 角色权限 | /system/roles | /system/roles:read | /system/roles |
| 审计日志 | 审计日志 | /system/audit | /system/audit-logs:read | /system/audit-logs |

## 2. 后端授权模型

### 2.1 授权核心表

| 表名 | 作用 | 关键字段 |
| --- | --- | --- |
| sys_permission | 权限定义表 | code, resource, action, parent_id |
| sys_role | 角色定义表 | code, name, is_active |
| sys_role_permission | 角色与权限关联表 | role_id, permission_id |
| sys_user | 用户表 | username, is_active, department_id |
| sys_user_role | 用户与角色关联表 | user_id, role_id |

### 2.2 权限动作约定

| action | 含义 |
| --- | --- |
| read | 页面进入、列表、详情、树查询 |
| write | 新建、编辑、发布、复制、重排、升版 |
| delete | 删除 |
| admin | 高级管理动作，如重置密码 |

## 3. 业务表映射

| 功能域 | 核心表 |
| --- | --- |
| 基础字典与模板 | md_attr_definition, md_resource_category, md_unit_dimension, md_unit, md_unit_conversion |
| 材料台账 | md_material |
| 设备能力库 | md_equipment |
| 工艺工时库 | md_process, md_process_resource |
| 人员技能矩阵 | md_labor |
| 能源日历 | md_energy_rate, md_energy_calendar |
| 产品方案池 | eng_project, eng_product, eng_design_scheme, eng_design_scheme_version |
| 设计要素编排 | eng_bom_node, eng_component_process_route, eng_route_step_bind |
| 全景快照中心 | eng_model_snapshot |
| LCC财务评估标准 | eng_lcc_financial_baseline |
| 系统管理 | org_department, sys_permission, sys_role, sys_user, sys_audit_log |

## 4. 当前实现口径

| 项目 | 当前实现 |
| --- | --- |
| 前端菜单定义 | frontend/src/layouts/AppLayout.vue |
| 前端路由定义 | frontend/src/router/index.ts |
| 后端权限种子 | backend/app/core/init_db.py |
| 后端权限校验入口 | backend/app/core/dependencies.py 中 require_permission |
| 权限树展示页 | frontend/src/views/system/PermissionsView.vue |

## 5. 特殊说明

| 场景 | 说明 |
| --- | --- |
| 产品快照中心 与 仿真结果优选与决策 | 两个菜单当前共用同一页面组件 SnapshotCenterView，统一读取 /engineering/snapshots:read |
| 旧仿真菜单路由 | /simulation/tasks 与 /simulation/results 当前仍保留为历史路由，但已不在主菜单树中展示 |
| 首页权限 | 当前未单独设置 dashboard read scope，默认登录后可进入首页 |
