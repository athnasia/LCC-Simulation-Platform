"""
工业互联网平台 —— 基于数字孪生的成本建模与仿真优化系统
FastAPI 应用入口

职责：
    - 创建 FastAPI 实例
    - 注册全部领域路由（/api/v1/...）
    - 挂载全局中间件（CORS、请求日志）
    - 注册统一异常处理器
    - 管理应用启动 / 关闭的资源生命周期
"""

import asyncio
import logging
import sys
import traceback

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import redis.exceptions as redis_exceptions

from app.core.config import settings
from app.core.database import engine, init_db
from app.core.exceptions import (
    AppBaseException,
    AuthenticationError,
    PermissionDeniedError,
    ResourceNotFoundError,
    ConflictError,
    BusinessRuleViolationError,
    RateLimitExceededError,
    DomainException,
    UnitConversionChainBrokenError,
    SnapshotFrozenError,
    CostingEngineError,
    SimulationError,
    DuplicateResourceError,
    ValidationError,
)

from app.api.v1.routers import (
    auth,
    system,
    system_dictionary,
    dict_templates,
    materials,
    equipments,
    labor,
    processes,
    energy,
    engineering,
    costing,
    simulation,
    dashboard,
    iot,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield
    await asyncio.to_thread(engine.dispose)


app = FastAPI(
    title="工业互联网 LCC 成本建模与仿真优化平台",
    description=(
        "基于数字孪生的全生命周期成本（LCC）建模、仿真与优化系统。\n\n"
        "核心业务流：主数据定义 → 工程建模 → 成本核算 → LCC 仿真推演。"
    ),
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _log_exception(request: Request, exc: Exception, level: int = logging.ERROR) -> None:
    exc_info = sys.exc_info()
    logger.log(
        level,
        f"Exception occurred: {type(exc).__name__}: {exc}\n"
        f"Request: {request.method} {request.url}\n"
        f"Client: {request.client.host if request.client else 'unknown'}",
        exc_info=exc_info,
    )


@app.exception_handler(AppBaseException)
async def app_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
    _log_exception(request, exc, level=logging.WARNING)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    _log_exception(request, exc, level=logging.WARNING)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(PermissionDeniedError)
async def permission_exception_handler(request: Request, exc: PermissionDeniedError) -> JSONResponse:
    _log_exception(request, exc, level=logging.WARNING)
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(ResourceNotFoundError)
async def not_found_exception_handler(request: Request, exc: ResourceNotFoundError) -> JSONResponse:
    _log_exception(request, exc, level=logging.INFO)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(ConflictError)
async def conflict_exception_handler(request: Request, exc: ConflictError) -> JSONResponse:
    _log_exception(request, exc, level=logging.WARNING)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(DuplicateResourceError)
async def duplicate_resource_exception_handler(request: Request, exc: DuplicateResourceError) -> JSONResponse:
    _log_exception(request, exc, level=logging.WARNING)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(BusinessRuleViolationError)
async def business_rule_exception_handler(request: Request, exc: BusinessRuleViolationError) -> JSONResponse:
    _log_exception(request, exc, level=logging.WARNING)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(RateLimitExceededError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceededError) -> JSONResponse:
    _log_exception(request, exc, level=logging.WARNING)
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
        headers={"Retry-After": str(exc.detail.get("retry_after", 60))},
    )


@app.exception_handler(UnitConversionChainBrokenError)
async def unit_conversion_exception_handler(
    request: Request, exc: UnitConversionChainBrokenError
) -> JSONResponse:
    _log_exception(request, exc, level=logging.ERROR)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(SnapshotFrozenError)
async def snapshot_frozen_exception_handler(request: Request, exc: SnapshotFrozenError) -> JSONResponse:
    _log_exception(request, exc, level=logging.WARNING)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(CostingEngineError)
async def costing_engine_exception_handler(request: Request, exc: CostingEngineError) -> JSONResponse:
    _log_exception(request, exc, level=logging.ERROR)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(SimulationError)
async def simulation_exception_handler(request: Request, exc: SimulationError) -> JSONResponse:
    _log_exception(request, exc, level=logging.ERROR)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    logger.warning(
        f"Validation error: {request.method} {request.url}\n"
        f"Errors: {errors}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "message": "请求参数验证失败",
            "detail": {"errors": errors},
        },
    )


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    
    logger.warning(
        f"Pydantic validation error: {request.method} {request.url}\n"
        f"Errors: {errors}"
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "message": "数据验证失败",
            "detail": {"errors": errors},
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    _log_exception(request, exc, level=logging.WARNING)
    
    error_message = "数据库完整性约束冲突"
    detail = {}
    
    if hasattr(exc, "orig") and exc.orig:
        orig_msg = str(exc.orig)
        if "Duplicate entry" in orig_msg or "UNIQUE constraint failed" in orig_msg:
            error_message = "资源已存在，唯一键冲突"
            detail["constraint"] = "unique"
        elif "foreign key constraint" in orig_msg.lower():
            error_message = "关联资源不存在"
            detail["constraint"] = "foreign_key"
        elif "cannot be null" in orig_msg.lower() or "NOT NULL constraint" in orig_msg:
            error_message = "必填字段不能为空"
            detail["constraint"] = "not_null"
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "code": "INTEGRITY_ERROR",
            "message": error_message,
            "detail": detail,
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    _log_exception(request, exc, level=logging.ERROR)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "DATABASE_ERROR",
            "message": "数据库操作异常",
            "detail": {"error_type": type(exc).__name__},
        },
    )


@app.exception_handler(redis_exceptions.RedisError)
async def redis_exception_handler(request: Request, exc: redis_exceptions.RedisError) -> JSONResponse:
    _log_exception(request, exc, level=logging.ERROR)
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "code": "REDIS_ERROR",
            "message": "缓存服务暂时不可用",
            "detail": {"error_type": type(exc).__name__},
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _log_exception(request, exc, level=logging.CRITICAL)
    
    if settings.APP_DEBUG:
        detail = {
            "error_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        }
    else:
        detail = {"error_type": type(exc).__name__}
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误，请稍后重试",
            "detail": detail,
        },
    )


_API_PREFIX = "/api/v1"

app.include_router(auth.router,           prefix=f"{_API_PREFIX}/auth",                    tags=["认证"])
app.include_router(system.router,         prefix=f"{_API_PREFIX}/system",                  tags=["系统管理"])
app.include_router(system_dictionary.router, prefix=f"{_API_PREFIX}/system/dictionaries", tags=["系统管理 - 数据字典"])
app.include_router(dict_templates.router, prefix=f"{_API_PREFIX}/master-data/dict-templates", tags=["主数据 - 字典与模板"])
app.include_router(materials.router,      prefix=f"{_API_PREFIX}/master-data/materials",   tags=["主数据 - 材料"])
app.include_router(equipments.router,     prefix=f"{_API_PREFIX}/master-data/equipments",  tags=["主数据 - 设备"])
app.include_router(labor.router,          prefix=f"{_API_PREFIX}/master-data/labor",       tags=["主数据 - 人员技能"])
app.include_router(processes.router,      prefix=f"{_API_PREFIX}/master-data/processes",   tags=["主数据 - 工艺工时库"])
app.include_router(energy.router,         prefix=f"{_API_PREFIX}/master-data/energy",      tags=["主数据 - 能源日历"])
app.include_router(engineering.router,    prefix=f"{_API_PREFIX}/engineering",             tags=["工程建模"])
app.include_router(costing.router,        prefix=f"{_API_PREFIX}/costing",                 tags=["成本核算"])
app.include_router(simulation.router,     prefix=f"{_API_PREFIX}/simulations",             tags=["LCC 仿真优化"])
app.include_router(dashboard.router,      prefix=f"{_API_PREFIX}/dashboard",               tags=["全景视界"])
app.include_router(iot.router,            prefix=f"{_API_PREFIX}/iot",                     tags=["IoT 现场采集"])


@app.get("/health", tags=["健康检查"], summary="服务存活探针")
async def health_check() -> dict:
    return {"status": "ok", "version": app.version}
