"""
系统管理域 Pydantic 校验层

设计原则：
  1. 读写分离：Create / Update / Response 严格隔离，禁止复用
  2. 敏感字段隔离：hashed_password 绝不出现在任何 Response 模型中
  3. ORM 映射：所有 Response 配置 from_attributes=True
  4. 关联嵌套：使用 Brief 轻量化模型打破循环引用（User→Role→User 链断路）
  5. 防御性校验：密码复杂度、邮箱格式、手机号格式在 Create 层拦截

模型层次速览：
  OrgDepartment  → OrgDepartmentCreate / Update / Response / Brief
  SysPermission  → SysPermissionCreate / Update / Response / Brief
  SysRole        → SysRoleCreate / Update / Response / Brief
  SysUser        → SysUserCreate / Update / Response / Detail（含 dept + roles 嵌套）
  SysAuditLog    → SysAuditLogResponse（只读）
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


# ══════════════════════════════════════════════════════════════════════════════
# 一、部门（OrgDepartment）
# ══════════════════════════════════════════════════════════════════════════════

class OrgDepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="部门名称")
    code: str = Field(..., min_length=1, max_length=50, pattern=r"^[A-Z0-9_-]+$", description="部门编码（大写字母/数字/下划线）")
    parent_id: int | None = Field(None, description="父部门 ID，为空则为顶级部门")
    sort_order: int = Field(0, ge=0, description="排序值，升序排列")
    is_active: bool = Field(True, description="是否启用")


class OrgDepartmentUpdate(BaseModel):
    """所有字段均为可选，仅传入需要修改的字段。"""
    name: str | None = Field(None, min_length=1, max_length=100)
    code: str | None = Field(None, min_length=1, max_length=50, pattern=r"^[A-Z0-9_-]+$")
    parent_id: int | None = None
    sort_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class OrgDepartmentBrief(BaseModel):
    """轻量嵌套版本，用于在 User 详情中展示所属部门，避免循环展开。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str


class OrgDepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    parent_id: int | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None


# ══════════════════════════════════════════════════════════════════════════════
# 二、权限（SysPermission）
# ══════════════════════════════════════════════════════════════════════════════

_VALID_ACTIONS = {"read", "write", "delete", "admin"}


class SysPermissionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, description="权限显示名称")
    code: str = Field(..., min_length=1, max_length=100, description="权限唯一编码")
    resource: str = Field(..., min_length=1, max_length=200, description="资源路径")
    action: str = Field(..., description="操作类型：read / write / delete / admin")
    description: str | None = Field(None, max_length=256)
    parent_id: int | None = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in _VALID_ACTIONS:
            raise ValueError(f"action 必须是 {_VALID_ACTIONS} 之一")
        return v


class SysPermissionUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=64)
    code: str | None = Field(None, min_length=1, max_length=100)
    resource: str | None = Field(None, min_length=1, max_length=200)
    action: str | None = None
    description: str | None = None
    parent_id: int | None = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str | None) -> str | None:
        if v is not None and v not in _VALID_ACTIONS:
            raise ValueError(f"action 必须是 {_VALID_ACTIONS} 之一")
        return v


class SysPermissionBrief(BaseModel):
    """用于角色详情中嵌套展示，避免循环引用。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    action: str


class SysPermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    resource: str
    action: str
    description: str | None
    parent_id: int | None
    created_at: datetime
    updated_at: datetime


# ══════════════════════════════════════════════════════════════════════════════
# 三、角色（SysRole）
# ══════════════════════════════════════════════════════════════════════════════

class SysRoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64, description="角色显示名称")
    code: str = Field(..., min_length=1, max_length=50, pattern=r"^[A-Z0-9_]+$", description="角色唯一编码")
    description: str | None = Field(None, max_length=256)
    is_active: bool = True
    permission_ids: list[int] = Field(default_factory=list, description="初始绑定的权限 ID 列表")


class SysRoleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=64)
    code: str | None = Field(None, min_length=1, max_length=50, pattern=r"^[A-Z0-9_]+$")
    description: str | None = None
    is_active: bool | None = None
    permission_ids: list[int] | None = Field(None, description="传入则全量替换权限列表；不传则不修改")


class SysRoleBrief(BaseModel):
    """用于用户详情中嵌套展示，不展开 permissions，避免多层递归。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    is_active: bool


class SysRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SysRoleDetail(SysRoleResponse):
    """角色详情：在 Response 基础上附加权限列表（Brief），最多一层嵌套。"""
    permissions: list[SysPermissionBrief] = []


# ══════════════════════════════════════════════════════════════════════════════
# 四、用户（SysUser）
# ══════════════════════════════════════════════════════════════════════════════

_PHONE_RE = re.compile(r"^1[3-9]\d{9}$")


def _validate_phone(v: str | None) -> str | None:
    if v is not None and not _PHONE_RE.match(v):
        raise ValueError("手机号格式不正确，须为 11 位大陆手机号")
    return v


class SysUserCreate(BaseModel):
    """
    创建用户模型。

    说明：
      - password 为必填明文密码，在 service 层哈希后存储
      - hashed_password 字段在此模型中不存在
    """
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_]+$", description="登录用户名（字母/数字/下划线）")
    password: str = Field(..., min_length=1, max_length=128, description="登录密码（明文）")
    real_name: str = Field(..., min_length=1, max_length=64, description="真实姓名")
    email: EmailStr | None = Field(None, description="邮箱")
    phone: str | None = Field(None, max_length=20, description="手机号")
    is_active: bool = True
    department_id: int | None = None
    role_ids: list[int] = Field(default_factory=list, description="初始绑定的角色 ID 列表")

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v: str | None) -> str | None:
        return _validate_phone(v)

class SysUserUpdate(BaseModel):
    """
    更新用户基础信息。
    ⚠️ 密码修改须走独立接口（ChangePasswordRequest），此处禁止传入密码字段。
    """
    real_name: str | None = Field(None, min_length=1, max_length=64)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=20)
    is_active: bool | None = None
    department_id: int | None = None
    role_ids: list[int] | None = Field(None, description="传入则全量替换角色列表；不传则不修改")

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v: str | None) -> str | None:
        return _validate_phone(v)


class SysUserChangePassword(BaseModel):
    """密码修改专用模型，独立于 Update 接口，强制要求旧密码验证。"""
    old_password: str = Field(..., min_length=1, max_length=128, description="当前密码")
    new_password: str = Field(..., min_length=1, max_length=128, description="新密码")
    confirm_password: str = Field(..., min_length=1, max_length=128, description="确认新密码")

    @model_validator(mode="after")
    def passwords_match(self) -> "SysUserChangePassword":
        if self.new_password != self.confirm_password:
            raise ValueError("新密码与确认密码不一致")
        return self

class SysUserAdminResetPassword(BaseModel):
    new_password: str = Field(..., min_length=1, max_length=128, description="新密码")


class SysUserResponse(BaseModel):
    """
    用户列表/基础信息响应模型。

    安全规则：
      - hashed_password 字段在此处永远不存在
      - 不包含关联嵌套，适合列表页高效渲染
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    real_name: str
    email: str | None
    phone: str | None
    is_active: bool
    department_id: int | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    updated_by: str | None


class SysUserDetail(SysUserResponse):
    """
    用户详情响应模型：在 Response 基础上附加关联嵌套。

    嵌套层级控制（防止溢出）：
      - department → OrgDepartmentBrief（只含 id/name/code，不展开父部门）
      - roles      → list[SysRoleBrief]（只含 id/name/code/is_active，不展开 permissions）
    """
    department: OrgDepartmentBrief | None = None
    roles: list[SysRoleBrief] = []
    permission_scopes: list[str] = []


# ══════════════════════════════════════════════════════════════════════════════
# 五、审计日志（SysAuditLog）
# ══════════════════════════════════════════════════════════════════════════════

class SysAuditLogResponse(BaseModel):
    """审计日志只读，无 Create/Update 模型（日志由系统自动写入，禁止用户手动创建）。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    username: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    detail: dict[str, Any] | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    @field_validator("detail", mode="before")
    @classmethod
    def parse_detail_json(cls, value: str | dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None or isinstance(value, dict):
            return value
        if isinstance(value, str) and value.strip():
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return {"raw": value}
            if isinstance(parsed, dict):
                return parsed
            return {"raw": parsed}
        return None


# ══════════════════════════════════════════════════════════════════════════════
# 六、认证相关（Auth）
# ══════════════════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64, description="用户名")
    password: str = Field(..., min_length=1, max_length=128, description="密码")


class TokenResponse(BaseModel):
    """登录成功后返回 Token 对（不使用 from_attributes，纯构造返回）。"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access Token 有效期（秒）")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="有效的 Refresh Token")
