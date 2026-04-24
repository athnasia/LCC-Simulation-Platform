from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_permission
from app.core.database import get_db
from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.models.system import SysUser
from app.models.engineering import EngModelSnapshot, LccFinancialBaseline
from app.schemas.simulation import SimulationStartRequest
from app.worker.tasks import run_lcc_simulation

router = APIRouter()


@router.post(
    "/{snapshot_id}/start",
    response_model=dict[str, Any],
    status_code=status.HTTP_202_ACCEPTED,
    summary="启动 LCC 动态仿真任务",
    description="将指定模型快照投入 Celery 队列，异步执行基于虚拟时间轴的 LCC 动态仿真。",
)
def start_simulation(
    snapshot_id: int,
    payload: SimulationStartRequest,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/snapshots", "write")),
) -> dict[str, Any]:
    if payload.snapshot_id != snapshot_id:
        raise BusinessRuleViolationError(
            message="请求体中的 snapshot_id 与路径参数不一致",
            error_code="SNAPSHOT_ID_MISMATCH",
            detail={"path_snapshot_id": snapshot_id, "payload_snapshot_id": payload.snapshot_id},
        )

    snapshot = db.execute(
        select(EngModelSnapshot).where(
            EngModelSnapshot.id == snapshot_id,
            EngModelSnapshot.is_deleted == False,
        )
    ).scalar_one_or_none()
    if snapshot is None:
        raise ResourceNotFoundError(resource="模型快照", identifier=snapshot_id)

    simulation_payload = payload.to_simulation_payload()

    if payload.baseline_id is not None:
        baseline = db.execute(
            select(LccFinancialBaseline).where(
                LccFinancialBaseline.id == payload.baseline_id,
                LccFinancialBaseline.is_deleted == False,
                LccFinancialBaseline.is_active == True,
            )
        ).scalar_one_or_none()
        if baseline is None:
            raise ResourceNotFoundError(resource="LCC 财务评估基准", identifier=payload.baseline_id)

    run_lcc_simulation.delay(snapshot_id, simulation_payload)
    return {
        "message": "仿真任务已投递",
        "snapshot_id": snapshot_id,
    }


@router.get(
    "/{snapshot_id}/status",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="查询 LCC 仿真状态与结果",
    description="前端轮询接口，用于获取快照当前的仿真状态及计算结果（若已完成）。",
)
def get_simulation_status(
    snapshot_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/engineering/snapshots", "read")),
) -> dict[str, Any]:
    # 纯读取接口，无需加锁
    snapshot = db.execute(
        select(EngModelSnapshot)
        .where(
            EngModelSnapshot.id == snapshot_id,
            EngModelSnapshot.is_deleted == False,
        )
    ).scalar_one_or_none()

    if snapshot is None:
        raise ResourceNotFoundError(resource="模型快照", identifier=snapshot_id)

    return {
        "snapshot_id": snapshot.id,
        "status": snapshot.status,
        # 若为 READY 或 SIMULATING，该字段可能为 None 或只包含极简的进度信息
        # 若为 COMPLETED，则包含完整的 lcc_total_cost 和 timeline_events
        "simulation_result": snapshot.simulation_result 
    }