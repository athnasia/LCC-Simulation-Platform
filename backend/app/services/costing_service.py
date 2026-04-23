"""
模块四：成本核算与仿真优化 - 静态成本计算引擎

核心功能：
  - 基于快照的静态成本核算
  - 工序级成本分解（料、工、机、外协）
  - BOM 树形卷积汇总（后序遍历算法）

成本计算公式：
  自制件 (IN_HOUSE):
    机器费 = (准备工时 + 运行工时) * 设备折旧费率
    人工费 = (准备工时 + 运行工时) * 人工费率
    辅材费 = Σ (辅材消耗量 * 辅材单价)
    工序成本 = 机器费 + 人工费 + 辅材费

  外协件 (OUTSOURCED):
    工序成本 = 外协单价 + Σ (辅材消耗量 * 辅材单价)

设计约定：
  1. 所有成本计算基于快照数据，确保可追溯性
  2. 使用 Decimal 进行精确计算，避免浮点误差
  3. 树形卷积必须使用后序遍历，保证子节点成本先于父节点计算
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError
from app.models.engineering import EngModelSnapshot


class CostingService:
    """
    静态成本计算服务
    
    负责基于快照数据进行静态成本核算，包括：
    - 工序级成本计算
    - 路线级成本汇总
    - BOM 树形卷积汇总
    """
    
    DEFAULT_LABOR_RATE = Decimal("80.0")
    DEFAULT_EQUIPMENT_RATE = Decimal("50.0")
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_static_cost(self, snapshot_id: int) -> dict[str, Any]:
        """
        计算静态成本（核心入口方法）
        
        Args:
            snapshot_id: 快照 ID
            
        Returns:
            dict: 包含以下字段
                - total_cost: 产品总制造成本
                - cost_breakdown: 分类成本汇总
                - annotated_bom_tree: 注入成本明细的 BOM 树
                - route_costs: 各路线成本明细
        """
        snapshot = self._load_snapshot(snapshot_id)
        snapshot_data = snapshot.snapshot_data
        
        bom_tree = snapshot_data.get("bom_tree", [])
        routes = snapshot_data.get("routes", [])
        master_data_rates = snapshot_data.get("master_data_rates", {})
        
        if not bom_tree:
            return {
                "total_cost": Decimal("0"),
                "cost_breakdown": self._empty_cost_breakdown(),
                "annotated_bom_tree": [],
                "route_costs": [],
            }
        
        route_costs = self._calculate_all_route_costs(routes, master_data_rates)
        
        route_cost_map = {rc["route_id"]: rc for rc in route_costs}
        
        node_route_map = self._build_node_route_map(routes)
        
        tree = self._build_bom_tree(bom_tree)
        
        annotated_tree = self._rollup_costs(tree, node_route_map, route_cost_map)
        
        total_cost, cost_breakdown = self._calculate_totals(annotated_tree)
        
        return {
            "total_cost": total_cost,
            "cost_breakdown": cost_breakdown,
            "annotated_bom_tree": annotated_tree,
            "route_costs": route_costs,
        }
    
    def _load_snapshot(self, snapshot_id: int) -> EngModelSnapshot:
        """加载快照记录"""
        snapshot = self.db.get(EngModelSnapshot, snapshot_id)
        if not snapshot:
            raise ResourceNotFoundError(
                resource_type="ModelSnapshot",
                resource_id=snapshot_id,
            )
        return snapshot
    
    def _calculate_all_route_costs(
        self, 
        routes: list[dict[str, Any]], 
        master_data_rates: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        计算所有工艺路线的成本
        
        Args:
            routes: 路线列表
            master_data_rates: 主数据费率快照
            
        Returns:
            list: 各路线的成本明细列表
        """
        route_costs = []
        
        for route in routes:
            route_cost = self._calculate_route_cost(route, master_data_rates)
            route_costs.append(route_cost)
        
        return route_costs
    
    def _calculate_route_cost(
        self, 
        route: dict[str, Any], 
        master_data_rates: dict[str, Any]
    ) -> dict[str, Any]:
        """
        计算单条工艺路线的成本
        
        Args:
            route: 路线数据
            master_data_rates: 主数据费率快照
            
        Returns:
            dict: 路线成本明细
        """
        route_id = route["route_id"]
        route_name = route["route_name"]
        bom_node_id = route["bom_node_id"]
        steps = route.get("steps", [])
        
        total_machine_cost = Decimal("0")
        total_labor_cost = Decimal("0")
        total_material_cost = Decimal("0")
        total_outsource_cost = Decimal("0")
        
        step_costs = []
        
        for step in steps:
            step_cost = self._calculate_step_cost(step, master_data_rates)
            step_costs.append(step_cost)
            
            total_machine_cost += step_cost["machine_cost"]
            total_labor_cost += step_cost["labor_cost"]
            total_material_cost += step_cost["material_cost"]
            total_outsource_cost += step_cost["outsource_cost"]
        
        route_total = (
            total_machine_cost 
            + total_labor_cost 
            + total_material_cost 
            + total_outsource_cost
        )
        
        return {
            "route_id": route_id,
            "route_name": route_name,
            "bom_node_id": bom_node_id,
            "step_count": len(steps),
            "machine_cost": total_machine_cost,
            "labor_cost": total_labor_cost,
            "material_cost": total_material_cost,
            "outsource_cost": total_outsource_cost,
            "total_cost": route_total,
            "step_costs": step_costs,
        }
    
    def _calculate_step_cost(
        self, 
        step: dict[str, Any], 
        master_data_rates: dict[str, Any]
    ) -> dict[str, Any]:
        """
        计算单道工序的成本
        
        根据工序类型（自制/外协）采用不同的计算公式：
        
        自制件 (IN_HOUSE):
            机器费 = (准备工时 + 运行工时) * 设备折旧费率
            人工费 = (准备工时 + 运行工时) * 人工费率
            辅材费 = Σ (辅材消耗量 * 辅材单价)
            
        外协件 (OUTSOURCED):
            工序成本 = 外协单价 + 辅材费
        
        Args:
            step: 工序步骤数据
            master_data_rates: 主数据费率快照
            
        Returns:
            dict: 工序成本明细
        """
        process_type = step.get("process_type", "IN_HOUSE")
        step_order = step.get("step_order", 0)
        process_id = step.get("process_id")
        process_name = step.get("process", {}).get("name", "")
        
        machine_cost = Decimal("0")
        labor_cost = Decimal("0")
        material_cost = Decimal("0")
        outsource_cost = Decimal("0")
        
        if process_type == "IN_HOUSE":
            t_set = Decimal(str(step.get("override_t_set") or 0))
            t_run = Decimal(str(step.get("override_t_run") or 0))
            total_time = t_set + t_run
            
            equipment_rate = self._get_equipment_rate(step, master_data_rates)
            machine_cost = total_time * equipment_rate
            
            labor_rate = self._get_labor_rate(step, master_data_rates)
            labor_cost = total_time * labor_rate
            
            material_cost = self._calculate_material_cost(step, master_data_rates)
            
        elif process_type == "OUTSOURCED":
            outsource_price = Decimal(str(step.get("outsource_price") or 0))
            outsource_cost = outsource_price
            
            material_cost = self._calculate_material_cost(step, master_data_rates)
        
        total_cost = machine_cost + labor_cost + material_cost + outsource_cost
        
        return {
            "step_order": step_order,
            "process_id": process_id,
            "process_name": process_name,
            "process_type": process_type,
            "t_set": t_set if process_type == "IN_HOUSE" else None,
            "t_run": t_run if process_type == "IN_HOUSE" else None,
            "machine_cost": machine_cost,
            "labor_cost": labor_cost,
            "material_cost": material_cost,
            "outsource_cost": outsource_cost,
            "total_cost": total_cost,
        }
    
    def _get_equipment_rate(
        self, 
        step: dict[str, Any], 
        master_data_rates: dict[str, Any]
    ) -> Decimal:
        """
        获取设备折旧费率
        
        优先级：
        1. 步骤中覆写的设备 ID 对应的费率
        2. 默认设备费率
        """
        equipment_rates = master_data_rates.get("equipment_rates", {})
        
        equipment_id = step.get("override_equipment_id")
        if equipment_id:
            equipment_code = f"EQ_{equipment_id:03d}"
            if equipment_code in equipment_rates:
                return Decimal(str(equipment_rates[equipment_code]))
        
        return self.DEFAULT_EQUIPMENT_RATE
    
    def _get_labor_rate(
        self, 
        step: dict[str, Any], 
        master_data_rates: dict[str, Any]
    ) -> Decimal:
        """
        获取人工费率
        
        MVP 阶段使用统一标准费率，后续可根据工序类型匹配不同工种费率
        """
        labor_rates = master_data_rates.get("labor_rates", {})
        
        if "STANDARD" in labor_rates:
            return Decimal(str(labor_rates["STANDARD"]))
        
        if labor_rates:
            first_rate = next(iter(labor_rates.values()))
            return Decimal(str(first_rate))
        
        return self.DEFAULT_LABOR_RATE
    
    def _calculate_material_cost(
        self, 
        step: dict[str, Any], 
        master_data_rates: dict[str, Any]
    ) -> Decimal:
        """
        计算辅材成本
        
        辅材费 = Σ (辅材消耗量 * 辅材单价)
        
        Args:
            step: 工序步骤数据
            master_data_rates: 主数据费率快照
            
        Returns:
            Decimal: 辅材总成本
        """
        material_prices = master_data_rates.get("material_prices", {})
        mat_params = step.get("override_mat_params") or {}
        
        total_cost = Decimal("0")
        
        for mat_code, quantity in mat_params.items():
            if mat_code in material_prices:
                price = Decimal(str(material_prices[mat_code]))
                qty = Decimal(str(quantity))
                total_cost += price * qty
            else:
                default_price = Decimal("10.0")
                qty = Decimal(str(quantity))
                total_cost += default_price * qty
        
        return total_cost
    
    def _build_node_route_map(
        self, 
        routes: list[dict[str, Any]]
    ) -> dict[int, list[int]]:
        """
        构建 BOM 节点到路线 ID 的映射
        
        Args:
            routes: 路线列表
            
        Returns:
            dict: {bom_node_id: [route_id, ...]}
        """
        node_route_map: dict[int, list[int]] = {}
        
        for route in routes:
            bom_node_id = route["bom_node_id"]
            route_id = route["route_id"]
            
            if bom_node_id not in node_route_map:
                node_route_map[bom_node_id] = []
            node_route_map[bom_node_id].append(route_id)
        
        return node_route_map
    
    def _build_bom_tree(self, bom_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        构建 BOM 树形结构
        
        将扁平的节点列表转换为树形结构，便于后续递归遍历
        
        Args:
            bom_nodes: BOM 节点列表（扁平）
            
        Returns:
            list: 树形结构的根节点列表
        """
        node_map: dict[int, dict[str, Any]] = {}
        root_nodes: list[dict[str, Any]] = []
        
        for node in bom_nodes:
            node_id = node["id"]
            node_copy = dict(node)
            node_copy["children"] = []
            node_copy["cost_detail"] = self._empty_cost_detail()
            node_map[node_id] = node_copy
        
        for node in bom_nodes:
            node_id = node["id"]
            parent_id = node.get("parent_id")
            
            if parent_id is None:
                root_nodes.append(node_map[node_id])
            elif parent_id in node_map:
                node_map[parent_id]["children"].append(node_map[node_id])
        
        return root_nodes
    
    def _rollup_costs(
        self, 
        tree: list[dict[str, Any]], 
        node_route_map: dict[int, list[int]], 
        route_cost_map: dict[int, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        树形卷积汇总（核心算法）
        
        使用后序遍历（Post-order Traversal）递归计算成本：
        1. 先递归计算所有子节点的成本
        2. 叶子节点成本 = 挂载在该节点上的路线成本
        3. 父节点成本 = 自身路线成本 + Σ(子节点成本 * 子节点数量)
        
        Args:
            tree: BOM 树
            node_route_map: 节点到路线的映射
            route_cost_map: 路线 ID 到成本的映射
            
        Returns:
            list: 注入成本明细的 BOM 树
        """
        for node in tree:
            self._rollup_node_cost(node, node_route_map, route_cost_map)
        
        return tree
    
    def _rollup_node_cost(
        self, 
        node: dict[str, Any], 
        node_route_map: dict[int, list[int]], 
        route_cost_map: dict[int, dict[str, Any]]
    ) -> dict[str, Any]:
        """
        递归计算单个节点的成本（后序遍历）
        
        Args:
            node: BOM 节点
            node_route_map: 节点到路线的映射
            route_cost_map: 路线 ID 到成本的映射
            
        Returns:
            dict: 节点的成本明细
        """
        children = node.get("children", [])
        
        for child in children:
            self._rollup_node_cost(child, node_route_map, route_cost_map)
        
        node_id = node["id"]
        quantity = Decimal(str(node.get("quantity") or 1))
        
        own_cost = self._calculate_own_route_cost(node_id, node_route_map, route_cost_map)
        
        children_cost = self._empty_cost_detail()
        for child in children:
            child_cost = child["cost_detail"]
            child_quantity = Decimal(str(child.get("quantity") or 1))
            
            children_cost["machine_cost"] += child_cost["machine_cost"] * child_quantity
            children_cost["labor_cost"] += child_cost["labor_cost"] * child_quantity
            children_cost["material_cost"] += child_cost["material_cost"] * child_quantity
            children_cost["outsource_cost"] += child_cost["outsource_cost"] * child_quantity
            children_cost["total_cost"] += child_cost["total_cost"] * child_quantity
        
        node["cost_detail"] = {
            "machine_cost": own_cost["machine_cost"] + children_cost["machine_cost"],
            "labor_cost": own_cost["labor_cost"] + children_cost["labor_cost"],
            "material_cost": own_cost["material_cost"] + children_cost["material_cost"],
            "outsource_cost": own_cost["outsource_cost"] + children_cost["outsource_cost"],
            "total_cost": own_cost["total_cost"] + children_cost["total_cost"],
            "own_cost": own_cost,
            "children_cost": children_cost,
        }
        
        return node["cost_detail"]
    
    def _calculate_own_route_cost(
        self, 
        node_id: int, 
        node_route_map: dict[int, list[int]], 
        route_cost_map: dict[int, dict[str, Any]]
    ) -> dict[str, Any]:
        """
        计算节点自身的路线成本（不含子节点）
        
        Args:
            node_id: BOM 节点 ID
            node_route_map: 节点到路线的映射
            route_cost_map: 路线 ID 到成本的映射
            
        Returns:
            dict: 节点自身的成本明细
        """
        route_ids = node_route_map.get(node_id, [])
        
        total_machine = Decimal("0")
        total_labor = Decimal("0")
        total_material = Decimal("0")
        total_outsource = Decimal("0")
        
        for route_id in route_ids:
            if route_id in route_cost_map:
                route_cost = route_cost_map[route_id]
                total_machine += route_cost["machine_cost"]
                total_labor += route_cost["labor_cost"]
                total_material += route_cost["material_cost"]
                total_outsource += route_cost["outsource_cost"]
        
        return {
            "machine_cost": total_machine,
            "labor_cost": total_labor,
            "material_cost": total_material,
            "outsource_cost": total_outsource,
            "total_cost": total_machine + total_labor + total_material + total_outsource,
        }
    
    def _calculate_totals(
        self, 
        annotated_tree: list[dict[str, Any]]
    ) -> tuple[Decimal, dict[str, Any]]:
        """
        计算总成本和分类汇总
        
        Args:
            annotated_tree: 注入成本的 BOM 树
            
        Returns:
            tuple: (总成本, 分类成本汇总)
        """
        breakdown = self._empty_cost_breakdown()
        
        for node in annotated_tree:
            cost_detail = node.get("cost_detail", {})
            breakdown["total_machine"] += cost_detail.get("machine_cost", Decimal("0"))
            breakdown["total_labor"] += cost_detail.get("labor_cost", Decimal("0"))
            breakdown["total_material"] += cost_detail.get("material_cost", Decimal("0"))
            breakdown["total_outsource"] += cost_detail.get("outsource_cost", Decimal("0"))
            breakdown["total_cost"] += cost_detail.get("total_cost", Decimal("0"))
        
        return breakdown["total_cost"], breakdown
    
    def _empty_cost_detail(self) -> dict[str, Decimal]:
        """返回空的成本明细结构"""
        return {
            "machine_cost": Decimal("0"),
            "labor_cost": Decimal("0"),
            "material_cost": Decimal("0"),
            "outsource_cost": Decimal("0"),
            "total_cost": Decimal("0"),
        }
    
    def _empty_cost_breakdown(self) -> dict[str, Decimal]:
        """返回空的成本汇总结构"""
        return {
            "total_machine": Decimal("0"),
            "total_labor": Decimal("0"),
            "total_material": Decimal("0"),
            "total_outsource": Decimal("0"),
            "total_cost": Decimal("0"),
        }
