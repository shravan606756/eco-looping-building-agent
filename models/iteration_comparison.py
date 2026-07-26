from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class IterationComparison:
    iteration: int
    heating_energy_change_pct: float
    cooling_energy_change_pct: float
    total_energy_change_pct: float
    comfort_percentage_change: float
    peak_heating_demand_change_pct: float
    peak_cooling_demand_change_pct: float
    hvac_mode_changed: bool
    temperature_trend_changed: bool
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
