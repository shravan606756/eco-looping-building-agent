import pytest
import shutil
import hashlib
from pathlib import Path

from config import ORIGINAL_IDF, WORKING_IDF
from simulation.simulation_builder import SimulationBuilder
from models.baseline_model import BaselineModel
from controller.schedule_modifier import ScheduleModifier, CompactSchedule
import re

def get_file_hash(filepath: Path) -> str:
    hasher = hashlib.md5()
    hasher.update(filepath.read_bytes())
    return hasher.hexdigest()

def test_baseline_never_changes():
    hash_before = get_file_hash(ORIGINAL_IDF)
    
    # Simulate an optimization run (or part of it)
    builder = SimulationBuilder()
    builder.build_working_idf(active_cooling_setpoint=25.0, active_heating_setpoint=22.0)
    
    hash_after = get_file_hash(ORIGINAL_IDF)
    assert hash_before == hash_after, "Baseline IDF was modified!"

def test_idempotent_schedule_modification():
    builder = SimulationBuilder()
    
    # Run 1
    builder.build_working_idf(active_cooling_setpoint=26.0, active_heating_setpoint=20.0)
    hash_run1 = get_file_hash(WORKING_IDF)
    
    # Run 2
    builder.build_working_idf(active_cooling_setpoint=26.0, active_heating_setpoint=20.0)
    hash_run2 = get_file_hash(WORKING_IDF)
    
    assert hash_run1 == hash_run2, "Consecutive modifications with identical setpoints are not byte-equivalent"

def test_changing_heating_does_not_affect_cooling():
    builder = SimulationBuilder()
    
    # Run with default cooling, modified heating
    baseline = BaselineModel()
    builder.build_working_idf(active_cooling_setpoint=baseline.initial_cooling_setpoint, active_heating_setpoint=22.5)
    
    # Check cooling schedule
    text = WORKING_IDF.read_text(encoding="utf-8")
    clg_match = re.search(r"(Schedule:Compact,\s*Clg-SetP-Sch\s*,[\s\S]*?;)", text, re.IGNORECASE)
    assert clg_match is not None
    
    clg_sch = CompactSchedule(clg_match.group(1))
    vals = clg_sch.get_all_values()
    assert min(vals) == baseline.initial_cooling_setpoint
