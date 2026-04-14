"""
统一异常体系

层次结构：
  AppBaseException                        ← 所有业务异常的基类
  ├── AuthenticationError                 ← 401 未认证
  ├── PermissionDeniedError               ← 403 无权限
  ├── ResourceNotFoundError               ← 404 资源不存在
  ├── BusinessRuleViolationError          ← 422 业务规则冲突
  └── DomainException                     ← 领域层计算异常基类
      ├── UnitConversionChainBrokenError  ← 量纲换算链路断裂（核算任务挂起）
      └── SnapshotFrozenError             ← 试图修改已冻结快照

main.py 中已为 AppBaseException 和 UnitConversionChainBrokenError
注册了全局 exception_handler，其余子类通过继承自动命中基类处理器。
"""

from __future__ import annotations

from typing import Any


# ── 基类 ───────────────────────────────────────────────────────────────────────

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


# ── 通用业务异常 ───────────────────────────────────────────────────────────────

class AuthenticationError(AppBaseException):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"
    message = "认证失败，请重新登录"


class PermissionDeniedError(AppBaseException):
    status_code = 403
    error_code = "PERMISSION_DENIED"
    message = "您没有执行此操作的权限"


class ResourceNotFoundError(AppBaseException):
    """
    用法示例：
        raise ResourceNotFoundError(resource="材料", identifier="MAT-001")
    """
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"
    message = "请求的资源不存在"

    def __init__(self, resource: str = "", identifier: Any = "") -> None:
        detail = {"resource": resource, "identifier": str(identifier)}
        super().__init__(
            message=f"{resource}「{identifier}」不存在" if resource else self.__class__.message,
            detail=detail,
        )


class BusinessRuleViolationError(AppBaseException):
    status_code = 422
    error_code = "BUSINESS_RULE_VIOLATION"
    message = "操作违反业务规则"


# ── 领域层计算异常 ─────────────────────────────────────────────────────────────

class DomainException(AppBaseException):
    """领域规则与计算逻辑的异常基类，默认 HTTP 422。"""
    status_code = 422
    error_code = "DOMAIN_RULE_ERROR"
    message = "领域规则校验失败"


class UnitConversionChainBrokenError(DomainException):
    """
    量纲换算链路断裂异常。

    当系统无法在以下路径中找到有效换算规则时抛出，并立即挂起核算任务：
      1. 全局同量纲标准换算表（md_unit_conversion）
      2. 物料专属跨维度换算表（md_material_conversion）
      3. 物料 JSON 属性中的隐含变量（如 density、linear_density）

    前端将收到以下 detail 结构，用于精准定位缺失配置：
    {
        "material_code":     "MAT-001",          # 涉事物料编码
        "material_name":     "304不锈钢管",       # 涉事物料名称（可选，方便人工定位）
        "pricing_unit":      "件",               # 财务计价单位
        "consumption_unit":  "kg",              # 工艺消耗单位
        "broken_at":         "material_conversion",  # 断裂位置
        "suggestion":        "..."              # 引导修复的提示语
    }

    broken_at 可选值：
        "global_unit_conversion"   - 全局换算表中无此量纲规则
        "material_conversion"      - 物料专属换算表中无此换算比
        "json_implicit_variable"   - JSON 属性中找不到隐含变量（如 density）
    """
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
    """
    试图修改已冻结的仿真/成本快照时抛出。
    快照一旦冻结（状态为 FROZEN），其输入数据不允许更新，以保证历史结果可重现。
    """
    status_code = 409
    error_code = "SNAPSHOT_FROZEN"
    message = "快照已冻结，不允许修改，如需重新计算请创建新任务"


# ── 内部工具函数 ───────────────────────────────────────────────────────────────

def _build_suggestion(
    broken_at: str,
    material_code: str,
    pricing_unit: str,
    consumption_unit: str,
    missing_variable: str,
) -> str:
    """根据断裂位置生成面向用户的修复引导语。"""
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
