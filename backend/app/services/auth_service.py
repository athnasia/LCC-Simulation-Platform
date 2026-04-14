"""
认证业务服务层

职责：
  - authenticate_user  : 校验用户名+密码，含防时序攻击保护
  - create_tokens      : 同时签发 Access Token 与 Refresh Token
  - refresh_access_token: 验证 Refresh Token，换发新 Access Token
  - get_user_detail    : 按 ID 查询用户并预加载部门与角色（供 /me 使用）

本层严格遵守单向依赖：Service → Repository/ORM，不包含任何路由层逻辑。
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ResourceNotFoundError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_subject_from_token,
    hash_password,
    verify_password,
)
from app.models.system import SysRole, SysUser
from app.schemas.system import SysUserDetail, TokenResponse

# ── 防时序攻击哑元哈希 ─────────────────────────────────────────────────────────
# 当查询不到用户时，依然执行一次 bcrypt 校验，使响应时间与"密码错误"分支一致，
# 防止攻击者通过响应时间差枚举有效用户名。
# 模块加载时计算一次，后续复用。
_TIMING_GUARD_HASH: str = hash_password("__lcc_timing_guard_placeholder__")


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── 认证 ────────────────────────────────────────────────────────────────────

    def authenticate_user(self, username: str, password: str) -> SysUser:
        """
        校验用户名和密码，返回通过认证的用户对象。

        安全策略：
          1. 无论用户是否存在都执行 bcrypt 校验，防止时序攻击。
          2. 用户不存在与密码错误返回相同提示，防止用户名枚举。
          3. 仅在密码验证通过后，才判断账号启用状态，避免信息泄露。

        Raises:
            AuthenticationError: 用户名/密码不正确，或账号已禁用
        """
        user: SysUser | None = self.db.execute(
            select(SysUser).where(
                SysUser.username == username,
                SysUser.is_deleted == False,
            )
        ).scalar_one_or_none()

        # 用户不存在时使用哑元哈希保持 bcrypt 时间消耗，随后统一抛出
        target_hash = user.hashed_password if user is not None else _TIMING_GUARD_HASH
        password_valid = verify_password(password, target_hash)

        if user is None or not password_valid:
            raise AuthenticationError(message="用户名或密码错误")

        # 密码验证通过后，再检查账号启用状态（此处区分提示信息是安全的）
        if not user.is_active:
            raise AuthenticationError(message="账号已被禁用，请联系管理员")

        return user

    # ── Token 签发 ──────────────────────────────────────────────────────────────

    def create_tokens(self, user: SysUser) -> TokenResponse:
        """
        同时签发 Access Token 与 Refresh Token。

        Access Token 附加 Claims（用于中间件快速鉴权，减少查库次数）：
          - username   : 显示名称
          - role_codes : 角色编码列表
        """
        # 若 roles 关系尚未加载，此处会触发懒加载；
        # 如果 Session 已关闭，由调用方确保先行加载（login 流程 Session 仍开放）
        role_codes: list[str] = [r.code for r in user.roles] if user.roles else []

        access_token = create_access_token(
            subject=user.id,
            extra_claims={
                "username": user.username,
                "role_codes": role_codes,
            },
        )
        refresh_token = create_refresh_token(subject=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        验证 Refresh Token 合法性，换发新的 Access Token。
        Refresh Token 本身不轮换（若需要 Refresh Token 轮换，可在此扩展）。

        Raises:
            AuthenticationError: Token 无效、过期或对应用户不存在/已禁用
        """
        # decode_token 内部已校验 type="refresh" 及过期
        user_id_str = get_subject_from_token(refresh_token, expected_type="refresh")

        user: SysUser | None = self.db.execute(
            select(SysUser)
            .where(
                SysUser.id == int(user_id_str),
                SysUser.is_deleted == False,
            )
            .options(selectinload(SysUser.roles))
        ).scalar_one_or_none()

        if user is None:
            raise AuthenticationError(message="Token 对应的用户不存在或已被删除")
        if not user.is_active:
            raise AuthenticationError(message="账号已被禁用，请使用新账号重新登录")

        return self.create_tokens(user)

    # ── 用户详情（含关联预加载）──────────────────────────────────────────────────

    def get_user_detail(self, user_id: int) -> SysUserDetail:
        """
        查询用户并预加载 department 与 roles 关联，供 /me 接口序列化使用。

        使用 selectinload 策略（而非 joinedload）：
          - 避免因多对多 JOIN 产生笛卡尔积膨胀
          - 确保关联数据在 Session 关闭前已完全加载到内存，
            Pydantic 序列化时不会触发额外懒加载

        Raises:
            ResourceNotFoundError: 用户不存在或已逻辑删除
        """
        user: SysUser | None = self.db.execute(
            select(SysUser)
            .where(
                SysUser.id == user_id,
                SysUser.is_deleted == False,
            )
            .options(
                selectinload(SysUser.department),
                selectinload(SysUser.roles).selectinload(SysRole.permissions),
            )
        ).scalar_one_or_none()

        if user is None:
            raise ResourceNotFoundError(resource="用户", identifier=user_id)

        detail = SysUserDetail.model_validate(user)
        detail.permission_scopes = sorted(
            {
                f"{permission.resource}:{permission.action}"
                for role in user.roles
                if role.is_active
                for permission in role.permissions
                if not permission.is_deleted
            }
        )
        return detail
