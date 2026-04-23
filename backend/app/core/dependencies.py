"""
FastAPI 公共依赖注入

职责：
  - get_db：提供 SQLAlchemy Session，通过 yield 保证 Session 生命周期与请求一致
  - get_current_user：从 Authorization Bearer Token 中解析当前用户，注入路由层
  - get_current_active_user：在 get_current_user 基础上额外校验账号启用状态
"""

from typing import Callable, Generator

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import SessionLocal
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import get_subject_from_token


# ── 数据库 Session ─────────────────────────────────────────────────────────────

def get_db() -> Generator[Session, None, None]:
    """
    为每个请求分配独立的 SQLAlchemy Session。

    生命周期：
      1. 路由函数执行前：从连接池取出连接，开启 Session
      2. 路由函数执行中：通过 yield 将 Session 注入
      3. 路由函数执行后（含异常）：
         - 正常：由 Router 层负责 commit（符合 AGENTS.md 规范）
         - 异常：rollback 回滚，再向上抛出，由全局 exception_handler 处理
         - finally：无论如何关闭 Session，归还连接到池

    使用方式：
        @router.get("/")
        def list_items(db: Session = Depends(get_db)):
            ...

        @router.post("/")
        def create_item(db: Session = Depends(get_db)):
            ...
            db.commit()  # Router 层负责提交
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── 当前用户解析 ───────────────────────────────────────────────────────────────

def _extract_bearer_token(authorization: str | None) -> str:
    """从 Authorization 请求头中提取 Bearer Token 字符串。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError(message="缺少或格式错误的 Authorization 请求头")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise AuthenticationError(message="Authorization Token 不能为空")
    return token


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """
    解析 Bearer Token，返回数据库中对应的用户 ORM 对象。

    此处使用延迟导入 SysUser model，避免在基础设施层直接依赖业务 ORM，
    形成单向依赖：domain → infrastructure，而非反向。

    Raises:
        AuthenticationError: Token 无效或用户不存在
    """
    from app.models.system import SysUser  # 延迟导入，避免循环依赖

    token = _extract_bearer_token(authorization)
    user_id = get_subject_from_token(token, expected_type="access")

    user = db.execute(
        select(SysUser).where(
            SysUser.id == int(user_id),
            SysUser.is_deleted == False,
        )
    ).scalar_one_or_none()
    if user is None:
        raise AuthenticationError(message="用户不存在或已被删除")
    return user


def get_current_active_user(
    current_user=Depends(get_current_user),
):
    """
    在 get_current_user 基础上，额外校验账号是否处于启用状态。

    Raises:
        PermissionDeniedError: 账号已禁用
    """
    if not current_user.is_active:
        raise PermissionDeniedError(message="账号已被禁用，请联系管理员")
    return current_user


def require_permission(resource: str, action: str) -> Callable:
    allowed_actions = {
        "read": {"read", "write", "delete", "admin"},
        "write": {"write", "admin"},
        "delete": {"delete", "admin"},
        "admin": {"admin"},
    }
    expected_actions = allowed_actions.get(action, {action})

    def checker(
        current_user=Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ):
        from app.models.system import SysRole, SysUser

        user = db.execute(
            select(SysUser)
            .options(selectinload(SysUser.roles).selectinload(SysRole.permissions))
            .where(
                SysUser.id == current_user.id,
                SysUser.is_deleted == False,
            )
        ).scalar_one_or_none()

        if user is None:
            raise AuthenticationError(message="用户不存在或已被删除")

        role_codes = {role.code for role in user.roles if role.is_active and not role.is_deleted}
        if "SUPER_ADMIN" in role_codes:
            return user

        for role in user.roles:
            if not role.is_active or role.is_deleted:
                continue
            for permission in role.permissions:
                if permission.is_deleted:
                    continue
                if permission.resource == resource and permission.action in expected_actions:
                    return user

        raise PermissionDeniedError(message=f"缺少权限：{resource}#{action}")

    return checker
