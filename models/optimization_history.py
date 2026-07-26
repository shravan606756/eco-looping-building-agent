from dataclasses import dataclass
from typing import List, Optional

from models.building_state import BuildingState
from ai.decision_schema import Decision


@dataclass
class IterationRecord:
    iteration: int
    building_state: BuildingState
    decision: Decision
    heating_setpoint: float
    cooling_setpoint: float
    comfort_percentage: float
    total_heating_energy: float
    total_cooling_energy: float
    hvac_mode: str
    temperature_trend: str
    timestamp: str


class OptimizationHistory:

    def __init__(self):
        self.records: List[IterationRecord] = []

    def add_record(self, iteration: int, state: BuildingState, decision: Decision, applied_heating: float, applied_cooling: float) -> IterationRecord:

        rec = IterationRecord(
            iteration=iteration,
            building_state=state,
            decision=decision,
            heating_setpoint=applied_heating,
            cooling_setpoint=applied_cooling,
            comfort_percentage=state.comfort_percentage,
            total_heating_energy=state.total_heating_energy,
            total_cooling_energy=state.total_cooling_energy,
            hvac_mode=state.hvac_operating_mode,
            temperature_trend=state.temperature_trend,
            timestamp=state.timestamp
        )
        self.records.append(rec)
        return rec

    def get_last_record(self) -> Optional[IterationRecord]:
        return self.records[-1] if self.records else None


