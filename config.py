from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")

ROOT_DIR = Path(__file__).resolve().parent

DATA_DIR = ROOT_DIR / "data"

IDF_DIR = DATA_DIR / "idf"
ORIGINAL_IDF = IDF_DIR / "original" / "5ZoneAirCooled.idf"
WORKING_DIR = IDF_DIR / "working"
WORKING_IDF = WORKING_DIR / "current.idf"

OPTIMIZED_DIR = IDF_DIR / "optimized"
OPTIMIZED_IDF = OPTIMIZED_DIR / "optimized.idf"

WEATHER_FILE = DATA_DIR / "weather" / "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw"

OUTPUT_DIR = DATA_DIR / "outputs"
BASELINE_OUTPUT = OUTPUT_DIR / "baseline"

ENERGYPLUS_HOME = Path(r"C:\EnergyPlusV26-1-0")

ENERGYPLUS_EXE = ENERGYPLUS_HOME / "energyplus.exe"

READVARS_EXE = ENERGYPLUS_HOME / "PostProcess" / "ReadVarsESO.exe"