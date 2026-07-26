from dataclasses import asdict
from typing import Dict, Any
from tools.base_tool import BaseTool
from models.building_state import BuildingState


class FeatureEngineeringTool(BaseTool):
    name = "FeatureEngineeringTool"
    description = "Exposes rolling 24-hour building performance intelligence dictionary from BuildingState."

    def execute(self, building_state: BuildingState, **kwargs) -> Dict[str, Any]:
        features = asdict(building_state)
        return {
            "features": features,
            "feature_count": len(features),
            "hvac_mode": building_state.hvac_operating_mode,
            "temperature_trend": building_state.temperature_trend
        }
