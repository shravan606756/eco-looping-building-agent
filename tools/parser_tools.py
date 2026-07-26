from pathlib import Path
from typing import Dict, Any
from tools.base_tool import BaseTool
from simulation.output_parser import OutputParser
from models.building_state import BuildingState


class ParseResultsTool(BaseTool):
    name = "ParseResultsTool"
    description = "Parses EnergyPlus output CSV into a BuildingState object over a configurable rolling time window."

    def execute(self, csv_path: Path, hours: int = 24, **kwargs) -> Dict[str, Any]:
        c_path = Path(csv_path)
        if not c_path.exists():
            raise FileNotFoundError(f"CSV file not found: {c_path}")

        parser = OutputParser(str(c_path))
        state: BuildingState = parser.latest_state(hours=hours)

        return {
            "building_state": state,
            "timestamp": state.timestamp,
            "comfort_percentage": state.comfort_percentage,
            "average_indoor_temperature": state.average_indoor_temperature,
            "total_heating_energy": state.total_heating_energy,
            "total_cooling_energy": state.total_cooling_energy
        }
