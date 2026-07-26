import unittest
from pathlib import Path
from simulation.output_parser import OutputParser
from config import BASELINE_OUTPUT


class TestBuildingState(unittest.TestCase):

    def test_building_state_parser(self):
        csv_file = BASELINE_OUTPUT / "eplusout.csv"
        if not csv_file.exists():
            self.skipTest(f"Baseline CSV file not found at {csv_file}")
        parser = OutputParser(str(csv_file))
        state = parser.latest_state()
        self.assertIsNotNone(state)
        self.assertGreater(state.average_indoor_temperature, 0.0)


if __name__ == "__main__":
    unittest.main()