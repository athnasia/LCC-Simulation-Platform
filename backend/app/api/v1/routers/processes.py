"""
标准工艺/工时库 API 路由
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_db, require_permission
from app.schemas.common import PageResult
from app.schemas.master_data import (
    ProcessCloneRequest,
    ProcessCreate,
    ProcessResourceCreate,
    ProcessResourceResponse,
    ProcessResponse,
    ProcessUpdate,
)
from app.services.master_data_service import ProcessService
from app.models.system import SysUser

router = APIRouter()


@router.get("", response_model=PageResult[ProcessResponse])
def list_processes(
    keyword: str | None = None,
    category_id: int | None = None,
    is_active: bool | None = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_active_user),
):
    return ProcessService(db).list(
        keyword=keyword,
        category_id=category_id,
        is_active=is_active,
        page=page,
        size=size,
    )


@router.post("", response_model=ProcessResponse, status_code=status.HTTP_201_CREATED)
def create_process(
    payload: ProcessCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/processes", "write")),
):
    result = ProcessService(db).create(payload, current_user.username)
    db.commit()
    return result


@router.get("/{process_id}", response_model=ProcessResponse)
def get_process(
    process_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(get_current_active_user),
):
    return ProcessService(db).get(process_id)


@router.put("/{process_id}", response_model=ProcessResponse)
def update_process(
    process_id: int,
    payload: ProcessUpdate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/processes", "write")),
):
    result = ProcessService(db).update(process_id, payload, current_user.username)
    db.commit()
    return result


@router.delete("/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_process(
    process_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/processes", "delete")),
):
    ProcessService(db).delete(process_id, current_user.username)
    db.commit()


@router.post("/{process_id}/clone", response_model=ProcessResponse, status_code=status.HTTP_201_CREATED)
def clone_process(
    process_id: int,
    payload: ProcessCloneRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/processes", "write")),
):
    result = ProcessService(db).clone(process_id, payload, current_user.username)
    db.commit()
    return result


@router.post("/{process_id}/resources", response_model=ProcessResourceResponse, status_code=status.HTTP_201_CREATED)
def add_process_resource(
    process_id: int,
    payload: ProcessResourceCreate,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/processes", "write")),
):
    result = ProcessService(db).add_resource(process_id, payload, current_user.username)
    db.commit()
    return result


@router.delete("/{process_id}/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_process_resource(
    process_id: int,
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(require_permission("/master-data/processes", "write")),
):
    ProcessService(db).remove_resource(process_id, resource_id, current_user.username)
    db.commit()
