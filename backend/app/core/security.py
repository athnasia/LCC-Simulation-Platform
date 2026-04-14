"""
安全与认证工具

职责：
  - JWT Access Token / Refresh Token 的签发与校验
  - 密码 bcrypt 哈希与验证
  - 不含任何 I/O，可被 services 层和 FastAPI Depends 安全调用
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import AuthenticationError

# ── 密码哈希 ───────────────────────────────────────────────────────────────────

_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,       # 12 轮在安全性与性能间取得合理平衡
)


def hash_password(plain_password: str) -> str:
    """将明文密码哈希为 bcrypt 密文，存入数据库。"""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与数据库存储的哈希是否匹配。"""
    return _pwd_context.verify(plain_password, hashed_password)


# ── JWT Token ──────────────────────────────────────────────────────────────────

def create_access_token(subject: str | int, extra_claims: dict[str, Any] | None = None) -> str:
    """
    签发 Access Token。

    Args:
        subject:      Token 主体标识（通常为 user_id）
        extra_claims: 附加业务字段（如 role_codes、tenant_id）

    Returns:
        JWT 字符串
    """
    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(tz=timezone.utc),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str | int) -> str:
    """
    签发 Refresh Token（有效期更长，不携带业务 claims，仅用于换取新 Access Token）。
    """
    expire = datetime.now(tz=timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(tz=timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """
    校验并解码 JWT Token。

    Args:
        token:         JWT 字符串
        expected_type: "access" 或 "refresh"，防止两种 Token 混用

    Returns:
        已验证的 payload 字典

    Raises:
        AuthenticationError: Token 无效、已过期或类型不匹配
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise AuthenticationError(message="Token 无效或已过期，请重新登录")

    if payload.get("type") != expected_type:
        raise AuthenticationError(
            message=f"Token 类型错误：期望 {expected_type}，实际 {payload.get('type')}"
        )

    return payload


def get_subject_from_token(token: str, expected_type: str = "access") -> str:
    """
    快捷方法：直接返回 Token 中的 sub（用户 ID 字符串）。

    Raises:
        AuthenticationError: Token 无效时抛出
    """
    payload = decode_token(token, expected_type=expected_type)
    sub = payload.get("sub")
    if not sub:
        raise AuthenticationError(message="Token 中缺少用户标识")
    return sub
