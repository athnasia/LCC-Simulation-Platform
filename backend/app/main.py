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

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, init_db
from app.core.exceptions import (
    AppBaseException,
    UnitConversionChainBrokenError,
)

# ── 路由模块导入 ───────────────────────────────────────────────────────────────
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


# ── 应用生命周期 ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    管理启动与关闭资源：
    - 启动：预检数据库连接、预热 Redis 连接池
    - 关闭：释放连接池，确保无资源泄漏
    """
    # ── 启动阶段 ────────────────────────────────────────────────────────────────
    await init_db()

    yield

    # ── 关闭阶段 ────────────────────────────────────────────────────────────────
    await asyncio.to_thread(engine.dispose)
    # TODO: 在引入 Redis 连接池后，在此补充 close / disconnect 逻辑。


# ── FastAPI 实例 ───────────────────────────────────────────────────────────────

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


# ── 中间件 ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 统一异常处理器 ─────────────────────────────────────────────────────────────

@app.exception_handler(AppBaseException)
async def app_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
    """
    捕获所有业务层主动抛出的领域异常，统一返回标准错误响应体。
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


@app.exception_handler(UnitConversionChainBrokenError)
async def unit_conversion_exception_handler(
    request: Request, exc: UnitConversionChainBrokenError
) -> JSONResponse:
    """
    量纲换算链路断裂时立即挂起并返回明确的参数缺失定位信息，
    防止带着错误单位进入成本核算引擎。
    """
    return JSONResponse(
        status_code=422,
        content={
            "code": "UNIT_CONVERSION_CHAIN_BROKEN",
            "message": "单位换算链路断裂，核算任务已挂起",
            "detail": exc.detail,
        },
    )


# ── 路由注册 ───────────────────────────────────────────────────────────────────

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


# ── 健康检查 ───────────────────────────────────────────────────────────────────

@app.get("/health", tags=["健康检查"], summary="服务存活探针")
async def health_check() -> dict:
    return {"status": "ok", "version": app.version}
