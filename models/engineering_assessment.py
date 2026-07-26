from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, Any


class ActionEffectiveness(str, Enum):
    SUCCESSFUL = "SUCCESSFUL"
    COUNTERPRODUCTIVE = "COUNTERPRODUCTIVE"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class MetricTrend(str, Enum):
    SIGNIFICANT_IMPROVEMENT = "SIGNIFICANT_IMPROVEMENT"
    IMPROVED = "IMPROVED"
    UNCHANGED = "UNCHANGED"
    DEGRADED = "DEGRADED"
    SIGNIFICANT_DEGRADATION = "SIGNIFICANT_DEGRADATION"
    UNKNOWN = "UNKNOWN"


@dataclass
class EngineeringAssessment:
    action_effectiveness: ActionEffectiveness
    comfort_trend: MetricTrend
    energy_trend: MetricTrend
    peak_demand_trend: MetricTrend

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
