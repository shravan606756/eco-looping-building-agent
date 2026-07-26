from pathlib import Path
from typing import Dict, Any, List

from config import (
    ORIGINAL_IDF,
    WEATHER_FILE,
    ENERGYPLUS_EXE,
    READVARS_EXE,
    GROQ_API_KEY,
    OUTPUT_DIR,
    WORKING_DIR,
)


class EnvironmentValidator:

    @staticmethod
    def validate_environment() -> Dict[str, Any]:
        errors: List[str] = []
        checks: List[Dict[str, str]] = []

        if ORIGINAL_IDF.exists():
            checks.append({"item": "Original IDF File", "status": "[OK]", "path": str(ORIGINAL_IDF)})
        else:
            errors.append(f"Original IDF file missing at: {ORIGINAL_IDF}")

        if WEATHER_FILE.exists():
            checks.append({"item": "Weather File (EPW)", "status": "[OK]", "path": str(WEATHER_FILE)})
        else:
            errors.append(f"Weather file missing at: {WEATHER_FILE}")

        if ENERGYPLUS_EXE.exists():
            checks.append({"item": "EnergyPlus Executable", "status": "[OK]", "path": str(ENERGYPLUS_EXE)})
        else:
            errors.append(f"EnergyPlus executable missing at: {ENERGYPLUS_EXE}")

        if READVARS_EXE.exists():
            checks.append({"item": "ReadVarsESO Executable", "status": "[OK]", "path": str(READVARS_EXE)})
        else:
            errors.append(f"ReadVarsESO executable missing at: {READVARS_EXE}")

        if GROQ_API_KEY and len(GROQ_API_KEY) > 5:
            checks.append({"item": "Groq API Key", "status": "[OK]", "path": "Environment .env"})
        else:
            errors.append("GROQ_API_KEY missing or invalid in .env")


        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        WORKING_DIR.mkdir(parents=True, exist_ok=True)

        return {
            "valid": len(errors) == 0,
            "checks": checks,
            "errors": errors
        }
