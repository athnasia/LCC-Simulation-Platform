from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import BusinessRuleViolationError, ResourceNotFoundError, SimulationError
from app.models.engineering import EngModelSnapshot, LccFinancialBaseline
from app.models.master_data import EnergyType, MdEnergyRate, MdEquipment
from app.services.costing_service import CostingService


DECIMAL_ZERO = Decimal("0")
DECIMAL_ONE = Decimal("1")
MONEY_QUANTIZER = Decimal("0.0001")
FINANCIAL_QUANTIZER = Decimal("0.01")
RATIO_QUANTIZER = Decimal("0.000000")
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

    def run_time_stepped_simulation(self, snapshot_id: int, simulation_params: dict[str, Any] | None = None) -> dict[str, Any]:
        if simulation_params and simulation_params.get("baseline_id") not in (None, ""):
            return self._run_chemical_npv_simulation(snapshot_id, simulation_params)

        snapshot = self._lock_snapshot(snapshot_id)
        self._assert_status_available(snapshot)

        virtual_clock = self._build_virtual_start_time(simulation_params)
        simulation_started_at = datetime.now()
        financial_baseline = self._build_financial_baseline_context(simulation_params)

        snapshot.status = "SIMULATING"
        snapshot.updated_by = SYSTEM_OPERATOR
        snapshot.simulation_result = {
            "status": "SIMULATING",
            "started_at": simulation_started_at.isoformat(),
            "snapshot_id": snapshot_id,
            "simulation_params": simulation_params,
            "financial_baseline": financial_baseline,
        }
        self.db.commit()

        snapshot_data = snapshot.snapshot_data or {}
        routes = snapshot_data.get("routes", [])
        master_data_rates = snapshot_data.get("master_data_rates", {})

        electricity_context, active_rate_code = self._load_electricity_rate_context(simulation_params)
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
            "virtual_started_at": self._build_virtual_start_time(simulation_params).isoformat(),
            "virtual_finished_at": virtual_clock.isoformat(),
            "started_at": simulation_started_at.isoformat(),
            "finished_at": simulation_finished_at.isoformat(),
            "simulation_params": simulation_params,
            "financial_baseline": financial_baseline,
            "energy_context": {
                "rate_code": active_rate_code,
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

    def _run_chemical_npv_simulation(self, snapshot_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        snapshot = self._lock_snapshot(snapshot_id)
        self._assert_status_available(snapshot)

        baseline_id = payload.get("baseline_id")
        if baseline_id in (None, ""):
            raise BusinessRuleViolationError(
                message="化工 NPV 仿真缺少 baseline_id",
                error_code="CHEMICAL_BASELINE_REQUIRED",
                detail={"snapshot_id": snapshot_id},
            )

        capex = self._to_financial_decimal(payload.get("capex"))
        base_mc = self._to_financial_decimal(payload.get("base_mc"))
        annual_hours = self._to_decimal(payload.get("annual_hours"))
        if capex <= DECIMAL_ZERO or base_mc <= DECIMAL_ZERO or annual_hours <= DECIMAL_ZERO:
            raise BusinessRuleViolationError(
                message="化工 NPV 仿真参数必须大于 0",
                error_code="CHEMICAL_SIMULATION_PARAM_INVALID",
                detail={
                    "snapshot_id": snapshot_id,
                    "capex": self._decimal_to_currency_string(capex),
                    "base_mc": self._decimal_to_currency_string(base_mc),
                    "annual_hours": self._decimal_to_string(annual_hours),
                },
            )

        baseline = self._load_financial_baseline(int(baseline_id), active_only=True)
        financial_baseline = self._build_financial_baseline_context(payload)
        simulation_started_at = datetime.now()

        snapshot.status = "SIMULATING"
        snapshot.updated_by = SYSTEM_OPERATOR
        snapshot.simulation_result = {
            "status": "SIMULATING",
            "snapshot_id": snapshot_id,
            "started_at": simulation_started_at.isoformat(),
            "simulation_type": "PROCESS_CHEMICAL",
            "simulation_params": payload,
            "financial_baseline": financial_baseline,
        }
        self.db.commit()

        lifecycle_years = baseline.lifecycle_years
        discount_rate = self._percent_to_ratio(baseline.discount_rate)
        corrosion_rate = self._percent_to_ratio(baseline.corrosion_rate)
        risk_strategy = str(baseline.risk_strategy or "FIXED").upper()
        risk_value = self._to_financial_decimal(baseline.risk_value)
        if risk_strategy == "PERCENTAGE":
            risk_value = self._percent_to_ratio(risk_value)
        eol_salvage_rate = self._percent_to_ratio(baseline.eol_salvage_rate)

        static_total_cost = self._to_financial_decimal(
            CostingService(self.db).calculate_static_cost(snapshot_id).get("total_cost", DECIMAL_ZERO)
        )
        snapshot_data = snapshot.snapshot_data or {}
        single_run_hours = self._extract_single_run_hours(snapshot_data)
        if single_run_hours <= DECIMAL_ZERO:
            single_run_hours = DECIMAL_ONE

        routes = snapshot_data.get("routes", [])
        master_data_rates = snapshot_data.get("master_data_rates", {})
        equipment_profiles = self._load_equipment_profiles(routes)
        
        energy_kwh_per_run = DECIMAL_ZERO
        for route in routes:
            for step in route.get("steps", []):
                process_type = str(step.get("process_type") or "IN_HOUSE").upper()
                if process_type == "IN_HOUSE":
                    eq_prof = self._get_equipment_profile(step, equipment_profiles, master_data_rates)
                    t_hours = self._to_decimal(step.get("override_t_set")) + self._to_decimal(step.get("override_t_run"))
                    energy_kwh_per_run += eq_prof.power_consumption * t_hours

        electricity_context, active_rate_code = self._load_electricity_rate_context(payload)
        
        total_mult = DECIMAL_ZERO
        for h in range(24):
            t = time(hour=h, minute=0, second=0)
            rate = DECIMAL_ONE
            for rule in electricity_context.rules:
                if rule.matches(t):
                    rate = rule.multiplier
                    break
            total_mult += rate
        
        weighted_multiplier = total_mult / Decimal("24.0")
        weighted_electricity_price = self._quantize_financial(electricity_context.base_price * weighted_multiplier)
        annual_energy_kwh = (energy_kwh_per_run / single_run_hours) * annual_hours
        annual_energy_cost = self._quantize_financial(annual_energy_kwh * weighted_electricity_price)
        annual_regular_opex = self._quantize_financial((static_total_cost / single_run_hours) * annual_hours)

        annual_opex = annual_regular_opex + annual_energy_cost

        capex_pv_total = capex
        opex_pv_total = DECIMAL_ZERO
        maintenance_pv_total = DECIMAL_ZERO
        risk_pv_total = DECIMAL_ZERO
        eol_pv_total = DECIMAL_ZERO
        total_npv = capex
        timeline_events: list[dict[str, Any]] = []

        for year in range(1, lifecycle_years + 1):
            discount_factor = (DECIMAL_ONE + discount_rate) ** year
            mc_t = self._quantize_financial(base_mc * ((DECIMAL_ONE + corrosion_rate) ** (year - 1)))
            rc_t = self._quantize_financial(annual_opex * risk_value) if risk_strategy == "PERCENTAGE" else risk_value

            pv_opex = self._quantize_financial(annual_opex / discount_factor)
            pv_mc = self._quantize_financial(mc_t / discount_factor)
            pv_rc = self._quantize_financial(rc_t / discount_factor)
            pv_eol = DECIMAL_ZERO
            if year == lifecycle_years:
                pv_eol = self._quantize_financial(-(capex * eol_salvage_rate) / discount_factor)

            year_npv = pv_opex + pv_mc + pv_rc + pv_eol
            total_npv += year_npv
            opex_pv_total += pv_opex
            maintenance_pv_total += pv_mc
            risk_pv_total += pv_rc
            eol_pv_total += pv_eol

            timeline_events.append(
                {
                    "year": year,
                    "discount_factor": self._decimal_to_ratio_string(discount_factor),
                    "annual_opex": self._decimal_to_currency_string(annual_opex),
                    "maintenance_cost": self._decimal_to_currency_string(mc_t),
                    "risk_cost": self._decimal_to_currency_string(rc_t),
                    "pv_opex": self._decimal_to_currency_string(pv_opex),
                    "pv_mc": self._decimal_to_currency_string(pv_mc),
                    "pv_rc": self._decimal_to_currency_string(pv_rc),
                    "pv_eol": self._decimal_to_currency_string(pv_eol),
                    "year_total_pv": self._decimal_to_currency_string(year_npv),
                }
            )

        simulation_finished_at = datetime.now()
        result = {
            "status": "COMPLETED",
            "snapshot_id": snapshot_id,
            "started_at": simulation_started_at.isoformat(),
            "finished_at": simulation_finished_at.isoformat(),
            "simulation_type": "PROCESS_CHEMICAL",
            "simulation_params": payload,
            "financial_baseline": financial_baseline,
            "static_total_cost": self._decimal_to_currency_string(static_total_cost),
            "single_run_hours": self._decimal_to_string(single_run_hours),
            "annual_opex": self._decimal_to_currency_string(annual_opex),
            "chemical_energy_analysis": {
                "rate_code": active_rate_code,
                "base_price": self._decimal_to_string(electricity_context.base_price),
                "weighted_multiplier": self._decimal_to_string(weighted_multiplier),
                "weighted_price": self._decimal_to_currency_string(weighted_electricity_price),
                "energy_kwh_per_run": self._decimal_to_string(energy_kwh_per_run),
                "annual_energy_kwh": self._decimal_to_string(annual_energy_kwh),
                "annual_energy_cost": self._decimal_to_currency_string(annual_energy_cost),
                "annual_regular_opex": self._decimal_to_currency_string(annual_regular_opex)
            },
            "financial_breakdown": {
                "CAPEX": self._decimal_to_currency_string(capex_pv_total),
                "OPEX": self._decimal_to_currency_string(opex_pv_total),
                "M&R": self._decimal_to_currency_string(maintenance_pv_total),
                "RISK_COST": self._decimal_to_currency_string(risk_pv_total),
                "EOL": self._decimal_to_currency_string(eol_pv_total),
            },
            "lcc_total_cost": self._decimal_to_currency_string(total_npv),
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

    def _build_virtual_start_time(self, simulation_params: dict[str, Any] | None = None) -> datetime:
        if simulation_params:
            start_time_str = simulation_params.get("start_time")
            if start_time_str:
                try:
                    return datetime.fromisoformat(start_time_str)
                except ValueError:
                    pass
        tomorrow = datetime.now() + timedelta(days=1)
        return datetime.combine(tomorrow.date(), time(hour=8, minute=0, second=0))

    def _build_financial_baseline_context(self, simulation_params: dict[str, Any] | None) -> dict[str, Any] | None:
        if not simulation_params:
            return None

        baseline_id = simulation_params.get("baseline_id")
        if baseline_id in (None, ""):
            return None

        baseline = self._load_financial_baseline(int(baseline_id), active_only=False)

        return {
            "id": baseline.id,
            "rule_name": baseline.rule_name,
            "lifecycle_years": baseline.lifecycle_years,
            "discount_rate": self._decimal_to_string(self._to_decimal(baseline.discount_rate)),
            "corrosion_rate": self._decimal_to_string(self._to_decimal(baseline.corrosion_rate)),
            "risk_strategy": baseline.risk_strategy,
            "risk_value": self._decimal_to_string(self._to_decimal(baseline.risk_value)),
            "eol_salvage_rate": self._decimal_to_string(self._to_decimal(baseline.eol_salvage_rate)),
            "is_active": baseline.is_active,
        }

    def _load_financial_baseline(self, baseline_id: int, *, active_only: bool) -> LccFinancialBaseline:
        stmt = select(LccFinancialBaseline).where(
            LccFinancialBaseline.id == baseline_id,
            LccFinancialBaseline.is_deleted == False,
        )
        if active_only:
            stmt = stmt.where(LccFinancialBaseline.is_active == True)

        baseline = self.db.execute(stmt).scalar_one_or_none()
        if baseline is None:
            raise ResourceNotFoundError(resource="LCC 财务评估基准", identifier=baseline_id)
        return baseline

    def _extract_single_run_hours(self, snapshot_data: dict[str, Any]) -> Decimal:
        total_hours = DECIMAL_ZERO
        for route in snapshot_data.get("routes", []):
            for step in route.get("steps", []):
                total_hours += self._to_decimal(step.get("override_t_set"))
                total_hours += self._to_decimal(step.get("override_t_run"))
        return self._quantize(total_hours)

    def _to_financial_decimal(self, value: Any) -> Decimal:
        if value in (None, ""):
            return DECIMAL_ZERO
        if isinstance(value, Decimal):
            return self._quantize_financial(value)
        return self._quantize_financial(Decimal(str(value)))

    def _percent_to_ratio(self, value: Any) -> Decimal:
        return self._quantize_ratio(self._to_financial_decimal(value) / Decimal("100"))

    def _quantize_financial(self, value: Decimal) -> Decimal:
        return value.quantize(FINANCIAL_QUANTIZER, rounding=ROUND_HALF_UP)

    def _quantize_ratio(self, value: Decimal) -> Decimal:
        return value.quantize(RATIO_QUANTIZER, rounding=ROUND_HALF_UP)

    def _decimal_to_currency_string(self, value: Decimal) -> str:
        return format(self._quantize_financial(value), "f")

    def _decimal_to_ratio_string(self, value: Decimal) -> str:
        return format(self._quantize_ratio(value), "f")

    def _load_electricity_rate_context(self, simulation_params: dict[str, Any] | None = None) -> tuple[ElectricityRateContext, str]:
        target_code = (simulation_params or {}).get("energy_rate_code")

        stmt = (
            select(MdEnergyRate)
            .where(
                MdEnergyRate.energy_type == EnergyType.ELECTRICITY,
                MdEnergyRate.is_deleted == False,
                MdEnergyRate.is_active == True,
            )
            .options(selectinload(MdEnergyRate.calendars))
        )

        if target_code:
            stmt = stmt.where(MdEnergyRate.code == target_code)
        
        energy_rate = self.db.execute(stmt).scalars().first()

        if energy_rate is None:
            raise ResourceNotFoundError(resource="工业用电费率", identifier=target_code or "ANY_ACTIVE_ELECTRICITY")

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
        ), energy_rate.code

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