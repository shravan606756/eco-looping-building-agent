import unittest
from pathlib import Path
from simulation.output_parser import OutputParser
from config import BASELINE_OUTPUT


class TestOutputParser(unittest.TestCase):

    def test_output_parser_latest_state(self):
        csv_file = BASELINE_OUTPUT / "eplusout.csv"
        if not csv_file.exists():
            self.skipTest(f"Baseline CSV file not found at {csv_file}")
        parser = OutputParser(str(csv_file))
        state = parser.latest_state()
        self.assertIsNotNone(state)
        self.assertIsNotNone(state.timestamp)


if __name__ == "__main__":
    unittest.main()