from config import WEATHER_FILE, BASELINE_OUTPUT
from simulation.energyplus_runner import EnergyPlusRunner

runner = EnergyPlusRunner()

runner.prepare_working_file()

runner.run(
    weather_file=WEATHER_FILE,
    output_directory=BASELINE_OUTPUT
)

print("\nBaseline simulation finished.")