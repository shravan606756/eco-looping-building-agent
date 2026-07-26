import json
from pathlib import Path
from typing import Dict, Any, Optional


class ReportReader:

    @staticmethod
    def read_report(output_dir: Path) -> Optional[Dict[str, Any]]:
        report_file = Path(output_dir) / "optimization_report.json"
        if not report_file.exists():
            return None
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    @staticmethod
    def print_executive_summary(output_dir: Path, session_dir: str = ""):
        report = ReportReader.read_report(output_dir)
        if not report:
            print("\n[WARNING] Optimization report file not found.")
            return

        opt = report.get("optimization", {})
        imp = report.get("improvements", {})
        base = report.get("baseline", {})
        optm = report.get("optimized", {})
        sys_info = report.get("system_information", {})

        print("\n==================================================")
        print("  HONEYWELL ECO-LOOP OPTIMIZATION EXECUTIVE SUMMARY  ")
        print("==================================================")
        print(f"Project             : {sys_info.get('project', 'Honeywell Eco-Loop')}")
        print(f"Simulation Engine   : {sys_info.get('simulation_engine', 'EnergyPlus')}")
        print(f"LLM Reasoning Engine: Groq {sys_info.get('llm_model', 'Llama 3.3 70B')}")
        print(f"Iterations Completed: {opt.get('iterations', 0)}")
        print(f"Total Runtime       : {opt.get('runtime_seconds', 0.0)} seconds")
        print(f"Convergence Reason  : {opt.get('convergence_reason', 'N/A')}")
        print("--------------------------------------------------")
        print("Key Performance Metrics:")
        print(f"  • Total HVAC Energy Reduction : {imp.get('total_hvac_energy_reduction_pct', 0.0):.2f}%")
        print(f"  • Heating Energy Reduction    : {imp.get('heating_energy_reduction_pct', 0.0):.2f}%")
        print(f"  • Cooling Energy Change       : {imp.get('cooling_energy_change_pct', 0.0):+.2f}%")
        print(f"  * Comfort Change              : {imp.get('comfort_change_pct', 0.0):+.1f}% (Baseline: {base.get('comfort_percentage', 0)}% -> Optimized: {optm.get('comfort_percentage', 0)}%)")

        if 'peak_demand_reduction_pct' in imp:
            print(f"  • Peak Demand Reduction       : {imp.get('peak_demand_reduction_pct', 0.0):.2f}%")
        else:
            print(f"  • Peak Demand Change          : {imp.get('peak_demand_change_pct', 0.0):+.2f}%")

        print("--------------------------------------------------")
        print("Final Optimized Setpoints:")
        print(f"  • Cooling Setpoint     : {opt.get('final_cooling_setpoint', 24.0)} °C")
        print(f"  • Heating Setpoint     : {opt.get('final_heating_setpoint', 20.0)} °C")
        print("--------------------------------------------------")
        print("Artifact Outputs:")
        print(f"  • Report (JSON) : {output_dir / 'optimization_report.json'}")
        print(f"  • Report (MD)   : {output_dir / 'optimization_report.md'}")
        print(f"  • Summary (CSV) : {output_dir / 'optimization_summary.csv'}")
        if session_dir:
            print(f"  • Session Logs  : {session_dir}")
        print("==================================================\n")
