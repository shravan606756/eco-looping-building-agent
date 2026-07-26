from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ORIGINAL_IDF = ROOT / "data" / "idf" / "original" / "5ZoneAirCooled.idf"
WORKING_IDF = ROOT / "data" / "idf" / "working" / "current.idf"
WEATHER_FILE = ROOT / "data" / "weather" / "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw"
OUTPUT_DIR = ROOT / "data" / "outputs"