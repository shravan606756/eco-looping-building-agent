from pathlib import Path

from ai.agent import BuildingOptimizationAgent
from controller.schedule_modifier import ScheduleModifier
from simulation.energyplus_runner import EnergyPlusRunner
from simulation.output_parser import OutputParser

from models.iteration_result import IterationResult

from config import (
    WEATHER_FILE,
    WORKING_IDF,
)


class OptimizationLoop:

    def __init__(self):
        self.runner = EnergyPlusRunner()
        self.agent = BuildingOptimizationAgent()
        self.modifier = ScheduleModifier(WORKING_IDF)

        self.history = []

    def run(self, iterations: int, output_root: Path):

        for i in range(iterations):

            print(f"\n========== ITERATION {i+1} ==========\n")

            output_dir = output_root / f"iteration_{i+1}"

            self.runner.run(
                weather_file=WEATHER_FILE,
                output_directory=output_dir
            )

            parser = OutputParser(output_dir / "eplusout.csv")

            state = parser.latest_state()

            decision = self.agent.decide(state)

            self.modifier.update_setpoints(
                cooling=decision.cooling_setpoint,
                heating=decision.heating_setpoint
            )

            result = IterationResult(
                iteration=i + 1,

                cooling_setpoint=decision.cooling_setpoint,
                heating_setpoint=decision.heating_setpoint,

                outdoor_temperature=state.outdoor_temperature,
                indoor_temperature=state.average_indoor_temperature,

                cooling_rate=state.average_cooling_rate,
                heating_rate=state.average_heating_rate,

                chiller_electricity=state.chiller_electricity,
                plant_cooling_demand=state.plant_cooling_demand,

                confidence=decision.confidence
            )

            self.history.append(result)

            print(result)

        return self.history