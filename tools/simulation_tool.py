from pathlib import Path
from typing import Dict, Any
from tools.base_tool import BaseTool
from simulation.energyplus_runner import EnergyPlusRunner
from config import WEATHER_FILE


class RunSimulationTool(BaseTool):
    name = "RunSimulationTool"
    description = "Executes EnergyPlus simulation for specified output directory and generates output CSV."

    def __init__(self, runner: EnergyPlusRunner = None):
        self.runner = runner or EnergyPlusRunner()

    def execute(self, output_directory: Path, weather_file: Path = None, **kwargs) -> Dict[str, Any]:
        w_file = weather_file or WEATHER_FILE
        out_dir = Path(output_directory)

        self.runner.run(weather_file=w_file, output_directory=out_dir)
        csv_file = out_dir / "eplusout.csv"

        if not csv_file.exists():
            raise FileNotFoundError(f"Simulation output CSV missing at {csv_file}")

        return {
            "status": "completed",
            "csv_path": str(csv_file),
            "output_directory": str(out_dir)
        }
