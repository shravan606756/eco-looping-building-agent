from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from models.building_state import BuildingState
from models.iteration_comparison import IterationComparison
from models.engineering_assessment import EngineeringAssessment
from ai.decision_schema import Decision


@dataclass
class OptimizationContext:
    iteration: int
    current_state: BuildingState
    previous_state: Optional[BuildingState]
    iteration_comparison: Optional[IterationComparison]
    engineering_assessment: Optional[EngineeringAssessment]
    previous_decision: Optional[Decision]
    active_heating_setpoint: float
    active_cooling_setpoint: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
