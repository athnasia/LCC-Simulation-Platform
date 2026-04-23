"""
统一异常体系

层次结构：
  AppBaseException                        ← 所有业务异常的基类
  ├── AuthenticationError                 ← 401 未认证
  ├── PermissionDeniedError               ← 403 无权限
  ├── ResourceNotFoundError               ← 404 资源不存在
  ├── ConflictError                       ← 409 资源冲突
  ├── BusinessRuleViolationError          ← 422 业务规则冲突
  ├── RateLimitExceededError              ← 429 请求频率超限
  └── DomainException                     ← 领域层计算异常基类
      ├── UnitConversionChainBrokenError  ← 量纲换算链路断裂（核算任务挂起）
      ├── SnapshotFrozenError             ← 试图修改已冻结快照
      ├── CostingEngineError              ← 成本核算引擎异常
      └── SimulationError                 ← LCC 仿真异常

main.py 中已为 AppBaseException 和其他异常类型
注册了全局 exception_handler，确保所有异常都有统一的响应格式。
"""

from __future__ import annotations

from typing import Any


class AppBaseException(Exception):
    """
    所有业务异常的基类。

    Attributes:
        status_code:  HTTP 状态码
        error_code:   前端可枚举的业务错误码（SCREAMING_SNAKE_CASE）
        message:      面向用户的中文提示
        detail:       面向开发者/前端的结构化附加信息
    """
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "服务器内部错误"

    def __init__(
        self,
        message: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.detail = detail or {}
        super().__init__(self.message)


class AuthenticationError(AppBaseException):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"
    message = "认证失败，请重新登录"


class TokenExpiredError(AppBaseException):
    status_code = 401
    error_code = "TOKEN_EXPIRED"
    message = "登录已过期，请重新登录"


class PermissionDeniedError(AppBaseException):
    status_code = 403
    error_code = "PERMISSION_DENIED"
    message = "您没有执行此操作的权限"


class ResourceNotFoundError(AppBaseException):
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"
    message = "请求的资源不存在"

    def __init__(self, resource: str = "", identifier: Any = "") -> None:
        detail = {"resource": resource, "identifier": str(identifier)}
        super().__init__(
            message=f"{resource}「{identifier}」不存在" if resource else self.__class__.message,
            detail=detail,
        )


class ConflictError(AppBaseException):
    status_code = 409
    error_code = "RESOURCE_CONFLICT"
    message = "资源冲突"

    def __init__(
        self,
        message: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)


class BusinessRuleViolationError(AppBaseException):
    status_code = 422
    error_code = "BUSINESS_RULE_VIOLATION"
    message = "操作违反业务规则"

    def __init__(
        self,
        message: str | None = None,
        detail: dict[str, Any] | None = None,
        error_code: str | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.detail = detail or {}
        if error_code:
            self.error_code = error_code
        super().__init__(message=self.message, detail=self.detail)


class RateLimitExceededError(AppBaseException):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "请求频率超限，请稍后重试"

    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            message=self.__class__.message,
            detail={"retry_after": retry_after},
        )


class DomainException(AppBaseException):
    status_code = 422
    error_code = "DOMAIN_RULE_ERROR"
    message = "领域规则校验失败"


class UnitConversionChainBrokenError(DomainException):
    status_code = 422
    error_code = "UNIT_CONVERSION_CHAIN_BROKEN"
    message = "单位换算链路断裂，核算任务已挂起，请补充换算规则后重试"

    def __init__(
        self,
        material_code: str,
        pricing_unit: str,
        consumption_unit: str,
        broken_at: str,
        material_name: str = "",
        missing_variable: str = "",
    ) -> None:
        suggestion = _build_suggestion(
            broken_at=broken_at,
            material_code=material_code,
            pricing_unit=pricing_unit,
            consumption_unit=consumption_unit,
            missing_variable=missing_variable,
        )
        detail: dict[str, Any] = {
            "material_code": material_code,
            "material_name": material_name,
            "pricing_unit": pricing_unit,
            "consumption_unit": consumption_unit,
            "broken_at": broken_at,
            "suggestion": suggestion,
        }
        if missing_variable:
            detail["missing_variable"] = missing_variable

        super().__init__(message=self.__class__.message, detail=detail)


class SnapshotFrozenError(DomainException):
    status_code = 409
    error_code = "SNAPSHOT_FROZEN"
    message = "快照已冻结，不允许修改，如需重新计算请创建新任务"


class CostingEngineError(DomainException):
    status_code = 422
    error_code = "COSTING_ENGINE_ERROR"
    message = "成本核算引擎执行异常"

    def __init__(
        self,
        message: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)


class SimulationError(DomainException):
    status_code = 422
    error_code = "SIMULATION_ERROR"
    message = "LCC 仿真执行异常"

    def __init__(
        self,
        message: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message=message, detail=detail)


class DuplicateResourceError(ConflictError):
    error_code = "DUPLICATE_RESOURCE"
    message = "资源已存在"

    def __init__(self, resource: str = "", field: str = "", value: str = "") -> None:
        detail = {"resource": resource, "field": field, "value": value}
        super().__init__(
            message=f"{resource}的{field}「{value}」已存在" if resource else self.__class__.message,
            detail=detail,
        )


class ValidationError(BusinessRuleViolationError):
    error_code = "VALIDATION_ERROR"
    message = "数据验证失败"

    def __init__(
        self,
        message: str | None = None,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message or self.__class__.message,
            detail={"errors": errors or []},
        )


def _build_suggestion(
    broken_at: str,
    material_code: str,
    pricing_unit: str,
    consumption_unit: str,
    missing_variable: str,
) -> str:
    if broken_at == "global_unit_conversion":
        return (
            f"量纲「{pricing_unit}」与「{consumption_unit}」之间不存在全局换算规则，"
            f"请在【主数据 → 全局单位换算】中补充对应量纲的标准换算率。"
        )
    if broken_at == "material_conversion":
        return (
            f"物料「{material_code}」的计价单位「{pricing_unit}」与消耗单位「{consumption_unit}」"
            f"量纲不同，且未配置物料专属换算比，"
            f"请在【主数据 → 柔性材料台账 → 专属换算】中为该物料添加换算规则。"
        )
    if broken_at == "json_implicit_variable":
        return (
            f"物料「{material_code}」缺少用于跨维度换算的隐含属性变量"
            f"「{missing_variable or '未知'}」（如 density / linear_density），"
            f"请在【主数据 → 柔性材料台账 → 动态属性】中补充该变量的值。"
        )
    return (
        f"物料「{material_code}」的单位换算链路在未知位置断裂，"
        f"请检查计价单位「{pricing_unit}」与消耗单位「{consumption_unit}」的完整换算路径。"
    )
