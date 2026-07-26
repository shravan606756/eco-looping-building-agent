import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class UntilEntry:
    time_str: str
    value: float
    raw_line: str


@dataclass
class DayProfileGroup:
    day_types: List[str]
    entries: List[UntilEntry] = field(default_factory=list)


class CompactSchedule:

    def __init__(self, raw_block: str):
        self.raw_block = raw_block
        self.name: str = ""
        self.type_limits: str = ""
        self.groups: List[DayProfileGroup] = []
        self._parse()

    def _parse(self):
        lines = [line.strip() for line in self.raw_block.splitlines() if line.strip()]
        if not lines:
            return

        header_text = "\n".join(lines)
        name_match = re.search(r"Schedule:Compact\s*,\s*([^,;]+)\s*,\s*([^,;]+)", header_text, re.IGNORECASE)
        if name_match:
            self.name = name_match.group(1).strip()
            self.type_limits = name_match.group(2).strip()

        current_day_types: List[str] = []
        current_group: Optional[DayProfileGroup] = None

        for line in lines:
            for_match = re.search(r"For:\s*([^,;!]+)", line, re.IGNORECASE)
            if for_match:
                day_types_str = for_match.group(1).strip()
                current_day_types = [dt.strip() for dt in day_types_str.split() if dt.strip()]
                current_group = DayProfileGroup(day_types=current_day_types, entries=[])
                self.groups.append(current_group)
                continue

            until_match = re.search(r"Until:\s*([\d:]+)\s*,\s*(-?\d+(?:\.\d+)?)", line, re.IGNORECASE)
            if until_match and current_group is not None:
                time_str = until_match.group(1).strip()
                val = float(until_match.group(2))
                current_group.entries.append(UntilEntry(time_str=time_str, value=val, raw_line=line))

    def get_all_values(self) -> List[float]:
        vals = []
        for g in self.groups:
            for e in g.entries:
                vals.append(e.value)
        return vals


    def update_occupied_setpoint(self, target_value: float, occupied_indices: List[Tuple[int, int]]) -> str:
        if not occupied_indices:
            return self.raw_block

        modified_block = self.raw_block

        for g_idx, e_idx in occupied_indices:
            if g_idx < len(self.groups) and e_idx < len(self.groups[g_idx].entries):
                e = self.groups[g_idx].entries[e_idx]
                # Match exact Until: HH:MM, value in line
                line_pattern = rf"(Until:\s*{re.escape(e.time_str)}\s*,\s*){re.escape(str(e.value))}(\s*[,;!]?)"
                modified_block = re.sub(
                    line_pattern,
                    rf"\g<1>{target_value:.1f}\g<2>",
                    modified_block,
                    count=1
                )

        return modified_block


class ScheduleModifier:

    def __init__(self, idf_path: str):
        self.idf_path = Path(idf_path)

    def update_setpoints(self, cooling: float, heating: float, cooling_indices: List[Tuple[int, int]], heating_indices: List[Tuple[int, int]]):
        text = self.idf_path.read_text(encoding="utf-8")

        text = self._update_schedule_block(text, "Clg-SetP-Sch", cooling, cooling_indices)
        text = self._update_schedule_block(text, "Htg-SetP-Sch", heating, heating_indices)

        self.idf_path.write_text(text, encoding="utf-8")

    def _update_schedule_block(self, text: str, schedule_name: str, target_value: float, indices: List[Tuple[int, int]]) -> str:
        pattern = (
            rf"(Schedule:Compact,\s*"
            rf"{re.escape(schedule_name)}\s*,[\s\S]*?;\s*)"
        )

        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            raise ValueError(f"Schedule '{schedule_name}' not found in IDF.")

        raw_block = match.group(1)
        compact_sch = CompactSchedule(raw_block)
        modified_block = compact_sch.update_occupied_setpoint(target_value=target_value, occupied_indices=indices)

        return text.replace(raw_block, modified_block)