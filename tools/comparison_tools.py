from typing import Dict, Any, Optional
from tools.base_tool import BaseTool
from models.building_state import BuildingState
from models.iteration_comparison import IterationComparison


class CompareIterationsTool(BaseTool):
    name = "CompareIterationsTool"
    description = "Compares current iteration building state against previous iteration building state."

    def execute(
        self,
        iteration: int,
        current_state: BuildingState,
        previous_state: Optional[BuildingState] = None,
        **kwargs
    ) -> Dict[str, Any]:

        if not previous_state:
            cmp = IterationComparison(
                iteration=iteration,
                heating_energy_change_pct=0.0,
                cooling_energy_change_pct=0.0,
                total_energy_change_pct=0.0,
                comfort_percentage_change=0.0,
                peak_heating_demand_change_pct=0.0,
                peak_cooling_demand_change_pct=0.0,
                hvac_mode_changed=False,
                temperature_trend_changed=False,
                description="Baseline iteration (no comparative history available)."
            )
            return {"comparison": cmp, "comparison_dict": cmp.to_dict()}

        prev_h = previous_state.total_heating_energy
        curr_h = current_state.total_heating_energy
        h_pct = ((curr_h - prev_h) / prev_h * 100.0) if prev_h > 0 else 0.0

        prev_c = previous_state.total_cooling_energy
        curr_c = current_state.total_cooling_energy
        c_pct = ((curr_c - prev_c) / prev_c * 100.0) if prev_c > 0 else 0.0

        prev_tot = prev_h + prev_c
        curr_tot = curr_h + curr_c
        tot_pct = ((curr_tot - prev_tot) / prev_tot * 100.0) if prev_tot > 0 else 0.0

        comfort_diff = current_state.comfort_percentage - previous_state.comfort_percentage

        prev_pk_h = previous_state.peak_heating_rate
        curr_pk_h = current_state.peak_heating_rate
        pk_h_pct = ((curr_pk_h - prev_pk_h) / prev_pk_h * 100.0) if prev_pk_h > 0 else 0.0

        prev_pk_c = previous_state.peak_cooling_rate
        curr_pk_c = current_state.peak_cooling_rate
        pk_c_pct = ((curr_pk_c - prev_pk_c) / prev_pk_c * 100.0) if prev_pk_c > 0 else 0.0

        mode_changed = (current_state.hvac_operating_mode != previous_state.hvac_operating_mode)
        trend_changed = (current_state.temperature_trend != previous_state.temperature_trend)

        desc = (
            f"Iteration {iteration}: Total energy change: {tot_pct:+.2f}%, "
            f"Comfort change: {comfort_diff:+.1f}%. "
            f"Mode: {current_state.hvac_operating_mode}."
        )

        cmp = IterationComparison(
            iteration=iteration,
            heating_energy_change_pct=round(h_pct, 2),
            cooling_energy_change_pct=round(c_pct, 2),
            total_energy_change_pct=round(tot_pct, 2),
            comfort_percentage_change=round(comfort_diff, 2),
            peak_heating_demand_change_pct=round(pk_h_pct, 2),
            peak_cooling_demand_change_pct=round(pk_c_pct, 2),
            hvac_mode_changed=mode_changed,
            temperature_trend_changed=trend_changed,
            description=desc
        )

        return {"comparison": cmp, "comparison_dict": cmp.to_dict()}
