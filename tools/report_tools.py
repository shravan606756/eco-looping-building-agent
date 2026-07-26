import csv
import json
from pathlib import Path
from typing import Dict, Any
from tools.base_tool import BaseTool
from models.optimization_history import OptimizationHistory
from tools.tool_registry import TOOL_REGISTRY_VERSION


class ReportGenerationTool(BaseTool):
    name = "ReportGenerationTool"
    description = "Generates dashboard-ready quantitative performance reports (optimization_report.json, optimization_report.md, optimization_summary.csv)."

    def execute(
        self,
        output_directory: Path,
        performance_metrics: Dict[str, Any],
        history: OptimizationHistory,
        **kwargs
    ) -> Dict[str, Any]:

        out_dir = Path(output_directory)
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = out_dir / "optimization_report.json"
        md_path = out_dir / "optimization_report.md"
        csv_path = out_dir / "optimization_summary.csv"

        p = performance_metrics
        runtime_sec = round(p.get("runtime_ms", 0) / 1000.0, 2)

        pk_reduction = p.get("peak_demand_reduction_pct", 0.0)
        if pk_reduction > 0:
            pk_key = "peak_demand_reduction_pct"
            pk_val = pk_reduction
            pk_label = "Peak Demand Reduction"
            pk_str = f"{pk_val:.2f}%"
        else:
            pk_key = "peak_demand_change_pct"
            pk_val = -pk_reduction
            pk_label = "Peak Demand Change"
            pk_str = f"{pk_val:+.2f}%"

        report_json_data = {
            "title": "Honeywell Closed-Loop Autonomous HVAC Optimization Report",
            "baseline": {
                "heating_energy_wh": p.get("baseline_heating_energy_wh", 0.0),
                "cooling_energy_wh": p.get("baseline_cooling_energy_wh", 0.0),
                "total_hvac_energy_wh": p.get("baseline_total_energy_wh", 0.0),
                "comfort_percentage": p.get("baseline_comfort_pct", 0.0),
                "peak_heating_rate_w": p.get("baseline_peak_heating_rate_w", 0.0),
                "peak_cooling_rate_w": p.get("baseline_peak_cooling_rate_w", 0.0)
            },
            "optimized": {
                "heating_energy_wh": p.get("optimized_heating_energy_wh", 0.0),
                "cooling_energy_wh": p.get("optimized_cooling_energy_wh", 0.0),
                "total_hvac_energy_wh": p.get("optimized_total_energy_wh", 0.0),
                "comfort_percentage": p.get("optimized_comfort_pct", 0.0),
                "peak_heating_rate_w": p.get("optimized_peak_heating_rate_w", 0.0),
                "peak_cooling_rate_w": p.get("optimized_peak_cooling_rate_w", 0.0)
            },
            "improvements": {
                "heating_energy_reduction_pct": p.get("heating_reduction_pct", 0.0),
                "cooling_energy_change_pct": p.get("cooling_change_pct", 0.0),
                "total_hvac_energy_reduction_pct": p.get("total_hvac_reduction_pct", 0.0),
                "comfort_change_pct": p.get("comfort_change_pct", 0.0),
                pk_key: pk_val
            },
            "optimization": {
                "iterations": p.get("total_iterations", 0),
                "runtime_seconds": runtime_sec,
                "convergence_reason": p.get("convergence_reason", ""),
                "final_heating_setpoint": p.get("final_heating_setpoint", 20.0),
                "final_cooling_setpoint": p.get("final_cooling_setpoint", 24.0)
            },
            "system_information": {
                "project": "Honeywell Eco-Loop Building Agents",
                "simulation_engine": "EnergyPlus 26.1.0",
                "llm_model": "llama-3.3-70b-versatile",
                "optimization_window_hours": 24,
                "tool_registry_version": TOOL_REGISTRY_VERSION
            },
            "iteration_records": [
                {
                    "iteration": rec.iteration,
                    "heating_setpoint": rec.heating_setpoint,
                    "cooling_setpoint": rec.cooling_setpoint,
                    "comfort_percentage": rec.comfort_percentage,
                    "total_heating_energy_wh": rec.total_heating_energy,
                    "total_cooling_energy_wh": rec.total_cooling_energy,
                    "hvac_mode": rec.hvac_mode,
                    "temperature_trend": rec.temperature_trend,
                    "reason": rec.decision.reason
                }
                for rec in history.records
            ]
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_json_data, f, indent=2)

        md_text = f"""# Honeywell Autonomous HVAC Optimization Report

## Executive Performance Summary

- **Total HVAC Energy Reduction**: `{p.get('total_hvac_reduction_pct', 0.0):.2f}%`
- **Heating Energy Reduction**: `{p.get('heating_reduction_pct', 0.0):.2f}%`
- **Cooling Energy Change**: `{p.get('cooling_change_pct', 0.0):+.2f}%`
- **Comfort Change**: `{p.get('comfort_change_pct', 0.0):+.1f}%` (Baseline: `{p.get('baseline_comfort_pct', 0)}%` → Optimized: `{p.get('optimized_comfort_pct', 0)}%`)
- **{pk_label}**: `{pk_str}`
- **Final Setpoints**: Cooling Setpoint `{p.get('final_cooling_setpoint', 24)}°C` | Heating Setpoint `{p.get('final_heating_setpoint', 20)}°C`
- **Iterations Completed**: `{p.get('total_iterations', 0)}`
- **Total Runtime**: `{runtime_sec} s`
- **Convergence Reason**: `{p.get('convergence_reason', 'N/A')}`

---

## System Information

- **Project**: Honeywell Eco-Loop Building Agents
- **Simulation Engine**: EnergyPlus 26.1.0
- **LLM Engine**: Groq Llama 3.3 70B Versatile
- **Tool Registry Version**: `{TOOL_REGISTRY_VERSION}`

---

## Iteration Progression Summary

| Iteration | Heating SP | Cooling SP | Comfort % | Heating Energy (Wh) | Cooling Energy (Wh) | HVAC Mode |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
        for rec in history.records:
            md_text += f"| {rec.iteration} | {rec.heating_setpoint}°C | {rec.cooling_setpoint}°C | {rec.comfort_percentage:.1f}% | {rec.total_heating_energy:.2f} | {rec.total_cooling_energy:.2f} | {rec.hvac_mode} |\n"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_text)

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "iteration",
                "heating_setpoint",
                "cooling_setpoint",
                "comfort_percentage",
                "total_heating_energy_wh",
                "total_cooling_energy_wh",
                "hvac_mode",
                "temperature_trend",
                "reason"
            ])
            for rec in history.records:
                writer.writerow([
                    rec.iteration,
                    rec.heating_setpoint,
                    rec.cooling_setpoint,
                    rec.comfort_percentage,
                    rec.total_heating_energy,
                    rec.total_cooling_energy,
                    rec.hvac_mode,
                    rec.temperature_trend,
                    rec.decision.reason
                ])

        return {
            "status": "generated",
            "report_json": str(json_path),
            "report_md": str(md_path),
            "summary_csv": str(csv_path)
        }
