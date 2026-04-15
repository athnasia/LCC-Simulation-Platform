from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.exceptions import BusinessRuleViolationError
from app.models.master_data import ResourceType, MdProcessResource

def _build_deleted_unique_value(value: str | None, record_id: int, max_length: int) -> str | None:
    """构建逻辑删除后的唯一字段墓碑值"""
    if not value:
        return value

    suffix = f"__deleted_{record_id}"
    keep_length = max_length - len(suffix)
    if keep_length <= 0:
        return suffix[-max_length:]
    return f"{value[:keep_length]}{suffix}"

def _check_process_resource_reference(
    db: Session, resource_type: ResourceType, resource_id: int, resource_name: str
) -> None:
    """检查资源是否被工序引用，若被引用则抛出异常"""
    references = db.execute(
        select(MdProcessResource).where(
            MdProcessResource.resource_type == resource_type,
            MdProcessResource.resource_id == resource_id,
            MdProcessResource.is_deleted == False,
        )
        .limit(5)
    ).scalars().all()

    if references:
        process_names = [f"工序ID={ref.process_id}" for ref in references[:3]]
        extra = f"等 {len(references)} 个工序" if len(references) > 3 else ""
        raise BusinessRuleViolationError(
            error_code="RESOURCE_REFERENCED_BY_PROCESS",
            message=f"{resource_name} 已被工序引用（{', '.join(process_names)}{extra}），无法删除。请先解除工序中的资源挂载。",
        )
