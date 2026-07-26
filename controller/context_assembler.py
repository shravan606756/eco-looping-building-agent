from typing import Optional
from models.building_state import BuildingState
from models.iteration_comparison import IterationComparison
from models.optimization_context import OptimizationContext
from controller.engineering_evaluator import EngineeringEvaluator
from ai.decision_schema import Decision


class ContextAssembler:

    @staticmethod
    def build(
        iteration: int,
        current_state: BuildingState,
        previous_state: Optional[BuildingState],
        iteration_comparison: Optional[IterationComparison],
        previous_decision: Optional[Decision],
        active_heating_setpoint: float,
        active_cooling_setpoint: float
    ) -> OptimizationContext:
        assessment = None
        if iteration_comparison is not None:
            assessment = EngineeringEvaluator.evaluate(iteration_comparison)

        return OptimizationContext(
            iteration=iteration,
            current_state=current_state,
            previous_state=previous_state,
            iteration_comparison=iteration_comparison,
            engineering_assessment=assessment,
            previous_decision=previous_decision,
            active_heating_setpoint=active_heating_setpoint,
            active_cooling_setpoint=active_cooling_setpoint
        )
