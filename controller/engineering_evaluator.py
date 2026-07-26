from typing import Optional
from models.iteration_comparison import IterationComparison
from models.engineering_assessment import EngineeringAssessment, ActionEffectiveness, MetricTrend


class EngineeringEvaluator:
    """
    Evaluates raw transition metrics from IterationComparison and converts them
    into structured semantic enums.
    """

    @staticmethod
    def evaluate(comparison: IterationComparison) -> EngineeringAssessment:
        comfort_trend = EngineeringEvaluator._evaluate_comfort(comparison.comfort_percentage_change)
        energy_trend = EngineeringEvaluator._evaluate_energy(comparison.total_energy_change_pct)
        peak_demand_trend = EngineeringEvaluator._evaluate_energy(comparison.peak_cooling_demand_change_pct) # Approximate for peak

        effectiveness = EngineeringEvaluator._evaluate_effectiveness(comfort_trend, energy_trend)

        return EngineeringAssessment(
            action_effectiveness=effectiveness,
            comfort_trend=comfort_trend,
            energy_trend=energy_trend,
            peak_demand_trend=peak_demand_trend
        )

    @staticmethod
    def _evaluate_comfort(comfort_change_pct: float) -> MetricTrend:
        if comfort_change_pct > 5.0:
            return MetricTrend.SIGNIFICANT_IMPROVEMENT
        elif comfort_change_pct > 0.5:
            return MetricTrend.IMPROVED
        elif comfort_change_pct > -0.5:
            return MetricTrend.UNCHANGED
        elif comfort_change_pct > -5.0:
            return MetricTrend.DEGRADED
        else:
            return MetricTrend.SIGNIFICANT_DEGRADATION

    @staticmethod
    def _evaluate_energy(energy_change_pct: float) -> MetricTrend:
        # Negative energy change means improvement (savings)
        if energy_change_pct < -5.0:
            return MetricTrend.SIGNIFICANT_IMPROVEMENT
        elif energy_change_pct < -0.5:
            return MetricTrend.IMPROVED
        elif energy_change_pct < 0.5:
            return MetricTrend.UNCHANGED
        elif energy_change_pct < 5.0:
            return MetricTrend.DEGRADED
        else:
            return MetricTrend.SIGNIFICANT_DEGRADATION

    @staticmethod
    def _evaluate_effectiveness(comfort_trend: MetricTrend, energy_trend: MetricTrend) -> ActionEffectiveness:
        if (comfort_trend in [MetricTrend.IMPROVED, MetricTrend.SIGNIFICANT_IMPROVEMENT, MetricTrend.UNCHANGED] and
            energy_trend in [MetricTrend.IMPROVED, MetricTrend.SIGNIFICANT_IMPROVEMENT]):
            return ActionEffectiveness.SUCCESSFUL
        
        if (comfort_trend in [MetricTrend.IMPROVED, MetricTrend.SIGNIFICANT_IMPROVEMENT] and
            energy_trend in [MetricTrend.IMPROVED, MetricTrend.SIGNIFICANT_IMPROVEMENT, MetricTrend.UNCHANGED]):
            return ActionEffectiveness.SUCCESSFUL

        if (comfort_trend in [MetricTrend.DEGRADED, MetricTrend.SIGNIFICANT_DEGRADATION] and
            energy_trend in [MetricTrend.DEGRADED, MetricTrend.SIGNIFICANT_DEGRADATION]):
            return ActionEffectiveness.COUNTERPRODUCTIVE

        if comfort_trend == MetricTrend.UNCHANGED and energy_trend == MetricTrend.UNCHANGED:
            return ActionEffectiveness.NEUTRAL

        return ActionEffectiveness.MIXED
