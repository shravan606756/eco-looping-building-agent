import unittest
import shutil
from pathlib import Path
from controller.schedule_modifier import CompactSchedule, ScheduleModifier
from config import WORKING_IDF, ORIGINAL_IDF


class TestScheduleModifierSemantic(unittest.TestCase):

    def setUp(self):
        if ORIGINAL_IDF.exists():
            shutil.copy2(ORIGINAL_IDF, WORKING_IDF)

    def test_custom_schedule_parsing_and_semantic_update(self):
        sample_schedule = """
  Schedule:Compact,
    Custom-Htg-Sch,
    Temperature,
    Through: 12/31,
    For: WeekDays,
    Until: 7:30,15.0,
    Until: 17:30,22.0,
    Until: 24:00,15.0,
    For: WeekEnds,
    Until: 24:00,15.0;
"""
        sch = CompactSchedule(sample_schedule)
        self.assertEqual(sch.name, "Custom-Htg-Sch")
        self.assertEqual(len(sch.groups), 2)

        updated = sch.update_occupied_setpoint(target_value=21.0, is_heating=True)

        self.assertIn("Until: 17:30,21.0", updated)
        self.assertIn("Until: 7:30,15.0", updated)
        self.assertIn("Until: 24:00,15.0", updated)

    def test_cooling_schedule_semantic_update(self):
        sample_schedule = """
  Schedule:Compact,
    Custom-Clg-Sch,
    Temperature,
    Through: 12/31,
    For: WeekDays,
    Until: 8:00,30.0,
    Until: 18:30,24.0,
    Until: 24:00,30.0,
    For: WeekEnds,
    Until: 24:00,30.0;
"""
        sch = CompactSchedule(sample_schedule)
        updated = sch.update_occupied_setpoint(target_value=23.0, is_heating=False)

        self.assertIn("Until: 18:30,23.0", updated)
        self.assertIn("Until: 8:00,30.0", updated)
        self.assertIn("Until: 24:00,30.0", updated)

    def test_split_shift_schedule(self):
        split_shift_schedule = """
  Schedule:Compact,
    Split-Shift-Htg,
    Temperature,
    Through: 12/31,
    For: WeekDays,
    Until: 7:00,16.0,
    Until: 12:00,22.0,
    Until: 16:00,18.0,
    Until: 21:00,22.0,
    Until: 24:00,16.0;
"""
        sch = CompactSchedule(split_shift_schedule)
        updated = sch.update_occupied_setpoint(target_value=20.5, is_heating=True)

        # Both morning shift (Until: 12:00) and evening shift (Until: 21:00) match occupied max (22.0)
        self.assertIn("Until: 12:00,20.5", updated)
        self.assertIn("Until: 21:00,20.5", updated)
        # Night (16.0) and mid-day setback (18.0) remain intact
        self.assertIn("Until: 7:00,16.0", updated)
        self.assertIn("Until: 16:00,18.0", updated)

    def test_warmup_preconditioning_schedule(self):
        warmup_schedule = """
  Schedule:Compact,
    WarmUp-Htg-Sch,
    Temperature,
    Through: 12/31,
    For: WeekDays,
    Until: 6:00,15.0,
    Until: 8:00,18.5,
    Until: 18:00,22.0,
    Until: 24:00,15.0;
"""
        sch = CompactSchedule(warmup_schedule)
        updated = sch.update_occupied_setpoint(target_value=21.0, is_heating=True)

        self.assertIn("Until: 18:00,21.0", updated)
        self.assertIn("Until: 6:00,15.0", updated)
        self.assertIn("Until: 8:00,18.5", updated)
        self.assertIn("Until: 24:00,15.0", updated)

    def test_seasonal_multi_through_schedule(self):
        seasonal_schedule = """
  Schedule:Compact,
    Seasonal-Clg-Sch,
    Temperature,
    Through: 4/30,
    For: AllDays,
    Until: 24:00,28.0,
    Through: 10/31,
    For: WeekDays,
    Until: 7:00,29.0,
    Until: 19:00,24.0,
    Until: 24:00,29.0,
    Through: 12/31,
    For: AllDays,
    Until: 24:00,28.0;
"""
        sch = CompactSchedule(seasonal_schedule)
        updated = sch.update_occupied_setpoint(target_value=23.5, is_heating=False)

        self.assertIn("Until: 19:00,23.5", updated)
        self.assertIn("Until: 7:00,29.0", updated)
        self.assertIn("Until: 24:00,28.0", updated)

    def test_original_idf_schedule_modifier(self):
        if not WORKING_IDF.exists():
            self.skipTest(f"WORKING_IDF not found at {WORKING_IDF}")

        modifier = ScheduleModifier(str(WORKING_IDF))
        modifier.update_setpoints(cooling=24.0, heating=21.0)

        text = WORKING_IDF.read_text(encoding="utf-8")

        self.assertIn("Until: 20:00,21.0", text)
        self.assertIn("Until: 20:00,24.0", text)
        self.assertIn("Until: 6:00,16.7", text)
        self.assertIn("Until: 6:00,29.4", text)


if __name__ == "__main__":
    unittest.main()
