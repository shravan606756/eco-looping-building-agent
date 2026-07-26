from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class OptimizationStatus:
    current_iteration: int
    max_iterations: int
    converged: bool
    convergence_reason: str
    current_comfort_pct: float
    current_total_energy_wh: float
    overall_energy_savings_pct: float
    overall_comfort_change_pct: float
    runtime_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
