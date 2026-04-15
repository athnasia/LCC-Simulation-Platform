"""
系统管理域 ORM 模型

包含：
  - OrgDepartment       部门表（支持树形嵌套）
  - SysUser             系统用户表
  - SysRole             角色表
  - SysPermission       权限表（支持层级）
  - SysUserRole         用户-角色关联表
  - SysRolePermission   角色-权限关联表
  - SysAuditLog         操作审计日志表（不继承 AuditMixin，本身即为审计记录）
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditMixin, Base


# ── 部门 ───────────────────────────────────────────────────────────────────────

class OrgDepartment(AuditMixin, Base):
    __tablename__ = "org_department"
    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uq_org_department_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="部门名称")
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="部门编码")
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("org_department.id"), nullable=True, comment="父部门 ID"
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序值，升序")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", comment="是否启用")

    # 自关联树
    parent: Mapped["OrgDepartment | None"] = relationship(
        "OrgDepartment",
        back_populates="children",
        remote_side="OrgDepartment.id",
        foreign_keys=[parent_id],
    )
    children: Mapped[list["OrgDepartment"]] = relationship(
        "OrgDepartment",
        back_populates="parent",
        foreign_keys=[parent_id],
    )
    users: Mapped[list["SysUser"]] = relationship("SysUser", back_populates="department")


# ── 用户 ───────────────────────────────────────────────────────────────────────

class SysUser(AuditMixin, Base):
    __tablename__ = "sys_user"
    __table_args__ = (
        UniqueConstraint("username", "is_deleted", name="uq_sys_user_username_deleted"),
        UniqueConstraint("email", "is_deleted", name="uq_sys_user_email_deleted"),
    )

    username: Mapped[str] = mapped_column(String(64), nullable=False, comment="登录用户名")
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False, comment="bcrypt 密码哈希")
    real_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="真实姓名")
    email: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="邮箱")
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="手机号")
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1", nullable=False, comment="账号是否启用"
    )
    department_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("org_department.id"), nullable=True, comment="所属部门 ID"
    )

    department: Mapped["OrgDepartment | None"] = relationship("OrgDepartment", back_populates="users")
    # 通过关联表获取角色列表，viewonly=True 防止直接操作 secondary 表
    roles: Mapped[list["SysRole"]] = relationship(
        "SysRole",
        secondary="sys_user_role",
        viewonly=True,
        lazy="selectin",
    )
    user_roles: Mapped[list["SysUserRole"]] = relationship(
        "SysUserRole", back_populates="user", cascade="all, delete-orphan"
    )


# ── 角色 ───────────────────────────────────────────────────────────────────────

class SysRole(AuditMixin, Base):
    __tablename__ = "sys_role"
    __table_args__ = (
        UniqueConstraint("name", "is_deleted", name="uq_sys_role_name_deleted"),
        UniqueConstraint("code", "is_deleted", name="uq_sys_role_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="角色显示名称")
    code: Mapped[str] = mapped_column(String(50), nullable=False, comment="角色唯一编码（程序内使用）")
    description: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="角色描述")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", comment="是否启用")

    permissions: Mapped[list["SysPermission"]] = relationship(
        "SysPermission",
        secondary="sys_role_permission",
        viewonly=True,
        lazy="selectin",
    )
    role_permissions: Mapped[list["SysRolePermission"]] = relationship(
        "SysRolePermission", back_populates="role", cascade="all, delete-orphan"
    )


# ── 权限 ───────────────────────────────────────────────────────────────────────

class SysPermission(AuditMixin, Base):
    __tablename__ = "sys_permission"
    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uq_sys_permission_code_deleted"),
    )

    name: Mapped[str] = mapped_column(String(64), nullable=False, comment="权限显示名称")
    code: Mapped[str] = mapped_column(String(100), nullable=False, comment="权限唯一编码")
    resource: Mapped[str] = mapped_column(String(200), nullable=False, comment="资源路径（如 /api/v1/materials）")
    action: Mapped[str] = mapped_column(String(20), nullable=False, comment="操作类型：read/write/delete/admin")
    description: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="权限描述")
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("sys_permission.id"), nullable=True, comment="父权限 ID（用于菜单分组）"
    )

    parent: Mapped["SysPermission | None"] = relationship(
        "SysPermission",
        back_populates="children",
        remote_side="SysPermission.id",
        foreign_keys=[parent_id],
    )
    children: Mapped[list["SysPermission"]] = relationship(
        "SysPermission",
        back_populates="parent",
        foreign_keys=[parent_id],
    )


# ── 关联表 ─────────────────────────────────────────────────────────────────────

class SysUserRole(AuditMixin, Base):
    __tablename__ = "sys_user_role"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sys_user.id", ondelete="CASCADE"), nullable=False, comment="用户 ID"
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sys_role.id", ondelete="CASCADE"), nullable=False, comment="角色 ID"
    )

    user: Mapped["SysUser"] = relationship("SysUser", back_populates="user_roles")
    role: Mapped["SysRole"] = relationship("SysRole")


class SysRolePermission(AuditMixin, Base):
    __tablename__ = "sys_role_permission"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sys_role.id", ondelete="CASCADE"), nullable=False, comment="角色 ID"
    )
    permission_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sys_permission.id", ondelete="CASCADE"), nullable=False, comment="权限 ID"
    )

    role: Mapped["SysRole"] = relationship("SysRole", back_populates="role_permissions")
    permission: Mapped["SysPermission"] = relationship("SysPermission")


# ── 审计日志 ───────────────────────────────────────────────────────────────────

class SysAuditLog(Base):
    """
    操作审计日志。
    不继承 AuditMixin，因为它本身就是审计记录，且禁止逻辑删除（日志必须只增不删）。
    """
    __tablename__ = "sys_audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="操作人用户 ID")
    username: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="操作人用户名（快照）")
    action: Mapped[str] = mapped_column(String(50), nullable=False, comment="操作动作（CREATE/UPDATE/DELETE/LOGIN）")
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="操作对象类型")
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="操作对象 ID")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True, comment="操作详情（JSON 字符串）")
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="客户端 IP")
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="User-Agent")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, comment="记录时间"
    )
