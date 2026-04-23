from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError, SimulationError
from app.models.engineering import EngModelSnapshot
from app.models.master_data import EnergyType, MdEnergyRate, MdEquipment


DECIMAL_ZERO = Decimal("0")
DECIMAL_ONE = Decimal("1")
MONEY_QUANTIZER = Decimal("0.0001")
DEFAULT_EQUIPMENT_RATE = Decimal("50.0")
DEFAULT_LABOR_RATE = Decimal("80.0")
DEFAULT_POWER_CONSUMPTION = Decimal("1.0")
SYSTEM_OPERATOR = "celery_worker"


@dataclass(frozen=True)
class ElectricityCalendarRule:
    name: str
    start_time: time
    end_time: time
    multiplier: Decimal

    def matches(self, current_time: time) -> bool:
        if self.start_time <= self.end_time:
            return self.start_time <= current_time < self.end_time
        return current_time >= self.start_time or current_time < self.end_time


@dataclass(frozen=True)
class ElectricityRateContext:
    base_price: Decimal
    rules: tuple[ElectricityCalendarRule, ...]


@dataclass(frozen=True)
class EquipmentProfile:
    equipment_id: int
    code: str | None
    depreciation_rate: Decimal
    power_consumption: Decimal


class SimulationService:
    """LCC 动态仿真服务。"""

    def __init__(self, db: Session):
        self.db = db

    def run_time_stepped_simulation(self, snapshot_id: int) -> dict[str, Any]:
        snapshot = self._lock_snapshot(snapshot_id)
        self._assert_status_available(snapshot)

        virtual_clock = self._build_virtual_start_time()
        simulation_started_at = datetime.now()

        snapshot.status = "SIMULATING"
        snapshot.updated_by = SYSTEM_OPERATOR
        snapshot.simulation_result = {
            "status": "SIMULATING",
            "started_at": simulation_started_at.isoformat(),
            "snapshot_id": snapshot_id,
        }
        self.db.commit()

        snapshot_data = snapshot.snapshot_data or {}
        routes = snapshot_data.get("routes", [])
        master_data_rates = snapshot_data.get("master_data_rates", {})

        electricity_context = self._load_electricity_rate_context()
        equipment_profiles = self._load_equipment_profiles(routes)

        total_machine_cost = DECIMAL_ZERO
        total_labor_cost = DECIMAL_ZERO
        total_material_cost = DECIMAL_ZERO
        total_outsource_cost = DECIMAL_ZERO
        total_energy_cost = DECIMAL_ZERO
        timeline_events: list[dict[str, Any]] = []

        for route in routes:
            route_id = route.get("route_id")
            route_name = route.get("route_name") or ""
            bom_node_id = route.get("bom_node_id")
            bom_node_name = route.get("bom_node_name") or ""

            for step in route.get("steps", []):
                process_type = str(step.get("process_type") or "IN_HOUSE").upper()
                event_start = virtual_clock
                material_cost = self._calculate_material_cost(step, master_data_rates)

                if process_type == "OUTSOURCED":
                    outsource_cost = self._to_decimal(step.get("outsource_price"))
                    event_payload = {
                        "route_id": route_id,
                        "route_name": route_name,
                        "bom_node_id": bom_node_id,
                        "bom_node_name": bom_node_name,
                        "step_order": step.get("step_order"),
                        "process_id": step.get("process_id"),
                        "process_name": self._resolve_process_name(step),
                        "process_type": process_type,
                        "start_time": event_start.isoformat(),
                        "end_time": event_start.isoformat(),
                        "duration_hours": self._decimal_to_string(DECIMAL_ZERO),
                        "machine_cost": self._decimal_to_string(DECIMAL_ZERO),
                        "labor_cost": self._decimal_to_string(DECIMAL_ZERO),
                        "material_cost": self._decimal_to_string(material_cost),
                        "energy_cost": self._decimal_to_string(DECIMAL_ZERO),
                        "outsource_cost": self._decimal_to_string(outsource_cost),
                        "total_cost": self._decimal_to_string(material_cost + outsource_cost),
                    }
                    timeline_events.append(event_payload)
                    total_material_cost += material_cost
                    total_outsource_cost += outsource_cost
                    continue

                if process_type != "IN_HOUSE":
                    raise SimulationError(
                        message=f"不支持的工序类型：{process_type}",
                        detail={
                            "snapshot_id": snapshot_id,
                            "route_id": route_id,
                            "step_order": step.get("step_order"),
                        },
                    )

                total_hours = self._to_decimal(step.get("override_t_set")) + self._to_decimal(step.get("override_t_run"))
                labor_rate = self._get_labor_rate(step, master_data_rates)
                equipment_profile = self._get_equipment_profile(step, equipment_profiles, master_data_rates)

                remaining_hours = total_hours
                machine_cost = DECIMAL_ZERO
                labor_cost = DECIMAL_ZERO
                energy_cost = DECIMAL_ZERO
                hourly_breakdown: list[dict[str, str]] = []

                while remaining_hours > DECIMAL_ZERO:
                    current_slice_hours = min(DECIMAL_ONE, remaining_hours)
                    electricity_rate = self.get_electricity_rate(virtual_clock, electricity_context)
                    slice_machine_cost = equipment_profile.depreciation_rate * current_slice_hours
                    slice_labor_cost = labor_rate * current_slice_hours
                    slice_energy_cost = equipment_profile.power_consumption * electricity_rate * current_slice_hours

                    machine_cost += slice_machine_cost
                    labor_cost += slice_labor_cost
                    energy_cost += slice_energy_cost
                    hourly_breakdown.append(
                        {
                            "segment_start": virtual_clock.isoformat(),
                            "segment_hours": self._decimal_to_string(current_slice_hours),
                            "electricity_rate": self._decimal_to_string(electricity_rate),
                            "machine_cost": self._decimal_to_string(slice_machine_cost),
                            "labor_cost": self._decimal_to_string(slice_labor_cost),
                            "energy_cost": self._decimal_to_string(slice_energy_cost),
                        }
                    )

                    remaining_hours -= current_slice_hours
                    virtual_clock += timedelta(hours=float(current_slice_hours))

                total_machine_cost += machine_cost
                total_labor_cost += labor_cost
                total_material_cost += material_cost
                total_energy_cost += energy_cost

                timeline_events.append(
                    {
                        "route_id": route_id,
                        "route_name": route_name,
                        "bom_node_id": bom_node_id,
                        "bom_node_name": bom_node_name,
                        "step_order": step.get("step_order"),
                        "process_id": step.get("process_id"),
                        "process_name": self._resolve_process_name(step),
                        "process_type": process_type,
                        "equipment_id": step.get("override_equipment_id"),
                        "equipment_code": equipment_profile.code,
                        "start_time": event_start.isoformat(),
                        "end_time": virtual_clock.isoformat(),
                        "duration_hours": self._decimal_to_string(total_hours),
                        "machine_cost": self._decimal_to_string(machine_cost),
                        "labor_cost": self._decimal_to_string(labor_cost),
                        "material_cost": self._decimal_to_string(material_cost),
                        "energy_cost": self._decimal_to_string(energy_cost),
                        "outsource_cost": self._decimal_to_string(DECIMAL_ZERO),
                        "total_cost": self._decimal_to_string(machine_cost + labor_cost + material_cost + energy_cost),
                        "hourly_breakdown": hourly_breakdown,
                    }
                )

        lcc_total_cost = (
            total_machine_cost
            + total_labor_cost
            + total_material_cost
            + total_outsource_cost
            + total_energy_cost
        )
        simulation_finished_at = datetime.now()
        result = {
            "status": "COMPLETED",
            "snapshot_id": snapshot_id,
            "virtual_started_at": self._build_virtual_start_time().isoformat(),
            "virtual_finished_at": virtual_clock.isoformat(),
            "started_at": simulation_started_at.isoformat(),
            "finished_at": simulation_finished_at.isoformat(),
            "energy_context": {
                "rate_code": "ELEC_INDUSTRIAL",
                "base_price": self._decimal_to_string(electricity_context.base_price),
                "rules": [
                    {
                        "name": rule.name,
                        "start_time": rule.start_time.isoformat(),
                        "end_time": rule.end_time.isoformat(),
                        "multiplier": self._decimal_to_string(rule.multiplier),
                    }
                    for rule in electricity_context.rules
                ],
            },
            "cost_breakdown": {
                "machine_cost": self._decimal_to_string(total_machine_cost),
                "labor_cost": self._decimal_to_string(total_labor_cost),
                "material_cost": self._decimal_to_string(total_material_cost),
                "energy_cost": self._decimal_to_string(total_energy_cost),
                "outsource_cost": self._decimal_to_string(total_outsource_cost),
            },
            "lcc_total_cost": self._decimal_to_string(lcc_total_cost),
            "timeline_events": timeline_events,
        }

        snapshot.status = "COMPLETED"
        snapshot.updated_by = SYSTEM_OPERATOR
        snapshot.simulation_result = result
        self.db.commit()
        return result

    def mark_failed(self, snapshot_id: int, error_message: str, stack_trace: str) -> None:
        snapshot = self.db.execute(
            select(EngModelSnapshot).where(
                EngModelSnapshot.id == snapshot_id,
                EngModelSnapshot.is_deleted == False,
            )
        ).scalar_one_or_none()
        if snapshot is None:
            return

        snapshot.status = "FAILED"
        snapshot.updated_by = SYSTEM_OPERATOR
        snapshot.simulation_result = {
            "status": "FAILED",
            "snapshot_id": snapshot_id,
            "failed_at": datetime.now().isoformat(),
            "error_message": error_message,
            "stack_trace": stack_trace,
        }
        self.db.commit()

    def get_electricity_rate(
        self,
        current_datetime: datetime,
        electricity_context: ElectricityRateContext,
    ) -> Decimal:
        current_time = current_datetime.time()
        for rule in electricity_context.rules:
            if rule.matches(current_time):
                return self._quantize(electricity_context.base_price * rule.multiplier)
        return self._quantize(electricity_context.base_price)

    def _lock_snapshot(self, snapshot_id: int) -> EngModelSnapshot:
        snapshot = self.db.execute(
            select(EngModelSnapshot)
            .where(
                EngModelSnapshot.id == snapshot_id,
                EngModelSnapshot.is_deleted == False,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if snapshot is None:
            raise ResourceNotFoundError(resource="模型快照", identifier=snapshot_id)
        return snapshot

    def _assert_status_available(self, snapshot: EngModelSnapshot) -> None:
        if snapshot.status == "SIMULATING":
            raise BusinessRuleViolationError(
                message="该快照已有仿真任务在执行，请勿重复投递",
                error_code="SIMULATION_ALREADY_RUNNING",
                detail={"snapshot_id": snapshot.id},
            )
        if snapshot.status in {"DRAFT", "ARCHIVED"}:
            raise BusinessRuleViolationError(
                message=f"当前状态不允许执行仿真：{snapshot.status}",
                error_code="INVALID_SNAPSHOT_STATUS",
                detail={"snapshot_id": snapshot.id, "status": snapshot.status},
            )

    def _build_virtual_start_time(self) -> datetime:
        tomorrow = datetime.now() + timedelta(days=1)
        return datetime.combine(tomorrow.date(), time(hour=8, minute=0, second=0))

    def _load_electricity_rate_context(self) -> ElectricityRateContext:
        energy_rate = self.db.execute(
            select(MdEnergyRate)
            .where(
                MdEnergyRate.code == "ELEC_INDUSTRIAL",
                MdEnergyRate.energy_type == EnergyType.ELECTRICITY,
                MdEnergyRate.is_deleted == False,
                MdEnergyRate.is_active == True,
            )
            .options(selectinload(MdEnergyRate.calendars))
        ).scalar_one_or_none()

        if energy_rate is None:
            raise ResourceNotFoundError(resource="工业用电费率", identifier="ELEC_INDUSTRIAL")

        rules = tuple(
            ElectricityCalendarRule(
                name=calendar.name,
                start_time=calendar.start_time,
                end_time=calendar.end_time,
                multiplier=self._to_decimal(calendar.multiplier),
            )
            for calendar in energy_rate.calendars
            if calendar.is_active
        )
        return ElectricityRateContext(
            base_price=self._to_decimal(energy_rate.unit_price),
            rules=rules,
        )

    def _load_equipment_profiles(self, routes: list[dict[str, Any]]) -> dict[int, EquipmentProfile]:
        equipment_ids = sorted(
            {
                int(step["override_equipment_id"])
                for route in routes
                for step in route.get("steps", [])
                if step.get("process_type") == "IN_HOUSE" and step.get("override_equipment_id") is not None
            }
        )
        if not equipment_ids:
            return {}

        equipments = self.db.execute(
            select(MdEquipment).where(
                MdEquipment.id.in_(equipment_ids),
                MdEquipment.is_deleted == False,
            )
        ).scalars().all()

        profile_map: dict[int, EquipmentProfile] = {}
        for equipment in equipments:
            power_consumption = self._to_decimal(equipment.power_consumption)
            dynamic_attributes = equipment.dynamic_attributes or {}
            if power_consumption <= DECIMAL_ZERO and dynamic_attributes.get("rated_power") is not None:
                power_consumption = self._to_decimal(dynamic_attributes.get("rated_power"))

            profile_map[equipment.id] = EquipmentProfile(
                equipment_id=equipment.id,
                code=equipment.code,
                depreciation_rate=self._to_decimal(equipment.depreciation_rate),
                power_consumption=power_consumption,
            )
        return profile_map

    def _get_equipment_profile(
        self,
        step: dict[str, Any],
        equipment_profiles: dict[int, EquipmentProfile],
        master_data_rates: dict[str, Any],
    ) -> EquipmentProfile:
        equipment_id = step.get("override_equipment_id")
        if equipment_id is not None and equipment_id in equipment_profiles:
            return equipment_profiles[equipment_id]

        equipment_rates = master_data_rates.get("equipment_rates", {})
        equipment_code = None
        depreciation_rate = DEFAULT_EQUIPMENT_RATE
        if equipment_id is not None:
            equipment_code = f"EQ_{int(equipment_id):03d}"
            if equipment_code in equipment_rates:
                depreciation_rate = self._to_decimal(equipment_rates[equipment_code])

        return EquipmentProfile(
            equipment_id=int(equipment_id or 0),
            code=equipment_code,
            depreciation_rate=depreciation_rate,
            power_consumption=DEFAULT_POWER_CONSUMPTION,
        )

    def _get_labor_rate(
        self,
        step: dict[str, Any],
        master_data_rates: dict[str, Any],
    ) -> Decimal:
        del step
        labor_rates = master_data_rates.get("labor_rates", {})
        if "STANDARD" in labor_rates:
            return self._to_decimal(labor_rates["STANDARD"])
        if labor_rates:
            first_rate = next(iter(labor_rates.values()))
            return self._to_decimal(first_rate)
        return DEFAULT_LABOR_RATE

    def _calculate_material_cost(
        self,
        step: dict[str, Any],
        master_data_rates: dict[str, Any],
    ) -> Decimal:
        material_prices = master_data_rates.get("material_prices", {})
        mat_params = step.get("override_mat_params") or {}
        total_cost = DECIMAL_ZERO
        for material_code, quantity in mat_params.items():
            unit_price = self._to_decimal(material_prices.get(material_code))
            total_cost += self._to_decimal(quantity) * unit_price
        return self._quantize(total_cost)

    def _resolve_process_name(self, step: dict[str, Any]) -> str:
        process_info = step.get("process") or {}
        return str(process_info.get("name") or "")

    def _to_decimal(self, value: Any) -> Decimal:
        if value in (None, ""):
            return DECIMAL_ZERO
        if isinstance(value, Decimal):
            return self._quantize(value)
        return self._quantize(Decimal(str(value)))

    def _quantize(self, value: Decimal) -> Decimal:
        return value.quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)

    def _decimal_to_string(self, value: Decimal) -> str:
        return format(self._quantize(value), "f")