from pathlib import Path
import shutil
import subprocess

from config import (
    ENERGYPLUS_EXE,
    READVARS_EXE,
    ORIGINAL_IDF,
    WORKING_IDF,
    WORKING_DIR,
)

#to execute EnergyPlus simulation and handle the output files ie eplusout.eso -> eplusout.csv
class EnergyPlusRunner:

    def __init__(self):
        WORKING_DIR.mkdir(parents=True, exist_ok=True)

    def prepare_working_file(self):
        # Deprecated: File preparation is now strictly delegated to SimulationBuilder
        pass

    def run(self, weather_file: Path, output_directory: Path):

        output_directory.mkdir(parents=True, exist_ok=True)

        command = [
            str(ENERGYPLUS_EXE),
            "-w",
            str(weather_file),
            "-d",
            str(output_directory),
            str(WORKING_IDF),
        ]

        print("\nRunning EnergyPlus...\n")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            err_file = output_directory / "eplusout.err"
            err_content = ""
            if err_file.exists():
                try:
                    err_content = err_file.read_text(encoding="utf-8")
                except Exception:
                    pass
            
            severes = [line for line in err_content.splitlines() if "** Severe  **" in line]
            fatals = [line for line in err_content.splitlines() if "**  Fatal  **" in line]
            
            diag = f"""EnergyPlus Simulation Failed!
Exit Code: {result.returncode}
Command: {' '.join(command)}
Output Directory: {output_directory}
IDF Path: {WORKING_IDF}
Weather File: {weather_file}

Stdout:
{result.stdout}

Stderr:
{result.stderr}

Severe Errors:
{chr(10).join(severes)}

Fatal Errors:
{chr(10).join(fatals)}
"""
            print(diag)
            raise RuntimeError(diag)

        print("EnergyPlus simulation completed.")

        self.generate_csv(output_directory)

        print("CSV generation completed.")

    def generate_csv(self, output_directory: Path):

        eso_file = output_directory / "eplusout.eso"

        if not eso_file.exists():
            raise FileNotFoundError("eplusout.eso not found.")

        import sys
        sys.stdout.flush()
        sys.stderr.flush()

        subprocess.run(
            [str(READVARS_EXE)],
            cwd=output_directory,
            check=True
        )