"""
模块四：成本核算与仿真优化 - API 路由

包含：
  - 静态成本计算接口
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Any

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.system import SysUser
from app.services.costing_service import CostingService

router = APIRouter()


@router.get(
    "/static/{snapshot_id}",
    response_model=dict[str, Any],
    summary="计算静态成本台账",
    description="基于快照数据计算静态成本，返回总成本、成本分解和带成本标注的 BOM 树",
)
def calculate_static_cost(
    snapshot_id: int,
    db: Session = Depends(get_db),
    _: SysUser = Depends(require_permission("/costing/static", "read")),
) -> dict[str, Any]:
    """
    计算静态成本台账
    
    Args:
        snapshot_id: 快照 ID
        
    Returns:
        dict: 包含以下字段
            - total_cost: 产品总制造成本
            - cost_breakdown: 分类成本汇总
            - annotated_bom_tree: 注入成本明细的 BOM 树
            - route_costs: 各路线成本明细
    """
    service = CostingService(db)
    result = service.calculate_static_cost(snapshot_id)
    
    return result

