from pathlib import Path
from typing import Tuple, Dict, Optional, List

from models.building_state import BuildingState
from models.optimization_context import OptimizationContext


PROMPTS_DIR = Path("prompts")


def load_system_prompt() -> str:
    return (PROMPTS_DIR / "system_prompt.txt").read_text(encoding="utf-8")


def build_user_prompt_sections(
    state: BuildingState,
    candidates: List[Dict],
    context: Optional[OptimizationContext] = None
) -> Tuple[str, Dict[str, str]]:

    building_summary = f"""
# Building Performance Summary (Current State)

Timestamp: {state.timestamp}

Weather
-------
Average Outdoor Temperature: {state.average_outdoor_temperature:.2f} °C
Minimum Outdoor Temperature: {state.minimum_outdoor_temperature:.2f} °C
Maximum Outdoor Temperature: {state.maximum_outdoor_temperature:.2f} °C

Indoor Comfort Analysis
-----------------------
Average Indoor Temperature: {state.average_indoor_temperature:.2f} °C
Minimum Indoor Temperature: {state.minimum_indoor_temperature:.2f} °C
Maximum Indoor Temperature: {state.maximum_indoor_temperature:.2f} °C
Temperature Standard Deviation: {state.temperature_standard_deviation:.2f} °C

Cooling Performance
-------------------
Average Cooling Rate: {state.average_cooling_rate:.2f} W
Peak Cooling Rate: {state.peak_cooling_rate:.2f} W
Total Cooling Energy: {state.total_cooling_energy:.2f} Wh
Cooling Load Factor: {state.cooling_load_factor:.3f}

Heating Performance
-------------------
Average Heating Rate: {state.average_heating_rate:.2f} W
Peak Heating Rate: {state.peak_heating_rate:.2f} W
Total Heating Energy: {state.total_heating_energy:.2f} Wh
Heating Load Factor: {state.heating_load_factor:.3f}

Chiller Performance
-------------------
Average Chiller Power: {state.average_chiller_power:.2f} W
Peak Chiller Power: {state.peak_chiller_power:.2f} W

Plant Performance
-----------------
Average Plant Cooling Demand: {state.average_plant_cooling_demand:.2f} W
Peak Plant Cooling Demand: {state.peak_plant_cooling_demand:.2f} W

Comfort Analysis
----------------
Comfort Hours (21.0°C - 25.0°C): {state.comfort_hours:.1f} hrs
Discomfort Hours: {state.discomfort_hours:.1f} hrs
Comfort Percentage: {state.comfort_percentage:.1f}%

Operational Intelligence
------------------------
HVAC Operating Mode: {state.hvac_operating_mode}
Temperature Trend: {state.temperature_trend}
""".strip()

    if context:
        prev_comfort = context.previous_state.comfort_percentage if context.previous_state else 0.0
        prev_heat = context.previous_state.total_heating_energy if context.previous_state else 0.0
        prev_cool = context.previous_state.total_cooling_energy if context.previous_state else 0.0
        prev_mode = context.previous_state.hvac_operating_mode if context.previous_state else "Unknown"
        prev_trend = context.previous_state.temperature_trend if context.previous_state else "Unknown"
        
        if context.iteration_comparison and context.engineering_assessment and context.previous_decision:
            assessment = context.engineering_assessment
            comp = context.iteration_comparison
            prev_dec = context.previous_decision
            
            previous_context_str = f"""
# Previous Optimization Result Context (Iteration {context.iteration})

Active Heating Setpoint: {context.active_heating_setpoint:.1f} °C
Active Cooling Setpoint: {context.active_cooling_setpoint:.1f} °C

## Transition Metrics
- Previous Action: Selected Candidate {prev_dec.selected_candidate_index}
- Action Effectiveness: {assessment.action_effectiveness.value}
- Comfort Trend: {assessment.comfort_trend.value} ({comp.comfort_percentage_change:+.1f}%)
- Heating Energy Trend: {assessment.energy_trend.value} ({comp.heating_energy_change_pct:+.1f}%)
- Cooling Energy Trend: {assessment.energy_trend.value} ({comp.cooling_energy_change_pct:+.1f}%)
- Total Energy Trend: {assessment.energy_trend.value} ({comp.total_energy_change_pct:+.1f}%)
""".strip()
        else:
            previous_context_str = f"""
# Previous Optimization Result Context (Iteration {context.iteration})

Active Heating Setpoint: {context.active_heating_setpoint:.1f} °C
Active Cooling Setpoint: {context.active_cooling_setpoint:.1f} °C
Previous Comfort Percentage: {prev_comfort:.1f}%
Previous Heating Energy: {prev_heat:.2f} Wh
Previous Cooling Energy: {prev_cool:.2f} Wh
Previous HVAC Mode: {prev_mode}
Previous Temperature Trend: {prev_trend}
""".strip()
    else:
        previous_context_str = """
# Previous Optimization Result Context

Initial Baseline Iteration (No previous setpoint modification history available).
""".strip()

    optimization_objective = """
# Optimization Objective

Priority 1: Maintain or improve occupant comfort.
Priority 2: Reduce TOTAL HVAC energy consumption.
Priority 3: Reduce peak demand.
Priority 4: Avoid unnecessary thermostat movement.

The model should understand that improving average temperature is NOT the primary objective if it increases overall HVAC energy while comfort remains unchanged.
""".strip()

    constraints = """
# Operational Constraints

- Heating Setpoint Absolute Range: 18.0°C to 24.0°C
- Cooling Setpoint Absolute Range: 22.0°C to 28.0°C
- Maximum Step Size: You may adjust setpoints by a maximum of ±1.0°C per iteration.
- Deadband Constraint: The system will automatically ensure cooling is at least 1.0°C higher than heating.
""".strip()

    candidates_str = "# Evaluated Candidates\n\nWe have pre-simulated the following nearby thermostat configurations. Compare them against the Current State.\n\n"
    for i, cand in enumerate(candidates, 1):
        c_state = cand["state"]
        candidates_str += f"""Candidate {i}
- Heating: {cand['heating']:.1f}°C, Cooling: {cand['cooling']:.1f}°C
- Total Energy: {c_state.total_heating_energy + c_state.total_cooling_energy:.2f} Wh
- Comfort: {c_state.comfort_percentage:.1f}%
- Peak Heating: {c_state.peak_heating_rate:.2f} W
- Peak Cooling: {c_state.peak_cooling_rate:.2f} W
- Temperature Trend: {c_state.temperature_trend}

"""
    candidates_str = candidates_str.strip()

    decision_strategy = """
# Decision Strategy (Engineering Policy)

You must select exactly ONE candidate from the Evaluated Candidates list that best satisfies the engineering policy.

## Rule 1
If a candidate improves comfort AND decreases total HVAC energy, strongly prefer it.

## Rule 2
If a candidate maintains comfort AND decreases total HVAC energy, prefer it over the current state. Energy has improved.

## Rule 3
If multiple candidates reduce energy without sacrificing comfort, select the one with the lowest total energy.

## Rule 4
If ALL candidates decrease comfort significantly, you must select the candidate that best preserves comfort, or select the candidate representing the Current State (if available in the list or if its performance is superior).

## Rule 5
Average indoor temperature should NEVER be used alone to justify thermostat changes. Decision making must primarily rely on Comfort Percentage and Total HVAC Energy.

# Explicit Reasoning Order
Before producing your selection, you must internally evaluate the following in order:
1. Which candidates improve or maintain comfort?
2. Among those, which candidate has the lowest total HVAC energy?
3. Does this candidate outperform the Current State?
Only then determine the selected candidate index.

Return ONLY valid JSON in the exact format:
{
    "selected_candidate_index": int,
    "reason": "...",
    "confidence": float
}
""".strip()

    full_prompt = f"{building_summary}\n\n{previous_context_str}\n\n{optimization_objective}\n\n{constraints}\n\n{candidates_str}\n\n{decision_strategy}"

    prompt_sections = {
        "building_summary": building_summary,
        "previous_context": previous_context_str,
        "optimization_objective": optimization_objective,
        "constraints": constraints,
        "candidates_str": candidates_str,
        "decision_strategy": decision_strategy
    }

    return full_prompt, prompt_sections


def build_user_prompt(
    state: BuildingState,
    candidates: List[Dict],
    context: Optional[OptimizationContext] = None
) -> str:
    full_prompt, _ = build_user_prompt_sections(state, candidates, context)
    return full_prompt