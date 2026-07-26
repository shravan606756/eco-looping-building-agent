from typing import Dict, Any
from tools.base_tool import BaseTool
from models.optimization_history import OptimizationHistory


class ConvergenceCheckTool(BaseTool):
    name = "ConvergenceCheckTool"
    description = "Evaluates closed-loop optimization stopping conditions (max iterations, setpoints unchanged, energy threshold, comfort degradation)."

    def execute(
        self,
        current_iteration: int,
        max_iterations: int,
        history: OptimizationHistory,
        min_energy_improvement_pct: float = 0.5,
        max_comfort_degradation_pct: float = 10.0,
        **kwargs
    ) -> Dict[str, Any]:

        records = history.records
        if current_iteration >= max_iterations:
            return {
                "converged": True,
                "reason": f"Maximum iterations reached ({max_iterations})."
            }

        if len(records) >= 2:
            last = records[-1]
            prev = records[-2]

            if (last.heating_setpoint == prev.heating_setpoint and 
                last.cooling_setpoint == prev.cooling_setpoint):
                return {
                    "converged": True,
                    "reason": f"Setpoints unchanged ({last.cooling_setpoint}°C / {last.heating_setpoint}°C) for two consecutive iterations."
                }

            first = records[0]
            if (first.comfort_percentage - last.comfort_percentage) > max_comfort_degradation_pct:
                return {
                    "converged": True,
                    "reason": f"Comfort percentage degraded beyond limit ({last.comfort_percentage:.1f}% vs baseline {first.comfort_percentage:.1f}%)."
                }

        if len(records) >= 3:
            r1 = records[-3]
            r3 = records[-1]
            tot_1 = r1.total_heating_energy + r1.total_cooling_energy
            tot_3 = r3.total_heating_energy + r3.total_cooling_energy

            if tot_1 > 0:
                imp = ((tot_1 - tot_3) / tot_1) * 100.0
                if 0 <= imp < min_energy_improvement_pct:
                    return {
                        "converged": True,
                        "reason": f"Energy improvement ({imp:.2f}%) fell below minimum threshold ({min_energy_improvement_pct}%)."
                    }

        return {
            "converged": False,
            "reason": "Optimization continuing: performance improving and setpoints active."
        }
