from pathlib import Path
from typing import Dict, Any
from tools.base_tool import BaseTool
from simulation.simulation_builder import SimulationBuilder
from simulation.energyplus_runner import EnergyPlusRunner
from controller.schedule_modifier import ScheduleModifier
from config import WORKING_IDF


class PrepareWorkingFileTool(BaseTool):
    name = "PrepareWorkingFileTool"
    description = "Prepares a fresh working IDF with specified setpoints."

    def __init__(self, builder: SimulationBuilder = None):
        self.builder = builder or SimulationBuilder()

    def execute(self, active_cooling_setpoint: float, active_heating_setpoint: float, **kwargs) -> Dict[str, Any]:
        idf_path = self.builder.build_working_idf(
            active_cooling_setpoint=active_cooling_setpoint,
            active_heating_setpoint=active_heating_setpoint
        )
        return {
            "status": "prepared",
            "working_idf": str(idf_path)
        }


class ModifyScheduleTool(BaseTool):
    name = "ModifyScheduleTool"
    description = "Deprecated. Use PrepareWorkingFileTool instead."

    def __init__(self, modifier: ScheduleModifier = None):
        pass

    def execute(self, cooling_setpoint: float, heating_setpoint: float, idf_path: Path = None, **kwargs) -> Dict[str, Any]:
        return {
            "status": "deprecated",
            "message": "Schedule modification is now handled idempotently by SimulationBuilder."
        }
