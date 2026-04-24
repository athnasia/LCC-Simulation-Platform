from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_permission
from app.models.system import SysUser
from app.schemas.engineering import (
    PromoteSnapshotToVersionRequest,
    PromoteSnapshotToVersionResponse,
)
from app.services.engineering_service import ModelSnapshotService
from app.services.system_service import AuditLogService

router = APIRouter()


@router.post("/{snapshot_id}/promote-to-version", response_model=PromoteSnapshotToVersionResponse)
def promote_snapshot_to_version(
    snapshot_id: int,
    payload: PromoteSnapshotToVersionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/engineering/snapshots", "write")),
) -> PromoteSnapshotToVersionResponse:
    """基于冻结快照数据创建新的方案版本。"""
    result = ModelSnapshotService(db).promote_to_version(snapshot_id, payload, current_user.username)

    AuditLogService(db).write(
        user_id=current_user.id,
        username=current_user.username,
        action="PROMOTE_TO_VERSION",
        resource_type="MODEL_SNAPSHOT",
        resource_id=result.snapshot_id,
        detail={
            "version_id": result.version_id,
            "version_number": result.version_number,
            "description": result.description,
        },
        ip_address=request.client.host if request.client else None,
    )

    return result