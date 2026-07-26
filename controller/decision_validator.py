from typing import Tuple


class DecisionValidator:
    """
    DecisionValidator acts as a deterministic safety envelope for the control system.
    It does not 'think' or invent new control actions. It mathematically clamps
    candidate setpoints to ensure physical safety and deadband constraints.
    """
    
    MIN_HEATING = 18.0
    MAX_HEATING = 24.0
    
    MIN_COOLING = 22.0
    MAX_COOLING = 28.0
    
    MIN_DEADBAND = 1.0

    @staticmethod
    def validate(candidate_heating: float, candidate_cooling: float) -> Tuple[float, float]:
        # 1. Enforce absolute physical limits (clamping)
        safe_heating = max(DecisionValidator.MIN_HEATING, min(DecisionValidator.MAX_HEATING, candidate_heating))
        safe_cooling = max(DecisionValidator.MIN_COOLING, min(DecisionValidator.MAX_COOLING, candidate_cooling))
        
        # 2. Enforce minimum deadband (Cooling must be >= Heating + DEADBAND)
        if safe_cooling - safe_heating < DecisionValidator.MIN_DEADBAND:
            # We must adjust one to maintain the deadband. 
            # A common strategy is to push cooling up to preserve the deadband.
            # However, if pushing cooling up exceeds MAX_COOLING, we must push heating down.
            if safe_heating + DecisionValidator.MIN_DEADBAND <= DecisionValidator.MAX_COOLING:
                safe_cooling = safe_heating + DecisionValidator.MIN_DEADBAND
            else:
                # E.g. heating is 27.5, cooling is 28.0. MAX_COOLING is 28.0.
                safe_cooling = DecisionValidator.MAX_COOLING
                safe_heating = safe_cooling - DecisionValidator.MIN_DEADBAND
                
        return round(safe_heating, 1), round(safe_cooling, 1)
