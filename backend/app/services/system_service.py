"""
系统管理域业务服务层

包含：
  - DepartmentService   部门 CRUD（树形保护、编码唯一性）
  - PermissionService   权限 CRUD（代码唯一性）
  - RoleService         角色 CRUD（权限批量绑定/全量替换）
  - UserService         用户 CRUD（角色挂载、密码哈希、自助改密）
  - AuditLogService     审计日志写入 + 分页查询

设计约定：
    1. 所有服务接收 Session 并在此层管理数据库操作，路由层只负责 I/O 转换
    2. 逻辑删除统一通过 is_deleted=True 实现，禁止物理 DELETE
    3. 写操作由路由层统一 commit，Service 内仅负责 add/flush
    4. 审计日志在关键写操作后由 AuditLogService.write() 随同当前事务提交
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload


class DecimalEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理 Decimal 类型"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.core.security import hash_password, verify_password
from app.models.system import (
    OrgDepartment,
    SysAuditLog,
    SysPermission,
    SysRole,
    SysRolePermission,
    SysUser,
    SysUserRole,
)
from app.schemas.common import PageResult
from app.schemas.system import (
    OrgDepartmentCreate,
    OrgDepartmentResponse,
    OrgDepartmentUpdate,
    SysAuditLogResponse,
    SysPermissionCreate,
    SysPermissionResponse,
    SysPermissionUpdate,
    SysRoleCreate,
    SysRoleDetail,
    SysRoleResponse,
    SysRoleUpdate,
    SysUserChangePassword,
    SysUserCreate,
    SysUserDetail,
    SysUserResponse,
    SysUserUpdate,
)


def _build_deleted_unique_value(value: str | None, record_id: int, max_length: int) -> str | None:
    if not value:
        return value

    suffix = f"__deleted__{record_id}"
    keep_length = max_length - len(suffix)
    if keep_length <= 0:
        return suffix[-max_length:]
    return f"{value[:keep_length]}{suffix}"


# ══════════════════════════════════════════════════════════════════════════════
# 一、部门服务
# ══════════════════════════════════════════════════════════════════════════════

class DepartmentService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── 内部工具 ──────────────────────────────────────────────────────────────

    def _get_or_404(self, dept_id: int) -> OrgDepartment:
        dept = self.db.execute(
            select(OrgDepartment).where(
                OrgDepartment.id == dept_id,
                OrgDepartment.is_deleted == False,
            )
        ).scalar_one_or_none()
        if dept is None:
            raise ResourceNotFoundError(resource="部门", identifier=dept_id)
        return dept

    def _assert_code_unique(self, code: str, exclude_id: int | None = None) -> None:
        stmt = select(OrgDepartment).where(
            OrgDepartment.code == code,
            OrgDepartment.is_deleted == False,
        )
        if exclude_id is not None:
            stmt = stmt.where(OrgDepartment.id != exclude_id)
        exists = self.db.execute(stmt).scalar_one_or_none()
        if exists is not None:
            raise BusinessRuleViolationError(
                message=f"部门编码「{code}」已存在，请使用唯一编码"
            )

    def _assert_no_cycle(self, dept_id: int, parent_id: int) -> None:
        ancestor = self._get_or_404(parent_id)
        visited_ids = {dept_id}

        while ancestor is not None:
            if ancestor.id in visited_ids:
                raise BusinessRuleViolationError(message="部门层级不能形成循环父子关系")
            visited_ids.add(ancestor.id)

            if ancestor.parent_id is None:
                break

            ancestor = self.db.execute(
                select(OrgDepartment).where(
                    OrgDepartment.id == ancestor.parent_id,
                    OrgDepartment.is_deleted == False,
                )
            ).scalar_one_or_none()

    # ── 查询 ──────────────────────────────────────────────────────────────────

    def list(
        self,
        *,
        keyword: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[OrgDepartmentResponse]:
        stmt = select(OrgDepartment).where(OrgDepartment.is_deleted == False)

        if keyword:
            stmt = stmt.where(
                or_(
                    OrgDepartment.name.ilike(f"%{keyword}%"),
                    OrgDepartment.code.ilike(f"%{keyword}%"),
                )
            )
        if is_active is not None:
            stmt = stmt.where(OrgDepartment.is_active == is_active)

        total: int = self.db.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar_one()

        rows = self.db.execute(
            stmt.order_by(OrgDepartment.sort_order, OrgDepartment.id)
            .offset((page - 1) * size)
            .limit(size)
        ).scalars().all()

        return PageResult.build(
            items=[OrgDepartmentResponse.model_validate(r) for r in rows],
            total=total,
            page=page,
            size=size,
        )

    def get(self, dept_id: int) -> OrgDepartmentResponse:
        return OrgDepartmentResponse.model_validate(self._get_or_404(dept_id))

    # ── 写入 ──────────────────────────────────────────────────────────────────

    def create(self, payload: OrgDepartmentCreate, operator: str) -> OrgDepartmentResponse:
        self._assert_code_unique(payload.code)
        if payload.parent_id is not None:
            self._get_or_404(payload.parent_id)  # 确认父部门存在

        dept = OrgDepartment(
            name=payload.name,
            code=payload.code,
            parent_id=payload.parent_id,
            sort_order=payload.sort_order,
            is_active=payload.is_active,
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(dept)
        self.db.flush()
        return OrgDepartmentResponse.model_validate(dept)

    def update(self, dept_id: int, payload: OrgDepartmentUpdate, operator: str) -> OrgDepartmentResponse:
        dept = self._get_or_404(dept_id)

        if payload.code is not None and payload.code != dept.code:
            self._assert_code_unique(payload.code, exclude_id=dept_id)
        if payload.parent_id is not None and payload.parent_id != dept.parent_id:
            if payload.parent_id == dept_id:
                raise BusinessRuleViolationError(message="部门不能将自身设为父部门")
            self._get_or_404(payload.parent_id)
            self._assert_no_cycle(dept_id, payload.parent_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dept, field, value)
        dept.updated_by = operator
        self.db.flush()
        return OrgDepartmentResponse.model_validate(dept)

    def delete(self, dept_id: int, operator: str) -> None:
        dept = self._get_or_404(dept_id)
        # 保护：若有未删除子部门则拒绝删除
        children_count: int = self.db.execute(
            select(func.count()).where(
                OrgDepartment.parent_id == dept_id,
                OrgDepartment.is_deleted == False,
            )
        ).scalar_one()
        if children_count > 0:
            raise BusinessRuleViolationError(message="该部门下仍有子部门，请先移除子部门后再删除")
        # 保护：若有绑定用户则拒绝删除
        user_count: int = self.db.execute(
            select(func.count()).select_from(SysUser).where(
                SysUser.department_id == dept_id,
                SysUser.is_deleted == False,
            )
        ).scalar_one()
        if user_count > 0:
            raise BusinessRuleViolationError(message=f"该部门下仍有 {user_count} 名用户，请先调整用户归属后再删除")

        dept.code = _build_deleted_unique_value(dept.code, dept.id, 50)
        dept.is_deleted = True
        dept.updated_by = operator
        self.db.flush()


# ══════════════════════════════════════════════════════════════════════════════
# 二、权限服务
# ══════════════════════════════════════════════════════════════════════════════

class PermissionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, perm_id: int) -> SysPermission:
        perm = self.db.execute(
            select(SysPermission).where(
                SysPermission.id == perm_id,
                SysPermission.is_deleted == False,
            )
        ).scalar_one_or_none()
        if perm is None:
            raise ResourceNotFoundError(resource="权限", identifier=perm_id)
        return perm

    def _assert_code_unique(self, code: str, exclude_id: int | None = None) -> None:
        stmt = select(SysPermission).where(
            SysPermission.code == code,
            SysPermission.is_deleted == False,
        )
        if exclude_id is not None:
            stmt = stmt.where(SysPermission.id != exclude_id)
        if self.db.execute(stmt).scalar_one_or_none() is not None:
            raise BusinessRuleViolationError(message=f"权限编码「{code}」已存在")

    def list(
        self,
        *,
        keyword: str | None = None,
        action: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[SysPermissionResponse]:
        stmt = select(SysPermission).where(SysPermission.is_deleted == False)
        if keyword:
            stmt = stmt.where(
                or_(
                    SysPermission.name.ilike(f"%{keyword}%"),
                    SysPermission.code.ilike(f"%{keyword}%"),
                    SysPermission.resource.ilike(f"%{keyword}%"),
                )
            )
        if action:
            stmt = stmt.where(SysPermission.action == action)

        total: int = self.db.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar_one()
        rows = self.db.execute(
            stmt.order_by(SysPermission.id).offset((page - 1) * size).limit(size)
        ).scalars().all()

        return PageResult.build(
            items=[SysPermissionResponse.model_validate(r) for r in rows],
            total=total,
            page=page,
            size=size,
        )

    def get(self, perm_id: int) -> SysPermissionResponse:
        return SysPermissionResponse.model_validate(self._get_or_404(perm_id))

    def create(self, payload: SysPermissionCreate, operator: str) -> SysPermissionResponse:
        self._assert_code_unique(payload.code)
        if payload.parent_id is not None:
            self._get_or_404(payload.parent_id)

        perm = SysPermission(
            name=payload.name,
            code=payload.code,
            resource=payload.resource,
            action=payload.action,
            description=payload.description,
            parent_id=payload.parent_id,
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(perm)
        self.db.flush()
        return SysPermissionResponse.model_validate(perm)

    def update(self, perm_id: int, payload: SysPermissionUpdate, operator: str) -> SysPermissionResponse:
        perm = self._get_or_404(perm_id)
        if payload.code is not None and payload.code != perm.code:
            self._assert_code_unique(payload.code, exclude_id=perm_id)
        if payload.parent_id is not None and payload.parent_id == perm_id:
            raise BusinessRuleViolationError(message="权限节点不能将自身设为父节点")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(perm, field, value)
        perm.updated_by = operator
        self.db.flush()
        return SysPermissionResponse.model_validate(perm)

    def delete(self, perm_id: int, operator: str) -> None:
        perm = self._get_or_404(perm_id)
        child_count: int = self.db.execute(
            select(func.count()).where(
                SysPermission.parent_id == perm_id,
                SysPermission.is_deleted == False,
            )
        ).scalar_one()
        if child_count > 0:
            raise BusinessRuleViolationError(message="该权限节点下仍有子权限，请先删除子权限")

        role_count: int = self.db.execute(
            select(func.count(func.distinct(SysRole.id)))
            .select_from(SysRolePermission)
            .join(SysRole, SysRole.id == SysRolePermission.role_id)
            .where(
                SysRolePermission.permission_id == perm_id,
                SysRole.is_deleted == False,
            )
        ).scalar_one()
        if role_count > 0:
            raise BusinessRuleViolationError(message=f"该权限仍被 {role_count} 个角色使用，请先解除角色绑定后删除")

        stale_bindings = self.db.execute(
            select(SysRolePermission).where(SysRolePermission.permission_id == perm_id)
        ).scalars().all()
        for binding in stale_bindings:
            self.db.delete(binding)
        self.db.flush()

        perm.code = _build_deleted_unique_value(perm.code, perm.id, 100)
        perm.is_deleted = True
        perm.updated_by = operator
        self.db.flush()


# ══════════════════════════════════════════════════════════════════════════════
# 三、角色服务
# ══════════════════════════════════════════════════════════════════════════════

class RoleService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, role_id: int) -> SysRole:
        role = self.db.execute(
            select(SysRole).where(
                SysRole.id == role_id,
                SysRole.is_deleted == False,
            )
        ).scalar_one_or_none()
        if role is None:
            raise ResourceNotFoundError(resource="角色", identifier=role_id)
        return role

    def _assert_unique(self, *, name: str | None = None, code: str | None = None, exclude_id: int | None = None) -> None:
        if name is not None:
            stmt = select(SysRole).where(SysRole.name == name, SysRole.is_deleted == False)
            if exclude_id:
                stmt = stmt.where(SysRole.id != exclude_id)
            if self.db.execute(stmt).scalar_one_or_none():
                raise BusinessRuleViolationError(message=f"角色名称「{name}」已存在")
        if code is not None:
            stmt = select(SysRole).where(SysRole.code == code, SysRole.is_deleted == False)
            if exclude_id:
                stmt = stmt.where(SysRole.id != exclude_id)
            if self.db.execute(stmt).scalar_one_or_none():
                raise BusinessRuleViolationError(message=f"角色编码「{code}」已存在")

    def _bind_permissions(self, role: SysRole, permission_ids: list[int], operator: str) -> None:
        """全量替换角色权限（先清后写）。"""
        # 删除旧绑定
        old_bindings = self.db.execute(
            select(SysRolePermission).where(SysRolePermission.role_id == role.id)
        ).scalars().all()
        for b in old_bindings:
            self.db.delete(b)
        self.db.flush()

        # 校验所有权限 ID 存在
        for perm_id in set(permission_ids):
            perm = self.db.execute(
                select(SysPermission).where(
                    SysPermission.id == perm_id,
                    SysPermission.is_deleted == False,
                )
            ).scalar_one_or_none()
            if perm is None:
                raise ResourceNotFoundError(resource="权限", identifier=perm_id)
            self.db.add(SysRolePermission(
                role_id=role.id,
                permission_id=perm_id,
                created_by=operator,
                updated_by=operator,
            ))
        self.db.flush()

    def list(
        self,
        *,
        keyword: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[SysRoleResponse]:
        stmt = select(SysRole).where(SysRole.is_deleted == False)
        if keyword:
            stmt = stmt.where(
                or_(SysRole.name.ilike(f"%{keyword}%"), SysRole.code.ilike(f"%{keyword}%"))
            )
        if is_active is not None:
            stmt = stmt.where(SysRole.is_active == is_active)

        total: int = self.db.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar_one()
        rows = self.db.execute(
            stmt.options(selectinload(SysRole.permissions))
            .order_by(SysRole.id)
            .offset((page - 1) * size)
            .limit(size)
        ).scalars().all()

        return PageResult.build(
            items=[SysRoleResponse.model_validate(r) for r in rows],
            total=total,
            page=page,
            size=size,
        )

    def get(self, role_id: int) -> SysRoleDetail:
        role = self.db.execute(
            select(SysRole)
            .options(selectinload(SysRole.permissions))
            .where(SysRole.id == role_id, SysRole.is_deleted == False)
        ).scalar_one_or_none()
        if role is None:
            raise ResourceNotFoundError(resource="角色", identifier=role_id)
        return SysRoleDetail.model_validate(role)

    def create(self, payload: SysRoleCreate, operator: str) -> SysRoleDetail:
        self._assert_unique(name=payload.name, code=payload.code)

        role = SysRole(
            name=payload.name,
            code=payload.code,
            description=payload.description,
            is_active=payload.is_active,
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(role)
        self.db.flush()  # 获取 role.id

        if payload.permission_ids:
            self._bind_permissions(role, payload.permission_ids, operator)

        # 重新加载含关联数据
        return self.get(role.id)

    def update(self, role_id: int, payload: SysRoleUpdate, operator: str) -> SysRoleDetail:
        role = self._get_or_404(role_id)

        if payload.name is not None and payload.name != role.name:
            self._assert_unique(name=payload.name, exclude_id=role_id)
        if payload.code is not None and payload.code != role.code:
            self._assert_unique(code=payload.code, exclude_id=role_id)

        update_data = payload.model_dump(exclude_unset=True, exclude={"permission_ids"})
        for field, value in update_data.items():
            setattr(role, field, value)
        role.updated_by = operator
        self.db.flush()

        if payload.permission_ids is not None:
            self._bind_permissions(role, payload.permission_ids, operator)

        return self.get(role_id)

    def delete(self, role_id: int, operator: str) -> None:
        role = self._get_or_404(role_id)
        # 保护：若有用户绑定此角色则拒绝
        user_count: int = self.db.execute(
            select(func.count(func.distinct(SysUser.id)))
            .select_from(SysUserRole)
            .join(SysUser, SysUser.id == SysUserRole.user_id)
            .where(
                SysUserRole.role_id == role_id,
                SysUser.is_deleted == False,
            )
        ).scalar_one()
        if user_count > 0:
            raise BusinessRuleViolationError(message=f"该角色仍有 {user_count} 名用户绑定，请先解除绑定后删除")

        user_bindings = self.db.execute(
            select(SysUserRole).where(SysUserRole.role_id == role_id)
        ).scalars().all()
        for binding in user_bindings:
            self.db.delete(binding)

        permission_bindings = self.db.execute(
            select(SysRolePermission).where(SysRolePermission.role_id == role_id)
        ).scalars().all()
        for binding in permission_bindings:
            self.db.delete(binding)
        self.db.flush()

        role.name = _build_deleted_unique_value(role.name, role.id, 64)
        role.code = _build_deleted_unique_value(role.code, role.id, 50)
        role.is_deleted = True
        role.updated_by = operator
        self.db.flush()


# ══════════════════════════════════════════════════════════════════════════════
# 四、用户服务
# ══════════════════════════════════════════════════════════════════════════════

class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_or_404(self, user_id: int) -> SysUser:
        user = self.db.execute(
            select(SysUser)
            .options(
                selectinload(SysUser.department),
                selectinload(SysUser.roles),
            )
            .where(SysUser.id == user_id, SysUser.is_deleted == False)
        ).scalar_one_or_none()
        if user is None:
            raise ResourceNotFoundError(resource="用户", identifier=user_id)
        return user

    def _assert_username_unique(self, username: str, exclude_id: int | None = None) -> None:
        stmt = select(SysUser).where(SysUser.username == username, SysUser.is_deleted == False)
        if exclude_id:
            stmt = stmt.where(SysUser.id != exclude_id)
        if self.db.execute(stmt).scalar_one_or_none():
            raise BusinessRuleViolationError(message=f"用户名「{username}」已被占用")

    def _assert_email_unique(self, email: str, exclude_id: int | None = None) -> None:
        stmt = select(SysUser).where(SysUser.email == email, SysUser.is_deleted == False)
        if exclude_id:
            stmt = stmt.where(SysUser.id != exclude_id)
        if self.db.execute(stmt).scalar_one_or_none():
            raise BusinessRuleViolationError(message=f"邮箱「{email}」已被其他账号占用")

    def _bind_roles(self, user: SysUser, role_ids: list[int], operator: str) -> None:
        """全量替换用户角色（先清后写）。"""
        old_bindings = self.db.execute(
            select(SysUserRole).where(SysUserRole.user_id == user.id)
        ).scalars().all()
        for b in old_bindings:
            self.db.delete(b)
        self.db.flush()

        seen: set[int] = set()
        for role_id in role_ids:
            if role_id in seen:
                continue
            seen.add(role_id)
            role = self.db.execute(
                select(SysRole).where(SysRole.id == role_id, SysRole.is_deleted == False)
            ).scalar_one_or_none()
            if role is None:
                raise ResourceNotFoundError(resource="角色", identifier=role_id)
            self.db.add(SysUserRole(
                user_id=user.id,
                role_id=role_id,
                created_by=operator,
                updated_by=operator,
            ))
        self.db.flush()

    def list(
        self,
        *,
        keyword: str | None = None,
        is_active: bool | None = None,
        department_id: int | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[SysUserResponse]:
        stmt = select(SysUser).where(SysUser.is_deleted == False)
        if keyword:
            stmt = stmt.where(
                or_(
                    SysUser.username.ilike(f"%{keyword}%"),
                    SysUser.real_name.ilike(f"%{keyword}%"),
                    SysUser.email.ilike(f"%{keyword}%"),
                )
            )
        if is_active is not None:
            stmt = stmt.where(SysUser.is_active == is_active)
        if department_id is not None:
            stmt = stmt.where(SysUser.department_id == department_id)

        total: int = self.db.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar_one()
        rows = self.db.execute(
            stmt.order_by(SysUser.id).offset((page - 1) * size).limit(size)
        ).scalars().all()

        return PageResult.build(
            items=[SysUserResponse.model_validate(r) for r in rows],
            total=total,
            page=page,
            size=size,
        )

    def get(self, user_id: int) -> SysUserDetail:
        return SysUserDetail.model_validate(self._get_or_404(user_id))

    def create(self, payload: SysUserCreate, operator: str) -> SysUserDetail:
        self._assert_username_unique(payload.username)
        if payload.email:
            self._assert_email_unique(payload.email)

        if payload.department_id is not None:
            dept = self.db.execute(
                select(OrgDepartment).where(
                    OrgDepartment.id == payload.department_id,
                    OrgDepartment.is_deleted == False,
                )
            ).scalar_one_or_none()
            if dept is None:
                raise ResourceNotFoundError(resource="部门", identifier=payload.department_id)

        user = SysUser(
            username=payload.username,
            hashed_password=hash_password(payload.password),
            real_name=payload.real_name,
            email=payload.email,
            phone=payload.phone,
            is_active=payload.is_active,
            department_id=payload.department_id,
            created_by=operator,
            updated_by=operator,
        )
        self.db.add(user)
        self.db.flush()

        if payload.role_ids:
            self._bind_roles(user, payload.role_ids, operator)

        return self.get(user.id)

    def update(self, user_id: int, payload: SysUserUpdate, operator: str) -> SysUserDetail:
        # _get_or_404 预加载了关联，确认存在即可，后续直接查无关联版本做更新
        user_bare = self.db.execute(
            select(SysUser).where(SysUser.id == user_id, SysUser.is_deleted == False)
        ).scalar_one_or_none()
        if user_bare is None:
            raise ResourceNotFoundError(resource="用户", identifier=user_id)

        if payload.email is not None and payload.email != user_bare.email:
            self._assert_email_unique(payload.email, exclude_id=user_id)

        if payload.department_id is not None and payload.department_id != user_bare.department_id:
            dept = self.db.execute(
                select(OrgDepartment).where(
                    OrgDepartment.id == payload.department_id,
                    OrgDepartment.is_deleted == False,
                )
            ).scalar_one_or_none()
            if dept is None:
                raise ResourceNotFoundError(resource="部门", identifier=payload.department_id)

        update_data = payload.model_dump(exclude_unset=True, exclude={"role_ids"})
        for field, value in update_data.items():
            setattr(user_bare, field, value)
        user_bare.updated_by = operator
        self.db.flush()

        if payload.role_ids is not None:
            self._bind_roles(user_bare, payload.role_ids, operator)

        return self.get(user_id)

    def delete(self, user_id: int, operator: str) -> None:
        user_bare = self.db.execute(
            select(SysUser).where(SysUser.id == user_id, SysUser.is_deleted == False)
        ).scalar_one_or_none()
        if user_bare is None:
            raise ResourceNotFoundError(resource="用户", identifier=user_id)
        if str(user_bare.id) == operator:
            raise BusinessRuleViolationError(message="不能删除当前登录账号自身")

        role_bindings = self.db.execute(
            select(SysUserRole).where(SysUserRole.user_id == user_id)
        ).scalars().all()
        for binding in role_bindings:
            self.db.delete(binding)
        self.db.flush()

        user_bare.username = _build_deleted_unique_value(user_bare.username, user_bare.id, 64)
        user_bare.email = _build_deleted_unique_value(user_bare.email, user_bare.id, 128)
        user_bare.is_deleted = True
        user_bare.updated_by = operator
        self.db.flush()

    def change_password(self, user_id: int, payload: SysUserChangePassword, operator: str) -> None:
        """当前用户自助改密，需验证旧密码。"""
        user_bare = self.db.execute(
            select(SysUser).where(SysUser.id == user_id, SysUser.is_deleted == False)
        ).scalar_one_or_none()
        if user_bare is None:
            raise ResourceNotFoundError(resource="用户", identifier=user_id)

        if not verify_password(payload.old_password, user_bare.hashed_password):
            raise BusinessRuleViolationError(message="原密码不正确")

        user_bare.hashed_password = hash_password(payload.new_password)
        user_bare.updated_by = operator
        self.db.flush()

    def reset_password(self, user_id: int, new_password: str, operator: str) -> None:
        """管理员重置指定用户密码，无需验证旧密码。"""
        user_bare = self.db.execute(
            select(SysUser).where(SysUser.id == user_id, SysUser.is_deleted == False)
        ).scalar_one_or_none()
        if user_bare is None:
            raise ResourceNotFoundError(resource="用户", identifier=user_id)

        user_bare.hashed_password = hash_password(new_password)
        user_bare.updated_by = operator
        self.db.flush()


# ══════════════════════════════════════════════════════════════════════════════
# 五、审计日志服务
# ══════════════════════════════════════════════════════════════════════════════

class AuditLogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def write(
        self,
        *,
        user_id: int | None,
        username: str | None,
        action: str,
        resource_type: str | None = None,
        resource_id: Any = None,
        detail: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        写入一条审计日志。

        约定：
          - detail 传入 dict，自动序列化为 JSON 字符串存储
          - resource_id 统一转为字符串，兼容各类主键类型
          - 不 flush，由调用方的事务统一提交

        示例：
            AuditLogService(db).write(
                user_id=current_user.id,
                username=current_user.username,
                action="CREATE",
                resource_type="SysUser",
                resource_id=new_user.id,
                detail={"username": new_user.username},
                ip_address=request.client.host,
            )
        """
        log = SysAuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            detail=json.dumps(detail, ensure_ascii=False, cls=DecimalEncoder) if detail else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(log)

    def list(
        self,
        *,
        user_id: int | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        page: int = 1,
        size: int = 20,
    ) -> PageResult[SysAuditLogResponse]:
        stmt = select(SysAuditLog)

        if user_id is not None:
            stmt = stmt.where(SysAuditLog.user_id == user_id)
        if action:
            stmt = stmt.where(SysAuditLog.action == action)
        if resource_type:
            stmt = stmt.where(SysAuditLog.resource_type == resource_type)
        if start_time:
            stmt = stmt.where(SysAuditLog.created_at >= start_time)
        if end_time:
            stmt = stmt.where(SysAuditLog.created_at <= end_time)

        total: int = self.db.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar_one()
        rows = self.db.execute(
            stmt.order_by(SysAuditLog.created_at.desc()).offset((page - 1) * size).limit(size)
        ).scalars().all()

        return PageResult.build(
            items=[SysAuditLogResponse.model_validate(r) for r in rows],
            total=total,
            page=page,
            size=size,
        )
