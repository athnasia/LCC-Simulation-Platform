from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import Field
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db, require_permission
from app.models.system import SysUser
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
    SysUserAdminResetPassword,
    SysUserChangePassword,
    SysUserCreate,
    SysUserDetail,
    SysUserResponse,
    SysUserUpdate,
)
from app.services.system_service import (
    AuditLogService,
    DepartmentService,
    PermissionService,
    RoleService,
    UserService,
)

router = APIRouter()
def _commit_write(db: Session) -> None:
    db.commit()


@router.get(
    "/departments",
    response_model=PageResult[OrgDepartmentResponse],
    summary="List departments",
    description="Filter by keyword and active status with pagination.",
)
def list_departments(
    keyword: str | None = Query(None, description="Department name or code keyword"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=500, description="Page size"),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/system/departments", "read")),
) -> PageResult[OrgDepartmentResponse]:
    return DepartmentService(db).list(keyword=keyword, is_active=is_active, page=page, size=size)


@router.post(
    "/departments",
    response_model=OrgDepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create department",
)
def create_department(
    payload: OrgDepartmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/departments", "write")),
) -> OrgDepartmentResponse:
    operator = str(current_user.id)
    result = DepartmentService(db).create(payload, operator)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="OrgDepartment",
        resource_id=result.id,
        detail={"name": result.name, "code": result.code},
        ip_address=request.client.host if request.client else None,
    )
    _commit_write(db)
    return result


@router.get(
    "/departments/{dept_id}",
    response_model=OrgDepartmentResponse,
    summary="Get department",
)
def get_department(
    dept_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/system/departments", "read")),
) -> OrgDepartmentResponse:
    return DepartmentService(db).get(dept_id)


@router.put(
    "/departments/{dept_id}",
    response_model=OrgDepartmentResponse,
    summary="Update department",
)
def update_department(
    dept_id: int,
    payload: OrgDepartmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/departments", "write")),
) -> OrgDepartmentResponse:
    operator = str(current_user.id)
    result = DepartmentService(db).update(dept_id, payload, operator)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="OrgDepartment",
        resource_id=dept_id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    _commit_write(db)
    return result


@router.delete(
    "/departments/{dept_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete department",
)
def delete_department(
    dept_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/departments", "delete")),
) -> None:
    operator = str(current_user.id)
    DepartmentService(db).delete(dept_id, operator)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="OrgDepartment",
        resource_id=dept_id,
        ip_address=request.client.host if request.client else None,
    )
    _commit_write(db)


@router.get(
    "/permissions",
    response_model=PageResult[SysPermissionResponse],
    summary="List permissions",
)
def list_permissions(
    keyword: str | None = Query(None, description="Permission name, code, or resource path keyword"),
    action: str | None = Query(None, description="Action filter: read/write/delete/admin"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/system/permissions", "read")),
) -> PageResult[SysPermissionResponse]:
    return PermissionService(db).list(keyword=keyword, action=action, page=page, size=size)


@router.post(
    "/permissions",
    response_model=SysPermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create permission",
)
def create_permission(
    payload: SysPermissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/permissions", "write")),
) -> SysPermissionResponse:
    operator = str(current_user.id)
    result = PermissionService(db).create(payload, operator)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="SysPermission",
        resource_id=result.id,
        detail={"code": result.code, "action": result.action},
        ip_address=request.client.host if request.client else None,
    )
    _commit_write(db)
    return result


@router.get(
    "/permissions/{perm_id}",
    response_model=SysPermissionResponse,
    summary="Get permission",
)
def get_permission(
    perm_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/system/permissions", "read")),
) -> SysPermissionResponse:
    return PermissionService(db).get(perm_id)


@router.put(
    "/permissions/{perm_id}",
    response_model=SysPermissionResponse,
    summary="Update permission",
)
def update_permission(
    perm_id: int,
    payload: SysPermissionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/permissions", "write")),
) -> SysPermissionResponse:
    operator = str(current_user.id)
    result = PermissionService(db).update(perm_id, payload, operator)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="SysPermission",
        resource_id=perm_id,
        detail=payload.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
    )
    _commit_write(db)
    return result


@router.delete(
    "/permissions/{perm_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete permission",
)
def delete_permission(
    perm_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/permissions", "delete")),
) -> None:
    PermissionService(db).delete(perm_id, str(current_user.id))
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="SysPermission",
        resource_id=perm_id,
        ip_address=request.client.host if request.client else None,
    )
    _commit_write(db)


@router.get(
    "/roles",
    response_model=PageResult[SysRoleResponse],
    summary="List roles",
)
def list_roles(
    keyword: str | None = Query(None, description="Role name or code keyword"),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/system/roles", "read")),
) -> PageResult[SysRoleResponse]:
    return RoleService(db).list(keyword=keyword, is_active=is_active, page=page, size=size)


@router.post(
    "/roles",
    response_model=SysRoleDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create role",
)
def create_role(
    payload: SysRoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/roles", "write")),
) -> SysRoleDetail:
    operator = str(current_user.id)
    result = RoleService(db).create(payload, operator)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="SysRole",
        resource_id=result.id,
        detail={"name": result.name, "code": result.code},
        ip_address=request.client.host if request.client else None,
    )
    _commit_write(db)
    return result


@router.get(
    "/roles/{role_id}",
    response_model=SysRoleDetail,
    summary="Get role",
)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/system/roles", "read")),
) -> SysRoleDetail:
    return RoleService(db).get(role_id)


@router.put(
    "/roles/{role_id}",
    response_model=SysRoleDetail,
    summary="Update role",
    description="permission_ids replaces the full permission binding set when provided.",
)
def update_role(
    role_id: int,
    payload: SysRoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/roles", "write")),
) -> SysRoleDetail:
    operator = str(current_user.id)
    result = RoleService(db).update(role_id, payload, operator)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="SysRole",
        resource_id=role_id,
        detail=payload.model_dump(exclude_unset=True, exclude={"permission_ids"}),
        ip_address=request.client.host if request.client else None,
    )
    _commit_write(db)
    return result


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete role",
)
def delete_role(
    role_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/roles", "delete")),
) -> None:
    RoleService(db).delete(role_id, str(current_user.id))
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="SysRole",
        resource_id=role_id,
        ip_address=request.client.host if request.client else None,
    )
    _commit_write(db)


@router.get(
    "/users",
    response_model=PageResult[SysUserResponse],
    summary="List users",
)
def list_users(
    keyword: str | None = Query(None, description="Username, real name, or phone keyword"),
    is_active: bool | None = Query(None),
    department_id: int | None = Query(None, description="Department ID"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/system/users", "read")),
) -> PageResult[SysUserResponse]:
    return UserService(db).list(
        keyword=keyword,
        is_active=is_active,
        department_id=department_id,
        page=page,
        size=size,
    )


@router.post(
    "/users",
    response_model=SysUserDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
)
def create_user(
    payload: SysUserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/users", "write")),
) -> SysUserDetail:
    operator = str(current_user.id)
    result = UserService(db).create(payload, operator)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CREATE",
        resource_type="SysUser",
        resource_id=result.id,
        detail={"username": result.username, "real_name": result.real_name},
        ip_address=request.client.host if request.client else None,
    )
    _commit_write(db)
    return result


@router.get(
    "/users/{user_id}",
    response_model=SysUserDetail,
    summary="Get user",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/system/users", "read")),
) -> SysUserDetail:
    return UserService(db).get(user_id)


@router.put(
    "/users/{user_id}",
    response_model=SysUserDetail,
    summary="Update user",
    description="role_ids replaces the full role binding set when provided.",
)
def update_user(
    user_id: int,
    payload: SysUserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/users", "write")),
) -> SysUserDetail:
    operator = str(current_user.id)
    result = UserService(db).update(user_id, payload, operator)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE",
        resource_type="SysUser",
        resource_id=user_id,
        detail=payload.model_dump(exclude_unset=True, exclude={"role_ids"}),
        ip_address=request.client.host if request.client else None,
    )
    _commit_write(db)
    return result


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/users", "delete")),
) -> None:
    UserService(db).delete(user_id, str(current_user.id))
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="DELETE",
        resource_type="SysUser",
        resource_id=user_id,
        ip_address=request.client.host if request.client else None,
    )
    _commit_write(db)


@router.post(
    "/users/{user_id}/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset user password",
    description="Admin resets a user password directly.",
)
def reset_user_password(
    user_id: int,
    body: SysUserAdminResetPassword,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/system/users", "admin")),
) -> None:
    UserService(db).reset_password(user_id, body.new_password, str(current_user.id))
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="RESET_PASSWORD",
        resource_type="SysUser",
        resource_id=user_id,
        ip_address=request.client.host if request.client else None,
    )
    _commit_write(db)


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change current user password",
    description="Require current password and matching new password confirmation.",
)
def change_my_password(
    payload: SysUserChangePassword,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_active_user),
) -> None:
    operator = str(current_user.id)
    UserService(db).change_password(current_user.id, payload, operator)
    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="CHANGE_PASSWORD",
        resource_type="SysUser",
        resource_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    _commit_write(db)


@router.get(
    "/audit-logs",
    response_model=PageResult[SysAuditLogResponse],
    summary="List audit logs",
    description="Filter by user, action, resource type, and time range with pagination.",
)
def list_audit_logs(
    user_id: int | None = Query(None, description="Operator user ID"),
    action: str | None = Query(None, description="Action such as CREATE, UPDATE, DELETE"),
    resource_type: str | None = Query(None, description="Resource type such as SysUser or SysRole"),
    start_time: datetime | None = Query(None, description="Start time in ISO 8601"),
    end_time: datetime | None = Query(None, description="End time in ISO 8601"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/system/audit-logs", "read")),
) -> PageResult[SysAuditLogResponse]:
    return AuditLogService(db).list(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        start_time=start_time,
        end_time=end_time,
        page=page,
        size=size,
    )