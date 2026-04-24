from __future__ import annotations

import logging
import traceback
from typing import Any

from app.core.database import SessionLocal
from app.services.simulation_service import SimulationService
from app.tasks import celery_app


logger = logging.getLogger(__name__)


@celery_app.task(name="run_lcc_simulation", bind=True)
def run_lcc_simulation(self, snapshot_id: int, simulation_params: dict[str, Any] | None = None) -> dict[str, Any]:
    db = SessionLocal()
    try:
        result = SimulationService(db).run_time_stepped_simulation(snapshot_id, simulation_params)
        return {
            "task_id": self.request.id,
            "snapshot_id": snapshot_id,
            "status": "COMPLETED",
            "lcc_total_cost": result.get("lcc_total_cost", "0.0000"),
        }
    except Exception as exc:
        db.rollback()
        stack_trace = traceback.format_exc()
        logger.exception("LCC 仿真任务执行失败，snapshot_id=%s", snapshot_id)

        recovery_db = SessionLocal()
        try:
            SimulationService(recovery_db).mark_failed(
                snapshot_id=snapshot_id,
                error_message=str(exc),
                stack_trace=stack_trace,
            )
        finally:
            recovery_db.close()
        raise
    finally:
        db.close()