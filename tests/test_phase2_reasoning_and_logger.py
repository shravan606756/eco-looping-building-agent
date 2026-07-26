import unittest
import json
import shutil
import tempfile
from pathlib import Path

from models.building_state import BuildingState
from models.optimization_context import OptimizationContext
from ai.prompt_builder import load_system_prompt, build_user_prompt, build_user_prompt_sections
from ai.decision_schema import Decision
from ai.agent import BuildingOptimizationAgent
from utils.logger import IterationLogger
from config import BASELINE_OUTPUT


class TestPhase2ReasoningAndLogger(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.sample_state = BuildingState(
            timestamp="12/31 24:00:00",
            average_outdoor_temperature=0.17,
            minimum_outdoor_temperature=-5.69,
            maximum_outdoor_temperature=2.58,
            average_indoor_temperature=20.68,
            minimum_indoor_temperature=19.99,
            maximum_indoor_temperature=23.85,
            temperature_standard_deviation=1.01,
            average_cooling_rate=795.16,
            peak_cooling_rate=1954.08,
            total_cooling_energy=19083.81,
            cooling_load_factor=0.407,
            average_heating_rate=2815.74,
            peak_heating_rate=6369.92,
            total_heating_energy=67577.84,
            heating_load_factor=0.442,
            average_chiller_power=0.0,
            peak_chiller_power=0.0,
            average_plant_cooling_demand=0.0,
            peak_plant_cooling_demand=0.0,
            comfort_hours=9.0,
            discomfort_hours=15.0,
            comfort_percentage=37.5,
            hvac_operating_mode="Heating Dominant",
            temperature_trend="Stable"
        )
        self.sample_context = OptimizationContext(
            iteration=1,
            current_state=self.sample_state,
            active_heating_setpoint=20.0,
            active_cooling_setpoint=24.0,
            previous_decision=None,
            previous_state=None,
            iteration_comparison=None,
            engineering_assessment=None
        )

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_optimization_context_dataclass(self):
        context_dict = self.sample_context.__dict__
        self.assertEqual(context_dict["iteration"], 1)
        self.assertEqual(context_dict["active_heating_setpoint"], 20.0)

    def test_system_prompt_engineering_persona_and_constraints(self):
        sys_prompt = load_system_prompt()
        self.assertIn("expert Building Energy Management and HVAC Optimization Engineer", sys_prompt)
        self.assertIn("Priority 1", sys_prompt)
        self.assertIn("Priority 2", sys_prompt)
        self.assertIn("18.0°C to 24.0°C", sys_prompt)
        self.assertIn("22.0°C to 28.0°C", sys_prompt)
        self.assertIn("Cooling Setpoint >= Heating Setpoint", sys_prompt)

    def test_prompt_builder_with_and_without_context(self):
        prompt_no_ctx = build_user_prompt(self.sample_state)
        self.assertIn("Building Performance Summary", prompt_no_ctx)
        self.assertIn("Initial Baseline Iteration", prompt_no_ctx)

        prompt_with_ctx, sections = build_user_prompt_sections(self.sample_state, self.sample_context)
        self.assertIn("Previous Optimization Result Context (Iteration 1)", prompt_with_ctx)
        self.assertIn("Active Heating Setpoint: 20.0 °C", prompt_with_ctx)

        self.assertIn("building_summary", sections)
        self.assertIn("previous_context", sections)
        self.assertIn("optimization_objective", sections)
        self.assertIn("constraints", sections)
        self.assertIn("decision_strategy", sections)

    def test_iteration_logger_session_and_artifacts(self):
        logger = IterationLogger(base_log_dir=self.temp_dir, session_name="test_session")
        decision = Decision(
            selected_candidate_index=1,
            reason="Gradual 1°C increase in heating setpoint to improve comfort.",
            confidence=0.92
        )

        _, sections = build_user_prompt_sections(self.sample_state, self.sample_context)
        prompt_str = build_user_prompt(self.sample_state, self.sample_context)

        success = logger.log_iteration(
            iteration=1,
            building_state=self.sample_state,
            prompt=prompt_str,
            prompt_sections=sections,
            raw_response=json.dumps(decision.model_dump()),
            decision=decision,
            system_prompt=load_system_prompt(),
            metadata={"response_time_ms": 450}
        )
        self.assertTrue(success)

        iter_dir = self.temp_dir / "test_session" / "iteration_001"
        self.assertTrue(iter_dir.exists())

        required_files = [
            "building_state.json",
            "prompt.txt",
            "prompt.json",
            "llm_response.json",
            "decision.json",
            "metadata.json"
        ]
        for fname in required_files:
            file_path = iter_dir / fname
            self.assertTrue(file_path.exists(), f"Log file {fname} missing.")
            self.assertGreater(file_path.stat().st_size, 0)

        # Finalize session
        summary_success = logger.finalize_session()
        self.assertTrue(summary_success)

        summary_path = self.temp_dir / "test_session" / "summary.json"
        self.assertTrue(summary_path.exists())
        with open(summary_path, "r", encoding="utf-8") as f:
            sum_data = json.load(f)
            self.assertEqual(sum_data["iterations"], 1)

    def test_logger_fault_tolerance(self):
        dummy_file = self.temp_dir / "dummy_file.txt"
        dummy_file.write_text("not a directory", encoding="utf-8")

        logger = IterationLogger(base_log_dir=dummy_file, session_name="failed_session")

        decision = Decision(selected_candidate_index=2, reason="test", confidence=0.9)
        success = logger.log_iteration(
            iteration=1,
            building_state=self.sample_state,
            prompt="prompt",
            prompt_sections={},
            raw_response="{}",
            decision=decision
        )
        self.assertFalse(success)


    def test_end_to_end_agent_with_phase2_reasoning_and_logging(self):
        csv_path = BASELINE_OUTPUT / "eplusout.csv"
        if not csv_path.exists():
            self.skipTest(f"Baseline CSV not found at {csv_path}")

        agent = BuildingOptimizationAgent()
        logger = IterationLogger(base_log_dir=self.temp_dir, session_name="agent_test_session")

        decision = agent.decide(
            state=self.sample_state,
            context=self.sample_context,
            iteration=1,
            logger=logger,
            debug=True
        )

        self.assertIsInstance(decision, Decision)
        self.assertGreaterEqual(decision.selected_candidate_index, 1)
        self.assertLessEqual(decision.selected_candidate_index, 9)

        # Confirm reasoning contains engineering details
        self.assertGreater(len(decision.reason), 20)

        # Confirm iteration log artifact exists
        iter_dir = self.temp_dir / "agent_test_session" / "iteration_001"
        self.assertTrue(iter_dir.exists())
        self.assertTrue((iter_dir / "decision.json").exists())


if __name__ == "__main__":
    unittest.main()
