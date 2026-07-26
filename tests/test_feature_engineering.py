import unittest
from pathlib import Path
from simulation.output_parser import OutputParser
from models.building_state import BuildingState


class TestFeatureEngineering(unittest.TestCase):

    def setUp(self):
        self.csv_path = Path("data/outputs/baseline/eplusout.csv")

    def test_parser_returns_populated_building_state(self):
        if not self.csv_path.exists():
            self.skipTest(f"Sample CSV not found at {self.csv_path}")

        parser = OutputParser(str(self.csv_path))
        state = parser.latest_state(hours=24)

        self.assertIsInstance(state, BuildingState)
        self.assertIsNotNone(state.timestamp)

        # Weather assertion
        self.assertLessEqual(state.minimum_outdoor_temperature, state.average_outdoor_temperature)
        self.assertGreaterEqual(state.maximum_outdoor_temperature, state.average_outdoor_temperature)

        # Indoor comfort assertion
        self.assertLessEqual(state.minimum_indoor_temperature, state.average_indoor_temperature)
        self.assertGreaterEqual(state.maximum_indoor_temperature, state.average_indoor_temperature)
        self.assertGreaterEqual(state.temperature_standard_deviation, 0.0)

        # Cooling assertion
        self.assertGreaterEqual(state.peak_cooling_rate, state.average_cooling_rate)
        self.assertGreaterEqual(state.total_cooling_energy, 0.0)
        self.assertGreaterEqual(state.cooling_load_factor, 0.0)
        self.assertLessEqual(state.cooling_load_factor, 1.0)

        # Heating assertion
        self.assertGreaterEqual(state.peak_heating_rate, state.average_heating_rate)
        self.assertGreaterEqual(state.total_heating_energy, 0.0)
        self.assertGreaterEqual(state.heating_load_factor, 0.0)
        self.assertLessEqual(state.heating_load_factor, 1.0)

        # Chiller & Plant assertion
        self.assertGreaterEqual(state.peak_chiller_power, state.average_chiller_power)
        self.assertGreaterEqual(state.peak_plant_cooling_demand, state.average_plant_cooling_demand)

        # Comfort metrics assertion
        self.assertEqual(state.comfort_hours + state.discomfort_hours, 24.0)
        self.assertGreaterEqual(state.comfort_percentage, 0.0)
        self.assertLessEqual(state.comfort_percentage, 100.0)

        # Categorical metrics assertion
        self.assertIn(state.hvac_operating_mode, ["Heating Dominant", "Cooling Dominant", "Balanced"])
        self.assertIn(state.temperature_trend, ["Increasing", "Decreasing", "Stable"])

        # Backward compatibility assertion
        self.assertEqual(state.outdoor_temperature, state.average_outdoor_temperature)
        self.assertEqual(state.chiller_electricity, state.average_chiller_power)
        self.assertEqual(state.plant_cooling_demand, state.average_plant_cooling_demand)


if __name__ == "__main__":
    unittest.main()
