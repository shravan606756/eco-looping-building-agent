from typing import Dict, Any
from tools.base_tool import BaseTool
from models.building_state import BuildingState
from models.optimization_history import OptimizationHistory


class EvaluatePerformanceTool(BaseTool):
    name = "EvaluatePerformanceTool"
    description = "Evaluates quantitative performance metrics between Baseline and Final Optimized states."

    def execute(
        self,
        baseline_state: BuildingState,
        final_state: BuildingState,
        history: OptimizationHistory,
        runtime_ms: int = 0,
        convergence_reason: str = "",
        **kwargs
    ) -> Dict[str, Any]:

        base_h = baseline_state.total_heating_energy
        fin_h = final_state.total_heating_energy
        h_reduction_pct = ((base_h - fin_h) / base_h * 100.0) if base_h > 0 else 0.0

        base_c = baseline_state.total_cooling_energy
        fin_c = final_state.total_cooling_energy
        c_change_pct = ((fin_c - base_c) / base_c * 100.0) if base_c > 0 else 0.0

        base_tot = base_h + base_c
        fin_tot = fin_h + fin_c
        tot_reduction_pct = ((base_tot - fin_tot) / base_tot * 100.0) if base_tot > 0 else 0.0

        comfort_change_pct = final_state.comfort_percentage - baseline_state.comfort_percentage

        base_pk = max(baseline_state.peak_heating_rate, baseline_state.peak_cooling_rate)
        fin_pk = max(final_state.peak_heating_rate, final_state.peak_cooling_rate)
        pk_reduction_pct = ((base_pk - fin_pk) / base_pk * 100.0) if base_pk > 0 else 0.0

        last_rec = history.get_last_record()
        final_h_sp = last_rec.heating_setpoint if last_rec else 20.0
        final_c_sp = last_rec.cooling_setpoint if last_rec else 24.0

        metrics = {
            "baseline_heating_energy_wh": round(base_h, 2),
            "optimized_heating_energy_wh": round(fin_h, 2),
            "baseline_cooling_energy_wh": round(base_c, 2),
            "optimized_cooling_energy_wh": round(fin_c, 2),
            "baseline_total_energy_wh": round(base_tot, 2),
            "optimized_total_energy_wh": round(fin_tot, 2),
            "heating_reduction_pct": round(h_reduction_pct, 2),
            "cooling_change_pct": round(c_change_pct, 2),
            "total_hvac_reduction_pct": round(tot_reduction_pct, 2),
            "baseline_comfort_pct": round(baseline_state.comfort_percentage, 1),
            "optimized_comfort_pct": round(final_state.comfort_percentage, 1),
            "comfort_change_pct": round(comfort_change_pct, 1),
            "peak_demand_reduction_pct": round(pk_reduction_pct, 2),
            "total_iterations": len(history.records),
            "runtime_ms": runtime_ms,
            "final_heating_setpoint": final_h_sp,
            "final_cooling_setpoint": final_c_sp,
            "convergence_reason": convergence_reason
        }

        return {"performance_metrics": metrics}
