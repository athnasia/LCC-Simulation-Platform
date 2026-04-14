# 模块六：系统与平台管理 — 后端接口文档

> **Base URL**: `http://{host}:8000/api/v1/system`
> **认证方式**: Bearer Token（JWT），通过 `POST /api/v1/auth/login` 获取
> **所有接口均需携带 Header**: `Authorization: Bearer <access_token>`

---

## 通用说明

### 通用分页响应结构

所有列表接口均返回统一分页包装体：

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

### 通用错误响应结构

```json
{
  "code": "BUSINESS_RULE_VIOLATION",
  "message": "部门编码「RD」已存在，请使用唯一编码",
  "detail": {}
}
```

| HTTP 状态码 | error_code | 说明 |
|---|---|---|
| 401 | `AUTHENTICATION_FAILED` | 未携带 Token 或 Token 无效/过期 |
| 403 | `PERMISSION_DENIED` | 账号已禁用 |
| 404 | `RESOURCE_NOT_FOUND` | 目标资源不存在 |
| 422 | `BUSINESS_RULE_VIOLATION` | 业务规则冲突（如唯一性约束、删除保护等）|

---

## 一、部门管理 `/departments`

### 1.1 部门列表

```
GET /api/v1/system/departments
```

**Query 参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `keyword` | string | 否 | 部门名称或编码模糊搜索 |
| `is_active` | boolean | 否 | 启用状态过滤 |
| `page` | integer | 否 | 页码，默认 1 |
| `size` | integer | 否 | 每页条数，默认 20，最大 100 |

**响应 200**

```json
{
  "items": [
    {
      "id": 1,
      "name": "集团总部",
      "code": "ROOT",
      "parent_id": null,
      "sort_order": 0,
      "is_active": true,
      "created_at": "2026-04-14T21:54:00Z",
      "updated_at": "2026-04-14T21:54:00Z",
      "created_by": null,
      "updated_by": null
    }
  ],
  "total": 1, "page": 1, "size": 20, "pages": 1
}
```

---

### 1.2 新建部门

```
POST /api/v1/system/departments
```

**请求体**

```json
{
  "name": "研发中心",
  "code": "RD",
  "parent_id": 1,
  "sort_order": 1,
  "is_active": true
}
```

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `name` | string | 是 | 1-100 字符 |
| `code` | string | 是 | 1-50 字符，`[A-Z0-9_-]+`，全局唯一 |
| `parent_id` | integer\|null | 否 | 父部门 ID，为 null 则为顶级 |
| `sort_order` | integer | 否 | 默认 0，非负整数 |
| `is_active` | boolean | 否 | 默认 true |

**响应 201**: 返回完整部门对象。

**业务规则保护**:
- `code` 唯一性校验，重复则返回 422
- `parent_id` 指向的父部门必须存在且未被删除

---

### 1.3 部门详情

```
GET /api/v1/system/departments/{dept_id}
```

**响应 200**: 返回单个部门对象。

---

### 1.4 更新部门

```
PUT /api/v1/system/departments/{dept_id}
```

**请求体**（所有字段可选，仅传入需修改的字段）

```json
{
  "name": "新名称",
  "sort_order": 5,
  "is_active": false
}
```

**业务规则保护**:
- `code` 修改时仍会检查唯一性
- `parent_id` 不能设置为自身（防止树结构循环）

**响应 200**: 返回更新后的部门对象。

---

### 1.5 删除部门（逻辑删除）

```
DELETE /api/v1/system/departments/{dept_id}
```

**响应 204**: 无内容。

**业务规则保护**（以下情况返回 422 并说明原因）:
- 该部门下存在未删除的**子部门**
- 该部门下存在**已绑定的用户**

---

## 二、权限管理 `/permissions`

### 2.1 权限列表

```
GET /api/v1/system/permissions
```

**Query 参数**

| 参数 | 类型 | 说明 |
|---|---|---|
| `keyword` | string | 名称/编码/资源路径模糊搜索 |
| `action` | string | 操作类型过滤：`read`/`write`/`delete`/`admin` |
| `page` | integer | 默认 1 |
| `size` | integer | 默认 20，最大 100 |

**响应 200**: 返回分页权限列表。

---

### 2.2 新建权限

```
POST /api/v1/system/permissions
```

**请求体**

```json
{
  "name": "材料主数据读取",
  "code": "MATERIAL_READ",
  "resource": "/api/v1/master-data/materials",
  "action": "read",
  "description": "允许查询材料主数据列表和详情",
  "parent_id": null
}
```

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `name` | string | 是 | 1-64 字符 |
| `code` | string | 是 | 1-100 字符，全局唯一 |
| `resource` | string | 是 | 1-200 字符，API 路径 |
| `action` | string | 是 | 枚举：`read`/`write`/`delete`/`admin` |
| `description` | string\|null | 否 | 最大 256 字符 |
| `parent_id` | integer\|null | 否 | 父权限节点 ID，用于菜单分组 |

**响应 201**: 返回创建的权限对象。

---

### 2.3 权限详情

```
GET /api/v1/system/permissions/{perm_id}
```

---

### 2.4 更新权限

```
PUT /api/v1/system/permissions/{perm_id}
```

所有字段可选，语义同创建接口。`action` 修改时仍需满足枚举约束。

**响应 200**: 返回更新后的权限对象。

---

### 2.5 删除权限（逻辑删除）

```
DELETE /api/v1/system/permissions/{perm_id}
```

**响应 204**: 无内容。

**业务规则保护**: 该权限节点下仍有**子权限**时返回 422。

---

## 三、角色管理 `/roles`

### 3.1 角色列表

```
GET /api/v1/system/roles
```

**Query 参数**: `keyword`、`is_active`、`page`、`size`（同部门列表）

**响应 200**: 返回分页角色列表（不含权限详情，仅基础字段）。

---

### 3.2 新建角色（含权限绑定）

```
POST /api/v1/system/roles
```

**请求体**

```json
{
  "name": "工艺工程师",
  "code": "PROCESS_ENG",
  "description": "负责工艺路线创建与设备指派",
  "is_active": true,
  "permission_ids": [1, 2, 3]
}
```

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `name` | string | 是 | 1-64 字符，全局唯一 |
| `code` | string | 是 | `[A-Z0-9_]+`，全局唯一 |
| `description` | string\|null | 否 | 最大 256 字符 |
| `is_active` | boolean | 否 | 默认 true |
| `permission_ids` | list[int] | 否 | 初始绑定的权限 ID 列表，默认空 |

**响应 201**: 返回角色详情（含嵌套的 `permissions` 列表）。

---

### 3.3 角色详情（含权限列表）

```
GET /api/v1/system/roles/{role_id}
```

**响应 200**

```json
{
  "id": 2,
  "name": "工艺工程师",
  "code": "PROCESS_ENG",
  "description": "...",
  "is_active": true,
  "created_at": "...",
  "updated_at": "...",
  "permissions": [
    { "id": 1, "name": "材料读取", "code": "MATERIAL_READ", "action": "read" },
    { "id": 2, "name": "设备写入", "code": "EQUIP_WRITE", "action": "write" }
  ]
}
```

---

### 3.4 更新角色

```
PUT /api/v1/system/roles/{role_id}
```

**请求体**（所有字段可选）

```json
{
  "is_active": false,
  "permission_ids": [1, 3]
}
```

> **重要**：`permission_ids` 传入时执行**全量替换**（先清除旧绑定，再写入新绑定）；不传则不修改权限关系。

**响应 200**: 返回更新后的角色详情（含最新权限列表）。

---

### 3.5 删除角色（逻辑删除）

```
DELETE /api/v1/system/roles/{role_id}
```

**响应 204**: 无内容。

**业务规则保护**: 仍有用户绑定此角色时返回 422，提示绑定用户数量。

---

## 四、用户管理 `/users`

### 4.1 用户列表

```
GET /api/v1/system/users
```

**Query 参数**

| 参数 | 类型 | 说明 |
|---|---|---|
| `keyword` | string | 用户名/姓名/邮箱模糊搜索 |
| `is_active` | boolean | 启用状态过滤 |
| `department_id` | integer | 按部门 ID 过滤 |
| `page` | integer | 默认 1 |
| `size` | integer | 默认 20，最大 100 |

**响应 200**: 返回分页用户列表（不含部门/角色嵌套，适合表格渲染）。

---

### 4.2 新建用户（含角色绑定）

```
POST /api/v1/system/users
```

**请求体**

```json
{
  "username": "zhangsan",
  "password": "Min@8chars",
  "real_name": "张三",
  "email": "zhangsan@company.com",
  "phone": "13800138000",
  "is_active": true,
  "department_id": 1,
  "role_ids": [1, 2]
}
```

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `username` | string | 是 | 3-64 字符，`[a-zA-Z0-9_]+`，全局唯一 |
| `password` | string | 是 | 1-128 字符明文（后端 bcrypt 哈希存储） |
| `real_name` | string | 是 | 1-64 字符 |
| `email` | string\|null | 否 | 合法邮箱格式，全局唯一 |
| `phone` | string\|null | 否 | 11 位大陆手机号 |
| `is_active` | boolean | 否 | 默认 true |
| `department_id` | integer\|null | 否 | 所属部门 ID，须存在 |
| `role_ids` | list[int] | 否 | 初始绑定角色列表，默认空 |

**安全保证**: `hashed_password` 字段永远不会出现在任何响应体中。

**响应 201**: 返回用户详情（含部门和角色嵌套）。

---

### 4.3 用户详情（含部门与角色）

```
GET /api/v1/system/users/{user_id}
```

**响应 200**

```json
{
  "id": 3,
  "username": "testuser01",
  "real_name": "TestUser",
  "email": "test01@lcc.com",
  "phone": null,
  "is_active": true,
  "department_id": null,
  "created_at": "...",
  "updated_at": "...",
  "created_by": "1",
  "updated_by": "1",
  "department": null,
  "roles": [
    { "id": 2, "name": "工艺工程师", "code": "PROCESS_ENG", "is_active": true }
  ]
}
```

---

### 4.4 更新用户基础信息

```
PUT /api/v1/system/users/{user_id}
```

**请求体**（所有字段可选）

```json
{
  "real_name": "张三（更新）",
  "department_id": 2,
  "role_ids": [1]
}
```

> **密码修改须走独立接口**，此处禁止传入密码字段。
> `role_ids` 传入时执行**全量替换**；不传则不修改角色绑定。

**响应 200**: 返回更新后的用户详情。

---

### 4.5 删除用户（逻辑删除）

```
DELETE /api/v1/system/users/{user_id}
```

**响应 204**: 无内容。

**业务规则保护**: 不允许账号删除自身（返回 422）。

---

### 4.6 管理员重置用户密码

```
POST /api/v1/system/users/{user_id}/reset-password
```

**请求体**

```json
{
  "new_password": "NewSecure@2026"
}
```

| 字段 | 类型 | 约束 |
|---|---|---|
| `new_password` | string | 最少 8 字符，最大 128 字符 |

> 无需验证旧密码，直接覆盖。仅限管理员操作，操作会写入审计日志。

**响应 204**: 无内容。

---

### 4.7 当前用户自助修改密码

```
POST /api/v1/system/me/change-password
```

**请求体**

```json
{
  "old_password": "Current@Pass",
  "new_password": "New@Pass2026",
  "confirm_password": "New@Pass2026"
}
```

| 字段 | 类型 | 约束 |
|---|---|---|
| `old_password` | string | 当前密码，1-128 字符 |
| `new_password` | string | 新密码，最少 8 字符，最大 128 字符 |
| `confirm_password` | string | 须与 `new_password` 完全一致 |

**业务规则**:
- `old_password` 不正确 → 422 `BUSINESS_RULE_VIOLATION`
- `new_password` 与 `confirm_password` 不一致 → Pydantic 422

**响应 204**: 无内容。

---

## 五、审计日志 `/audit-logs`（只读）

### 5.1 审计日志查询

```
GET /api/v1/system/audit-logs
```

**Query 参数**

| 参数 | 类型 | 说明 |
|---|---|---|
| `user_id` | integer | 按操作人用户 ID 过滤 |
| `action` | string | 操作类型：`CREATE`/`UPDATE`/`DELETE`/`RESET_PASSWORD`/`CHANGE_PASSWORD` |
| `resource_type` | string | 资源类型：`OrgDepartment`/`SysPermission`/`SysRole`/`SysUser` |
| `start_time` | datetime | 开始时间（ISO 8601）|
| `end_time` | datetime | 结束时间（ISO 8601）|
| `page` | integer | 默认 1 |
| `size` | integer | 默认 20，最大 100 |

**响应 200**

```json
{
  "items": [
    {
      "id": 12,
      "user_id": 1,
      "username": "admin",
      "action": "RESET_PASSWORD",
      "resource_type": "SysUser",
      "resource_id": "3",
      "detail": null,
      "ip_address": "127.0.0.1",
      "user_agent": null,
      "created_at": "2026-04-14T22:38:00Z"
    }
  ],
  "total": 12, "page": 1, "size": 20, "pages": 1
}
```

> 按操作时间**倒序**返回（最新操作在最前）。
> 审计日志只增不删，系统自动写入，禁止通过接口手动创建。

---

## 六、测试结果汇总

以下为实际运行测试的验证结果：

| 测试场景 | 期望结果 | 实测结果 |
|---|---|---|
| `POST /auth/login` 正确密码 | 200 + Token 对 | ✅ 通过 |
| `GET /departments` 列表分页 | 200 + total/pages | ✅ 通过 |
| `POST /departments` 新建部门 | 201 + 部门对象 | ✅ 通过 |
| `POST /departments` 重复 code | 422 业务规则冲突 | ✅ 通过 |
| `PUT /departments/{id}` 更新 | 200 + 更新后对象 | ✅ 通过 |
| `DELETE /departments` 有用户绑定 | 422 删除保护 | ✅ 通过 |
| `POST /permissions` 新建权限 | 201 + 权限对象 | ✅ 通过 |
| `POST /permissions` 重复 code | 422 业务规则冲突 | ✅ 通过 |
| `POST /roles` 含权限绑定 | 201 + 角色详情(含permissions) | ✅ 通过 |
| `GET /roles/{id}` 详情含权限 | 200 + permissions 数组 | ✅ 通过 |
| `POST /users` 含角色绑定 | 201 + 用户详情(含roles) | ✅ 通过 |
| `GET /users/{id}` 详情含部门+角色 | 200 + 嵌套数据 | ✅ 通过 |
| `POST /users/{id}/reset-password` | 204 + 新密码可登录 | ✅ 通过 |
| `POST /me/change-password` 旧密码错误 | 422 原密码不正确 | ✅ 通过 |
| `GET /audit-logs` 操作类型过滤 | 200 + 过滤后的日志 | ✅ 通过 |
| 所有写操作审计日志自动写入 | audit-logs total=12 | ✅ 通过 |
| 无 Token 访问任意接口 | 401 AUTHENTICATION_FAILED | ✅ 通过 |
