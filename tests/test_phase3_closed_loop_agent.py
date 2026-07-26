import unittest
import json
import shutil
import tempfile
from pathlib import Path

from models.building_state import BuildingState
from models.optimization_history import OptimizationHistory
from ai.decision_schema import Decision

from tools.tool_registry import ToolRegistry
from tools.base_tool import BaseTool
from tools.comparison_tools import CompareIterationsTool
from tools.convergence_tools import ConvergenceCheckTool
from tools.performance_tools import EvaluatePerformanceTool
from tools.report_tools import ReportGenerationTool
from optimizer.closed_loop_agent import ClosedLoopAgent
from config import BASELINE_OUTPUT


class DummyTool(BaseTool):
    name = "DummyTool"
    description = "Dummy test tool"

    def execute(self, value: int = 1, **kwargs):
        return {"result_value": value * 2}


class TestPhase3ClosedLoopAgent(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.baseline_state = BuildingState(
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
        self.opt_state = BuildingState(
            timestamp="12/31 24:00:00",
            average_outdoor_temperature=0.17,
            minimum_outdoor_temperature=-5.69,
            maximum_outdoor_temperature=2.58,
            average_indoor_temperature=21.20,
            minimum_indoor_temperature=20.50,
            maximum_indoor_temperature=24.10,
            temperature_standard_deviation=0.85,
            average_cooling_rate=750.00,
            peak_cooling_rate=1800.00,
            total_cooling_energy=18000.00,
            cooling_load_factor=0.417,
            average_heating_rate=2200.00,
            peak_heating_rate=5500.00,
            total_heating_energy=52800.00,
            heating_load_factor=0.400,
            average_chiller_power=0.0,
            peak_chiller_power=0.0,
            average_plant_cooling_demand=0.0,
            peak_plant_cooling_demand=0.0,
            comfort_hours=18.0,
            discomfort_hours=6.0,
            comfort_percentage=75.0,
            hvac_operating_mode="Heating Dominant",
            temperature_trend="Stable"
        )

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_tool_registry_registration_and_execution(self):
        registry = ToolRegistry(session_dir=self.temp_dir)
        registry.register_tool(DummyTool())

        manifest = registry.get_manifest()
        self.assertIn("tool_registry_version", manifest)
        self.assertEqual(manifest["tools"][0]["name"], "DummyTool")

        res = registry.execute_tool("DummyTool", value=5)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"]["result_value"], 10)

        tool_calls_file = self.temp_dir / "tool_calls.json"
        self.assertTrue(tool_calls_file.exists())
        with open(tool_calls_file, "r", encoding="utf-8") as f:
            log_data = json.load(f)
            self.assertIn("execution_sequence", log_data)
            self.assertIn("tool_calls", log_data)
            self.assertEqual(log_data["execution_sequence"], ["DummyTool"])
            self.assertEqual(log_data["tool_calls"][0]["tool"], "DummyTool")
            self.assertIn("started_at", log_data["tool_calls"][0])
            self.assertIn("completed_at", log_data["tool_calls"][0])
            self.assertIn("duration_ms", log_data["tool_calls"][0])

    def test_compare_iterations_tool(self):
        tool = CompareIterationsTool()
        res = tool.execute(iteration=2, current_state=self.opt_state, previous_state=self.baseline_state)
        cmp = res["comparison"]

        self.assertLess(cmp.total_energy_change_pct, 0.0)
        self.assertGreater(cmp.comfort_percentage_change, 0.0)

    def test_convergence_check_tool_max_iterations(self):
        tool = ConvergenceCheckTool()
        history = OptimizationHistory()
        res = tool.execute(current_iteration=5, max_iterations=5, history=history)

        self.assertTrue(res["converged"])
        self.assertIn("Maximum iterations reached", res["reason"])

    def test_convergence_check_tool_setpoints_unchanged(self):
        tool = ConvergenceCheckTool()
        history = OptimizationHistory()

        d1 = Decision(selected_candidate_index=3, reason="r1", confidence=0.9)
        d2 = Decision(selected_candidate_index=3, reason="r2", confidence=0.9)

        history.add_record(1, self.baseline_state, d1, applied_heating=21.0, applied_cooling=24.0)
        history.add_record(2, self.opt_state, d2, applied_heating=21.0, applied_cooling=24.0)

        res = tool.execute(current_iteration=2, max_iterations=5, history=history)
        self.assertTrue(res["converged"])
        self.assertIn("Setpoints unchanged", res["reason"])

    def test_evaluate_performance_and_report_generation(self):
        eval_tool = EvaluatePerformanceTool()
        report_tool = ReportGenerationTool()

        history = OptimizationHistory()
        d = Decision(selected_candidate_index=5, reason="optimized", confidence=0.9)
        history.add_record(1, self.opt_state, d, applied_heating=21.5, applied_cooling=23.5)

        perf_res = eval_tool.execute(
            baseline_state=self.baseline_state,
            final_state=self.opt_state,
            history=history,
            runtime_ms=1200,
            convergence_reason="Setpoints unchanged for two consecutive iterations."
        )
        perf_metrics = perf_res["performance_metrics"]

        self.assertGreater(perf_metrics["total_hvac_reduction_pct"], 0.0)
        self.assertGreater(perf_metrics["comfort_change_pct"], 0.0)

        rep_res = report_tool.execute(
            output_directory=self.temp_dir,
            performance_metrics=perf_metrics,
            history=history
        )

        self.assertTrue(Path(rep_res["report_json"]).exists())
        self.assertTrue(Path(rep_res["report_md"]).exists())
        self.assertTrue(Path(rep_res["summary_csv"]).exists())

        with open(rep_res["report_json"], "r", encoding="utf-8") as f:
            r_json = json.load(f)
            self.assertIn("baseline", r_json)
            self.assertIn("optimized", r_json)
            self.assertIn("improvements", r_json)
            self.assertIn("optimization", r_json)
            self.assertIn("system_information", r_json)
            self.assertEqual(r_json["optimization"]["iterations"], 1)

    def test_closed_loop_agent_end_to_end(self):
        csv_path = BASELINE_OUTPUT / "eplusout.csv"
        if not csv_path.exists():
            self.skipTest(f"Baseline CSV not found at {csv_path}")

        agent = ClosedLoopAgent(session_name="test_closed_loop_session")
        results = agent.run_optimization(max_iterations=2, output_root=self.temp_dir)

        self.assertIsNotNone(results)
        self.assertIn("status", results)
        self.assertIn("performance_metrics", results)
        self.assertIn("reports", results)

        self.assertTrue(Path(results["reports"]["report_json"]).exists())
        self.assertTrue(Path(results["reports"]["report_md"]).exists())
        self.assertTrue(Path(results["reports"]["summary_csv"]).exists())


if __name__ == "__main__":
    unittest.main()

