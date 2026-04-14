"""
认证路由层

端点：
  POST /api/v1/auth/login    — 用户登录，返回 Token 对
  POST /api/v1/auth/refresh  — 用 Refresh Token 换发新 Access Token
  GET  /api/v1/auth/me       — 获取当前登录用户详情（含部门与角色）

路由层职责边界：
  - 接收并校验请求参数（Pydantic 自动完成）
  - 调用 AuthService 执行业务逻辑
  - 封装响应对象返回给调用方
  - 严禁在此处编写 SQL、ORM 操作或业务规则
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db
from app.models.system import SysUser
from app.schemas.system import (
    LoginRequest,
    RefreshTokenRequest,
    SysUserDetail,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


# ── POST /login ────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="用户登录",
    description=(
        "接收用户名与密码，校验通过后同时签发 Access Token（8小时）与 "
        "Refresh Token（7天）。密码错误与用户不存在返回相同提示，防止枚举攻击。"
    ),
)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    user = service.authenticate_user(credentials.username, credentials.password)
    return service.create_tokens(user)


# ── POST /refresh ──────────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="刷新 Access Token",
    description=(
        "传入有效的 Refresh Token，换发新的 Access Token。"
        "Refresh Token 本身不续期，到期后需重新登录。"
    ),
)
def refresh_token(
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    return service.refresh_access_token(body.refresh_token)


# ── GET /me ────────────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=SysUserDetail,
    status_code=status.HTTP_200_OK,
    summary="获取当前登录用户信息",
    description=(
        "依赖 Bearer Token 认证。返回当前用户完整档案，"
        "包含所属部门（Brief）与已绑定角色列表（Brief）。"
    ),
)
def get_me(
    current_user: SysUser = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SysUser:
    """
    实现说明：

    1. `get_current_active_user` 负责 Token 解析与账号启用状态校验，
       若失败则在依赖注入阶段直接返回 401/403，路由函数不会执行。

    2. FastAPI 在同一请求内缓存 Depends(get_db)，`get_current_active_user`
       与本函数共享同一 Session，不会重复创建连接。

    3. 调用 `get_user_detail` 通过 selectinload 预加载 department 与 roles，
       确保 Pydantic 序列化时关联数据已在内存中，不触发 Session 关闭后的懒加载。
    """
    service = AuthService(db)
    return service.get_user_detail(current_user.id)
