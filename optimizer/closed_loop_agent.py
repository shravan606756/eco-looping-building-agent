import time
import warnings
from pathlib import Path
from typing import Dict, Any, Optional

from simulation.energyplus_runner import EnergyPlusRunner
from simulation.simulation_builder import SimulationBuilder
from controller.schedule_modifier import ScheduleModifier
from ai.agent import BuildingOptimizationAgent
from models.building_state import BuildingState
from models.optimization_history import OptimizationHistory
from models.optimization_status import OptimizationStatus
from models.optimization_context import OptimizationContext
from models.baseline_model import BaselineModel
from controller.context_assembler import ContextAssembler

from utils.logger import IterationLogger
from config import BASELINE_OUTPUT, OUTPUT_DIR, WORKING_IDF

from tools.tool_registry import ToolRegistry
from tools.simulation_tool import RunSimulationTool
from tools.parser_tools import ParseResultsTool
from tools.feature_tools import FeatureEngineeringTool
from tools.idf_tool import ModifyScheduleTool, PrepareWorkingFileTool

from tools.comparison_tools import CompareIterationsTool
from tools.convergence_tools import ConvergenceCheckTool
from tools.performance_tools import EvaluatePerformanceTool
from tools.report_tools import ReportGenerationTool


class ClosedLoopAgent:

    def __init__(self, session_name: Optional[str] = None):
        self.runner = EnergyPlusRunner()
        self.agent = BuildingOptimizationAgent()
        self.modifier = ScheduleModifier(WORKING_IDF)
        self.history = OptimizationHistory()

        self.logger = IterationLogger(session_name=session_name)
        self.registry = ToolRegistry(session_dir=self.logger.session_dir)
        self.builder = SimulationBuilder()
        self.baseline_model = self.builder.baseline

        # Register custom tools
        self.registry.register_tool(PrepareWorkingFileTool(self.builder))
        self.registry.register_tool(RunSimulationTool(self.runner))
        self.registry.register_tool(ParseResultsTool())
        self.registry.register_tool(FeatureEngineeringTool())
        self.registry.register_tool(ModifyScheduleTool(self.modifier))
        self.registry.register_tool(CompareIterationsTool())
        self.registry.register_tool(ConvergenceCheckTool())
        self.registry.register_tool(EvaluatePerformanceTool())
        self.registry.register_tool(ReportGenerationTool())

    def run_optimization(
        self,
        max_iterations: int = 5,
        output_root: Path = OUTPUT_DIR
    ) -> Dict[str, Any]:

        start_time = time.perf_counter()

        # 1. Baseline Run
        print("\n==========================================")
        print("Starting Baseline Simulation")
        print("==========================================")
        
        # Use baseline setpoints for the baseline run
        baseline_heating = self.baseline_model.initial_heating_setpoint
        baseline_cooling = self.baseline_model.initial_cooling_setpoint
        print(f"Extracted Baseline from IDF -> Heating: {baseline_heating:.1f}°C | Cooling: {baseline_cooling:.1f}°C")
        
        prep_res = self.registry.execute_tool(
            "PrepareWorkingFileTool",
            active_cooling_setpoint=baseline_cooling,
            active_heating_setpoint=baseline_heating
        )
        if prep_res["status"] == "error":
            raise RuntimeError(f"PrepareWorkingFileTool failed: {prep_res.get('error')}")
        
        base_dir = output_root / "baseline"
        sim_res = self.registry.execute_tool("RunSimulationTool", output_directory=base_dir)
        if sim_res["status"] == "error":
            raise RuntimeError(f"Baseline simulation failed: {sim_res.get('error')}")

        parse_res = self.registry.execute_tool("ParseResultsTool", csv_path=base_dir / "eplusout.csv")
        baseline_state: BuildingState = parse_res["result"]["building_state"]

        self.registry.execute_tool("FeatureEngineeringTool", building_state=baseline_state)

        # 2. Closed-Loop Optimization Iterations
        prev_state: Optional[BuildingState] = None
        convergence_reason = f"Completed maximum specified iterations ({max_iterations})."
        
        # Initialize Candidate Cache
        candidate_cache: Dict[tuple[float, float], BuildingState] = {}
        
        # Add baseline state to cache
        candidate_cache[(baseline_heating, baseline_cooling)] = baseline_state

        for iteration in range(1, max_iterations + 1):
            print(f"\n==========================================")
            print(f"Closed-Loop Iteration {iteration} of {max_iterations}")
            print("==========================================")

            iter_dir = output_root / f"iteration_{iteration}"
            iter_dir.mkdir(parents=True, exist_ok=True)

            last_record = self.history.get_last_record()
            active_heating = last_record.heating_setpoint if last_record else baseline_heating
            active_cooling = last_record.cooling_setpoint if last_record else baseline_cooling

            print(f"[Iteration {iteration} BEGIN] Current Operating Point -> Heating: {active_heating:.1f}°C | Cooling: {active_cooling:.1f}°C")

            # Phase 1: Exploration (Generate Neighborhood)
            candidates_to_evaluate = []
            deltas = [-0.5, 0.0, 0.5]
            
            for hd in deltas:
                for cd in deltas:
                    h = active_heating + hd
                    c = active_cooling + cd
                    
                    # Validate constraints: deadband and absolute bounds
                    if not (18.0 <= h <= 24.0) or not (22.0 <= c <= 28.0):
                        continue
                    if c < h + 1.0:
                        continue
                        
                    candidates_to_evaluate.append({"heating": h, "cooling": c})

            print(f"Generated {len(candidates_to_evaluate)} valid candidates in the neighborhood.")

            # Phase 2: Simulation (Evaluate Candidates)
            evaluated_candidates = []
            for i, cand in enumerate(candidates_to_evaluate, 1):
                h, c = cand["heating"], cand["cooling"]
                cache_key = (h, c)
                
                if cache_key in candidate_cache:
                    cand_state = candidate_cache[cache_key]
                    print(f"\n[Iteration {iteration}]")
                    print(f"Candidate {i}")
                    print(f"Heating = {h:.1f}°C")
                    print(f"Cooling = {c:.1f}°C")
                    print(f"Output: {iter_dir / f'cand_{i}'}")
                    print(f"Working IDF: {WORKING_IDF}")
                    print(f"Thermostat written: Heating={h:.1f}°C, Cooling={c:.1f}°C")
                    print(f"Schedules Modified: Htg-SetP-Sch, Clg-SetP-Sch")
                    print(f"Cache Used: True\n")
                else:
                    cand_dir = iter_dir / f"cand_{i}"
                    
                    print(f"\n[Iteration {iteration}]")
                    print(f"Candidate {i}")
                    print(f"Heating = {h:.1f}°C")
                    print(f"Cooling = {c:.1f}°C")
                    print(f"Output: {cand_dir}")
                    print(f"Working IDF: {WORKING_IDF}")
                    print(f"Thermostat written: Heating={h:.1f}°C, Cooling={c:.1f}°C")
                    print(f"Schedules Modified: Htg-SetP-Sch, Clg-SetP-Sch")
                    print(f"Cache Used: False\n")

                    prep_res = self.registry.execute_tool(
                        "PrepareWorkingFileTool",
                        active_cooling_setpoint=c,
                        active_heating_setpoint=h
                    )
                    
                    sim_res = self.registry.execute_tool("RunSimulationTool", output_directory=cand_dir)
                    if sim_res["status"] == "error":
                        import logging
                        logger = logging.getLogger(__name__)
                        exc = sim_res.get("exception_obj")
                        print(f"\nCandidate {i}\nHeating {h:.1f}°C\nCooling {c:.1f}°C\nEnergyPlus Error: {sim_res.get('error')}")
                        if exc:
                            logger.exception("Simulation failed with exception:", exc_info=exc)
                        else:
                            logger.error(f"Simulation failed: {sim_res.get('error')}")
                        raise RuntimeError(f"Iteration {iteration} Candidate {i} simulation failed.\nReason: {sim_res.get('error')}")
                        
                    parse_res = self.registry.execute_tool("ParseResultsTool", csv_path=cand_dir / "eplusout.csv")
                    if parse_res["status"] == "error":
                        import logging
                        logger = logging.getLogger(__name__)
                        exc = parse_res.get("exception_obj")
                        print(f"\nCandidate {i}\nHeating {h:.1f}°C\nCooling {c:.1f}°C\nParse Error: {parse_res.get('error')}")
                        if exc:
                            logger.exception("Parsing failed with exception:", exc_info=exc)
                        else:
                            logger.error(f"Parsing failed: {parse_res.get('error')}")
                        raise RuntimeError(f"Iteration {iteration} Candidate {i} parse failed.\nReason: {parse_res.get('error')}")
                        
                    cand_state = parse_res["result"]["building_state"]
                    candidate_cache[cache_key] = cand_state
                    
                cand["state"] = cand_state
                evaluated_candidates.append(cand)
                
            if not evaluated_candidates:
                convergence_reason = "No valid candidates could be evaluated."
                break
                
            # Current state corresponds to the active setpoints
            current_state = candidate_cache.get((active_heating, active_cooling), prev_state or baseline_state)

            # Step C: Feature Engineering
            self.registry.execute_tool("FeatureEngineeringTool", building_state=current_state)

            # Step D: Compare Iterations
            cmp_res = self.registry.execute_tool(
                "CompareIterationsTool",
                iteration=iteration,
                current_state=current_state,
                previous_state=prev_state or baseline_state
            )
            iteration_comparison = cmp_res["result"]["comparison"]

            # Step E: Load Context & Execute LLM Agent Decision
            previous_decision = last_record.decision if last_record else None

            opt_context = ContextAssembler.build(
                iteration=iteration,
                current_state=current_state,
                previous_state=prev_state or baseline_state,
                iteration_comparison=iteration_comparison,
                previous_decision=previous_decision,
                active_heating_setpoint=active_heating,
                active_cooling_setpoint=active_cooling
            )

            # Phase 3: AI Reasoning
            decision = self.agent.decide(
                state=current_state,
                candidates=evaluated_candidates,
                context=opt_context,
                iteration=iteration,
                logger=self.logger,
                debug=True
            )

            # Extract chosen candidate
            selected_idx = decision.selected_candidate_index - 1
            if selected_idx < 0 or selected_idx >= len(evaluated_candidates):
                warnings.warn(f"LLM returned invalid index {decision.selected_candidate_index}. Defaulting to Candidate 1.")
                selected_idx = 0
                
            chosen_candidate = evaluated_candidates[selected_idx]
            safe_heating = chosen_candidate["heating"]
            safe_cooling = chosen_candidate["cooling"]
            chosen_state = chosen_candidate["state"]

            # Record iteration history
            self.history.add_record(
                iteration=iteration, 
                state=current_state, 
                decision=decision,
                applied_heating=safe_heating,
                applied_cooling=safe_cooling
            )
            print(f"[Iteration {iteration} END] New Setpoints for next iter -> Heating: {safe_heating:.1f}°C | Cooling: {safe_cooling:.1f}°C")
            prev_state = current_state

            # Step G: Convergence Check
            conv_res = self.registry.execute_tool(
                "ConvergenceCheckTool",
                current_iteration=iteration,
                max_iterations=max_iterations,
                history=self.history
            )

            if conv_res["status"] == "success" and conv_res["result"]["converged"]:
                convergence_reason = conv_res["result"]["reason"]
                print(f"\n[CONVERGENCE DETECTED]: {convergence_reason}")
                break

        # 3. Final Performance Evaluation & Report Generation
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        final_state = self.history.records[-1].building_state if self.history.records else baseline_state

        perf_res = self.registry.execute_tool(
            "EvaluatePerformanceTool",
            baseline_state=baseline_state,
            final_state=final_state,
            history=self.history,
            runtime_ms=elapsed_ms,
            convergence_reason=convergence_reason
        )
        perf_metrics = perf_res["result"]["performance_metrics"]

        report_res = self.registry.execute_tool(
            "ReportGenerationTool",
            output_directory=output_root,
            performance_metrics=perf_metrics,
            history=self.history
        )

        status = OptimizationStatus(
            current_iteration=len(self.history.records),
            max_iterations=max_iterations,
            converged=True,
            convergence_reason=convergence_reason,
            current_comfort_pct=final_state.comfort_percentage,
            current_total_energy_wh=final_state.total_heating_energy + final_state.total_cooling_energy,
            overall_energy_savings_pct=perf_metrics.get("total_hvac_reduction_pct", 0.0),
            overall_comfort_change_pct=perf_metrics.get("comfort_change_pct", 0.0),
            runtime_ms=elapsed_ms
        )

        from config import OPTIMIZED_DIR, OPTIMIZED_IDF
        import shutil
        OPTIMIZED_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(WORKING_IDF, OPTIMIZED_IDF)

        self.logger.finalize_session(summary_data=status.to_dict())

        return {
            "status": status.to_dict(),
            "performance_metrics": perf_metrics,
            "reports": report_res["result"],
            "session_dir": str(self.logger.session_dir) if self.logger.session_dir else ""
        }
