import re
from pathlib import Path
from typing import List, Tuple
from config import ORIGINAL_IDF
from controller.schedule_modifier import CompactSchedule

class BaselineModel:
    def __init__(self, idf_path: Path = ORIGINAL_IDF):
        self.idf_path = idf_path
        self.initial_heating_setpoint = 21.0
        self.initial_cooling_setpoint = 24.0
        self.heating_occupied_indices: List[Tuple[int, int]] = []
        self.cooling_occupied_indices: List[Tuple[int, int]] = []
        self._parse()

    def _parse(self):
        try:
            text = self.idf_path.read_text(encoding="utf-8", errors="ignore")
        except FileNotFoundError:
            return

        # Parse Cooling
        clg_match = re.search(r"(Schedule:Compact,\s*Clg-SetP-Sch\s*,[\s\S]*?;)", text, re.IGNORECASE)
        if clg_match:
            clg_sch = CompactSchedule(clg_match.group(1))
            vals = clg_sch.get_all_values()
            if vals:
                self.initial_cooling_setpoint = min(vals)
                for g_idx, g in enumerate(clg_sch.groups):
                    for e_idx, e in enumerate(g.entries):
                        if abs(e.value - self.initial_cooling_setpoint) < 1e-4:
                            self.cooling_occupied_indices.append((g_idx, e_idx))
                            
        # Parse Heating
        htg_match = re.search(r"(Schedule:Compact,\s*Htg-SetP-Sch\s*,[\s\S]*?;)", text, re.IGNORECASE)
        if htg_match:
            htg_sch = CompactSchedule(htg_match.group(1))
            vals = htg_sch.get_all_values()
            if vals:
                self.initial_heating_setpoint = max(vals)
                for g_idx, g in enumerate(htg_sch.groups):
                    for e_idx, e in enumerate(g.entries):
                        if abs(e.value - self.initial_heating_setpoint) < 1e-4:
                            self.heating_occupied_indices.append((g_idx, e_idx))
