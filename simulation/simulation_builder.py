import shutil
from pathlib import Path
from config import ORIGINAL_IDF, WORKING_IDF, WORKING_DIR
from models.optimization_context import OptimizationContext
from models.baseline_model import BaselineModel
from controller.schedule_modifier import ScheduleModifier

class SimulationBuilder:
    def __init__(self):
        self.baseline = BaselineModel()
        WORKING_DIR.mkdir(parents=True, exist_ok=True)

    def build_working_idf(self, active_cooling_setpoint: float, active_heating_setpoint: float) -> Path:
        shutil.copy2(ORIGINAL_IDF, WORKING_IDF)
        
        modifier = ScheduleModifier(str(WORKING_IDF))
        modifier.update_setpoints(
            cooling=active_cooling_setpoint,
            heating=active_heating_setpoint,
            cooling_indices=self.baseline.cooling_occupied_indices,
            heating_indices=self.baseline.heating_occupied_indices
        )
        
        return WORKING_IDF
